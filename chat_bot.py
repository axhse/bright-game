import re
from io import StringIO
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import menu_converters as converters
from utils.logger import Logger, LogReport
from utils.log_types import ExceptionLog
from data.content import Content
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
            content, emoji = Content.get_content(player), Content.get_emoji()
            markup = InlineKeyboardMarkup()
            for game in ['memory']:
                text = Content.combine(emoji['game'][game]['icon'], content['game'][game]['title'])
                markup.row(InlineKeyboardButton(text, callback_data=f'main-menu:navigate:game-menu:{game}'))
            # text = Content.combine(emoji['menu']['settings'], content['menu']['settings'])
            # markup.row(InlineKeyboardButton(text, callback_data='main-menu:navigate:settings:'))
            text = Content.shift(content['menu']['main-menu'])
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_main_menu'))

    def display_game_menu(self, player: Player, call: CallInfo):
        try:
            game = call.parameter
            content, emoji = Content.get_content(player)['menu'], Content.get_emoji()
            markup = InlineKeyboardMarkup()
            if game == 'memory':
                if 'w' in call.args and 'h' in call.args and 'variety' in call.args:
                    args = f"w={call.args['w']},h={call.args['h']},variety={call.args['variety']}"
                else:
                    default = player.game_settings['memory']
                    args = f"w={default['w']},h={default['h']},variety={default['variety']}"
                text = Content.combine(emoji['game'][game]['icon'], content['game-service'])
                buttons = [InlineKeyboardButton(text, callback_data=f'game-menu:navigate:game-service:{game}:{args}')]
                text = Content.combine(emoji['menu']['difficulty'], content['difficulty'])
                buttons.append(InlineKeyboardButton(text, callback_data=f'game-menu:navigate:difficulty:{game}'))
                markup.row(*buttons)
            rules_text = Content.combine(emoji['menu']['rules'], content['rules'])
            navigate_main_text = Content.combine(emoji['menu']['navigate-back'], content['main-menu'])
            markup.row(InlineKeyboardButton(rules_text, callback_data=f'game-menu:navigate:rules:{game}'),
                       InlineKeyboardButton(navigate_main_text, callback_data='game-menu:navigate:main-menu:'))
            text = ''
            if game == 'memory':
                text = converters.difficulty_info_from_call(player, call)
            text = Content.shift(text)
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_game_menu'))

    def display_difficulty(self, player: Player, call: CallInfo):    # TODO
        try:
            if call.parameter == 'memory':
                text = Content.shift(Content.get_content(player)['game']['memory']['difficulty']['menu-title'])
                markup = converters.difficulty_markup(player, call)
                self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_difficulty'))

    def display_rules(self, player: Player, call: CallInfo):    # TODO
        try:
            if call.parameter == 'memory':
                self._bot.send_message(player.user_id, Content.get_content(player)['game']['memory']['rules'])
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_rules'))

    def display_status(self, player: Player, status: BotStatus):
        try:
            content, emoji = Content.get_content(player)['admin'], Content.get_emoji()['info']
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton(content['pause'], callback_data='admin-menu:pause-bot::'),
                       InlineKeyboardButton(content['resume'], callback_data='admin-menu:resume-bot::'))
            markup.row(InlineKeyboardButton(content['stop'], callback_data='admin-menu:stop-server::'))
            markup.row(InlineKeyboardButton(content['logs'], callback_data='admin-menu:get-logs::'))
            tag = 'bot-paused' if status.is_paused else 'bot-working'
            text = Content.combine(emoji[tag], content[tag])
            if status.active_game_count is not None:
                text = Content.combine(text, Content.subs(content['active-games'], count=status.active_game_count))
            if status.log_count is not None:
                text = Content.combine(text, Content.subs(content['total-log-count'], count=status.log_count))
            self._bot.send_message(player.user_id, text, reply_markup=markup)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_status'))

    def display_logs(self, player: Player, log_report: LogReport):
        try:
            content = Content.get_content(player)['admin']
            if log_report.count is not None:
                self._bot.send_message(player.user_id, Content.subs(content['log-count'], count=log_report.count))
            if len(log_report.text):
                file = StringIO()
                file.name = 'logs.txt'
                file.write(log_report.text)
                file.seek(0)
                self._bot.send_document(player.user_id, file)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'ChatBot.display_logs'))

    def inform_bot_is_paused(self, player: Player):
        self._bot.send_message(player.user_id, Content.get_content(player)['info']['paused'])

    def inform_server_is_stopping(self, player: Player):
        self._bot.send_message(player.user_id, Content.get_content(player)['admin']['server-stopping'])

    def inform_server_is_stopped(self, player: Player):
        self._bot.send_message(player.user_id, Content.get_content(player)['admin']['server-stopped'])
