from threading import Lock
from utils.unique_item import UniqueItem


class UniqueItemLockingStorage:    # TODO: Test
    """
    Thread-safe storage of UniqueItem objects.
    Element receiving is locking.
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
    def stored_ids(self) -> set:
        with self._storage_lock:
            return set(self._items.keys())

    def add(self, value: UniqueItem):
        if not isinstance(value, UniqueItem):
            raise TypeError('Adding value must be an instance of UniqueItem.')
        with self._storage_lock:
            if value.uid not in self._items:
                self._items[value.uid] = value
                self._item_locks[value.uid] = Lock()

    def id_exists(self, uid: str) -> bool:
        with self._storage_lock:
            return uid in self._items

    def acquire_by_id_no_wait(self, uid: str):
        item = None
        with self._storage_lock:
            exists = uid in self._items
            if exists:
                is_acquired = self._item_locks[uid].acquire(blocking=False)
                if is_acquired:
                    item = self._items[uid]
        return item

    def acquire_by_id(self, uid: str):
        with self._storage_lock:
            exists = uid in self._items
            item = self._items[uid] if exists else None
            lock = self._item_locks[uid] if exists else None
        if exists:
            lock.acquire()
            if uid not in self._items:
                item = None
                lock.release()
        return item

    def release_by_id(self, uid: str, remove: bool = False):
        with self._storage_lock:
            if uid in self._items:
                try:
                    self._item_locks[uid].release()
                except RuntimeError:
                    pass
                if remove:
                    self._items.pop(uid)
                    self._item_locks.pop(uid)
