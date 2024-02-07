"""Config flow for the HASL component."""
import voluptuous
import logging
import uuid

from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback

from .const import (
    DOMAIN,
    SCHEMA_VERSION,
    CONF_NAME,
    SENSOR_RRARR,
    SENSOR_RRROUTE,
    SENSOR_RRDEP,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_TYPE,
    CONF_INTEGRATION_LIST,
)

from .config_schema import (
    hasl_base_config_schema,
    standard_config_option_schema,
    status_config_option_schema,
    vehiclelocation_config_option_schema,
    deviation_config_option_schema,
    route_config_option_schema,
    rrdep_config_option_schema,
    rrarr_config_option_schema,
    rrroute_config_option_schema
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.config")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HASL."""

    VERSION = SCHEMA_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    # FIXME: DOES NOT ACTUALLY VALIDATE ANYTHING! WE NEED THIS! =)
    async def validate_input(self, data):
        """Validate input in step user"""

        if not data[CONF_INTEGRATION_TYPE] in CONF_INTEGRATION_LIST:
            raise InvalidIntegrationType

        return data

    async def validate_config(self, data):
        """Validate input in step config"""

        return data

    async def async_step_user(self, user_input):
        """Handle the initial step."""
        logger.debug("[setup_integration] Entered")
        errors = {}

        if user_input is None:
            logger.debug("[async_step_user] No user input so showing creation form")
            return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(hasl_base_config_schema(user_input, True)))

        try:
            user_input = await self.validate_input(user_input)
        except InvalidIntegrationType:
            errors["base"] = "invalid_integration_type"
            logger.debug("[setup_integration(validate)] Invalid integration type")
            return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(hasl_base_config_schema(user_input, True)), errors=errors)
        except InvalidIntegrationName:
            errors["base"] = "invalid_integration_name"
            logger.debug("[setup_integration(validate)] Invalid integration type")
            return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(hasl_base_config_schema(user_input, True)), errors=errors)
        except Exception:  # pylint: disable=broad-except
            errors["base"] = "unknown_exception"
            logger.debug("[setup_integration(validate)] Unknown exception occured")
            return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(hasl_base_config_schema(user_input, True)), errors=errors)

        id = str(uuid.uuid4())
        await self.async_set_unique_id(id)
        user_input[CONF_INTEGRATION_ID] = id
        self._userdata = user_input

        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_STANDARD:
            schema = standard_config_option_schema()
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:
            schema = status_config_option_schema()
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_VEHICLE_LOCATION:
            schema = vehiclelocation_config_option_schema()
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_DEVIATION:
            schema = deviation_config_option_schema()
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_ROUTE:
            schema = route_config_option_schema()
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_RRDEP:
            schema = rrdep_config_option_schema()         
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_RRARR:
            schema = rrarr_config_option_schema()         
        if user_input[CONF_INTEGRATION_TYPE] == SENSOR_RRROUTE:
            schema = rrroute_config_option_schema()         

        return self.async_show_form(step_id="config", data_schema=voluptuous.Schema(schema), errors=errors)

    async def async_step_config(self, user_input):
        """Handle a flow initialized by the user."""
        logger.debug("[setup_integration_config] Entered")
        errors = {}

        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_STANDARD:
            schema = standard_config_option_schema(user_input)
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:
            schema = status_config_option_schema(user_input)
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_VEHICLE_LOCATION:
            schema = vehiclelocation_config_option_schema(user_input)
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_DEVIATION:
            schema = deviation_config_option_schema(user_input)
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_ROUTE:
            schema = route_config_option_schema(user_input)
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_RRDEP:
            schema = rrdep_config_option_schema(user_input)         
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_RRARR:
            schema = rrarr_config_option_schema(user_input)         
        if self._userdata[CONF_INTEGRATION_TYPE] == SENSOR_RRROUTE:
            schema = rrroute_config_option_schema(user_input)         

        logger.debug(f"[setup_integration_config] Schema is {self._userdata[CONF_INTEGRATION_TYPE]}")

        # FIXME: DOES NOT ACTUALLY VALIDATE ANYTHING! WE NEED THIS! =)
        if user_input is not None:
            try:
                user_input = await self.validate_config(user_input)
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown_exception"
                logger.debug("[setup_integration_config(validate)] Unknown exception occured")
            else:
                try:
                    name = self._userdata[CONF_NAME]
                    del self._userdata[CONF_NAME]
                    logger.debug(f"[setup_integration_config] Creating entry '{name}' with id {self._userdata[CONF_INTEGRATION_ID]}")

                    self._userdata.update(user_input)

                    # split configuration into data and options
                    data = {
                        CONF_INTEGRATION_ID: self._userdata[CONF_INTEGRATION_ID],
                        CONF_INTEGRATION_TYPE: self._userdata[CONF_INTEGRATION_TYPE],
                    }
                    options = {k: v for k, v in self._userdata.items() if k not in data}

                    tempresult = self.async_create_entry(title=name, data=data, options=options)
                    logger.debug("[setup_integration_config] Entry creating succeeded")
                    return tempresult
                except:
                    logger.error(f"[setup_integration] Entry creation failed for '{name}' with id {self._userdata[CONF_INTEGRATION_ID]}")
                    return self.async_abort(reason="not_supported")

            logger.debug("[setup_integration_config] Validation errors encountered so showing options form again")
            return self.async_show_form(step_id="config", data_schema=voluptuous.Schema(schema), errors=errors)

        logger.debug("[setup_integration_config] No user input so showing options form")
        return self.async_show_form(step_id="config", data_schema=voluptuous.Schema(schema))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """HASL config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HASL options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def validate_input(self, data):
        """Validate input in step user"""
        # FIXME: DOES NOT ACTUALLY VALIDATE ANYTHING! WE NEED THIS! =)

        return data

    async def async_step_user(self, user_input):
        """Handle a flow initialized by the user."""
        logger.debug("[integration_options] Entered")
        errors = {}

        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_STANDARD:
            schema = standard_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:
            schema = status_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_VEHICLE_LOCATION:
            schema = vehiclelocation_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_DEVIATION:
            schema = deviation_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_ROUTE:
            schema = route_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_RRDEP:
            schema = rrdep_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_RRARR:
            schema = rrarr_config_option_schema(self.config_entry.options)
        if self.config_entry.data[CONF_INTEGRATION_TYPE] == SENSOR_RRROUTE:
            schema = rrroute_config_option_schema(self.config_entry.options)

        logger.debug(f"[integration_options] Schema is {self.config_entry.data[CONF_INTEGRATION_TYPE]}")

        # FIXME: DOES NOT ACTUALLY VALIDATE ANYTHING! WE NEED THIS! =)
        if user_input is not None:
            try:
                user_input = await self.validate_input(user_input)
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown_exception"
                logger.debug("[integration_options(validate)] Unknown exception occured")
            else:
                try:
                    tempresult = self.async_create_entry(title=self.config_entry.title, data=user_input)
                    logger.debug("[integration_options] Entry update succeeded")
                    return tempresult
                except:
                    logger.error("[integration_options] Unknown exception occured")

            logger.debug("[integration_options] Validation errors encountered so showing options form again")
            return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(schema), errors=errors)

        logger.debug("[integration_options] No user input so showing options form")
        return self.async_show_form(step_id="user", data_schema=voluptuous.Schema(schema))


class InvalidIntegrationType(HomeAssistantError):
    """Error to indicate the integration is not of a valid type."""


class InvalidIntegrationName(HomeAssistantError):
    """Error to indicate that the name is not a legal name."""
