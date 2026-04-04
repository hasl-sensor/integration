import logging
from asyncio import timeout
from datetime import datetime, timedelta
from functools import cached_property
from typing import cast
from zoneinfo import ZoneInfo

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import STATE_ON, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector as sel
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.device_registry import async_get as get_dr
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util.dt import async_get_time_zone, now

from .. import const
from ..rrapi.client import ResRobotClient
from ..rrapi.model import ListOfDepartures
from ..rrapi.utils import (
    map_rr_departures_to_legacy_departures,
    map_rr_departures_to_v4_departures,
)
from .device import SL_TRAFFIK_DEVICE_INFO

logger = logging.getLogger(__name__)


ATTRIBUTION = "Samtrafiken Resrobot"
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_SOURCE): sel.TextSelector(),
        vol.Optional(const.CONF_SENSOR): sel.EntitySelector(
            sel.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(const.CONF_SCAN_INTERVAL, default=300): sel.NumberSelector(
            sel.NumberSelectorConfig(
                min=0,
                unit_of_measurement="seconds",
                mode=sel.NumberSelectorMode.BOX,
            )
        ),
    }
)


class DepartureDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    config_entry: ConfigEntry
    friendly_name: str
    timezone: ZoneInfo

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        self.api_key: str = config_entry.data[const.CONF_API_KEY]
        self.origin: str = subentry.data[const.CONF_SOURCE]
        self._sensor_id: str | None = subentry.data.get(const.CONF_SENSOR)
        self.friendly_name = subentry.title
        self.subentry = subentry
        self.get_device = lambda: get_dr(hass).async_get_device(
            {(const.DOMAIN, subentry.subentry_id)}
        )
        interval = timedelta(seconds=subentry.data[const.CONF_SCAN_INTERVAL])

        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            config_entry=config_entry,
            name=const.DOMAIN,
            update_interval=interval,
        )

    async def _async_update_data(self):
        if (device := self.get_device()) and device.disabled:
            self.logger.debug(
                "Not updating %s. Device is off", self.subentry.subentry_id
            )
            return self.data

        if self._sensor_id and not self.hass.states.is_state(self._sensor_id, STATE_ON):
            self.logger.debug(
                'Not updating %s. Sensor "%s" is off',
                self.subentry.subentry_id,
                self._sensor_id,
            )

            return self.data

        self.timezone = cast(ZoneInfo, await async_get_time_zone("Europe/Stockholm"))
        client = ResRobotClient(async_get_clientsession(self.hass), self.api_key)
        async with timeout(10):
            try:
                departures = await client.get_departures(self.origin)
            except Exception as error:
                logger.error(
                    "Failed to fetch departures for %s: %s",
                    self.origin,
                    error,
                )
                raise UpdateFailed(
                    f"Failed to fetch departures for {self.origin}"
                ) from error

        return departures

    def get_legacy_data(self):
        if data := self.data:
            return map_rr_departures_to_legacy_departures(
                cast(ListOfDepartures, data), now(), self.timezone
            )

    def get_modern_data(self):
        if data := self.data:
            return map_rr_departures_to_v4_departures(
                cast(ListOfDepartures, data), self.timezone
            )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
) -> list[Entity]:
    """Set up the sensor platform."""

    coordinator = DepartureDataUpdateCoordinator(hass, entry, subentry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data[const.KEY_COORDINATORS].append(coordinator)

    context = {
        "id": subentry.subentry_id,
        "type": subentry.data[const.CONF_INTEGRATION_TYPE],
        "name": subentry.title,
    }
    return [
        ResRobotDepartureLegacySensor(coordinator, context),
        ResRobotDepartureV4Sensor(coordinator, context),
        ResRobotDepartureMinSensor(coordinator, context),
        ResRobotDepartureTimeSensor(coordinator, context),
    ]


class ResRobotBaseDepartureSensor(
    CoordinatorEntity[DepartureDataUpdateCoordinator],
    SensorEntity,
):
    def entity_description(self):
        sid = self.coordinator_context["id"]
        _type = self.coordinator_context["type"]
        return {
            "key": f"{self.coordinator.config_entry.entry_id}_{_type}_{sid}",
            "icon": "mdi:train",
            "has_entity_name": True,
            "name": f"{self.coordinator_context['name']}",
        }

    @property
    def unique_id(self):
        sid = self.coordinator_context["id"]
        _type = self.coordinator_context["type"]
        return f"{self.coordinator.config_entry.entry_id}_{_type}_{sid}"

    def nextDeparture(self):
        if data := self.coordinator.get_modern_data():
            departures = sorted(
                data,
                key=lambda x: x.get("expected", None) or x.get("scheduled", None),
            )
            return next(iter(departures), None)

    @cached_property
    def device_info(self) -> DeviceInfo:
        return {
            **SL_TRAFFIK_DEVICE_INFO,
            "identifiers": {(const.DOMAIN, self.coordinator_context["id"])},
            "name": "Departure Sensor",
        }


class ResRobotDepartureV4Sensor(ResRobotBaseDepartureSensor):
    """
    Contains departures mapped for compatibility with Departure Card V4.
    """

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset({"departures"})

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            key="departures",
            icon="mdi:swap-horizontal",
            has_entity_name=True,
            name=f"{data['name']} departures",
        )

    @property
    def native_value(self):
        if data := self.coordinator.get_modern_data():
            return len(data)

        return None

    @property
    def extra_state_attributes(self):
        return {"departures": self.coordinator.get_modern_data() or []}


class ResRobotDepartureLegacySensor(ResRobotBaseDepartureSensor):
    """
    Contains raw departures in `departures` attribute.
    """

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset({"departures"})

    @property
    def unique_id(self):
        return f"{super().unique_id}_legacy"

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            **{
                **data,
                "icon": "mdi:swap-horizontal",
                "name": f"{data['name']} raw departures",
            },
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )

    @property
    def native_value(self):
        if data := self.coordinator.data:
            return len(data)

        return None

    @property
    def extra_state_attributes(self):
        return {"departures": self.coordinator.get_legacy_data() or []}


class ResRobotDepartureMinSensor(ResRobotBaseDepartureSensor):
    _attr_attribution = ATTRIBUTION

    @property
    def unique_id(self):
        return f"{super().unique_id}_min"

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            **{
                **data,
                "icon": "mdi:timer",
                "name": f"{data['name']} time to next departure",
            },
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
        )

    @property
    def native_value(self):
        if next_departure := self.nextDeparture():
            now = datetime.now(ZoneInfo("Europe/Stockholm"))
            arrival = datetime.fromisoformat(
                next_departure.get("expected", None)
                or next_departure.get("scheduled", None)
            )
            diff = arrival - now
            return round(diff.total_seconds() / 60)


class ResRobotDepartureTimeSensor(ResRobotBaseDepartureSensor):
    _attr_attribution = ATTRIBUTION

    @property
    def unique_id(self):
        return f"{super().unique_id}_time"

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            **{
                **data,
                "icon": "mdi:clock",
                "name": f"{data['name']} next departure time",
            },
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self):
        if next_departure := self.nextDeparture():
            return datetime.fromisoformat(next_departure["expected"])
