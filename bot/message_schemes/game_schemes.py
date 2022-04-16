from message_schemes.message_scheme import MessageScheme, MarkupScheme, ButtonScheme
from message_schemes import converters
from utils.logger import StaticLogger
from data import content
from game_models.models_enum import GameModels
from call import CallSources
from player import Player
from game import Game


class MemoryMain(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, game: Game):
        player = game.players[0]
        emoji = content.emoji['game'][GameModels.MEMORY.key]
        card_emoji = emoji['cards']
        hidden_emoji, removed_emoji = emoji['hidden'], emoji['removed']
        board = game.model.get_board()
        markup = MarkupScheme(width=board.columns)
        for i in range(board.rows):
            for j in range(board.columns):
                card = board[i, j]
                item_emoji = removed_emoji
                if not card.is_removed:
                    item_emoji = hidden_emoji
                    if not card.is_hidden:
                        item_emoji = card_emoji[card.value]
                markup.add(ButtonScheme(item_emoji,
                                        f'{CallSources.GAME.value}:action=click,game-id={game.uid},a={i},b={j}'))

        text = content.get_text(player.lang, 'game')
        removed = game.model.removed_count
        size, variety = game.model.get_board().size, game.model.get_board().variety
        title = content.combine(converters.memory_difficulty_title(player, size, variety),
                                converters.game_move_count(player, game),
                                content.subs(text[GameModels.MEMORY.key]['progress'], removed=removed, size=size))
        super().__init__(title, markup)


class HalmaMain(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, game: Game, player_index: int):
        player = game.players[player_index]
        emoji = content.emoji['game'][GameModels.HALMA.key]
        board = game.model.get_board(player_index)
        markup = MarkupScheme(width=8)
        for i in range(8):
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
                a, b = ((i, j), (7 - i, 7 - j))[player_index]
                markup.add(ButtonScheme(item_emoji,
                           f'{CallSources.GAME.value}:action=click,game-id={game.uid},p={player_index},a={a},b={b}'))
        if game.model.can_end_turn(player_index):
            markup.row(ButtonScheme(content.get_text(player.lang, 'game', 'halma', 'end-turn'),
                                    f'{CallSources.GAME.value}:action=end-turn,game-id={game.uid},p={player_index}'))
        text = content.get_text(player.lang, 'game')
        title = text['player-turn'] if player_index == game.model.turn else text['opponent-turn']
        super().__init__(title, markup)


class MemoryFinal(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, game: Game):
        player = game.players[0]
        result = game.results[0]
        text = content.get_text(player.lang, 'game')
        icon = content.emoji['game'][GameModels.MEMORY.key]['icon']
        main_line = content.subs(text['result']['message'],
                                 game=content.combine(icon, text[GameModels.MEMORY.key]['name']),
                                 result=text['result'][result.status.value])
        title = content.combine(main_line, converters.memory_difficulty_title(player,
                                game.model.get_board().size, game.model.get_board().variety, custom_detailed=True),
                                converters.game_move_count(player, game))
        super().__init__(title)


class HalmaFinal(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, game: Game, player_index: int):
        player = game.players[player_index]
        result = game.results[player_index]
        text = content.get_text(player.lang, 'game')
        icon = content.emoji['game'][GameModels.HALMA.key]['icon']
        main_line = content.subs(text['result']['message'],
                                 game=content.combine(icon, text[GameModels.HALMA.key]['name']),
                                 result=text['result'][result.status.value])
        title = content.combine(main_line, converters.game_move_count(player, game))
        super().__init__(title)


class OpponentSearch(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, args: dict):
        text = content.get_text(player.lang, 'game-menu')
        title = text['finding-opponent'] if GameModels.from_key(args['game-key']).value.PLAYER_COUNT == 2 \
            else text['finding-opponents']
        markup = MarkupScheme()
        markup.add(ButtonScheme(text['stop-searching'],
                                f"{CallSources.CONNECTING.value}:action=disconnect,game-key={args['game-key']}"))
        super().__init__(title, markup)
