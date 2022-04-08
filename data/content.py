import json
from os import path, environ
from dotenv import load_dotenv


def _load_json(file_path: str):
    with open(file_path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


def get_text(*args: str):
    global all_text
    result = all_text
    for arg in args:
        result = result[arg]
    return result


def subs(text: str, **kwargs) -> str:
    for var in kwargs.keys():
        text = text.replace('{{' + var + '}}', str(kwargs[var]))
    return text


def combine(*args) -> str:
    def is_emoji(text_value: str): return len(text_value) == 1    # FIXME
    if not len(args):
        return ''
    args = [str(arg) for arg in args]
    text = args[0]
    for i in range(1, len(args)):
        if is_emoji(args[i - 1]) or is_emoji(args[i]):
            text = text + ' ' + args[i]
        else:
            text = text + '\n' + args[i]
    return text


def combine_with_dash(text: str) -> str:
    global emoji
    return f"{emoji['dash']}\n{text}" if len(text) else emoji['dash']


load_dotenv()
game_setup = _load_json(path.join(environ['DATA_DIRECTORY'], 'game_setup.json'))
emoji = _load_json(path.join(environ['DATA_DIRECTORY'], 'emoji.json'))
all_text = _load_json(path.join(environ['DATA_DIRECTORY'], 'localization.json'))
__all__ = ['get_text', 'subs', 'combine', 'combine_with_dash',
           'game_setup', 'emoji', 'all_text']
