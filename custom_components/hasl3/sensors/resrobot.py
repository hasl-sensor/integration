from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ..const import CONF_INTEGRATION_TYPE, KEY_COORDINATORS, SENSOR_RESROBOT_ROUTE
from .rr_route import async_setup_entry as setup_route_entry


async def setup_resrobot_subentries(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
):
    config_entry.runtime_data = {KEY_COORDINATORS: []}

    for subentry_id, subentry in config_entry.subentries.items():
        if subentry.data.get(CONF_INTEGRATION_TYPE) == SENSOR_RESROBOT_ROUTE:
            entities = await setup_route_entry(hass, config_entry, subentry)
            async_add_entities(entities, config_subentry_id=subentry_id)
