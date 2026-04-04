from functools import partial

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from ..const import DOMAIN
from .trip_finder import DESTINATION, LANG, ORIGIN, SIMPLIFIED, TRIPS, find_trip

SCHEMA = vol.Schema(
    {
        vol.Required(ORIGIN): str,
        vol.Required(DESTINATION): str,
        vol.Optional(TRIPS, default=1): int,
        vol.Optional(LANG, default="en"): str,
        vol.Optional(SIMPLIFIED, default=False): vol.Coerce(bool),
    }
)


async def service(hass: HomeAssistant, call: ServiceCall):
    return await find_trip(hass, call, coordinates=False)


def register(hass: HomeAssistant):
    hass.services.async_register(
        DOMAIN,
        "sl_find_trip_id",
        partial(service, hass),
        schema=SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
