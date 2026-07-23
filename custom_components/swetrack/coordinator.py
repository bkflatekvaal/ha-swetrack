"""Data coordinator for SweTrack."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SweTrackApiClient,
    SweTrackApiError,
    SweTrackAuthError,
    SweTrackRateLimitError,
)
from .const import (
    AUTO_RESERVE_RATIO,
    CONF_ENABLED_DEVICES,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_MODE,
    DEFAULT_AUTO_INTERVAL,
    DEFAULT_MANUAL_INTERVAL,
    DOMAIN,
    ISSUE_API_QUOTA_EXHAUSTED,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    UPDATE_MODE_AUTO,
)
from .models import SweTrackDevice, extract_device_list, normalize_device

_LOGGER = logging.getLogger(__name__)


class SweTrackCoordinator(DataUpdateCoordinator[dict[str, SweTrackDevice]]):
    """Coordinate a single API poll for all SweTrack entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: SweTrackApiClient,
    ) -> None:
        self.entry = entry
        self.api = api
        self.last_headers: dict[str, str] = {}
        self.last_raw_payload: Any = None
        self.request_limit: int | None = None
        self.request_count: int | None = None
        self.requests_remaining: int | None = None
        self.reset_at: str | None = None
        self.device_count: int = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=self._configured_interval()),
            always_update=False,
        )

    def _configured_interval(self) -> int:
        mode = self.entry.options.get(CONF_UPDATE_MODE, UPDATE_MODE_AUTO)
        if mode != UPDATE_MODE_AUTO:
            value = self.entry.options.get(
                CONF_UPDATE_INTERVAL, DEFAULT_MANUAL_INTERVAL
            )
            return max(MIN_UPDATE_INTERVAL, min(MAX_UPDATE_INTERVAL, int(value)))
        return DEFAULT_AUTO_INTERVAL

    async def _async_update_data(self) -> dict[str, SweTrackDevice]:
        try:
            response = await self.api.async_get_devices()
        except SweTrackAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except SweTrackRateLimitError as err:
            self._lengthen_interval()
            self._create_quota_repair()
            raise UpdateFailed(str(err)) from err
        except SweTrackApiError as err:
            raise UpdateFailed(str(err)) from err

        self._delete_quota_repair()
        self.last_headers = response.headers
        self.last_raw_payload = response.data
        self._read_rate_limit(response.data, response.headers)

        devices: dict[str, SweTrackDevice] = {}
        for item in extract_device_list(response.data):
            device = normalize_device(item)
            if device is not None:
                devices[device.device_id] = device

        self.device_count = len(devices)

        enabled = self.entry.options.get(CONF_ENABLED_DEVICES)
        if enabled is not None:
            enabled_set = {str(value) for value in enabled}
            devices = {
                device_id: device
                for device_id, device in devices.items()
                if device_id in enabled_set
            }

        if self.entry.options.get(CONF_UPDATE_MODE, UPDATE_MODE_AUTO) == UPDATE_MODE_AUTO:
            self._apply_automatic_interval()

        return devices

    @property
    def quota_issue_id(self) -> str:
        """Return the unique Repairs issue ID for this config entry."""
        return f"{ISSUE_API_QUOTA_EXHAUSTED}_{self.entry.entry_id}"

    def _create_quota_repair(self) -> None:
        """Create a Repairs issue when the API quota is exhausted."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.quota_issue_id,
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_API_QUOTA_EXHAUSTED,
            translation_placeholders={
                "account": self.entry.title,
            },
        )

    def _delete_quota_repair(self) -> None:
        """Remove the quota issue after a successful API request."""
        ir.async_delete_issue(self.hass, DOMAIN, self.quota_issue_id)

    def _read_rate_limit(
        self, payload: Any, headers: dict[str, str]
    ) -> None:
        def integer_from(*values: Any) -> int | None:
            for value in values:
                if value is None:
                    continue
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
            return None

        body = payload if isinstance(payload, dict) else {}
        meta = body.get("meta", {})
        if not isinstance(meta, dict):
            meta = {}
        api_usage = meta.get("api_usage", {})
        if not isinstance(api_usage, dict):
            api_usage = {}

        rate = body.get("rate_limit", body.get("rateLimit", {}))
        if not isinstance(rate, dict):
            rate = {}

        self.request_limit = integer_from(
            headers.get("x-ratelimit-limit"),
            headers.get("x-rate-limit-limit"),
            api_usage.get("daily_limit"),
            body.get("daily_limit"),
            rate.get("daily_limit"),
            rate.get("limit"),
        )
        self.request_count = integer_from(
            api_usage.get("request_count"),
            body.get("request_count"),
            rate.get("request_count"),
            rate.get("used"),
        )
        self.requests_remaining = integer_from(
            headers.get("x-ratelimit-remaining"),
            headers.get("x-rate-limit-remaining"),
            api_usage.get("remaining_requests"),
            body.get("remaining_requests"),
            rate.get("remaining_requests"),
            rate.get("remaining"),
        )
        self.reset_at = (
            headers.get("x-ratelimit-reset")
            or headers.get("x-rate-limit-reset")
            or api_usage.get("reset_at")
            or body.get("reset_at")
            or rate.get("reset_at")
        )

    def _apply_automatic_interval(self) -> None:
        interval = DEFAULT_AUTO_INTERVAL

        if self.requests_remaining is not None and self.requests_remaining > 0:
            seconds_to_reset = self._seconds_to_reset()
            if seconds_to_reset is not None:
                usable_requests = max(
                    1, int(self.requests_remaining * (1 - AUTO_RESERVE_RATIO))
                )
                interval = max(interval, int(seconds_to_reset / usable_requests) + 1)

        interval = max(MIN_UPDATE_INTERVAL, min(MAX_UPDATE_INTERVAL, interval))
        new_interval = timedelta(seconds=interval)
        if self.update_interval != new_interval:
            _LOGGER.debug("SweTrack automatic polling interval set to %s seconds", interval)
            self.update_interval = new_interval

    def _seconds_to_reset(self) -> int | None:
        if self.reset_at is None:
            return None

        try:
            if str(self.reset_at).isdigit():
                reset = datetime.fromtimestamp(int(self.reset_at), tz=timezone.utc)
            else:
                reset = datetime.fromisoformat(
                    str(self.reset_at).replace("Z", "+00:00")
                )
                if reset.tzinfo is None:
                    reset = reset.replace(tzinfo=timezone.utc)
            return max(1, int((reset - datetime.now(timezone.utc)).total_seconds()))
        except (TypeError, ValueError, OSError):
            return None

    def _lengthen_interval(self) -> None:
        current = int((self.update_interval or timedelta(minutes=3)).total_seconds())
        self.update_interval = timedelta(
            seconds=min(MAX_UPDATE_INTERVAL, max(current * 2, 300))
        )
