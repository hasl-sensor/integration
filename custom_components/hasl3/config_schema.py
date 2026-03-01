"""HASL Configuration Database."""

import voluptuous as vol
from homeassistant.helpers import selector

from .const import (
    CONF_API_KEY,
    CONF_NAME,
    SENSOR_DEPARTURE,
    SENSOR_RESROBOT_ARRIVAL,
    SENSOR_RESROBOT_DEPARTURE,
    SENSOR_RESROBOT_ROUTE,
    SENSOR_ROUTE,
    SENSOR_STATUS,
    SERVICE_RESROBOT_KEY,
)
from .sensors.departure import CONFIG_SCHEMA as departure_config_schema
from .sensors.route import CONFIG_SCHEMA as route_config_option_schema
from .sensors.rr_arrival import CONFIG_SCHEMA as rrarr_config_option_schema
from .sensors.rr_departure import CONFIG_SCHEMA as rrdep_config_option_schema
from .sensors.rr_route import CONFIG_SCHEMA as rrroute_config_option_schema
from .sensors.status import CONFIG_SCHEMA as status_config_schema

NAME_CONFIG_SCHEMA = vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()})

API_KEY_CONFIG_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): selector.TextSelector()})

def schema_by_type(type_: str | None) -> vol.Schema:
    """Return the schema for the specified type."""

    if schema := {
        SENSOR_DEPARTURE: departure_config_schema,
        SENSOR_STATUS: status_config_schema,
        SENSOR_ROUTE: route_config_option_schema,
        # ResRobot
        SERVICE_RESROBOT_KEY: API_KEY_CONFIG_SCHEMA,
        SENSOR_RESROBOT_ROUTE: rrroute_config_option_schema,
        SENSOR_RESROBOT_DEPARTURE: rrdep_config_option_schema,
        SENSOR_RESROBOT_ARRIVAL: rrarr_config_option_schema
    }.get(type_):
        return schema

    raise ValueError(f"Unknown schema type: {type_}")
