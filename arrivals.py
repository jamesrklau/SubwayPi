
import time


def get_arrivals(feed, target_route, target_stop):
    """
    Original route-specific arrival parser.

    Kept for backward compatibility with existing code and tests.
    """
    arrivals = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        trip = trip_update.trip

        if trip.route_id != target_route:
            continue

        for stop in trip_update.stop_time_update:
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
                "arrival_time": arrival_time,
            })

    arrivals.sort(key=lambda train: train["arrival_time"])

    return arrivals


def get_station_arrivals(feeds, station_config, direction=None):
    """
    Collect realtime arrivals for every platform at a station.

    Args:
        feeds: Dictionary mapping feed names to parsed GTFS-Realtime feeds.
        station_config: Configuration returned by build_station_config().
        direction: "northbound", "southbound", or None for both.

    Static route assignments are deliberately not used to filter trains.
    A prediction is included when its stop ID matches a station platform,
    regardless of the trip's route_id.
    """
    valid_directions = {"northbound", "southbound"}

    if direction is not None and direction not in valid_directions:
        raise ValueError(
            "Direction must be 'northbound', 'southbound', or None"
        )

    platforms = station_config.get("platforms", {})

    if direction:
        selected_directions = [direction]
    else:
        selected_directions = [
            "northbound",
            "southbound",
            "unknown",
        ]

    platform_directions = {}

    for selected_direction in selected_directions:
        for platform in platforms.get(selected_direction, []):
            stop_id = platform.get("stop_id")

            if stop_id:
                platform_directions[stop_id] = selected_direction

    if not platform_directions:
        return []

    current_time = time.time()
    arrivals = []

    for feed_name, feed in feeds.items():
        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            trip_update = entity.trip_update
            trip = trip_update.trip

            for stop in trip_update.stop_time_update:
                stop_id = stop.stop_id

                if stop_id not in platform_directions:
                    continue

                if not stop.HasField("arrival"):
                    continue

                arrival_time = stop.arrival.time

                if arrival_time <= current_time:
                    continue

                arrivals.append({
                    "route": trip.route_id,
                    "trip_id": trip.trip_id,
                    "arrival_time": arrival_time,
                    "stop_id": stop_id,
                    "direction": platform_directions[stop_id],
                    "feed": feed_name,
                })

    arrivals.sort(key=lambda train: train["arrival_time"])

    return arrivals
