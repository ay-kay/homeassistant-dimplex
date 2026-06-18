"""Select platform for Dimplex integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VarID,
    OPERATING_MODE_MAP,
    OPERATING_MODE_TO_VALUE,
    VENTILATION_MODE_MAP,
    VENTILATION_MODE_TO_VALUE,
)
from .coordinator import DimplexCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dimplex select entities."""
    coordinator: DimplexCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        DimplexVentilationModeSelect(coordinator),
        DimplexOperatingModeSelect(coordinator),
    ])


class DimplexOperatingModeSelect(CoordinatorEntity[DimplexCoordinator], SelectEntity):
    """Representation of the Dimplex operating mode (Betriebsart) selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "operating_mode"
    _attr_icon = "mdi:sun-snowflake-variant"
    _attr_options = list(OPERATING_MODE_MAP.values())

    def __init__(self, coordinator: DimplexCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_id}_operating_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.device_id)},
            "name": "Dimplex Heat Pump",
            "manufacturer": "Dimplex",
            "model": "Heat Pump",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current operating mode."""
        return self.coordinator.get_mapped_value(
            VarID.OPERATING_MODE,
            OPERATING_MODE_MAP,
            default=None,
        )

    async def async_select_option(self, option: str) -> None:
        """Set the operating mode."""
        if option not in OPERATING_MODE_TO_VALUE:
            _LOGGER.error("Invalid operating mode: %s", option)
            return

        value = int(OPERATING_MODE_TO_VALUE[option])
        _LOGGER.debug("Setting operating mode to %s (value: %d)", option, value)
        await self.coordinator.client.write_variable(VarID.OPERATING_MODE, value)
        await self.coordinator.async_request_refresh()


class DimplexVentilationModeSelect(CoordinatorEntity[DimplexCoordinator], SelectEntity):
    """Representation of the Dimplex ventilation mode selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "ventilation_mode"
    _attr_icon = "mdi:fan"
    _attr_options = list(VENTILATION_MODE_MAP.values())

    def __init__(self, coordinator: DimplexCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_id}_ventilation_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.device_id)},
            "name": "Dimplex Heat Pump",
            "manufacturer": "Dimplex",
            "model": "Heat Pump",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current ventilation mode."""
        return self.coordinator.get_mapped_value(
            VarID.VENTILATION_MODE,
            VENTILATION_MODE_MAP,
            default=None,
        )

    async def async_select_option(self, option: str) -> None:
        """Set the ventilation mode."""
        if option not in VENTILATION_MODE_TO_VALUE:
            _LOGGER.error("Invalid ventilation mode: %s", option)
            return

        value = int(VENTILATION_MODE_TO_VALUE[option])
        _LOGGER.debug("Setting ventilation mode to %s (value: %d)", option, value)
        await self.coordinator.client.set_ventilation_mode(value)
        await self.coordinator.async_request_refresh()
