import logging
from functools import partial

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from ..const import DOMAIN
from .trip_finder import (
    DESTINATION_LAT,
    DESTINATION_LON,
    LANG,
    ORIGIN_LAT,
    ORIGIN_LON,
    SIMPLIFIED,
    TRIPS,
    find_trip,
)

logger = logging.getLogger(__name__)


SCHEMA = vol.Schema(
    {
        vol.Required(ORIGIN_LAT): vol.Coerce(float),
        vol.Required(ORIGIN_LON): vol.Coerce(float),
        vol.Required(DESTINATION_LAT): vol.Coerce(float),
        vol.Required(DESTINATION_LON): vol.Coerce(float),
        vol.Optional(TRIPS, default=1): int,
        vol.Optional(LANG, default="en"): str,
        vol.Optional(SIMPLIFIED, default=False): vol.Coerce(bool),
    }
)


async def service(hass: HomeAssistant, call: ServiceCall):
    return await find_trip(hass, call, coordinates=True)


def register(hass: HomeAssistant):
    hass.services.async_register(
        DOMAIN,
        "sl_find_trip_pos",
        partial(service, hass),
        schema=SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
