"""Config flow for the HASL component."""

import logging
import uuid
from functools import partial
from typing import Any, Awaitable, Callable, cast

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_POLL,
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigSubentryFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector as sel
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)
from tsl.clients.common import ClientException
from tsl.clients.journey import JourneyPlannerClient
from tsl.utils import global_id_to_site_id

from .rrapi.model import LocationSearchType

from . import const
from .config_schema import API_KEY_CONFIG_SCHEMA, NAME_CONFIG_SCHEMA, schema_by_type
from .const import (
    CONF_API_KEY,
    CONF_DESTINATION,
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_LIST,
    CONF_INTEGRATION_TYPE,
    CONF_SITE_ID,
    CONF_SOURCE,
    DOMAIN,
    SCHEMA_VERSION,
    SENSOR_DEPARTURE,
    SENSOR_RESROBOT_DEPARTURE,
    SENSOR_RESROBOT_ROUTE,
    SENSOR_ROUTE,
    SENSOR_STATUS,
    SERVICE_RESROBOT_KEY,
)
from .rrapi.client import ResRobotClient
from .utils import DestinationInvalid, SourceInvalid, siteid_or_coords

logger = logging.getLogger(__name__)


async def get_schema_by_handler(handler: SchemaCommonFlowHandler):
    """Return the schema for the handler."""
    parent_handler = cast(SchemaOptionsFlowHandler, handler.parent_handler)
    return schema_by_type(parent_handler.config_entry.data[CONF_INTEGRATION_TYPE])


OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(next_step="user"),  # redirect to 'user' step
    "user": SchemaFlowFormStep(get_schema_by_handler),
}

LOOKUP_SEARCH_KEY = "lookup_search_key"

UserInputType = dict[str, Any] | None
AsyncCallable = Callable[..., Awaitable[Any]]


