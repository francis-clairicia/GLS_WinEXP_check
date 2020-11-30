# -*- coding: utf-8 -*

import os
import sys
import glob
from gls_winexp_check import GLSWinEXPCheck
from gls_winexp_check.updater import Updater

def main():
    window = GLSWinEXPCheck()
    Updater.clear_old_files()
    update_archive = os.path.join(sys.path[0], f"GLS_WinEXP_check.zip")
    if not os.path.isfile(update_archive):
        files_to_delete_filepath = os.path.join(sys.path[0], "files-to-delete.txt")
        if os.path.isfile(files_to_delete_filepath):
            with open(files_to_delete_filepath, "r") as files_to_delete:
                for file in files_to_delete.read().splitlines():
                    file = os.path.join(sys.path[0], file.replace("/", "\\"))
                    if os.path.isfile(file):
                        os.remove(file)
            os.remove(files_to_delete_filepath)
        window.mainloop()
    else:
        window.update_app = True
    window.destroy()
    if window.update_app:
        updater = Updater()
        updater.launch(update_archive)
    return 0

if __name__ == "__main__":
    sys.exit(main())