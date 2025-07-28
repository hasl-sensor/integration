import logging
from functools import partial

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.dt import async_get_time_zone

from ..rrapi.client import ResRobotClient

from ..const import DOMAIN

logger = logging.getLogger(__name__)


API_KEY = "api_key"
SEARCH_STRING = "search_string"


SCHEMA = vol.Schema({vol.Required(API_KEY): str, vol.Required(SEARCH_STRING): str})


async def service(hass: HomeAssistant, call: ServiceCall):
    api_key = call.data.get(API_KEY)
    search_string = call.data.get(SEARCH_STRING)

    logger.debug(f"Looking for '{search_string}' with key {api_key}")

    tz = await async_get_time_zone("Europe/Stockholm")
    session = async_get_clientsession(hass)
    rrapi = ResRobotClient(session, api_key, tz=tz)
    requestResult = await rrapi.find_location(search_string)
    return {
        "search_string": search_string,
        "results": requestResult
    }


def register(hass: HomeAssistant):
    hass.services.async_register(
        DOMAIN,
        "rr_find_location",
        partial(service, hass),
        schema=SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
