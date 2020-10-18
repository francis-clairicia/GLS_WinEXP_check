# -*- coding: Utf-8 -*

import os
import sys
import configparser
import csv
import json
import pickle
import webbrowser
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror, showinfo
from io import TextIOBase
from threading import Thread
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
from .prestashop import PrestaShopAPI, PrestaShopAPIError
from .window import Window
from .version import __version__

API_KEY_SAVE_FILE = os.path.join(sys.path[0], "api.key")
SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")

GUIDE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/README.md"
LICENSE_LINK = "https://github.com/francis-clairicia/GLS_WinEXP_check/blob/master/LICENSE"

def unlock_text_widget(function):

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        self.configure(state="normal")
        to_return = function(self, *args, **kwargs)
        self.configure(state="disabled")
        return to_return

    return wrapper

class Log(ScrolledText, TextIOBase):
    def __init__(self, master, *args, **kwargs):
        ScrolledText.__init__(self, master, *args, **kwargs)
        TextIOBase.__init__(self)
        self.configure(state="disabled")

    def print(self, *values, **kwargs):
        return print(*values, **kwargs, file=self)

    @unlock_text_widget
    def clear(self):
        self.delete("1.0", "end")

    @unlock_text_widget
    def write(self, s: str):
        self.insert("end", s)
        return len(s)

