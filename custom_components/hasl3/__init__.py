import logging
import jsonpickle
import time
import asyncio

from custom_components.hasl3.haslworker import HaslWorker
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    HASL_VERSION,
    SCHEMA_VERSION,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_GUID,
    CONF_INTEGRATION_TYPE,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
)

from custom_components.hasl3.slapi import (
    slapi_rp3,
    slapi_pu1,
)

from custom_components.hasl3.rrapi import (
    rrapi_sl
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")
serviceLogger = logging.getLogger(f"custom_components.{DOMAIN}.services")


async def async_setup(hass, config):
    """Set up HASL integration"""
    logger.debug("[setup] Entering")

    # SERVICE FUNCTIONS
    @callback
    async def dump_cache(service):
        serviceLogger.debug("[dump_cache] Entered")
        timestring = time.strftime("%Y%m%d%H%M%S")
        outputfile = hass.config.path(f"hasl_data_{timestring}.json")

        serviceLogger.debug(f"[dump_cache] Will dump to {outputfile}")

        try:
            jsonFile = open(outputfile, "w")
            jsonFile.write(jsonpickle.dumps(worker.data.dump(), 4, unpicklable=False))
            jsonFile.close()
            serviceLogger.debug("[dump_cache] Completed")
            hass.bus.fire(DOMAIN, {"source": "dump_cache", "state": "success", "result": outputfile})
            return True
        except Exception as e:
            serviceLogger.debug("[dump_cache] Failed to take a dump")
            hass.bus.fire(DOMAIN, {"source": "dump_cache", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def get_cache(service):
        serviceLogger.debug("[get_cache] Entered")

        try:
            dataDump = jsonpickle.dump(worker.data.dump(), 4, unpicklable=False)
            serviceLogger.debug("[get_cache] Completed")
            hass.bus.fire(DOMAIN, {"source": "get_cache", "state": "success", "result": dataDump})
            return True
        except Exception as e:
            serviceLogger.debug("[get_cache] Failed to get dump")
            hass.bus.fire(DOMAIN, {"source": "get_cache", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def sl_find_location(service):
        serviceLogger.debug("[sl_find_location] Entered")
        search_string = service.data.get('search_string')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[sl_find_location] Looking for '{search_string}' with key {api_key}")

        try:
            pu1api = slapi_pu1(api_key)
            requestResult = await pu1api.request(search_string)
            serviceLogger.debug("[sl_find_location] Completed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_location", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[sl_find_location] Lookup failed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_location", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def rr_find_location(service):
        serviceLogger.debug("[rr_find_location] Entered")
        search_string = service.data.get('search_string')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[rr_find_location] Looking for '{search_string}' with key {api_key}")

        try:
            rrapi = rrapi_sl(api_key)
            requestResult = await rrapi.request(search_string)
            serviceLogger.debug("[rr_find_location] Completed")
            hass.bus.fire(DOMAIN, {"source": "rr_find_location", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[rr_find_location] Lookup failed")
            hass.bus.fire(DOMAIN, {"source": "rr_find_location", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True            

    @callback
    async def sl_find_trip_id(service):
        serviceLogger.debug("[sl_find_trip_id] Entered")
        origin = service.data.get('org')
        destination = service.data.get('dest')
        api_key = service.data.get('api_key')

        # serviceLogger.debug(f"[sl_Availablefind_trip_id] Finding from '{origin}' to '{destination}' with key {api_key}")

        try:
            rp3api = slapi_rp3(api_key)
            requestResult = await rp3api.request(origin, destination, '', '', '', '')
            serviceLogger.debug("[sl_find_trip_id] Completed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_trip_id", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[sl_find_trip_id] Lookup failed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_trip_id", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def sl_find_trip_pos(service):
        serviceLogger.debug("[sl_find_trip_pos] Entered")
        olat = service.data.get('orig_lat')
        olon = service.data.get('orig_long')
        dlat = service.data.get('dest_lat')
        dlon = service.data.get('dest_long')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[sl_find_trip_pos] Finding from '{olat} {olon}' to '{dlat} {dlon}' with key {api_key}")

        try:
            rp3api = slapi_rp3(api_key)
            requestResult = await rp3api.request('', '', olat, olon, dlat, dlon)
            serviceLogger.debug("[sl_find_trip_pos] Completed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_trip_pos", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[sl_find_trip_pos] Lookup failed")
            hass.bus.fire(DOMAIN, {"source": "sl_find_trip_pos", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def eventListener(service):
        serviceLogger.debug("[eventListener] Entered")

        command = service.data.get('cmd')

        if command == "dump_cache":
            dump_cache(service)
            serviceLogger.debug("[eventListener] Dispatched to dump_cache")
            return True
        if command == "get_cache":
            get_cache(service)
            serviceLogger.debug("[eventListener] Dispatched to get_cache")
            return True
        if command == "sl_find_location":
            sl_find_location(service)
            serviceLogger.debug("[eventListener] Dispatched to sl_find_location")
            return True
        if command == "rr_find_location":
            rr_find_location(service)
            serviceLogger.debug("[eventListener] Dispatched to rr_find_location")
            return True
        if command == "sl_find_trip_pos":
            sl_find_trip_pos(service)
            serviceLogger.debug("[eventListener] Dispatched to sl_find_trip_pos")
            return True
        if command == "sl_find_trip_id":
            sl_find_trip_id(service)
            serviceLogger.debug("[eventListener] Dispatched to sl_find_trip_id")
            return True

    try:
        if DOMAIN not in hass.data:
            hass.data.setdefault(DOMAIN, {})

        if "worker" not in hass.data[DOMAIN]:
            logger.debug("[setup] No worker present")
            worker = HaslWorker()
            worker.hass = hass
            hass.data[DOMAIN] = {
                "worker": worker
            }
            logger.debug("[setup] Worker created")
    except:
        logger.error("[setup] Could not get worker")
        return False

    logger.debug("[setup] Registering services")
    try:
        hass.services.async_register(DOMAIN, 'dump_cache', dump_cache)
        hass.services.async_register(DOMAIN, 'get_cache', get_cache)
        hass.services.async_register(DOMAIN, 'sl_find_location', sl_find_location)
        hass.services.async_register(DOMAIN, 'rr_find_location', rr_find_location)
        hass.services.async_register(DOMAIN, 'sl_find_trip_pos', sl_find_trip_pos)
        hass.services.async_register(DOMAIN, 'sl_find_trip_id', sl_find_trip_id)
        logger.debug("[setup] Service registration completed")
    except:
        logger.error("[setup] Service registration failed")

    logger.debug("[setup] Registering event listeners")
    try:
        hass.bus.async_listen(DOMAIN, eventListener)
        logger.debug("[setup] Registering event listeners completed")
    except:
        logger.error("[setup] Registering event listeners failed")

    hass.data[DOMAIN]["worker"].status.startup_in_progress = False
    logger.debug("[setup] Completed")
    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    logger.debug("[migrate_entry] Entered")

    logger.debug("[migrate_entry] Migrating configuration from schema version %s to version %s", config_entry.version, SCHEMA_VERSION)

    data = {**config_entry.data}
    options = {**config_entry.options}

    if config_entry.version != "1" and config_entry.version != "2" and config_entry.version != "3":
        for option in config_entry.options:
            logger.debug(f"[migrate_entry] set {option} = {config_entry.options[option]}")
            data[option] = config_entry.options[option]

    if config_entry.version == "2" and SCHEMA_VERSION == "3":
        if data[CONF_INTEGRATION_TYPE] == "Departures":
            data[CONF_INTEGRATION_TYPE] = SENSOR_STANDARD
            logger.debug(f"[migrate_entry] migrate from Departures to {SENSOR_STANDARD}")
        if data[CONF_INTEGRATION_TYPE] == "Traffic Status":
            data[CONF_INTEGRATION_TYPE] = SENSOR_STATUS
            logger.debug(f"[migrate_entry] migrate from Traffic Status to {SENSOR_STATUS}")
        if data[CONF_INTEGRATION_TYPE] == "Vehicle Locations":
            data[CONF_INTEGRATION_TYPE] = SENSOR_VEHICLE_LOCATION
            logger.debug(f"[migrate_entry] migrate from Vehicle Locations to {SENSOR_VEHICLE_LOCATION}")
        if data[CONF_INTEGRATION_TYPE] == "Deviations":
            data[CONF_INTEGRATION_TYPE] = SENSOR_DEVIATION
            logger.debug(f"[migrate_entry] migrate from Deviations to {SENSOR_DEVIATION}")
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


async def reload_entry(hass, entry):
    """Reload HASL."""
    logger.debug(f"[reload_entry] Entering for {entry.entry_id}")

    try:
        await async_unload_entry(hass, entry)
        logger.debug("[reload_entry] Unload succeeded")
    except:
        logger.error("[reload_entry] Unload failed")

    try:
        await async_setup_entry(hass, entry)
        logger.debug("[reload_entry] Setup succeeded")
    except:
        logger.error("[reload_entry] Setup failed")

    logger.debug("[reload_entry] Completed")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up HASL entries"""

    logger.debug(f"[setup_entry] Entering for {entry.entry_id}")

    try:
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, DEVICE_GUID)},
            name=DEVICE_NAME,
            model=DEVICE_MODEL,
            sw_version=HASL_VERSION,
            manufacturer=DEVICE_MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE
        )
        logger.debug("[setup_entry] Created device")
    except Exception as e:
        logger.error(f"[setup_entry] Failed to create device: {str(e)}")        
        return False

    try:
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "binary_sensor"))
        logger.debug("[setup_entry] Forward entry setup succeeded")
    except:
        logger.error("[setup_entry] Forward entry setup failed")
        return False

    updater = None
    try:
        updater = entry.add_update_listener(reload_entry)
    except:
        logger.error("[setup_entry] Update listener setup failed")
        return False

    try:
        hass.data[DOMAIN]["worker"].instances.add(entry.entry_id, updater)
        logger.debug("[setup_entry] Worker registration succeeded")
    except Exception as e:
        logger.error(f"[setup_entry] Worker registration failed: {str(e)}")
        return False

    logger.debug("[setup_entry] Completed")

    return True


async def async_unload_entry(hass, entry):
    """Unload entry."""
    logger.debug("[unload_entry] Entered")

    try:

        hass.async_add_job(hass.config_entries.async_forward_entry_unload(entry, "sensor"))
        hass.async_add_job(hass.config_entries.async_forward_entry_unload(entry, "binary_sensor"))
    except:
        logger.error("[unload_entry] Forward entry unload failed")
        return False

    try:
        hass.data[DOMAIN]["worker"].instances.remove(entry.entry_id)
        logger.debug("[unload_entry] Worker deregistration succeeded")
    except:
        logger.error("[unload_entry] Worker deregistration failed")
        return False

    logger.debug("[unload_entry] Completed")
    return True
