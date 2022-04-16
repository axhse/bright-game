import time
from threading import Lock


class CachingItem:
    def __init__(self, value):
        self.value = value
        self.last_call = time.time()

    def report_called(self):
        self.last_call = time.time()


class Cache:
    def __init__(self):
        self._data = dict()
        self._data_lock = Lock()

    def __getitem__(self, key):
        with self._data_lock:
            if key in self._data:
                self._data[key].report_called()
                return self._data[key].value
        # TODO: Try load from database
        return None

    def __setitem__(self, key, value):
        with self._data_lock:
            self._data[key] = CachingItem(value)

    def remove(self, key):
        with self._data_lock:
            if key in self._data:
                self._data.pop(key)
