import json
from os import path, environ
from dotenv import load_dotenv


def load_json(file_path: str):
    with open(file_path, 'r') as f:
        return json.loads(f.read())


def get_local(lang: str):
    global all_content
    return all_content[lang]


def subs(text: str, **kwargs):
    for var in kwargs.keys():
        text = text.replace('{{' + var + '}}', str(kwargs[var]))
    return text


def combine(*args):
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


def shift(text: str):
    global emoji
    return f"{emoji['shift-symbol']}\n{text}" if len(text) else emoji['shift-symbol']


load_dotenv()
game_setup = load_json(path.join(environ['DATA_DIRECTORY'], 'game_setup.json'))
emoji = load_json(path.join(environ['DATA_DIRECTORY'], 'emoji.json'))
all_content = load_json(path.join(environ['DATA_DIRECTORY'], 'localization.json'))
