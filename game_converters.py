from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.content import Content
from data.game_data import GameData
from common_types import Game
from game_models.memory import MemoryModel


def game_difficulty(game: Game, player=None, detailed=False):
    if type(game.model) is MemoryModel:
        player = game.players[0]
        content = Content.get_content(player)['game']['memory']['difficulty']
        levels = GameData.get()['memory']['levels']
        size = game.model.get_board().size
        variety = game.model.get_board().variety
        level = 'custom'
        for key in levels:
            if levels[key]['size'] == size and levels[key]['variety'] == variety:
                level = key
                break
        if detailed:
            value = Content.subs(content['value'], level=content['levels'][level], size=size, variety=variety)
        else:
            value = content['levels'][level]
        text = Content.subs(content['info'], value=value)
        return text


def game_moves_made(game: Game, player=None):
    if type(game.model) is MemoryModel:
        player = game.players[0]
        moves = game.model.total_moves
        return Content.subs(Content.get_content(player)['game']['moves-made'], moves=moves)


def game_main_text(game: Game, player=None):
    content = Content.get_content(game.players[0])['game']
    if type(game.model) is MemoryModel:
        removed = game.model.total_removed
        size = game.model.get_board().size
        text = Content.combine(game_difficulty(game),
                               game_moves_made(game),
                               Content.subs(content['memory']['progress'], removed=removed, total=size))
        return text


def game_main_markup(game: Game, player=None):
    emoji = Content.get_emoji()['game']
    if type(game.model) is MemoryModel:
        emoji = emoji['memory']
        card_emoji = emoji['cards']
        hidden_emoji, removed_emoji = emoji['hidden'], emoji['removed']
        board = game.model.get_board()
        markup = InlineKeyboardMarkup()
        for i in range(board.rows):
            buttons = []
            for j in range(board.columns):
                card = board[i, j]
                item_emoji = removed_emoji
                if not card.is_removed:
                    item_emoji = hidden_emoji
                    if not card.is_hidden:
                        item_emoji = card_emoji[card.value]
                buttons.append(InlineKeyboardButton(item_emoji,
                                                    callback_data=f'game-service:click:{game.uid}:{i},{j}'))
            markup.row(*buttons)
        return markup
