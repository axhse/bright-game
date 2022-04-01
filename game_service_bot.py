from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import game_converters as converters
from utils.stubborn_executor import StubbornExecutor
from utils.logger import Logger
from utils.log_types import ExceptionLog
from data.content import Content
from common_types import Game, CallInfo
from game_models.memory import MemoryModel


class GameServiceBot:
    def __init__(self, bot: TeleBot, logger: Logger):
        self._bot = bot
        self._logger = logger

    def start_game(self, game: Game):
        try:
            if game.is_online:
                for p in range(len(game.players)):
                    player = game.players[p]
                    content = Content.get_content(player)['game']
                    text = content['opponent-found'] if len(game.players) == 2 else content['opponents-found']
                    markup = InlineKeyboardMarkup()
                    markup.row(InlineKeyboardButton(content['start-game'],
                                                    callback_data=f'game-service:sync:{game.uid}:{p}'))
                    self._send_message(game.players[0], text, markup)
            else:
                self.display_game_state(game, is_synced=False)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.start_game'))

    def display_game_state(self, game: Game, is_synced=True):
        try:
            if game.is_online:
                pass
            else:
                player = game.players[0]
                if type(game.model) is MemoryModel:
                    if game.model.is_ended:
                        self._end_game(game)
                        return
                    text = converters.game_main_text(game)
                    markup = converters.game_main_markup(game)
                    if is_synced:
                        message = game.messages[player]['main']
                        self._edit_message(message, text, markup)
                    else:
                        self._send_message(player, text, markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.display_game_state'))

    def cancel_game(self, game, cause=None):    # TODO: Test
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

    def delete_call_message(self, call: CallInfo):    # TODO: Test
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
                                         content['memory']['title']), result=Content.combine(content['win']))
                text = Content.combine(main_line, converters.game_difficulty(game, detailed=True),
                                       converters.game_moves_made(game))
                self._send_message(player, text)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.end_game'))

    def _send_message(self, player, text, markup=None):
        try:
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.send_message'))

    def _delete_message(self, message: Message):
        try:
            self._bot.delete_message(message.chat.id, message.message_id)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.delete_message'))

    def _edit_message(self, message: Message, new_text: str = None, new_markup: InlineKeyboardMarkup = None,
                      delete_markup: bool = False):
        try:
            if new_text is None:
                new_text = message.text
            if new_markup is None and not delete_markup:
                new_markup = message.reply_markup
            self._bot.edit_message_text(new_text, message.chat.id, message.message_id, reply_markup=new_markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'GameServiceBot.update_message'))
