from threading import Lock
from collections import deque


class QueueProvider:    # FIXME: Check if same elements
    def __init__(self, queue_names: set, bounds: dict):
        self._names = queue_names
        self._lock = Lock()
        self._queues = dict()
        self._queue_locks = dict()
        self._bounds = dict()
        self._sizes = dict()
        for name in queue_names:
            self._queues[name] = deque()
            self._queue_locks[name] = Lock()
            self._sizes[name] = 0
        if bounds is not None:
            for key in bounds:
                self._bounds[key] = bounds[key]

    def is_completed(self, queue_name):
        return self._sizes[queue_name] >= self._bounds[queue_name]

    def put(self, queue_name, item):
        with self._lock:
            if queue_name not in self._names:
                raise KeyError
            with self._queue_locks[queue_name]:
                self._queues[queue_name].append(item)
                self._sizes[queue_name] += 1

    def pop_group(self, queue_name):
        with self._lock:
            if queue_name not in self._names:
                raise KeyError
            with self._queue_locks[queue_name]:
                if not self.is_completed(queue_name):
                    return None
                items = []
                for i in range(self._bounds[queue_name]):
                    items.append(self._queues[queue_name].popleft())
                self._sizes[queue_name] -= self._bounds[queue_name]
                return items

    def pop_all(self, queue_name):
        with self._lock:
            if queue_name not in self._names:
                raise KeyError
            with self._queue_locks[queue_name]:
                self._sizes[queue_name] = 0
                items = []
                while True:
                    try:
                        items.append(self._queues[queue_name].popleft())
                    except IndexError:
                        return items
