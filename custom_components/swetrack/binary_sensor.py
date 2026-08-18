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
from homeassistant.helpers import entity_registry as er

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
        name="Online",
        translation_key="online",
        icon="mdi:lan-connect",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.online,
    ),
    SweTrackBinaryDescription(
        key="ignition",
        name="Ignition",
        translation_key="ignition",
        icon="mdi:key-variant",
        value_fn=lambda device: device.ignition,
    ),
    SweTrackBinaryDescription(
        key="external_power",
        name="External power connected",
        translation_key="external_power",
        icon="mdi:power-plug",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda device: device.external_power,
    ),
    SweTrackBinaryDescription(
        key="power_saving",
        name="Power saving mode",
        translation_key="power_saving",
        icon="mdi:leaf",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.power_saving,
    ),
    SweTrackBinaryDescription(
        key="wake_by_time",
        name="Wake by time",
        translation_key="wake_by_time",
        icon="mdi:clock-start",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.wake_by_time,
    ),
    SweTrackBinaryDescription(
        key="wake_by_vibration",
        name="Wake by vibration",
        translation_key="wake_by_vibration",
        icon="mdi:vibrate",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.wake_by_vibration,
    ),
    SweTrackBinaryDescription(
        key="wake_by_light",
        name="Wake by light",
        translation_key="wake_by_light",
        icon="mdi:weather-sunny",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.wake_by_light,
    ),
    SweTrackBinaryDescription(
        key="safety_zone",
        name="Safety zone",
        translation_key="safety_zone",
        icon="mdi:shield-map-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.safety_zone,
    ),
    SweTrackBinaryDescription(
        key="relay",
        name="Relay",
        translation_key="relay",
        icon="mdi:electric-switch",
        value_fn=lambda device: device.relay,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Remove stale v0.2.6 wake-up entities which were created without first
    # checking whether that tracker model exposes the capability.
    _async_remove_stale_optional_entities(hass, entry, coordinator)

    async_add_entities(
        SweTrackBinarySensor(coordinator, device_id, description)
        for device_id, device in coordinator.data.items()
        for description in BINARY_SENSORS
        if device.supports(description.key)
    )


OPTIONAL_TRACKER_BINARY_KEYS = {
    "wake_by_time",
    "wake_by_vibration",
    "wake_by_light",
    "safety_zone",
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
        for key in OPTIONAL_TRACKER_BINARY_KEYS
        if not device.supports(key)
    }

    for registry_entry in entries:
        if (
            registry_entry.domain == "binary_sensor"
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id in unsupported_unique_ids
        ):
            registry.async_remove(registry_entry.entity_id)


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
        self._attr_name = description.name
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if not self.device:
            return None
        return self.entity_description.value_fn(self.device)
