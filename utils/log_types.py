import time


class LogReport:
    def __init__(self, text: str, count: int = None):
        self.text = text
        self.count = count
        self.creation_time = time.time()

    @property
    def creation_time_text_info(self) -> str:
        return time.strftime("%H:%M:%S %d %b", time.gmtime(self.creation_time))


class Log:
    type = 'no type'

    def __init__(self, value=None):
        self.time = time.time()
        self.value = value

    def __str__(self):
        return f'{time.strftime("%H:%M:%S %d %b", time.gmtime(self.time))}  -  {self.type}  -  {self.value}'


class ExceptionLog(Log):
    type = 'exception'

    def __init__(self, exception: Exception, position_tag=None):
        super().__init__(f'[{type(exception).__name__}]  {str(exception)}')
        self.position = position_tag

    def __str__(self):
        return f'{super().__str__()}  /  {self.position}'


class UnknownTypeLog(Log):
    type = 'unknown type'

    def __init__(self, value):
        super().__init__(value)
