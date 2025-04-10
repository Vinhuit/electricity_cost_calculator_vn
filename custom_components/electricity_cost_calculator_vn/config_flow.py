from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, CONF_KWH_SENSOR, CONF_POWER_SENSOR, CONF_CURRENT_SENSOR, CONF_VOLTAGE_SENSOR, CONF_DEVICE_NAME

class ElectricityCostCalculatorVNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Electricity Cost Calculator VN."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.info("Starting Config Flow for Electricity Cost Calculator VN")
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
            _LOGGER.info("Received user input: %s", user_input)
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
                    await self.async_set_unique_id(user_input[CONF_DEVICE_NAME])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_DEVICE_NAME],
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_KWH_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_POWER_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_CURRENT_SENSOR): vol.In(all_sensors),
                    vol.Optional(CONF_VOLTAGE_SENSOR): vol.In(all_sensors),
                    vol.Required(CONF_DEVICE_NAME): str,
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

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        # Get all sensors from the entity registry
        entity_registry = er.async_get(self.hass)
        all_sensors = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("sensor.")
        ]

        all_sensors.insert(0, None)

        if user_input is not None:
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
                    vol.Required(
                        CONF_DEVICE_NAME,
                        default=self.config_entry.data.get(CONF_DEVICE_NAME),
                    ): str,
                }
            ),
        )