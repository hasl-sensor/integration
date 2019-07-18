"""HomeAssistant Sensor for SL (Storstockholms Lokaltrafik)"""
import datetime
import json
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import now

from hasl import (haslapi, pu1api, tp3api,
                  HASL_Error, HASL_API_Error, HASL_HTTP_Error)

__version__ = '2.2.0'
_LOGGER = logging.getLogger(__name__)

DOMAIN = "hasl"
VERSION = __version__

CONF_PU1_KEY = 'pu1key'
CONF_TP3_KEY = 'tp3key'

# Schema to validate the configured MQTT topic
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_PU1_KEY): cv.string,
    vol.Optional(CONF_TP3_KEY): cv.string
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Setup our communication platform."""

    try:
        _pu1api = pu1api(config[DOMAIN][CONF_PU1_KEY])
    except:
        _pu1api = pu1api('')

    try:
        _tp3api = tp3api(config[DOMAIN][CONF_TP3_KEY])
    except:
        _tp3api = tp3api('')

    def clear_cache(call):
        for sensor in hass.data[DOMAIN]:
                hass.data[DOMAIN][sensor] = ''

        jsonFile = open(hass.config.path('.storage/haslcache.json'), "w")
        jsonFile.write(json.dumps({}))
        jsonFile.close()

        return "{ 'result': true }"

    def find_location(call):
        search_string = call.data.get('search_string')

        return _pu1api.request(search_string)

    def find_trip_id(call):
        origin = call.data.get('org')
        destination = call.data.get('dest')

        return _tp3api.request(origin, destination, '', '', '', '')

    def find_trip_pos(call):
        olat = call.data.get('orig_lat')
        olon = call.data.get('orig_long')
        dlat = call.data.get('dest_lat')
        dlon = call.data.get('dest_long')

        return _tp3api.request('', '', olat, olon, dlat, dlon)

    # track_time_interval(hass, FUNC, INTERVALL).
    hass.services.register(DOMAIN, 'clear_cache', clear_cache)
    hass.services.register(DOMAIN, 'find_location', find_location)
    hass.services.register(DOMAIN, 'find_trip_id', find_trip_id)
    hass.services.register(DOMAIN, 'find_trip_pos', find_trip_pos)

    # Return boolean to indicate that initialization was successfully.
    return True
