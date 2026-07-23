"""Normalization helpers for SweTrack payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib


def as_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_bool(value: Any) -> bool | None:
    """Convert common boolean representations."""
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
    model_generation: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    accuracy: float | None = None
    speed: float | None = None
    speed_limit: float | None = None
    heading: float | None = None
    battery: float | None = None
    external_voltage: float | None = None
    online: bool | None = None
    ignition: bool | None = None
    external_power: bool | None = None
    power_saving: bool | None = None
    relay: bool | None = None
    temperature: float | None = None
    humidity: float | None = None
    wake_by_time: bool | None = None
    wake_interval: int | None = None
    wake_by_vibration: bool | None = None
    wake_by_light: bool | None = None
    safety_zone: bool | None = None
    last_seen: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def extract_device_list(payload: Any) -> list[dict[str, Any]]:
    """Extract devices from SweTrack's response envelope."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    data = payload.get("data")
    if isinstance(data, dict):
        devices = data.get("devices")
        if isinstance(devices, list):
            return [item for item in devices if isinstance(item, dict)]

    devices = payload.get("devices")
    if isinstance(devices, list):
        return [item for item in devices if isinstance(item, dict)]

    return []


def normalize_device(raw: dict[str, Any]) -> SweTrackDevice | None:
    """Normalize one SweTrack tracker object."""
    device_id = raw.get("id") or raw.get("device_id") or raw.get("uniqueid")
    if device_id is None:
        return None

    model_data = raw.get("model")
    model = model_data.get("model") if isinstance(model_data, dict) else model_data
    model_photo = (
        model_data.get("model_photo") if isinstance(model_data, dict) else None
    )
    model_generation = None
    if isinstance(model_photo, str):
        lower_photo = model_photo.lower()
        if "gen1" in lower_photo:
            model_generation = "Gen1"
        elif "gen2" in lower_photo:
            model_generation = "Gen2"

    position = raw.get("position_info")
    if not isinstance(position, dict):
        position = {}

    battery_data = raw.get("battery")
    if not isinstance(battery_data, dict):
        battery_data = {}

    speed_data = raw.get("speed")
    if not isinstance(speed_data, dict):
        speed_data = {}
    current_speed = speed_data.get("current_speed")
    if not isinstance(current_speed, dict):
        current_speed = {}
    speed_limit = speed_data.get("speed_limit")
    if not isinstance(speed_limit, dict):
        speed_limit = {}

    ignition_data = raw.get("ignition")
    ignition = (
        ignition_data.get("value")
        if isinstance(ignition_data, dict)
        else ignition_data
    )

    relay_data = raw.get("relay_switch")
    relay = relay_data.get("value") if isinstance(relay_data, dict) else relay_data

    saving_data = raw.get("powersaving_mode")
    power_saving = (
        saving_data.get("current") if isinstance(saving_data, dict) else saving_data
    )

    temp_hum = raw.get("temp_hum")
    if not isinstance(temp_hum, dict):
        temp_hum = {}
    current_temp_hum = temp_hum.get("current_data")
    if not isinstance(current_temp_hum, dict):
        current_temp_hum = {}
    temp_settings = temp_hum.get("current_settings")
    if not isinstance(temp_settings, dict):
        temp_settings = {}

    temperature = as_float(current_temp_hum.get("temperature"))
    humidity = as_float(current_temp_hum.get("humidity"))
    if temperature is not None:
        temperature /= 100
        if str(temp_settings.get("temp_unit", "")).lower().startswith("fahrenheit"):
            temperature = (temperature - 32) * 5 / 9
    if humidity is not None:
        humidity /= 100

    wakeup_info = raw.get("wakeup_info")
    if not isinstance(wakeup_info, dict):
        wakeup_info = {}
    wake_settings = wakeup_info.get("current_settings")
    if not isinstance(wake_settings, dict):
        wake_settings = {}

    status = raw.get("status")

    return SweTrackDevice(
        device_id=str(device_id),
        name=str(raw.get("name") or f"SweTrack {device_id}"),
        model=str(model) if model is not None else None,
        model_generation=model_generation,
        latitude=as_float(position.get("latitude")),
        longitude=as_float(position.get("longitude")),
        altitude=as_float(position.get("altitude")),
        accuracy=as_float(position.get("accuracy")),
        speed=as_float(current_speed.get("value")),
        speed_limit=as_float(speed_limit.get("value")),
        heading=as_float(position.get("heading")),
        battery=as_float(battery_data.get("internal")),
        external_voltage=as_float(battery_data.get("external_voltage")),
        online=as_bool(status),
        ignition=as_bool(ignition),
        external_power=as_bool(battery_data.get("external_power_supply")),
        power_saving=as_bool(power_saving),
        relay=as_bool(relay),
        temperature=temperature,
        humidity=humidity,
        wake_by_time=as_bool(wake_settings.get("wakebytime")),
        wake_interval=(
            int(wake_settings["wakebytimeinfo"])
            if wake_settings.get("wakebytimeinfo") is not None
            else None
        ),
        wake_by_vibration=as_bool(wake_settings.get("wakebyvib")),
        wake_by_light=as_bool(wake_settings.get("wakebylight")),
        safety_zone=as_bool(wake_settings.get("safetyzone")),
        last_seen=raw.get("last_update") or position.get("datetime"),
        raw=raw,
    )



def derive_account_identity(account_payload: Any, api_key: str) -> tuple[str, str, str | None]:
    """Derive a stable account identifier and useful display name."""
    data = account_payload
    if isinstance(account_payload, dict) and isinstance(account_payload.get("data"), dict):
        data = account_payload["data"]

    if not isinstance(data, dict):
        data = {}

    user = data.get("user")
    if not isinstance(user, dict):
        user = data

    raw_id = (
        user.get("id")
        or user.get("user_id")
        or user.get("userId")
        or data.get("account_id")
        or data.get("accountId")
    )

    username = user.get("username") or user.get("name")
    email = user.get("email")

    if username:
        display_name = str(username)
    elif email:
        # Show a useful but less exposing fallback in Home Assistant.
        local_part, separator, domain = str(email).partition("@")
        if separator:
            display_name = f"{local_part[:2]}***@{domain}"
        else:
            display_name = "SweTrack account"
    else:
        display_name = "SweTrack account"

    if raw_id is None:
        # Never expose or store the API key itself as the account identifier.
        raw_id = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:20]

    language = user.get("language") or data.get("language")
    return str(raw_id), display_name, str(language) if language is not None else None
