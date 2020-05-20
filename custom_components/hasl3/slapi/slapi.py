import json
import httpx
import time
from .exceptions import *
from .const import (
    __version__,
    FORDONSPOSITION_URL,
    TRAFIKLAB_URL,
    SI2_URL,
    TL2_URL,
    RI4_URL,
    PU1_URL,
    RP3_URL,
    USER_AGENT
)


class slapi_fp(object):
    def __init__(self, timeout=None):
        self._timeout = timeout

    def version(self):
        return __version__

    async def request(self, vehicletype):

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
                                   allow_redirects=True,
                                   timeout=self._timeout)
        except Exception as e:
            raise SLAPI_HTTP_Error(997, "A HTTP error occured", str(e))

        response = json.loads(request.json())

        result = []

        for trip in response['Trips']:
            result.append(trip)

        return result


class slapi(object):

    def __init__(self, timeout=None):
        self._timeout = timeout

    def version(self):
        return __version__

    async def _get(self, url):

        api_errors = {
            1001: 'API key is over qouta',
            1002: 'API key is invalid',
            }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url,
                                headers={"User-agent": USER_AGENT},
                                allow_redirects=True,
                                timeout=self._timeout)
        except Exception as e:
            raise SLAPI_HTTP_Error(997, "A HTTP error occured", str(e))

        try:
            jsonResponse = resp.json()
        except Exception as e:
            raise SLAPI_API_Error(998, "A parsing error occured", str(e))

        if not jsonResponse:
            raise SLAPI_Error(999, "Internal error", "jsonResponse is empty")

        if 'StatusCode' in jsonResponse:

            if jsonResponse['StatusCode'] == 0:
                return jsonResponse

            apiErrorText = api_errors.get(jsonResponse['StatusCode'])

            if apiErrorText:
                raise SLAPI_API_Error(jsonResponse['StatusCode'],
                                     apiErrorText,
                                     jsonResponse['Message'])
            else:
                raise SLAPI_API_Error(jsonResponse['StatusCode'],
                                     "Unknown API-response code encountered",
                                     jsonResponse['Message'])

        elif 'Trip' in jsonResponse:
            return jsonResponse

        elif 'Sites' in jsonResponse:
            return jsonResponse

        else:
            raise SLAPI_Error(-100, "ResponseType is not known")


class slapi_pu1(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, searchstring):
        return await self._get(PU1_URL.format(self._api_token, searchstring))


class slapi_rp3(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, origin, destination, orgLat, orgLong, destLat, destLong):
        return await self._get(RP3_URL.format(self._api_token, origin, destination,
                                        orgLat, orgLong, destLat, destLong))



class slapi_ri4(slapi):

    def __init__(self, api_token, window, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token
        self._window = window

    async def request(self, siteid):
        return await self._get(RI4_URL.format(self._api_token,
                                        siteid, self._window))


class slapi_si2(slapi):

    def __init__(self, api_token, siteid, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self, siteid, lines):
        return await self._get(SI2_URL.format(self._api_token,
                                        siteid, lines))


class slapi_tl2(slapi):
    def __init__(self, api_token, timeout=None):
        super().__init__(timeout)
        self._api_token = api_token

    async def request(self):
        return await self._get(TL2_URL.format(self._api_token))
