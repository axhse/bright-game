from threading import Lock
from collections import deque

from call import Call
from player import Player
from game_models.models_enum import GameModels


class PlayerConnection:
    def __init__(self, player: Player, call: Call):
        self.player = player
        self.call = call

    def equals(self, connection):
        if self.call.args['game-key'] != connection.call.args['game-key']:
            return False
        if GameModels.from_key(connection.call.args['game-key']) in {GameModels.HALMA}:
            return self.call.message.message_id == connection.call.message.message_id
        return self.player.user_id == connection.player.user_id


class MultiplayerProvider:
    def __init__(self):
        self._lock = Lock()
        self._queues = {model: [] for model in GameModels}
        self._groups = {model: deque() for model in GameModels}

    def try_connect(self, game_model: GameModels, connection: PlayerConnection) -> bool:
        with self._lock:
            for i in range(len(self._queues[game_model])):
                if self._queues[game_model][i].equals(connection):
                    return False
            self._queues[game_model].append(connection)
            if len(self._queues[game_model]) >= game_model.value.PLAYER_COUNT:
                self._groups[game_model].append(self._queues[game_model].copy())
                self._queues[game_model].clear()
        return True

    def try_disconnect(self, game_model: GameModels, connection: PlayerConnection) -> bool:
        with self._lock:
            for i in range(len(self._queues[game_model])):
                if self._queues[game_model][i].equals(connection):
                    self._queues[game_model].pop(i)
                    return True
        return False

    def pop_group(self, game_model: GameModels) -> list:
        with self._lock:
            try:
                return self._groups[game_model].popleft()
            except IndexError:
                pass

    def get_all_connections(self) -> set:
        connections = set()
        with self._lock:
            for game_model in self._queues:
                for connection in self._queues[game_model]:
                    connections.add(connection)
            for game_model in self._groups:
                for group in self._groups[game_model]:
                    for connection in group:
                        connections.add(connection)
        return connections

    def clear(self):
        with self._lock:
            self._queues.clear()
            self._groups.clear()
