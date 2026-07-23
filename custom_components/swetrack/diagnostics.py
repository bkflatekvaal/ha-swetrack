"""Diagnostics support for SweTrack."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN

TO_REDACT = {
    CONF_API_KEY,
    "authorization",
    "token",
    "access_token",
    "imei",
    "serial_number",
    "serialNumber",
    "latitude",
    "longitude",
    "lat",
    "lng",
    "lon",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options)}, TO_REDACT
        ),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "request_limit": coordinator.request_limit,
            "requests_remaining": coordinator.requests_remaining,
            "reset_at": coordinator.reset_at,
            "headers": async_redact_data(coordinator.last_headers, TO_REDACT),
            "payload": async_redact_data(coordinator.last_raw_payload, TO_REDACT),
        },
    }
