from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .. import const


class HASLDevice(Entity):
    """HASL Device class."""

    @classmethod
    def get_device_info(cls):
        return {
            "identifiers": {(const.DOMAIN, const.DEVICE_GUID)},
            "name": const.DEVICE_NAME,
            "manufacturer": const.DEVICE_MANUFACTURER,
            "model": const.DEVICE_MODEL,
            "sw_version": const.HASL_VERSION,
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def device_info(self):
        """Return device information about HASL Device."""
        return self.get_device_info()


SL_TRAFFIK_DEVICE_INFO = DeviceInfo(
    entry_type=DeviceEntryType.SERVICE,
    identifiers={(const.DOMAIN, const.SL_TRAFIK_DEVICE_GUID)},
    manufacturer=const.DEVICE_MANUFACTURER,
    model=const.DEVICE_MODEL,
    name=const.SL_TRAFIK_DEVICE_NAME,
    sw_version=const.HASL_VERSION,
)
