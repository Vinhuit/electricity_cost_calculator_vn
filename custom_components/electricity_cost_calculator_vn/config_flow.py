from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
import voluptuous as vol
import logging
import re

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
    DEFAULT_TIER_1_RATE,
    DEFAULT_TIER_2_RATE,
    DEFAULT_TIER_3_RATE,
    DEFAULT_TIER_4_RATE,
    DEFAULT_TIER_5_RATE,
    DEFAULT_TIER_6_RATE,
    DEFAULT_VAT_RATE,
    DEFAULT_COST_UNIT,
)

class ElectricityCostCalculatorVNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Electricity Cost Calculator VN."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    def _clean_numeric_input(self, value):
        """Clean a numeric input by removing whitespace and common formatting characters."""
        if value is None:
            return None
        # Convert to string and strip whitespace
        value = str(value).strip()
        # Remove common formatting characters (e.g., commas, spaces)
        value = re.sub(r"[^\d.-]", "", value)
        return value

    async def async_step_user(self, user_input=None):
        """Handle the initial step: sensor and device name selection."""
        _LOGGER.info("Starting Config Flow for Electricity Cost Calculator VN - Step 1")
        errors = {}

        # Get all sensors from the entity registry
        entity_registry = er.async_get(self.hass)
        all_sensors = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("sensor.")
        ]

        # Add a "None" option for optional fields
        all_sensors.insert(0, None)

        if not all_sensors[1:]:  # Check if there are any sensors (excluding None)
            errors["base"] = "no_sensors"

        if user_input is not None:
            _LOGGER.info("Received user input (Step 1): %s", user_input)
            # Validate that at least one sensor type is provided
            if not (user_input.get(CONF_KWH_SENSOR) or user_input.get(CONF_POWER_SENSOR) or (user_input.get(CONF_CURRENT_SENSOR) and user_input.get(CONF_VOLTAGE_SENSOR))):
                errors["base"] = "no_sensor_selected"
            else:
                # Validate the selected sensors
                for sensor_type, sensor_id in [
                    (CONF_KWH_SENSOR, user_input.get(CONF_KWH_SENSOR)),
                    (CONF_POWER_SENSOR, user_input.get(CONF_POWER_SENSOR)),
                    (CONF_CURRENT_SENSOR, user_input.get(CONF_CURRENT_SENSOR)),
                    (CONF_VOLTAGE_SENSOR, user_input.get(CONF_VOLTAGE_SENSOR)),
                ]:
                    if sensor_id:
                        state = self.hass.states.get(sensor_id)
                        if state is None or state.state in ("unknown", "unavailable"):
                            errors[sensor_type] = "invalid_sensor"
                            break

                if not errors:
                    # Store the user input from this step
                    self._data.update(user_input)
                    # Generate a default device name if none is provided
                    device_name = self._data.get(CONF_DEVICE_NAME)
                    if not device_name:
                        for sensor_id in [
                            self._data.get(CONF_KWH_SENSOR),
                            self._data.get(CONF_POWER_SENSOR),
                            self._data.get(CONF_CURRENT_SENSOR),
                            self._data.get(CONF_VOLTAGE_SENSOR),
                        ]:
                            if sensor_id:
                                device_name = sensor_id.replace("sensor.", "").replace("_", " ").title()
                                break
                        if not device_name:
                            device_name = "Electricity Cost Device"
                    self._data[CONF_DEVICE_NAME] = device_name

                    # Proceed to the pricing step
                    return await self.async_step_pricing()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_KWH_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_POWER_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_CURRENT_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_VOLTAGE_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_DEVICE_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_pricing(self, user_input=None):
        """Handle the pricing configuration step."""
        _LOGGER.info("Config Flow for Electricity Cost Calculator VN - Step 2: Pricing")
        errors = {}

        if user_input is not None:
            _LOGGER.info("Received user input (Step 2): %s", user_input)
            # Validate the pricing inputs (ensure they are positive numbers)
            for key in [
                CONF_TIER_1_RATE,
                CONF_TIER_2_RATE,
                CONF_TIER_3_RATE,
                CONF_TIER_4_RATE,
                CONF_TIER_5_RATE,
                CONF_TIER_6_RATE,
                CONF_VAT_RATE,
            ]:
                value = user_input.get(key)
                # Skip validation for optional fields if not provided
                if key != CONF_TIER_1_RATE and key != CONF_VAT_RATE and (value is None or str(value).strip() == ""):
                    continue
                if value is None or str(value).strip() == "":
                    errors[key] = "missing_value"
                    continue
                # Clean the input
                cleaned_value = self._clean_numeric_input(value)
                try:
                    float_value = float(cleaned_value)
                    if float_value < 0:
                        errors[key] = "negative_value"
                    # Update the user_input with the cleaned float value
                    user_input[key] = float_value
                except (ValueError, TypeError):
                    _LOGGER.error("Invalid value for %s: %s (cleaned: %s)", key, value, cleaned_value)
                    errors[key] = "invalid_number"

            # Set optional tier rates to tier_1_rate if not provided
            tier_1_rate = user_input.get(CONF_TIER_1_RATE)
            if tier_1_rate is not None:  # Ensure tier_1_rate is valid
                for key in [
                    CONF_TIER_2_RATE,
                    CONF_TIER_3_RATE,
                    CONF_TIER_4_RATE,
                    CONF_TIER_5_RATE,
                    CONF_TIER_6_RATE,
                ]:
                    if key not in user_input or user_input[key] is None or str(user_input[key]).strip() == "":
                        user_input[key] = tier_1_rate

            # Validate the cost unit (ensure it's not empty)
            cost_unit = user_input.get(CONF_COST_UNIT)
            if not cost_unit or str(cost_unit).strip() == "":
                errors[CONF_COST_UNIT] = "empty_cost_unit"

            if not errors:
                # Store the pricing data
                self._data.update(user_input)
                # Set the unique ID and create the config entry
                await self.async_set_unique_id(self._data[CONF_DEVICE_NAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=self._data[CONF_DEVICE_NAME],
                    data=self._data,
                )

        return self.async_show_form(
            step_id="pricing",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TIER_1_RATE, default=DEFAULT_TIER_1_RATE): str,
                    vol.Optional(CONF_TIER_2_RATE, default=DEFAULT_TIER_2_RATE): str,
                    vol.Optional(CONF_TIER_3_RATE, default=DEFAULT_TIER_3_RATE): str,
                    vol.Optional(CONF_TIER_4_RATE, default=DEFAULT_TIER_4_RATE): str,
                    vol.Optional(CONF_TIER_5_RATE, default=DEFAULT_TIER_5_RATE): str,
                    vol.Optional(CONF_TIER_6_RATE, default=DEFAULT_TIER_6_RATE): str,
                    vol.Required(CONF_VAT_RATE, default=DEFAULT_VAT_RATE): str,
                    vol.Required(CONF_COST_UNIT, default=DEFAULT_COST_UNIT): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    def _clean_numeric_input(self, value):
        """Clean a numeric input by removing whitespace and common formatting characters."""
        if value is None:
            return None
        # Convert to string and strip whitespace
        value = str(value).strip()
        # Remove common formatting characters (e.g., commas, spaces)
        value = re.sub(r"[^\d.-]", "", value)
        return value

    async def async_step_init(self, user_input=None):
        """Manage the options: sensors, device name, pricing, and cost unit."""
        # Get all sensors from the entity registry
        entity_registry = er.async_get(self.hass)
        all_sensors = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("sensor.")
        ]

        all_sensors.insert(0, None)

        if user_input is not None:
            # Validate the pricing inputs (ensure they are positive numbers)
            errors = {}
            for key in [
                CONF_TIER_1_RATE,
                CONF_TIER_2_RATE,
                CONF_TIER_3_RATE,
                CONF_TIER_4_RATE,
                CONF_TIER_5_RATE,
                CONF_TIER_6_RATE,
                CONF_VAT_RATE,
            ]:
                value = user_input.get(key)
                # Skip validation for optional fields if not provided
                if key != CONF_TIER_1_RATE and key != CONF_VAT_RATE and (value is None or str(value).strip() == ""):
                    continue
                if value is None or str(value).strip() == "":
                    errors[key] = "missing_value"
                    continue
                # Clean the input
                cleaned_value = self._clean_numeric_input(value)
                try:
                    float_value = float(cleaned_value)
                    if float_value < 0:
                        errors[key] = "negative_value"
                    # Update the user_input with the cleaned float value
                    user_input[key] = float_value
                except (ValueError, TypeError):
                    _LOGGER.error("Invalid value for %s: %s (cleaned: %s)", key, value, cleaned_value)
                    errors[key] = "invalid_number"

            # Set optional tier rates to tier_1_rate if not provided
            tier_1_rate = user_input.get(CONF_TIER_1_RATE)
            if tier_1_rate is not None:  # Ensure tier_1_rate is valid
                for key in [
                    CONF_TIER_2_RATE,
                    CONF_TIER_3_RATE,
                    CONF_TIER_4_RATE,
                    CONF_TIER_5_RATE,
                    CONF_TIER_6_RATE,
                ]:
                    if key not in user_input or user_input[key] is None or str(user_input[key]).strip() == "":
                        user_input[key] = tier_1_rate

            # Validate the cost unit (ensure it's not empty)
            cost_unit = user_input.get(CONF_COST_UNIT)
            if not cost_unit or str(cost_unit).strip() == "":
                errors[CONF_COST_UNIT] = "empty_cost_unit"

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(
                                CONF_KWH_SENSOR,
                                default=self.config_entry.data.get(CONF_KWH_SENSOR),
                            ): vol.In(all_sensors),
                            vol.Optional(
                                CONF_POWER_SENSOR,
                                default=self.config_entry.data.get(CONF_POWER_SENSOR),
                            ): vol.In(all_sensors),
                            vol.Optional(
                                CONF_CURRENT_SENSOR,
                                default=self.config_entry.data.get(CONF_CURRENT_SENSOR),
                            ): vol.In(all_sensors),
                            vol.Optional(
                                CONF_VOLTAGE_SENSOR,
                                default=self.config_entry.data.get(CONF_VOLTAGE_SENSOR),
                            ): vol.In(all_sensors),
                            vol.Optional(
                                CONF_DEVICE_NAME,
                                default=self.config_entry.data.get(CONF_DEVICE_NAME),
                            ): str,
                            vol.Required(
                                CONF_TIER_1_RATE,
                                default=self.config_entry.data.get(CONF_TIER_1_RATE, DEFAULT_TIER_1_RATE),
                            ): str,
                            vol.Optional(
                                CONF_TIER_2_RATE,
                                default=self.config_entry.data.get(CONF_TIER_2_RATE, DEFAULT_TIER_2_RATE),
                            ): str,
                            vol.Optional(
                                CONF_TIER_3_RATE,
                                default=self.config_entry.data.get(CONF_TIER_3_RATE, DEFAULT_TIER_3_RATE),
                            ): str,
                            vol.Optional(
                                CONF_TIER_4_RATE,
                                default=self.config_entry.data.get(CONF_TIER_4_RATE, DEFAULT_TIER_4_RATE),
                            ): str,
                            vol.Optional(
                                CONF_TIER_5_RATE,
                                default=self.config_entry.data.get(CONF_TIER_5_RATE, DEFAULT_TIER_5_RATE),
                            ): str,
                            vol.Optional(
                                CONF_TIER_6_RATE,
                                default=self.config_entry.data.get(CONF_TIER_6_RATE, DEFAULT_TIER_6_RATE),
                            ): str,
                            vol.Required(
                                CONF_VAT_RATE,
                                default=self.config_entry.data.get(CONF_VAT_RATE, DEFAULT_VAT_RATE),
                            ): str,
                            vol.Required(
                                CONF_COST_UNIT,
                                default=self.config_entry.data.get(CONF_COST_UNIT, DEFAULT_COST_UNIT),
                            ): str,
                        }
                    ),
                    errors=errors,
                )

            # Generate a default device name if none is provided
            device_name = user_input.get(CONF_DEVICE_NAME)
            if not device_name:
                for sensor_id in [
                    user_input.get(CONF_KWH_SENSOR),
                    user_input.get(CONF_POWER_SENSOR),
                    user_input.get(CONF_CURRENT_SENSOR),
                    user_input.get(CONF_VOLTAGE_SENSOR),
                ]:
                    if sensor_id:
                        device_name = sensor_id.replace("sensor.", "").replace("_", " ").title()
                        break
                if not device_name:
                    device_name = "Electricity Cost Device"
            user_input[CONF_DEVICE_NAME] = device_name

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KWH_SENSOR,
                        default=self.config_entry.data.get(CONF_KWH_SENSOR),
                    ): vol.In(all_sensors),
                    vol.Optional(
                        CONF_POWER_SENSOR,
                        default=self.config_entry.data.get(CONF_POWER_SENSOR),
                    ): vol.In(all_sensors),
                    vol.Optional(
                        CONF_CURRENT_SENSOR,
                        default=self.config_entry.data.get(CONF_CURRENT_SENSOR),
                    ): vol.In(all_sensors),
                    vol.Optional(
                        CONF_VOLTAGE_SENSOR,
                        default=self.config_entry.data.get(CONF_VOLTAGE_SENSOR),
                    ): vol.In(all_sensors),
                    vol.Optional(
                        CONF_DEVICE_NAME,
                        default=self.config_entry.data.get(CONF_DEVICE_NAME),
                    ): str,
                    vol.Required(
                        CONF_TIER_1_RATE,
                        default=self.config_entry.data.get(CONF_TIER_1_RATE, DEFAULT_TIER_1_RATE),
                    ): str,
                    vol.Optional(
                        CONF_TIER_2_RATE,
                        default=self.config_entry.data.get(CONF_TIER_2_RATE, DEFAULT_TIER_2_RATE),
                    ): str,
                    vol.Optional(
                        CONF_TIER_3_RATE,
                        default=self.config_entry.data.get(CONF_TIER_3_RATE, DEFAULT_TIER_3_RATE),
                    ): str,
                    vol.Optional(
                        CONF_TIER_4_RATE,
                        default=self.config_entry.data.get(CONF_TIER_4_RATE, DEFAULT_TIER_4_RATE),
                    ): str,
                    vol.Optional(
                        CONF_TIER_5_RATE,
                        default=self.config_entry.data.get(CONF_TIER_5_RATE, DEFAULT_TIER_5_RATE),
                    ): str,
                    vol.Optional(
                        CONF_TIER_6_RATE,
                        default=self.config_entry.data.get(CONF_TIER_6_RATE, DEFAULT_TIER_6_RATE),
                    ): str,
                    vol.Required(
                        CONF_VAT_RATE,
                        default=self.config_entry.data.get(CONF_VAT_RATE, DEFAULT_VAT_RATE),
                    ): str,
                    vol.Required(
                        CONF_COST_UNIT,
                        default=self.config_entry.data.get(CONF_COST_UNIT, DEFAULT_COST_UNIT),
                    ): str,
                }
            ),
        )