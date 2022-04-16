import time
from telebot import TeleBot
from telebot.types import Message
from threading import Thread, Lock

from utils.async_executor import IgnoringLimitedExecutor
from utils.logger import Logger, StaticLogger
from utils.log_types import CriticalLog, ExceptionLog, WarningLog
from data.cache import Cache
from game_service import GameService
from menu_bot import MenuBot
from call import Call, CallSources
from player import Player
from bot_status import BotStatus


class QueryHandler:
    def __init__(self, bot: TeleBot, menu_bot: MenuBot, game_service: GameService,
                 update_workers_count: int, callback_workers_count: int, admin_user_id: int = None):
        self._admin_user_id = admin_user_id
        self._bot = bot
        self._menu_bot = menu_bot
        self._game_service = game_service
        self._update_executor = IgnoringLimitedExecutor(update_workers_count)
        self._callback_executor = IgnoringLimitedExecutor(callback_workers_count)
        self._player_cache = Cache()
        self._bot.set_update_listener(self._handle_updates_async)
        self._bot.register_callback_query_handler(self._handle_callback_async, None)
        self._start_lock = Lock()
        self._is_paused = False

    @StaticLogger.exception_logged
    def start(self):
        if not self._start_lock.acquire(blocking=False):
            raise RuntimeError('Handler can be started only once.')
        self._game_service.start()
        self._bot.infinity_polling()

    @StaticLogger.exception_logged
    def stop(self):
        if self._admin_user_id is not None:
            self._menu_bot.inform_server_is_stopping(Player(self._admin_user_id))   # FIXME: From Cache
        self._bot.stop_polling()
        self._update_executor.pause()
        self._callback_executor.pause()
        time.sleep(0.5)    # Catching lost tasks (requested but not started)
        while self._update_executor.is_busy or self._callback_executor.is_busy:
            time.sleep(0.2)
        self._game_service.stop()
        if self._admin_user_id is not None:
            self._menu_bot.inform_server_is_stopped(Player(self._admin_user_id))   # FIXME: TEMP

    @StaticLogger.exception_logged
    def _handle_updates_async(self, updates):
        for update in updates:
            self._update_executor.execute(self._handle_message, update)

    @StaticLogger.exception_logged
    def _handle_callback_async(self, callback_query):
        self._callback_executor.execute(self._handle_callback, Call(callback_query))

    @StaticLogger.exception_logged
    def _handle_message(self, message: Message):
        player = self._find_player_from_message(message)
        if message.text == '/admin' and player.user_id == self._admin_user_id:
            self._menu_bot.display_admin_menu(player, BotStatus(self._is_paused, self._game_service.active_game_count,
                                                                StaticLogger.logger.log_count))
        if self._is_paused and player.user_id != self._admin_user_id:
            self._menu_bot.inform_bot_is_paused(player)
        else:
            self._menu_bot.reply_to_message(player, message)

    @StaticLogger.exception_logged
    def _handle_callback(self, call: Call):
        player = self._find_player_from_message(call.message)
        if self._is_paused and call.source not in [CallSources.GAME, CallSources.ADMIN] \
                and player.user_id != self._admin_user_id:
            self._menu_bot.inform_bot_is_paused(player)
            self._bot.answer_callback_query(call.call_id)
        else:
            if call.source == CallSources.NAVIGATION:
                self._menu_bot.reply_to_navigation(player, call)
            if call.source == CallSources.UPDATE_PARAM:
                self._menu_bot.reply_to_param_update(player, call)
            if call.source == CallSources.GAME:
                self._game_service.add_game_call(call)
            if call.source == CallSources.CONNECTING:
                self._game_service.handle_connecting_call(player, call)
            if call.source == CallSources.ADMIN:
                self._handle_admin_callback(player, call)
            self._bot.answer_callback_query(call.call_id)

    @StaticLogger.exception_logged
    def _handle_admin_callback(self, player: Player, call: Call):
        if player.user_id != self._admin_user_id:
            return
        if call.args['action'] == 'pause-bot':
            if not self._is_paused:
                self._is_paused = True
                self._menu_bot.display_admin_menu(player, BotStatus(self._is_paused,
                                                  self._game_service.active_game_count, StaticLogger.logger.log_count),
                                                  call.message)
        if call.args['action'] == 'resume-bot':
            if self._is_paused:
                self._is_paused = False
                self._menu_bot.display_admin_menu(player, BotStatus(self._is_paused,
                                                  self._game_service.active_game_count, StaticLogger.logger.log_count),
                                                  call.message)
        if call.args['action'] == 'stop-server':
            Thread(target=self.stop).start()
        if call.args['action'] == 'load-logs':
            self._menu_bot.display_logs(player, StaticLogger.logger.get_report(
                    Logger.type_rule(CriticalLog, ExceptionLog, WarningLog)))

    @StaticLogger.exception_logged
    def _find_player_from_message(self, message: Message) -> Player:
        player = self._player_cache[message.chat.id]
        if player is not None:
            return player
        lang = message.from_user.language_code
        if lang not in ['en', 'ru']:
            lang = 'en'
        player = Player(message.chat.id, lang)
        self._player_cache[player.user_id] = player
        return player
