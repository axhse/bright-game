from telebot import TeleBot
from telebot.types import Message

from message_schemes.menu_schemes import MessageScheme
from player import Player


class ChatBot:
    def __init__(self, bot: TeleBot):
        self._bot = bot

    def send_message(self, player: Player, scheme: MessageScheme):
        self._bot.send_message(player.user_id, scheme.title, reply_markup=scheme.get_inline_markup())

    def delete_message(self, message: Message):
        self._bot.delete_message(message.chat.id, message.message_id)

    def update_message(self, message: Message):
        self._bot.edit_message_text(message.text, message.chat.id,
                                    message.message_id, reply_markup=message.reply_markup)

    def send_document(self, player: Player, document):
        self._bot.send_document(player.user_id, document)
