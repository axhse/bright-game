from game_models.game_model import GameModel
from game_models.game_result import HalmaResult, ResultStatus


class HalmaSquare:
    def __init__(self, color: int = None):
        self.is_selected = False
        self.color = color    # 0, 1

    @property
    def is_empty(self) -> bool:
        return self.color is None

    def try_select(self, player_index: int) -> bool:
        if player_index == self.color and not self.is_selected:
            self.is_selected = True
            return True
        return False

    def try_deselect(self, player_index: int) -> bool:
        if player_index == self.color and self.is_selected:
            self.is_selected = False
            return True
        return False


class HalmaBoard:
    def __init__(self):
        self._board = [[HalmaSquare() for _ in range(8)] for _ in range(8)]
        for i in range(8):
            for j in range(8):
                if i + j < 4:
                    self[i, j].color = 1
                if i + j > 10:
                    self[i, j].color = 0

    def __getitem__(self, index_pair) -> HalmaSquare:
        return self._board[index_pair[0]][index_pair[1]]

    def __setitem__(self, index_pair, value: HalmaSquare):
        self._board[index_pair[0]][index_pair[1]] = value

    def reversed(self):
        board = HalmaBoard()
        for i in range(8):
            for j in range(8):
                board[i, j] = HalmaSquare()
                board[i, j].is_selected = self[7 - i, 7 - j].is_selected
                if not self[7 - i, 7 - j].is_empty:
                    board[i, j].color = self[7 - i, 7 - j].color ^ 1
        return board


class HalmaModel(GameModel):
    PLAYER_COUNT = 2

    def __init__(self):
        super().__init__()
        self._board = HalmaBoard()
        self._turn = 0    # 0, 1
        self._selected = None
        self._visited_squares = set()
        self._move_count = 0

    @property
    def move_count(self) -> int:
        return self._move_count

    @property
    def turn(self) -> int:
        return self._turn

    def can_end_turn(self, player_index: int) -> bool:
        return player_index == self.turn and self._piece_moved

    def try_end_turn(self, player_index: int) -> bool:
        if self.can_end_turn(player_index):
            self._change_turn()
            return True
        return False

    def try_click(self, player_index: int, row_id: int, column_id: int) -> bool:
        if self.is_ended or player_index != self._turn:
            return False
        if self._piece_moved:
            return self._try_move_piece(row_id, column_id)
        else:
            if self._try_move_piece(row_id, column_id):
                return True
            changed = False
            if self._selected is not None:
                if (row_id, column_id) == self._selected:
                    return False
                changed = True
                self._board[self._selected].try_deselect(player_index)
            if self._board[row_id, column_id].try_select(player_index):
                self._selected = (row_id, column_id)
                self._visited_squares.clear()
                self._visited_squares.add(self._selected)
                changed = True
            return changed

    def get_board(self, player_index: int) -> HalmaBoard:
        if player_index == 0:
            return self._board
        else:
            return self._board.reversed()

    @property
    def _piece_moved(self) -> bool:
        return len(self._visited_squares) > 1

    def _can_move_to(self, new_i: int, new_j: int) -> bool:
        if self._selected is None:
            return False
        i, j = self._selected
        if i == new_i and j == new_j:
            return False
        if (new_i, new_j) in self._visited_squares:
            return False
        if new_i - i in [-1, 0, 1] and new_j - j in [-1, 0, 1]:
            return self._board[new_i, new_j].is_empty and not self._piece_moved
        if new_i - i in [-2, 0, 2] and new_j - j in [-2, 0, 2]:
            if self._board[new_i, new_j].is_empty and not self._board[(new_i + i) // 2, (new_j + j) // 2].is_empty:
                return True
        return False

    def _try_move_piece(self, new_i: int, new_j: int) -> bool:
        if not self._can_move_to(new_i, new_j):
            return False
        i, j = self._selected
        self._board[new_i, new_j] = self._board[i, j]
        self._board[i, j] = HalmaSquare()
        self._visited_squares.add((new_i, new_j))
        self._selected = (new_i, new_j)
        can_move = False
        if new_i - i in [-2, 0, 2] and new_j - j in [-2, 0, 2]:
            for a in range(-2, 4, 2):
                for b in range(-2, 4, 2):
                    if (not a == b == 0) and 0 <= new_i + a <= 7 and 0 <= new_j + b <= 7:
                        if self._can_move_to(new_i + a, new_j + b):
                            can_move = True
        if not can_move:
            self._change_turn()
        return True

    def _change_turn(self):
        if self._turn == 1:
            self._move_count += 1
        self._check_if_is_ended()
        self._board[self._selected].is_selected = False
        self._selected = None
        self._visited_squares.clear()
        self._turn ^= 1

    def _check_if_is_ended(self):
        first_won, second_won = True, True
        for i in range(8):
            for j in range(8):
                if i + j < 4 and self._board[i, j].color != 0:
                    first_won = False
                if i + j > 10 and self._board[i, j].color != 1:
                    second_won = False
        if first_won:
            self._end(self._get_results(winner_id=0))
        if second_won:
            self._end(self._get_results(winner_id=1))

    def _get_results(self, winner_id: int) -> list:
        results = []
        for player_index in [0, 1]:
            status = ResultStatus.WIN if player_index == winner_id else ResultStatus.DEFEAT
            results.append(HalmaResult(status=status, move_count=self._move_count))
        return results
