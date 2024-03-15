"""HASL Configuration Database."""

import voluptuous as vol

from homeassistant.helpers import selector

from .const import (
    CONF_ANALOG_SENSORS,
    CONF_DESTINATION,
    CONF_DESTINATION_ID,
    CONF_DEVIATION_LINES,
    CONF_DEVIATION_STOPS,
    CONF_DIRECTION,
    CONF_DIRECTION_LIST,
    CONF_FP_LB,
    CONF_FP_PT,
    CONF_FP_RB,
    CONF_FP_SB,
    CONF_FP_SPVC,
    CONF_FP_TB1,
    CONF_FP_TB2,
    CONF_FP_TB3,
    CONF_FP_TVB,
    CONF_INTEGRATION_TYPE,
    CONF_LINE,
    CONF_LINES,
    CONF_NAME,
    CONF_RI4_KEY,
    CONF_RP3_KEY,
    CONF_RR_KEY,
    CONF_RRARR_PROPERTY_LIST,
    CONF_RRDEP_PROPERTY_LIST,
    CONF_SCAN_INTERVAL,
    CONF_SENSOR,
    CONF_SENSOR_PROPERTY,
    CONF_SENSOR_PROPERTY_LIST,
    CONF_SI2_KEY,
    CONF_SITE_ID,
    CONF_SOURCE,
    CONF_SOURCE_ID,
    CONF_TIMEWINDOW,
    CONF_TL2_KEY,
    DEFAULT_DIRECTION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_PROPERTY,
    DEFAULT_TIMEWINDOW,
    SENSOR_DEPARTURE,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
    SENSOR_RRARR,
    SENSOR_RRDEP,
    SENSOR_RRROUTE,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    CONF_INTEGRATION_LIST,
)
from .sensors.departure import CONFIG_SCHEMA as departure_config_schema


START_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_INTEGRATION_TYPE, default=SENSOR_DEPARTURE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=CONF_INTEGRATION_LIST,
                translation_key=CONF_INTEGRATION_TYPE,
            )
        ),
    }
)


def schema_by_type(type_: str) -> vol.Schema:
    """Return the schema for the specified type."""

    # TODO: remove shortcut
    if type_ == SENSOR_DEPARTURE:
        return departure_config_schema

    schema = {
        SENSOR_STANDARD: standard_config_option_schema,
        SENSOR_STATUS: status_config_option_schema,
        SENSOR_VEHICLE_LOCATION: vehiclelocation_config_option_schema,
        SENSOR_DEVIATION: deviation_config_option_schema,
        SENSOR_ROUTE: route_config_option_schema,
        SENSOR_RRDEP: rrdep_config_option_schema,
        SENSOR_RRARR: rrarr_config_option_schema,
        SENSOR_RRROUTE: rrroute_config_option_schema,
    }.get(type_)

    return vol.Schema(schema())


