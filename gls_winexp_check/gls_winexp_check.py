# -*- coding: Utf-8 -*

import os
import sys
import configparser
import csv
import json
import pickle
import webbrowser
import shutil
import tkinter as tk
import requests
import packaging.version
from tkinter.messagebox import showerror, showinfo, askquestion
from cryptography.fernet import Fernet, InvalidToken
from .prestashop import PrestaShopAPI, PrestaShopAPIFilter
from .window import Window
from .log import Log
from .settings import Settings
from .download_latest_update import DownloadLatestUpdate
from .functions import thread_function
from .version import __version__

maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

API_KEY_SAVE_FILE = os.path.join(sys.path[0], "api.key")
SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")
BACKUP_FOLDER = os.path.join(sys.path[0], "backup")
ICON_FILE = os.path.join(sys.path[0], "icon.ico")

GUIDE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/README.md"
LICENSE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/LICENSE"
ISSUES_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/issues"
RELEASE_LINK = f"https://github.com/francis-clairicia/GLS_WinEXP_check/releases/tag/v{__version__}"

class GLSWinEXPCheck(Window):

    def __init__(self):
        Window.__init__(self, title=f"Prestashop customer check for GLS Winexpé v{__version__}", width=900, height=600)
        if os.path.isfile(ICON_FILE):
            self.iconbitmap(ICON_FILE)
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
        self.menu_bar.add_section_command("Aide", "Note de mise à jour", lambda link=RELEASE_LINK: webbrowser.open(link, new=2))
        self.menu_bar.add_section_command("Aide", "Mise à jour", self.launch_application_update)

        self.update_app = False
        self.auto_check_update = False

        self.prestashop = PrestaShopAPI(id_group_shop=1)
        self.gls_folder = None

        self.api_URL = tk.StringVar()
        self.api_key = tk.StringVar()
        self.gls_folder_label = tk.StringVar()
        self.order_state_list = list()
        self.order_select_mode_label = tk.StringVar()
        self.order_select_mode = "nb_last_orders"
        self.all_order_select_modes = {
            "nb_last_orders": "Récupérer les {X} dernières commandes",
            "last_gotten_order_id": "Récupérer toutes les commandes effectués depuis la commande {ID}"
        }
        self.nb_last_orders = 20
        self.last_gotten_order_id = 0

        self.central_frame = tk.Frame(self)
        self.central_frame.grid(row=0, column=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        text_font = ("", 12)
        tk.Label(self.central_frame, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self.central_frame, textvariable=self.api_URL, font=text_font, width=40, state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Dossier d'installation GLS WinEXPé:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.gls_folder_label, font=text_font).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Mode de sélection des commandes:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Message(self.central_frame, textvariable=self.order_select_mode_label, font=text_font, aspect=900).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        self.update_customers_button = tk.Button(self.central_frame, text="Mettre à jour", font=text_font, command=self.update_customers)
        self.update_customers_button.grid(row=3, columnspan=3, padx=10, pady=10)
        self.log = Log(self.central_frame, relief=tk.RIDGE, bd=4)
        self.log.grid(row=4, columnspan=3, padx=10, pady=10, sticky=tk.NSEW)
        self.central_frame.grid_rowconfigure(4, weight=1)

        self.load_settings()
        self.open_api_key_file()
        self.update_stringvars()
        self.settings_toplevel = dict()

        if self.auto_check_update:
            self.after(50, lambda: self.launch_application_update(at_start=True))

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
        self.quit()

    @thread_function
    def launch_application_update(self, at_start=False):
        release = self.get_latest_update()
        if release is None:
            return
        tag = str(release["tag_name"])
        version = tag[tag.find("v") + 1:]
        if release is None or packaging.version.parse(__version__) >= packaging.version.parse(version):
            if not at_start:
                showinfo("Mise à jour", "Vous êtes sous la dernière version connue")
            return
        if askquestion("Nouvelle mise à jour", f"Voulez-vous installer la nouvelle version {version} ?") == "no":
            return
        toplevel = DownloadLatestUpdate(self, release["assets"])
        self.wait_window(toplevel)
        try:
            if not toplevel.error_download:
                gls_model = os.path.join(sys.path[0], "Prestashop.ini")
                if self.gls_folder and os.path.isdir(os.path.join(self.gls_folder, "DAT", "ConsDscr")):
                    if os.path.isfile(os.path.join(self.gls_folder, "DAT", "ConsDscr", os.path.basename(gls_model))):
                        os.remove(os.path.join(self.gls_folder, "DAT", "ConsDscr", os.path.basename(gls_model)))
                    shutil.move(gls_model, os.path.join(self.gls_folder, "DAT", "ConsDscr"))
                else:
                    os.remove(gls_model)
                self.update_app = True
                self.stop()
        except Exception as e:
            showerror(e.__class__.__name__, str(e))

    def get_latest_update(self) -> dict:
        if self.check_github_api_rate_limit() is False:
            return {"tag_name": "v0.0.0"}
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
        except Exception:
            return False
        return bool(response.json()["resources"]["core"]["remaining"] > 0)

    def update_stringvars(self):
        self.api_URL.set(self.prestashop.url or "No API URL")
        self.api_key.set(self.prestashop.key or str())
        self.gls_folder_label.set(self.gls_folder or "No Folder")
        self.order_select_mode_label.set(self.all_order_select_modes[self.order_select_mode].format(X=self.nb_last_orders, ID=self.last_gotten_order_id))

    def open_api_key_file(self):
        if not os.path.isfile(API_KEY_SAVE_FILE):
            return
        try:
            with open(API_KEY_SAVE_FILE, "rb") as file:
                data = pickle.load(file)
        except (IOError, pickle.UnpicklingError):
            return
        if not isinstance(data, tuple) or len(data) != 2:
            return
        fernet = Fernet(data[0])
        try:
            api_key = fernet.decrypt(data[1]).decode()
        except InvalidToken:
            return
        self.prestashop.key = api_key

    def save_api_key(self):
        if self.prestashop.key:
            key = Fernet.generate_key()
            fernet = Fernet(key)
            encrypted_api_key = fernet.encrypt(self.prestashop.key.encode())
            with open(API_KEY_SAVE_FILE, "wb") as file:
                pickle.dump((key, encrypted_api_key), file)
        elif os.path.isfile(API_KEY_SAVE_FILE):
            os.remove(API_KEY_SAVE_FILE)

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
        try:
            self.auto_check_update = config.getboolean("UPDATER", "auto_check_update", fallback=self.auto_check_update)
        except:
            pass

    def save_settings(self):
        settings = {
            "API": {
                "url": self.prestashop.url
            },
            "GLS WINEXPE": {
                "location": self.gls_folder if self.gls_folder else str(),
            },
            "ORDERS": {
                "order_select_mode": self.order_select_mode,
                "order_states": json.dumps(self.order_state_list),
                "nb_last_orders_to_get": self.nb_last_orders,
                "last_gotten_order_id": self.last_gotten_order_id
            },
            "UPDATER": {
                "auto_check_update": "yes" if self.auto_check_update else "no"
            }
        }
        config = configparser.ConfigParser()
        config.read_dict(settings)
        with open(SETTINGS_FILE, "w") as file:
            config.write(file, space_around_delimiters=False)

    def change_settings(self, page: int):
        if page not in self.settings_toplevel:
            try:
                self.settings_toplevel[page] = Settings(self, page)
            except Exception as e:
                showerror(e.__class__.__name__, str(e))
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
            self.log.print("Reading backup of previous update...")
            csv_filename = "Client_Prestashop.csv"
            csv_file = os.path.join(BACKUP_FOLDER, csv_filename)
            csv_customers = dict()
            if not os.path.isdir(BACKUP_FOLDER):
                os.mkdir(BACKUP_FOLDER)
            if not os.path.isfile(csv_file):
                self.log.print("No Backup")
            else:
                lines_with_errors = 0
                with open(csv_file, "r", newline="") as file:
                    reader = csv.DictReader(file, delimiter=";", quoting=csv.QUOTE_NONE)
                    for i, row in enumerate(reader):
                        if i == 0:
                            continue
                        try:
                            csv_customers[int(row["Identifiant"])] = {
                                key: value.strip() if isinstance(value, str) else None
                                for key, value in row.items() if key in self.csv_columns_formatter
                            }
                        except (KeyError, ValueError):
                            lines_with_errors += 1
                self.log.print(f"{reader.line_num - 2} lines read, removing the duplicates")
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
                output = os.path.join(output_folder, csv_filename)
                self.log.print(f"Save customers in '{output}'")
                for filepath in (output, csv_file):
                    with open(filepath, "w", newline="") as file:
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
            self.update_stringvars()
            if not orders:
                showinfo("Mise à jour terminée", "Rien à mettre à jour :)")
            else:
                showinfo("Mise à jour réussie", "La mise à jour des clients a été effectuée")
        finally:
            self.update_customers_button.configure(state="normal")
            self.protocol("WM_DELETE_WINDOW", self.stop)
