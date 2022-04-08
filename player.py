from game_models.models_enum import GameModels


class Player:
    _default_settings = {GameModels.MEMORY.key: {'w': 4, 'h': 3, 'variety': 6}}

    def __init__(self, user_id: int, lang: str = None):
        self.user_id = user_id
        self.lang = 'en' if lang is None else lang
        self.game_settings = Player._default_settings

    def get_dictionary(self) -> dict:
        return self.__dict__

    def set_dictionary(self, dictionary: dict):
        self.__dict__ = dictionary
