
import pytest

from stations import build_station_config


@pytest.fixture
def station_data():
    stops = [
        {
            "stop_id": "JAY",
            "stop_name": "Jay St-MetroTech",
            "location_type": "1",
            "parent_station": "",
        },
        {
            "stop_id": "A41N",
            "stop_name": "Jay St-MetroTech",
            "location_type": "0",
            "parent_station": "JAY",
        },
        {
            "stop_id": "A41S",
            "stop_name": "Jay St-MetroTech",
            "location_type": "0",
            "parent_station": "JAY",
        },
        {
            "stop_id": "R29N",
            "stop_name": "Jay St-MetroTech",
            "location_type": "0",
            "parent_station": "JAY",
        },
        {
            "stop_id": "R29S",
            "stop_name": "Jay St-MetroTech",
            "location_type": "0",
            "parent_station": "JAY",
        },
    ]

    routes = [
        {"route_id": "A", "route_short_name": "A"},
        {"route_id": "C", "route_short_name": "C"},
        {"route_id": "R", "route_short_name": "R"},
    ]

    trips = [
        {"trip_id": "trip-a", "route_id": "A"},
        {"trip_id": "trip-c", "route_id": "C"},
        {"trip_id": "trip-r", "route_id": "R"},
    ]

    stop_times = [
        {"trip_id": "trip-a", "stop_id": "A41N"},
        {"trip_id": "trip-c", "stop_id": "A41S"},
        {"trip_id": "trip-r", "stop_id": "R29N"},
        {"trip_id": "trip-r", "stop_id": "R29S"},
    ]

    return stops, routes, trips, stop_times


def test_discovers_station_platforms_and_directions(station_data):
    stops, routes, trips, stop_times = station_data

    config = build_station_config(
        "Jay St-MetroTech",
        stops,
        routes,
        trips,
        stop_times,
    )

    assert config["station_id"] == "JAY"

    assert [
        platform["stop_id"]
        for platform in config["platforms"]["northbound"]
    ] == ["A41N", "R29N"]

    assert [
        platform["stop_id"]
        for platform in config["platforms"]["southbound"]
    ] == ["A41S", "R29S"]


def test_discovers_relevant_realtime_feeds(station_data):
    stops, routes, trips, stop_times = station_data

    config = build_station_config(
        "Jay St-MetroTech",
        stops,
        routes,
        trips,
        stop_times,
    )

    assert config["routes"] == ["A", "C", "R"]
    assert config["feeds"] == ["ACE", "NQRW"]
    assert config["unmapped_routes"] == []


def test_station_search_is_case_insensitive(station_data):
    stops, routes, trips, stop_times = station_data

    config = build_station_config(
        "JAY ST-METROTECH",
        stops,
        routes,
        trips,
        stop_times,
    )

    assert config["name"] == "Jay St-MetroTech"


def test_unknown_station_raises_error(station_data):
    stops, routes, trips, stop_times = station_data

    with pytest.raises(ValueError, match="Station not found"):
        build_station_config(
            "Unknown Station",
            stops,
            routes,
            trips,
            stop_times,
        )


def test_station_without_platforms_raises_error():
    stops = [
        {
            "stop_id": "EMPTY",
            "stop_name": "Empty Station",
            "location_type": "1",
            "parent_station": "",
        }
    ]

    with pytest.raises(ValueError, match="No platform stops"):
        build_station_config(
            "Empty Station",
            stops,
            [],
            [],
            [],
        )
