"""Simple service for SL (Storstockholms Lokaltrafik)"""
import datetime
from datetime import timedelta
import logging

import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, ToggleEntity
from homeassistant.helpers.event import (async_track_point_in_utc_time,
                                         async_track_utc_time_change,
										 track_time_interval)
from homeassistant.util import dt as dt_util
from homeassistant.const import (ATTR_FRIENDLY_NAME, ATTR_NAME, CONF_PREFIX,
                                 CONF_USERNAME, STATE_ON, STATE_OFF)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

__version__ = '0.0.9'
_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = []
REQUIREMENTS = ['hasl==1.0.2']

CONF_RI4_KEY = 'ri4key'
CONF_SI2_KEY = 'si2key'
CONF_SITEID = 'siteid'
CONF_LINES = 'lines'
CONF_DIRECTION = 'direction'
CONF_ENABLED_SENSOR = 'sensor'
CONF_INTERVAL = 'interval'
CONF_TIMEWINDOW = 'timewindow'

DEFAULT_INTERVAL=5
DEFAULT_TIMEWINDOW=30
DEFAULT_PREFIX='HASL'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(ATTR_FRIENDLY_NAME): cv.string,
	vol.Optional(ATTR_NAME): cv.string,
    vol.Required(CONF_RI4_KEY): cv.string,   
    vol.Required(CONF_SI2_KEY): cv.string,
    vol.Required(CONF_SITEID): cv.string,
	vol.Optional(CONF_PREFIX,default=DEFAULT_PREFIX): cv.string,
    vol.Optional(CONF_LINES): vol.All(
        cv.ensure_list, [cv.positive_int]),
    vol.Optional(CONF_DIRECTION): ,
    vol.Optional(CONF_TIMEWINDOW,default=DEFAULT_TIMEWINDOW): vol.All(
	    cv.positive_int, vol.Range(min=0,max=60)),
    vol.Optional(CONF_ENABLED_SENSOR): cv.string,
    vol.Optional(CONF_INTERVAL,default=DEFAULT_INTERVAL): vol.All(
	    cv.time_period, vol.Range(min=5,max=60))
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensors."""

    sensors = []
    sensors.append(
        SLTraficInformationSensor(
            hass,
            config.get(CONF_SI2_KEY),
	        config.get(CONF_RI4_KEY),
			config.get(CONF_SITEID),
			config.get(CONF_LINES),
			config.get(CONF_SITEID),
			config.get(ATTR_NAME),
            config.get(ATTR_FRIENDLY_NAME),			
            config.get(CONF_PREFIX),			
            config.get(CONF_ENABLED_SENSOR),
            config.get(CONF_INTERVAL),
            config.get(CONF_DIRECTION),
			config.get(CONF_TIMEWINDOW)
        )
    )
    add_devices(sensors)

class SLTraficInformationSensor(Entity):
    """Department board for one SL site."""

    def __init__(self, hass, si2key, ri4key, siteid, lines, name,
	             friendly_name, prefix, enabled_sensor, interval,
				 direction, timewindow):
				 
        """Initialize""" 
		from hasl import hasl		
		self._haslapi = hasl(si2key,ri4key,siteid,lines,timewindow);
        self._hass = hass
		
        self._sensor = name or "{}_{}".format(prefix,siteid);
        self._name = name or "{}_{}".format(prefix,siteid);
        self._lines = lines
        self._siteid = siteid
        self._friendly_name = friendly_name		
        self._enabled_sensor = enabled_sensor
		
		self._departuredata = '{}'
		self._deviationdata = '{}'
        self._departure_table = []
        self._deviations_table = []
		self._direction = 0
		self._timewindow = timewindow
		
		track_time_interval(hass, self.update, interval)

    @property
    def name(self):
        """Return the name of the sensor."""
        return _friendly_name

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return 'mdi:train-car'

    @property
    def state(self):
        """ Return number of minutes to the next departure """
        if len(self._departure_table) > 0:
            return self._departure_table[0]['time']

        return -1

    @property
    def device_state_attributes(self):
        """ Return the sensor attributes ."""

        val = {}
        val['attribution'] = 'Stockholms Lokaltrafik'
        val['unit_of_measurement'] = 'min'
        val['departure_board'] = self._departure_table
        val['deviations'] = self._deviations_table

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
            _LOGGER.info('SL Sensor updating departures for site %s...', self._siteid)
            self._departuredata = _haslapi.get_departures();
            departures = []
                iconswitcher = {
                    "Buses": "mdi:bus",
                    "Trams": "mdi:tram",
                    "Ships": "mdi:boat",
                    "Metros": "mdi:subway-variant",
                    "Trains": "mdi:train"
                }
                for i,traffictype in enumerate(['Metros','Buses','Trains','Trams', 'Ships']):
                    for idx, value in enumerate(self._departuredata.data['ResponseData'][traffictype]):
                        direction = value['JourneyDirection'] or 0
                        displaytime = value['DisplayTime'] or ''
                        destination = value['Destination'] or ''
                        linenumber = value['LineNumber'] or ''
                        icon = iconswitcher.get(traffictype, "mdi:train-car")
                        if (int(self._direction) == 0 or int(direction) == int(self._direction)):
                            if(self._lines is None or (linenumber in self._lines)):
                                diff = self.parseDepartureTime(displaytime)
                                departures.append({"line":linenumber,"direction":direction,"departure":displaytime,"destination":destination, 'time': diff, 'type': traffictype, 'icon': icon})
            self._departure_table = sorted(departures, key=lambda k: k['time'])
            _LOGGER.info(self._departure_table)
            
            _LOGGER.info('SL Sensor updating deviations for site %s...', self._siteid)
            self._deviationdata = _haslapi.get_deviations();
            deviations = []
                for idx, value in enumerate(self._deviationdata.data['ResponseData']):
                    deviations.append({"updated":value['Updated'],"title":value['Header'],"fromDate":value['FromDateTime'],"toDate":value['UpToDateTime'], 'details': value['Details'], 'sortOrder': value['SortOrder']})
            self._deviations_table = sorted(deviations, key=lambda k: k['sortOrder'])
            _LOGGER.info(self._deviations_table)

                          
                          
