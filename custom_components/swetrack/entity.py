"""Base entities for SweTrack."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ACCOUNT_NAME, DOMAIN
from .coordinator import SweTrackCoordinator


def account_identifier(coordinator: SweTrackCoordinator) -> tuple[str, str]:
    """Return the identifier for the API account device."""
    return (DOMAIN, f"account_{coordinator.entry.entry_id}")


class SweTrackAccountEntity(CoordinatorEntity[SweTrackCoordinator]):
    """Base entity attached to one SweTrack config entry/account."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        account_name = self.coordinator.entry.data.get(
            CONF_ACCOUNT_NAME, self.coordinator.entry.title
        )
        return DeviceInfo(
            identifiers={account_identifier(self.coordinator)},
            manufacturer="SweTrack",
            model="Account",
            name=f"SweTrack – {account_name}",
            configuration_url="https://www.swetrack.com/live",
        )


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
        if device and device.model_generation:
            model = f"{model} {device.model_generation}" if model else device.model_generation

        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            manufacturer="SweTrack",
            model=model,
            name=name,
            via_device=account_identifier(self.coordinator),
            configuration_url="https://www.swetrack.com/live",
        )
