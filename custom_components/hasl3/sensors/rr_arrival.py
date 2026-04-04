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
from ..rrapi.model import ListOfArrivals
from ..rrapi.utils import (
    map_rr_arrivals_to_legacy_arrivals,
    map_rr_arrivals_to_v4_departures,
)
from .device import SL_TRAFFIK_DEVICE_INFO

logger = logging.getLogger(__name__)

ATTRIBUTION = "Samtrafiken Resrobot"
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_DESTINATION): sel.TextSelector(),
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


class ArrivalDataUpdateCoordinator(DataUpdateCoordinator[dict]):
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
        self.destination: str = subentry.data[const.CONF_DESTINATION]
        self._sensor_id: str | None = subentry.data.get(const.CONF_SENSOR)
        self.subentry = subentry
        self.get_device = lambda: get_dr(hass).async_get_device(
            {(const.DOMAIN, subentry.subentry_id)}
        )
        interval = timedelta(seconds=subentry.data[const.CONF_SCAN_INTERVAL])
        self.friendly_name = subentry.title

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
                arrivals = await client.get_arrivals(self.destination)
            except Exception as error:
                logger.error(
                    "Failed to fetch arrivals for %s: %s",
                    self.destination,
                    error,
                )
                raise UpdateFailed(
                    f"Failed to fetch arrivals for {self.destination}"
                ) from error

        return arrivals

    def get_legacy_data(self):
        if data := self.data:
            return map_rr_arrivals_to_legacy_arrivals(
                cast(ListOfArrivals, data), now(), self.timezone
            )

    def get_modern_data(self):
        if data := self.data:
            return map_rr_arrivals_to_v4_departures(
                cast(ListOfArrivals, data), self.timezone
            )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
) -> list[Entity]:
    """Set up the sensor platform."""

    coordinator = ArrivalDataUpdateCoordinator(hass, entry, subentry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data[const.KEY_COORDINATORS].append(coordinator)

    context = {
        "id": subentry.subentry_id,
        "type": subentry.data[const.CONF_INTEGRATION_TYPE],
        "name": subentry.title,
    }
    return [
        ResRobotArrivalLegacySensor(coordinator, context),
        ResRobotArrivalV4Sensor(coordinator, context),
        ResRobotArrivalMinSensor(coordinator, context),
        ResRobotArrivalTimeSensor(coordinator, context),
    ]


class ResRobotBaseArrivalSensor(
    CoordinatorEntity[ArrivalDataUpdateCoordinator],
    SensorEntity,
):
    _attr_attribution = ATTRIBUTION

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

    def nextArrival(self):
        if data := self.coordinator.get_modern_data():
            arrivals = sorted(
                data,
                key=lambda x: x.get("expected", None) or x.get("scheduled", None),
            )
            return next(iter(arrivals), None)

    @cached_property
    def device_info(self) -> DeviceInfo:
        return {
            **SL_TRAFFIK_DEVICE_INFO,
            "identifiers": {(const.DOMAIN, self.coordinator_context["id"])},
            "name": "Arrival Sensor",
        }


class ResRobotArrivalV4Sensor(ResRobotBaseArrivalSensor):
    """
    Contains arrivals mapped for compatibility with Departure Card V4.
    """

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset({"arrivals"})

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            key="arrivals",
            icon="mdi:swap-horizontal",
            has_entity_name=True,
            name=f"{data['name']} arrivals",
        )

    @property
    def native_value(self):
        if data := self.coordinator.get_modern_data():
            return len(data)

        return None

    @property
    def extra_state_attributes(self):
        # NOTE: "departures" is intentional here, to match the expected format of the Departure Card
        return {"departures": self.coordinator.get_modern_data() or []}


class ResRobotArrivalLegacySensor(ResRobotBaseArrivalSensor):
    """
    Contains raw arrivals in `arrivals` attribute.
    """

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset({"arrivals"})

    @property
    def unique_id(self):
        return f"{super().unique_id}_debug"

    @cached_property
    def entity_description(self):
        data = super().entity_description()
        return SensorEntityDescription(
            **{
                **data,
                "icon": "mdi:swap-horizontal",
                "name": f"{data['name']} raw arrivals",
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
        return {"arrivals": self.coordinator.get_legacy_data() or []}


class ResRobotArrivalMinSensor(ResRobotBaseArrivalSensor):
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
                "name": f"{data['name']} time to next arrival",
            },
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
        )

    @property
    def native_value(self):
        if next_arrival := self.nextArrival():
            now = datetime.now(ZoneInfo("Europe/Stockholm"))
            arrival = datetime.fromisoformat(
                next_arrival.get("expected", None)
                or next_arrival.get("scheduled", None)
            )
            diff = arrival - now
            return round(diff.total_seconds() / 60)


class ResRobotArrivalTimeSensor(ResRobotBaseArrivalSensor):
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
                "name": f"{data['name']} next arrival time",
            },
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self):
        if next_arrival := self.nextArrival():
            return next_arrival["expected"]
