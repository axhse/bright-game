from enum import Enum
from telebot.types import CallbackQuery


class CallSources(Enum):
    NAVIGATION = 'navigation'
    UPDATE_PARAM = 'update-param'
    GAME = 'game'
    CONNECTING = 'connecting'
    ADMIN = 'admin'


class Call:
    def __init__(self, call: CallbackQuery):
        self.call_id = call.id
        self.message = call.message
        self.chat_id = call.message.chat.id
        self.date = call.message.date
        source_name, self.arg_str = call.data.split(':')
        self.source = CallSources(source_name)
        self.args = dict()
        for item in self.arg_str.split(','):
            if not item.count('='):
                continue
            key, value = item.split('=')
            self.args[key] = value
