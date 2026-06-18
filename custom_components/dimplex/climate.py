"""Climate platform for Dimplex integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VarID
from .coordinator import DimplexCoordinator

# Map the live status register (WP_STATUS_1 / 1586i) to what the pump is
# currently doing. The operating mode itself (Betriebsart) is exposed as a
# separate select entity, so this entity only reports the live action.
STATUS_VALUE_TO_ACTION: dict[str, HVACAction] = {
    "2": HVACAction.HEATING,    # Heizen
    "3": HVACAction.HEATING,    # Schwimmbad
    "4": HVACAction.IDLE,       # Warmwasser (no dedicated HA action)
    "5": HVACAction.COOLING,    # Kühlen
    "10": HVACAction.DEFROSTING,  # Abtauen
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dimplex climate entities."""
    coordinator: DimplexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DimplexClimate(coordinator)])


class DimplexClimate(CoordinatorEntity[DimplexCoordinator], ClimateEntity):
    """Heat pump climate entity for room temperature control (heating circuit 1).

    Target/current temperature use the base room setpoint (502a, a plain degC
    float) and the actual room temperature (1632i) rather than the
    heating-curve-derived flow values (1620i/1621i), which are recomputed and
    cannot be set directly. The operating mode (Betriebsart) is handled by a
    dedicated select entity, so this entity only exposes temperature plus the
    current activity via ``hvac_action``.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "heat_pump"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    # Mode selection lives in the Betriebsart select; keep a single neutral mode
    # here so the card never shows a misleading "Off" (Sommer still does hot water).
    _attr_hvac_modes = [HVACMode.AUTO]
    _attr_hvac_mode = HVACMode.AUTO
    _attr_min_temp = 10.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 0.1

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
        """Return the current room temperature."""
        return self.coordinator.get_value(VarID.ROOM_TEMP_HK1, scale=0.1)

    @property
    def target_temperature(self) -> float | None:
        """Return the room temperature setpoint (502a is a plain degC float)."""
        value = self.coordinator.get_value(VarID.ROOM_SETPOINT_HK1)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return what the heat pump is currently doing."""
        status = self.coordinator.get_value(VarID.WP_STATUS_1)
        if status is None:
            return None
        return STATUS_VALUE_TO_ACTION.get(str(status), HVACAction.IDLE)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new room temperature setpoint."""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # 502a is a plain degC float (0.1 resolution) - write it directly.
        api_value = round(float(temp), 1)
        await self.coordinator.client.write_variable(
            VarID.ROOM_SETPOINT_HK1, api_value
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """No-op: the operating mode is controlled via the Betriebsart select."""
        return
