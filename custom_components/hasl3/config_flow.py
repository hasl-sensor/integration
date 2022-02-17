"""Config flow for the HASL component."""
import voluptuous
import logging
import uuid

from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback

from .const import (
    DOMAIN,
    HASL_VERSION,
    CONF_NAME,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_TYPE,
    CONF_INTEGRATION_LIST
)

from .config_schema import (
    hasl_base_config_schema,
    standard_config_option_schema,
    status_config_option_schema,
    vehiclelocation_config_option_schema,
    deviation_config_option_schema,
    route_config_option_schema
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.config")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HASL."""

    VERSION = HASL_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    # FIXME: DOES NOT ACTUALLY VALIDATE ANYTHING! WE NEED THIS! =)
    async def validate_input(self, data):
        """Validate input in step user"""

        if not data[CONF_INTEGRATION_TYPE] in CONF_INTEGRATION_LIST:
            raise InvalidIntegrationType

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

        name = user_input[CONF_NAME]
        del user_input[CONF_NAME]

        logger.debug(f"[setup_integration] Creating entry '{name}' with id {id}")
        try:
            tempResult = self.async_create_entry(title=name, data=user_input)
            logger.debug("[setup_integration] Entry creating succeeded")
            return tempResult
        except:
            logger.error(f"[setup_integration] Entry creation failed for '{name}' with id {id}")
            return self.async_abort(reason="not_supported")

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
