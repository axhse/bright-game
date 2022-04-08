import time


class LogReport:
    def __init__(self, text: str, count: int):
        self.text = text
        self.count = count
        self.creation_time = time.time()

    @property
    def creation_time_info(self) -> str:
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

    def __init__(self, exception: Exception, origin_tag=None):
        super().__init__(f'[{type(exception).__name__}]  {str(exception)}')
        self.origin = origin_tag

    def __str__(self):
        return f'{super().__str__()}  /  {self.origin}'
