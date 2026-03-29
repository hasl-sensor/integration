"""SL Platform Constants"""

from enum import IntEnum

HASL_VERSION = "3.2.0b2"
SCHEMA_VERSION = "5"
DOMAIN = "hasl3"
NAME = "Swedish Public Transport Sensor (HASL)"

DEVICE_MANUFACTURER = "hasl.sorlov.com"
DEVICE_MODEL = "Software device"
DEVICE_GUID = (
    "10ba5386-5fad-49c6-8f03-c7a047cd5aa5-6a618956-520c-41d2-9a10-6d7e7353c7f5"
)
SL_TRAFIK_DEVICE_GUID = "feb117a9-c5cb-4f0c-b08e-331d5c081bfc"
SL_TRAFIK_DEVICE_NAME = "SL Traffic"

KEY_COORDINATORS = "coordinators"

SENSOR_RRDEP = "Resrobot Departures"
SENSOR_RRARR = "Resrobot Arrivals"
SENSOR_RRROUTE = 'Resrobot Route Sensor'
SENSOR_STATUS = "status_v2"
SENSOR_ROUTE = "route_v2"
SENSOR_DEPARTURE = "departure_v2"
SERVICE_RESROBOT_KEY = "resrobot_key"
SENSOR_RESROBOT_ROUTE = "resrobot_route"
SENSOR_RESROBOT_DEPARTURE = "resrobot_departure"
SENSOR_RESROBOT_ARRIVAL = "resrobot_arrival"

CONF_API_KEY = "api_key"
CONF_RR_KEY = "rrkey"

CONF_SITE_ID = "siteid"
CONF_SITE_IDS = "siteids"
CONF_SENSOR = "sensor"
CONF_LINE = "line"
CONF_LINES = "lines"
CONF_TRANSPORT = "transport"
CONF_TRANSPORTS = "transports"
CONF_ENABLED = "enabled"
CONF_DIRECTION = "direction"
CONF_TIMEWINDOW = "timewindow"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INTEGRATION_TYPE = "type"
CONF_INTEGRATION_ID = "id"
CONF_SOURCE = "from"
CONF_DESTINATION = "to"
CONF_SOURCE_ID = "fromid"
CONF_DESTINATION_ID = "toid"

class DirectionType(IntEnum):
    """Direction type."""

    ANY = 0
    LEFT = 1
    RIGHT = 2
