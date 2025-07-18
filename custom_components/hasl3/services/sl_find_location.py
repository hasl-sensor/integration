import logging
from functools import partial

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from tsl.clients.stoplookup import StopLookupClient
from tsl.utils import global_id_to_site_id

from ..const import DOMAIN

logger = logging.getLogger(__name__)


SEARCH_STRING = "search_string"


SCHEMA = vol.Schema({vol.Required(SEARCH_STRING): str})


async def service(hass: HomeAssistant, call: ServiceCall):
    search_string = call.data.get(SEARCH_STRING)

    logger.debug(f"Searching for '{search_string}'")

    session = async_get_clientsession(hass)
    client = StopLookupClient(session)

    requestResult = await client.get_stops(search_string)
    logger.debug(
        f"Completed search for '{search_string}'. Found {len(requestResult)} results"
    )

    return {
        SEARCH_STRING: search_string,
        "results": [
            {
                "name": r["disassembledName"],
                "full_name": r["name"],
                "id": r["id"],
                "site_id": global_id_to_site_id(r["id"]),
            }
            for r in requestResult[:10]
        ],
    }


def register(hass: HomeAssistant):
    hass.services.async_register(
        DOMAIN,
        "sl_find_location",
        partial(service, hass),
        schema=SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
