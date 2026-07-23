"""Sensor platform for SweTrack."""

from __future__ import annotations

from dataclasses import dataclass
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
from .entity import SweTrackEntity
from .models import SweTrackDevice


@dataclass(frozen=True, kw_only=True)
class SweTrackSensorDescription(SensorEntityDescription):
    """Describe a SweTrack sensor."""

    value_fn: Callable[[SweTrackDevice], object]


SENSORS = (
    SweTrackSensorDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.battery,
    ),
    SweTrackSensorDescription(
        key="external_voltage",
        translation_key="external_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.external_voltage,
    ),
    SweTrackSensorDescription(
        key="speed",
        translation_key="speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.speed,
    ),
    SweTrackSensorDescription(
        key="speed_limit",
        translation_key="speed_limit",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.speed_limit,
    ),
    SweTrackSensorDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.last_seen,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SweTrackSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    )


class SweTrackSensor(SweTrackEntity, SensorEntity):
    """Represent one SweTrack sensor."""

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
            from datetime import datetime
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
        return value
