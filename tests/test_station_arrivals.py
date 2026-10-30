
import pytest
from google.transit import gtfs_realtime_pb2

from arrivals import get_station_arrivals


@pytest.fixture
def current_time(monkeypatch):
    monkeypatch.setattr("arrivals.time.time", lambda: 1000)


def make_feed(trains):
    feed = gtfs_realtime_pb2.FeedMessage()

    for train in trains:
        entity = feed.entity.add()
        entity.id = train["trip_id"]

        if not train.get("has_trip_update", True):
            continue

        trip_update = entity.trip_update
        trip_update.trip.route_id = train["route"]
        trip_update.trip.trip_id = train["trip_id"]

        stop = trip_update.stop_time_update.add()
        stop.stop_id = train["stop"]

        if train.get("has_arrival", True):
            stop.arrival.time = train["arrival_time"]

    return feed


@pytest.fixture
def station_config():
    return {
        "name": "Jay St-MetroTech",
        "platforms": {
            "northbound": [
                {"stop_id": "A41N"},
                {"stop_id": "R29N"},
            ],
            "southbound": [
                {"stop_id": "A41S"},
                {"stop_id": "R29S"},
            ],
            "unknown": [],
        },
    }


def test_collects_arrivals_from_multiple_feeds(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "ace-train",
                "arrival_time": 1200,
            },
        ]),
        "NQRW": make_feed([
            {
                "route": "R",
                "stop": "R29N",
                "trip_id": "nqrw-train",
                "arrival_time": 1100,
            },
        ]),
    }

    arrivals = get_station_arrivals(feeds, station_config)

    assert [train["trip_id"] for train in arrivals] == [
        "nqrw-train",
        "ace-train",
    ]


def test_does_not_filter_by_trip_route(
    current_time,
    station_config,
):
    feeds = {
        "BDFM": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "rerouted-train",
                "arrival_time": 1200,
            },
        ]),
    }

    arrivals = get_station_arrivals(feeds, station_config)

    assert len(arrivals) == 1
    assert arrivals[0]["route"] == "A"
    assert arrivals[0]["stop_id"] == "A41N"
    assert arrivals[0]["feed"] == "BDFM"


def test_filters_northbound_arrivals(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "northbound",
                "arrival_time": 1100,
            },
            {
                "route": "A",
                "stop": "A41S",
                "trip_id": "southbound",
                "arrival_time": 1200,
            },
        ]),
    }

    arrivals = get_station_arrivals(
        feeds,
        station_config,
        direction="northbound",
    )

    assert [train["trip_id"] for train in arrivals] == [
        "northbound"
    ]


def test_filters_southbound_arrivals(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "northbound",
                "arrival_time": 1100,
            },
            {
                "route": "A",
                "stop": "A41S",
                "trip_id": "southbound",
                "arrival_time": 1200,
            },
        ]),
    }

    arrivals = get_station_arrivals(
        feeds,
        station_config,
        direction="southbound",
    )

    assert [train["trip_id"] for train in arrivals] == [
        "southbound"
    ]


def test_excludes_past_arrivals(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "past",
                "arrival_time": 900,
            },
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "future",
                "arrival_time": 1100,
            },
        ]),
    }

    arrivals = get_station_arrivals(feeds, station_config)

    assert [train["trip_id"] for train in arrivals] == ["future"]


def test_excludes_unrelated_platforms(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A42N",
                "trip_id": "other-station",
                "arrival_time": 1100,
            },
        ]),
    }

    assert get_station_arrivals(feeds, station_config) == []


def test_excludes_entities_without_trip_updates(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "no-update",
                "arrival_time": 1100,
                "has_trip_update": False,
            },
        ]),
    }

    assert get_station_arrivals(feeds, station_config) == []


def test_excludes_stops_without_arrival_times(
    current_time,
    station_config,
):
    feeds = {
        "ACE": make_feed([
            {
                "route": "A",
                "stop": "A41N",
                "trip_id": "no-arrival",
                "has_arrival": False,
            },
        ]),
    }

    assert get_station_arrivals(feeds, station_config) == []


def test_rejects_invalid_direction(station_config):
    with pytest.raises(ValueError, match="Direction must be"):
        get_station_arrivals({}, station_config, direction="eastbound")


def test_empty_feeds_return_no_arrivals(station_config):
    assert get_station_arrivals({}, station_config) == []
