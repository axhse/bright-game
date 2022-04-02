import time
from telebot import TeleBot
from telebot.types import Message
from threading import Thread, Lock

from chat_bot import ChatBot
from game_service import GameService
from utils.async_executor import IgnoringLimitedExecutor
from utils.logger import Logger
from utils.log_types import ExceptionLog, UnknownTypeLog
from common_types import Player, BotStatus, CallInfo


class QueryHandler:
    def __init__(self, bot: TeleBot, chat_bot: ChatBot, game_service: GameService, logger: Logger,
                 admin_user_id: int, update_workers_count: int, callback_workers_count: int):
        self._admin_user_id = admin_user_id
        self._bot = bot
        self._chat_bot = chat_bot
        self._game_service = game_service
        self._update_executor = IgnoringLimitedExecutor(update_workers_count)
        self._callback_executor = IgnoringLimitedExecutor(callback_workers_count)
        self._logger = logger
        self._bot.set_update_listener(self._handle_updates_async)
        self._bot.register_callback_query_handler(self._handle_callback_async, None)
        self._start_lock = Lock()
        self._is_paused = False

    def start(self):
        try:
            if not self._start_lock.acquire(blocking=False):
                raise RuntimeError('Handler can be started only once.')
            self._game_service.start()
            self._bot.infinity_polling()
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'QueryHandler.start'))

    def stop(self):
        try:
            self._bot.stop_polling()
            self._update_executor.pause()
            self._callback_executor.pause()
            time.sleep(0.5)    # Catching lost tasks (requested but not started)
            while self._update_executor.is_busy or self._callback_executor.is_busy:
                time.sleep(0.2)
            self._game_service.stop()
            self._chat_bot.inform_server_is_stopped(Player(self._admin_user_id))
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'QueryHandler.stop'))

    def _handle_updates_async(self, updates):
        for update in updates:
            if type(update) is not Message:
                self._logger.add_log(UnknownTypeLog(f'type(update) is {type(update)}'))
                continue
            if update.content_type != 'text':
                self._logger.add_log(UnknownTypeLog(f'update.content_type is {update.content_type}'))
                continue
            self._update_executor.perform(lambda: self._handle_message(update))

    def _handle_callback_async(self, callback_query):
        self._callback_executor.perform(lambda: self._handle_callback(CallInfo(callback_query)))

    def _handle_message(self, message: Message):
        try:
            player = self._get_player_from_message(message)
            if self._is_paused:
                if player.user_id != self._admin_user_id:
                    self._chat_bot.inform_bot_is_paused(player)
                    return
            command = self._chat_bot.get_command(message)
            if player.user_id == self._admin_user_id:
                if command == 'status':
                    self._chat_bot.display_status(player, BotStatus(self._is_paused,
                                                  self._game_service.active_game_count, self._logger.log_count))
            if command == 'start':
                self._chat_bot.display_main_menu(player)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'QueryHandler.handle_message'))

    def _handle_callback(self, call: CallInfo):
        try:
            player = self._get_player_from_message(call.message)
            if self._is_paused:
                if player.user_id != self._admin_user_id and call.source != 'game-service':
                    self._chat_bot.inform_bot_is_paused(player)
                    self._bot.answer_callback_query(call.call_id)
                    return
            if call.source == 'admin-menu' and player.user_id == self._admin_user_id:
                self._handle_admin_callback(player, call)
            if call.source == 'game-service':
                self._game_service.add_click_call(call)
            if call.source == 'game-pool':
                self._game_service.add_pool_call(player, call)
            if call.action == 'navigate':
                if call.target == 'main-menu':
                    self._chat_bot.display_main_menu(player)
                if call.target == 'game-menu':
                    self._chat_bot.display_game_menu(player, call)
                if call.target == 'difficulty':
                    self._chat_bot.display_difficulty(player, call)
                if call.target == 'settings':
                    pass    # TODO
                if call.target == 'rules':
                    self._chat_bot.display_rules(player, call)
                if call.target == 'rating':
                    pass    # TODO
                if call.target == 'feedback':
                    pass    # TODO
            self._bot.answer_callback_query(call.call_id)
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'QueryHandler.handle_callback'))

    def _handle_admin_callback(self, player: Player, call: CallInfo):
        try:
            if call.action == 'pause-bot':
                self._is_paused = True
            if call.action == 'resume-bot':
                self._is_paused = False
            if call.action == 'stop-server':
                Thread(target=self.stop).start()
                self._chat_bot.inform_server_is_stopping(player)
            if call.action == 'get-logs':
                self._chat_bot.display_logs(player, self._logger.get_report())
        except Exception as exception:
            self._logger.add_log(ExceptionLog(exception, 'QueryHandler.handle_admin_callback'))

    @staticmethod
    def _get_player_from_message(message: Message):   # Do not use message.from_user.id
        lang = message.from_user.language_code
        if lang not in ['en']:
            lang = 'en'
        return Player(message.chat.id, lang)
