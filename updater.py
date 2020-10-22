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
    def __init__(self):
        Window.__init__(self, "GLS WinEXP check updater", width=500, height=300)

        self.log = Log(self, relief=tk.RIDGE, bd=4)
        self.log.grid(row=0, sticky=tk.NSEW)
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate", value=0)
        self.progress.grid(row=1, sticky=tk.EW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    @thread_function
    def launch_update(self, archive: str):
        if not archive:
            return
        self.log.print("Opening {}".format(archive))
        with ZipFile(archive, "r") as zip_file:
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
        showinfo("Mise à jour terminée", "La mise à jour est effectuée")
        self.reopen_main_program()
        self.destroy()

    def reopen_main_program(self):
        try:
            launcher = os.path.join(sys.path[0], "GLS WinEXP check.exe")
            if os.path.isfile(launcher):
                updater_args = [launcher]
            else:
                updater_args = ["python.exe", "run.py"]
            process = subprocess.Popen(updater_args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception as e:
            self.log.print(f" -> {e.__class__.__name__}: {e}")
            print(f" -> {e.__class__.__name__}: {e}", file=sys.stderr)

def main():
    time.sleep(1)
    window = GLSWinEXPCheckUpdater()
    update_file = os.path.join(sys.path[0], "update.txt")
    if not os.path.isfile(update_file):
        window.reopen_main_program()
        return 0
    with open(update_file, "r") as update:
        version = update.read()
    os.remove(update_file)
    update_archive = os.path.join(sys.path[0], f"GLS_WinEXP_check-v{version}.zip")
    all_archives = glob.glob(os.path.join(sys.path[0], "GLS_WinEXP_check-v*.zip"))
    for archive in all_archives:
        if archive != update_archive:
            os.remove(archive)
    window.after(10, lambda archive=update_archive: window.launch_update(archive))
    window.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())