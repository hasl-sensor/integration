import logging
import jsonpickle
import time
import asyncio

from datetime import datetime
from custom_components.hasl3.haslworker import HaslWorker
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    HASL_VERSION,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_GUID
)

from custom_components.hasl3.slapi import (
    slapi_rp3,
    slapi_pu1,
) 

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")
serviceLogger = logging.getLogger(f"custom_components.{DOMAIN}.services")       

@asyncio.coroutine
async def async_setup(hass, config):
    """Set up HASL integration"""
    logger.debug("[setup] Entering")

    ##########################################################################################
    ## SERVICE FUNCTIONS
    ##########################################################################################
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
            hass.bus.fire(f"{DOMAIN}_response", {"source": "dump_cache", "state": "success", "result": outputfile})
            return True
        except Exception as e:
            serviceLogger.debug("[dump_cache] Failed to take a dump")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "dump_cache", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def get_cache(service):
        serviceLogger.debug("[get_cache] Entered")

        try:
            dataDump = jsonpickle.dump(worker.data.dump(), 4, unpicklable=False)
            serviceLogger.debug("[dump_cache] Completed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "get_cache", "state": "success", "result": dataDump})
            return True
        except Exception as e:
            serviceLogger.debug("[get_cache] Failed to get dump")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "get_cache", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def find_location(service):
        serviceLogger.debug("[find_location] Entered")
        search_string = service.data.get('search_string')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[find_location] Looking for '{search_string}' with key {api_key}")

        try:
            pu1api = slapi_pu1(api_key)
            requestResult = await pu1api.request(search_string)
            serviceLogger.debug("[find_location] Completed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_location", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[find_location] Lookup failed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_location", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def find_trip_id(service):
        serviceLogger.debug("[find_trip_id] Entered")
        origin = service.data.get('org')
        destination = service.data.get('dest')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[find_trip_id] Finding from '{origin}' to '{destination}' with key {api_key}")

        try:
            rp3api = slapi_rp3(api_key)
            requestResult = await rp3api.request(origin, destination, '', '', '', '')
            serviceLogger.debug("[find_trip_id] Completed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_trip_id", "state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[find_trip_id] Lookup failed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_trip_id", "state": "error", "result": f"Exception occured during execution: {str(e)}"})
            return True

    @callback
    async def find_trip_pos(service):
        serviceLogger.debug("[find_trip_pos] Entered")
        olat = service.data.get('orig_lat')
        olon = service.data.get('orig_long')
        dlat = service.data.get('dest_lat')
        dlon = service.data.get('dest_long')
        api_key = service.data.get('api_key')

        serviceLogger.debug(f"[find_trip_pos] Finding from '{olat} {olon}' to '{dlat} {dlon}' with key {api_key}")

        try:
            rp3api = slapi_rp3(api_key)
            requestResult = await rp3api.request('', '', olat, olon, dlat, dlon)   
            serviceLogger.debug("[find_trip_pos] Completed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_trip_pos","state": "success", "result": requestResult})
            return True
        except Exception as e:
            serviceLogger.debug("[find_trip_pos] Lookup failed")
            hass.bus.fire(f"{DOMAIN}_response", {"source": "find_trip_pos","state": "error", "result": f"Exception occured during execution: {str(e)}"})
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
        if command == "find_location":
            find_location(service)
            serviceLogger.debug("[eventListener] Dispatched to find_location")
            return True
        if command == "find_trip_pos":
            find_trip_pos(service)
            serviceLogger.debug("[eventListener] Dispatched to find_trip_pos")
            return True
        if command == "find_trip_id":
            find_trip_id(service)
            serviceLogger.debug("[eventListener] Dispatched to find_trip_id")
            return True

        hass.bus.fire(f"{DOMAIN}_response", {"source": "service", "state": "error", "result": f"No or empty cmd specified"})
        serviceLogger.debug("[eventListener] No cmd found")



    ##########################################################################################
    ##########################################################################################

    try:
        if not DOMAIN in hass.data:
            hass.data.setdefault(DOMAIN,{})

        if not "worker" in hass.data[DOMAIN]:
            logger.debug("[setup] No worker present")
            worker = HaslWorker()
            worker.hass = hass
            hass.data[DOMAIN] = {
                "worker": worker
            }
            logger.debug("[setup] Worker created")
    except Exception as e:
            logger.error("[setup] Could not get worker")
            return False

    logger.debug("[setup] Registering services")
    try:
        hass.services.async_register(DOMAIN, 'dump_cache', dump_cache)
        hass.services.async_register(DOMAIN, 'get_cache', get_cache)
        hass.services.async_register(DOMAIN, 'find_location', find_location)
        hass.services.async_register(DOMAIN, 'find_trip_pos', find_trip_pos)
        hass.services.async_register(DOMAIN, 'find_trip_id', find_trip_id)
        logger.debug("[setup] Service registration completed")
    except Exception as e:
        logger.error("[setup] Service registration failed")

    logger.debug("[setup] Registering event listeners")
    try:
        hass.bus.async_listen(f"{DOMAIN}_execute", eventListener)
        logger.debug("[setup] Registering event listeners completed")
    except Exception as e:
        logger.error("[setup] Registering event listeners failed")

    hass.data[DOMAIN]["worker"].status.startup_in_progress = False
    logger.debug("[setup] Completed")
    return True

async def async_migrate_entry(hass, config_entry: ConfigEntry):
    logger.debug("[migrate_entry] Entered")

    logger.debug("[migrate_entry] Nothing to do from version %s to version %s", config_entry.version, HASL_VERSION)

    logger.debug("[migrate_entry] Completed")

    return True


async def reload_entry(hass, entry):
    """Reload HASL."""
    logger.debug(f"[reload_entry] Entering for {entry.entry_id}")

    try:
        await async_unload_entry(hass, entry)
        logger.debug("[reload_entry] Unload succeeded")
    except Exception as e:
        logger.error("[reload_entry] Unload failed")

    try:
        await async_setup_entry(hass, entry)
        logger.debug("[reload_entry] Setup succeeded")
    except Exception as e:
        logger.error("[reload_entry] Setup failed")

    logger.debug("[reload_entry] Completed")

    

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up HASL entries"""

    logger.debug(f"[setup_entry] Entering for {entry.entry_id}")

    try:
        device_registry = await dr.async_get_registry(hass)
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
        logger.error("[setup_entry] Failed to create device")
        return False

    try:
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "binary_sensor"))
        logger.debug("[setup_entry] Forward entry setup succeeded")
    except Exception as e:
        logger.error("[setup_entry] Forward entry setup failed")
        return False

    updater = None
    try:
        updater = entry.add_update_listener(reload_entry)
    except Exception as e:
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
    except Exception as e:
        logger.error("[unload_entry] Forward entry unload failed")
        return False

    try:
        hass.data[DOMAIN]["worker"].instances.remove(entry.entry_id)
        logger.debug("[unload_entry] Worker deregistration succeeded")
    except Exception as e:
        logger.error("[unload_entry] Worker deregistration failed")
        return False

    logger.debug("[unload_entry] Completed")
    return True


