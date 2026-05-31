"""Sensor platform for Dimplex integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
    UnitOfEnergy,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    REVOLUTIONS_PER_MINUTE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VarID,
    WP_STATUS_1_MAP,
    WP_STATUS_2_MAP,
    VENTILATION_MODE_MAP,
)
from .coordinator import DimplexCoordinator


@dataclass(frozen=True, kw_only=True)
class DimplexSensorEntityDescription(SensorEntityDescription):
    """Describes Dimplex sensor entity."""

    variable_id: str
    scale: float = 1.0
    value_map: dict[str, str] | None = None


SENSOR_DESCRIPTIONS: tuple[DimplexSensorEntityDescription, ...] = (
    # Temperature sensors
    DimplexSensorEntityDescription(
        key="temperature_warmwater",
        variable_id=VarID.TEMP_WARMWATER,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_return",
        variable_id=VarID.TEMP_RETURN,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_supply",
        variable_id=VarID.TEMP_SUPPLY,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_hk",
        variable_id=VarID.TEMP_HK,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_hk_target",
        variable_id=VarID.TEMP_HK_SOLL,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_hk_actual",
        variable_id=VarID.TEMP_HK_IST,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_system_target",
        variable_id=VarID.TEMP_SYSTEM_SOLL,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_system_actual",
        variable_id=VarID.TEMP_SYSTEM_IST,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_room_target",
        variable_id=VarID.TEMP_ROOM_SOLL,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_room_actual",
        variable_id=VarID.TEMP_ROOM_IST,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="temperature_dewpoint",
        variable_id=VarID.TEMP_DEWPOINT,
        scale=0.1,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Ventilation temperature sensors
    DimplexSensorEntityDescription(
        key="vent_temp_outside",
        variable_id=VarID.VENT_TEMP_OUTSIDE,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_temp_supply",
        variable_id=VarID.VENT_TEMP_SUPPLY,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_temp_exhaust",
        variable_id=VarID.VENT_TEMP_EXHAUST,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_temp_outgoing",
        variable_id=VarID.VENT_TEMP_OUTGOING,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Humidity sensors
    DimplexSensorEntityDescription(
        key="vent_humidity_exhaust",
        variable_id=VarID.VENT_HUMIDITY_EXHAUST,
        scale=0.1,
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_humidity_outside",
        variable_id=VarID.VENT_HUMIDITY_OUTSIDE,
        scale=0.1,
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # VOC sensors
    DimplexSensorEntityDescription(
        key="vent_voc_exhaust",
        variable_id=VarID.VENT_VOC_EXHAUST,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_voc_outside",
        variable_id=VarID.VENT_VOC_OUTSIDE,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Ventilation flow sensors
    DimplexSensorEntityDescription(
        key="vent_filter_days",
        variable_id=VarID.VENT_FILTER_DAYS,
        icon="mdi:air-filter",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_exhaust_flow",
        variable_id=VarID.VENT_EXHAUST_FLOW,
        icon="mdi:fan",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_supply_flow",
        variable_id=VarID.VENT_SUPPLY_FLOW,
        icon="mdi:fan",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_supply_fan_speed",
        variable_id=VarID.VENT_SUPPLY_FAN_SPEED,
        icon="mdi:fan",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    DimplexSensorEntityDescription(
        key="vent_exhaust_fan_speed",
        variable_id=VarID.VENT_EXHAUST_FAN_SPEED,
        icon="mdi:fan",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Compressor stats
    DimplexSensorEntityDescription(
        key="compressor_runtime",
        variable_id=VarID.COMPRESSOR_RUNTIME,
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="compressor_clocks_total",
        variable_id=VarID.COMPRESSOR_CLOCKS_TOTAL,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="compressor_clocks_heating",
        variable_id=VarID.COMPRESSOR_CLOCKS_HEATING,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="compressor_clocks_hotwater",
        variable_id=VarID.COMPRESSOR_CLOCKS_HOTWATER,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="compressor_clocks_cooling",
        variable_id=VarID.COMPRESSOR_CLOCKS_COOLING,
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Status sensors
    DimplexSensorEntityDescription(
        key="wp_status",
        variable_id=VarID.WP_STATUS_1,
        icon="mdi:heat-pump",
        value_map=WP_STATUS_1_MAP,
    ),
    DimplexSensorEntityDescription(
        key="compressor_status",
        variable_id=VarID.WP_STATUS_2,
        icon="mdi:pump",
        value_map=WP_STATUS_2_MAP,
    ),
    DimplexSensorEntityDescription(
        key="ventilation_mode",
        variable_id=VarID.VENTILATION_MODE,
        icon="mdi:fan",
        value_map=VENTILATION_MODE_MAP,
    ),
    DimplexSensorEntityDescription(
        key="ventilation_bypass",
        variable_id=VarID.VENT_BYPASS_STATUS,
        icon="mdi:valve",
    ),
    # Energy sensors
    DimplexSensorEntityDescription(
        key="energy_heating",
        variable_id=VarID.ENERGY_HEATING,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="energy_hotwater",
        variable_id=VarID.ENERGY_WARMWATER,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="energy_cooling",
        variable_id=VarID.ENERGY_COOLING_ALT,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Heat quantity sensors
    DimplexSensorEntityDescription(
        key="heat_heating",
        variable_id=VarID.HEAT_HEATING,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    DimplexSensorEntityDescription(
        key="heat_hotwater",
        variable_id=VarID.HEAT_WARMWATER,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # Diagnostic / Alternative sensors (hidden by default)
    DimplexSensorEntityDescription(
        key="energy_total",
        variable_id=VarID.ENERGY_TOTAL_ALT,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
    ),
    DimplexSensorEntityDescription(
        key="heat_total",
        variable_id=VarID.HEAT_TOTAL_ALT,
        scale=1.0,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dimplex sensor entities."""
    coordinator: DimplexCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        DimplexSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class DimplexSensor(CoordinatorEntity[DimplexCoordinator], SensorEntity):
    """Representation of a Dimplex sensor."""

    entity_description: DimplexSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DimplexCoordinator,
        description: DimplexSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.device_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.device_id)},
            "name": "Dimplex Heat Pump",
            "manufacturer": "Dimplex",
            "model": "Heat Pump",
        }
        self._attr_translation_key = description.key

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        desc = self.entity_description

        if desc.value_map:
            return self.coordinator.get_mapped_value(
                desc.variable_id,
                desc.value_map,
            )

        return self.coordinator.get_value(
            desc.variable_id,
            scale=desc.scale,
        )
