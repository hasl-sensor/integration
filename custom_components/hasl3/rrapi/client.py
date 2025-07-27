import logging
from typing import Any
import aiohttp
import isodate

logger = logging.getLogger(__name__)


class ResRobotClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self._session = session
        self._api_key = api_key
        self._base_url = "https://api.resrobot.se/v2.1"

    async def _get_json(self, url: str) -> Any:
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                json = await response.json()

                if "errorCode" in json:
                    logger.error(f"API error occurred: {json['errorCode']}")
                    raise RuntimeError(f"API error: {json['errorText']}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

        return json

    async def find_location(self, search_string: str) -> list[dict[str, Any]]:
        """Search for a location by a free text string."""
        url = f"{self._base_url}/location.name?input={search_string}&format=json&accessId={self._api_key}"
        data = await self._get_json(url)

        # transform data
        result = []
        for stopOrLocation in data["stopLocationOrCoordLocation"]:
            place = stopOrLocation.get(
                "CoordLocation", stopOrLocation.get("StopLocation")
            )
            result.append(
                {
                    "longId": place["id"],
                    "name": place["name"],
                    "lon": place["lon"],
                    "lat": place["lat"],
                    "id": place.get("extId", ""),
                    "type": place.get("type", "STOP"),
                }
            )

        return result

    async def find_trip(self, origin: str, destination: str) -> list[dict[str, Any]]:
        """Find a route between two locations."""
        url = f"{self._base_url}/trip?format=json&originId={origin}&destId={destination}&passlist=true&showPassingPoints=true&accessId={self._api_key}"
        data = await self._get_json(url)

        # transform data
        trips = []

        #Parse every trip
        for trip in data["Trip"]:
            newtrip = {'legs': []}

            # Add legs to trips
            for leg in trip['LegList']['Leg']:
                newleg = {}
                # Walking is done by humans.
                # And robots.
                # Robots are scary.
                newleg['line'] = leg['Product'][0]['line'] if leg["type"] != "WALK" else "Walk"
                newleg['direction'] = leg['directionFlag'] if leg["type"] != "WALK" else "Walk"
                newleg['category'] = leg['type']
                newleg['name'] = leg['Product'][0]['name']
                newleg['from'] = leg['Origin']['name']
                newleg['to'] = leg['Destination']['name']
                newleg['time'] = f"{leg['Origin']['date']} {leg['Origin']['time']}"

                if leg.get('Stops'):
                    if leg['Stops'].get('Stop', {}):
                        newleg['stops'] = []
                        for stop in leg.get('Stops', {}).get('Stop', {}):
                            newleg['stops'].append(stop)

                newtrip['legs'].append(newleg)

            # Make some shortcuts for data
            newtrip['first_leg'] = newtrip['legs'][0]['name']
            newtrip['time'] = newtrip['legs'][0]['time']
            newtrip['duration'] = str(isodate.parse_duration(trip['duration']))
            trips.append(newtrip)

        # Add shortcuts to info in the first trip if it exists
        firstLegFirstTrip = next((x for x in trips[0]['legs'] if x["category"] != "WALK"), [])
        lastLegLastTrip = next((x for x in reversed(trips[0]['legs']) if x["category"] != "WALK"), [])

        result = {
            "transfers": sum(p["category"] != "WALK" for p in trips[0]['legs']) - 1 or 0,
            "time": trips[0]['time'] or '',
            "duration": trips[0]['duration'] or '',
            "from": trips[0]['legs'][0]['from'] or '',
            "to": trips[0]['legs'][-1]['to'] or '',
            "origin": {
                "leg": firstLegFirstTrip["name"] or '',
                "line": firstLegFirstTrip["line"] or '',
                "direction": firstLegFirstTrip["direction"] or '',
                "category": firstLegFirstTrip["category"] or '',
                "time": firstLegFirstTrip["time"] or '',
                "from": firstLegFirstTrip["from"] or '',
                "to": firstLegFirstTrip["to"] or '',
            },
            "destination": {
                "leg": lastLegLastTrip["name"] or '',
                "line": lastLegLastTrip["line"] or '',
                "direction": lastLegLastTrip["direction"] or '',
                "category": lastLegLastTrip["category"] or '',
                "time": lastLegLastTrip["time"] or '',
                "from": lastLegLastTrip["from"] or '',
                "to": lastLegLastTrip["to"] or '',
            },
            "trips": trips,
        }

        return result
