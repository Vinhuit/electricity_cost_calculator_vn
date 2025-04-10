from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
import logging

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    CONF_KWH_SENSOR,
    CONF_POWER_SENSOR,
    CONF_CURRENT_SENSOR,
    CONF_VOLTAGE_SENSOR,
    CONF_DEVICE_NAME,
    CONF_TIER_1_RATE,
    CONF_TIER_2_RATE,
    CONF_TIER_3_RATE,
    CONF_TIER_4_RATE,
    CONF_TIER_5_RATE,
    CONF_TIER_6_RATE,
    CONF_VAT_RATE,
    CONF_COST_UNIT,
    SENSOR_COST,
    SENSOR_COST_WITH_VAT,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    kwh_sensor = entry.data.get(CONF_KWH_SENSOR)
    power_sensor = entry.data.get(CONF_POWER_SENSOR)
    current_sensor = entry.data.get(CONF_CURRENT_SENSOR)
    voltage_sensor = entry.data.get(CONF_VOLTAGE_SENSOR)
    device_name = entry.data[CONF_DEVICE_NAME]

    # Create two sensors: cost without VAT and cost with VAT
    sensors = [
        ElectricityCostSensor(hass, entry, kwh_sensor, power_sensor, current_sensor, voltage_sensor, device_name, False),
        ElectricityCostSensor(hass, entry, kwh_sensor, power_sensor, current_sensor, voltage_sensor, device_name, True),
    ]
    async_add_entities(sensors)

class ElectricityCostSensor(SensorEntity):
    """Representation of an electricity cost sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, kwh_sensor: str, power_sensor: str, current_sensor: str, voltage_sensor: str, device_name: str, include_vat: bool):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.kwh_sensor = kwh_sensor
        self.power_sensor = power_sensor
        self.current_sensor = current_sensor
        self.voltage_sensor = voltage_sensor
        self.device_name = device_name
        self.include_vat = include_vat

        # Get pricing tiers, VAT rate, and cost unit from config entry
        self.tier_1_rate = entry.data[CONF_TIER_1_RATE]
        self.tier_2_rate = entry.data[CONF_TIER_2_RATE]
        self.tier_3_rate = entry.data[CONF_TIER_3_RATE]
        self.tier_4_rate = entry.data[CONF_TIER_4_RATE]
        self.tier_5_rate = entry.data[CONF_TIER_5_RATE]
        self.tier_6_rate = entry.data[CONF_TIER_6_RATE]
        self.vat_rate = entry.data[CONF_VAT_RATE]
        self.cost_unit = entry.data[CONF_COST_UNIT]

        _LOGGER.info("Creating sensor for device: %s with cost unit: %s", self.device_name, self.cost_unit)

        # Sensor attributes
        self._attr_name = (
            f"{device_name} Electricity Cost{' with VAT' if include_vat else ''}"
        )
        self._attr_unique_id = (
            f"{entry.entry_id}_{SENSOR_COST_WITH_VAT if include_vat else SENSOR_COST}"
        )
        self._attr_unit_of_measurement = self.cost_unit
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        kwh_value = 0.0

        # If a kWh sensor is provided, use it (normalize units if necessary)
        if self.kwh_sensor:
            kwh_state = self.hass.states.get(self.kwh_sensor)
            if kwh_state is None or kwh_state.state in ("unknown", "unavailable"):
                _LOGGER.warning("kWh sensor %s is unavailable", self.kwh_sensor)
                return 0
            try:
                value = float(kwh_state.state)
                # Normalize units (e.g., Wh to kWh, MJ to kWh)
                unit = kwh_state.attributes.get("unit_of_measurement", "").lower()
                if unit == "kwh":
                    kwh_value = value
                elif unit == "wh":
                    kwh_value = value / 1000  # Convert Wh to kWh
                elif unit == "mj":
                    kwh_value = value * 0.277778  # Convert MJ to kWh (1 MJ = 0.277778 kWh)
                else:
                    _LOGGER.warning("Unsupported unit for kWh sensor %s: %s", self.kwh_sensor, unit)
                    return 0
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid kWh value from sensor %s: %s", self.kwh_sensor, kwh_state.state)
                return 0

        # If a power sensor (W) is provided, convert to kWh
        elif self.power_sensor:
            power_state = self.hass.states.get(self.power_sensor)
            if power_state is None or power_state.state in ("unknown", "unavailable"):
                _LOGGER.warning("Power sensor %s is unavailable", self.power_sensor)
                return 0
            try:
                value = float(power_state.state)
                # Normalize units (e.g., kW to W)
                unit = power_state.attributes.get("unit_of_measurement", "").lower()
                if unit == "w":
                    power_value = value
                elif unit == "kw":
                    power_value = value * 1000  # Convert kW to W
                else:
                    _LOGGER.warning("Unsupported unit for power sensor %s: %s", self.power_sensor, unit)
                    return 0
                # Assume the power value is an average over 1 hour for simplicity
                kwh_value = (power_value * 1) / 1000
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid power value from sensor %s: %s", self.power_sensor, power_state.state)
                return 0

        # If current (A) and voltage (V) sensors are provided, calculate power and convert to kWh
        elif self.current_sensor and self.voltage_sensor:
            current_state = self.hass.states.get(self.current_sensor)
            voltage_state = self.hass.states.get(self.voltage_sensor)
            if current_state is None or current_state.state in ("unknown", "unavailable"):
                _LOGGER.warning("Current sensor %s is unavailable", self.current_sensor)
                return 0
            if voltage_state is None or voltage_state.state in ("unknown", "unavailable"):
                _LOGGER.warning("Voltage sensor %s is unavailable", self.voltage_sensor)
                return 0
            try:
                current_value = float(current_state.state)
                voltage_value = float(voltage_state.state)
                # Power (W) = Voltage (V) * Current (A)
                power_value = voltage_value * current_value
                # W to kWh: (W * hours) / 1000
                kwh_value = (power_value * 1) / 1000
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid current or voltage value: current=%s, voltage=%s", current_state.state, voltage_state.state)
                return 0

        else:
            _LOGGER.warning("No valid sensor provided for device %s", self.device_name)
            return 0

        # Calculate the cost using the tiered pricing structure
        cost = 0
        if kwh_value > 0:
            if kwh_value <= 50:
                cost = kwh_value * self.tier_1_rate
            elif kwh_value <= 100:
                cost = (50 * self.tier_1_rate) + ((kwh_value - 50) * self.tier_2_rate)
            elif kwh_value <= 200:
                cost = (50 * self.tier_1_rate) + (50 * self.tier_2_rate) + ((kwh_value - 100) * self.tier_3_rate)
            elif kwh_value <= 300:
                cost = (50 * self.tier_1_rate) + (50 * self.tier_2_rate) + (100 * self.tier_3_rate) + ((kwh_value - 200) * self.tier_4_rate)
            elif kwh_value <= 400:
                cost = (50 * self.tier_1_rate) + (50 * self.tier_2_rate) + (100 * self.tier_3_rate) + (100 * self.tier_4_rate) + ((kwh_value - 300) * self.tier_5_rate)
            else:
                cost = (50 * self.tier_1_rate) + (50 * self.tier_2_rate) + (100 * self.tier_3_rate) + (100 * self.tier_4_rate) + (100 * self.tier_5_rate) + ((kwh_value - 400) * self.tier_6_rate)

        # Add VAT if applicable
        if self.include_vat:
            cost = cost * (1 + self.vat_rate)

        return round(cost)

    async def async_update(self) -> None:
        """Update the sensor state."""
        self._attr_state = self.state