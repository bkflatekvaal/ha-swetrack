"""Device tracker platform for SweTrack."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import SweTrackCoordinator
from .entity import SweTrackEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: SweTrackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SweTrackDeviceTracker(coordinator, device_id)
        for device_id in coordinator.data
    )


class SweTrackDeviceTracker(SweTrackEntity, TrackerEntity):
    """Represent a SweTrack tracker on the map."""

    _attr_name = None
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(self, coordinator: SweTrackCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_location"

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return self.device.latitude if self.device else None

    @property
    def longitude(self) -> float | None:
        return self.device.longitude if self.device else None

    @property
    def location_accuracy(self) -> int:
        if not self.device or self.device.accuracy is None:
            return 0
        return max(0, round(self.device.accuracy))

    @property
    def extra_state_attributes(self):
        if not self.device:
            return {}
        return {
            "speed": self.device.speed,
            "heading": self.device.heading,
            "altitude": self.device.altitude,
            "last_seen": self.device.last_seen,
            "online": self.device.online,
            "power_saving": self.device.power_saving,
        }
