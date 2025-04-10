from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    CONF_KWH_SENSOR,
    CONF_DEVICE_NAME,
    TIER_1_RATE,
    TIER_2_RATE,
    TIER_3_RATE,
    TIER_4_RATE,
    TIER_5_RATE,
    TIER_6_RATE,
    VAT_RATE,
    SENSOR_COST,
    SENSOR_COST_WITH_VAT,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    kwh_sensor = entry.data[CONF_KWH_SENSOR]
    device_name = entry.data[CONF_DEVICE_NAME]

    # Create two sensors: cost without VAT and cost with VAT
    sensors = [
        ElectricityCostSensor(hass, entry, kwh_sensor, device_name, False),
        ElectricityCostSensor(hass, entry, kwh_sensor, device_name, True),
    ]
    async_add_entities(sensors)

class ElectricityCostSensor(SensorEntity):
    """Representation of an electricity cost sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, kwh_sensor: str, device_name: str, include_vat: bool):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.kwh_sensor = kwh_sensor
        self.device_name = device_name
        self.include_vat = include_vat

        # Sensor attributes
        self._attr_name = (
            f"{device_name} Electricity Cost{' with VAT' if include_vat else ''}"
        )
        self._attr_unique_id = (
            f"{entry.entry_id}_{SENSOR_COST_WITH_VAT if include_vat else SENSOR_COST}"
        )
        self._attr_unit_of_measurement = "VND"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        # Get the kWh value
        kwh = self.hass.states.get(self.kwh_sensor)
        if kwh is None or kwh.state in ("unknown", "unavailable"):
            return 0

        try:
            kwh_value = float(kwh.state)
        except (ValueError, TypeError):
            return 0

        # Calculate the cost using the tiered pricing structure
        cost = 0
        if kwh_value > 0:
            if kwh_value <= 50:
                cost = kwh_value * TIER_1_RATE
            elif kwh_value <= 100:
                cost = (50 * TIER_1_RATE) + ((kwh_value - 50) * TIER_2_RATE)
            elif kwh_value <= 200:
                cost = (50 * TIER_1_RATE) + (50 * TIER_2_RATE) + ((kwh_value - 100) * TIER_3_RATE)
            elif kwh_value <= 300:
                cost = (50 * TIER_1_RATE) + (50 * TIER_2_RATE) + (100 * TIER_3_RATE) + ((kwh_value - 200) * TIER_4_RATE)
            elif kwh_value <= 400:
                cost = (50 * TIER_1_RATE) + (50 * TIER_2_RATE) + (100 * TIER_3_RATE) + (100 * TIER_4_RATE) + ((kwh_value - 300) * TIER_5_RATE)
            else:
                cost = (50 * TIER_1_RATE) + (50 * TIER_2_RATE) + (100 * TIER_3_RATE) + (100 * TIER_4_RATE) + (100 * TIER_5_RATE) + ((kwh_value - 400) * TIER_6_RATE)

        # Add VAT if applicable
        if self.include_vat:
            cost = cost * (1 + VAT_RATE)

        return round(cost)

    async def async_update(self) -> None:
        """Update the sensor state."""
        self._attr_state = self.state