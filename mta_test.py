from mta import download_feed
from arrivals import get_arrivals
from routes import ROUTES
from departure import get_departure_options
import time

while True:

    all_arrivals = []

    # Get arrivals for every configured route
    for route, settings in ROUTES.items():

        feed = download_feed(settings["feed"])

        arrivals = get_arrivals(
            feed,
            route,
            settings["stop"]
        )

        all_arrivals.extend(arrivals)


    # Sort all trains chronologically
    all_arrivals.sort(
        key=lambda train: train["arrival_time"]
    )


    # Find trains we can realistically catch

    departure_options = get_departure_options(
        all_arrivals
    )


    # Find the next catchable train for each route

    next_trains = {}

    for train in departure_options:

        route = train["route"]

        if route not in next_trains:
             next_trains[route] = train

    # Sort the selected trains chronologically
    upcoming_trains = sorted(
        next_trains.values(),
        key=lambda train: train["arrival_time"]
    )


    # Display
    print("\033[2J\033[H")

    print("🚇 4 AV–9 ST — NORTHBOUND")
    print()

    for train in upcoming_trains:
        print(
            train["route"],
            "train |",
           train["minutes_away"],
            "min |",
            "leave in",
            train["leave_in"],
            "min"
        )


    print()
    print("Last updated:", time.strftime("%H:%M:%S"))
    print("Refreshing in 30 seconds...")

    time.sleep(30)
