import re
from io import StringIO
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import menu_converters as converters
from utils.logger import Logger, LogReport
from utils.log_types import ExceptionLog
from data import content
from common_types import Player, CallInfo, BotStatus


class ChatBot:
    def __init__(self, bot: TeleBot, logger: Logger):
        self._bot = bot
        self._logger = logger

    @staticmethod
    def get_command(message: Message):
        return None if re.search(r'^/[a-z]{1,20}$', message.text) is None else message.text[1:]

    def display_main_menu(self, player: Player):
        try:
            messages, emoji = content.get_local(player.lang), content.emoji
            markup = InlineKeyboardMarkup()
            for game_key in ['memory', 'halma']:
                text = content.combine(emoji['game'][game_key]['icon'], messages['game'][game_key]['title'])
                markup.row(InlineKeyboardButton(text, callback_data=f'main-menu:navigate:game-menu:{game_key}'))
            # text = content.combine(emoji['menu']['settings'], messages['menu']['settings'])
            # markup.row(InlineKeyboardButton(text, callback_data='main-menu:navigate:settings:'))
            text = content.shift(messages['menu']['main-menu'])
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_main_menu'))

    def display_game_menu(self, player: Player, call: CallInfo):
        try:
            game_key = call.parameter
            messages, emoji = content.get_local(player.lang)['menu'], content.emoji
            markup = InlineKeyboardMarkup(row_width=2)
            if game_key == 'memory':
                if 'w' in call.args and 'h' in call.args and 'variety' in call.args:
                    args = f"w={call.args['w']},h={call.args['h']},variety={call.args['variety']}"
                else:
                    default = player.game_settings['memory']
                    args = f"w={default['w']},h={default['h']},variety={default['variety']}"
                text = content.combine(emoji['game'][game_key]['icon'], messages['game-service'])
                buttons = [InlineKeyboardButton(text, callback_data=f'game-pool:join:{game_key}::{args}')]
                text = content.combine(emoji['menu']['difficulty'], messages['difficulty'])
                buttons.append(InlineKeyboardButton(text, callback_data=f'game-menu:navigate:difficulty:{game_key}'))
                markup.row(*buttons)
            if game_key == 'halma':
                text = content.combine(emoji['game'][game_key]['icon'], messages['game-service'])
                markup.row(InlineKeyboardButton(text, callback_data=f'game-pool:join:{game_key}:'))
            rules_text = content.combine(emoji['menu']['rules'], messages['rules'])
            navigate_main_text = content.combine(emoji['menu']['navigate-back'], messages['main-menu'])
            markup.row(InlineKeyboardButton(rules_text, callback_data=f'game-menu:navigate:rules:{game_key}'),
                       InlineKeyboardButton(navigate_main_text, callback_data='game-menu:navigate:main-menu:'))
            text = ''
            if game_key == 'memory':
                text = converters.difficulty_info_from_call(player, call, custom_detailed=True)
            text = content.shift(text)
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_game_menu'))

    def display_difficulty(self, player: Player, call: CallInfo):    # TODO
        try:
            if call.parameter == 'memory':
                text = content.shift(content.get_local(player.lang)['game']['memory']['difficulty']['menu-title'])
                markup = converters.difficulty_markup(player, call)
                self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_difficulty'))

    def display_rules(self, player: Player, call: CallInfo):    # TODO
        try:
            self._bot.send_message(player.user_id, content.get_local(player.lang)['game'][call.parameter]['rules'])
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_rules'))

    def display_status(self, player: Player, status: BotStatus):
        try:
            messages, emoji = content.get_local(player.lang)['admin'], content.emoji['info']
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton(messages['pause'], callback_data='admin-menu:pause-bot::'),
                       InlineKeyboardButton(messages['resume'], callback_data='admin-menu:resume-bot::'))
            markup.row(InlineKeyboardButton(messages['stop'], callback_data='admin-menu:stop-server::'))
            markup.row(InlineKeyboardButton(messages['logs'], callback_data='admin-menu:get-logs::'))
            tag = 'bot-paused' if status.is_paused else 'bot-working'
            text = content.combine(emoji[tag], messages[tag])
            if status.active_game_count is not None:
                text = content.combine(text, content.subs(messages['active-games'], count=status.active_game_count))
            if status.log_count is not None:
                text = content.combine(text, content.subs(messages['total-log-count'], count=status.log_count))
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_status'))

    def display_logs(self, player: Player, log_report: LogReport):
        try:
            messages = content.get_local(player.lang)['admin']
            if log_report.count is not None:
                self._bot.send_message(player.user_id, content.subs(messages['log-count'], count=log_report.count))
            if len(log_report.text):
                file = StringIO()
                file.name = 'logs.txt'
                file.write(log_report.text)
                file.seek(0)
                self._bot.send_document(player.user_id, file)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_logs'))

    def inform_bot_is_paused(self, player: Player):
        self._bot.send_message(player.user_id, content.get_local(player.lang)['info']['paused'])

    def inform_server_is_stopping(self, player: Player):
        self._bot.send_message(player.user_id, content.get_local(player.lang)['admin']['server-stopping'])

    def inform_server_is_stopped(self, player: Player):
        self._bot.send_message(player.user_id, content.get_local(player.lang)['admin']['server-stopped'])
