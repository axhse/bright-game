import time
from utils.logger import Logger
from utils.log_types import ExceptionLog


class StubbornExecutor:    # TODO: Test
    """
    Retries action calling when it breaks by exception.
    """

    @staticmethod
    def try_perform(action, delay=0, attempts: int = None, logger: Logger = None):
        while attempts is None or attempts > 0:
            try:
                action()
                return True
            except Exception as exception:
                if logger is not None:
                    logger.add_log(ExceptionLog(exception, 'StubbornExecutor'))
                if attempts is not None:
                    attempts -= 1
                time.sleep(delay)
        return False
