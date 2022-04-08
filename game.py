import time
import random
from game_models.game_model import GameModel
from game_models.models_enum import GameModels


class Game:
    DELETE_MESSAGES_WHEN_ENDED = {GameModels.MEMORY}

    def __init__(self, model: GameModel, players: list, duration_limit: int = None):
        self.model = model
        self.players = players
        self.messages = [dict() for _ in range(self.player_count)]    # Dict: [str message_tag] = Message message
        self.duration_limit = 32_000_000 if duration_limit is None else duration_limit    # Default 1 year
        self._creation_time = time.time()
        self._uid = Game._random_uid()

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def model_type(self) -> GameModels:
        return GameModels(type(self.model))

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def is_failed(self) -> bool:
        return time.time() > self._creation_time + self.duration_limit

    @property
    def is_ended(self) -> bool:
        return self.model.is_ended

    @property
    def results(self) -> list:
        return self.model.results

    def set_message(self, player_index, message, message_tag='main'):
        self.messages[player_index][message_tag] = message

    def message_is_set(self, player_index, message_tag='main') -> bool:
        return message_tag in self.messages[player_index]

    @staticmethod
    def _random_uid() -> str:
        symbols = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join([random.choice(symbols) for _ in range(25)])
