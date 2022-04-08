import time
from threading import Thread, Lock, Event
from queue import Queue, Empty
from collections import deque

from game_service_bot import GameServiceBot
from utils.async_executor import BlockingLimitedExecutor
from utils.single_access_dict import SingleAccessDict
from multiplayer_provider import MultiplayerProvider, PlayerConnection
from utils.logger import StaticLogger
from call import Call
from player import Player
from game import Game
from game_models.models_enum import GameModels
from game_models.memory import MemoryModel
from game_models.halma import HalmaModel


class GameService:
    def __init__(self, bot: GameServiceBot, max_workers: int):
        self._bot = bot
        self._executor = BlockingLimitedExecutor(max_workers)
        self._multiplayer_provider = MultiplayerProvider()
        self._active_games = SingleAccessDict()
        self._call_groups = dict()    # Dict: [game.uid] = deque of CallInfo
        self._games_to_start = Queue()
        self._pool_calls = Queue()
        self._call_groups_lock = Lock()
        self._counter_lock = Lock()
        self._stop_lock = Lock()
        self._stopped_event = Event()
        self._stopped_event.set()
        self._is_stopping = False

    @property
    def active_game_count(self):
        return self._active_games.count

    def start(self):
        self._stopped_event.wait()
        with self._stop_lock:
            self._stopped_event.clear()
            Thread(target=self._process_forever).start()

    def stop(self):
        with self._stop_lock:
            self._is_stopping = True
            self._stopped_event.wait()

    @StaticLogger.exception_logged
    def handle_connecting_call(self, player: Player, call: Call):
        if call.args['action'] == 'connect':
            if self._multiplayer_provider.try_connect(GameModels.from_key(call.args['game-key']),
                                                      PlayerConnection(player, call)):
                self._bot.update_connection_status(player, call)
        if call.args['action'] == 'disconnect':
            self._multiplayer_provider.try_disconnect(GameModels.from_key(call.args['game-key']),
                                                      PlayerConnection(player, call))
            self._bot.update_connection_status(player, call)

    @StaticLogger.exception_logged
    def add_game_call(self, call: Call):
        with self._call_groups_lock:
            try:
                self._call_groups[call.args['game-id']].append(call)
            except KeyError:
                pass
                # self._bot.delete_call_message(call)

    @StaticLogger.exception_logged
    def _process_forever(self):
        while True:
            if self._is_stopping:
                time.sleep(0.5)    # Catching lost tasks (requested but not started)
                while self._executor.is_busy:
                    time.sleep(0.2)
                keys = self._active_games.stored_keys
                for key in keys:
                    self._executor.execute(self._cancel_acquired_active_game,
                                           self._active_games.acquire_by_key(key), 'bot-stopped')
                while True:
                    try:
                        game = self._games_to_start.get(block=False)
                        self._executor.execute(self._bot.cancel_game, game, 'bot-stopped')
                    except Empty:
                        break
                with self._call_groups_lock:
                    self._call_groups.clear()
                self._stopped_event.set()
                break
            self._executor.execute(self._handle_connections)
            self._executor.execute(self._start_next_game)
            keys = self._active_games.stored_keys
            for key in keys:
                game = self._active_games.acquire_by_key(key, wait=False)
                if game is not None:
                    if game.is_failed:
                        self._cancel_acquired_active_game(game)    # TODO: Add cause
                    else:
                        self._executor.execute(self._process_game, game)

    @StaticLogger.exception_logged
    def _process_game(self, game):
        with self._call_groups_lock:
            calls = self._call_groups[game.uid].copy()
            self._call_groups[game.uid].clear()
        while True:
            try:
                call = calls.popleft()
            except IndexError:
                break
            if game.model_type is GameModels.MEMORY:
                a, b = int(call.args['a']), int(call.args['b'])
                if game.model.try_select(a, b):
                    self._bot.display_game_state(game)
            if game.model_type is GameModels.HALMA:
                if call.args['action'] == 'end-turn':
                    if game.model.try_end_turn(int(call.args['p'])):
                        self._bot.display_game_state(game)
                if call.args['action'] == 'click':
                    player_index, a, b = int(call.args['p']), int(call.args['a']), int(call.args['b'])
                    if game.model.try_click(player_index, a, b):
                        self._bot.display_game_state(game)
            if game.model.is_ended:
                self._remove_active_game(game)
        self._active_games.release_by_key(game.uid)    # Multiple release is possible, but it's OK

    @StaticLogger.exception_logged
    def _handle_connections(self):
        while True:
            connections = self._multiplayer_provider.pop_group(GameModels.MEMORY)
            if connections is None:
                break
            player, call = connections[0].player, connections[0].call
            model = MemoryModel(int(call.args['h']), int(call.args['w']), int(call.args['variety']))
            game = Game(model, [player])
            game.set_message(0, call.message)
            self._add_game(game)
        while True:
            connections = self._multiplayer_provider.pop_group(GameModels.HALMA)
            if connections is None:
                break
            model = HalmaModel()
            game = Game(model, [connection.player for connection in connections])
            for i in range(len(connections)):
                connection = connections[i]
                game.set_message(i, connection.call.message)
            self._add_game(game)

    @StaticLogger.exception_logged
    def _add_game(self, game: Game):
        if self._is_stopping or self._stopped_event.is_set():
            pass    # TODO
        else:
            self._games_to_start.put(game)

    @StaticLogger.exception_logged
    def _start_next_game(self):
        try:
            game = self._games_to_start.get(block=False)
            with self._call_groups_lock:
                self._call_groups[game.uid] = deque()
            self._active_games.add(game.uid, game)
            self._bot.display_game_state(game)
        except Empty:
            pass

    @StaticLogger.exception_logged
    def _cancel_acquired_active_game(self, game, cause=None):
        self._bot.cancel_game(game, cause)
        self._remove_active_game(game)

    @StaticLogger.exception_logged
    def _remove_active_game(self, game, acquired=True):
        if not acquired:
            if self._active_games.acquire_by_key(game.uid) is None:
                return
        with self._call_groups_lock:
            self._call_groups.pop(game.uid)
        self._active_games.release_by_key(game.uid, remove=True)
