import random


class MemoryCard:
    def __init__(self, value: int):
        self.is_removed = False
        self.is_hidden = True
        self.value = value

    def try_remove(self):
        if self.is_removed:
            return False
        self.is_removed = True
        return True

    def try_show(self):
        if self.is_removed or not self.is_hidden:
            return False
        self.is_hidden = False
        return True

    def try_hide(self):
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

    @staticmethod
    def create_random(rows, columns, variety):
        cards = [(i // 2) % variety for i in range(rows * columns)]
        random.shuffle(cards)
        values = [[cards[i * columns + j] for j in range(columns)] for i in range(rows)]
        return MemoryBoard(values, rows, columns, variety)

    @property
    def size(self) -> int:
        return self.rows * self.columns

    def __getitem__(self, index_pair) -> MemoryCard:
        return self._board[index_pair[0]][index_pair[1]]


class MemoryModel:
    def __init__(self, rows: int, columns: int, variety: int):
        self._board = MemoryBoard.create_random(rows, columns, variety)
        self._board_size = self._board.size
        self._columns = columns
        self._selected = None
        self._cards_to_remove = []
        self._cards_to_hide = []
        self._total_removed = 0
        self._total_moves = 0

    @property
    def is_ended(self) -> bool:
        return self._total_removed == self._board_size

    @property
    def total_removed(self) -> int:
        return self._total_removed

    @property
    def total_moves(self) -> int:
        return self._total_moves

    def try_select(self, row_id, column_id) -> bool:
        for card in self._cards_to_remove:
            card.try_remove()
        self._cards_to_remove.clear()
        for card in self._cards_to_hide:
            card.try_hide()
        self._cards_to_hide.clear()
        card = self._board[row_id, column_id]
        if not card.try_show():
            return False
        self._total_moves += 1
        if self._selected is None:
            self._selected = card
        else:
            if card.value == self._selected.value:
                self._cards_to_remove.extend([card, self._selected])
                self._total_removed += 2
            else:
                self._cards_to_hide.extend([card, self._selected])
            self._selected = None
        return True

    def get_board(self) -> MemoryBoard:
        return self._board
