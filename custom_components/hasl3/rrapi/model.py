from typing import TypedDict, NotRequired
from enum import StrEnum


class LocationSearchType(StrEnum):
    ALL = "ALL"  # Search in all existing location pools
    STOP = "S"  # Search for station/stops only
    ADDRESS = "A"  # Search for addresses only
    POI = "P"  # Search for POIs only
    STOP_OR_ADDRESS = "SA"  # Search for station/stops and addresses
    STOP_OR_POI = "SP"  # Search for station/stops and POIs
    ADDRESS_OR_POI = "AP"  # Search for addresses and POIs


class BoardLanguage(StrEnum):
    SV = "sv"  # Swedish
    EN = "en"  # English
    DA = "da"  # Danish
    NO = "no"  # Norwegian
    DE = "de"  # German
    FR = "fr"  # French
    IT = "it"  # Italian
    NL = "nl"  # Dutch
    TR = "tr"  # Turkish
    PL = "pl"  # Polish
    ES = "es"  # Spanish
    HU = "hu"  # Hungarian


class LocationType(StrEnum):
    ST = "ST"  # Stop or station
    ADR = "ADR"  # Address
    POI = "POI"  # Point of interest
    CRD = "CRD"  # Coordinate
    MCP = "MCP"  # Mode change point
    HL = "HL"  # Hailing point


class TransportCategory(StrEnum):
    BLT = "BLT"  # Regional bus (lanstrafik), e.g. SL, UL, Skanetrafiken
    BXB = "BXB"  # Express bus
    BAX = "BAX"  # Airport express bus
    BRE = "BRE"  # Regional bus other than lanstrafik
    BBL = "BBL"  # Train replacement bus
    ULT = "ULT"  # Metro
    JAX = "JAX"  # Airport express train
    JEX = "JEX"  # Express train
    JIC = "JIC"  # InterCity train
    JLT = "JLT"  # Local train
    JPT = "JPT"  # PagaTag
    JST = "JST"  # High-speed train
    JRE = "JRE"  # Regional train
    SLT = "SLT"  # Tram
    FLT = "FLT"  # Local ferry
    FUT = "FUT"  # International ferry


class JourneyStatus(StrEnum):
    PLANNED = "P"  # Planned
    REPLACEMENT = "R"  # Replacement
    ADDITIONAL = "A"  # Additional
    SPECIAL = "S"  # Special


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


class JourneyDetailRef(TypedDict):
    ref: str


class Stop(TypedDict):
    name: str
    id: str
    extId: str
    lon: float
    lat: float
    routeIdx: int
    arrTime: NotRequired[str]
    arrDate: NotRequired[str]
    depTime: NotRequired[str]
    depDate: NotRequired[str]


class Product(TypedDict):
    name: str
    cls: str
    internalName: NotRequired[str]
    num: NotRequired[str]
    displayNumber: NotRequired[str]
    line: NotRequired[str]
    lineId: NotRequired[str]
    catCode: NotRequired[str]
    catOut: NotRequired[TransportCategory]
    catIn: NotRequired[TransportCategory]
    catOutS: NotRequired[TransportCategory]
    catOutL: NotRequired[str]
    operatorCode: NotRequired[str]
    operator: NotRequired[str]


class DepartureStops(TypedDict):
    stop: list[Stop]


class DepartureBoardEntry(TypedDict):
    Stops: DepartureStops
    ProductAtStop: Product
    Product: list[Product]
    name: str
    type: LocationType
    stop: str
    stopid: str
    stopExtId: str
    time: str  # Scheduled departure/arrival time, formatted as HH:MM:SS
    date: str  # Scheduled departure/arrival date, formatted as YYYY-MM-DD
    rtTime: NotRequired[str]  # Realtime departure/arrival time, formatted as HH:MM:SS
    rtDate: NotRequired[str]  # Realtime departure/arrival date, formatted as YYYY-MM-DD
    direction: str
    transportNumber: str
    transportCategory: TransportCategory
    reachable: NotRequired[bool]
    JourneyStatus: NotRequired[JourneyStatus]
    JourneyDetailRef: NotRequired[JourneyDetailRef]


class ArrivalBoardEntry(TypedDict):
    Stops: list[Stop]
    ProductAtStop: Product
    Product: list[Product]
    name: str
    type: LocationType
    stop: str
    stopid: str
    stopExtId: str
    time: str
    date: str
    direction: str
    transportNumber: str
    transportCategory: TransportCategory
    origin: str
    JourneyStatus: NotRequired[JourneyStatus]
    JourneyDetailRef: NotRequired[JourneyDetailRef]


class ListOfDepartures(TypedDict):
    Departure: list[DepartureBoardEntry]
    requestId: NotRequired[str]


class ListOfArrivals(TypedDict):
    Arrival: list[ArrivalBoardEntry]
    requestId: NotRequired[str]


class ResrobotException(TypedDict):
    errorCode: str
    errorText: str
