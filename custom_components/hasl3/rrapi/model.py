from typing import TypedDict, NotRequired
from enum import Enum


class LocationSearchType(Enum):
    ALL = "ALL"  # Search in all existing location pools
    STOP = "S"  # Search for station/stops only
    ADDRESS = "A"  # Search for addresses only
    POI = "P"  # Search for POIs only
    STOP_OR_ADDRESS = "SA"  # Search for station/stops and addresses
    STOP_OR_POI = "SP"  # Search for station/stops and POIs
    ADDRESS_OR_POI = "AP"  # Search for addresses and POIs


class StopLookupEntry(TypedDict):
    id: str
    extId: NotRequired[str]
    name: str
    lon: float
    lat: float
    weight: int


class StopLocationWrapper(TypedDict):
    StopLocation: NotRequired[StopLookupEntry]
    CoordLocation: NotRequired[StopLookupEntry]


class StopLookupResponse(TypedDict):
    stopLocationOrCoordLocation: list[StopLocationWrapper]
