# -*- coding: utf-8 -*

import os
import sys
import subprocess
import glob
from gls_winexp_check import GLSWinEXPCheck

def main():
    archive = glob.glob(os.path.join(sys.path[0], "GLS_WinEXP_check-v*.zip"))
    window = GLSWinEXPCheck()
    if not archive:
        window.mainloop()
    else:
        window.update_app = True
    if window.update_app:
        updater_exe = os.path.join(sys.path[0], "Updater.exe")
        if os.path.isfile(updater_exe):
            updater_args = [updater_exe]
        else:
            updater_args = ["python.exe", "updater.py"]
        process = subprocess.Popen(updater_args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0

if __name__ == "__main__":
    sys.exit(main())