import time
from telebot.types import CallbackQuery
from utils.unique_item import UniqueItem


class Player:
    def __init__(self, user_id: int, lang: str = None):
        self.user_id = user_id
        self.lang = 'en' if lang is None else lang
        self.game_settings = {'memory': {'w': 4, 'h': 3, 'variety': 6}}


class Game(UniqueItem):
    def __init__(self, model, players: list, is_online=False, duration_limit: int = None):
        super().__init__(uid_length=32)
        self.model = model
        self.players = players
        self.is_online = is_online
        self.messages = {player: dict() for player in players}    # Dict: [str message_tag] = Message message
        self._is_synced = {player: False for player in players}    # Any callback received
        self._duration_limit = 32_000_000 if duration_limit is None else duration_limit    # Default 1 year
        self._create_time = time.time()

    def sync(self, player, message, message_tag='main'):
        self.messages[player][message_tag] = message
        self._is_synced[player] = True

    @property
    def is_synced(self, player=None) -> bool:
        if player is not None:
            return self._is_synced[player]
        for player in self.players:
            if not self._is_synced[player]:
                return False
        return True

    @property
    def is_failed(self) -> bool:
        return time.time() > self._create_time + self._duration_limit


class BotStatus:
    def __init__(self, is_paused: bool = None, active_game_count: int = None, log_count: int = None):
        self.is_paused = is_paused
        self.active_game_count = active_game_count
        self.log_count = log_count


class CallInfo:
    def __init__(self, call: CallbackQuery):
        self.call_id = call.id
        self.message = call.message
        self.chat_id = call.message.chat.id
        self.message_id = call.message.message_id
        self.date = call.message.date
        arguments = call.data.split(':')
        self.source = arguments[0]
        self.action = arguments[1]
        self.target = arguments[2]
        self.parameter = arguments[3]
        self.args_str = arguments[4] if len(arguments) == 5 else ''
        self.args = dict()
        for pair in self.args_str.split(','):
            if pair != '':
                key, value = pair.split('=')
                self.args[key] = value
