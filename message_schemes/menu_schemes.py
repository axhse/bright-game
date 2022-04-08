from io import StringIO

from message_schemes.message_scheme import MessageScheme, MarkupScheme, ButtonScheme
from message_schemes import converters
from utils.logger import StaticLogger, LogReport
from data import content
from game_models.models_enum import GameModels
from call import CallSources
from player import Player
from bot_status import BotStatus


class MainMenu(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player):
        text, emoji = content.get_text(player.lang), content.emoji
        markup = MarkupScheme()
        for model in GameModels:
            game_key = model.key
            label = content.combine(emoji['game'][game_key]['icon'], text['game'][game_key]['name'])
            markup.row(ButtonScheme(label,
                                    f'{CallSources.NAVIGATION.value}:category=menu,target=game,game-key={game_key}'))
        label = content.combine(emoji['menu']['settings'], text['settings']['label'])
        markup.row(ButtonScheme(label, f'{CallSources.NAVIGATION.value}:category=menu,target=settings'))
        title = content.combine_with_dash(text['main-menu']['title'])
        super().__init__(title, markup)


class GameMenu(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, arg_dict: dict):
        game_key = arg_dict['game-key']
        game_model = GameModels.from_key(game_key)
        text, emoji = content.get_text(player.lang), content.emoji
        title = ''
        markup = MarkupScheme(width=2)
        if game_model == GameModels.MEMORY:
            if 'w' in arg_dict and 'h' in arg_dict and 'variety' in arg_dict:
                w, h, variety = int(arg_dict['w']), int(arg_dict['h']), int(arg_dict['variety'])
            else:
                default = player.game_settings[game_model.key]
                w, h, variety = default['w'], default['h'], default['variety']
            title = converters.memory_difficulty_title(player, w * h, variety, custom_detailed=True)
            args = f"w={w},h={h},variety={variety}"
            label = content.combine(emoji['game'][game_key]['icon'], text['game-menu']['play'])
            markup.add(ButtonScheme(label,
                                    f'{CallSources.CONNECTING.value}:action=connect,game-key={game_key},{args}'))
            label = content.combine(emoji['menu']['difficulty'], text['game-menu']['difficulty'])
            markup.add(ButtonScheme(label,
                       f'{CallSources.NAVIGATION.value}:category=settings,target=difficulty,game-key={game_key}'))
        if game_model == GameModels.HALMA:
            label = content.combine(emoji['game'][game_key]['icon'], text['game-menu']['play'])
            markup.add(ButtonScheme(label, f'{CallSources.CONNECTING.value}:action=connect,game-key={game_key}'))
        label = content.combine(emoji['menu']['rules'], text['game-menu']['rules'])
        markup.row(ButtonScheme(label,
                                f'{CallSources.NAVIGATION.value}:category=info,target=rules,game-key={game_key}'))
        label = content.combine(emoji['menu']['navigate-back'], text['main-menu']['title'])
        markup.add(ButtonScheme(label, f'{CallSources.NAVIGATION.value}:category=menu,target=main'))
        title = content.combine(text['game'][game_key]['name'], title)
        title = content.combine_with_dash(title)
        super().__init__(title, markup)


class Settings(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player):
        text, emoji = content.get_text(player.lang, 'settings'), content.emoji['menu']
        markup = MarkupScheme()
        label = content.combine(emoji['lang'], text['lang']['label'])
        markup.row(ButtonScheme(label, f'{CallSources.NAVIGATION.value}:category=settings,target=lang'))
        title = content.combine_with_dash(text['title'])
        super().__init__(title, markup)


class AdminMenu(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, status: BotStatus):
        text, emoji = content.get_text(player.lang, 'admin-menu'), content.emoji['admin']
        markup = MarkupScheme(width=2)
        markup.add(ButtonScheme(text['pause-bot'], f'{CallSources.ADMIN.value}:action=pause-bot'),
                   ButtonScheme(text['resume-bot'], f'{CallSources.ADMIN.value}:action=resume-bot'),
                   ButtonScheme(text['stop-server'], f'{CallSources.ADMIN.value}:action=stop-server'),
                   ButtonScheme(text['load-logs'], f'{CallSources.ADMIN.value}:action=load-logs'))
        key = 'bot-paused' if status.is_paused else 'bot-working'
        label = content.combine(emoji[key], text[key])
        if status.active_game_count is not None:
            label = content.combine(label, content.subs(text['active-games'], count=status.active_game_count))
        if status.log_count is not None:
            label = content.combine(label, content.subs(text['total-log-count'], count=status.log_count))
        super().__init__(label, markup)


class RulesInfo(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, args: dict):
        super().__init__(content.get_text(player.lang, 'game', args['game-key'], 'rules'))


class LangSettings(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player):
        text = content.get_text(player.lang, 'settings', 'lang')
        markup = MarkupScheme(width=2)
        for lang_key in text['keys']:
            markup.add(ButtonScheme(text['keys'][lang_key],
                                    f'{CallSources.UPDATE_PARAM.value}:param=lang,lang={lang_key}'))
        title = content.combine_with_dash(text['title'])
        super().__init__(title, markup)


class DifficultySettings(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, args: dict):
        game_key = args['game-key']
        if GameModels.from_key(game_key) == GameModels.MEMORY:
            text = content.get_text(player.lang, 'game', game_key, 'difficulty')
            levels = content.game_setup[game_key]['levels']
            markup = MarkupScheme(width=2 if player.lang == 'en' else 1)
            for level in levels:
                w, h, variety = levels[level]['columns'], levels[level]['rows'], levels[level]['variety']
                label = content.subs(text['value'], level=text['levels'][level], size=w*h, variety=variety)
                markup.add(ButtonScheme(label, f'{CallSources.UPDATE_PARAM.value}:'
                                        f'param=difficulty,game-key={game_key},w={w},h={h},variety={variety}'))
            title = content.combine_with_dash(text['title'])
            super().__init__(title, markup)


class LogsInfo(MessageScheme):
    @StaticLogger.exception_logged
    def __init__(self, player: Player, log_report: LogReport):
        self.file = None
        if len(log_report.text):
            file = StringIO()
            file.name = 'logs.txt'
            file.write(log_report.text)
            file.seek(0)
            self.file = file
        super().__init__(content.subs(content.get_text(player.lang, 'admin-menu', 'log-count'), count=log_report.count))
