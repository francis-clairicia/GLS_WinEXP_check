# -*- coding:Utf-8 -*

"""
Icone sous Windows: il faut:
=> un xxx.ico pour integration dans le exe, avec "icon=xxx.ico"
=> un xxx.png pour integration avec PyQt4 + demander la recopie avec includefiles.
"""

import os
import sys
import argparse
import glob
from zipfile import ZipFile, ZIP_DEFLATED
from cx_Freeze import setup, Executable

def glob_multiple_pattern(*patterns: str):
    for pattern in patterns:
        yield from glob.glob(pattern)

def zip_compress():
    global executable_infos, options
    zip_filename = "{project_name}-v{version}.zip".format(**executable_infos).replace(" ", "_")
    print(f"Compress executable in {zip_filename}...")
    output_folder = options.get("build_exe", ".")
    output_zip = os.path.join(output_folder, zip_filename)
    all_files = list()
    pattern_list = ["*.exe", "lib", "python*.dll", "vcruntime140.dll", *options["include_files"]]
    for path in glob_multiple_pattern(*[os.path.join(output_folder, pattern) for pattern in pattern_list]):
        if os.path.isfile(path):
            all_files.append({"filename": path, "arcname": path.replace(output_folder, ".")})
        elif os.path.isdir(path):
            for root, folders, files in os.walk(path):
                for file in files:
                    file = os.path.join(root, file)
                    all_files.append({"filename": file, "arcname": file.replace(output_folder, ".")})
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED) as zip_file_fp:
        for file in all_files:
            zip_file_fp.write(**file)

#############################################################################
# Parsing des arguments

parser = argparse.ArgumentParser(prog="setup.py", description="Setup for executable freezing")
parser.add_argument("--zip", help="Create a zip file when it's finished", action="store_true")
parser.add_argument("--zip-no-build", help="Create a zip file without build", action="store_true")
args = parser.parse_args()

#############################################################################
# Recupération des valeurs

application = "gls_winexp_check"

app_globals = dict()

with open(os.path.join(application, "version.py")) as file:
    exec(file.read(), app_globals)

executable_infos = {
    "project_name": "GLS WinEXP check",
    "description": "A program to check customers on PrestaShop for GLS' WinEXPé software",
    "author": "Francis Clairicia-Rose-Claire-Josephine",
    "version": app_globals["__version__"],
    "executables": [
        {
            "script": "run.py",
            "name": "GLS WinEXP check",
            "base": "Win32GUI",
            "icon": "prestashop-282269.ico"
        },
        {
            "script": "updater.py",
            "name": "Updater",
            "base": "Win32GUI",
            "icon": None
        }
    ],
    "copyright": "Copyright (c) 2020 Francis Clairicia-Rose-Claire-Josephine",
}

options = {
    "path": sys.path,
    "build_exe": "build_dir",
    "includes": [
        application,
        "tkinter",
        "cryptography",
        "requests",
        "packaging"
    ],
    "excludes": [],
    "include_files": [
        "prestashop-282269.ico",
    ],
    "optimize": 0,
    "silent": True
}

if args.zip_no_build:
    zip_compress()
    print("-----------------------------------------------------------------------------------")
    os.system("pause")
    sys.exit(0)

print("-----------------------------------{ cx_Freeze }-----------------------------------")
print("Project Name: {project_name}".format(**executable_infos))
print("Author: {author}".format(**executable_infos))
print("Version: {version}".format(**executable_infos))
print("Description: {description}".format(**executable_infos))
print()
for i, infos in enumerate(executable_infos["executables"], start=1):
    print(f"Executable number {i}")
    print("Name: {name}".format(**infos))
    print("Icon: {icon}".format(**infos))
    print()
print("Modules: {includes}".format(**options))
print("Additional files/folders: {include_files}".format(**options))
print()

while True:
    OK = input("Is this ok ? (y/n) : ").lower()
    if OK in ("y", "n"):
        break

if OK == "n":
    sys.exit(0)

print("-----------------------------------------------------------------------------------")

if "tkinter" not in options["includes"]:
    options["excludes"].append("tkinter")

# pour inclure sous Windows les dll system de Windows necessaires
if sys.platform == "win32":
    options["include_msvcr"] = True

#############################################################################
# preparation de la cible

executables = list()
for infos in executable_infos["executables"]:
    target = Executable(
        script=os.path.join(sys.path[0], infos["script"]),
        base=infos["base"] if sys.platform == "win32" else None,
        targetName=infos["name"] + ".exe",
        icon=infos["icon"],
        copyright=executable_infos["copyright"]
    )
    executables.append(target)

#############################################################################
# creation du setup

sys.argv = [sys.argv[0], "build_exe"]

try:
    result = str()
    created = False
    setup(
        name=executable_infos["project_name"],
        version=executable_infos["version"],
        description=executable_infos["description"],
        author=executable_infos["author"],
        options={"build_exe": options},
        executables=executables
    )
except Exception as e:
    result = f"{e.__class__.__name__}: {e}"
else:
    result = "Build done"
    created = True
finally:
    print("-----------------------------------------------------------------------------------")
    print(result)
    if created and args.zip:
        zip_compress()
    print("-----------------------------------------------------------------------------------")
    os.system("pause")