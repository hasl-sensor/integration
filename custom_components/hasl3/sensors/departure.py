import logging
import math
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import now

from .. import const
from ..haslworker import DepartureData, DepartureKey, HaslWorker, MetaState
from .device import HASLDevice

logger = logging.getLogger(f"custom_components.{const.DOMAIN}.sensors.departure")


class TrafikDepartureSensor(HASLDevice):
    """Trafik Departure Sensor class."""

    _worker: HaslWorker
    _sensordata: Optional[DepartureData]

    unit_table = {
        "min": "min",
        "time": "",
        "updated": "",
    }

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize."""

        self._hass = hass
        self._config = config

        self._siteid: int = config.options[const.CONF_SITE_ID]
        self._sensorproperty = config.options[const.CONF_SENSOR_PROPERTY]

        self._line = int(config.options.get(const.CONF_LINE, 0))
        self._direction: int = config.options[const.CONF_DIRECTION]
        self._timewindow: int = config.options[const.CONF_TIMEWINDOW]

        self._name = f"SL Trafik Departure Sensor {self._siteid} ({self._config.title})"
        self._enabled_sensor = config.options.get(const.CONF_SENSOR)

        self._nextdeparture_minutes = "0"
        self._nextdeparture_expected = "-"
        self._lastupdate = "-"
        self._sensordata = None
        self._worker = hass.data[const.DOMAIN]["worker"]

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-departure-{self._siteid}-sensor-{self._config.data[const.CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.unit_table[self._sensorproperty]

    @property
    def scan_interval(self):
        """Return the scan interval."""

        return int(self._config.options[const.CONF_SCAN_INTERVAL] or 300)

    @property
    def available(self):
        """Return true if value is valid."""
        return bool(self._sensordata)

    @property
    def state(self):
        """Return the state of the sensor."""
        sensorproperty = self._config.options[const.CONF_SENSOR_PROPERTY]

        if not self._sensordata:
            return "Unknown"

        if sensorproperty == "updated":
            return self._sensordata.api_lastrun
        else:
            if (departure := self._nextDeparture()) is None:
                return "-"

            time = departure.expected or departure.scheduled
            if sensorproperty == "min":
                delta = time - now()
                expected_minutes = math.floor(delta.total_seconds() / 60)
                return str(max(0, expected_minutes))

            elif sensorproperty == "time":
                return time.strftime("%H:%M:%S")

        return "-"

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes ."""

        if not self._sensordata:
            return {}

        # Format the next exptected time.
        next_departure = self._nextDeparture()
        if next_departure:
            expected_time = next_departure.expected or next_departure.scheduled
            delta = expected_time - now()
            expected_minutes = max(0, math.floor(delta.total_seconds() / 60))
            expected_time = expected_time.strftime("%H:%M:%S")
        else:
            expected_time = "-"
            expected_minutes = "-"

        # Setup the unit of measure.
        val = {}
        val["unit_of_measurement"] = self.unit_of_measurement
        val["api_result"] = (
            "Ok"
            if self._sensordata.api_result == MetaState.SUCCESS
            else self._sensordata.api_error
        )

        # Set values of the sensor.
        val["scan_interval"] = self.scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )

        if self._sensordata.api_result != MetaState.SUCCESS:
            return val

        if departures := self._sensordata.data:
            val["attribution"] = "Stockholm Lokaltrafik"
            # TODO: fill according to old format
            val["departures"] = departures
            val["deviations"] = []
            val["deviation_count"] = 0
            val["next_departure_minutes"] = expected_minutes
            val["next_departure_time"] = expected_time

        val["last_refresh"] = self._sensordata.api_lastrun.strftime("%Y-%m-%d %H:%M:%S")

        return val

    @property
    def _departure_key(self):
        return DepartureKey(
            self._siteid,
            self._direction or None,
            self._timewindow or None,
            self._line or None,
        )

    def _nextDeparture(self):
        if not self._sensordata or not self._sensordata.data:
            return None

        departures = sorted(
            self._sensordata.data, key=lambda x: x.expected or x.scheduled
        )
        return next(iter(departures), None)

    async def async_update(self):
        """Update the sensor."""

        key = tuple(self._departure_key)
        if existing_data := self._worker.data.departures.get(key):
            sensor_enabled = self._worker.checksensorstate(
                self._enabled_sensor, STATE_ON
            )
            time_to_update = (
                now() - existing_data.api_lastrun
            ).total_seconds() >= self.scan_interval

            if sensor_enabled and time_to_update:
                logger.debug(f"[async_update] {self.unique_id} Fetching sensor data")
                await self._worker.get_departure_data(self._departure_key)
            else:
                logger.debug(
                    f"[async_update] {self.unique_id} Not due for update, skipping. ({sensor_enabled}, {time_to_update})"
                )

            self._sensordata = self._worker.data.departures[key]
        else:
            logger.debug("[async_update] no data yet")
            self._sensordata = None