class Settings(tk.Toplevel):

    GENERAL = 0
    ORDERS = 1

    def __init__(self, master, page: int):
        tk.Toplevel.__init__(self, master)
        self.master = master
        self.title("Configuration")
        self.transient(master)
        self.focus_set()
        self.resizable(width=False, height=False)
        self.text_font = text_font = ("", 12)
        self.page = page
        self.api_URL = tk.StringVar(value=self.master.prestashop.url)
        self.api_key = tk.StringVar(value=self.master.prestashop.key)
        if page == Settings.GENERAL:
            self.gls_folder = tk.StringVar(value=self.master.gls_folder)
            tk.Label(self, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Entry(self, textvariable=self.api_URL, font=text_font, width=40).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Label(self, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            self.api_key_entry = tk.Entry(self, textvariable=self.api_key, font=text_font, width=40, show="*")
            self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Button(self, text="Afficher/Cacher", font=text_font, command=self.toogle_key).grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
            tk.Label(self, text="Dossier d'installation GLS WinEXPé:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Entry(self, textvariable=self.gls_folder, font=text_font, width=40, state="readonly").grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Button(self, text="Choisir", font=text_font, command=self.choose_gls_folder).grid(row=2, column=2, padx=10, pady=10)
        elif page == Settings.ORDERS:
            self.order_state_list = dict()
            self.nb_orders = tk.StringVar(value=self.master.nb_last_orders)
            tk.Label(self, text="Filtre état des commandes:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            order_state_frame = tk.Frame(self)
            order_state_frame.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
            order_state_canvas = tk.Canvas(order_state_frame)
            order_state_canvas.grid(row=0, column=0, sticky=tk.NSEW)
            order_state_scrollbar = tk.Scrollbar(order_state_frame, orient=tk.VERTICAL, command=order_state_canvas.yview)
            order_state_scrollbar.grid(row=0, column=1, sticky=tk.NS)
            order_state_canvas.configure(yscrollcommand=order_state_scrollbar.set)
            self.order_state_scrollable_frame = tk.Frame(order_state_canvas)
            order_state_canvas.create_window((0, 0), window=self.order_state_scrollable_frame, anchor="nw")
            self.order_state_scrollable_frame.bind("<Configure>", lambda e: order_state_canvas.configure(scrollregion=order_state_canvas.bbox("all")))
            self.lambda_function_mouse_scroll = lambda e: order_state_canvas.yview_scroll(-int(e.delta / abs(e.delta)), tk.UNITS)
            for obj in (order_state_frame, order_state_canvas, self.order_state_scrollable_frame):
                obj.bind("<MouseWheel>", self.lambda_function_mouse_scroll)
            if self.load_order_states_checkbuttons() is False:
                return
            order_state_buttons = tk.Frame(self)
            order_state_buttons.grid(row=0, column=2, padx=10, pady=10)
            tk.Button(order_state_buttons, text="Tout\nsélectionner", font=text_font, command=lambda state=1: self.toogle_order_states(state)).grid(row=0, pady=10)
            tk.Button(order_state_buttons, text="Tout\ndésélectionner", font=text_font, command=lambda state=0: self.toogle_order_states(state)).grid(row=1, pady=10)
            tk.Label(self, text="Nombre maximum de commandes\nà récupérer:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Spinbox(self, from_=1, to=50, increment=1, textvariable=self.nb_orders, font=text_font, width=3).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self, text="Sauvegarder", font=text_font, command=self.save_and_quit).grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        tk.Button(self, text="Quitter", font=text_font, command=self.destroy).grid(row=3, column=1, columnspan=2, padx=10, pady=10)

    def choose_gls_folder(self):
        if self.page == Settings.GENERAL:
            directory = askdirectory(parent=self)
            if directory:
                self.gls_folder.set(directory)

    def toogle_key(self):
        if self.page == Settings.GENERAL:
            self.api_key_entry["show"] = "*" if not self.api_key_entry["show"] else str()

    def load_order_states_checkbuttons(self) -> bool:
        if self.page != Settings.ORDERS:
            return False
        prestashop = PrestaShopAPI(self.api_URL.get(), self.api_key.get(), id_group_shop=1)
        try:
            order_states = prestashop.get_all("order_states", display=["id", "name"], sort={"id": "ASC"})
        except Exception as e:
            self.destroy()
            showerror(e.__class__.__name__, str(e))
            return False
        self.order_state_list = {
            int(order_state["id"]): tk.IntVar(value=1 if int(order_state["id"]) in self.master.order_state_list else 0)
            for order_state in order_states
        }
        for i, order_state in enumerate(order_states):
            state_id = int(order_state["id"])
            state_name = order_state["name"][0]["value"]
            checkbutton = tk.Checkbutton(self.order_state_scrollable_frame, text=state_name, variable=self.order_state_list[state_id])
            checkbutton.grid(row=i, column=0, sticky=tk.W)
            checkbutton.bind("<MouseWheel>", self.lambda_function_mouse_scroll)
        return True

    def toogle_order_states(self, state: int):
        if self.page == Settings.ORDERS:
            for obj in self.order_state_list.values():
                obj.set(state)

    def save_and_quit(self):
        try:
            if self.page == Settings.GENERAL:
                self.master.prestashop.url = self.api_URL.get()
                self.master.prestashop.key = self.api_key.get()
                self.master.gls_folder = self.gls_folder.get()
                self.master.save_api_key()
            elif self.page == Settings.ORDERS:
                self.master.order_state_list = list(state for state, var in self.order_state_list.items() if var.get())
                self.master.nb_last_orders = int(self.nb_orders.get())
        except Exception as e:
            return showerror(e.__class__.__name__, str(e))
        self.master.save_settings()
        self.master.update_stringvars()
        self.destroy()

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

        self.prestashop = PrestaShopAPI(id_group_shop=1)
        self.gls_folder = None

        self.api_URL = tk.StringVar()
        self.api_key = tk.StringVar()
        self.gls_folder_label = tk.StringVar()
        self.csv_customers = tk.StringVar(value="A définir")
        self.csv_customers_folder = str()
        self.order_state_list = list()
        self.nb_last_orders = 20
        self.__crypt_key = bytes()

        self.central_frame = tk.Frame(self)
        self.central_frame.grid(row=0, column=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        text_font = ("", 12)
        tk.Label(self.central_frame, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self.central_frame, textvariable=self.api_URL, font=text_font, width=40, state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.api_key_entry = tk.Entry(self.central_frame, textvariable=self.api_key, font=text_font, width=40, state="readonly", show="*")
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Afficher/Cacher", font=text_font, command=self.toogle_key).grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Dossier d'installation GLS WinEXPé:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.gls_folder_label, font=text_font).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Fichier clients GLS:", font=text_font).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.csv_customers, font=text_font).grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Choisir", font=text_font, command=self.choose_csv_customers).grid(row=3, column=2, padx=10, pady=10, sticky=tk.W)
        self.update_customers_button = tk.Button(self.central_frame, text="Mettre à jour", font=text_font, command=self.update_customers)
        self.update_customers_button.grid(row=4, columnspan=3, padx=10, pady=10)
        self.log = Log(self.central_frame, relief=tk.RIDGE, bd=4)
        self.log.grid(row=5, columnspan=3, padx=10, pady=10, sticky=tk.NSEW)
        self.central_frame.grid_rowconfigure(5, weight=1)

        self.load_settings()
        self.open_api_key_file()
        self.update_stringvars()

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

    def toogle_key(self):
        self.api_key_entry["show"] = "*" if not self.api_key_entry["show"] else str()

    def update_stringvars(self):
        self.api_URL.set(self.prestashop.url if self.prestashop.url else "No API URL")
        self.api_key.set(self.prestashop.key)
        self.gls_folder_label.set(self.gls_folder if self.gls_folder else "No Folder")

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
            self.order_state_list = json.loads(config.get("API", "order_states", fallback="[]"))
        except json.JSONDecodeError:
            pass
        try:
            self.nb_last_orders = config.getint("API", "nb_last_orders_to_get", fallback=self.nb_last_orders)
        except:
            pass
        self.gls_folder = config.get("GLS WINEXPE", "location", fallback=None)

    def save_settings(self):
        settings = {
            "API": {
                "url": self.prestashop.url,
                "order_states": json.dumps(self.order_state_list),
                "nb_last_orders_to_get": self.nb_last_orders
            },
            "GLS WINEXPE": {
                "location": self.gls_folder if self.gls_folder else str()
            }
        }
        config = configparser.ConfigParser()
        config.read_dict(settings)
        with open(SETTINGS_FILE, "w") as file:
            config.write(file, space_around_delimiters=False)

    def change_settings(self, page: int):
        toplevel = Settings(self, page)

    def print_and_update(self, *args, **kwargs):
        self.log.print(*args, **kwargs)
        self.update()

    def update_customers(self):
        self.log.clear()
        self.update_customers_button.configure(state="disabled")
        try:
            prestashop = self.prestashop
            self.print_and_update("Checking GLS Folder...")
            if not os.path.isdir(self.gls_folder):
                raise FileNotFoundError(f"Can't find '{self.gls_folder_label.get()}' folder")
            output_folder = os.path.join(self.gls_folder.replace("/", "\\"), "DAT", "CsIMP")
            if not os.path.isdir(output_folder):
                raise FileNotFoundError(f"Can't find '{output_folder}' folder")
            self.print_and_update(f"Reading '{self.csv_customers.get()}'...")
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
            self.print_and_update(f"{reader.line_num} lines read, removing the duplicates")
            self.print_and_update(f"{len(csv_customers)} lines saved ({lines_with_errors} lines not valid)")
            self.print_and_update(f"Getting the last {self.nb_last_orders} orders...")
            orders = prestashop.get_all(
                resource="orders",
                display=["id_customer", "id_address_delivery"],
                filters={"current_state": PrestaShopAPI.field_in_list(self.order_state_list)},
                sort={"id": "DESC"},
                limit=self.nb_last_orders
            )
            self.print_and_update(f"{len(orders)} orders selected")
            self.print_and_update("Getting the delivery addresses list according to the order list...")
            addresses = prestashop.get_all(
                resource="addresses",
                display=["id", "firstname", "lastname", "address1", "address2", "postcode", "city", "id_country", "phone", "phone_mobile"],
                filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_address_delivery"])}
            )
            self.print_and_update(f"{len(addresses)} addresses gotten")
            self.print_and_update("Getting the customers infos...")
            customers = prestashop.get_all(
                resource="customers",
                display=["id", "note", "email"],
                filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_customer"])}
            )
            self.print_and_update("Getting all country codes...")
            self.all_country_codes = {
                country["id"]: country["iso_code"] for country in prestashop.get_all("countries", display=["id", "iso_code"])
            }
            self.print_and_update("Linking addresses and customers infos...")
            customer_address_list = [
                {
                    "customer": list(filter(lambda customer: int(customer["id"]) == int(order["id_customer"]), customers))[0],
                    "address": list(filter(lambda address: int(address["id"]) == int(order["id_address_delivery"]), addresses))[0]
                } for order in orders
            ]
            self.print_and_update("Updating customers...")
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
            self.print_and_update(f"Save customers in '{output}'")
            with open(output, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(self.csv_columns_formatter.keys()), delimiter=";")
                writer.writeheader()
                writer.writerows(csv_customers.values())
        except Exception as e:
            error_name = e.__class__.__name__
            error_message = str(e)
            self.print_and_update(f"{error_name}: {error_message}")
            showerror(error_name, error_message)
        else:
            self.print_and_update("Update successful")
            showinfo("Update status", "Update done")
        finally:
            self.update_customers_button.configure(state="normal")