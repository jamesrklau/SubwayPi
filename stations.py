
import csv
import io
import zipfile
from urllib.request import urlopen


STOPS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip"

FEED_FOR_ROUTE = {
    "1": "123456",
    "2": "123456",
    "3": "123456",
    "4": "123456",
    "5": "123456",
    "6": "123456",
    "7": "123456",
    "S": "123456",
    "A": "ACE",
    "C": "ACE",
    "E": "ACE",
    "B": "BDFM",
    "D": "BDFM",
    "F": "BDFM",
    "FX": "BDFM",
    "M": "BDFM",
    "G": "G",
    "J": "JZ",
    "Z": "JZ",
    "L": "L",
    "N": "NQRW",
    "Q": "NQRW",
    "R": "NQRW",
    "W": "NQRW",
}


def _read_csv_from_zip(archive, filename):
    with archive.open(filename) as file:
        text = io.TextIOWrapper(file, encoding="utf-8")
        return list(csv.DictReader(text))


def load_static_gtfs():
    """Download and load the static GTFS files needed for station discovery."""
    with urlopen(STOPS_URL, timeout=30) as response:
        data = response.read()

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        stops = _read_csv_from_zip(archive, "stops.txt")
        routes = _read_csv_from_zip(archive, "routes.txt")
        trips = _read_csv_from_zip(archive, "trips.txt")
        stop_times = _read_csv_from_zip(archive, "stop_times.txt")

    return stops, routes, trips, stop_times


def build_station_config(station_name, stops, routes, trips, stop_times):
    """
    Build a station-first configuration from static GTFS data.

    Static route information is used only to discover relevant realtime
    feeds. It is not intended to filter realtime train predictions.
    """
    search_name = station_name.strip().casefold()

    station_matches = [
        stop
        for stop in stops
        if stop.get("stop_name", "").strip().casefold() == search_name
        and stop.get("location_type") == "1"
    ]

    if not station_matches:
        raise ValueError(f"Station not found: {station_name}")

    station_ids = {
        station["stop_id"]
        for station in station_matches
        if station.get("stop_id")
    }

    platforms = [
        stop
        for stop in stops
        if stop.get("parent_station") in station_ids
        and stop.get("stop_id")
    ]

    if not platforms:
        raise ValueError(
            f"No platform stops found for station: {station_name}"
        )

    platforms_by_direction = {
        "northbound": [],
        "southbound": [],
        "unknown": [],
    }

    platform_ids = {
        platform["stop_id"]
        for platform in platforms
    }

    for platform in platforms:
        stop_id = platform["stop_id"]

        if stop_id.endswith("N"):
            direction = "northbound"
        elif stop_id.endswith("S"):
            direction = "southbound"
        else:
            direction = "unknown"

        platforms_by_direction[direction].append({
            "stop_id": stop_id,
            "stop_name": platform.get("stop_name", ""),
        })

    trips_by_id = {
        trip["trip_id"]: trip
        for trip in trips
        if trip.get("trip_id")
    }

    routes_by_id = {
        route["route_id"]: route
        for route in routes
        if route.get("route_id")
    }

    serving_routes = set()

    for stop_time in stop_times:
        if stop_time.get("stop_id") not in platform_ids:
            continue

        trip = trips_by_id.get(stop_time.get("trip_id"))
        if not trip:
            continue

        route = routes_by_id.get(trip.get("route_id"))
        if not route:
            continue

        route_name = (
            route.get("route_short_name")
            or route.get("route_id")
        )

        if route_name:
            serving_routes.add(route_name)

    feeds = set()
    unmapped_routes = []

    for route in sorted(serving_routes):
        feed = FEED_FOR_ROUTE.get(route)

        if feed:
            feeds.add(feed)
        else:
            unmapped_routes.append(route)

    for direction_platforms in platforms_by_direction.values():
        direction_platforms.sort(
            key=lambda platform: platform["stop_id"]
        )

    return {
        "station_id": sorted(station_ids)[0],
        "station_ids": sorted(station_ids),
        "name": station_matches[0].get("stop_name", station_name),
        "platforms": platforms_by_direction,
        "routes": sorted(serving_routes),
        "feeds": sorted(feeds),
        "unmapped_routes": unmapped_routes,
    }