def standard_config_option_schema(options: dict = {}) -> dict:
    """Options for departure sensor / standard sensor."""
    if not options:
        options = {
            CONF_SENSOR: "",
            CONF_RI4_KEY: "",
            CONF_SITE_ID: "",
            CONF_SENSOR: "",
            CONF_LINES: "",
            CONF_DIRECTION: DEFAULT_DIRECTION,
            CONF_SENSOR_PROPERTY: DEFAULT_SENSOR_PROPERTY,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_TIMEWINDOW: DEFAULT_TIMEWINDOW,
        }
    return {
        vol.Required(CONF_RI4_KEY, default=options.get(CONF_RI4_KEY)): str,
        vol.Required(CONF_SITE_ID, default=options.get(CONF_SITE_ID)): int,
        vol.Required(
            CONF_SENSOR_PROPERTY, default=options.get(CONF_SENSOR_PROPERTY)
        ): vol.In(CONF_SENSOR_PROPERTY_LIST),
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Required(CONF_TIMEWINDOW, default=options.get(CONF_TIMEWINDOW)): int,
        vol.Optional(CONF_LINES, default=options.get(CONF_LINES)): str,
        vol.Optional(CONF_DIRECTION, default=options.get(CONF_DIRECTION)): vol.In(
            CONF_DIRECTION_LIST
        ),
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


def deviation_config_option_schema(options: dict = {}) -> dict:
    """Deviation sensor options."""
    if not options:
        options = {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SENSOR: "",
            CONF_SI2_KEY: "",
            CONF_DEVIATION_STOPS: "",
            CONF_DEVIATION_LINES: "",
        }
    return {
        vol.Required(CONF_SI2_KEY, default=options.get(CONF_SI2_KEY)): str,
        vol.Optional(
            CONF_DEVIATION_STOPS, default=options.get(CONF_DEVIATION_STOPS)
        ): str,
        vol.Optional(
            CONF_DEVIATION_LINES, default=options.get(CONF_DEVIATION_LINES)
        ): str,
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


CONF_METRO = "metro"
CONF_TRAIN = "train"
CONF_LOCAL = "local"
CONF_TRAM = "tram"
CONF_BUS = "bus"
CONF_FERRY = "ferry"


def status_config_option_schema(options: dict = {}) -> dict:
    """Status sensor options."""
    if not options:
        options = {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SENSOR: "",
            CONF_TL2_KEY: "",
            CONF_ANALOG_SENSORS: False,
            CONF_METRO: False,
            CONF_TRAIN: False,
            CONF_LOCAL: False,
            CONF_TRAM: False,
            CONF_BUS: False,
            CONF_FERRY: False,
        }
    return {
        vol.Required(CONF_TL2_KEY, default=options.get(CONF_TL2_KEY)): str,
        vol.Optional(CONF_METRO, default=options.get(CONF_METRO)): bool,
        vol.Optional(CONF_TRAIN, default=options.get(CONF_TRAIN)): bool,
        vol.Optional(CONF_LOCAL, default=options.get(CONF_LOCAL)): bool,
        vol.Optional(CONF_TRAM, default=options.get(CONF_TRAM)): bool,
        vol.Optional(CONF_BUS, default=options.get(CONF_BUS)): bool,
        vol.Optional(CONF_FERRY, default=options.get(CONF_FERRY)): bool,
        vol.Optional(
            CONF_ANALOG_SENSORS, default=options.get(CONF_ANALOG_SENSORS)
        ): bool,
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


def vehiclelocation_config_option_schema(options: dict = {}) -> dict:
    """The schema used for train location service"""
    if not options:
        options = {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SENSOR: "",
            CONF_FP_PT: False,
            CONF_FP_RB: False,
            CONF_FP_TVB: False,
            CONF_FP_SB: False,
            CONF_FP_LB: False,
            CONF_FP_SPVC: False,
            CONF_FP_TB1: False,
            CONF_FP_TB2: False,
            CONF_FP_TB3: False,
        }
    return {
        vol.Optional(CONF_FP_PT, default=options.get(CONF_FP_PT)): bool,
        vol.Optional(CONF_FP_RB, default=options.get(CONF_FP_RB)): bool,
        vol.Optional(CONF_FP_TVB, default=options.get(CONF_FP_TVB)): bool,
        vol.Optional(CONF_FP_SB, default=options.get(CONF_FP_SB)): bool,
        vol.Optional(CONF_FP_LB, default=options.get(CONF_FP_LB)): bool,
        vol.Optional(CONF_FP_SPVC, default=options.get(CONF_FP_SPVC)): bool,
        vol.Optional(CONF_FP_TB1, default=options.get(CONF_FP_TB1)): bool,
        vol.Optional(CONF_FP_TB2, default=options.get(CONF_FP_TB2)): bool,
        vol.Optional(CONF_FP_TB3, default=options.get(CONF_FP_TB3)): bool,
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


def route_config_option_schema(options: dict = {}) -> dict:
    """Deviation sensor options."""
    if not options:
        options = {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_SENSOR: "",
            CONF_RP3_KEY: "",
            CONF_SOURCE: "",
            CONF_DESTINATION: "",
        }
    return {
        vol.Required(CONF_RP3_KEY, default=options.get(CONF_RP3_KEY)): str,
        vol.Required(CONF_SOURCE, default=options.get(CONF_SOURCE)): str,
        vol.Required(CONF_DESTINATION, default=options.get(CONF_DESTINATION)): str,
        vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL)): int,
        vol.Optional(CONF_SENSOR, default=options.get(CONF_SENSOR)): str,
    }


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
