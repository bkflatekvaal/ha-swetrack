"""Sensor platform for SweTrack."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import CONF_ACCOUNT_LANGUAGE, CONF_ACCOUNT_NAME, DOMAIN
from .coordinator import SweTrackCoordinator
from .entity import SweTrackAccountEntity, SweTrackEntity
from .models import SweTrackDevice


@dataclass(frozen=True, kw_only=True)
class SweTrackSensorDescription(SensorEntityDescription):
    """Describe a SweTrack tracker sensor."""

    value_fn: Callable[[SweTrackDevice], object]


SENSORS = (
    SweTrackSensorDescription(
        key="battery",
        name="Battery",
        translation_key="battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.battery,
    ),
    SweTrackSensorDescription(
        key="external_voltage",
        name="External voltage",
        translation_key="external_voltage",
        icon="mdi:car-battery",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.external_voltage,
    ),
    SweTrackSensorDescription(
        key="speed",
        name="Current speed",
        translation_key="speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.speed,
    ),
    SweTrackSensorDescription(
        key="speed_limit",
        name="Speed limit",
        translation_key="speed_limit",
        icon="mdi:speedometer-medium",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.speed_limit,
    ),
    SweTrackSensorDescription(
        key="temperature",
        name="Temperature",
        translation_key="temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.temperature,
    ),
    SweTrackSensorDescription(
        key="humidity",
        name="Humidity",
        translation_key="humidity",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.humidity,
    ),
    SweTrackSensorDescription(
        key="wake_interval",
        name="Wake-up interval",
        translation_key="wake_interval",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.wake_interval,
    ),
    SweTrackSensorDescription(
        key="last_seen",
        name="Last seen",
        translation_key="last_seen",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.last_seen,
    ),
)


@dataclass(frozen=True, kw_only=True)
class SweTrackAccountSensorDescription(SensorEntityDescription):
    """Describe an account/API diagnostic sensor."""

    value_fn: Callable[[SweTrackCoordinator], object]


ACCOUNT_SENSORS = (
    SweTrackAccountSensorDescription(
        key="daily_limit",
        name="Daily API limit",
        translation_key="daily_limit",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.request_limit,
    ),
    SweTrackAccountSensorDescription(
        key="requests_today",
        name="API requests today",
        translation_key="requests_today",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.request_count,
    ),
    SweTrackAccountSensorDescription(
        key="remaining",
        name="API requests remaining",
        translation_key="remaining",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.requests_remaining,
    ),
    SweTrackAccountSensorDescription(
        key="reset",
        name="Quota reset",
        translation_key="reset",
        icon="mdi:clock-refresh-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: coordinator.reset_at,
    ),
    SweTrackAccountSensorDescription(
        key="polling_interval",
        name="Polling interval",
        translation_key="polling_interval",
        icon="mdi:timer-sync-outline",
        native_unit_of_measurement="s",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: (
            int(coordinator.update_interval.total_seconds())
            if coordinator.update_interval
            else None
        ),
    ),
    SweTrackAccountSensorDescription(
        key="trackers",
        name="Trackers",
        translation_key="trackers",
        icon="mdi:map-marker-multiple",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.device_count,
    ),
    SweTrackAccountSensorDescription(
        key="events",
        name="Total events",
        translation_key="events",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda coordinator: coordinator.event_count,
    ),
    SweTrackAccountSensorDescription(
        key="language",
        name="Account language",
        translation_key="language",
        icon="mdi:translate",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: coordinator.entry.data.get(CONF_ACCOUNT_LANGUAGE),
    ),
)



async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Remove stale v0.2.6 optional entities that were created for trackers
    # which never exposed those hardware capabilities.
    _async_remove_stale_optional_entities(hass, entry, coordinator)

    entities = [
        SweTrackSensor(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        for description in SENSORS
        if device.supports(description.key)
    ]
    entities.extend(
        SweTrackAccountSensor(coordinator, description)
        for description in ACCOUNT_SENSORS
    )
    async_add_entities(entities)


OPTIONAL_TRACKER_SENSOR_KEYS = {
    "temperature",
    "humidity",
    "wake_interval",
}


def _async_remove_stale_optional_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: SweTrackCoordinator,
) -> None:
    """Remove optional entities incorrectly created by v0.2.6."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    unsupported_unique_ids = {
        f"{device_id}_{key}"
        for device_id, device in coordinator.data.items()
        for key in OPTIONAL_TRACKER_SENSOR_KEYS
        if not device.supports(key)
    }

    for registry_entry in entries:
        if (
            registry_entry.domain == "sensor"
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id in unsupported_unique_ids
        ):
            registry.async_remove(registry_entry.entity_id)


class SweTrackSensor(SweTrackEntity, SensorEntity):
    """Represent one tracker sensor."""

    entity_description: SweTrackSensorDescription

    def __init__(
        self,
        coordinator: SweTrackCoordinator,
        device_id: str,
        description: SweTrackSensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self):
        if not self.device:
            return None
        value = self.entity_description.value_fn(self.device)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return _as_datetime(value)
        return value


class SweTrackAccountSensor(SweTrackAccountEntity, SensorEntity):
    """Represent account/API diagnostics."""

    entity_description: SweTrackAccountSensorDescription

    def __init__(
        self,
        coordinator: SweTrackCoordinator,
        description: SweTrackAccountSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_{description.key}"
        )

    @property
    def native_value(self):
        value = self.entity_description.value_fn(self.coordinator)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return _as_datetime(value)
        return value


def _as_datetime(value):
    """Convert ISO date text to datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