class LocationLookupMixin:
    """
    Mixin to add location lookup functionality to a config flow.
    """

    _options: dict[str, Any]
    async_show_form: Callable[..., Any]

    async def _find_location(
        self,
        step_id: str,
        step_call: AsyncCallable,
        next_step: AsyncCallable,
        search_call: Callable[[str], Awaitable[list[sel.SelectOptionDict]]],
        target_field: str,
        target_field_setter: Callable[[str], None] | None = None,
        user_input: UserInputType = None,
    ):
        if not user_input or (search_key := user_input.get(LOOKUP_SEARCH_KEY)) is None:
            return self.async_show_form(
                step_id=step_id,
                data_schema=vol.Schema(
                    {
                        vol.Required(LOOKUP_SEARCH_KEY): str,
                    }
                ),
            )

        # if the search key has changed, reset the site id
        if last_search_key := self._options.get(LOOKUP_SEARCH_KEY):
            if last_search_key != search_key:
                self._options.pop(LOOKUP_SEARCH_KEY, None)
                user_input.pop(target_field, None)
        else:
            self._options[LOOKUP_SEARCH_KEY] = search_key

        # the result was chosen
        if site_id := user_input.get(target_field):
            self._options.pop(LOOKUP_SEARCH_KEY, None)
            if target_field_setter:
                target_field_setter(site_id)
            else:
                self._options[target_field] = site_id
            return await next_step()

        # perform the search

        try:
            stop_options = await search_call(search_key)
        except Exception:
            return await step_call({"errors": {"base": "lookup_failed"}})

        if first_option := next(iter(stop_options), None):
            first_option = first_option["value"]

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(LOOKUP_SEARCH_KEY, default=search_key): str,
                    vol.Optional(
                        target_field,  # default=first_option or vol.UNDEFINED
                        description={"suggested_value": first_option},
                    ): sel.SelectSelector(
                        sel.SelectSelectorConfig(
                            options=stop_options,
                            translation_key=target_field,
                            mode=sel.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )


class ConfigFlowHandler(ConfigFlow, LocationLookupMixin, domain=DOMAIN):
    """Handle a config flow for HASL."""

    VERSION = SCHEMA_VERSION
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    new_sensors = [
        SENSOR_DEPARTURE,
        SENSOR_STATUS,
        SENSOR_ROUTE,
        SERVICE_RESROBOT_KEY,
    ]

    def __init__(self):
        self._options = {}

        # plug in the handlers for the legacy integration types
        for step in (x for x in CONF_INTEGRATION_LIST if x not in self.new_sensors):
            setattr(self, f"async_step_{step}", partial(self.async_step_legacy, step))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        """Get the options flow for this handler."""
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)

    @classmethod
    @callback
    def async_supports_options_flow(cls, config_entry: ConfigEntry) -> bool:
        """Return if the config entry supports an options flow."""
        return config_entry.data.get(CONF_INTEGRATION_TYPE) != SERVICE_RESROBOT_KEY

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        if _type := config_entry.data.get(CONF_INTEGRATION_TYPE):
            if _type == SERVICE_RESROBOT_KEY:
                return {
                    SERVICE_RESROBOT_KEY: ResrobotSubentryFlowHandler,
                }
        return {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        # TODO: add back legacy sensor types
        return self.async_show_menu(step_id="user", menu_options=self.new_sensors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        entry_type = self._get_reconfigure_entry().data.get(CONF_INTEGRATION_TYPE)
        if entry_type == SERVICE_RESROBOT_KEY:
            return await self.async_step_resrobot_key(user_input)

        # HACK: since config expects this to work
        self._options[CONF_INTEGRATION_TYPE] = entry_type
        return await self.async_step_config(user_input)

    async def async_step_resrobot_key(self, user_input: dict[str, Any] | None = None):
        """Handle the ResRobot API key configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id=SERVICE_RESROBOT_KEY,
                data_schema=API_KEY_CONFIG_SCHEMA,
            )

        # validate the API key
        session = async_get_clientsession(self.hass)
        client = ResRobotClient(session, user_input[const.CONF_API_KEY])

        try:
            await client.find_stop_location("Slussen")
        except Exception:
            return self.async_show_form(
                step_id=SERVICE_RESROBOT_KEY,
                data_schema=API_KEY_CONFIG_SCHEMA,
                errors={"base": "invalid_api_key"},
            )

        # TODO: consider using `next_flow` to immediately start the subflow
        # for creating a sensor, instead of going back to the menu
        return self.async_create_entry(
            title="ResRobot",
            data={CONF_INTEGRATION_TYPE: SERVICE_RESROBOT_KEY, **user_input},
            description="Configured ResRobot API key",
        )

    async def async_step_departure_v2(self, user_input: dict[str, Any] | None = None):
        self._options[CONF_INTEGRATION_TYPE] = SENSOR_DEPARTURE

        return self.async_show_menu(
            step_id="departure_v2", menu_options=["lookup_location", "name"]
        )

    async def async_step_status_v2(self, user_input: dict[str, Any] | None = None):
        self._options[CONF_INTEGRATION_TYPE] = SENSOR_STATUS

        # TODO: evaluate, if we need to check for existing status sensors
        # check if there any other configured status sensors
        # entries = self.hass.config_entries.async_entries(DOMAIN)
        # for entry in entries:
        #     if entry.data[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:
        #         raise SchemaFlowError("only_one_status_sensor")

        return await self.async_step_name()

    async def async_step_route_v2(self, user_input: dict[str, Any] | None = None):
        self._options[CONF_INTEGRATION_TYPE] = SENSOR_ROUTE

        return await self.async_step_name()

    async def _find_stops(self, search_key: str) -> list[sel.SelectOptionDict]:
        session = async_get_clientsession(self.hass)
        client = JourneyPlannerClient(session)
        stops = await client.find_stops(search_key)

        return [
            {"value": str(global_id_to_site_id(stop["id"])), "label": stop["name"]}
            for stop in stops
        ]

    async def async_step_lookup_location(
        self, user_input: dict[str, Any] | None = None
    ):
        return await self._find_location(
            step_id="lookup_location",
            step_call=self.async_step_lookup_location,
            next_step=self.async_step_name,
            search_call=self._find_stops,
            target_field=CONF_SITE_ID,
            target_field_setter=lambda site_id: self._options.__setitem__(
                CONF_SITE_ID, int(site_id)
            ),
            user_input=user_input,
        )

    async def async_step_legacy(
        self, type_: str, user_input: dict[str, Any] | None = None
    ):
        self._options[CONF_INTEGRATION_TYPE] = type_
        return await self.async_step_name()

    async def async_step_name(self, user_input: dict[str, Any] | None = None):
        if not user_input:
            return self.async_show_form(step_id="name", data_schema=NAME_CONFIG_SCHEMA)

        self._options[CONF_NAME] = user_input[CONF_NAME]
        return await self.async_step_config()

    async def async_step_config(self, user_input: dict[str, Any] | None = None):
        type_ = self._options[CONF_INTEGRATION_TYPE]

        schema = schema_by_type(type_)

        # patch schema with suggested values from self._options for known types
        if type_ == SENSOR_DEPARTURE:
            if site_id := self._options.get(CONF_SITE_ID):
                schema = self.add_suggested_values_to_schema(
                    schema,
                    {CONF_SITE_ID: site_id},
                )

        if user_input is None:
            return self.async_show_form(step_id="config", data_schema=schema)

        # validate user input
        errors = {}
        if type_ == SENSOR_ROUTE:
            source = user_input[const.CONF_SOURCE]
            dest = user_input[const.CONF_DESTINATION]

            try:
                siteid_or_coords(source, dest)
            except* SourceInvalid:
                errors[const.CONF_SOURCE] = "invalid_siteid_or_coords"
            except* DestinationInvalid:
                errors[const.CONF_DESTINATION] = "invalid_siteid_or_coords"
            except* ValueError:
                errors["base"] = "inconsistent_source_and_destination"

        if errors:
            schema = self.add_suggested_values_to_schema(schema, user_input)
            return self.async_show_form(
                step_id="config",
                data_schema=schema,
                errors=errors,
            )

        data = {
            CONF_INTEGRATION_TYPE: type_,
        }

        # TODO: remove legacy: generate a new integration id
        if type_ not in (SENSOR_DEPARTURE, SENSOR_STATUS):
            data[CONF_INTEGRATION_ID] = uuid.uuid1()

        return self.async_create_entry(
            title=self._options[CONF_NAME], data=data, options=user_input
        )


class ResrobotSubentryFlowHandler(ConfigSubentryFlow, LocationLookupMixin):
    _options = {}

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        """Get the options flow for this handler."""
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)

    async def async_step_user(self, _: UserInputType = None):
        return self.async_show_menu(
            step_id="user",
            menu_options=[
                SENSOR_RESROBOT_ROUTE,
                SENSOR_RESROBOT_DEPARTURE,
            ],
        )

    async def async_step_resrobot_route(self, _: UserInputType = None):
        self._options[CONF_INTEGRATION_TYPE] = SENSOR_RESROBOT_ROUTE
        return self.async_show_menu(
            step_id=SENSOR_RESROBOT_ROUTE,
            menu_options=["find_source", "name"],
        )

    async def async_step_resrobot_departure(self, _: dict[str, Any] | None = None):
        self._options[CONF_INTEGRATION_TYPE] = SENSOR_RESROBOT_DEPARTURE
        return self.async_show_menu(
            step_id=SENSOR_RESROBOT_DEPARTURE,
            menu_options=["find_stop", "name"],
        )

    async def async_step_name(self, user_input: UserInputType = None):
        if not user_input:
            return self.async_show_form(step_id="name", data_schema=NAME_CONFIG_SCHEMA)

        self._options[CONF_NAME] = user_input[CONF_NAME]
        return await self.async_step_config()

    async def _find_stops(self, search_key: str) -> list[sel.SelectOptionDict]:
        session = async_get_clientsession(self.hass)
        client = ResRobotClient(session, self._get_entry().data[CONF_API_KEY])
        stops = await client.find_stop_location(search_key, LocationSearchType.STOP)
        return [{"value": stop["id"], "label": stop["name"]} for stop in stops]
    
    async def async_step_find_stop(self, user_input: UserInputType = None):
        return await self._find_location(
            step_id="find_stop",
            step_call=self.async_step_find_stop,
            search_call=self._find_stops,
            next_step=self.async_step_name,
            target_field=CONF_SOURCE,
            user_input=user_input,
        )

    async def async_step_find_source(self, user_input: UserInputType = None):
        return await self._find_location(
            step_id="find_source",
            step_call=self.async_step_find_source,
            search_call=self._find_stops,
            next_step=self.async_step_find_destination,
            target_field=CONF_SOURCE,
            user_input=user_input,
        )

    async def async_step_find_destination(self, user_input: UserInputType = None):
        return await self._find_location(
            step_id="find_destination",
            step_call=self.async_step_find_destination,
            next_step=self.async_step_name,
            search_call=self._find_stops,
            target_field=CONF_DESTINATION,
            user_input=user_input,
        )

    async def async_step_config(self, user_input: UserInputType = None):
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is None:
            if not self._is_new:
                # If this is a reconfiguration, we need to copy the existing options
                self._options = self._get_reconfigure_subentry().data.copy()
                self._options[CONF_NAME] = self._get_reconfigure_subentry().title

            type_ = self._options[CONF_INTEGRATION_TYPE]
            schema = schema_by_type(type_)
            schema = self.add_suggested_values_to_schema(schema, self._options)

            return self.async_show_form(step_id="config", data_schema=schema)

        type_ = self._options[CONF_INTEGRATION_TYPE]
        final_data = {
            CONF_INTEGRATION_TYPE: type_,
            **user_input,
        }

        if self._is_new:
            return self.async_create_entry(
                title=self._options[CONF_NAME],
                data=final_data,
                unique_id=f"{self._entry_id}_{type_}_{uuid.uuid1()}",
            )

        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            data=final_data,
        )

    async_step_reconfigure = async_step_config
