from urllib.request import urlopen
from google.transit import gtfs_realtime_pb2
from urllib.error import HTTPError, URLError

FEED_URLS = {
    "ACE": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "NQRW": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
}


def download_feed(feed_name):
       if feed_name not in FEED_URLS:
           raise ValueError(f"Unknown feed: {feed_name}")

       url = FEED_URLS[feed_name]
       try:
           with urlopen(url, timeout=10) as response:
               data = response.read()
       except HTTPError as e:
           raise RuntimeError(f"MTA feed '{feed_name}' returned HTTP {e.code} for {url}") from e
       except URLError as e:
           raise RuntimeError(f"Could not reach MTA feed '{feed_name}': {e.reason}") from e

       feed = gtfs_realtime_pb2.FeedMessage()
       feed.ParseFromString(data)
       return feed
