from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.content import Content
from data.game_data import GameData
from common_types import CallInfo, Player


def difficulty_info_from_call(player: Player, call: CallInfo, detailed=False):
    if call.parameter == 'memory':
        content = Content.get_content(player)['game']['memory']['difficulty']
        levels = GameData.get()['memory']['levels']
        if 'w' in call.args and 'h' in call.args and 'variety' in call.args:
            size = int(call.args['w']) * int(call.args['h'])
            variety = int(call.args['variety'])
        else:
            size = player.game_settings['memory']['w'] * player.game_settings['memory']['h']
            variety = player.game_settings['memory']['variety']
        level = 'custom'
        for key in levels:
            if levels[key]['size'] == size and levels[key]['variety'] == variety:
                level = key
                break
        if level == 'custom' or detailed:
            value = Content.subs(content['value'], level=content['levels'][level], size=size, variety=variety)
        else:
            value = content['levels'][level]
        text = Content.subs(content['info'], value=value)
        return text


def difficulty_markup(player: Player, call: CallInfo):
    if call.parameter == 'memory':
        content = Content.get_content(player)['game']['memory']['difficulty']
        levels = GameData.get()['memory']['levels']
        markup = InlineKeyboardMarkup(row_width=5)
        for level in levels:
            h, w, variety = levels[level]['rows'], levels[level]['columns'], levels[level]['variety']
            text = Content.subs(content['value'], level=content['levels'][level], size=h*w, variety=variety)
            markup.add(InlineKeyboardButton(text,
                       callback_data=f'difficulty:navigate:game-menu:memory:h={h},w={w},variety={variety}'))
        return markup
