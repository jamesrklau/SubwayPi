
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from google.transit import gtfs_realtime_pb2


FEED_URLS = {
    "123456": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "ACE": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "JZ": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "NQRW": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "SI": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
}


def download_feed(feed_name):
    """Download and parse one MTA GTFS-Realtime feed."""

    if feed_name not in FEED_URLS:
        raise ValueError(f"Unknown feed: {feed_name}")

    url = FEED_URLS[feed_name]

    request = Request(
        url,
        headers={"User-Agent": "SubwayPi/1.0"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = response.read()

    except HTTPError as error:
        raise RuntimeError(
            f"MTA feed '{feed_name}' returned HTTP "
            f"{error.code} for {url}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Could not reach MTA feed '{feed_name}': {error.reason}"
        ) from error

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)

    return feed
