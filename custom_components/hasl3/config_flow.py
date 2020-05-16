"""Adds config flow for HASL."""
# pylint: disable=dangerous-default-value
import logging
import voluptuous as vol
import uuid

from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_NAME,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_TYPE
)
    
from .config_schema import (
    hasl_base_config_schema,
    standard_config_option_schema,
    status_config_option_schema,
    trainlocation_config_option_schema,
    deviation_config_option_schema
)
from .globals import get_worker


class HaslFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HASL."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input={}):
        """Handle a flow initialized by the user."""
        self._errors = {}
        #if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")
        #if self.hass.data.get(DOMAIN):
        #    return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            user_input[CONF_INTEGRATION_ID] = str(uuid.uuid4())
            setname = user_input[CONF_NAME]
            del user_input[CONF_NAME]
            return self.async_create_entry(title=setname, data=user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(hasl_base_config_schema(user_input, True)),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HaslOptionsFlowHandler(config_entry)

    async def async_step_import(self, user_input):
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})


class HaslOptionsFlowHandler(config_entries.OptionsFlow):
    """HASL config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HASL options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        worker = get_worker()
        if user_input is not None:
            return self.async_create_entry(title=self.config_entry.title, data=user_input)

        if worker.configuration.config_type == "yaml":
            schema = {vol.Optional("not_in_use", default=""): str}
        else:
            if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_STANDARD:            
                schema = standard_config_option_schema(self.config_entry.options)
            if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:            
                schema = status_config_option_schema(self.config_entry.options)
            if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_VEHICLE_LOCATION:            
                schema = trainlocation_config_option_schema(self.config_entry.options)
            if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_DEVIATION:            
                schema = deviation_config_option_schema(self.config_entry.options)

        return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))
