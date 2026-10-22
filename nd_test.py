from mta import download_feed


TARGET_STOPS = {
    "F23N": "4 Av-9 St northbound",
    "R33N": "4 Av-9 St northbound"
}


ROUTES = {
    "D": "BDFM",
    "N": "NQRW"
}


for route, feed_name in ROUTES.items():

    print()
    print("=" * 50)
    print(f"Checking {route} trains")
    print("=" * 50)

    feed = download_feed(feed_name)

    found = False

    for entity in feed.entity:

        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        trip = trip_update.trip

        if trip.route_id != route:
            continue

        for stop in trip_update.stop_time_update:

            if stop.stop_id not in TARGET_STOPS:
                continue

            found = True

            print()
            print("Route:", trip.route_id)
            print("Trip:", trip.trip_id)
            print("Direction ID:", trip.direction_id)
            print("Stop:", stop.stop_id)
            print("Station:", TARGET_STOPS[stop.stop_id])

            if stop.HasField("arrival"):
                print("Arrival:", stop.arrival.time)

    if not found:
        print()
        print(f"No {route} trains currently predicted at 4 Av-9 St.")
