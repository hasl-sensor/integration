from datetime import datetime
from zoneinfo import ZoneInfo

from .model import ListOfDepartures, ListOfArrivals, TransportCategory

transportMap = {
    "BLT": "BUS",
    "BXB": "BUS",
    "BAX": "BUS",
    "BRE": "BUS",
    "BBL": "BUS",
    "ULT": "METRO",
    "JAX": "TRAIN",
    "JEX": "TRAIN",
    "JIC": "TRAIN",
    "JLT": "TRAIN",
    "JPT": "TRAIN",
    "JST": "TRAIN",
    "JRE": "TRAIN",
    "SLT": "TRAM",
    "FLT": "FERRY",
    "FUT": "FERRY",
}

iconswitcher = {
    "BLT": "mdi:bus",
    "BXB": "mdi:bus",
    "ULT": "mdi:subway-variant",
    "JAX": "mdi:train",
    "JLT": "mdi:train",
    "JRE": "mdi:train",
    "JIC": "mdi:train",
    "JPT": "mdi:train",
    "JEX": "mdi:train",
    "SLT": "mdi:tram",
    "FLT": "mdi:ferry",
    "FUT": "mdi:ferry",
}


def convert_date_and_time_to_dateime(date: str, time: str, timezone: ZoneInfo):
    return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone
    )


def map_rr_departures_to_v4_departures(data: ListOfDepartures, timezone: ZoneInfo):
    departures = []
    for departure in data["Departure"]:
        (date, time) = departure["date"], departure["time"]
        scheduledTime = convert_date_and_time_to_dateime(date, time, timezone)
        expectedTime = convert_date_and_time_to_dateime(
            departure.get("rtDate", date), departure.get("rtTime", time), timezone
        )

        departures.append(
            {
                "destination": departure["direction"],
                "direction": "",
                "direction_code": departure.get("directionFlag", 0),
                "state": "EXPECTED",
                "display": departure["name"],
                "stop_point": {"name": departure["stop"], "designation": ""},
                "line": {
                    "id": departure["ProductAtStop"].get("lineId", 0),
                    "designation": departure["ProductAtStop"].get("displayNumber"),
                    "transport_mode": transportMap.get(
                        departure["ProductAtStop"].get("catOut", TransportCategory.BLT)
                    ),
                    "group_of_lines": "",
                },
                "scheduled": scheduledTime.isoformat(),
                "expected": expectedTime.isoformat(),
            }
        )

    return departures


def map_rr_arrivals_to_v4_departures(data: ListOfArrivals, timezone: ZoneInfo):
    arrivals = []
    for arrival in data["Arrival"]:
        (date, time) = arrival["date"], arrival["time"]
        scheduledTime = convert_date_and_time_to_dateime(date, time, timezone)
        expectedTime = convert_date_and_time_to_dateime(
            arrival.get("rtDate", date), arrival.get("rtTime", time), timezone
        )

        arrivals.append(
            {
                "destination": arrival["direction"],
                "direction": "",
                "direction_code": arrival.get("directionFlag", 0),
                "state": "EXPECTED",
                "display": arrival["name"],
                "stop_point": {"name": arrival["stop"], "designation": ""},
                "line": {
                    "id": arrival["ProductAtStop"].get("lineId", 0),
                    "designation": arrival["ProductAtStop"].get("displayNumber"),
                    "transport_mode": transportMap.get(
                        arrival["ProductAtStop"].get("catOut", TransportCategory.ULT)
                    ),
                    "group_of_lines": "",
                },
                "scheduled": scheduledTime.isoformat(),
                "expected": expectedTime.isoformat(),
            }
        )

    return arrivals


def map_rr_departures_to_legacy_departures(
    data: ListOfDepartures, now: datetime, timezone: ZoneInfo
):
    departures = []
    for departure in data["Departure"]:
        date, time = departure["date"], departure["time"]

        if "rtDate" in departure and "rtTime" in departure:
            diff_date, diff_time = departure["rtDate"], departure["rtTime"]
        else:
            diff_date, diff_time = date, time

        adjustedDateTime = now.replace(tzinfo=None)
        diff = (
            datetime.strptime(f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S")
            - adjustedDateTime
        )
        diff = round(diff.total_seconds() / 60)

        expected = datetime.strptime(
            f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone)

        departures.append(
            {
                "line": departure["ProductAtStop"].get("displayNumber"),
                "direction": departure.get("directionFlag"),
                "departure": datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S"),
                "destination": departure["direction"],
                "time": diff,
                "operator": departure["ProductAtStop"].get("operator"),
                "expected": expected,
                "type": departure["ProductAtStop"].get("catOut"),
                "icon": iconswitcher.get(departure["type"], "mdi:train"),
            }
        )

    return departures


def map_rr_arrivals_to_legacy_arrivals(
    data: ListOfArrivals, now: datetime, timezone: ZoneInfo
):
    arrivals = []
    for arrival in data["Arrival"]:
        date, time = arrival["date"], arrival["time"]

        if "rtDate" in arrival and "rtTime" in arrival:
            diff_date, diff_time = arrival["rtDate"], arrival["rtTime"]
        else:
            diff_date, diff_time = date, time

        adjustedDateTime = now.replace(tzinfo=None)
        diff = (
            datetime.strptime(f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S")
            - adjustedDateTime
        )
        diff = round(diff.total_seconds() / 60)

        expected = datetime.strptime(
            f"{diff_date} {diff_time}", "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone)

        arrivals.append(
            {
                "line": arrival["ProductAtStop"].get("displayNumber"),
                "arrival": datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S"),
                "origin": arrival["origin"],
                "time": diff,
                "operator": arrival["ProductAtStop"].get("operator"),
                "expected": expected,
                "type": arrival["ProductAtStop"].get("catOut"),
                "icon": iconswitcher.get(arrival["type"], "mdi:train"),
            }
        )

    return arrivals
