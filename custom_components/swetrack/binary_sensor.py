"""Binary sensor platform for SweTrack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import SweTrackCoordinator
from .entity import SweTrackEntity
from .models import SweTrackDevice


@dataclass(frozen=True, kw_only=True)
class SweTrackBinaryDescription(BinarySensorEntityDescription):
    """Describe a binary sensor."""

    value_fn: Callable[[SweTrackDevice], bool | None]


BINARY_SENSORS = (
    SweTrackBinaryDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.online,
    ),
    SweTrackBinaryDescription(
        key="ignition",
        translation_key="ignition",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda device: device.ignition,
    ),
    SweTrackBinaryDescription(
        key="external_power",
        translation_key="external_power",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda device: device.external_power,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SweTrackBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
    )


class SweTrackBinarySensor(SweTrackEntity, BinarySensorEntity):
    """Represent a SweTrack binary sensor."""

    entity_description: SweTrackBinaryDescription

    def __init__(
        self,
        coordinator: SweTrackCoordinator,
        device_id: str,
        description: SweTrackBinaryDescription,
    ) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if not self.device:
            return None
        return self.entity_description.value_fn(self.device)
