import threading
import time

class WindowCounter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits = 0
        self._window_start = time.monotonic()

    def allow(self, limit=120, burst=20) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            if now - self._window_start >= 60:
                self._window_start = now
                self._hits = 0
            if self._hits >= limit:
                return False, self._hits
            extra = max(0, self._hits - (limit - burst))
            if extra > 0:
                return False, self._hits
            self._hits += 1
            return True, self._hits

_window = WindowCounter()

def check(limit=120, burst=20) -> tuple[bool, int]:
    return _window.allow(limit=limit, burst=burst)
