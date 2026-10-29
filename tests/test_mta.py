from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest
from google.transit import gtfs_realtime_pb2

from mta import download_feed


def test_rejects_unknown_feed():
    with pytest.raises(ValueError, match="Unknown feed"):
        download_feed("UNKNOWN")


@patch("mta.urlopen")
def test_downloads_and_parses_feed(mock_urlopen):
    expected_feed = gtfs_realtime_pb2.FeedMessage()

    # GTFS-Realtime requires a header.
    expected_feed.header.gtfs_realtime_version = "2.0"

    entity = expected_feed.entity.add()
    entity.id = "test-entity"

    response = MagicMock()
    response.read.return_value = expected_feed.SerializeToString()

    mock_urlopen.return_value.__enter__.return_value = response

    feed = download_feed("ACE")

    assert len(feed.entity) == 1
    assert feed.entity[0].id == "test-entity"
    mock_urlopen.assert_called_once()


@patch("mta.urlopen")
def test_handles_http_errors(mock_urlopen):
    mock_urlopen.side_effect = HTTPError(
        "https://example.com/feed",
        503,
        "Service Unavailable",
        None,
        None,
    )

    with pytest.raises(RuntimeError, match="HTTP 503"):
        download_feed("ACE")


@patch("mta.urlopen")
def test_handles_network_errors(mock_urlopen):
    mock_urlopen.side_effect = URLError("Network unavailable")

    with pytest.raises(RuntimeError, match="Could not reach MTA feed"):
        download_feed("ACE")