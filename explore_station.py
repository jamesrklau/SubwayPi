import csv
import io
import zipfile
import sys
from urllib.request import urlopen


STOPS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip"


FEED_FOR_ROUTE = {
    "1": "123456",
    "2": "123456",
    "3": "123456",
    "4": "123456",
    "5": "123456",
    "6": "123456",

    "A": "ACE",
    "C": "ACE",
    "E": "ACE",

    "B": "BDFM",
    "D": "BDFM",
    "F": "BDFM",
    "M": "BDFM",

    "G": "G",

    "J": "JZ",
    "Z": "JZ",

    "L": "L",

    "N": "NQRW",
    "Q": "NQRW",
    "R": "NQRW",
    "W": "NQRW",

    "S": "123456"
}


def load_gtfs():

    print("Downloading MTA static subway data...")
    print()

    response = urlopen(STOPS_URL)
    data = response.read()

    stops = []
    routes = {}
    trips = {}
    stop_times = []

    with zipfile.ZipFile(io.BytesIO(data)) as archive:

        # ---------------------------------------------------------
        # stops.txt
        # ---------------------------------------------------------

        with archive.open("stops.txt") as file:

            text = io.TextIOWrapper(
                file,
                encoding="utf-8"
            )

            reader = csv.DictReader(text)

            for row in reader:
                stops.append(row)

        # ---------------------------------------------------------
        # routes.txt
        # ---------------------------------------------------------

        with archive.open("routes.txt") as file:

            text = io.TextIOWrapper(
                file,
                encoding="utf-8"
            )

            reader = csv.DictReader(text)

            for row in reader:

                route_id = row.get("route_id", "")

                if route_id:
                    routes[route_id] = row

        # ---------------------------------------------------------
        # trips.txt
        # ---------------------------------------------------------

        with archive.open("trips.txt") as file:

            text = io.TextIOWrapper(
                file,
                encoding="utf-8"
            )

            reader = csv.DictReader(text)

            for row in reader:

                trip_id = row.get("trip_id", "")

                if trip_id:
                    trips[trip_id] = row

        # ---------------------------------------------------------
        # stop_times.txt
        # ---------------------------------------------------------

        with archive.open("stop_times.txt") as file:

            text = io.TextIOWrapper(
                file,
                encoding="utf-8"
            )

            reader = csv.DictReader(text)

            for row in reader:
                stop_times.append(row)

    return stops, routes, trips, stop_times


def find_station(stops, search):

    search = search.strip().lower()

    matches = []

    for stop in stops:

        name = stop.get("stop_name", "").strip().lower()

        if name == search:

            matches.append(stop)

    return matches


def get_child_stops(stops, station_ids):

    child_stops = []

    for stop in stops:

        parent = stop.get("parent_station", "")

        if parent in station_ids:

            child_stops.append(stop)

    return child_stops


def find_routes_for_stops(
    child_stops,
    stop_times,
    trips,
    routes
):

    target_stop_ids = {
        stop.get("stop_id")
        for stop in child_stops
    }

    route_data = {}

    for stop_time in stop_times:

        stop_id = stop_time.get("stop_id", "")

        if stop_id not in target_stop_ids:
            continue

        trip_id = stop_time.get("trip_id", "")

        trip = trips.get(trip_id)

        if not trip:
            continue

        route_id = trip.get("route_id", "")

        if not route_id:
            continue

        route = routes.get(route_id)

        if not route:
            continue

        route_short_name = route.get(
            "route_short_name",
            route_id
        )

        direction_id = trip.get(
            "direction_id",
            ""
        )

        if route_short_name not in route_data:

            route_data[route_short_name] = {
                "stop_ids": set(),
                "direction_ids": set()
            }

        route_data[route_short_name]["stop_ids"].add(
            stop_id
        )

        route_data[route_short_name]["direction_ids"].add(
            direction_id
        )

    return route_data


def choose_direction(route_data):

    print()
    print("Available directions:")
    print()

    directions = {}

    for route, data in sorted(route_data.items()):

        stops = sorted(data["stop_ids"])

        print(
            f"{route}: "
            f"{', '.join(stops)}"
        )

        for stop_id in stops:

            if stop_id.endswith("N"):

                directions.setdefault(
                    "N",
                    []
                ).append(
                    (route, stop_id)
                )

            elif stop_id.endswith("S"):

                directions.setdefault(
                    "S",
                    []
                ).append(
                    (route, stop_id)
                )

    print()
    print("N = northbound / generally Manhattan-bound")
    print("S = southbound / generally Brooklyn-bound")
    print()

    choice = input(
        "Which direction do you want? [N/S]: "
    ).strip().upper()

    if choice not in directions:

        print()
        print("Invalid direction.")
        return None

    return directions[choice]


def print_settings(routes):

    print()
    print("=" * 70)
    print("COPY THIS INTO routes.py")
    print("=" * 70)
    print()

    for route, stop_id in routes:

        feed = FEED_FOR_ROUTE.get(route)

        if not feed:

            print(
                f"# WARNING: No realtime feed mapping for {route}"
            )
            continue

        print(f'    "{route}": {{')
        print(f'        "feed": "{feed}",')
        print(f'        "stop": "{stop_id}"')
        print("    },")

    print()
    print("=" * 70)
    print()


def main():

    if len(sys.argv) < 2:

        print()
        print("Usage:")
        print()
        print('python explore_station.py "Jay St-MetroTech"')
        print()

        return

    search = " ".join(sys.argv[1:])

    stops, routes, trips, stop_times = load_gtfs()

    station_matches = find_station(
        stops,
        search
    )

    if not station_matches:

        print()
        print("Station not found.")
        print()
        print("Use:")
        print("python list_stations.py")
        print()

        return

    print()
    print("Station matches:")
    print()

    for station in station_matches:

        print(
            station.get("stop_id"),
            "|",
            station.get("stop_name")
        )

    station_ids = {
        station.get("stop_id")
        for station in station_matches
    }

    child_stops = get_child_stops(
        stops,
        station_ids
    )

    if not child_stops:

        print()
        print("No platform stops found.")
        return

    print()
    print("Platforms:")
    print()

    for stop in sorted(
        child_stops,
        key=lambda item: item.get("stop_id", "")
    ):

        print(
            stop.get("stop_id"),
            "|",
            stop.get("stop_name")
        )

    route_data = find_routes_for_stops(
        child_stops,
        stop_times,
        trips,
        routes
    )

    if not route_data:

        print()
        print("No routes found.")
        return

    print()
    print("Train lines serving this station:")
    print()

    for route in sorted(route_data):

        stops_for_route = sorted(
            route_data[route]["stop_ids"]
        )

        print(
            f"{route}: "
            f"{', '.join(stops_for_route)}"
        )

    selected_routes = choose_direction(
        route_data
    )

    if selected_routes is None:
        return

    print_settings(
        selected_routes
    )


if __name__ == "__main__":
    main()
