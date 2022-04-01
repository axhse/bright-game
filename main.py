import telebot

from os import environ
from dotenv import load_dotenv

from query_handler import QueryHandler
from chat_bot import ChatBot
from game_service import GameService
from game_service_bot import GameServiceBot
from utils.logger import Logger
from data.content import Content
from data.game_data import GameData

load_dotenv()

token = environ['BOT_TOKEN']
admin_user = int(environ['ADMIN_USER_ID'])
update_workers = int(environ['UPDATE_HANDLER_WORKERS'])
callback_workers = int(environ['CALLBACK_HANDLER_WORKERS'])
game_manager_workers = int(environ['GAME_MANAGER_WORKERS'])
content_path = environ['CONTENT_FILE']
emoji_path = environ['EMOJI_FILE']
game_path = environ['GAME_FILE']

bot = telebot.TeleBot(token)
logger = Logger(allow_printing=True)
Content.load(content_path, emoji_path)
GameData.load(game_path)
chat_bot = ChatBot(bot, logger)
game_service_bot = GameServiceBot(bot, logger)
game_service = GameService(game_service_bot, game_manager_workers, logger)
handler = QueryHandler(bot, chat_bot, game_service, logger, admin_user, update_workers, callback_workers)
handler.start()
