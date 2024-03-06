import json
import httpx
import time
import logging

from .exceptions import (
    RRAPI_Error,
    RRAPI_HTTP_Error,
    RRAPI_API_Error
)
from .const import (
    __version__,
    BASE_URL,
    STOP_LOOKUP_URL,
    ARRIVAL_BOARD_URL,
    DEPARTURE_BOARD_URL,
    ROUTE_PLANNER_URL,
    USER_AGENT
)

logger = logging.getLogger("custom_components.hasl3.rrapi")

class rrapi(object):

    def __init__(self, timeout=None):
        self._timeout = timeout

    def version(self):
        return __version__

    async def _get(self, url, api):

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url,
                                        headers={"User-agent": USER_AGENT},
                                        follow_redirects=True,
                                        timeout=self._timeout)
        except Exception as e:
            error = RRAPI_HTTP_Error(997, f"A HTTP error occured ({api})", str(e))
            logger.debug(e)
            logger.error(error)
            raise error

        try:
            jsonResponse = resp.json()
        except Exception as e:
            error = RRAPI_API_Error(998, f"A parsing error occurred ({api})", str(e))
            logger.debug(error)
            raise error

        if not jsonResponse:
            error = RRAPI_Error(999, "Internal error", f"jsonResponse is empty ({api})")
            logger.error(error)
            raise error

        if 'errorCode' in jsonResponse:
            error = RRAPI_API_Error(jsonResponse['errorCode'], jsonResponse['errorText'],jsonResponse['errorText'])
            logger.error(error)
            raise error

        return jsonResponse


class rrapi_sl(rrapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, searchstring):
        logger.debug("Will call RR-SL API")

        data = await self._get(STOP_LOOKUP_URL.format(BASE_URL, searchstring, self._api_token),"Location Lookup")
        result = []

        for stopOrLocation in data["stopLocationOrCoordLocation"]:
          place = stopOrLocation["CoordLocation"] if "CoordLocation" in stopOrLocation else stopOrLocation["StopLocation"]
          entry = {}
          entry["longId"] = place["id"]
          entry["name"] = place["name"]
          entry["lon"] = place["lon"]
          entry["lat"] = place["lat"]
          entry["id"] = place["extId"] if 'extId' in place else ''
          entry["type"] = place["type"] if 'type' in place else 'STOP'
          result.append(entry)            
       
        return result




class rrapi_rrr(rrapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, origin, destination):
        logger.debug("Will call RR-RP API")
        return await self._get(ROUTE_PLANNER_URL.format(BASE_URL, origin, destination, self._api_token), "Route Planner")


class rrapi_rrd(rrapi):

    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, id):
        logger.debug("Will call RRDB API")
        return await self._get(DEPARTURE_BOARD_URL.format(BASE_URL, id, self._api_token),"Departure Board")

class rrapi_rra(rrapi):

    def __init__(self, api_token, id, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, id):
        logger.debug("Will call RRAB API")
        return await self._get(ARRIVAL_BOARD_URL.format(BASE_URL, id, self._api_token),"Arrivals Board")

