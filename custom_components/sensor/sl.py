"""
Simple service for SL (Storstockholms Lokaltrafik)


"""
import datetime
from datetime import timedelta
import logging

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, ToggleEntity
from homeassistant.helpers.event import (
    async_track_point_in_utc_time, async_track_utc_time_change)
from homeassistant.util import dt as dt_util
from homeassistant.const import STATE_ON, STATE_OFF

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

__version__ = '0.0.5'

_LOGGER = logging.getLogger(__name__)

CONF_RI4_KEY = 'ri4key'
CONF_SI2_KEY = 'si2key'
CONF_SITEID = 'siteid'
CONF_LINES = 'lines'
CONF_NAME = 'name'
CONF_DIRECTION = 'direction'
CONF_ENABLED_SENSOR = 'sensor'

UPDATE_FREQUENCY = timedelta(seconds=600)
FORCED_UPDATE_FREQUENCY = timedelta(seconds=5)

USER_AGENT = "HomeAssistant-Traffic-Info/"+__version__

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RI4_KEY): cv.string,   
    vol.Required(CONF_SI2_KEY): cv.string,
    vol.Required(CONF_SITEID): cv.string,
    vol.Optional(CONF_LINES): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_DIRECTION): cv.string,
    vol.Optional(CONF_ENABLED_SENSOR): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensors.
    
       right now only one, but later there should probably be another sensor for deviations at the same site
    """

    ri4data = SlDepartureData(
        config.get(CONF_RI4_KEY),
        config.get(CONF_SITEID),
        config.get(CONF_LINES),
        config.get(CONF_DIRECTION),
    )
    si2data = SlDevianceData(
        config.get(CONF_SI2_KEY),
        config.get(CONF_SITEID),
        config.get(CONF_LINES),
        config.get(CONF_DIRECTION),
    )

    sensors = []
    sensors.append(
        SLTraficInformationSensor(
            hass,
            ri4data,
            si2data,
            config.get(CONF_SITEID),
            config.get(CONF_NAME),
            config.get(CONF_ENABLED_SENSOR)
        )
    )
    add_devices(sensors)

class SLTraficInformationSensor(Entity):
    """Department board for one SL site."""

    def __init__(self, hass, ri4data, si2data, siteid, name, enabled_sensor):
        """Initialize"""
        self._hass = hass
        self._sensor = 'sl'
        self._siteid = siteid
        self._name = name or siteid
        self._ri4data = ri4data
        self._si2data = si2data
        self._nextdeparture = -1
        self._board = []
        self._deviances = []
        self._ri4error_logged = False
        self._si2error_logged = False
        self._enabled_sensor = enabled_sensor

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._sensor, self._name)

    @property
    def intervall(self):
        """Return the intervall of the sensor."""
        return self._intervall
        
    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return 'mdi:train-car'

    @property
    def state(self):
        """ Return number of minutes to the next departure """
        if len(self._board) > 0:
            return self._board[0]['time']

        return -1

    @property
    def device_state_attributes(self):
        """ Return the sensor attributes ."""

        val = {}
        val['attribution'] = 'Stockholms Lokaltrafik'
        val['unit_of_measurement'] = 'min'

        if not(self._ri4data.data) :
            return val

        val['departure_board'] = self._board

        if not(self._si2data.data) :
            return val

        val['deviances'] = self._deviances

        return val

    def parseDepartureTime(self, t):
        """ weird time formats from the API, do some quick and dirty conversions """

        try:        
            if t == 'Nu':
                return 0
            s = t.split()
            if(len(s) > 1 and s[1] == 'min'):
                return int(s[0])
            s = t.split(':')
            if(len(s) > 1):
                now = datetime.datetime.now()
                min = (int(s[0])*60 + int(s[1])) - (now.hour*60 + now.minute)
                if min < 0: 
                    min = min + 1440
                return min
        except Exception:
            _LOGGER.error('Failed to parse departure time (%s) ', t)
        return 0
        
    def icon_mapper(argument):
        switcher = {
            "Buses": "mdi:bus",
            "Trams": "mdi:tram",
            "Ships": "mdi:boat",
            "Metros": "mdi:subway-variant",
            "Trains": "mdi:train"
        }
        return switcher.get(argument, "mdi:train-car")

    def update(self):
        """Get the departure board."""
        if self._enabled_sensor is not None:
            sensor_state = self._hass.states.get(self._enabled_sensor)
        if self._enabled_sensor is None or sensor_state.state is STATE_ON:
            self._ri4data.update()
            board = []
            if self._ri4data.data['StatusCode'] != 0:
                if not self._ri4error_logged:
                    _LOGGER.warn("Status code: {}, {}".format(self._ri4data.data['StatusCode'], self._ri4data.data['Message']))
                    self._ri4error_logged = True  # Only report error once, until success.
            else:
                if self._ri4error_logged:
                    _LOGGER.warn("API call successful again")
                    self._ri4error_logged = False  # Reset that error has been reported.
                for i,traffictype in enumerate(['Metros','Buses','Trains','Trams', 'Ships']):
                    for idx, value in enumerate(self._ri4data.data['ResponseData'][traffictype]):
                        direction = value['JourneyDirection'] or 0
                        displaytime = value['DisplayTime'] or ''
                        destination = value['Destination'] or ''
                        linenumber = value['LineNumber'] or ''
                        if 
                        if (int(self._ri4data._direction) == 0 or int(direction) == int(self._ri4data._direction)):
                            if(self._ri4data._lines is None or (linenumber in self._ri4data._lines)):
                                diff = self.parseDepartureTime(displaytime)
                                board.append({"line":linenumber,"direction":direction,"departure":displaytime,"destination":destination, 'time': diff, 'type': traffictype, 'icon': icon_mapper(traffictype)})
            self._board = sorted(board, key=lambda k: k['time'])
            _LOGGER.info(self._board)
            
            self._si2data.update()
            deviances = []
            if self._si2data.data['StatusCode'] != 0:
                if not self._si2error_logged:
                    _LOGGER.warn("Status code: {}, {}".format(self._si2data.data['StatusCode'], self._si2data.data['Message']))
                    self._si2error_logged = True  # Only report error once, until success.
            else:
                if self._si2error_logged:
                    self._ri4error_logged = False  # Reset that error has been reported.
                    _LOGGER.warn("API call successful again")
                    self._si2error_logged = False  # Reset that error has been reported.
                for idx, value in enumerate(self._si2data.data['ResponseData']):
                    board.deviances({"updated":value['Updated'],"title":value['Header'],"fromDate":value['FromDateTime'],"toDate":value['UpToDateTime'], 'details': value['Details'], 'sortOrder': value['SortOrder']})
            self._deviances = sorted(deviances, key=lambda k: k['sortOrder'])
            _LOGGER.info(self._deviances)


class SlDepartureData(object):
    """ Class for retrieving API data """
    def __init__(self, apikey, siteid, lines, direction):
        """Initialize the data object."""
        self._apikey = apikey
        self._siteid = siteid
        self._lines = lines 
        self._direction = direction or 0
        self.data = {}

    @Throttle(UPDATE_FREQUENCY, FORCED_UPDATE_FREQUENCY)
    def update(self, **kwargs):
        """Get the latest data for this site from the API."""
        try:
            _LOGGER.info("SL: fetching RI4 Data for '%s'", self._siteid)
            url = "https://api.sl.se/api2/realtimedeparturesV4.json?key={}&siteid={}". \
                   format(self._apikey, self._siteid)

            req = requests.get(url, headers={"User-agent": USER_AGENT}, allow_redirects=True, timeout=5)

        except requests.exceptions.RequestException:
            _LOGGER.error("SL: failed fetching RI4 Data for '%s'", self._siteid)
            return

        if req.status_code == 200:
            self.data = req.json()

        else:
            _LOGGER.error("SL: failed fetching RI4 Data for '%s'"
                          "(HTTP Status_code = %d)", self._siteid,
                          req.status_code)

                          
class SlDevianceData(object):
    """ Class for retrieving API data """
    def __init__(self, apikey, siteid, lines, direction):
        """Initialize the data object."""
        self._apikey = apikey
        self._siteid = siteid
        self._lines = lines 
        self._direction = direction or 0
        self.data = {}

    @Throttle(UPDATE_FREQUENCY, FORCED_UPDATE_FREQUENCY)
    def update(self, **kwargs):
        """Get the latest data for this site from the API."""
        try:
            _LOGGER.info("SL: fetching SI2 Data for '%s'", self._siteid)
            url = "https://api.sl.se/api2/deviations.json?key={}&siteid={}&lineNumber={}". \
                   format(self._apikey, self._siteid,self._lines)

            req = requests.get(url, headers={"User-agent": USER_AGENT}, allow_redirects=True, timeout=5)

        except requests.exceptions.RequestException:
            _LOGGER.error("SL: failed fetching SI2 Data for '%s'", self._siteid)
            return

        if req.status_code == 200:
            self.data = req.json()

        else:
            _LOGGER.error("SL: failed fetching SI2 Data for '%s'"
                          "(HTTP Status_code = %d)", self._siteid,
                          req.status_code)                          
                          
                          
                          
                          
