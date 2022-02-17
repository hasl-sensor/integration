"""Provide info to system health."""
import sys
import logging

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    HASL_VERSION,
    SLAPI_VERSION
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0

    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    logger.debug("[system_health_register] Entered")

    try:
        register.domain = DOMAIN
        register.async_register_info(system_health_info, "/config/integrations")
        logger.debug("[system_health_register] System health registration succeeded")
    except:
        logger.error("[system_health_register] System health registration failed")


async def system_health_info(hass):
    """Get info for the info page."""
    logger.debug("[system_health_info] Entered")
    worker = hass.data[DOMAIN]["worker"]

    try:
        statusObject = {
            "Core Version": HASL_VERSION,
            "Slapi Version": SLAPI_VERSION,
            "Instances": worker.instances.count(),
            "Database Size": f"{get_size(worker.data)} bytes",
            "Startup in progress": worker.status.startup_in_progress,
            "Running tasks": worker.status.running_background_tasks
        }
        logger.debug("[system_health_info] Information gather succeeded")
        return statusObject
    except:
        logger.debug("[system_health_info] Information gather Failed")
        return {
            "Core Version": HASL_VERSION,
            "Slapi Version": SLAPI_VERSION,
            "Instances": "(worker_failed)",
            "Database Size": "(worker_failed)",
            "Startup in progress": "(worker_failed)",
            "Running tasks": "(worker_failed)"
        }
