"""HASL Configuration Database."""

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_DESTINATION,
    CONF_DESTINATION_ID,
    CONF_DIRECTION,
    CONF_DIRECTION_LIST,
    CONF_LINES,
    CONF_NAME,
    CONF_RR_KEY,
    CONF_RRARR_PROPERTY_LIST,
    CONF_RRDEP_PROPERTY_LIST,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR,
    CONF_SENSOR_PROPERTY,
    CONF_SITE_ID,
    CONF_SOURCE,
    CONF_SOURCE_ID,
    CONF_TIMEWINDOW,
    DEFAULT_DIRECTION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_PROPERTY,
    DEFAULT_TIMEWINDOW,
    SENSOR_DEPARTURE,
    SENSOR_ROUTE,
    SENSOR_RRARR,
    SENSOR_RRDEP,
    SENSOR_RRROUTE,
    SENSOR_STATUS,
)
from .sensors.departure import CONFIG_SCHEMA as departure_config_schema
from .sensors.route import CONFIG_SCHEMA as route_config_option_schema
from .sensors.status import CONFIG_SCHEMA as status_config_schema

NAME_CONFIG_SCHEMA = vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()})


def schema_by_type(type_: str) -> vol.Schema:
    """Return the schema for the specified type."""

    # TODO: remove shortcut
    if schema := {
        SENSOR_DEPARTURE: departure_config_schema,
        SENSOR_STATUS: status_config_schema,
        SENSOR_ROUTE: route_config_option_schema,
    }.get(type_):
        return schema

    if schema := {
        SENSOR_RRDEP: rrdep_config_option_schema,
        SENSOR_RRARR: rrarr_config_option_schema,
        SENSOR_RRROUTE: rrroute_config_option_schema,
    }.get(type_):
        return schema

    return vol.Schema(schema())


def rrdep_config_option_schema(options: dict = {}) -> dict:
    """Options for resrobot departure sensor."""
    if not options:
        options = {
            CONF_SENSOR: "",
            CONF_RR_KEY: "",
            CONF_SITE_ID: "",
            CONF_SENSOR: "",
            CONF_LINES: "",
            CONF_DIRECTION: DEFAULT_DIRECTION,
            CONF_SENSOR_PROPERTY: DEFAULT_SENSOR_PROPERTY,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_TIMEWINDOW: DEFAULT_TIMEWINDOW,
        }
    return {
        vol.Required(CONF_RR_KEY, default=options.get(CONF_RR_KEY)): str,
        vol.Required(CONF_SITE_ID, default=options.get(CONF_SITE_ID)): int,
        vol.Required(
            CONF_SENSOR_PROPERTY, default=options.get(CONF_SENSOR_PROPERTY)
        ): vol.In(CONF_RRDEP_PROPERTY_LIST),
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Required(CONF_TIMEWINDOW, default=options.get(CONF_TIMEWINDOW)): int,
        vol.Optional(CONF_LINES, default=options.get(CONF_LINES)): str,
        vol.Optional(CONF_DIRECTION, default=options.get(CONF_DIRECTION)): vol.In(
            CONF_DIRECTION_LIST
        ),
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


def rrarr_config_option_schema(options: dict = {}) -> dict:
    """Options for resrobot arrival sensor."""
    if not options:
        options = {
            CONF_SENSOR: "",
            CONF_RR_KEY: "",
            CONF_SITE_ID: "",
            CONF_SENSOR: "",
            CONF_LINES: "",
            CONF_DIRECTION: DEFAULT_DIRECTION,
            CONF_SENSOR_PROPERTY: DEFAULT_SENSOR_PROPERTY,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_TIMEWINDOW: DEFAULT_TIMEWINDOW,
        }
    return {
        vol.Required(CONF_RR_KEY, default=options.get(CONF_RR_KEY)): str,
        vol.Required(CONF_SITE_ID, default=options.get(CONF_SITE_ID)): int,
        vol.Required(
            CONF_SENSOR_PROPERTY, default=options.get(CONF_SENSOR_PROPERTY)
        ): vol.In(CONF_RRARR_PROPERTY_LIST),
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Required(CONF_TIMEWINDOW, default=options.get(CONF_TIMEWINDOW)): int,
        vol.Optional(CONF_LINES, default=options.get(CONF_LINES)): str,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


def rrroute_config_option_schema(options: dict = {}) -> dict:
    """Deviation sensor options."""
    if not options:
        options = {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SENSOR: "",
            CONF_RR_KEY: "",
            CONF_SOURCE_ID: "",
            CONF_DESTINATION_ID: "",
        }
    return {
        vol.Required(CONF_RR_KEY, default=options.get(CONF_RR_KEY)): str,
        vol.Required(CONF_SOURCE_ID, default=options.get(CONF_SOURCE)): str,
        vol.Required(CONF_DESTINATION_ID, default=options.get(CONF_DESTINATION)): str,
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }
