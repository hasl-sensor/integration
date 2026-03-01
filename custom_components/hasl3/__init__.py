import logging

from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_INTEGRATION_ID,
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    SCHEMA_VERSION,
    SENSOR_DEPARTURE,
    SENSOR_ROUTE,
    SENSOR_STATUS,
)
from .sensors.departure import async_setup_coordinator as setup_departure_coordinator
from .sensors.route import async_setup_coordinator as setup_route_coordinator
from .sensors.status import async_setup_coordinator as setup_status_coordinator
from .services.sl_find_location import register as register_sl_find_location
from .services.sl_find_trip_id import register as register_sl_find_trip_id
from .services.sl_find_trip_pos import register as register_sl_find_trip_pos
from .services.rr_find_location import register as register_rr_find_location

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")


async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Set up HASL integration"""
    logger.debug("[setup] Entering")

    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})

    logger.debug("[setup] Registering services")
    register_sl_find_location(hass)
    register_sl_find_trip_id(hass)
    register_sl_find_trip_pos(hass)
    register_rr_find_location(hass)
    logger.debug("[setup] Service registration completed")

    hass.data[DOMAIN]["worker"].status.startup_in_progress = False
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
