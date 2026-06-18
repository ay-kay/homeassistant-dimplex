"""Water heater platform for Dimplex integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VarID
from .coordinator import DimplexCoordinator

# Operation modes map onto the external hot-water block (771d):
#   "heat_pump" -> block off (hot water allowed)
#   "off"       -> block on  (hot water suppressed)
OPERATION_ON = STATE_HEAT_PUMP
OPERATION_OFF = STATE_OFF


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dimplex water heater entity."""
    coordinator: DimplexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DimplexWaterHeater(coordinator)])


class DimplexWaterHeater(CoordinatorEntity[DimplexCoordinator], WaterHeaterEntity):
    """Hot water control for the Dimplex heat pump.

    Exposes the current hot-water temperature (1305a) and the writable hot-water
    setpoint (1042i). The on/off operation maps onto the external hot-water block
    (771d), which can be used to suppress hot water during expensive hours.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "hot_water"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_operation_list = [OPERATION_ON, OPERATION_OFF]
    _attr_min_temp = 30.0
    _attr_max_temp = 65.0
    _attr_target_temperature_step = 1.0  # the setpoint (1042i) is whole degrees

    def __init__(self, coordinator: DimplexCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.device_id}_hot_water"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.device_id)},
            "name": "Dimplex Heat Pump",
            "manufacturer": "Dimplex",
            "model": "Heat Pump",
        }

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def current_temperature(self) -> float | None:
        """Return the current hot water temperature."""
        return self._to_float(self.coordinator.get_value(VarID.TEMP_WARMWATER))

    @property
    def target_temperature(self) -> float | None:
        """Return the hot water setpoint."""
        return self._to_float(self.coordinator.get_value(VarID.WW_SETPOINT))

    @property
    def current_operation(self) -> str:
        """Return whether hot water is currently allowed or blocked."""
        blocked = self.coordinator.get_value(VarID.WW_BLOCK_EXT)
        return OPERATION_OFF if str(blocked) == "1" else OPERATION_ON

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new hot water setpoint."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        await self.coordinator.client.write_variable(
            VarID.WW_SETPOINT, int(round(temp))
        )
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Allow or block hot water via the external block flag."""
        value = 1 if operation_mode == OPERATION_OFF else 0
        await self.coordinator.client.write_variable(VarID.WW_BLOCK_EXT, value)
        await self.coordinator.async_request_refresh()
