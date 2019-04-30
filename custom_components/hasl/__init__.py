"""HomeAssistant Sensor for SL (Storstockholms Lokaltrafik)"""
import datetime
from datetime import timedelta
import logging
import voluptuous as vol
import os
import stat
import json

import homeassistant.helpers.config_validation as cv

from homeassistant.util.dt import now
from homeassistant.helpers.event import async_track_time_interval

__version__ = '2.0.1'
_LOGGER = logging.getLogger(__name__)

DOMAIN = "hasl"

def setup(hass, config):
    """Setup our communication platform."""
    
    def clear_cache(call):     
        for sensor in hass.data[DOMAIN]:
                hass.data[DOMAIN][sensor] = ''
                
        jsonFile = open(hass.config.path('haslcache.json'), "w")
        jsonFile.write(json.dumps({}))
        jsonFile.close()

        return "{ 'result': true }"

    #track_time_interval(hass, FUNC, INTERVALL)
    hass.services.register(DOMAIN, 'clear_cache', clear_cache)

    # Return boolean to indicate that initialization was successfully.
    return True

