# -*- coding: Utf-8 -*

import os
import sys
import requests
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror
from threading import Thread
from typing import Dict, Any
from .functions import sizeof_fmt, thread_function

class DownloadLatestUpdate(tk.Toplevel):

    def __init__(self, master, assets: Dict[str, Any]):
        tk.Toplevel.__init__(self)
        self.title("Downloading...")
        self.geometry("545x200")
        self.focus_set()
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.download_file_state = tk.StringVar()
        tk.Label(self, textvariable=self.download_file_state, font=("Times New Roman", 15)).grid(row=0, column=0)
        self.progress = ttk.Progressbar(self, length=200, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.grid(row=1, column=0, sticky=tk.EW)
        self.assets = assets
        self.error_download = False

    @thread_function
    def start(self):
        for file_infos in self.assets:
            self.progress.configure(value=0, maximum=file_infos["size"])
            message = "Retrieving {name}".format(**file_infos)
            self.download_file_state.set(message)
            try:
                response = requests.get(file_infos["browser_download_url"], stream=True)
                response.raise_for_status()
            except Exception as e:
                showerror(e.__class__.__name__, str(e))
                self.error_download = True
                break
            else:
                with open(os.path.join(sys.path[0], file_infos["name"]), "wb") as file_stream:
                    for chunk in response.iter_content(chunk_size=1024*512):
                        self.progress["value"] += file_stream.write(chunk)
                        self.download_file_state.set("{message} - {bytes_downloaded}/{max_bytes} ({percent:.2f}%)".format(
                            message=message,
                            bytes_downloaded=sizeof_fmt(self.progress["value"]),
                            max_bytes=sizeof_fmt(self.progress["maximum"]),
                            percent=(self.progress["value"] * 100) / self.progress["maximum"]
                        ))
            self.download_file_state.set(str())
        self.destroy()