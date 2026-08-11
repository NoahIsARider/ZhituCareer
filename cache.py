"""A tiny thread-safe TTL cache.

Used to avoid re-running expensive operations (market scraping, LLM career
analysis) within a short window, which keeps latency and LLM cost low when
many users hit the same resource at once.
"""

import threading
import time


class TTLCache:
    def __init__(self, ttl_seconds=1800, maxsize=128):
        self.ttl = ttl_seconds
        self.maxsize = maxsize
        self._data = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expire_at = item
            if expire_at is not None and time.time() > expire_at:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl_seconds=None):
        ttl = self.ttl if ttl_seconds is None else ttl_seconds
        with self._lock:
            if self.maxsize and len(self._data) >= self.maxsize:
                oldest_key = next(iter(self._data))
                self._data.pop(oldest_key, None)
            expire_at = time.time() + ttl if ttl else None
            self._data[key] = (value, expire_at)

    def clear(self):
        with self._lock:
            self._data.clear()
