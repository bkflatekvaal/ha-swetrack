"""Base entities for SweTrack."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ACCOUNT_NAME, DOMAIN
from .coordinator import SweTrackCoordinator


def account_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Describe the same account device during setup and entity registration."""
    account_name = entry.data.get(CONF_ACCOUNT_NAME, entry.title)
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{entry.entry_id}")},
        manufacturer="SweTrack",
        model="Account",
        name=f"SweTrack – {account_name}",
        configuration_url="https://www.swetrack.com/live",
    )


class SweTrackAccountEntity(CoordinatorEntity[SweTrackCoordinator]):
    """Base entity attached to one SweTrack config entry/account."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return account_device_info(self.coordinator.entry)


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
            via_device_id=self.coordinator.account_device_id,
            configuration_url="https://www.swetrack.com/live",
        )
