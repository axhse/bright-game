from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


class ButtonScheme:
    def __init__(self, label: str, callback_data: str):
        self.label = label
        self.callback_data = callback_data
        if len(callback_data) > 64:    # FIXME: TEMP
            print(callback_data)
            print(len(callback_data))

    def to_inline_button(self):
        return InlineKeyboardButton(text=self.label, callback_data=self.callback_data)
    

class MarkupScheme:
    def __init__(self, width=8):
        self._width = width
        self._button_schemes = []

    def add(self, *args: ButtonScheme):
        if len(self._button_schemes) == 0:
            self._button_schemes.append([])
        for arg in args:
            if len(self._button_schemes[-1]) >= self._width:
                self._button_schemes.append([])
            self._button_schemes[-1].append(arg)

    def row(self, *args: ButtonScheme):
        self._button_schemes.append(list(args))

    def insert(self, row_id: int, *args: ButtonScheme):
        self._button_schemes[row_id].extend(args)

    def to_inline_markup(self):
        markup = InlineKeyboardMarkup(row_width=self._width)
        for row in self._button_schemes:
            markup.row(*[scheme.to_inline_button() for scheme in row])
        return markup
            
    
class MessageScheme:

    def __init__(self, title: str, markup_scheme: MarkupScheme = None):
        self.title = title
        self.markup_scheme = markup_scheme

    def paste_to_message(self, message: Message):
        message.text = self.title
        if self.markup_scheme is not None:
            message.reply_markup = self.markup_scheme.to_inline_markup()

    def get_inline_markup(self):
        return None if self.markup_scheme is None else self.markup_scheme.to_inline_markup()
