from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
import voluptuous as vol

from .const import DOMAIN, CONF_KWH_SENSOR, CONF_DEVICE_NAME

class ElectricityCostCalculatorVNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Electricity Cost Calculator VN."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        # Get all energy sensors (kWh) from the entity registry
        entity_registry = er.async_get(self.hass)
        energy_sensors = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("sensor.")
            and entry.device_class == "energy"
            and entry.unit_of_measurement == "kWh"
        ]

        if not energy_sensors:
            errors["base"] = "no_energy_sensors"

        if user_input is not None:
            # Validate the kWh sensor
            kwh_sensor = user_input[CONF_KWH_SENSOR]
            state = self.hass.states.get(kwh_sensor)
            if state is None or state.state in ("unknown", "unavailable"):
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
                    vol.Required(CONF_KWH_SENSOR): vol.In(energy_sensors),
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
        # Get all energy sensors (kWh) from the entity registry
        entity_registry = er.async_get(self.hass)
        energy_sensors = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.entity_id.startswith("sensor.")
            and entry.device_class == "energy"
            and entry.unit_of_measurement == "kWh"
        ]

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_KWH_SENSOR,
                        default=self.config_entry.data.get(CONF_KWH_SENSOR),
                    ): vol.In(energy_sensors),
                    vol.Required(
                        CONF_DEVICE_NAME,
                        default=self.config_entry.data.get(CONF_DEVICE_NAME),
                    ): str,
                }
            ),
        )