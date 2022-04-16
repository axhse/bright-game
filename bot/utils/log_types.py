import time

TIME_FORMAT = "%H:%M:%S %d %b"


class ConsoleColors:
    DEFAULT = '0'
    RED = '31'
    GREEN = '32'
    YELLOW = '33'
    BLUE = '34'
    LIGHT_RED = '91'
    BRIGHT_YELLOW = '93'
    PINK = '95'


class LogReport:
    def __init__(self, logs: list):
        self.text = '\n'.join([str(log) for log in logs])
        self.count = len(logs)
        self.creation_time = time.time()

    @property
    def creation_time_info(self) -> str:
        return time.strftime(TIME_FORMAT, time.gmtime(self.creation_time))


class Log:
    message_color = ConsoleColors.DEFAULT

    def __init__(self, message: str = None, **kwargs):
        self.message = '' if message is None else message
        self.kwargs = kwargs
        self.creation_time = time.time()
        self.time_format = TIME_FORMAT

    def __str__(self):
        type_name = self.__class__.__name__.lower().replace('log', '')
        text = f'{time.strftime(self.time_format, time.gmtime(self.creation_time))}  -  {type_name}  -  {self.message}'
        if len(self.kwargs):
            text += f"\n{'    '.join(f'{key} = {self.kwargs[key]}' for key in self.kwargs)}"
        return text

    def print(self):
        print(f'\033[{self.message_color}m{str(self)}\033[0m')


class CriticalLog(Log):
    message_color = ConsoleColors.RED

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)


class ExceptionLog(Log):
    message_color = ConsoleColors.YELLOW

    def __init__(self, exception: Exception, func_name: str = None, show_call_stack: bool = False):
        self.exception = exception
        traceback = exception.__traceback__
        while traceback.tb_next is not None:
            traceback = traceback.tb_next
        tb_frame = traceback.tb_frame
        if func_name is None:
            func_name = f'{tb_frame.f_code.co_filename}   {tb_frame.f_code.co_name}'
        message = f'[{type(exception).__name__}]  {str(exception)}   /   {func_name}  {tb_frame.f_lineno}'
        if show_call_stack:
            call_stack_info = ''
            while tb_frame is not None:
                func_name, line_index = tb_frame.f_code.co_name, tb_frame.f_lineno
                if len(call_stack_info):
                    call_stack_info = '  -  ' + call_stack_info
                call_stack_info = f'{func_name} {line_index}{call_stack_info}'
                tb_frame = tb_frame.f_back
            message += f'\n{call_stack_info}'
        super().__init__(message)


class WarningLog(Log):
    message_color = ConsoleColors.PINK

    def __init__(self, message, **kwargs):
        super().__init__(message, **kwargs)


class InfoLog(Log):
    def __init__(self, message: str = None, **kwargs):
        super().__init__(message, **kwargs)


class DebugLog(Log):
    message_color = ConsoleColors.BLUE

    def __init__(self, message: str = None, **kwargs):
        super().__init__(message, **kwargs)
