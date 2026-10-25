import pytest
from google.transit import gtfs_realtime_pb2

from arrivals import get_arrivals


@pytest.fixture
def current_time(monkeypatch):
    """Freeze time so arrival tests are predictable."""
    monkeypatch.setattr("arrivals.time.time", lambda: 1000)


def make_feed(trains):
    """Build a GTFS-realtime feed from simple test data."""
    feed = gtfs_realtime_pb2.FeedMessage()

    for train in trains:
        entity = feed.entity.add()
        entity.id = train["trip_id"]

        if not train.get("has_trip_update", True):
            continue

        trip_update = entity.trip_update
        trip_update.trip.route_id = train["route"]
        trip_update.trip.trip_id = train["trip_id"]

        if not train.get("has_stop_update", True):
            continue

        stop = trip_update.stop_time_update.add()
        stop.stop_id = train["stop"]

        if train.get("has_arrival", True):
            stop.arrival.time = train["arrival_time"]

    return feed


def test_returns_matching_future_arrivals_sorted_by_time(current_time):
    feed = make_feed([
        {
            "route": "A",
            "stop": "A41N",
            "trip_id": "later",
            "arrival_time": 1300,
        },
        {
            "route": "A",
            "stop": "A41N",
            "trip_id": "sooner",
            "arrival_time": 1100,
        },
    ])

    arrivals = get_arrivals(feed, "A", "A41N")

    assert [train["trip_id"] for train in arrivals] == [
        "sooner",
        "later",
    ]


def test_excludes_arrivals_in_the_past(current_time):
    feed = make_feed([
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
    ])

    arrivals = get_arrivals(feed, "A", "A41N")

    assert [train["trip_id"] for train in arrivals] == ["future"]


def test_excludes_wrong_routes_and_stops(current_time):
    feed = make_feed([
        {
            "route": "C",
            "stop": "A41N",
            "trip_id": "wrong-route",
            "arrival_time": 1100,
        },
        {
            "route": "A",
            "stop": "A42N",
            "trip_id": "wrong-stop",
            "arrival_time": 1200,
        },
        {
            "route": "A",
            "stop": "A41N",
            "trip_id": "match",
            "arrival_time": 1300,
        },
    ])

    arrivals = get_arrivals(feed, "A", "A41N")

    assert [train["trip_id"] for train in arrivals] == ["match"]


def test_excludes_entities_without_trip_updates(current_time):
    feed = make_feed([
        {
            "route": "A",
            "stop": "A41N",
            "trip_id": "no-trip-update",
            "has_trip_update": False,
            "arrival_time": 1100,
        },
    ])

    assert get_arrivals(feed, "A", "A41N") == []


def test_excludes_stops_without_arrival_times(current_time):
    feed = make_feed([
        {
            "route": "A",
            "stop": "A41N",
            "trip_id": "no-arrival",
            "has_arrival": False,
        },
    ])

    assert get_arrivals(feed, "A", "A41N") == []