"""Departure sensor for hasl3."""

import logging
from asyncio import timeout
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import selector as sel
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from tsl.clients.journey import Journey, JourneyPlannerClient, SearchLeg
from tsl.tools.journey import SimpleJourneyInterpreter, leg_display_str

from .. import const
from ..utils import siteid_or_coords
from .device import SL_TRAFFIK_DEVICE_INFO

logger = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_SOURCE): str,
        vol.Required(const.CONF_DESTINATION): str,
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


async def async_setup_coordinator(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    coordinator = RouteDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    return coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""

    async_add_entities(
        [
            RouteRidesSensor(entry),
            RouteDurationSensor(entry),
            RouteTripsSensor(entry),
            RouteTripsDebugSensor(entry),
        ]
    )


@dataclass
class Data:
    """Data class for route data."""

    trips: list[Journey]
    trips_rides: list[int]
    simple_trips_steps: list[list[str]]


class RouteDataUpdateCoordinator(DataUpdateCoordinator[Data]):
    """Class to manage fetching Route data API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        source: str = config_entry.options[const.CONF_SOURCE]
        dest: str = config_entry.options[const.CONF_DESTINATION]
        try:
            ids_or_ccords = siteid_or_coords(source, dest)
        except* ValueError as exc:
            raise ConfigEntryError("source-or-dest-invalid") from exc
        else:
            if len(ids_or_ccords) == 2:
                _from, _to = ids_or_ccords
                self._lookup = (
                    SearchLeg.from_any(_from),
                    SearchLeg.from_any(_to),
                )
            else:
                olat, olon, dlat, dlon = ids_or_ccords
                self._lookup = (
                    SearchLeg.from_coordinates(olat, olon),
                    SearchLeg.from_coordinates(dlat, dlon),
                )

        self._sensor_id: str | None = config_entry.options.get(const.CONF_SENSOR)
        interval = timedelta(seconds=config_entry.options[const.CONF_SCAN_INTERVAL])

        if TYPE_CHECKING:
            assert config_entry.unique_id

        device_info = SL_TRAFFIK_DEVICE_INFO.copy()
        device_info["identifiers"] = {(const.DOMAIN, config_entry.entry_id)}
        device_info["name"] = config_entry.title
        self.device_info = device_info

        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            config_entry=config_entry,
            name=const.DOMAIN,
            update_interval=interval,
        )

    async def _async_update_data(self):
        if self._sensor_id and not self.hass.states.is_state(self._sensor_id, STATE_ON):
            self.logger.debug(
                'Not updating %s. Sensor "%s" is off',
                self.config_entry.entry_id,
                self._sensor_id,
            )

            return self.data

        client = JourneyPlannerClient(async_get_clientsession(self.hass))
        origin, destination = self._lookup
        request = client.build_request_params(origin=origin, destination=destination)

        async with timeout(10):
            try:
                data = await client.search_trip(request)
            except Exception as error:
                raise UpdateFailed(f"Failed to fetch trip from '{origin}' to '{destination}'") from error

        rides = []
        simple_trips = []
        for journey in data:
            legs = list(SimpleJourneyInterpreter(journey).get_itinerary())
            rides.append(len([x for x in legs if x._type != "walk"]))
            simple_trips.append([leg_display_str(leg) for leg in legs])

        return Data(trips=data, trips_rides=rides, simple_trips_steps=simple_trips)


class RouteBaseSensor(
    CoordinatorEntity[RouteDataUpdateCoordinator],
    SensorEntity,
):
    _attr_attribution = "Stockholm Lokaltrafik"

    def __init__(
        self,
        entry: ConfigEntry[RouteDataUpdateCoordinator],
    ):
        super().__init__(entry.runtime_data)

        self._attr_unique_id = f"{entry.entry_id}_{self.entity_description.key}"
        self._attr_device_info = self.coordinator.device_info


class RouteTripsDebugSensor(RouteBaseSensor):
    """
    Sensor for number of routes.
    Contains raw steps in `routes` attribute.
    """

    _unrecorded_attributes = frozenset({"routes"})

    entity_description = SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        key="raw_routes",
        icon="mdi:swap-horizontal",
        has_entity_name=True,
        name="Raw Routes",
    )

    @property
    def native_value(self):
        if data := self.coordinator.data.trips:
            return len(data)

        return None

    @property
    def extra_state_attributes(self):
        return {"routes": self.coordinator.data.trips or []}


class RouteTripsSensor(RouteBaseSensor):
    """
    Sensor for number of simple routes.
    Contains human-readable steps in `routes` attribute.
    """

    _unrecorded_attributes = frozenset({"routes"})

    entity_description = SensorEntityDescription(
        key="simple_routes",
        icon="mdi:swap-horizontal",
        has_entity_name=True,
        name="Routes",
    )

    @property
    def native_value(self):
        if data := self.coordinator.data.simple_trips_steps:
            return len(data)

        return None

    @property
    def extra_state_attributes(self):
        return {"routes": self.coordinator.data.simple_trips_steps or []}


class RouteDurationSensor(RouteBaseSensor):
    """Sensor for first available route duration."""

    entity_description = SensorEntityDescription(
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        key="duration",
        icon="mdi:timer",
        has_entity_name=True,
        name="Duration",
    )

    @property
    def native_value(self):
        if data := self.coordinator.data.trips:
            first_trip = data[0]
            return first_trip["tripDuration"]

        return None


class RouteRidesSensor(RouteBaseSensor):
    """Sensor for number of transport rides in the first available route"""

    entity_description = SensorEntityDescription(
        key="rides",
        icon="mdi:train",
        has_entity_name=True,
        name="Rides",
    )

    @property
    def native_value(self):
        if data := self.coordinator.data.trips_rides:
            first_trip = data[0]
            return first_trip

        return None
