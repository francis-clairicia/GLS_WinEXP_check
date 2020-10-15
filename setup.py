# -*- coding:Utf-8 -*

"""
Icone sous Windows: il faut:
=> un xxx.ico pour integration dans le exe, avec "icon=xxx.ico"
=> un xxx.png pour integration avec PyQt4 + demander la recopie avec includefiles.
"""

import os
import sys
from cx_Freeze import setup, Executable

#############################################################################
# Recupération des valeurs

executable_infos = {
    "script": "run.py",
    "base": "Win32GUI",
    "name": "GLS WinEXP check",
    "description": "A program to check customers on PrestaShop for GLS' WinEXPé software",
    "author": "Francis Clairicia",
    "icon": None,
}

options = {
    "path": sys.path,
    "build_exe": "build_dir",
    "includes": [
        "os",
        "sys",
        "configparser",
        "csv",
        "json",
        "tkinter",
        "io",
        "threading",
        "cryptography",
        "prestashop",
        "window",
        "random",
        "string",
        "requests",
        "typing",
    ],
    "excludes": [],
    "include_files": [],
    "optimize": 0,
    "silent": True
}

print("-----------------------------------{ cx_Freeze }-----------------------------------")
print("Name: {name}".format(**executable_infos))
print("Author: {author}".format(**executable_infos))
executable_infos["version"] = input("Version: ")
print("Description: {description}".format(**executable_infos))
print("Icon: {icon}".format(**executable_infos))
print("Modules: {includes}".format(**options))
print("Additional files/folders: {include_files}".format(**options))

while True:
    OK = input("Is this ok ? (y/n) : ").lower()
    if OK in ("y", "n"):
        break

if OK == "n":
    sys.exit(0)

print("-----------------------------------------------------------------------------------")

if "tkinter" in options["includes"]:
    PYTHON_INSTALL_DIR = sys.path[4]
    os.environ["TCL_LIBRARY"] = os.path.join(PYTHON_INSTALL_DIR, "tcl", "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(PYTHON_INSTALL_DIR, "tcl", "tk8.6")
    
    options["include_files"] += [
        os.path.join(PYTHON_INSTALL_DIR, "DLLs", "tk86t.dll"),
        os.path.join(PYTHON_INSTALL_DIR, "DLLs", "tcl86t.dll"),
    ]
else:
    options["excludes"].append("tkinter")

# pour inclure sous Windows les dll system de Windows necessaires
if sys.platform == "win32":
    options["include_msvcr"] = True

#############################################################################
# preparation de la cible

target = Executable(
    script=os.path.join(sys.path[0], executable_infos["script"]),
    base=executable_infos["base"] if sys.platform == "win32" else None,
    targetName=executable_infos["name"] + ".exe",
    shortcutName=executable_infos["name"],
    icon=executable_infos["icon"]
)

#############################################################################
# creation du setup

sys.argv = [sys.argv[0], "build_exe"]

try:
    result = str()
    setup(
        name=executable_infos["name"],
        version=executable_infos["version"],
        description=executable_infos["description"],
        author=executable_infos["author"],
        options={"build_exe": options},
        executables=[target]
    )
except Exception as e:
    result = f"{e.__class__.__name__}: {e}"
else:
    result = "La conversion est terminée"
finally:
    print("-----------------------------------------------------------------------------------")
    print(result)
    print("-----------------------------------------------------------------------------------")
    os.system("pause")