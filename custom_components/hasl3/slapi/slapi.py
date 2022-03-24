import json
import httpx
import time
import logging

from .exceptions import (
    SLAPI_Error,
    SLAPI_HTTP_Error,
    SLAPI_API_Error
)
from .const import (
    __version__,
    FORDONSPOSITION_URL,
    SI2_URL,
    TL2_URL,
    RI4_URL,
    PU1_URL,
    RP3_URL,
    USER_AGENT
)

logger = logging.getLogger("custom_components.hasl3.slapi")


class slapi_fp(object):
    def __init__(self, timeout=None):
        self._timeout = timeout

    def version(self):
        return __version__

    async def request(self, vehicletype):

        logger.debug("Will call FP API")
        if vehicletype not in ('PT', 'RB', 'TVB', 'SB', 'LB',
                               'SpvC', 'TB1', 'TB2', 'TB3'):
            raise SLAPI_Error(-1, "Vehicle type is not valid",
                                  "Must be one of 'PT','RB','TVB','SB',"
                                  "'LB','SpvC','TB1','TB2','TB3'")

        try:
            async with httpx.AsyncClient() as client:
                request = await client.get(FORDONSPOSITION_URL.format(vehicletype,
                                                                      time.time()),
                                           headers={"User-agent": USER_AGENT},
                                           follow_redirects=True,
                                           timeout=self._timeout)
        except Exception as e:
            error = SLAPI_HTTP_Error(997, "A HTTP error occured (Vechicle Locations)", str(e))
            logger.debug(e)
            logger.error(error)
            raise error

        response = json.loads(request.json())

        result = []

        for trip in response['Trips']:
            result.append(trip)

        logger.debug("Call completed")
        return result


class slapi(object):

    def __init__(self, timeout=None):
        self._timeout = timeout

    def version(self):
        return __version__

    async def _get(self, url, api):

        api_errors = {
            1001: 'No API key supplied in request',
            1002: 'The supplied API key is not valid',
            1003: 'Specified API is not valid',
            1004: 'The API is not avaliable for this key',
            1005: 'Key exists but is not for requested API',
            1006: 'To many request per minute (qouta exceeded for key)',
            1007: 'To many request per month (qouta exceeded for key)',
            4002: 'Date filter is not valid',
            5000: 'Parameter invalid',
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url,
                                        headers={"User-agent": USER_AGENT},
                                        follow_redirects=True,
                                        timeout=self._timeout)
        except Exception as e:
            error = SLAPI_HTTP_Error(997, f"A HTTP error occured ({api})", str(e))
            logger.debug(e)
            logger.error(error)
            raise error

        try:
            jsonResponse = resp.json()
        except Exception as e:
            error = SLAPI_API_Error(998, f"A parsing error occured ({api})", str(e))
            logger.debug(error)
            raise error

        if not jsonResponse:
            error = SLAPI_Error(999, "Internal error", f"jsonResponse is empty ({api})")
            logger.error(error)
            raise error

        if 'StatusCode' in jsonResponse:

            if jsonResponse['StatusCode'] == 0:
                logger.debug("Call completed")
                return jsonResponse

            apiErrorText = f"{api_errors.get(jsonResponse['StatusCode'])} ({api})"

            if apiErrorText:
                error = SLAPI_API_Error(jsonResponse['StatusCode'],
                                        apiErrorText,
                                        jsonResponse['Message'])
                logger.error(error)
                raise error
            else:
                error = SLAPI_API_Error(jsonResponse['StatusCode'],
                                        "Unknown API-response code encountered ({api})",
                                        jsonResponse['Message'])
                logger.error(error)
                raise error

        elif 'Trip' in jsonResponse:
            logger.debug("Call completed")
            return jsonResponse

        elif 'Sites' in jsonResponse:
            logger.debug("Call completed")
            return jsonResponse

        else:
            error = SLAPI_Error(-100, f"ResponseType is not ({api})")
            logger.error(error)
            raise error


class slapi_pu1(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, searchstring):
        logger.debug("Will call PU1 API")
        return await self._get(PU1_URL.format(self._api_token, searchstring),"Location Lookup")


class slapi_rp3(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, origin, destination, orgLat, orgLong, destLat, destLong):
        logger.debug("Will call RP3 API")
        return await self._get(RP3_URL.format(self._api_token, origin, destination,
                                              orgLat, orgLong, destLat, destLong),"Route")


class slapi_ri4(slapi):

    def __init__(self, api_token, window, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token
        self._window = window

    async def request(self, siteid):
        logger.debug("Will call RI4 API")
        return await self._get(RI4_URL.format(self._api_token,
                                              siteid, self._window),"Departures")


class slapi_si2(slapi):

    def __init__(self, api_token, siteid, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, siteid, lines):
        logger.debug("Will call SI2 API")
        return await self._get(SI2_URL.format(self._api_token,
                                              siteid, lines),"Deviations")


class slapi_tl2(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self):
        logger.debug("Will call TL2 API")
        return await self._get(TL2_URL.format(self._api_token),"Traffic Status")
