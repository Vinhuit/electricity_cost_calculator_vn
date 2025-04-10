import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
    DEFAULT_TIER_1_RATE,
    DEFAULT_TIER_2_RATE,
    DEFAULT_TIER_3_RATE,
    DEFAULT_TIER_4_RATE,
    DEFAULT_TIER_5_RATE,
    DEFAULT_TIER_6_RATE,
    DEFAULT_VAT_RATE,
    DEFAULT_COST_UNIT,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Electricity Cost Calculator VN integration."""
    _LOGGER.info("Setting up Electricity Cost Calculator VN integration")
    # If the integration is configured via YAML, set up a config entry
    if DOMAIN in config:
        for entry in config[DOMAIN]:
            # Generate a default device name if none is provided
            device_name = entry.get(CONF_DEVICE_NAME)
            if not device_name:
                for sensor_key in [CONF_KWH_SENSOR, CONF_POWER_SENSOR, CONF_CURRENT_SENSOR, CONF_VOLTAGE_SENSOR]:
                    sensor_id = entry.get(sensor_key)
                    if sensor_id:
                        device_name = sensor_id.replace("sensor.", "").replace("_", " ").title()
                        break
                if not device_name:
                    device_name = "Electricity Cost Device"
            entry[CONF_DEVICE_NAME] = device_name

            # Add default pricing tiers, VAT rate, and cost unit if not provided
            entry.setdefault(CONF_TIER_1_RATE, DEFAULT_TIER_1_RATE)
            entry.setdefault(CONF_TIER_2_RATE, DEFAULT_TIER_2_RATE)
            entry.setdefault(CONF_TIER_3_RATE, DEFAULT_TIER_3_RATE)
            entry.setdefault(CONF_TIER_4_RATE, DEFAULT_TIER_4_RATE)
            entry.setdefault(CONF_TIER_5_RATE, DEFAULT_TIER_5_RATE)
            entry.setdefault(CONF_TIER_6_RATE, DEFAULT_TIER_6_RATE)
            entry.setdefault(CONF_VAT_RATE, DEFAULT_VAT_RATE)
            entry.setdefault(CONF_COST_UNIT, DEFAULT_COST_UNIT)

            # Validate pricing tiers and VAT rate
            for key in [
                CONF_TIER_1_RATE,
                CONF_TIER_2_RATE,
                CONF_TIER_3_RATE,
                CONF_TIER_4_RATE,
                CONF_TIER_5_RATE,
                CONF_TIER_6_RATE,
                CONF_VAT_RATE,
            ]:
                value = entry.get(key)
                try:
                    float_value = float(value)
                    if float_value < 0:
                        _LOGGER.error("Invalid value for %s in YAML config: %s (must be non-negative)", key, value)
                        return False
                except (ValueError, TypeError):
                    _LOGGER.error("Invalid value for %s in YAML config: %s (must be a number)", key, value)
                    return False

            # Validate cost unit
            cost_unit = entry.get(CONF_COST_UNIT)
            if not cost_unit or str(cost_unit).strip() == "":
                _LOGGER.error("Cost unit in YAML config cannot be empty")
                return False

            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": "import"}, data=entry
                )
            )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Electricity Cost Calculator VN from a config entry."""
    _LOGGER.info("Setting up Electricity Cost Calculator VN with entry: %s", entry.data)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Electricity Cost Calculator VN entry: %s", entry.entry_id)
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True