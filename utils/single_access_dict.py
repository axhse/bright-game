from threading import Lock


class SingleAccessDict:
    """
    Thread-safe dictionary-based storage.
    Element receiving is blocking.
    """

    def __init__(self):
        self._storage_lock = Lock()
        self._item_locks = dict()
        self._items = dict()

    @property
    def count(self) -> int:
        with self._storage_lock:
            return len(self._items)

    @property
    def stored_keys(self) -> set:
        with self._storage_lock:
            return set(self._items.keys())

    def add(self, key: str, value):
        with self._storage_lock:
            if key not in self._items:
                self._items[value.uid] = value
                self._item_locks[value.uid] = Lock()

    def contains(self, key: str) -> bool:    # TODO: Remove
        with self._storage_lock:
            return key in self._items

    def acquire_by_key(self, key: str, wait: bool = True):
        item, lock = None, None
        with self._storage_lock:
            if key in self._items:
                if wait:
                    lock = self._item_locks[key]
                else:
                    if self._item_locks[key].acquire(blocking=False):
                        item = self._items[key]
        if wait and lock is not None:
            lock.acquire()
            item = self._items[key]
        return item

    def release_by_key(self, key: str, remove: bool = False):
        with self._storage_lock:
            if key in self._items:
                try:
                    self._item_locks[key].release()
                except RuntimeError:
                    pass
                if remove:
                    self._items.pop(key)
                    self._item_locks.pop(key)
