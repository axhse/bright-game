
class GameModel:
    PLAYER_COUNT = None

    def __init__(self):
        self._is_ended = False
        self._results = []

    @property
    def is_ended(self) -> bool:
        return self._is_ended

    @property
    def results(self) -> list:
        return self._results

    def _end(self, results: list):
        self._is_ended = True
        self._results = results
