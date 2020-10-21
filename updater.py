# -*- coding: utf-8 -*

import os
import sys
import time
import glob
import tkinter as tk
import tkinter.ttk as ttk
import subprocess
from tkinter.messagebox import showinfo
from zipfile import ZipFile
from gls_winexp_check.window import Window
from gls_winexp_check.log import Log
from gls_winexp_check.gls_winexp_check import thread_function

class GLSWinEXPCheckUpdater(Window):
    def __init__(self, archive: str):
        Window.__init__(self, "GLS WinEXP check updater", width=500, height=300)

        self.archive = archive

        self.log = Log(self, relief=tk.RIDGE, bd=4)
        self.log.grid(row=0, sticky=tk.NSEW)
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate", value=0)
        self.progress.grid(row=1, sticky=tk.EW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.after(10, self.launch_update)

    @thread_function
    def launch_update(self):
        self.log.print("Opening {}".format(self.archive))
        with ZipFile(self.archive, "r") as zip_file:
            file_list = zip_file.namelist()
            self.progress["maximum"] = len(file_list)
            for i, file in enumerate(file_list, start=1):
                try:
                    if os.path.basename(file) != "Updater.exe":
                        zip_file.extract(file)
                except Exception as e:
                    if not isinstance(e, PermissionError):
                        self.log.print(f" -> {e.__class__.__name__}: {e}")
                finally:
                    self.progress["value"] = i
        self.log.print("Removing {}".format(self.archive))
        os.remove(self.archive)
        showinfo("Mise à jour terminée", "La mise à jour est effectuée")
        try:
            launcher = os.path.join(sys.path[0], "GLS WinEXP check.exe")
            if os.path.isfile(launcher):
                updater_args = [launcher]
            else:
                updater_args = ["python.exe", "run.py"]
            process = subprocess.Popen(updater_args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.destroy()
        except Exception as e:
            self.log.print(f" -> {e.__class__.__name__}: {e}")

def main():
    time.sleep(1)
    all_archives = glob.glob(".\\GLS_WinEXP_check-v*.zip")
    if not all_archives:
        return 0
    for archive in all_archives[:-1]:
        os.remove(archive)
    window = GLSWinEXPCheckUpdater(all_archives[-1])
    window.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())