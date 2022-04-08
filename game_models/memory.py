import random
from game_models.game_model import GameModel
from game_models.game_result import MemoryResult


class MemoryCard:
    def __init__(self, value: int):
        self.is_removed = False
        self.is_hidden = True
        self.value = value

    def try_remove(self) -> bool:
        if self.is_removed:
            return False
        self.is_removed = True
        return True

    def try_show(self) -> bool:
        if self.is_removed or not self.is_hidden:
            return False
        self.is_hidden = False
        return True

    def try_hide(self) -> bool:
        if self.is_removed or self.is_hidden:
            return False
        self.is_hidden = True
        return True


class MemoryBoard:
    def __init__(self, values, rows=None, columns=None, variety=None):
        self._board = [[MemoryCard(v) for v in row] for row in values]
        self.rows = rows
        self.columns = columns
        self.variety = variety

    def __getitem__(self, index_pair) -> MemoryCard:
        return self._board[index_pair[0]][index_pair[1]]

    @property
    def size(self) -> int:
        return self.rows * self.columns

    @staticmethod
    def create_random(rows: int, columns: int, variety: int):
        cards = [(i // 2) % variety for i in range(rows * columns)]
        random.shuffle(cards)
        values = [[cards[i * columns + j] for j in range(columns)] for i in range(rows)]
        return MemoryBoard(values, rows, columns, variety)


class MemoryModel(GameModel):
    PLAYER_COUNT = 1

    def __init__(self, rows: int, columns: int, variety: int):
        super().__init__()
        self._board = MemoryBoard.create_random(rows, columns, variety)
        self._selected = None
        self._cards_to_remove = []
        self._cards_to_hide = []
        self._move_count = 0
        self._removed_count = 0

    @property
    def move_count(self) -> int:
        return self._move_count

    @property
    def removed_count(self) -> int:
        return self._removed_count

    def try_select(self, row_id: int, column_id: int) -> bool:
        for card in self._cards_to_remove:
            card.try_remove()
        self._cards_to_remove.clear()
        for card in self._cards_to_hide:
            card.try_hide()
        self._cards_to_hide.clear()
        card = self._board[row_id, column_id]
        if not card.try_show():
            return False
        self._move_count += 1
        if self._selected is None:
            self._selected = card
        else:
            if card.value == self._selected.value:
                self._cards_to_remove.extend([card, self._selected])
                self._removed_count += 2
            else:
                self._cards_to_hide.extend([card, self._selected])
            self._selected = None
        if self._removed_count == self._board.size:
            self._end(self._get_results())
        return True

    def get_board(self) -> MemoryBoard:
        return self._board

    def _get_results(self) -> list:
        return [MemoryResult(self.move_count)]
