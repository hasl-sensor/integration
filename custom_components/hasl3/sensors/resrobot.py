from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ..const import CONF_INTEGRATION_TYPE, KEY_COORDINATORS, SENSOR_RESROBOT_ROUTE, SENSOR_RESROBOT_DEPARTURE
from .rr_route import async_setup_entry as setup_route_entry
from .rr_departure import async_setup_entry as setup_departure_entry


async def setup_resrobot_subentries(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
):
    config_entry.runtime_data = {KEY_COORDINATORS: []}

    setup_map = {
        SENSOR_RESROBOT_ROUTE: setup_route_entry,
        SENSOR_RESROBOT_DEPARTURE: setup_departure_entry,
    }

    for subentry_id, subentry in config_entry.subentries.items():
        if setup := setup_map.get(subentry.data.get(CONF_INTEGRATION_TYPE)):
            entities = await setup(hass, config_entry, subentry)
            async_add_entities(entities, config_subentry_id=subentry_id)
