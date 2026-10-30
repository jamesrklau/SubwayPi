
from functools import lru_cache
import time

from flask import Flask, render_template, jsonify, request

from mta import download_feed
from arrivals import get_station_arrivals
from stations import load_static_gtfs, build_station_config
from departure import get_departure_options


app = Flask(__name__)

STATION_NAME = "Jay St-MetroTech"
DEFAULT_DIRECTION = "northbound"


@lru_cache(maxsize=1)
def get_station_config():
    """Load and cache the selected station's static GTFS configuration."""
    data = load_static_gtfs()
    return build_station_config(STATION_NAME, *data)


def get_selected_direction():
    """Read and validate the requested travel direction."""
    direction = request.args.get(
        "direction",
        DEFAULT_DIRECTION
    ).lower()

    if direction not in ("northbound", "southbound"):
        direction = DEFAULT_DIRECTION

    return direction


def get_subway_data(max_trains=None, direction=DEFAULT_DIRECTION):
    """Collect station arrivals and calculate catchable departures."""

    station_config = get_station_config()

    # Download each required realtime feed exactly once.
    feeds = {
        feed_name: download_feed(feed_name)
        for feed_name in station_config["feeds"]
    }

    # Collect arrivals for the selected direction.
    all_arrivals = get_station_arrivals(
        feeds,
        station_config,
        direction=direction
    )

    # Apply walking time and safety buffer.
    departure_options = get_departure_options(all_arrivals)

    # Keep only the next catchable train for each route.
    next_trains = {}

    for train in departure_options:
        route = train["route"]

        if route not in next_trains:
            next_trains[route] = train

    upcoming_trains = sorted(
        next_trains.values(),
        key=lambda train: train["arrival_time"]
    )

    if max_trains is not None:
        upcoming_trains = upcoming_trains[:max_trains]

    return upcoming_trains


@app.route("/")
def home():
    direction = get_selected_direction()
    trains = get_subway_data(direction=direction)

    return render_template(
        "index.html",
        trains=trains,
        station_name=STATION_NAME,
        direction=direction,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/compact")
def compact():
    direction = get_selected_direction()
    trains = get_subway_data(
        max_trains=3,
        direction=direction
    )

    return render_template(
        "compact.html",
        trains=trains,
        station_name=STATION_NAME,
        direction=direction,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/api/trains")
def api_trains():
    direction = get_selected_direction()
    trains = get_subway_data(direction=direction)
    print("REQUESTED DIRECTION:", request.args.get("direction"))
    print("SELECTED DIRECTION:", get_selected_direction())  

    return jsonify(trains)


@app.route("/api/compact")
def api_compact():
    direction = get_selected_direction()
    trains = get_subway_data(
        max_trains=3,
        direction=direction
    )

    return jsonify(trains)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
