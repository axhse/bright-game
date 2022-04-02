from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import game_converters as converters
from utils.stubborn_executor import StubbornExecutor
from utils.logger import Logger
from utils.log_types import ExceptionLog
from data.content import Content
from common_types import CallInfo, Game, Player
from game_models.memory import MemoryModel
from game_models.halma import HalmaModel


class GameServiceBot:
    def __init__(self, bot: TeleBot, logger: Logger):
        self._bot = bot
        self._logger = logger

    def inform_joined(self, player: Player, call: CallInfo):
        try:
            if call.target in ['halma']:
                content = Content.get_content(player)['game']
                text = content['opponent-searching-joined'] if call.target in ['halma'] \
                    else content['opponents-searching-joined']
                self._send_message(player, text)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.inform_joined'))

    def inform_left(self, player: Player):
        try:
            self._send_message(player, Content.get_content(player)['game']['searching-left'])
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.inform_left'))

    def start_game(self, game: Game):
        try:
            if game.is_online:
                for player_id in range(len(game.players)):
                    player = game.players[player_id]
                    content = Content.get_content(player)['game']
                    text = content['opponent-found'] if len(game.players) == 2 else content['opponents-found']
                    markup = InlineKeyboardMarkup()
                    markup.row(InlineKeyboardButton(content['start-game'],
                                                    callback_data=f'game-service:sync:{game.uid}:{player_id}'))
                    self._send_message(player, text, markup)
            else:
                self.display_game_state(game)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.start_game'))

    def display_game_state(self, game: Game, target_player=None):
        try:
            for player in game.players:
                if target_player is not None and player != target_player:
                    continue
                text = converters.game_main_text(game, player)
                markup = converters.game_main_markup(game, player)
                if game.is_synced(player):
                    message = game.messages[player]['main']
                    message.text = text
                    message.reply_markup = markup
                    self._update_message(message)
                elif not game.is_online:
                    self._send_message(player, text, markup)
            if game.model.is_ended:    # FIXME: Don't use duck typing
                self._end_game(game)
                return
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.display_game_state'))

    def cancel_game(self, game, cause=None):
        try:
            for player in game.players:
                for message in game.messages[player].values():
                    self._delete_message(message)
                content = Content.get_content(player)['game']['canceled']
                text = content['title']
                if cause is not None:
                    text = Content.combine(text, Content.subs(content['cause'], cause=content[cause]))
                self._send_message(player, text)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.cancel_game'))

    def delete_call_message(self, call: CallInfo):
        try:
            self._delete_message(call.message)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.delete_call_message'))

    def _end_game(self, game):
        try:
            if type(game.model) is MemoryModel:
                player = game.players[0]
                for message in game.messages[player].values():
                    self._delete_message(message)
                content = Content.get_content(player)['game']
                emoji = Content.get_emoji()['game']
                main_line = Content.subs(content['game-result'], game=Content.combine(emoji['memory']['icon'],
                                         content['memory']['title']), result=content['win'])
                text = Content.combine(main_line, converters.game_difficulty(game, custom_detailed=True),
                                       converters.game_moves_made(game))
                self._send_message(player, text)
            if type(game.model) is HalmaModel:
                for player_id in range(len(game.players)):
                    player = game.players[player_id]
                    content = Content.get_content(player)['game']
                    for message in game.messages[player].values():
                        message.text = content['game-ended']
                        self._update_message(message)
                    emoji = Content.get_emoji()['game']
                    result = content['win'] if game.model.winner == player_id else content['defeat']
                    main_line = Content.subs(content['game-result'], game=Content.combine(emoji['halma']['icon'],
                                             content['halma']['title']), result=result)
                    text = Content.combine(main_line, converters.game_moves_made(game, player))
                    self._send_message(player, text)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.end_game'))

    def _send_message(self, player: Player, text: str, markup: InlineKeyboardMarkup = None):
        try:
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.send_message'))

    def _delete_message(self, message: Message):
        try:
            self._bot.delete_message(message.chat.id, message.message_id)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.delete_message'))

    def _update_message(self, message: Message):
        try:
            self._bot.edit_message_text(message.text, message.chat.id,
                                        message.message_id, reply_markup=message.reply_markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.update_message'))
