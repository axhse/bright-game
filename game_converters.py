from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.content import Content
from data.game_data import GameData
from common_types import Game
from game_models.memory import MemoryModel
from game_models.halma import HalmaModel


def game_difficulty(game: Game, player=None, all_detailed=False, custom_detailed=False):
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
        if all_detailed or level == 'custom' and custom_detailed:
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
    if type(game.model) is HalmaModel:
        moves = game.model.total_moves
        return Content.subs(Content.get_content(player)['game']['moves-made'], moves=moves)


def game_main_text(game: Game, player=None):
    if type(game.model) is MemoryModel:
        content = Content.get_content(game.players[0])['game']
        removed = game.model.total_removed
        size = game.model.get_board().size
        text = Content.combine(game_difficulty(game),
                               game_moves_made(game),
                               Content.subs(content['memory']['progress'], removed=removed, total=size))
        return text
    if type(game.model) is HalmaModel:
        for player_id in range(len(game.players)):
            if game.players[player_id] == player:
                content = Content.get_content(player)['game']
                return content['player-turn'] if player_id == game.model.turn else content['opponent-turn']
        return None


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
    if type(game.model) is HalmaModel:
        emoji = emoji['halma']
        for player_id in range(len(game.players)):
            if game.players[player_id] == player:
                board = game.model.get_board(player_id)
                markup = InlineKeyboardMarkup()
                for i in range(8):
                    buttons = []
                    for j in range(8):
                        square = board[i, j]
                        item_emoji = ' '
                        if square.color == 0:
                            item_emoji = emoji['player-piece']
                            if square.is_selected:
                                item_emoji = emoji['player-selected-piece']
                        if square.color == 1:
                            item_emoji = emoji['opponent-piece']
                            if square.is_selected:
                                item_emoji = emoji['opponent-selected-piece']
                        a, b = ((i, j), (7 - i, 7 - j))[player_id]
                        buttons.append(InlineKeyboardButton(item_emoji, callback_data=f'game-service'
                                                            f':click:{game.uid}:{player_id},{a},{b}'))
                    markup.row(*buttons)
                if game.model.can_end_turn(player_id):
                    markup.row(InlineKeyboardButton(Content.get_content(player)['game']['halma']['end-turn'],
                                                    callback_data=f'game-service:end-turn:{game.uid}:{player_id}'))
                return markup
