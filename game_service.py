import time
from threading import Thread, Lock, Event
from queue import Queue, Empty
from collections import deque

from game_service_bot import GameServiceBot
from utils.async_executor import BlockingLimitedExecutor
from utils.unique_item_storage import UniqueItemLockingStorage
from utils.logger import Logger
from utils.log_types import ExceptionLog
from common_types import Game, CallInfo
from game_models.memory import MemoryModel


class GameService:
    def __init__(self, bot: GameServiceBot, max_workers: int, logger: Logger):
        self._bot = bot
        self._logger = logger
        self._executor = BlockingLimitedExecutor(max_workers)
        self._call_groups_lock = Lock()
        self._counter_lock = Lock()
        self._stop_lock = Lock()
        self._stopped_event = Event()
        self._stopped_event.set()
        self._active_games = UniqueItemLockingStorage()
        self._call_groups = dict()    # Dict: [game.uid] = deque of CallInfo
        self._games_to_start = Queue()
        self._is_stopping = False

    @property
    def active_game_count(self):    # TODO: Test
        return self._active_games.count

    def start(self):    # TODO: Test
        self._stopped_event.wait()
        with self._stop_lock:
            self._stopped_event.clear()
            Thread(target=self._process_forever).start()

    def stop(self):    # TODO: Test
        with self._stop_lock:
            self._is_stopping = True
            self._stopped_event.wait()

    def create_game(self, players, call: CallInfo):    # FIXME: Move to online-service
        if call.parameter == 'memory':
            model = MemoryModel(int(call.args['h']), int(call.args['w']), int(call.args['variety']))
            game = Game(model, players)
            self.add_game(game)

    def add_game(self, game: Game):    # TODO: Cancel if stopped ?
        try:
            self._games_to_start.put(game)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameService.add_game'))

    def add_call(self, call: CallInfo):    # TODO: Test
        try:
            with self._call_groups_lock:
                is_relevant = call.target in self._call_groups    # call.target = game.uid
                if is_relevant:
                    self._call_groups[call.target].append(call)
            if not is_relevant:
                self._bot.delete_call_message(call)    # FIXME: Might be info message ?
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameService.add_call'))

    def _process_forever(self):    # TODO: Test
        try:
            while True:
                if self._is_stopping:
                    time.sleep(0.5)    # Catching lost tasks (requested but not started)
                    while self._executor.is_busy:
                        time.sleep(0.2)
                    ids = self._active_games.stored_ids
                    for game_id in ids:
                        self._executor.perform(self._cancel_acquired_active_game,
                                               self._active_games.acquire_by_id(game_id), 'bot-stopped')
                    while True:
                        try:
                            game = self._games_to_start.get(block=False)
                            self._executor.perform(self._bot.cancel_game, game, 'bot-stopped')
                        except Empty:
                            break
                    with self._call_groups_lock:
                        self._call_groups.clear()
                    self._stopped_event.set()
                    break
                self._executor.perform(self._start_next_game)
                ids = self._active_games.stored_ids
                for game_id in ids:
                    game = self._active_games.acquire_by_id_no_wait(game_id)
                    if game is not None:
                        if game.is_failed:
                            self._cancel_acquired_active_game(game)    # TODO: Add cause
                        else:
                            self._executor.perform(self._process_game, game)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameService.process_forever'))

    def _process_game(self, game):    # TODO : Test
        try:
            with self._call_groups_lock:
                calls = self._call_groups[game.uid].copy()
                self._call_groups[game.uid].clear()
            while True:
                try:
                    call = calls.popleft()
                except IndexError:
                    break
                if type(game.model) is MemoryModel:
                    if not game.is_synced:
                        game.sync(game.players[0], call.message)
                    a, b = map(int, call.parameter.split(','))
                    if game.model.try_select(a, b):
                        self._bot.display_game_state(game)
                    if game.model.is_ended:
                        self._remove_active_game(game)
            self._active_games.release_by_id(game.uid)    # Multiple release is possible, but it's OK
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameService.process_game'))
    
    def _start_next_game(self):    # TODO: Test
        try:
            game = self._games_to_start.get(block=False)
            with self._call_groups_lock:
                self._call_groups[game.uid] = deque()
            self._active_games.add(game)
            self._bot.start_game(game)
        except Empty:
            pass
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameService.start_next_game'))

    def _cancel_acquired_active_game(self, game, cause=None):    # TODO: Test
        self._bot.cancel_game(game, cause)
        self._remove_active_game(game)

    def _remove_active_game(self, game, acquired=True):    # TODO: Test
        if not acquired:
            if self._active_games.acquire_by_id(game.uid) is None:
                return
        with self._call_groups_lock:
            self._call_groups.pop(game.uid)
        self._active_games.release_by_id(game.uid, remove=True)
