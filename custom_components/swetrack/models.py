"""Normalization helpers for SweTrack payloads.

The public API may vary by tracker model. These helpers deliberately accept
several likely field names until real device payloads have been verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def first_value(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first present, non-null key."""
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def nested_value(data: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    """Return the first value found at one of several nested paths."""
    for path in paths:
        current: Any = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current is not None:
            return current
    return None


def as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on", "online", "active"}:
            return True
        if normalized in {"false", "0", "no", "off", "offline", "inactive"}:
            return False
    return None


@dataclass(slots=True)
class SweTrackDevice:
    """Normalized tracker state."""

    device_id: str
    name: str
    model: str | None = None
    manufacturer: str = "SweTrack"
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    accuracy: float | None = None
    speed: float | None = None
    heading: float | None = None
    battery: float | None = None
    external_voltage: float | None = None
    online: bool | None = None
    ignition: bool | None = None
    external_power: bool | None = None
    last_seen: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def extract_device_list(payload: Any) -> list[dict[str, Any]]:
    """Find a device list in common API envelope formats."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("devices", "data", "result", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for nested_key in ("devices", "items", "data"):
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return [item for item in nested if isinstance(item, dict)]
    return []


def normalize_device(raw: dict[str, Any]) -> SweTrackDevice | None:
    """Normalize one tracker object."""
    device_id = first_value(
        raw, "id", "device_id", "deviceId", "imei", "serial_number", "serialNumber"
    )
    if device_id is None:
        return None

    position = first_value(raw, "position", "location", "last_position", default={})
    if not isinstance(position, dict):
        position = {}

    status = first_value(raw, "status", "telemetry", "state", default={})
    if not isinstance(status, dict):
        status = {}

    latitude = first_value(raw, "latitude", "lat")
    if latitude is None:
        latitude = first_value(position, "latitude", "lat")

    longitude = first_value(raw, "longitude", "lng", "lon")
    if longitude is None:
        longitude = first_value(position, "longitude", "lng", "lon")

    return SweTrackDevice(
        device_id=str(device_id),
        name=str(first_value(raw, "name", "device_name", "deviceName", default=f"SweTrack {device_id}")),
        model=first_value(raw, "model", "product", "device_model", "deviceModel"),
        latitude=as_float(latitude),
        longitude=as_float(longitude),
        altitude=as_float(first_value(position, "altitude", "alt")),
        accuracy=as_float(first_value(position, "accuracy", "horizontal_accuracy", "hdop")),
        speed=as_float(first_value(raw, "speed", default=first_value(position, "speed"))),
        heading=as_float(first_value(raw, "heading", "course", default=first_value(position, "heading", "course"))),
        battery=as_float(first_value(raw, "battery", "battery_level", "batteryLevel", default=first_value(status, "battery", "battery_level"))),
        external_voltage=as_float(first_value(raw, "external_voltage", "externalVoltage", "voltage", default=first_value(status, "external_voltage", "voltage"))),
        online=as_bool(first_value(raw, "online", "is_online", "isOnline", default=first_value(status, "online"))),
        ignition=as_bool(first_value(raw, "ignition", "ignition_on", "ignitionOn", default=first_value(status, "ignition"))),
        external_power=as_bool(first_value(raw, "external_power", "externalPower", "charging", default=first_value(status, "external_power", "charging"))),
        last_seen=first_value(raw, "last_seen", "lastSeen", "updated_at", "updatedAt", "timestamp", default=first_value(position, "timestamp", "updated_at")),
        raw=raw,
    )
