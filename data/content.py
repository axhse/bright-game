import json
from common_types import Player


class Content:
    _ALL_CONTENT: dict = None
    _EMOJI: dict = None
    _is_loaded = False

    @staticmethod
    def load(content_path: str, emoji_path: str):
        with open(content_path, 'r') as f:
            Content._ALL_CONTENT = json.loads(f.read())
        with open(emoji_path, 'r') as f:
            Content._EMOJI = json.loads(f.read())
        Content._is_loaded = True

    @staticmethod
    def get_content(player: Player):
        if not Content._is_loaded:
            raise RuntimeError('Content is not loaded.')
        return Content._ALL_CONTENT[player.lang]

    @staticmethod
    def get_emoji():
        if not Content._is_loaded:
            raise RuntimeError('Content is not loaded.')
        return Content._EMOJI

    @staticmethod
    def subs(text: str, **kwargs):
        for var in kwargs.keys():
            text = text.replace('{{' + var + '}}', str(kwargs[var]))
        return text

    @staticmethod
    def combine(*args):
        if not len(args):
            return None
        args = [str(arg) for arg in args]
        text = args[0]
        for i in range(1, len(args)):
            if Content._is_emoji(args[i - 1]) or Content._is_emoji(args[i]):
                text = text + ' ' + args[i]
            else:
                text = text + '\n' + args[i]
        return text

    @staticmethod
    def shift(text: str):
        return f"{Content._EMOJI['shift-symbol']}\n{text}" if len(text) else Content._EMOJI['shift-symbol']

    @staticmethod
    def _is_emoji(text: str):
        return len(text) == 1    # FIXME
