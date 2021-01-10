# -*- coding: Utf-8 -*

from tkinter.scrolledtext import ScrolledText
from io import TextIOBase
from .functions import unlock_text_widget

class Log(ScrolledText, TextIOBase):
    def __init__(self, master, *args, **kwargs):
        ScrolledText.__init__(self, master, *args, **kwargs)
        TextIOBase.__init__(self)
        self.configure(state="disabled")

    def print(self, *values, **kwargs):
        return print(*values, **kwargs, file=self)

    @unlock_text_widget
    def clear(self):
        self.delete("1.0", "end")

    @unlock_text_widget
    def write(self, s: str):
        self.insert("end", s)
        return len(s)
