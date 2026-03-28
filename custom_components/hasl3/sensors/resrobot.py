from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ..const import (
    CONF_INTEGRATION_TYPE,
    KEY_COORDINATORS,
    SENSOR_RESROBOT_ARRIVAL,
    SENSOR_RESROBOT_DEPARTURE,
    SENSOR_RESROBOT_ROUTE,
)
from .rr_arrival import async_setup_entry as setup_arrival_entry
from .rr_departure import async_setup_entry as setup_departure_entry
from .rr_route import async_setup_entry as setup_route_entry


async def setup_resrobot_subentries(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
):
    config_entry.runtime_data = {KEY_COORDINATORS: []}

    setup_map = {
        SENSOR_RESROBOT_ROUTE: setup_route_entry,
        SENSOR_RESROBOT_DEPARTURE: setup_departure_entry,
        SENSOR_RESROBOT_ARRIVAL: setup_arrival_entry,
    }

    for subentry_id, subentry in config_entry.subentries.items():
        if (_type := subentry.data.get(CONF_INTEGRATION_TYPE)) is None:
            error = ValueError(f"Subentry {subentry_id} missing integration type")
            raise ConfigEntryError(error) from error

        if setup := setup_map.get(_type):
            entities = await setup(hass, config_entry, subentry)
            async_add_entities(entities, config_subentry_id=subentry_id)
