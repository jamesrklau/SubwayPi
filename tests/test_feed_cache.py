from feed_cache import FeedCache


def test_refresh_loads_all_feeds():
    calls = []

    def fake_downloader(feed_name):
        calls.append(feed_name)
        return f"data-{feed_name}"

    cache = FeedCache(
        ["ACE", "BDFM", "G"],
        downloader=fake_downloader,
    )

    cache.refresh_once()

    assert calls == ["ACE", "BDFM", "G"]
    assert cache.get_feeds() == {
        "ACE": "data-ACE",
        "BDFM": "data-BDFM",
        "G": "data-G",
    }


def test_failed_refresh_preserves_previous_feed():
    attempts = {"count": 0}

    def fake_downloader(feed_name):
        attempts["count"] += 1

        if attempts["count"] == 1:
            return "original-data"

        raise RuntimeError("MTA unavailable")

    cache = FeedCache(
        ["ACE"],
        downloader=fake_downloader,
    )

    cache.refresh_once()
    cache.refresh_once()

    assert cache.get_feeds()["ACE"] == "original-data"
    assert "ACE" in cache.get_status()["errors"]


def test_successful_refresh_clears_previous_error():
    attempts = {"count": 0}

    def fake_downloader(feed_name):
        attempts["count"] += 1

        if attempts["count"] == 1:
            raise RuntimeError("Temporary failure")

        return "updated-data"

    cache = FeedCache(
        ["ACE"],
        downloader=fake_downloader,
    )

    cache.refresh_once()
    assert "ACE" in cache.get_status()["errors"]

    cache.refresh_once()

    assert cache.get_feeds()["ACE"] == "updated-data"
    assert "ACE" not in cache.get_status()["errors"]


def test_duplicate_feed_names_are_removed():
    cache = FeedCache(
        ["ACE", "BDFM", "ACE"],
        downloader=lambda name: name,
    )

    assert cache.feed_names == ("ACE", "BDFM")
