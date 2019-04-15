"""Simple service for SL (Storstockholms Lokaltrafik)"""
import datetime
from datetime import timedelta
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (async_track_point_in_utc_time,
                                         async_track_utc_time_change,
                                         track_time_interval)
from homeassistant.util import dt as dt_util
from homeassistant.util import Throttle
from homeassistant.const import (ATTR_FRIENDLY_NAME, ATTR_NAME, CONF_PREFIX,
                                 CONF_USERNAME, STATE_ON, STATE_OFF,
                                 CONF_SCAN_INTERVAL)
import homeassistant.helpers.config_validation as cv

__version__ = '1.0.1'
_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = []
REQUIREMENTS = ['hasl==1.1.0']

CONF_RI4_KEY = 'ri4key'
CONF_SI2_KEY = 'si2key'
CONF_SITEID = 'siteid'
CONF_LINES = 'lines'
CONF_DIRECTION = 'direction'
CONF_ENABLED_SENSOR = 'sensor'
CONF_TIMEWINDOW = 'timewindow'

DEFAULT_INTERVAL=timedelta(minutes=10)
DEFAULT_TIMEWINDOW=30

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RI4_KEY): cv.string,   
    vol.Required(CONF_SI2_KEY): cv.string,
    vol.Required(CONF_SITEID): cv.string,
    vol.Optional(ATTR_FRIENDLY_NAME): cv.string,
    vol.Optional(CONF_LINES): cv.string,
    vol.Optional(CONF_DIRECTION): cv.string,
    vol.Optional(CONF_TIMEWINDOW,default=DEFAULT_TIMEWINDOW):
        vol.All(vol.Coerce(int), vol.Range(min=0,max=60)),
    vol.Optional(CONF_ENABLED_SENSOR): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL):
        vol.Any(cv.time_period, cv.positive_timedelta),
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
            config.get(ATTR_FRIENDLY_NAME),            
            config.get(CONF_ENABLED_SENSOR),
            config.get(CONF_SCAN_INTERVAL),
            config.get(CONF_DIRECTION),
            config.get(CONF_TIMEWINDOW)
        )
    )
    add_devices(sensors)

class SLTraficInformationSensor(Entity):
    """Department board for one SL site."""

    def __init__(self, hass, si2key, ri4key, siteid, lines,
                 friendly_name, enabled_sensor, interval,
                 direction, timewindow):
                 
        """Initialize""" 
        from hasl import hasl        
        self._haslapi = hasl(si2key,ri4key,siteid,lines,timewindow);
        self._hass = hass 
        self._uniqueid = "hasl-{}-{}".format(siteid,direction)    
        self._name = friendly_name or "hasl_{}_{}".format(siteid,direction)
        self._lines = lines
        self._siteid = siteid
        self._enabled_sensor = enabled_sensor
        
        self._departure_table = []
        self._deviations_table = []
        self._direction = direction
        self._timewindow = timewindow
        self._nextdeparture_minutes = '0'
        self._nextdeparture_expected = '-'
        self._lastupdate = '-'
        
        #track_time_interval(hass, self.update, interval)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the name of the sensor."""
        return self._uniqueid

    @property
    def icon(self):
        """ Return the icon for the frontend."""
        return 'mdi:train-car'

    @property
    def state(self):
        """ Return number of minutes to the next departure """
        return self._nextdeparture_minutes
        
    @property
    def device_state_attributes(self):
        """ Return the sensor attributes ."""

        expected = self._nextdeparture_expected
        if expected is not '-':
            expected = datetime.datetime.strptime(self._nextdeparture_expected,
                '%Y-%m-%dT%H:%M:%S')
            expected = expected.strftime('%H:%M:%S')
            
        refresh = self._lastupdate
        if self._lastupdate is not '-':
            refresh = refresh.strftime('%Y-%m-%d %H:%M:%S')
            
        val = {}
        val['attribution'] = 'Stockholms Lokaltrafik'
        val['unit_of_measurement'] = 'min'
        val['next_departure_minutes'] = self._nextdeparture_minutes
        val['next_departure_expected'] = expected
        val['departures'] = self._departure_table
        val['deviations'] = self._deviations_table
        val['last_refresh'] = refresh
        
        if self._enabled_sensor is not None:
            sensor_state = self._hass.states.get(self._enabled_sensor)
            
        if self._enabled_sensor is None or sensor_state.state is STATE_ON:
            val['refresh_enabled'] = STATE_ON
        else:
            val['refresh_enabled'] = STATE_OFF

        return val

    def parseDepartureTime(self, t):
        """ weird time formats from the API,
        do some quick and dirty conversions """

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

    @Throttle(DEFAULT_INTERVAL)
    def update(self):
        """Get the departure board."""
        if self._enabled_sensor is not None:
            sensor_state = self._hass.states.get(self._enabled_sensor)
            
        if self._enabled_sensor is None or sensor_state.state is STATE_ON:
            _LOGGER.info('SL Sensor updating departures for site %s...',
                self._siteid)
                
            departuredata = self._haslapi.get_departures();
            departures = []
            
            iconswitcher = {
                "Buses": "mdi:bus",
                "Trams": "mdi:tram",
                "Ships": "mdi:boat",
                "Metros": "mdi:subway-variant",
                "Trains": "mdi:train"
            }
            
            for i,traffictype in enumerate(
                ['Metros','Buses','Trains','Trams', 'Ships']):
                
                for idx, value in enumerate(
                    departuredata['ResponseData'][traffictype]):
                    
                    direction = value['JourneyDirection'] or 0
                    displaytime = value['DisplayTime'] or ''
                    destination = value['Destination'] or ''
                    linenumber = value['LineNumber'] or ''
                    expected = value['ExpectedDateTime'] or ''
                    icon = iconswitcher.get(traffictype, "mdi:train-car")
                    if (int(self._direction) == 0 or
                        int(direction) == int(self._direction)):
                        if(self._lines is None or (linenumber in self._lines)):
                            diff = self.parseDepartureTime(displaytime)
                            departures.append({'line':linenumber,
                                               'direction':direction,
                                               'departure':displaytime,
                                               'destination':destination,
                                               'time': diff,
                                               'expected': expected,
                                               'type': traffictype,
                                               'icon': icon})
                                               
        self._departure_table = sorted(departures, key=lambda k: k['time'])
        
        _LOGGER.info('SL Sensor updating deviations for site %s...',
            self._siteid)

        deviationdata = self._haslapi.get_deviations();
        deviations = []

        for idx, value in enumerate(deviationdata['ResponseData']):
            deviations.append({'updated':value['Updated'],
                               'title':value['Header'],
                               'fromDate':value['FromDateTime'],
                               'toDate':value['UpToDateTime'],
                               'details': value['Details'],
                               'sortOrder': value['SortOrder']})

            self._deviations_table = sorted(deviations,
                key=lambda k: k['sortOrder'])

        self._lastupdate = datetime.datetime.now()
        if len(self._departure_table) > 0:
            self._nextdeparture_minutes = self._departure_table[0]['time']
            self._nextdeparture_expected = self._departure_table[0]['expected']
        else:
            self._nextdeparture_minutes = '-'
            self._nextdeparture_expected = '-'
                          
                          
