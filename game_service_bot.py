
from message_schemes.game_schemes import *
from message_schemes.menu_schemes import GameMenu
from utils.logger import StaticLogger
from data import content
from chat_bot import ChatBot
from call import Call
from player import Player
from game import Game
from game_models.models_enum import GameModels


class GameServiceBot:
    def __init__(self, bot: ChatBot):
        self._bot = bot

    @StaticLogger.exception_logged
    def update_connection_status(self, player: Player, call: Call):
        if GameModels.from_key(call.args['game-key']).value.PLAYER_COUNT == 1:
            return
        scheme = None
        if call.args['action'] == 'connect':
            scheme = OpponentSearch(player, call.args)
        if call.args['action'] == 'disconnect':
            scheme = GameMenu(player, call.args)
        message = call.message
        scheme.paste_to_message(message)
        self._bot.update_message(message)

    @StaticLogger.exception_logged
    def display_game_state(self, game: Game, target_player_index: int = None):
        for player_index in range(game.player_count):
            if target_player_index is not None and player_index != target_player_index:
                continue
            scheme = None
            if game.model_type == GameModels.MEMORY:
                scheme = MemoryMain(game)
            if game.model_type == GameModels.HALMA:
                scheme = HalmaMain(game, player_index)
            if game.message_is_set(player_index, 'main'):
                message = game.messages[player_index]['main']
                scheme.paste_to_message(message)
                self._bot.update_message(message)
            else:
                self._bot.send_message(game.players[player_index], scheme)
        if game.is_ended:
            self.end_game(game)

    @StaticLogger.exception_logged
    def delete_call_message(self, call: Call):
        self._bot.delete_message(call.message)

    @StaticLogger.exception_logged
    def end_game(self, game: Game):
        for player_index in range(game.player_count):
            player = game.players[player_index]
            for message in game.messages[player_index].values():
                if game.model_type in Game.DELETE_MESSAGES_WHEN_ENDED:
                    self._bot.delete_message(message)
                else:
                    scheme = MessageScheme(content.get_text(player.lang, 'game', 'ended'))
                    scheme.paste_to_message(message)
                    self._bot.update_message(message)
            scheme = None
            if game.model_type == GameModels.MEMORY:
                scheme = MemoryFinal(game)
            if game.model_type == GameModels.HALMA:
                scheme = HalmaFinal(game, player_index)
            self._bot.send_message(player, scheme)
            self._bot.send_message(player, GameMenu(player, {'game-key': game.model_type.key}))

    @StaticLogger.exception_logged
    def cancel_game(self, game: Game, cause_key: str = None):
        for player_index in range(game.player_count):
            player = game.players[player_index]
            text = content.get_text(player.lang, 'game', 'canceled')
            for message in game.messages[player_index].values():
                if game.model_type in Game.DELETE_MESSAGES_WHEN_ENDED:
                    self._bot.delete_message(message)
                else:
                    scheme = MessageScheme(text['title'])
                    scheme.paste_to_message(message)
                    self._bot.update_message(message)
            title = text['title']
            if cause_key is not None:
                title = content.combine(title, content.subs(text['cause'], cause=text[cause_key]))
            scheme = MessageScheme(title)
            self._bot.send_message(player, scheme)
