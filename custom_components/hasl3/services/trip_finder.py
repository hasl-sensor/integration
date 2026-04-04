import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from tsl.models.journey import SearchLeg, Language
from tsl.clients.journey import JourneyPlannerClient
from tsl.tools.journey import SimpleJourneyInterpreter, leg_display_str, pretty_duration

logger = logging.getLogger(__name__)

ORIGIN = "orig"
ORIGIN_LAT = "orig_lat"
ORIGIN_LON = "orig_lon"
DESTINATION = "dest"
DESTINATION_LAT = "dest_lat"
DESTINATION_LON = "dest_lon"
TRIPS = "trips"
LANG = "lang"
SIMPLIFIED = "simplified"

async def find_trip(hass: HomeAssistant, call: ServiceCall, coordinates: bool = False):
    if coordinates:
        olat, olon = call.data[ORIGIN_LAT], call.data[ORIGIN_LON]
        dlat, dlon = call.data[DESTINATION_LAT], call.data[DESTINATION_LON]
        origin = SearchLeg.from_coordinates(str(olat), str(olon))
        destination = SearchLeg.from_coordinates(str(dlat), str(dlon))
    else:
        origin, destination = call.data[ORIGIN], call.data[DESTINATION]
        origin = SearchLeg.from_any(origin)
        destination = SearchLeg.from_any(destination)

    lang = call.data.get(LANG, Language.EN)
    trips = call.data.get(TRIPS, 1)
    simplified = call.data.get(SIMPLIFIED, False)

    logger.debug(f"Searching for trip {origin} -> {destination}")

    session = async_get_clientsession(hass)
    client = JourneyPlannerClient(session)
    params = client.build_request_params(
        origin=origin,
        destination=destination,
        calc_number_of_trips=trips,
        language=lang,
    )
    requestResult = await client.search_trip(params)

    if simplified:
        trips = []
        for journey in requestResult:
            interpreter = SimpleJourneyInterpreter(journey)
            if duration := journey.get("tripDuration"):
                duration = pretty_duration(timedelta(seconds=duration))
            else:
                duration = "Undefined"

            trips.append(
                {
                    "duration": duration,
                    "steps": [
                        leg_display_str(step) for step in interpreter.get_itinerary()
                    ]
                }
            )

        return {"simplified": True, "trips": trips}

    return {"simplified": False, "trips": requestResult}
