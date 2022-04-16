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
                log.print()

    def get_report(self, *selection_rules) -> LogReport:
        logs = []
        with self._lock:
            for log in self._logs:
                logs.append(log)
        for i in range(len(logs) - 1, -1, -1):
            for rule in selection_rules:
                if not rule(logs[i]):
                    logs.pop(i)
                    break
        return LogReport(logs)

    def clear(self):
        with self._lock:
            self._logs.clear()

    @staticmethod
    def period_rule(begin_timestamp: float = 0, end_timestamp: float = 1e10):
        def period_is_correct(log: Log):
            return begin_timestamp <= log.creation_time <= end_timestamp
        return period_is_correct

    @staticmethod
    def type_rule(*allowed_log_types: type):
        def type_is_correct(log: Log):
            return type(log) in allowed_log_types
        return type_is_correct


class StaticLogger:
    logger = Logger()

    @staticmethod
    def exception_logged(func):    # Decorator
        def execute_and_log(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exception:
                StaticLogger.logger.add_log(ExceptionLog(exception, func_name=func.__qualname__))
        return execute_and_log
