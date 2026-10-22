import time


def get_arrivals(feed, target_route, target_stop):

    arrivals = []

    for entity in feed.entity:

        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip

        if trip.route_id != target_route:
            continue

        for stop in entity.trip_update.stop_time_update:

            if stop.stop_id != target_stop:
                continue

            if not stop.HasField("arrival"):
                continue

            arrival_time = stop.arrival.time

            if arrival_time <= time.time():
                continue

            arrivals.append({
                "route": trip.route_id,
                "trip_id": trip.trip_id,
                "arrival_time": arrival_time
            })

    arrivals.sort(key=lambda train: train["arrival_time"])

    return arrivals
