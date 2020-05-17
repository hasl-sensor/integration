""" SL Platform Sensor """
import logging

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant, State
from homeassistant.util.dt import now
from .haslworker import HaslWorker as worker
from .globals import get_worker
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .slapi import (
    slapi,
    SLAPI_Error,
    SLAPI_API_Error,
    SLAPI_HTTP_Error
)

from .slapi.const import (
    __version__ as SLAPI_VERSION
)

from .const import (
    DOMAIN,
    VERSION,
    STATE_OFF,
    STATE_ON,
    CONF_SENSOR,
    CONF_ANALOG_SENSORS,
    CONF_TL2_KEY,
    SENSOR_STATUS,
    CONF_INTEGRATION_TYPE,
    CONF_INTEGRATION_ID
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities(await setup_hasl_sensor(hass,config))

async def async_setup_entry(hass, config_entry, async_add_devices):
    async_add_devices(await setup_hasl_sensor(hass, config_entry))

async def setup_hasl_sensor(hass,config):
    sensors = []
    worker = get_worker()
    
    if config.data[CONF_INTEGRATION_TYPE]==SENSOR_STATUS:
        if not config.options[CONF_ANALOG_SENSORS]:
            if CONF_TL2_KEY in config.options:
                await worker.assert_tl2(config.options[CONF_TL2_KEY])
                for sensortype in ["metro","train","local","tram","bus","ferry"]:
                    sensors.append(HASLTrafficProblemSensor(hass,config,sensortype))
            await worker.process_tl2()

    return sensors

class HASLDevice(Entity):
    """HASL Device class."""
    @property
    def device_info(self):
        """Return device information about HASL Device."""
        return {
            "identifiers": {(DOMAIN, f"10ba5386-5fad-49c6-8f03-c7a047cd5aa5-6a618956-520c-41d2-9a10-6d7e7353c7f5")},
            "name": f"SL API Communications Device",
            "manufacturer": "hasl.sorlov.com",
            "model": f"slapi-v{SLAPI_VERSION}",
            "sw_version": VERSION,
        }

class HASLTrafficProblemSensor(HASLDevice):
    """Class to hold Hue Sensor basic info."""

    def __init__(self, hass, config, sensortype):
        """Initialize the sensor object."""
        self._hass = hass
        self._config = config
        self._sensortype = sensortype
        self._enabled_sensor = config.options[CONF_SENSOR]
        self._name = f"SL {self._sensortype.capitalize()} Problem Sensor"
        self._sensordata = []

    async def async_added_to_hass(self):
        """Register update signal handler."""
        async def async_update_state():
            """Update sensor state."""
            await self.async_update_ha_state(True)
            
        async_dispatcher_connect(self.hass,"tl2_data_update", async_update_state)

    def update(self):
         self._sensordata = worker.data.tl2[self._config.options[CONF_TL2_KEY]]       

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name   
   
    @property
    def should_poll(self):
        """No polling needed."""
        return False
        
    @property
    def unique_id(self):
        return f"sl-{self._sensortype}-status-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

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
    def is_on(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return False
        else:
            if self._sensordata["data"][self._sensortype]["status"]=="Good":
                return False
            else:
                return True

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return False
        else:
            if self._sensordata["data"][self._sensortype]["status"]=="Good":
                return False
            else:
                return True

    @property
    def device_class(self):
        """Return the class of this device."""
        return "problem"

    @property
    def device_state_attributes(self):
        """Attributes."""
        val = {}
        
        if self._sensordata == []:
            return val
             
        # Check if sensor is currently updating or not.
        if not self._enabled_sensor == "":
            sensor_state = self._hass.states.get(self._enabled_sensor)
            if sensor_state.state is STATE_ON:
                val['refresh_enabled'] = STATE_ON
            else:
                val['refresh_enabled'] = STATE_OFF            
        else:
            val['refresh_enabled'] = STATE_ON

        
        if self._sensordata["api_result"] == "Success":
            val['api_result'] = "Ok"
        else:
            val['api_result'] = self._sensordata["api_error"]

        # Set values of the sensor.
        val['attribution'] = self._sensordata["attribution"]
        val['status_text'] = self._sensordata["data"][self._sensortype]["status"]
        val['status_icon'] = self._sensordata["data"][self._sensortype]["status_icon"]
        val['events'] = self._sensordata["data"][self._sensortype]["events"]        
        val['last_updated'] = self._sensordata["last_updated"]

        return val
