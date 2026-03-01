import logging
from datetime import datetime, tzinfo, UTC
from typing import Any, cast
from .model import StopLookupResponse, LocationSearchType

import aiohttp
import isodate
import urllib.parse

logger = logging.getLogger(__name__)


class ResRobotClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str, tz: tzinfo = UTC):
        self._session = session
        self._api_key = api_key
        self._base_url = "https://api.resrobot.se/v2.1"
        self._timezone = tz

    async def _get_json(self, url: str, params: dict[str, Any] = {}) -> Any:
        encoded_params = dict(
            (urllib.parse.quote(key), urllib.parse.quote_plus(value))
            for key, value in params.items()
        )
        try:
            async with self._session.get(url=url, params=encoded_params) as response:
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

    async def find_stop_location(
        self,
        search_string: str,
        location_search_type: LocationSearchType = LocationSearchType.ALL,
    ) -> list[dict[str, Any]]:
        """Search for a stop location by a free text string."""
        data = await self._get_json(
            url=f"{self._base_url}/location.name",
            params={
                "input": search_string,
                "format": "json",
                "accessId": self._api_key,
                "type": location_search_type.value,
            },
        )
        data = cast(StopLookupResponse, data)

        # transform data
        result = []
        for stop in data["stopLocationOrCoordLocation"]:
            place = stop.get("StopLocation", stop.get("CoordLocation", None))
            if place is not None:
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

        # Parse every trip
        for trip in data["Trip"]:
            newtrip = {"legs": []}

            # Add legs to trips
            for leg in trip["LegList"]["Leg"]:
                newleg = {}
                # Walking is done by humans.
                # And robots.
                # Robots are scary.
                newleg["line"] = (
                    leg["Product"][0]["line"] if leg["type"] != "WALK" else "Walk"
                )
                newleg["direction"] = (
                    leg["directionFlag"] if leg["type"] != "WALK" else "Walk"
                )
                newleg["category"] = leg["type"]
                newleg["name"] = leg["Product"][0]["name"]
                newleg["from"] = leg["Origin"]["name"]
                newleg["to"] = leg["Destination"]["name"]
                newleg["time"] = f"{leg['Origin']['date']} {leg['Origin']['time']}"

                if leg.get("Stops"):
                    if leg["Stops"].get("Stop", {}):
                        newleg["stops"] = []
                        for stop in leg.get("Stops", {}).get("Stop", {}):
                            newleg["stops"].append(stop)

                newtrip["legs"].append(newleg)

            # Make some shortcuts for data
            newtrip["first_leg"] = newtrip["legs"][0]["name"]
            newtrip["time"] = newtrip["legs"][0]["time"]
            newtrip["duration"] = str(isodate.parse_duration(trip["duration"]))
            trips.append(newtrip)

        # Add shortcuts to info in the first trip if it exists
        firstLegFirstTrip = next(
            (x for x in trips[0]["legs"] if x["category"] != "WALK"), []
        )
        lastLegLastTrip = next(
            (x for x in reversed(trips[0]["legs"]) if x["category"] != "WALK"), []
        )

        result = {
            "transfers": sum(p["category"] != "WALK" for p in trips[0]["legs"]) - 1
            or 0,
            "time": trips[0]["time"] or "",
            "duration": trips[0]["duration"] or "",
            "from": trips[0]["legs"][0]["from"] or "",
            "to": trips[0]["legs"][-1]["to"] or "",
            "origin": {
                "leg": firstLegFirstTrip["name"] or "",
                "line": firstLegFirstTrip["line"] or "",
                "direction": firstLegFirstTrip["direction"] or "",
                "category": firstLegFirstTrip["category"] or "",
                "time": firstLegFirstTrip["time"] or "",
                "from": firstLegFirstTrip["from"] or "",
                "to": firstLegFirstTrip["to"] or "",
            },
            "destination": {
                "leg": lastLegLastTrip["name"] or "",
                "line": lastLegLastTrip["line"] or "",
                "direction": lastLegLastTrip["direction"] or "",
                "category": lastLegLastTrip["category"] or "",
                "time": lastLegLastTrip["time"] or "",
                "from": lastLegLastTrip["from"] or "",
                "to": lastLegLastTrip["to"] or "",
            },
            "trips": trips,
        }

        return result

    async def get_departures(
        self, location_id: str, now: datetime
    ) -> list[dict[str, Any]]:
        """Get departures from a specific location."""
        url = f"{self._base_url}/departureBoard?format=json&id={location_id}&accessId={self._api_key}"
        data = await self._get_json(url)

        # transform data
        departures = []
        for departure in data["Departure"]:
            date, time = departure["date"], departure["time"]

            if "rtDate" in departure and "rtTime" in departure:
                diff_date, diff_time = departure["rtDate"], departure["rtTime"]
            else:
                diff_date, diff_time = date, time

            adjustedDateTime = now.replace(tzinfo=None)
            diff = (
                datetime.strptime(f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S")
                - adjustedDateTime
            )
            diff = round(diff.total_seconds() / 60)

            expected = datetime.strptime(
                f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=self._timezone)

            departures.append(
                {
                    "line": departure["ProductAtStop"]["displayNumber"],
                    "direction": departure["directionFlag"],
                    "departure": datetime.strptime(
                        f"{date} {time}", "%Y-%m-%d %H:%M:%S"
                    ),
                    "destination": departure["direction"],
                    "time": diff,
                    "operator": departure["ProductAtStop"]["operator"],
                    "expected": expected,
                    "type": departure["ProductAtStop"]["catOut"],
                }
            )

        return departures
