import threading
import time

from mta import download_feed


class FeedCache:
    """Refresh MTA feeds in the background and serve cached copies."""

    def __init__(
        self,
        feed_names,
        refresh_interval=30,
        downloader=None,
    ):
        self.feed_names = tuple(sorted(set(feed_names)))
        self.refresh_interval = refresh_interval
        self.downloader = downloader or download_feed

        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

        self._feeds = {}
        self._last_success = {}
        self._last_attempt = {}
        self._errors = {}

    def refresh_once(self):
        """Download each feed and update successful entries."""
        with self._refresh_lock:
            for feed_name in self.feed_names:
                with self._lock:
                    self._last_attempt[feed_name] = time.time()

                try:
                    feed = self.downloader(feed_name)
                except Exception as error:
                    with self._lock:
                        self._errors[feed_name] = str(error)
                    continue

                with self._lock:
                    self._feeds[feed_name] = feed
                    self._last_success[feed_name] = time.time()
                    self._errors.pop(feed_name, None)

    def get_feeds(self):
        """Return a thread-safe snapshot of available feeds."""
        with self._lock:
            return self._feeds.copy()

    def get_status(self):
        """Return refresh timestamps and current errors."""
        with self._lock:
            return {
                "last_success": self._last_success.copy(),
                "last_attempt": self._last_attempt.copy(),
                "errors": self._errors.copy(),
                "available_feeds": sorted(self._feeds),
            }

    def _run(self):
        while not self._stop_event.wait(self.refresh_interval):
            self.refresh_once()

    def start(self):
        """Start the background refresh thread once."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="mta-feed-cache",
                daemon=True,
            )
            self._thread.start()

    def stop(self):
        """Stop the background thread (useful for tests)."""
        self._stop_event.set()

        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=self.refresh_interval + 1)
