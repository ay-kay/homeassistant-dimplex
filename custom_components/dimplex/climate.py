"""Climate platform for Dimplex integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VarID, WP_STATUS_1_MAP
from .coordinator import DimplexCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dimplex climate entities."""
    coordinator: DimplexCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([DimplexClimate(coordinator)])


class DimplexClimate(CoordinatorEntity[DimplexCoordinator], ClimateEntity):
    """Representation of a Dimplex heat pump climate entity."""

    _attr_has_entity_name = True
    _attr_translation_key = "heat_pump"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
    )

    def __init__(self, coordinator: DimplexCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.device_id)},
            "name": "Dimplex Heat Pump",
            "manufacturer": "Dimplex",
            "model": "Heat Pump",
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.get_value(VarID.TEMP_HK_IST, scale=0.1)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self.coordinator.get_value(VarID.TEMP_HK_SOLL, scale=0.1)

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        status = self.coordinator.get_mapped_value(VarID.WP_STATUS_1, WP_STATUS_1_MAP)
        
        if status == "Off":
            return HVACMode.OFF
        if status == "Floor Heating":
            return HVACMode.HEAT
        if status == "Cooling":
            return HVACMode.COOL
        
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Scale back to API format (e.g. 32.3 -> 323)
        api_value = int(temp * 10)
        await self.coordinator.client.write_variable(VarID.TEMP_HK_SOLL, api_value)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # Mapping HVACMode back to API value
        mode_map = {
            HVACMode.OFF: 1,
            HVACMode.HEAT: 2,
            HVACMode.COOL: 5,
        }
        
        if hvac_mode not in mode_map:
            return

        await self.coordinator.client.write_variable(VarID.WP_STATUS_1, mode_map[hvac_mode])
        await self.coordinator.async_request_refresh()
