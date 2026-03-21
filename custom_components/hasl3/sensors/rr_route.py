import logging
from asyncio import timeout
from datetime import timedelta
from functools import cached_property

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigSubentry,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import selector as sel
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo, async_get as get_dr
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util.dt import async_get_time_zone

from .. import const
from ..rrapi.client import ResRobotClient
from .device import SL_TRAFFIK_DEVICE_INFO

logger = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_SOURCE): sel.TextSelector(),
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


class RouteDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        subentry: ConfigSubentry,
    ) -> None:
        self.api_key: str = config_entry.data[const.CONF_API_KEY]
        self.origin: str = subentry.data[const.CONF_SOURCE]
        self.destination: str = subentry.data[const.CONF_DESTINATION]
        self._sensor_id: str | None = subentry.data.get(const.CONF_SENSOR)
        self.subentry = subentry
        self.get_device = lambda: get_dr(hass).async_get_device({(const.DOMAIN, subentry.subentry_id)})
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
            self.logger.debug('Not updating %s. Device is off', self.subentry.subentry_id)
            return self.data

        if self._sensor_id and not self.hass.states.is_state(self._sensor_id, STATE_ON):
            self.logger.debug(
                'Not updating %s. Sensor "%s" is off',
                self.subentry.subentry_id,
                self._sensor_id,
            )

            return self.data

        tz = await async_get_time_zone("Europe/Stockholm")
        client = ResRobotClient(async_get_clientsession(self.hass), self.api_key, tz=tz)
        async with timeout(10):
            try:
                data = await client.find_trip(self.origin, self.destination)
            except Exception as error:
                raise ConfigEntryError(error) from error

        return data


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, subentry: ConfigSubentry
) -> list[Entity]:
    """Set up the sensor platform."""

    coordinator = RouteDataUpdateCoordinator(hass, entry, subentry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data[const.KEY_COORDINATORS].append(coordinator)
    return [
        ResRobotRouteSensor(
            coordinator,
            {
                "id": subentry.subentry_id,
                "type": subentry.data[const.CONF_INTEGRATION_TYPE],
                "name": subentry.title,
            },
        )
    ]


class ResRobotRouteSensor(
    CoordinatorEntity[RouteDataUpdateCoordinator],
    SensorEntity,
):
    _attr_attribution = "Samtrafiken Resrobot"
    _unrecorded_attributes = frozenset({"trips", "origin", "destination", "from", "to"})

    @cached_property
    def entity_description(self):
        sid = self.coordinator_context["id"]
        _type = self.coordinator_context["type"]
        return SensorEntityDescription(
            key=f"{self.coordinator.config_entry.entry_id}_{_type}_{sid}",
            icon="mdi:train",
            has_entity_name=True,
            name=f"{self.coordinator_context['name']}",
        )

    @property
    def unique_id(self):
        return f"{self.coordinator.config_entry.entry_id}_{self.entity_description.key}"

    @property
    def native_value(self):
        return len(self.coordinator.data["trips"])

    @property
    def extra_state_attributes(self):
        return self.coordinator.data

    @cached_property
    def device_info(self) -> DeviceInfo:
        return {
            **SL_TRAFFIK_DEVICE_INFO,
            "identifiers": {(const.DOMAIN, self.coordinator_context["id"])},
            "name": "Route Sensor",
        }
