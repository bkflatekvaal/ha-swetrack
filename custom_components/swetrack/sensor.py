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
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
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
        translation_key="battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.battery,
    ),
    SweTrackSensorDescription(
        key="external_voltage",
        translation_key="external_voltage",
        icon="mdi:car-battery",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.external_voltage,
    ),
    SweTrackSensorDescription(
        key="speed",
        translation_key="speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.speed,
    ),
    SweTrackSensorDescription(
        key="speed_limit",
        translation_key="speed_limit",
        icon="mdi:speedometer-medium",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.speed_limit,
    ),
    SweTrackSensorDescription(
        key="last_seen",
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
        key="api_daily_limit",
        translation_key="api_daily_limit",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.request_limit,
    ),
    SweTrackAccountSensorDescription(
        key="api_requests_used",
        translation_key="api_requests_used",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.request_count,
    ),
    SweTrackAccountSensorDescription(
        key="api_requests_remaining",
        translation_key="api_requests_remaining",
        icon="mdi:counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.requests_remaining,
    ),
    SweTrackAccountSensorDescription(
        key="api_reset",
        translation_key="api_reset",
        icon="mdi:clock-refresh-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: coordinator.reset_at,
    ),
    SweTrackAccountSensorDescription(
        key="polling_interval",
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        SweTrackSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    ]
    entities.extend(
        SweTrackAccountSensor(coordinator, description)
        for description in ACCOUNT_SENSORS
    )
    async_add_entities(entities)


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
