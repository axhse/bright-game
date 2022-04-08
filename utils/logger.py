from threading import Lock
from utils.log_types import LogReport, Log, ExceptionLog


class Logger:
    """
    Simple thread-safe logger.
    """

    def __init__(self, allow_printing: bool = False):
        self._logs = []
        self._lock = Lock()
        self._allow_printing = allow_printing

    @property
    def log_count(self):
        return len(self._logs)

    def add_log(self, log: Log):
        with self._lock:
            self._logs.append(log)
        if self._allow_printing:
            print(log)

    def get_report(self, begin_timestamp=0, end_timestamp=1e10, allowed_log_types=None) -> LogReport:
        logs = []
        with self._lock:
            for log in self._logs:
                if begin_timestamp <= log.time <= end_timestamp:
                    logs.append(log)
        if allowed_log_types is not None:
            for i in range(len(logs) - 1, -1, -1):
                if logs[i].type not in allowed_log_types:
                    logs.pop(i)
        return LogReport('\n'.join([str(log) for log in logs]), len(logs))

    def clear(self):
        with self._lock:
            self._logs.clear()


class StaticLogger:
    logger = Logger()

    @staticmethod
    def set_logger(logger: Logger):
        StaticLogger.logger = logger

    @staticmethod
    def exception_logged(func):  # Decorator
        def execute_and_log(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exception:
                StaticLogger.logger.add_log(ExceptionLog(exception, func.__qualname__))
        return execute_and_log
