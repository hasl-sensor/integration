import logging
from typing import Any

from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    entity_registry as er,
    device_registry as dr,
)

from .const import (
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_TYPE,
    CONF_SOURCE,
    CONF_DESTINATION,
    CONF_SITE_ID,
    DEVICE_GUID,
    DOMAIN,
    SCHEMA_VERSION,
    SENSOR_DEPARTURE,
    SENSOR_ROUTE,
    SENSOR_STATUS,
    SENSOR_RRARR,
    SENSOR_RRDEP,
    SENSOR_RRROUTE,
    SENSOR_RESROBOT_ARRIVAL,
    SENSOR_RESROBOT_DEPARTURE,
    SENSOR_RESROBOT_ROUTE,
    CONF_RR_KEY,
    CONF_API_KEY,
    CONF_SENSOR,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE_ID,
    CONF_DESTINATION_ID,
    SERVICE_RESROBOT_KEY,
)
from .sensors.departure import async_setup_coordinator as setup_departure_coordinator
from .sensors.route import async_setup_coordinator as setup_route_coordinator
from .sensors.status import async_setup_coordinator as setup_status_coordinator
from .services.rr_find_location import register as register_rr_find_location
from .services.sl_find_location import register as register_sl_find_location
from .services.sl_find_trip_id import register as register_sl_find_trip_id
from .services.sl_find_trip_pos import register as register_sl_find_trip_pos

from uuid import uuid4

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")


async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Set up HASL integration"""
    logger.debug("[setup] Entering")

    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
        
    await async_migrate_integration(hass)

    logger.debug("[setup] Registering services")
    register_sl_find_location(hass)
    register_sl_find_trip_id(hass)
    register_sl_find_trip_pos(hass)
    register_rr_find_location(hass)
    logger.debug("[setup] Service registration completed")

    logger.debug("[setup] Completed")
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    logger.debug("[migrate_entry] Entered")

    logger.debug(
        "[migrate_entry] Migrating configuration from schema version %s to version %s",
        config_entry.version,
        SCHEMA_VERSION,
    )

    data = {**config_entry.data}
    options = {**config_entry.options}

    if (
        config_entry.version != "1"
        and config_entry.version != "2"
        and config_entry.version != "3"
    ):
        for option in config_entry.options:
            logger.debug(
                f"[migrate_entry] set {option} = {config_entry.options[option]}"
            )
            data[option] = config_entry.options[option]

    if config_entry.version == "2" and SCHEMA_VERSION == "3":
        # TODO: write migration
        # if data[CONF_INTEGRATION_TYPE] == "Departures":
        #     data[CONF_INTEGRATION_TYPE] = SENSOR_STANDARD
        #     logger.debug(
        #         f"[migrate_entry] migrate from Departures to {SENSOR_STANDARD}"
        #     )

        # TODO: write migration
        # if data[CONF_INTEGRATION_TYPE] == "Traffic Status":
        #     data[CONF_INTEGRATION_TYPE] = SENSOR_STATUS
        #     logger.debug(
        #         f"[migrate_entry] migrate from Traffic Status to {SENSOR_STATUS}"
        #     )
        # TODO: write migration
        # if data[CONF_INTEGRATION_TYPE] == "Deviations":
        #     data[CONF_INTEGRATION_TYPE] = "SL Deviations"
        #     logger.debug(
        #         f"[migrate_entry] migrate from Deviations to SL Deviations"
        #     )
        if data[CONF_INTEGRATION_TYPE] == "Route":
            data[CONF_INTEGRATION_TYPE] = SENSOR_ROUTE
            logger.debug(f"[migrate_entry] migrate from Route to {SENSOR_ROUTE}")

    if config_entry.version == 3 and SCHEMA_VERSION == "4":
        # split data into static and configurable part
        new_data = {
            k: v
            for k, v in data.items()
            if k in (CONF_INTEGRATION_ID, CONF_INTEGRATION_TYPE)
        }
        options = {k: v for k, v in data.items() if k not in new_data}
        data = new_data
        config_entry.version = 4

    try:
        hass.config_entries.async_update_entry(config_entry, data=data, options=options)
        logger.debug("[migrate_entry] Completed")
    except Exception as e:
        logger.error(f"[migrate_entry] Failed: {str(e)}")
        return False

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up HASL entry."""

    type_ = entry.data[CONF_INTEGRATION_TYPE]
    if coro := {
        # "new-style" delegated setup functions
        SENSOR_DEPARTURE: setup_departure_coordinator,
        SENSOR_STATUS: setup_status_coordinator,
        SENSOR_ROUTE: setup_route_coordinator,
    }.get(type_):
        entry.runtime_data = await coro(hass, entry)

    # subscribe to updates
    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, [SENSOR_DOMAIN])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload HASL entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, [SENSOR_DOMAIN])

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


