"""Base entity for SweTrack."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SweTrackCoordinator


class SweTrackEntity(CoordinatorEntity[SweTrackCoordinator]):
    """Base class for tracker entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SweTrackCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self.device_id = device_id

    @property
    def device(self):
        return self.coordinator.data.get(self.device_id)

    @property
    def available(self) -> bool:
        return super().available and self.device is not None

    @property
    def device_info(self) -> DeviceInfo:
        device = self.device
        name = device.name if device else f"SweTrack {self.device_id}"
        model = device.model if device else None
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            manufacturer="SweTrack",
            model=model,
            name=name,
        )
