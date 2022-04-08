import enum
from game_models.memory import MemoryModel
from game_models.halma import HalmaModel


class GameModels(enum.Enum):
    MEMORY = MemoryModel
    HALMA = HalmaModel

    @staticmethod
    def from_key(key: str):
        for model in GameModels:
            if model.name == key.upper().replace('-', '_'):
                return model

    @property
    def key(self) -> str:
        return self.name.lower().replace('_', '-')
