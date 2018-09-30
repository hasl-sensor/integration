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

__version__ = '0.0.4'

_LOGGER = logging.getLogger(__name__)

CONF_RI4_KEY = 'ri4key'
CONF_SITEID = 'siteid'
CONF_LINES = 'lines'
CONF_NAME = 'name'
CONF_DIRECTION = 'direction'
CONF_ENABLED_SENSOR = 'sensor'

UPDATE_FREQUENCY = timedelta(seconds=60)
FORCED_UPDATE_FREQUENCY = timedelta(seconds=5)

USER_AGENT = "Home Assistant SL Sensor"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RI4_KEY): cv.string,   
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

    data = SlDepartureBoardData(
        config.get(CONF_RI4_KEY),
        config.get(CONF_SITEID),
        config.get(CONF_LINES),
        config.get(CONF_DIRECTION),
    )

    sensors = []
    sensors.append(
        SLDepartureBoardSensor(
            hass,
            data, 
            config.get(CONF_SITEID),
            config.get(CONF_NAME),
            config.get(CONF_ENABLED_SENSOR)
        )
    )
    add_devices(sensors)

class SLDepartureBoardSensor(Entity):
    """Department board for one SL site."""

    def __init__(self, hass, data, siteid, name, enabled_sensor):
        """Initialize"""
        self._hass = hass
        self._sensor = 'sl'
        self._siteid = siteid
        self._name = name or siteid
        self._data = data
        self._nextdeparture = 9999
        self._board = []
        self._error_logged = False  # Keep track of if error has been logged.
        self._enabled_sensor = enabled_sensor

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._sensor, self._name)

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return 'fa-subway'

    @property
    def state(self):
        """ Return number of minutes to the next departure """
        if len(self._board) > 0:
            return self._board[0]['time']

        return 9999

    @property
    def device_state_attributes(self):
        """ Return the sensor attributes ."""

        val = {}
        val['attribution'] = 'Data from sl.se / trafiklab.se'
        val['unit_of_measurement'] = 'min'

        if not(self._data.data) :
            return val

        if len(self._board) > 0:
            val['next_line'] = self._board[0]['line']
            val['next_destination'] = self._board[0]['destination']
            val['next_departure'] = self._board[0]['departure']

        if len(self._board) > 1:
            val['upcoming_line'] = self._board[1]['line']
            val['upcoming_destination'] = self._board[1]['destination']
            val['upcoming_departure'] = self._board[1]['departure']
            
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

    def update(self):
        """Get the departure board."""
        if self._enabled_sensor is not None:
            sensor_state = self._hass.states.get(self._enabled_sensor)
        if self._enabled_sensor is None or sensor_state.state is STATE_ON:
            self._data.update()
            board = []
            if self._data.data['StatusCode'] != 0:
                if not self._error_logged:
                    _LOGGER.warn("Status code: {}, {}".format(self._data.data['StatusCode'], self._data.data['Message']))
                    self._error_logged = True  # Only report error once, until success.
            else:
                if self._error_logged:
                    _LOGGER.warn("API call successful again")
                    self._error_logged = False  # Reset that error has been reported.
                for i,traffictype in enumerate(['Metros','Buses','Trains','Trams', 'Ships']):
                    for idx, value in enumerate(self._data.data['ResponseData'][traffictype]):
                        direction = value['JourneyDirection'] or 0
                        displaytime = value['DisplayTime'] or ''
                        destination = value['Destination'] or ''
                        linenumber = value['LineNumber'] or ''
                        if (int(self._data._direction) == 0 or int(direction) == int(self._data._direction)):
                            if(self._data._lines is None or (linenumber in self._data._lines)):
                                diff = self.parseDepartureTime(displaytime)
                                board.append({"line":linenumber,"departure":displaytime,"destination":destination, 'time': diff})
            self._board = sorted(board, key=lambda k: k['time'])
            _LOGGER.info(self._board)


class SlDepartureBoardData(object):
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
            _LOGGER.info("fetching SL Data for '%s'", self._siteid)
            url = "https://api.sl.se/api2/realtimedeparturesV4.json?key={}&siteid={}". \
                   format(self._apikey, self._siteid)

            req = requests.get(url, headers={"User-agent": USER_AGENT}, allow_redirects=True, timeout=5)

        except requests.exceptions.RequestException:
            _LOGGER.error("failed fetching SL Data for '%s'", self._siteid)
            return

        if req.status_code == 200:
            self.data = req.json()

        else:
            _LOGGER.error("failed fetching SL Data for '%s'"
                          "(HTTP Status_code = %d)", self._siteid,
                          req.status_code)