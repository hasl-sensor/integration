import logging
from typing import Any
import aiohttp

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
