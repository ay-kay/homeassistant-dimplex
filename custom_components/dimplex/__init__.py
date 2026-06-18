"""The Dimplex Heat Pump integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DimplexApiClient, DimplexAuthError, DimplexApiError
from .const import DOMAIN
from .coordinator import DimplexCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.CLIMATE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dimplex from a config entry."""
    session = async_get_clientsession(hass)

    client = DimplexApiClient(
        device_id=entry.data["device_id"],
        access_token=entry.data["access_token"],
        refresh_token=entry.data["refresh_token"],
        session=session,
    )

    # Test connection and handle auth errors
    try:
        if not await client.test_connection():
            raise ConfigEntryNotReady("Failed to connect to Dimplex API")
    except DimplexAuthError as err:
        raise ConfigEntryAuthFailed(err) from err
    except DimplexApiError as err:
        raise ConfigEntryNotReady(err) from err

    coordinator = DimplexCoordinator(hass, client, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: DimplexCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.close()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
