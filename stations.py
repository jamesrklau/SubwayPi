
import csv
import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


STOPS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip"

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "data"
CACHE_FILE = CACHE_DIR / "station_configs.json"

ALLOWED_STATIONS = {
    "w 4 st-wash sq",
    "jay st-metrotech",
    "bergen st",
    "4 av-9 st",
}

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


def _read_csv(archive, filename):
    """Open a CSV member from the GTFS ZIP archive."""
    with archive.open(filename) as file:
        text = io.TextIOWrapper(file, encoding="utf-8")
        yield from csv.DictReader(text)


def _load_relevant_stops(archive):
    """Find supported parent stations and their platform stops."""
    parents = {}
    parent_ids = set()

    # First pass: identify supported parent stations.
    for stop in _read_csv(archive, "stops.txt"):
        name = stop.get("stop_name", "").strip()
        normalized = name.casefold()

        if (
            stop.get("location_type") == "1"
            and normalized in ALLOWED_STATIONS
            and stop.get("stop_id")
        ):
            parents.setdefault(normalized, []).append({
                "stop_id": stop["stop_id"],
                "name": name,
            })
            parent_ids.add(stop["stop_id"])

    if not parents:
        raise RuntimeError("No supported stations were found in GTFS.")

    # Second pass: retain only platforms belonging to those parents.
    platforms = {parent_id: [] for parent_id in parent_ids}

    for stop in _read_csv(archive, "stops.txt"):
        parent_id = stop.get("parent_station")
        stop_id = stop.get("stop_id")

        if parent_id in parent_ids and stop_id:
            platforms[parent_id].append({
                "stop_id": stop_id,
                "stop_name": stop.get("stop_name", ""),
            })

    return parents, platforms


def _build_configurations(archive):
    """Build compact configurations for the supported stations."""
    parents, platforms_by_parent = _load_relevant_stops(archive)

    # Combine platforms for stations that have multiple parent IDs.
    station_data = {}

    for normalized_name, parent_records in parents.items():
        station_ids = sorted(
            record["stop_id"] for record in parent_records
        )

        platform_records = []
        for parent_id in station_ids:
            platform_records.extend(platforms_by_parent[parent_id])

        platform_ids = {
            platform["stop_id"] for platform in platform_records
        }

        directions = {
            "northbound": [],
            "southbound": [],
            "unknown": [],
        }

        for platform in platform_records:
            stop_id = platform["stop_id"]

            if stop_id.endswith("N"):
                direction = "northbound"
            elif stop_id.endswith("S"):
                direction = "southbound"
            else:
                direction = "unknown"

            directions[direction].append(platform)

        for items in directions.values():
            items.sort(key=lambda item: item["stop_id"])

        station_data[normalized_name] = {
            "station_id": station_ids[0],
            "station_ids": station_ids,
            "name": parent_records[0]["name"],
            "platforms": directions,
            "platform_ids": platform_ids,
            "routes": set(),
        }

    all_platform_ids = set()
    for station in station_data.values():
        all_platform_ids.update(station["platform_ids"])

    # Find only trips that serve one of our supported platforms.
    relevant_trip_ids = set()
    trips_by_station = {
        name: set() for name in station_data
    }

    for stop_time in _read_csv(archive, "stop_times.txt"):
        stop_id = stop_time.get("stop_id")
        trip_id = stop_time.get("trip_id")

        if stop_id not in all_platform_ids or not trip_id:
            continue

        relevant_trip_ids.add(trip_id)

        for name, station in station_data.items():
            if stop_id in station["platform_ids"]:
                trips_by_station[name].add(trip_id)

    # Retain route IDs only for relevant trips.
    relevant_routes = {}

    for trip in _read_csv(archive, "trips.txt"):
        trip_id = trip.get("trip_id")
        route_id = trip.get("route_id")

        if trip_id in relevant_trip_ids and route_id:
            relevant_routes[trip_id] = route_id

    # Load only route records referenced by those trips.
    route_names = {}

    for route in _read_csv(archive, "routes.txt"):
        route_id = route.get("route_id")

        if route_id in set(relevant_routes.values()):
            route_names[route_id] = (
                route.get("route_short_name") or route_id
            )

    # Assemble each station's final configuration.
    configurations = {}

    for name, station in station_data.items():
        serving_routes = set()

        for trip_id in trips_by_station[name]:
            route_id = relevant_routes.get(trip_id)
            route_name = route_names.get(route_id)

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

        configurations[station["station_id"]] = {
            "station_id": station["station_id"],
            "station_ids": station["station_ids"],
            "name": station["name"],
            "platforms": station["platforms"],
            "routes": sorted(serving_routes),
            "feeds": sorted(feeds),
            "unmapped_routes": unmapped_routes,
        }

    return configurations


def build_station_cache():
    """Download GTFS once and write compact station configurations."""
    print("Downloading static GTFS data...")

    with urlopen(STOPS_URL, timeout=30) as response:
        data = response.read()

    print(f"Downloaded {len(data):,} bytes.")
    print("Building station configurations...")

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        configurations = _build_configurations(archive)

    if not configurations:
        raise RuntimeError("No station configurations were generated.")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stations": configurations,
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = CACHE_FILE.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, separators=(",", ":"))
        file.flush()
        os.fsync(file.fileno())

    os.replace(temporary_file, CACHE_FILE)

    print(f"Station cache saved: {CACHE_FILE}")
    print(f"Stations generated: {len(configurations)}")

    for config in configurations.values():
        print(
            f"  {config['name']}: "
            f"{', '.join(config['routes'])} "
            f"(feeds: {', '.join(config['feeds'])})"
        )

    return configurations


def load_station_cache():
    """Load the compact station configuration cache."""
    if not CACHE_FILE.exists():
        raise RuntimeError(
            f"Station cache not found: {CACHE_FILE}. "
            "Run python stations.py --build-cache first."
        )

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        configurations = payload["stations"]

        if not configurations:
            raise ValueError("Station cache is empty.")

        return configurations

    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(
            f"Could not load station cache: {error}"
        ) from error


def get_station_list(configurations):
    """Return the curated station list."""
    return sorted(
        [
            {
                "station_id": config["station_id"],
                "name": config["name"],
            }
            for config in configurations.values()
        ],
        key=lambda station: station["name"].casefold(),
    )


def get_station_config(configurations, station_id):
    """Return a cached configuration by station ID."""
    config = configurations.get(station_id)

    if config is None:
        raise ValueError(f"Unknown station ID: {station_id}")

    return config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build or inspect the SubwayPi station cache."
    )
    parser.add_argument(
        "--build-cache",
        action="store_true",
        help="Download GTFS and build the station cache.",
    )
    args = parser.parse_args()

    if args.build_cache:
        build_station_cache()
    else:
        print("Use: python stations.py --build-cache")
