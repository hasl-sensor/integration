"""SL Platform Sensor"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    SENSOR_DEPARTURE,
    SENSOR_ROUTE,
    SENSOR_STATUS,
    SERVICE_RESROBOT_KEY,
)
from .sensors.departure import async_setup_entry as setup_departure_sensor
from .sensors.resrobot import setup_resrobot_subentries
from .sensors.route import async_setup_entry as setup_route_sensor
from .sensors.status import async_setup_entry as setup_status_sensor

logger = logging.getLogger(f"custom_components.{DOMAIN}.sensors")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""

    type_ = entry.data[CONF_INTEGRATION_TYPE]
    if coro := {
        # "new-style" delegated setup functions
        SENSOR_DEPARTURE: setup_departure_sensor,
        SENSOR_STATUS: setup_status_sensor,
        SENSOR_ROUTE: setup_route_sensor,
        SERVICE_RESROBOT_KEY: setup_resrobot_subentries,
    }.get(type_):
        await coro(hass, entry, async_add_entities)

    else:
        logger.error(
            "Unknown integration type '%s' for entry %s", type_, entry.entry_id
        )
