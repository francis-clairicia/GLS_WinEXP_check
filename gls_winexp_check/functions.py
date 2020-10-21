# -*- coding: Utf-8 -*

from threading import Thread
from functools import wraps

def thread_function(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
        thread = Thread(target=function, args=args, kwargs=kwargs, daemon=True)
        thread.start()

    return wrapper

def unlock_text_widget(function):

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        self.configure(state="normal")
        to_return = function(self, *args, **kwargs)
        self.configure(state="disabled")
        return to_return

    return wrapper

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)