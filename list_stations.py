import csv
import io
import zipfile
from urllib.request import urlopen


STOPS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip"


def load_stops():

    print("Downloading MTA subway station data...")
    print()

    response = urlopen(STOPS_URL)
    data = response.read()

    stops = []

    with zipfile.ZipFile(io.BytesIO(data)) as archive:

        with archive.open("stops.txt") as file:

            text = io.TextIOWrapper(
                file,
                encoding="utf-8"
            )

            reader = csv.DictReader(text)

            for row in reader:
                stops.append(row)

    return stops


def get_stations(stops):

    stations = {}

    for stop in stops:

        location_type = stop.get("location_type", "")

        # GTFS station records use location_type 1
        if location_type != "1":
            continue

        station_id = stop.get("stop_id", "")
        station_name = stop.get("stop_name", "")

        if not station_id or not station_name:
            continue

        stations[station_id] = {
            "name": station_name,
            "lat": stop.get("stop_lat", ""),
            "lon": stop.get("stop_lon", "")
        }

    return stations


def main():

    stops = load_stops()
    stations = get_stations(stops)

    print()
    print("=" * 70)
    print("NYC SUBWAY STATION DIRECTORY")
    print("=" * 70)
    print()

    sorted_stations = sorted(
        stations.items(),
        key=lambda item: item[1]["name"].lower()
    )

    print(f"{'STATION':<40} {'ID':<12} {'LAT':<12} {'LON'}")
    print("-" * 70)

    for station_id, station in sorted_stations:

        print(
            f"{station['name']:<40}"
            f"{station_id:<12}"
            f"{station['lat']:<12}"
            f"{station['lon']}"
        )

    print()
    print(f"Total stations: {len(sorted_stations)}")
    print()


if __name__ == "__main__":
    main()
