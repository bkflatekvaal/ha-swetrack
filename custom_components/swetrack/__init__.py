"""The SweTrack integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SweTrackApiClient
from .const import API_BASE_URL, CONF_API_KEY, DOMAIN, PLATFORMS
from .coordinator import SweTrackCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SweTrack from a config entry."""
    api = SweTrackApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_API_KEY],
        API_BASE_URL,
    )
    coordinator = SweTrackCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a SweTrack config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
