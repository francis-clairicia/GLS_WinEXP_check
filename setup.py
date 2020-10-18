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

application = "gls_winexp_check"
license_file = "LICENSE"

app_globals = dict()

with open(os.path.join(application, "version.py")) as file:
    exec(file.read(), app_globals)

executable_infos = {
    "script": "run.py",
    "base": "Win32GUI",
    "name": "GLS WinEXP check",
    "version": app_globals["__version__"],
    "description": "A program to check customers on PrestaShop for GLS' WinEXPé software",
    "author": "Francis Clairicia-Rose-Claire-Joséphine",
    "icon": None,
    "copyright": None,
}

options = {
    "path": sys.path,
    "build_exe": "build_dir",
    "includes": [
        application,
        "tkinter",
        "cryptography",
        "requests",
    ],
    "excludes": [],
    "include_files": [],
    "optimize": 0,
    "silent": True
}

print("-----------------------------------{ cx_Freeze }-----------------------------------")
print("Name: {name}".format(**executable_infos))
print("Author: {author}".format(**executable_infos))
print("Version: {version}".format(**executable_infos))
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
    if os.path.isfile(license_file):
        with open(license_file, "r") as file:
            for line in file.readlines():
                if line.startswith("Copyright"):
                    executable_infos["copyright"] = line
                    break

#############################################################################
# preparation de la cible

target = Executable(
    script=os.path.join(sys.path[0], executable_infos["script"]),
    base=executable_infos["base"] if sys.platform == "win32" else None,
    targetName=executable_infos["name"] + ".exe",
    shortcutName=executable_infos["name"],
    icon=executable_infos["icon"],
    copyright=executable_infos["copyright"]
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