# custom migration to convert resrobot entries to main entry with subentries
async def async_migrate_integration(hass: HomeAssistant) -> None:
    """Migrate integration entry structure."""
    NEW_VERSION = 5

    entries = hass.config_entries.async_entries(DOMAIN)

    # We migrate only resrobot entries
    old_versions = list(range(NEW_VERSION))
    old_versions = set([*old_versions, *[str(n) for n in old_versions]])
    if not any(entry.version in old_versions for entry in entries):
        return

    entries = [
        entry
        for entry in entries
        if entry.data.get(CONF_INTEGRATION_TYPE)
        in (SENSOR_RRARR, SENSOR_RRDEP, SENSOR_RRROUTE)
    ]
    if not entries:
        return

    api_keys_entries: dict[str, ConfigEntry] = {}
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    for entry in entries:
        use_existing = False
        
        subentry_type=map_RR_entry_to_subentry(entry.data[CONF_INTEGRATION_TYPE])
        subentry_data: dict[str, Any] = {
            CONF_INTEGRATION_TYPE: subentry_type,
            CONF_SCAN_INTERVAL: entry.data[CONF_SCAN_INTERVAL],
            CONF_SENSOR: entry.data[CONF_SENSOR]
        }
        
        if subentry_type == SENSOR_RESROBOT_DEPARTURE:
            subentry_data[CONF_SOURCE] = entry.data[CONF_SITE_ID]
        elif subentry_type == SENSOR_RESROBOT_ARRIVAL:
            subentry_data[CONF_DESTINATION] = entry.data[CONF_SITE_ID]
        elif subentry_type == SENSOR_RESROBOT_ROUTE:
            subentry_data[CONF_SOURCE] = entry.data[CONF_SOURCE_ID]
            subentry_data[CONF_DESTINATION] = entry.data[CONF_DESTINATION_ID]
            
        subentry = ConfigSubentry(
            data=subentry_data,
            subentry_type=subentry_type,
            title=entry.title,
            unique_id=str(uuid4()),
        )
        if entry.data[CONF_RR_KEY] not in api_keys_entries:
            use_existing = True
            # we save the whole original entry here, we will update it in the end
            api_keys_entries[entry.data[CONF_RR_KEY]] = entry

        parent_entry = api_keys_entries[entry.data[CONF_RR_KEY]]

        hass.config_entries.async_add_subentry(parent_entry, subentry)
        sensor_entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN,
            DOMAIN,
            entry.entry_id,
        )
        
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, DEVICE_GUID)}
        )
        if device is not None:
            device_registry.async_remove_device(
                device_id=device.id
            )
        
        if sensor_entity_id is not None:
            entity_registry.async_update_entity(
                entity_id=sensor_entity_id,
                config_entry_id=parent_entry.entry_id,
                config_subentry_id=subentry.subentry_id,
                new_unique_id=subentry.subentry_id,
            )

        if not use_existing:
            await hass.config_entries.async_remove(entry.entry_id)
        else:
            entry_data=dict()
            entry_data[CONF_API_KEY] = entry.data[CONF_RR_KEY]
            entry_data[CONF_INTEGRATION_TYPE] = SERVICE_RESROBOT_KEY
            hass.config_entries.async_update_entry(
                entry,
                title=SERVICE_RESROBOT_KEY,
                data=entry_data,
                options={},
                version=NEW_VERSION,
            )
            
def map_RR_entry_to_subentry(entry_name: str) -> str:
    if entry_name == SENSOR_RRDEP:
        return SENSOR_RESROBOT_DEPARTURE
    elif entry_name == SENSOR_RRARR:
        return SENSOR_RESROBOT_ARRIVAL
    elif entry_name == SENSOR_RRROUTE:
        return SENSOR_RESROBOT_ROUTE
    else:
        # raise exception?
        return ""
