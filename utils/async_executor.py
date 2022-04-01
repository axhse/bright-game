from threading import Semaphore, Lock, Event
from concurrent.futures import ThreadPoolExecutor


class IgnoringLimitedExecutor:
    """
    Performs asynchronously up to [max_workers] actions at the same time.
    Ignores new performing requests when paused or overloaded.
    """

    def __init__(self, max_workers: int):
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers)
        self._counter_lock = Lock()
        self._active_task_count = 0
        self._is_paused = False

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def active_task_count(self) -> int:
        return self._active_task_count

    @property
    def is_busy(self) -> bool:
        return self._active_task_count > 0

    @property
    def is_overloaded(self) -> bool:
        return self._active_task_count == self._max_workers

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def perform(self, target, *args):
        if self._is_paused:
            return
        if self._try_report_start():
            def action(): return target(*args)
            self._executor.submit(self._perform_and_report, action)

    def _perform_and_report(self, action):
        action()
        self._report_end()

    def _try_report_start(self):
        result = False
        with self._counter_lock:
            if self._active_task_count < self._max_workers:
                self._active_task_count += 1
                result = True
        return result

    def _report_end(self):
        with self._counter_lock:
            self._active_task_count -= 1


class BlockingLimitedExecutor:
    """
    Performs asynchronously up to [max_workers] actions at the same time.
    Blocks new performing requests when paused or overloaded.
    """

    def __init__(self, max_workers: int):
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers)
        self._semaphore = Semaphore(max_workers)
        self._resume_event = Event()
        self._counter_lock = Lock()
        self._active_task_count = 0
        self.resume()

    @property
    def is_paused(self) -> bool:
        return not self._resume_event.is_set()

    @property
    def active_task_count(self) -> int:
        return self._active_task_count

    @property
    def is_busy(self) -> bool:
        return self._active_task_count > 0

    @property
    def is_overloaded(self) -> bool:
        return self._active_task_count == self._max_workers

    def pause(self):
        self._resume_event.clear()

    def resume(self):
        self._resume_event.set()

    def perform(self, target, *args):
        self._resume_event.wait()
        self._report_start()
        def action(): return target(*args)
        self._executor.submit(self._perform_and_report, action)

    def _perform_and_report(self, action):
        action()
        self._report_end()

    def _report_start(self):
        self._semaphore.acquire()
        with self._counter_lock:
            self._active_task_count += 1

    def _report_end(self):
        with self._counter_lock:
            self._active_task_count -= 1
        self._semaphore.release()
