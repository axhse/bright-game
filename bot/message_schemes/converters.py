from data import content
from game_models.models_enum import GameModels
from player import Player
from game import Game


def game_move_count(player: Player, game: Game) -> str:
    if game.model_type in [GameModels.MEMORY, GameModels.HALMA]:
        moves = game.model.move_count
        return content.subs(content.get_text(player.lang, 'game', 'move-count'), moves=moves)


def memory_difficulty_title(player: Player, size: int, variety: int, all_detailed=False, custom_detailed=False) -> str:
    game_key = GameModels.MEMORY.key
    text = content.get_text(player.lang, 'game', game_key, 'difficulty')
    levels = content.game_setup[game_key]['levels']
    level = 'custom'
    for key in levels:
        if levels[key]['size'] == size and levels[key]['variety'] == variety:
            level = key
            break
    if all_detailed or level == 'custom' and custom_detailed:
        value = content.subs(text['value'], level=text['levels'][level], size=size, variety=variety)
    else:
        value = text['levels'][level]
    return content.subs(text['message'], value=value)
