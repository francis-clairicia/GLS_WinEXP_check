# -*- coding: Utf-8 -*

import os
import sys
import configparser
import csv
import json
import pickle
import webbrowser
import subprocess
import shutil
import tkinter as tk
import requests
import packaging
import packaging.version
from zipfile import ZipFile
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror, showinfo, askquestion
from cryptography.fernet import Fernet, InvalidToken
from .prestashop import PrestaShopAPI, PrestaShopAPIFilter, PrestaShopAPIError
from .window import Window
from .log import Log
from .settings import Settings
from .download_latest_update import DownloadLatestUpdate
from .functions import thread_function
from .version import __version__

API_KEY_SAVE_FILE = os.path.join(sys.path[0], "api.key")
SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")

GUIDE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/README.md"
LICENSE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/LICENSE"
ISSUES_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/issues"

class GLSWinEXPCheck(Window):

    def __init__(self):
        Window.__init__(self, title=f"Prestashop customer check for GLS Winexpé v{__version__}", width=900, height=600)
        self.menu_bar.add_section("Fichier")
        self.menu_bar.add_section_command("Fichier", "Quitter", self.stop, accelerator="Ctrl+Q")
        self.menu_bar.add_section("Configurer")
        self.menu_bar.add_section_command("Configurer", "Général", lambda page=Settings.GENERAL: self.change_settings(page))
        self.menu_bar.add_section_command("Configurer", "Commandes", lambda page=Settings.ORDERS: self.change_settings(page))
        self.menu_bar.add_section("Aide")
        self.menu_bar.add_section_command("Aide", "Guide d'utilisation", lambda link=GUIDE_LINK: webbrowser.open(link, new=2))
        self.menu_bar.add_section_command("Aide", "Voir la licence", lambda link=LICENSE_LINK: webbrowser.open(link, new=2))
        self.menu_bar.add_section_command("Aide", "Signaler un problème", lambda link=ISSUES_LINK: webbrowser.open(link, new=2))
        self.menu_bar.add_section_separator("Aide")
        self.menu_bar.add_section_command("Aide", "Mise à jour", self.launch_application_update)

        self.update_app = False

        self.prestashop = PrestaShopAPI(id_group_shop=1)
        self.gls_folder = None
        self.open_gls_import_module = "yes"

        self.api_URL = tk.StringVar()
        self.api_key = tk.StringVar()
        self.gls_folder_label = tk.StringVar()
        self.csv_customers = tk.StringVar(value="A définir")
        self.csv_customers_folder = str()
        self.order_state_list = list()
        self.order_select_mode_label = tk.StringVar()
        self.order_select_mode = "nb_last_orders"
        self.all_order_select_modes = {
            "nb_last_orders": "Récupérer les {X} dernières commandes",
            "last_gotten_order_id": "Récupérer toutes les commandes effectués depuis la commande {ID}"
        }
        self.nb_last_orders = 20
        self.last_gotten_order_id = 0
        self.__crypt_key = bytes()

        self.central_frame = tk.Frame(self)
        self.central_frame.grid(row=0, column=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        text_font = ("", 12)
        tk.Label(self.central_frame, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self.central_frame, textvariable=self.api_URL, font=text_font, width=40, state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self.central_frame, textvariable=self.api_key, font=text_font, width=40, state="readonly", show="*").grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Dossier d'installation GLS WinEXPé:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.gls_folder_label, font=text_font).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Fichier clients GLS:", font=text_font).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.csv_customers, font=text_font).grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Choisir", font=text_font, command=self.choose_csv_customers).grid(row=3, column=2, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Mode de sélection des commandes:", font=text_font).grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Message(self.central_frame, textvariable=self.order_select_mode_label, font=text_font, aspect=900).grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)
        self.update_customers_button = tk.Button(self.central_frame, text="Mettre à jour", font=text_font, command=self.update_customers)
        self.update_customers_button.grid(row=5, columnspan=3, padx=10, pady=10)
        self.log = Log(self.central_frame, relief=tk.RIDGE, bd=4)
        self.log.grid(row=6, columnspan=3, padx=10, pady=10, sticky=tk.NSEW)
        self.central_frame.grid_rowconfigure(6, weight=1)

        self.load_settings()
        self.open_api_key_file()
        self.update_stringvars()
        self.settings_toplevel = dict()

        self.all_country_codes = dict()
        self.csv_columns_formatter = {
            "Identifiant": lambda param: param["customer"]["id"],
            "Nom": lambda param: "{firstname} {lastname}".format(**param["address"]),
            "Nom Contact": lambda param: "{firstname} {lastname}".format(**param["address"]),
            "Code Produit": None,
            "COMPTE GLS": None,
            "Chargeur 2": None,
            "Adresse 1": lambda param: param["address"]["address1"],
            "Adresse 2": lambda param: param["address"]["address2"],
            "Adresse 3": None,
            "Code Postal": lambda param: param["address"]["postcode"],
            "Ville": lambda param: param["address"]["city"],
            "Code Pays": lambda param, self=self: self.all_country_codes.get(int(param["address"]["id_country"])),
            "TEL": lambda param: param["address"]["phone"],
            "Mobile": lambda param: param["address"]["phone_mobile"],
            "Note": lambda param: param["customer"]["note"],
            "Mail": lambda param: param["customer"]["email"],
            "Code NUIT": None
        }

    def stop(self):
        self.prestashop.close()
        self.destroy()

    def launch_application_update(self):
        release = self.get_latest_update()
        if release is None or packaging.version.parse(__version__) >= packaging.version.parse(release["tag_name"][1:]):
            showinfo("Mise à jour", "Vous êtes sous la dernière version connue")
            return
        version = release["tag_name"][1:]
        if askquestion("Nouvelle mise à jour", f"Voulez-vous installer la nouvelle version {version} ?") == "no":
            return
        toplevel = DownloadLatestUpdate(self, release["assets"])
        self.wait_window(toplevel)
        try:
            if not toplevel.error_download:
                archive = os.path.join(sys.path[0], f"GLS_WinEXP_check-v{version}.zip")
                gls_model = os.path.join(sys.path[0], f"Prestashop.ini")
                with ZipFile(archive) as zip_file:
                    zip_file.extract("Updater.exe")
                if self.gls_folder and os.path.isdir(os.path.join(self.gls_folder, "DAT", "ConsDscr")):
                    shutil.move(gls_model, os.path.join(self.gls_folder, "DAT", "ConsDscr"))
                else:
                    os.remove(gls_model)
                self.update_app = True
                self.stop()
        except Exception as e:
            showerror(e.__class__.__name__, str(e))

    def get_latest_update(self) -> dict:
        if self.check_github_api_rate_limit() is False:
            return None
        url = "https://api.github.com/repos/francis-clairicia/GLS_WinEXP_check/releases/latest"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            showerror(e.__class__.__name__, str(e))
            return None
        return response.json()

    def check_github_api_rate_limit(self) -> bool:
        url = "https://api.github.com/rate_limit"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            return False
        return bool(response.json()["resources"]["core"]["remaining"] > 0)

    def update_stringvars(self):
        self.api_URL.set(self.prestashop.url or "No API URL")
        self.api_key.set(self.prestashop.key or str())
        self.gls_folder_label.set(self.gls_folder or "No Folder")
        self.order_select_mode_label.set(self.all_order_select_modes[self.order_select_mode].format(X=self.nb_last_orders, ID=self.last_gotten_order_id))

    def open_api_key_file(self):
        self.__crypt_key = Fernet.generate_key()
        if not os.path.isfile(API_KEY_SAVE_FILE):
            return
        try:
            with open(API_KEY_SAVE_FILE, "rb") as file:
                data = pickle.load(file)
        except (IOError, pickle.UnpicklingError):
            return
        if not isinstance(data, tuple) or len(data) != 2:
            return
        self.__crypt_key = data[0]
        fernet = Fernet(self.__crypt_key)
        try:
            api_key = fernet.decrypt(data[1]).decode()
        except InvalidToken:
            return
        self.prestashop.key = api_key

    def save_api_key(self):
        if self.prestashop.key:
            fernet = Fernet(self.__crypt_key)
            encrypted_api_key = fernet.encrypt(self.prestashop.key.encode())
            with open(API_KEY_SAVE_FILE, "wb") as file:
                pickle.dump((self.__crypt_key, encrypted_api_key), file)

    def choose_csv_customers(self):
        csv_file = askopenfilename(
            title="Open CSV file",
            defaultextension='.csv',
            filetypes=[("CSV Files", "*.csv")]
        )
        if csv_file:
            folder, filename = os.path.split(csv_file)
            self.csv_customers.set(filename)
            self.csv_customers_folder = folder.replace("/", "\\")

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read(SETTINGS_FILE)
        self.prestashop.url = config.get("API", "url", fallback=None)
        try:
            self.order_state_list = json.loads(config.get("ORDERS", "order_states", fallback="[]"))
        except json.JSONDecodeError:
            pass
        order_select_mode = config.get("ORDERS", "order_select_mode", fallback=self.order_select_mode)
        if self.order_select_mode in self.all_order_select_modes:
            self.order_select_mode = order_select_mode
        try:
            self.nb_last_orders = config.getint("ORDERS", "nb_last_orders_to_get", fallback=self.nb_last_orders)
        except:
            pass
        try:
            self.last_gotten_order_id = config.getint("ORDERS", "last_gotten_order_id", fallback=self.last_gotten_order_id)
        except:
            pass
        self.gls_folder = config.get("GLS WINEXPE", "location", fallback=None)
        open_gls_import_module = config.get("GLS WINEXPE", "open_gls_import_module", fallback=self.open_gls_import_module)
        if open_gls_import_module in ("yes", "no", "prompt"):
            self.open_gls_import_module = open_gls_import_module

    def save_settings(self):
        settings = {
            "API": {
                "url": self.prestashop.url
            },
            "GLS WINEXPE": {
                "location": self.gls_folder if self.gls_folder else str(),
                "open_gls_import_module": self.open_gls_import_module
            },
            "ORDERS": {
                "order_select_mode": self.order_select_mode,
                "order_states": json.dumps(self.order_state_list),
                "nb_last_orders_to_get": self.nb_last_orders,
                "last_gotten_order_id": self.last_gotten_order_id
            }
        }
        config = configparser.ConfigParser()
        config.read_dict(settings)
        with open(SETTINGS_FILE, "w") as file:
            config.write(file, space_around_delimiters=False)

    def change_settings(self, page: int):
        if page not in self.settings_toplevel:
            self.settings_toplevel[page] = Settings(self, page)
        else:
            self.settings_toplevel[page].focus_set()

    @thread_function
    def update_customers(self):
        self.log.clear()
        self.update_customers_button.configure(state="disabled")
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        try:
            prestashop = self.prestashop
            self.log.print("Checking GLS Folder...")
            if not os.path.isdir(self.gls_folder):
                raise FileNotFoundError(f"Can't find '{self.gls_folder_label.get()}' folder")
            output_folder = os.path.join(self.gls_folder.replace("/", "\\"), "DAT", "CsIMP")
            if not os.path.isdir(output_folder):
                raise FileNotFoundError(f"Can't find '{output_folder}' folder")
            self.log.print(f"Reading '{self.csv_customers.get()}'...")
            csv_file = os.path.join(self.csv_customers_folder, self.csv_customers.get())
            if not os.path.isfile(csv_file):
                raise FileNotFoundError(f"Can't find '{csv_file}' file")
            csv_customers = dict()
            lines_with_errors = 0
            with open(csv_file, "r", newline="") as file:
                reader = csv.DictReader(file, delimiter=";", quoting=csv.QUOTE_NONE)
                for row in reader:
                    try:
                        csv_customers[int(row["Identifiant"])] = {
                            key: value.strip() for key, value in row.items() if key in self.csv_columns_formatter
                        }
                    except (KeyError, ValueError):
                        lines_with_errors += 1
            self.log.print(f"{reader.line_num} lines read, removing the duplicates")
            self.log.print(f"{len(csv_customers)} lines saved ({lines_with_errors} lines not valid)")
            if self.order_select_mode == "nb_last_orders":
                self.log.print(f"Getting the last {self.nb_last_orders} orders...")
                orders = prestashop.get_all(
                    resource="orders",
                    display=["id", "id_customer", "id_address_delivery"],
                    filters={"current_state": PrestaShopAPIFilter.field_in_list(self.order_state_list)},
                    sort={"id": "DESC"},
                    limit=self.nb_last_orders
                )
                orders.sort(key=lambda order: order["id"])
            elif self.order_select_mode == "last_gotten_order_id":
                self.log.print(f"Getting orders with ID greater than {self.last_gotten_order_id}")
                orders = prestashop.get_all(
                    resource="orders",
                    display=["id", "id_customer", "id_address_delivery"],
                    filters={
                        "id": PrestaShopAPIFilter.field_greater_than(self.last_gotten_order_id),
                        "current_state": PrestaShopAPIFilter.field_in_list(self.order_state_list)
                    },
                    sort={"id": "ASC"}
                )
            else:
                orders = list()
            self.log.print(f"{len(orders)} orders selected")
            if orders:
                self.log.print("Getting the delivery addresses list according to the order list...")
                addresses = prestashop.get_all(
                    resource="addresses",
                    display=["id", "firstname", "lastname", "address1", "address2", "postcode", "city", "id_country", "phone", "phone_mobile"],
                    filters={"id": PrestaShopAPIFilter.field_in_list(orders, key=lambda order: order["id_address_delivery"])}
                )
                self.log.print(f"{len(addresses)} addresses gotten")
                self.log.print("Getting the customers infos...")
                customers = prestashop.get_all(
                    resource="customers",
                    display=["id", "note", "email"],
                    filters={"id": PrestaShopAPIFilter.field_in_list(orders, key=lambda order: order["id_customer"])}
                )
                self.log.print("Getting all country codes...")
                self.all_country_codes = {
                    country["id"]: country["iso_code"] for country in prestashop.get_all("countries", display=["id", "iso_code"])
                }
                self.log.print("Linking addresses and customers infos...")
                customer_address_list = [
                    {
                        "customer": list(filter(lambda customer: int(customer["id"]) == int(order["id_customer"]), customers))[0],
                        "address": list(filter(lambda address: int(address["id"]) == int(order["id_address_delivery"]), addresses))[0]
                    } for order in orders
                ]
                self.log.print("Updating customers...")
                for customer_address in customer_address_list:
                    customer_id = customer_address["customer"]["id"]
                    if customer_id not in csv_customers:
                        csv_customers[customer_id] = dict.fromkeys(self.csv_columns_formatter.keys())
                    row = csv_customers[customer_id]
                    for column in row:
                        updater = self.csv_columns_formatter[column]
                        if callable(updater):
                            row[column] = str(updater(customer_address)).strip()
                output = os.path.join(output_folder, "Client_Prestashop.csv")
                self.log.print(f"Save customers in '{output}'")
                with open(output, "w", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=list(self.csv_columns_formatter.keys()), delimiter=";")
                    writer.writeheader()
                    writer.writerows(csv_customers.values())
                self.last_gotten_order_id = max(orders, key=lambda order: order["id"])["id"]
                self.log.print("Update successful")
        except Exception as e:
            error_name = e.__class__.__name__
            error_message = str(e)
            self.log.print(f"{error_name}: {error_message}")
            showerror(error_name, error_message)
        else:
            self.save_settings()
            if not orders:
                showinfo("Mise à jour terminée", "Rien à mettre à jour :)")
            else:
                open_gls_import_module = self.open_gls_import_module
                title = "Mise à jour réussie"
                message = "La mise à jour des clients a été effectuée"
                if open_gls_import_module != "no":
                    if open_gls_import_module == "yes":
                        message += "\n\n" + "Le module d'import de données de GLS WinEXPé sera lancé pour importer les modificiations"
                    elif open_gls_import_module == "prompt":
                        message += "\n\n" + "Voulez-vous lancer le module d'import de données de GLS WinEXPé pour importer les modificiations ?"
                    message += "\n\n" + "P.S.: Vous ne pourrez refaire une mise à jour ou quitter le logiciel que quand la fenêtre du module d'import de GLS sera fermée."
                if open_gls_import_module == "prompt":
                    open_gls_import_module = askquestion(title, message)
                else:
                    showinfo(title, message)
                if open_gls_import_module == "yes":
                    subprocess.run([os.path.join(self.gls_folder, "wxpimport.exe")], stdin=subprocess.DEVNULL)
        finally:
            self.update_customers_button.configure(state="normal")
            self.protocol("WM_DELETE_WINDOW", self.stop)