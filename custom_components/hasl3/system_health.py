"""Provide info to system health."""
import logging

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

from .const import (
    DOMAIN,
    HASL_VERSION,
    SLAPI_VERSION
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.core")

def total_size(o, handlers={}, verbose=False):
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers) # user handlers take precedence
    seen = set()                  # track which object id's have already been seen
    default_size = getsizeof(0)   # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen: # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)

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
            "Database Size": f"{total_size(worker.data)} bytes",
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


