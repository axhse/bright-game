import json


class GameData:
    _DATA: dict = None
    _is_loaded = False

    @staticmethod
    def load(game_path: str):
        with open(game_path, 'r') as f:
            GameData._DATA = json.loads(f.read())
        GameData._is_loaded = True

    @staticmethod
    def get():
        if not GameData._is_loaded:
            raise RuntimeError('Content is not loaded.')
        return GameData._DATA
