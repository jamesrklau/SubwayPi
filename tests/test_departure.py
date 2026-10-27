import departure


def configure_test_clock(monkeypatch):
    """Use predictable times and settings for departure tests."""
    monkeypatch.setattr(departure.time, "time", lambda: 1000)
    monkeypatch.setattr(departure, "WALKING_TIME_MINUTES", 5)
    monkeypatch.setattr(departure, "SAFETY_BUFFER_MINUTES", 2)


def test_calculates_minutes_until_arrival_and_departure(monkeypatch):
    configure_test_clock(monkeypatch)

    arrivals = [
        {
            "route": "F",
            "trip_id": "trip-1",
            "arrival_time": 1600,
        }
    ]

    options = departure.get_departure_options(arrivals)

    assert len(options) == 1
    assert options[0]["minutes_away"] == 10
    assert options[0]["leave_in"] == 3


def test_excludes_trains_that_are_too_close_to_catch(monkeypatch):
    configure_test_clock(monkeypatch)

    arrivals = [
        {
            "route": "F",
            "trip_id": "trip-1",
            "arrival_time": 1300,
        }
    ]

    options = departure.get_departure_options(arrivals)

    assert options == []


def test_includes_train_when_leave_time_is_exactly_zero(monkeypatch):
    configure_test_clock(monkeypatch)

    arrivals = [
        {
            "route": "G",
            "trip_id": "trip-2",
            "arrival_time": 1420,
        }
    ]

    options = departure.get_departure_options(arrivals)

    assert len(options) == 1
    assert options[0]["minutes_away"] == 7
    assert options[0]["leave_in"] == 0


def test_preserves_original_arrival_data(monkeypatch):
    configure_test_clock(monkeypatch)

    arrivals = [
        {
            "route": "R",
            "trip_id": "trip-3",
            "arrival_time": 1600,
        }
    ]

    original = [train.copy() for train in arrivals]

    options = departure.get_departure_options(arrivals)

    assert arrivals == original
    assert options[0]["route"] == "R"
    assert options[0]["trip_id"] == "trip-3"
    assert options[0]["arrival_time"] == 1600


def test_returns_empty_list_when_no_arrivals_are_available(monkeypatch):
    configure_test_clock(monkeypatch)

    assert departure.get_departure_options([]) == []