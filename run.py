# -*- coding: utf-8 -*

import os
import sys
import subprocess
from gls_winexp_check import GLSWinEXPCheck

def main():
    window = GLSWinEXPCheck()
    if not os.path.isfile(os.path.join(sys.path[0], "update.txt")):
        window.mainloop()
    else:
        window.update_app = True
    if window.update_app:
        updater_exe = os.path.join(sys.path[0], "Updater.exe")
        if os.path.isfile(updater_exe):
            updater_args = [updater_exe]
        else:
            updater_args = ["python.exe", "updater.py"]
        process = subprocess.Popen(updater_args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    return 0

if __name__ == "__main__":
    sys.exit(main())