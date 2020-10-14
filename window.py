# -*- coding: Utf-8 -*

import tkinter as tk
from typing import Callable, Any

class MenuWindow(tk.Menu):
    def __init__(self, master, *args, **kwargs):
        tk.Menu.__init__(self, *args, **kwargs)
        self.master = master
        master.config(menu=self)
        self.sections = dict()

    def add_command(self, name: str, command: Callable[..., Any], accelerator=None):
        if isinstance(accelerator, str):
            modifiers_tab = {
                "Ctrl": "Control",
                "Alt": "Alt",
                "Shift": "Shift"
            }
            splitted_accelerator = accelerator.split("+")
            modifiers = splitted_accelerator[:-1]
            letter = splitted_accelerator[-1]
            self.master.bind_key("-".join(modifiers_tab[m] for m in modifiers), letter, lambda event : command())
        return tk.Menu.add_command(self, label=name, command=command)

    def add_section(self, name: str):
        if name not in self.sections:
            self.sections[name] = tk.Menu(self, tearoff=0)
            self.add_cascade(label=name, menu=self.sections[name])

    def add_section_command(self, section: str, name: str, command: Callable[..., Any], accelerator=None, **kwargs):
        if section in self.sections:
            if isinstance(accelerator, str):
                kwargs["accelerator"] = accelerator
                modifiers_tab = {
                    "Ctrl": "Control",
                    "Alt": "Alt",
                    "Shift": "Shift"
                }
                splitted_accelerator = accelerator.split("+")
                modifiers = splitted_accelerator[:-1]
                letter = splitted_accelerator[-1]
                self.master.bind_key("-".join(modifiers_tab[m] for m in modifiers), letter, lambda event : command())
            self.sections[section].add_command(label=name, command=command, **kwargs)

    def add_section_separator(self, section: str):
        if section in self.sections:
            self.sections[section].add_separator()

class Window(tk.Tk):
    def __init__(self, title="tk", width=800, height=600):
        tk.Tk.__init__(self)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.protocol("WM_DELETE_WINDOW", self.stop)

        self.menu_bar = MenuWindow(self)
        self.refresh_functions = list()
        self.refresh_ratio = 10
        self.refresh()

    def bind_key(self, modifiers: str, key: str, command):
        if isinstance(modifiers, str) and len(modifiers) > 0:
            try:
                self.bind_all(f"<{modifiers}-KeyPress-{key.lower()}>", command)
            except tk.TclError:
                pass
            self.bind_all(f"<{modifiers}-KeyPress-{key.upper()}>", command)
        else:
            try:
                self.bind_all(f"<KeyPress-{key.lower()}>", command)
            except tk.TclError:
                pass
            self.bind_all(f"<KeyPress-{key.upper()}>", command)

    def stop(self):
        self.destroy()

    def refresh(self):
        for function in self.refresh_functions:
            function()
        self.after(self.refresh_ratio, self.refresh)