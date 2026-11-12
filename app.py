import time
from flask import Flask, render_template, jsonify, request
from feed_cache import FeedCache
from arrivals import get_station_arrivals
from functools import lru_cache
from stations import (
    load_station_cache,
    get_station_list as build_station_list,
    get_station_config as lookup_station_config,
)

app = Flask(__name__)

feed_cache = None


def start_feed_cache():
    """Initialize and start the background MTA feed cache."""
    global feed_cache

    if feed_cache is not None:
        return

    required_feeds = {
        feed_name
        for station in get_station_list()
        for feed_name in get_station_config(station["station_id"])["feeds"]
    }

    feed_cache = FeedCache(
        feed_names=required_feeds,
        refresh_interval=30,
    )

    # Populate the cache before serving requests.
    feed_cache.refresh_once()

    feed_cache.start()

DEFAULT_STATION_ID = "A32"  # W 4 St-Wash Sq
DEFAULT_DIRECTION = "northbound"


@lru_cache(maxsize=1)
def get_station_data():
    """Download and cache the static GTFS data."""
    return load_station_cache()



def get_station_list():
    """Return the curated list of supported stations."""
    return build_station_list(get_station_data())


def get_station_config(station_id):
    """Return a station configuration from the local cache."""
    return lookup_station_config(get_station_data(), station_id)

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

    # Retrieve the latest cached feeds.
    cached_feeds = feed_cache.get_feeds()

    # Only pass feeds required by this station.
    feeds = {
        feed_name: cached_feeds[feed_name]
        for feed_name in station_config["feeds"]
        if feed_name in cached_feeds
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
	max_trains=5,
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

@app.route("/api/feed-status")
def api_feed_status():
    if feed_cache is None:
        return jsonify({
            "status": "not_started",
            "available_feeds": [],
        }), 503

    status = feed_cache.get_status()

    expected_feeds = list(feed_cache.feed_names)
    available_feeds = status["available_feeds"]

    status["expected_feeds"] = expected_feeds
    status["missing_feeds"] = [
        feed for feed in expected_feeds
        if feed not in available_feeds
    ]

    status["status"] = (
        "healthy"
        if not status["missing_feeds"] and not status["errors"]
        else "degraded"
    )

    return jsonify(status)

if __name__ == "__main__":
    start_feed_cache()
    app.run(
        host="0.0.0.0",
        port=5000
    )
