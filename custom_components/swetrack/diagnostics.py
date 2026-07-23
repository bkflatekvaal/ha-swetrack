"""Diagnostics support for SweTrack."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "token",
    "access_token",
    "set-cookie",
    "cookie",
    "id",
    "device_id",
    "deviceId",
    "uniqueid",
    "imei",
    "serial_number",
    "serialNumber",
    "name",
    "account_name",
    "email",
    "latitude",
    "longitude",
    "lat",
    "lng",
    "lon",
    "model_photo",
}


def _redact(value: Any, parent_key: str | None = None) -> Any:
    """Recursively redact account, tracker and location identifiers."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_lower = key.lower()
            if key in SENSITIVE_KEYS or key_lower in SENSITIVE_KEYS:
                redacted[key] = "**REDACTED**"
            else:
                redacted[key] = _redact(item, key)
        return redacted

    if isinstance(value, list):
        return [_redact(item, parent_key) for item in value]

    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return privacy-preserving diagnostics."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return _redact(
        {
            "entry": {
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "coordinator": {
                "last_update_success": coordinator.last_update_success,
                "update_interval_seconds": (
                    coordinator.update_interval.total_seconds()
                    if coordinator.update_interval
                    else None
                ),
                "request_limit": coordinator.request_limit,
                "request_count": coordinator.request_count,
                "requests_remaining": coordinator.requests_remaining,
                "reset_at": coordinator.reset_at,
                "device_count": coordinator.device_count,
                "headers": coordinator.last_headers,
                "payload": coordinator.last_raw_payload,
            },
        }
    )
