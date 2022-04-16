import re
from telebot.types import Message

from message_schemes.menu_schemes import *
from utils.logger import StaticLogger, LogReport
from data import content
from chat_bot import ChatBot
from call import Call
from player import Player
from bot_status import BotStatus


class MenuBot:
    def __init__(self, bot: ChatBot):
        self._bot = bot

    @staticmethod
    def get_command_from_message(message: Message) -> str:
        return None if re.search(r'^/[a-z]{1,20}$', message.text) is None else message.text[1:]

    @StaticLogger.exception_logged
    def reply_to_message(self, player: Player, message: Message):
        command = self.get_command_from_message(message)
        if command == 'games' or command == 'start':
            self._bot.send_message(player, MainMenu(player))

    @StaticLogger.exception_logged
    def reply_to_navigation(self, player: Player, call: Call):
        category, target = call.args['category'], call.args['target']
        scheme = None
        send_new_message = False
        if category == 'menu':
            if target == 'main':
                scheme = MainMenu(player)
            if target == 'game':
                scheme = GameMenu(player, call.args)
                send_new_message = True
            if target == 'settings':
                scheme = Settings(player)
        if category == 'info':
            send_new_message = True
            if target == 'rules':
                scheme = RulesInfo(player, call.args)
        if category == 'settings':
            if target == 'lang':
                scheme = LangSettings(player)
            if target == 'difficulty':
                scheme = DifficultySettings(player, call.args)
        if send_new_message:
            self._bot.send_message(player, scheme)
        else:
            scheme.paste_to_message(call.message)
            self._bot.update_message(call.message)

    @StaticLogger.exception_logged
    def reply_to_param_update(self, player: Player, call: Call):
        param = call.args['param']
        if param == 'lang':
            player.lang = call.args['lang']
            MainMenu(player).paste_to_message(call.message)
            self._bot.update_message(call.message)
        if param == 'difficulty':
            player.game_settings[call.args['game-key']] = {'w': int(call.args['w']), 'h': int(call.args['h']),
                                                           'variety': int(call.args['variety'])}
            GameMenu(player, call.args).paste_to_message(call.message)
            self._bot.update_message(call.message)

    @StaticLogger.exception_logged
    def display_admin_menu(self, player: Player, status: BotStatus, message: Message = None):
        scheme = AdminMenu(player, status)
        if message is not None:
            scheme.paste_to_message(message)
            self._bot.update_message(message)
        else:
            self._bot.send_message(player, scheme)

    @StaticLogger.exception_logged
    def display_logs(self, player: Player, log_report: LogReport):
        logs = LogsInfo(player, log_report)
        self._bot.send_message(player, logs)
        if logs.file is not None:
            self._bot.send_document(player, logs.file)

    @StaticLogger.exception_logged
    def inform_bot_is_paused(self, player: Player):
        self._bot.send_message(player, MessageScheme(content.get_text(player.lang, 'info', 'bot-paused')))

    @StaticLogger.exception_logged
    def inform_server_is_stopping(self, player: Player):
        self._bot.send_message(player, MessageScheme(content.get_text(player.lang, 'admin-menu', 'server-stopping')))

    @StaticLogger.exception_logged
    def inform_server_is_stopped(self, player: Player):
        self._bot.send_message(player, MessageScheme(content.get_text(player.lang, 'admin-menu', 'server-stopped')))
