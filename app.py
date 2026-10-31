
from functools import lru_cache
import time

from flask import Flask, render_template, jsonify, request

from mta import download_feed
from arrivals import get_station_arrivals
from stations import load_static_gtfs, build_station_config


app = Flask(__name__)

DEFAULT_STATION_ID = "A32"  # W 4 St-Wash Sq
DEFAULT_DIRECTION = "northbound"


@lru_cache(maxsize=1)
def get_static_data():
    """Download and cache the static GTFS data."""
    return load_static_gtfs()



def get_station_list():
    """Return a curated, deduplicated list of supported stations."""
    stops, routes, trips, stop_times = get_static_data()

    allowed_names = {
        "w 4 st-wash sq",
        "jay st-metrotech",
        "bergen st",
        "4 av-9 st",
    }

    stations = {}

    for stop in stops:
        if stop.get("location_type") != "1":
            continue

        name = stop.get("stop_name", "").strip()
        normalized_name = name.casefold()

        if normalized_name not in allowed_names:
            continue

        # Build the station config so multiple parent IDs with
        # the same station name are represented as one selection.
        config = build_station_config(
            name,
            stops,
            routes,
            trips,
            stop_times
        )

        station_id = config["station_id"]

        stations[normalized_name] = {
            "station_id": station_id,
            "name": config["name"],
        }

    return sorted(
        stations.values(),
        key=lambda station: station["name"].casefold()
    )



@lru_cache(maxsize=256)
def get_station_config(station_id):
    """Build and cache a station configuration from its GTFS ID."""
    stops, routes, trips, stop_times = get_static_data()

    station = next(
        (
            stop for stop in stops
            if stop.get("stop_id") == station_id
            and stop.get("location_type") == "1"
        ),
        None
    )

    if station is None:
        raise ValueError(f"Unknown station ID: {station_id}")

    return build_station_config(
        station["stop_name"],
        stops,
        routes,
        trips,
        stop_times
    )


def get_selected_station_id():
    """Read and validate the requested station."""
    requested_id = request.args.get(
        "station",
        DEFAULT_STATION_ID
    )

    valid_ids = {
        station["station_id"]
        for station in get_station_list()
    }

    if requested_id not in valid_ids:
        return DEFAULT_STATION_ID

    return requested_id


def get_selected_direction():
    """Read and validate the requested travel direction."""
    direction = request.args.get(
        "direction",
        DEFAULT_DIRECTION
    ).lower()

    if direction not in ("northbound", "southbound"):
        return DEFAULT_DIRECTION

    return direction


def get_subway_data(
    station_id=DEFAULT_STATION_ID,
    max_trains=None,
    direction=DEFAULT_DIRECTION
):
    """Collect and return upcoming arrivals for a station."""
    station_config = get_station_config(station_id)

    # Download each required realtime feed exactly once.
    feeds = {
        feed_name: download_feed(feed_name)
        for feed_name in station_config["feeds"]
    }

    arrivals = get_station_arrivals(
        feeds,
        station_config,
        direction=direction
    )

    # Calculate arrival countdowns without filtering trains out.
    now = time.time()
    upcoming_trains = []

    for train in arrivals:
        train = train.copy()
        train["minutes_away"] = round(
            (train["arrival_time"] - now) / 60
        )
        upcoming_trains.append(train)

    upcoming_trains.sort(
        key=lambda train: train["arrival_time"]
    )

    if max_trains is not None:
        upcoming_trains = upcoming_trains[:max_trains]

    return upcoming_trains


@app.route("/")
def home():
    station_id = get_selected_station_id()
    station_config = get_station_config(station_id)
    direction = get_selected_direction()

    trains = get_subway_data(
        station_id=station_id,
        direction=direction
    )

    return render_template(
        "index.html",
        trains=trains,
        station_name=station_config["name"],
        station_id=station_id,
        stations=get_station_list(),
        direction=direction,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/compact")
def compact():
    station_id = get_selected_station_id()
    station_config = get_station_config(station_id)
    direction = get_selected_direction()

    trains = get_subway_data(
        station_id=station_id,
        max_trains=3,
        direction=direction
    )

    return render_template(
        "compact.html",
        trains=trains,
        station_name=station_config["name"],
        station_id=station_id,
        stations=get_station_list(),
        direction=direction,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/api/stations")
def api_stations():
    return jsonify(get_station_list())


@app.route("/api/trains")
def api_trains():
    station_id = get_selected_station_id()
    direction = get_selected_direction()

    trains = get_subway_data(
        station_id=station_id,
        direction=direction
    )

    return jsonify(trains)


@app.route("/api/compact")
def api_compact():
    station_id = get_selected_station_id()
    direction = get_selected_direction()

    trains = get_subway_data(
        station_id=station_id,
        max_trains=3,
        direction=direction
    )

    return jsonify(trains)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
