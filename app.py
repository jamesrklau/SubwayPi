from flask import Flask, render_template, jsonify
import time

from mta import download_feed
from arrivals import get_arrivals
from routes import ROUTES, STATION_NAME
from departure import get_departure_options


app = Flask(__name__)


def get_subway_data(max_trains=None):

    all_arrivals = []

    for route, settings in ROUTES.items():

        feed = download_feed(settings["feed"])

        arrivals = get_arrivals(
            feed,
            route,
            settings["stop"]
        )

        all_arrivals.extend(arrivals)

    all_arrivals.sort(
        key=lambda train: train["arrival_time"]
    )

    departure_options = get_departure_options(
        all_arrivals
    )

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

    trains = get_subway_data()

    return render_template(
        "index.html",
        trains=trains,
        station_name=STATION_NAME,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/compact")
def compact():

    trains = get_subway_data(max_trains=3)

    return render_template(
        "compact.html",
        trains=trains,
        station_name=STATION_NAME,
        updated=time.strftime("%H:%M:%S")
    )


@app.route("/api/trains")
def api_trains():

    trains = get_subway_data()

    return jsonify(trains)


@app.route("/api/compact")
def api_compact():

    trains = get_subway_data(max_trains=3)

    return jsonify(trains)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
