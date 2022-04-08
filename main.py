import telebot

from os import environ
from dotenv import load_dotenv

from query_handler import QueryHandler
from game_service import GameService
from chat_bot import ChatBot
from menu_bot import MenuBot
from game_service_bot import GameServiceBot
from utils.logger import Logger, StaticLogger

load_dotenv()

token = environ['BOT_TOKEN']
admin_var = environ.get('ADMIN_USER_ID')
admin_user_id = int(environ['ADMIN_USER_ID']) if admin_var is not None and admin_var.isnumeric() else None
update_workers = int(environ['UPDATE_HANDLER_WORKERS'])
callback_workers = int(environ['CALLBACK_HANDLER_WORKERS'])
game_manager_workers = int(environ['GAME_MANAGER_WORKERS'])

bot = telebot.TeleBot(token)
StaticLogger.set_logger(Logger(allow_printing=True))
chat_bot = ChatBot(bot)
game_service = GameService(GameServiceBot(chat_bot), game_manager_workers)
handler = QueryHandler(bot, MenuBot(chat_bot), game_service, update_workers, callback_workers, admin_user_id)
handler.start()
