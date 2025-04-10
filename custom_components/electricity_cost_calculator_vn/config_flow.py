from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN, CONF_KWH_SENSOR, CONF_DEVICE_NAME

class ElectricityCostCalculatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Electricity Cost Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            kwh_sensor = user_input[CONF_KWH_SENSOR]
            if not await self.hass.async_add_executor_job(
                lambda: self.hass.states.get(kwh_sensor) is not None
            ):
                errors["base"] = "invalid_sensor"
            else:
                # Use the device name as the unique ID
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
                    vol.Required(CONF_KWH_SENSOR): str,
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
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_KWH_SENSOR,
                        default=self.config_entry.data.get(CONF_KWH_SENSOR),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_NAME,
                        default=self.config_entry.data.get(CONF_DEVICE_NAME),
                    ): str,
                }
            ),
        )