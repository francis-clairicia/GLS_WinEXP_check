import os
import sys
import argparse
import subprocess
import glob
import tkinter as tk
import tkinter.ttk as ttk
from zipfile import ZipFile
from .functions import thread_function

class Updater(tk.Tk):

    OLD_FILE_PREFIX = "OLD_"

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Updater")
        self.geometry("{}x{}".format(500, 300))

        self.label = tk.Label(self, text=str(), font=("Times New Roman", 15))
        self.label.grid(row=0, sticky=tk.NSEW)
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate", value=0)
        self.progress.grid(row=1, sticky=tk.EW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.executable = sys.executable
        self.filepath = os.path.dirname(self.executable)

    @staticmethod
    def clear_old_files() -> None:
        for file in glob.glob(os.path.join(os.path.dirname(sys.executable), "**", "{prefix}*".format(prefix=Updater.OLD_FILE_PREFIX)), recursive=True):
            try:
                os.remove(file)
            except PermissionError:
                continue

    def launch(self, archive: str) -> None:
        if os.path.isfile(archive):
            self.__launch(archive)
        else:
            self.label["text"] = "No update to install"
        self.mainloop()

    @thread_function
    def __launch(self, archive: str) -> None:
        with ZipFile(archive, "r") as zip_file:
            self.label["text"] = "Installing new update..."
            file_list = zip_file.namelist()
            self.progress["maximum"] = len(file_list)
            for i, file in enumerate(file_list, start=1):
                try:
                    zip_file.extract(file, path=self.filepath)
                except PermissionError as e:
                    directory, filename = os.path.split(file)
                    os.rename(os.path.join(self.filepath, file), os.path.join(self.filepath, directory, Updater.OLD_FILE_PREFIX + filename))
                    zip_file.extract(file, path=self.filepath)
                finally:
                    self.progress["value"] = i
        os.remove(archive)
        os.execv(self.executable, [self.executable])