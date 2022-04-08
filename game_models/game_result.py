import enum


class ResultStatus(enum.Enum):
    WIN = 'win'
    DEFEAT = 'defeat'
    DRAW = 'draw'
    NAMELESS = 'nameless'
    NONE = None


class GameResult:
    def __init__(self, status: ResultStatus = ResultStatus.NONE):
        self.status = status
        self.move_count = None


class MemoryResult(GameResult):
    def __init__(self, move_count: int):
        super().__init__(ResultStatus.NAMELESS)
        self.move_count = move_count


class HalmaResult(GameResult):
    def __init__(self, status: ResultStatus, move_count: int):    # status: win, defeat
        super().__init__(status)
        self.move_count = move_count
