""" SL Platform Sensor """
import logging
import math
import datetime
import jsonpickle
import time
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, State
from homeassistant.util.dt import now
from .haslworker import HaslWorker as worker
from .globals import get_worker

from .slapi import (
    slapi,
    slapi_fp,
    slapi_tl2,
    slapi_ri4,
    slapi_si2,
    SLAPI_Error,
    SLAPI_API_Error,
    SLAPI_HTTP_Error
)
from .slapi.const import (
    __version__ as slapi_version
)

from .const import (
    DOMAIN,
    VERSION,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
    CONF_ANALOG_SENSORS,
    CONF_FP_PT,
    CONF_FP_RB,
    CONF_FP_TVB,
    CONF_FP_SB,
    CONF_FP_LB,
    CONF_FP_SPVC,
    CONF_FP_TB1,
    CONF_FP_TB2,
    CONF_FP_TB3,       
    CONF_TL2_KEY,
    CONF_RI4_KEY,
    CONF_SI2_KEY,
    CONF_RP3_KEY,
    CONF_SITE_ID,
    CONF_SENSOR,
    CONF_TRIPS,
    CONF_LINES,
    CONF_INTEGRATION_TYPE,
    CONF_INTEGRATION_ID,
    CONF_DEVIATION_LINES,
    CONF_DEVIATION_STOPS,
    CONF_DEVIATION_LINE,
    CONF_DEVIATION_STOP,
    CONF_SENSOR_PROPERTY,
    CONF_DIRECTION,
    CONF_TIMEWINDOW,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE,
    CONF_DESTINATION,
    STATE_OFF,
    STATE_ON
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities(await setup_hasl_sensor(hass,config))

async def async_setup_entry(hass, config_entry, async_add_devices):
    async_add_devices(await setup_hasl_sensor(hass, config_entry))

async def setup_hasl_sensor(hass,config):
    """Setup sensor platform."""
    sensors = []
    worker = get_worker()
   
    #try:

    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_STANDARD:
        if CONF_RI4_KEY in config.options and CONF_SITE_ID in config.options:
            await worker.assert_ri4(config.options[CONF_RI4_KEY],config.options[CONF_SITE_ID])
            sensors.append(HASLDepartureSensor(hass,config,config.options[CONF_SITE_ID]))
        await worker.process_ri4();

    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_DEVIATION:
        if CONF_SI2_KEY in config.options:
            for deviationid in ','.join(set(config.options[CONF_DEVIATION_LINES].split(','))).split(','):
                await worker.assert_si2_line(config.options[CONF_SI2_KEY],deviationid)
                sensors.append(HASLDeviationSensor(hass,config,CONF_DEVIATION_LINE,deviationid))
            for deviationid in ','.join(set(config.options[CONF_DEVIATION_STOPS].split(','))).split(','):
                await worker.assert_si2_stop(config.options[CONF_SI2_KEY],deviationid)
                sensors.append(HASLDeviationSensor(hass,config,CONF_DEVIATION_STOP,deviationid))
        await worker.process_si2()

    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_ROUTE:
        if CONF_RP3_KEY in config.options:            
            await worker.assert_rp3(config.options[CONF_RP3_KEY],config.options[CONF_SOURCE],config.options[CONF_DESTINATION])
            sensors.append(HASLRouteSensor(hass,config,f"{config.options[CONF_SOURCE]}-{config.options[CONF_DESTINATION]}"))
        await worker.process_rp3()
        
    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_STATUS:
        if config.options[CONF_ANALOG_SENSORS]:
            if CONF_TL2_KEY in config.options:
                await worker.assert_tl2(config.options[CONF_TL2_KEY])
                for sensortype in ["metro","train","local","tram","bus","ferry"]:
                    sensors.append(HASLTrafficStatusSensor(hass,config,sensortype))
            await worker.process_tl2()
        
    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_VEHICLE_LOCATION:
        if CONF_FP_PT in config.options and config.options[CONF_FP_PT]:
            await worker.assert_fp("PT")
            sensors.append(HASLVehicleLocationSensor(hass,config,'PT'))
        if CONF_FP_RB in config.options and config.options[CONF_FP_RB]:
            await worker.assert_fp("RB")
            sensors.append(HASLVehicleLocationSensor(hass,config,'RB'))
        if CONF_FP_TVB in config.options and config.options[CONF_FP_TVB]:
            await worker.assert_fp("TVB")
            sensors.append(HASLVehicleLocationSensor(hass,config,'TVB'))
        if CONF_FP_SB in config.options and config.options[CONF_FP_SB]:
            await worker.assert_fp("SB")
            sensors.append(HASLVehicleLocationSensor(hass,config,'SB'))
        if CONF_FP_LB in config.options and config.options[CONF_FP_LB]:
            await worker.assert_fp("LB")
            sensors.append(HASLVehicleLocationSensor(hass,config,'LB'))
        if CONF_FP_SPVC in config.options and config.options[CONF_FP_SPVC]:
            await worker.assert_fp("SpvC")
            sensors.append(HASLVehicleLocationSensor(hass,config,'SpvC'))
        if CONF_FP_TB1 in config.options and config.options[CONF_FP_TB1]:
            await worker.assert_fp("TB1")
            sensors.append(HASLVehicleLocationSensor(hass,config,'TB1'))
        if CONF_FP_TB2 in config.options and config.options[CONF_FP_TB2]:
            await worker.assert_fp("TB2")
            sensors.append(HASLVehicleLocationSensor(hass,config,'TB2'))
        if CONF_FP_TB2 in config.options and config.options[CONF_FP_TB2]:
            await worker.assert_fp("TB3")
            sensors.append(HASLVehicleLocationSensor(hass,config,'TB3'))
        await worker.process_fp();

    #except:
    #    return

    return sensors
    
class HASLDevice(Entity):
    """HASL Device class."""
    @property
    def device_info(self):
        """Return device information about HASL Device."""
        #Keep this for now if reverting to a per integration device but cannot see why we would do that
        #"identifiers": {(DOMAIN, f"10ba5386-5fad-49c6-8f03-c7a047cd5aa5-{self._config.data[CONF_INTEGRATION_ID]}")},
        #"name": f"SL {self._config.data[CONF_INTEGRATION_TYPE]} Device",
        return {
            "identifiers": {(DOMAIN, f"10ba5386-5fad-49c6-8f03-c7a047cd5aa5-6a618956-520c-41d2-9a10-6d7e7353c7f5")},
            "name": f"SL API Communications Device",
            "manufacturer": "hasl.sorlov.com",
            "model": f"slapi-v{slapi_version}",
            "sw_version": VERSION,
        }
        
class HASLRouteSensor(HASLDevice):
    """HASL Train Location Sensor class."""

    def __init__(self, hass, config, trip):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._trip = trip
        self._name = f"SL {self._trip} Route Sensor"
        self._sensordata = []
        self._scan_interval = self._config.options[CONF_SCAN_INTERVAL] or 300

    async def async_update(self):
        """Update the sensor."""
        worker = get_worker()

        if worker.system.status.background_task:
            return

        if worker.data.rp3[self._trip]["api_lastrun"]:
            if worker.checksensorstate(self._enabled_sensor,STATE_ON):
                if worker.getminutesdiff(now().strftime('%Y-%m-%d %H:%M:%S'), worker.data.rp3[self._trip]["api_lastrun"]) > self._config.options[CONF_SCAN_INTERVAL]:
                    await worker.process_rp3()

        self._sensordata = worker.data.rp3[self._trip]
        
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-route-{self._trip}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return 'Unknown'
        else:
            return len(self._sensordata["trips"])

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def device_state_attributes(self):
        worker = get_worker()
        val = {}
        
        if self._sensordata == []:
            return val
                      
        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Success"
        else:
            val['api_result'] = self._sensordata["api_error"]

        # Set values of the sensor.
        val['scan_interval'] = self._scan_interval
        val['refresh_enabled'] = worker.checksensorstate(self._enabled_sensor,STATE_ON)
        val['attribution'] = self._sensordata["attribution"]
        val['trips'] = self._sensordata["trips"]
        val['transfers'] = self._sensordata["transfers"]
        val['price'] = self._sensordata["price"]
        val['time'] = self._sensordata["time"]
        val['duration'] = self._sensordata["duration"]
        val['first_leg'] = self._sensordata["first_leg"]
        val['last_refresh'] = self._sensordata["last_updated"]
        val['trip_count'] = len(self._sensordata["trips"])
        
        return val                  
        
        
class HASLDepartureSensor(HASLDevice):
    """HASL Departure Sensor class."""

    def __init__(self, hass, config, siteid):
        """Initialize."""
        
        unit_table = {
            'min': 'min',
            'time': '',
            'deviations': '',
            'updated': '',
        }
    
        self._hass = hass
        self._config = config
        self._lines = config.options[CONF_LINES]
        self._siteid = str(siteid)
        self._name = f"SL Departure Sensor {self._siteid}"
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._sensorproperty = config.options[CONF_SENSOR_PROPERTY]
        self._direction = config.options[CONF_DIRECTION]
        self._timewindow = config.options[CONF_TIMEWINDOW]
        self._nextdeparture_minutes = '0'
        self._nextdeparture_expected = '-'
        self._lastupdate = '-'
        self._unit_of_measure = unit_table.get(self._config.options[CONF_SENSOR_PROPERTY], 'min')
        self._sensordata = None
        self._scan_interval = self._config.options[CONF_SCAN_INTERVAL] or 300
        
    async def async_update(self):
        """Update the sensor."""
        worker = get_worker()

        if worker.system.status.background_task:
            return

        if worker.data.ri4[self._siteid]["api_lastrun"]:
            if worker.checksensorstate(self._enabled_sensor,STATE_ON):
                if worker.getminutesdiff(now().strftime('%Y-%m-%d %H:%M:%S'), worker.data.ri4[self._siteid]["api_lastrun"]) > self._config.options[CONF_SCAN_INTERVAL]:
                    await worker.process_ri4()

        self._sensordata = worker.data.ri4[self._siteid]
        
        if f"stop_{self._siteid}" in worker.data.si2:
            self._sensordata["deviations"] = worker.data.si2[f"stop_{self._siteid}"]["data"]
        else:
            self._sensordata["deviations"] = []
               
        self._last_updated = self._sensordata["last_updated"]
        
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-stop-{self._siteid}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        sensorproperty = self._config.options[CONF_SENSOR_PROPERTY]

        if self._sensordata == []:
            return 'Unknown'
            
        if sensorproperty is 'min':
            next_departure = self.nextDeparture()
            if not next_departure:
                return '-'

            delta = next_departure['expected'] - datetime.datetime.now()
            expected_minutes = math.floor(delta.total_seconds() / 60)
            return expected_minutes

        # If the sensor should return the time at which next departure occurs.
        if sensorproperty is 'time':
            next_departure = self.nextDeparture()
            if not next_departure:
                return '-'

            expected = next_departure['expected'].strftime('%H:%M:%S')
            return expected

        # If the sensor should return the number of deviations.
        if sensorproperty is 'deviations':
            return len(self._sensordata["deviations"])

        if sensorproperty is 'updated':
            return self._sensordata["last_updated"]
            
        # Failsafe
        return '-'
        
    def nextDeparture(self):
        if not self._sensordata:
            return None

        now = datetime.datetime.now()
        for departure in self._sensordata["data"]:
            if departure['expected'] > now:
                return departure
        return None        

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measure

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def device_state_attributes(self):
        """ Return the sensor attributes ."""

        # Initialize the state attributes.
        worker = get_worker()
        val = {}

        if self._sensordata == [] or self._sensordata is None:
            return val

        # Format the next exptected time.
        next_departure = self.nextDeparture()
        if next_departure:
            expected_time = next_departure['expected']
            delta = expected_time - datetime.datetime.now()
            expected_minutes = math.floor(delta.total_seconds() / 60)
            expected_time = expected_time.strftime('%H:%M:%S')
        else:
            expected_time = '-'
            expected_minutes = '-'

        # Setup the unit of measure.
        if self._unit_of_measure is not '':
            val['unit_of_measurement'] = self._unit_of_measure

        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Ok"
        else:
            val['api_result'] = self._sensordata["api_error"]
            
        # Set values of the sensor.
        val['scan_interval'] = self._scan_interval
        val['refresh_enabled'] = worker.checksensorstate(self._enabled_sensor,STATE_ON)
        val['attribution'] = self._sensordata["attribution"]
        val['departures'] = self._sensordata["data"]
        val['deviations'] = self._sensordata["deviations"]
        val['last_refresh'] = self._sensordata["last_updated"]
        val['next_departure_minutes'] = expected_minutes
        val['next_departure_time'] = expected_time
        val['deviation_count'] = len(self._sensordata["deviations"])

        return val  
        
class HASLDeviationSensor(HASLDevice):
    """HASL Deviation Sensor class."""

    def __init__(self, hass, config, deviationtype, deviationkey):
        """Initialize."""
        self._config = config
        self._hass = hass
        self._deviationkey = deviationkey
        self._deviationtype = deviationtype
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._name = f"SL {self._deviationtype.capitalize()} Deviation Sensor {self._deviationkey}"
        self._sensordata = []
        self._enabled_sensor
        self._scan_interval = self._config.options[CONF_SCAN_INTERVAL] or 300
        
    async def async_update(self):
        """Update the sensor."""
        worker = get_worker()

        if worker.system.status.background_task:
            return


        if worker.data.si2[f"{self._deviationtype}_{self._deviationkey}"]["api_lastrun"]:
            if worker.checksensorstate(self._enabled_sensor,STATE_ON):
                if worker.getminutesdiff(now().strftime('%Y-%m-%d %H:%M:%S'), worker.data.si2[f"{self._deviationtype}_{self._deviationkey}"]["api_lastrun"]) > self._config.options[CONF_SCAN_INTERVAL]:
                    await worker.process_si2()
                    
        self._sensordata = worker.data.si2[f"{self._deviationtype}_{self._deviationkey}"]
        
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-deviation-{self._deviationtype}-{self._deviationkey}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return 'Unknown'
        else:
            return len(self._sensordata["data"])

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def device_state_attributes(self):
        """ Return the sensor attributes."""
        worker = get_worker()
        val = {}
        
        if self._sensordata == []:
            return val        
                
        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Ok"
        else:
            val['api_result'] = self._sensordata["api_error"]

        # Set values of the sensor.
        val['scan_interval'] = self._scan_interval
        val['refresh_enabled'] = worker.checksensorstate(self._enabled_sensor,STATE_ON)
        val['attribution'] = self._sensordata["attribution"]
        val['deviations'] = self._sensordata["data"]
        val['last_refresh'] = self._sensordata["last_updated"]
        val['deviation_count'] = len(self._sensordata["data"])
        
        return val           
        
class HASLVehicleLocationSensor(HASLDevice):
    """HASL Train Location Sensor class."""

    def __init__(self, hass, config, vehicletype):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._vehicletype = vehicletype
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._name = f"SL {self._vehicletype} Location Sensor"
        self._sensordata = []
        self._scan_interval = self._config.options[CONF_SCAN_INTERVAL] or 300

    async def async_update(self):
        """Update the sensor."""
        worker = get_worker()

        if worker.system.status.background_task:
            return

        if worker.data.fp[self._vehicletype]["api_lastrun"]:
            if worker.checksensorstate(self._enabled_sensor,STATE_ON):
                if worker.getminutesdiff(now().strftime('%Y-%m-%d %H:%M:%S'), worker.data.fp[self._vehicletype]["api_lastrun"]) > self._config.options[CONF_SCAN_INTERVAL]:
                    await worker.process_fp()

        self._sensordata = worker.data.fp[self._vehicletype]
        
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-fl-{self._vehicletype}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return 'Unknown'
        else:
            return len(self._sensordata["data"])

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def device_state_attributes(self):
        worker = get_worker()
        val = {}
        
        if self._sensordata == []:
            return val
                      
        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Success"
        else:
            val['api_result'] = self._sensordata["api_error"]

        # Set values of the sensor.
        val['scan_interval'] = self._scan_interval
        val['refresh_enabled'] = worker.checksensorstate(self._enabled_sensor,STATE_ON)
        val['attribution'] = self._sensordata["attribution"]
        val['data'] = self._sensordata["data"]
        val['last_refresh'] = self._sensordata["last_updated"]
        val['vehicle_count'] = len(self._sensordata["data"])
        
        return val           
     

class HASLTrafficStatusSensor(HASLDevice):
    """HASL Traffic Status Sensor class."""

    def __init__(self, hass, config, sensortype):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._sensortype = sensortype
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._name = f"SL {self._sensortype.capitalize()} Status Sensor"
        self._sensordata = []
        self._scan_interval = self._config.options[CONF_SCAN_INTERVAL] or 300

    async def async_update(self):
        """Update the sensor."""
        worker = get_worker()

        if worker.system.status.background_task:
            return

        if worker.data.tl2[self._config.options[CONF_TL2_KEY]]["api_lastrun"]:
            if worker.checksensorstate(self._enabled_sensor,STATE_ON):
                if worker.getminutesdiff(now().strftime('%Y-%m-%d %H:%M:%S'), worker.data.tl2[self._config.options[CONF_TL2_KEY]]["api_lastrun"]) > self._config.options[CONF_SCAN_INTERVAL]:
                    await worker.process_tl2()
                    
        self._sensordata = worker.data.tl2[self._config.options[CONF_TL2_KEY]]
        
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-{self._sensortype}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return 'Unknown'
        else:
            return self._sensordata["data"][self._sensortype]["status"]

    @property
    def icon(self):
        trafficTypeIcons = {
            'ferry': 'mdi:ferry',
            'bus': 'mdi:bus',
            'tram': 'mdi:tram',
            'train': 'mdi:train',
            'local': 'mdi:train-variant',
            'metro': 'mdi:subway-variant'
        } 

        return trafficTypeIcons.get(self._sensortype)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval
        
    @property
    def device_state_attributes(self):
        worker = get_worker()
        val = {}
        
        if self._sensordata == []:
            return val
                    
        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Ok"
        else:
            val['api_result'] = self._sensordata["api_error"]

        # Set values of the sensor.
        val['scan_interval'] = self._scan_interval
        val['refresh_enabled'] = worker.checksensorstate(self._enabled_sensor,STATE_ON)
        val['attribution'] = self._sensordata["attribution"]
        val['status_icon'] = self._sensordata["data"][self._sensortype]["status_icon"]
        val['events'] = self._sensordata["data"][self._sensortype]["events"]        
        val['last_updated'] = self._sensordata["last_updated"]

        return val
        
