# -*- coding: utf-8 -*

import os
import sys
import configparser
import csv
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showerror, showinfo
from io import TextIOBase
from threading import Thread
from cryptography.fernet import Fernet, InvalidToken
from prestashop import PrestaShopAPI, PrestaShopAPIError
from window import Window

WEBSERVICE_LINK = "https://www.atlantic-paintball.fr/api/"
API_KEY_SAVE_FILE = os.path.join(sys.path[0], "api.key")
SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")

def get_filename(path: str):
    head, tail = os.path.split(path)
    return tail or os.path.basename(head)

class Log(ScrolledText, TextIOBase):
    def __init__(self, master, *args, **kwargs):
        ScrolledText.__init__(self, master, *args, **kwargs)
        TextIOBase.__init__(self)
        self.configure(state="disabled")

    def print(self, *values, **kwargs):
        return print(*values, **kwargs, file=self)

    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")

    def write(self, s: str):
        self.configure(state="normal")
        self.insert("end", s)
        self.configure(state="disabled")
        return len(s)

class Settings(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.master = master
        self.title("Configuration")
        self.focus_set()
        self.resizable(width=False, height=False)
        text_font = ("", 12)
        self.api_URL = tk.StringVar(value=self.master.prestashop.url)
        self.api_key = tk.StringVar(value=self.master.prestashop.key)
        self.gls_folder = tk.StringVar(value=self.master.gls_folder)
        tk.Label(self, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self, textvariable=self.api_URL, font=text_font, width=40).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self, textvariable=self.api_key, font=text_font, width=40).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self, text="GLS Folder:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Entry(self, textvariable=self.gls_folder, font=text_font, width=40, state="readonly").grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self, text="Choisir", font=text_font, command=self.choose_gls_folder).grid(row=2, column=2, padx=10, pady=10)
        tk.Button(self, text="Sauvegarder", font=text_font, command=self.save_and_quit).grid(row=3, columnspan=3, padx=10, pady=10)

    def choose_gls_folder(self):
        self.gls_folder.set(askdirectory(parent=self))

    def save_and_quit(self):
        self.master.prestashop.url = self.api_URL.get()
        self.master.prestashop.key = self.api_key.get()
        self.master.gls_folder = self.gls_folder.get()
        self.master.save_settings()
        self.master.save_api_key()
        self.destroy()

class GLSWinEXPCheck(Window):

    __crypt_key = b'5h2mNznxqzsh8pwr-LxBCu_68VXILaejCibEgYS1F6w='

    def __init__(self):
        Window.__init__(self, title="Prestashop customer check for GLS Winexpé")
        self.menu_bar.add_section("Fichier")
        self.menu_bar.add_section_command("Fichier", "Quitter", self.stop, accelerator="Ctrl+Q")
        self.menu_bar.add_command("Configurer", self.change_settings)

        self.prestashop = PrestaShopAPI(id_group_shop=1)
        self.gls_folder = None

        self.api_URL = tk.StringVar()
        self.api_key = tk.StringVar()
        self.gls_folder_label = tk.StringVar()
        self.csv_customers = tk.StringVar(value="A définir")
        self.csv_customers_folder = str()
        self.show_key = False

        self.central_frame = tk.Frame(self)
        self.central_frame.grid(row=0, column=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        text_font = ("", 12)
        tk.Label(self.central_frame, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.api_URL, font=text_font).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.api_key, font=text_font).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Afficher/Cacher", font=text_font, command=self.toogle_key).grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="GLS WinEXPé Folder:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.gls_folder_label, font=text_font).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, text="Fichier clients GLS:", font=text_font).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        tk.Label(self.central_frame, textvariable=self.csv_customers, font=text_font).grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Choisir", font=text_font, command=self.choose_csv_customers).grid(row=3, column=2, padx=10, pady=10, sticky=tk.W)
        tk.Button(self.central_frame, text="Mettre à jour", font=text_font, command=self.update_customers).grid(row=4, columnspan=3, padx=10, pady=10)
        self.log = Log(self.central_frame)
        self.log.grid(row=5, columnspan=3, padx=10, pady=10, sticky=tk.NSEW)
        self.central_frame.grid_rowconfigure(5, weight=1)

        self.load_settings()
        self.open_api_key_file()
        self.refresh_functions.append(self.update_stringvars)

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
        self.show_key = not self.show_key

    def update_stringvars(self):
        self.api_URL.set(self.prestashop.url if self.prestashop.url else "No API URL")
        if self.show_key:
            self.api_key.set(self.prestashop.key if self.prestashop.key else "No API Key")
        else:
            self.api_key.set("".join("*" for _ in range(len(self.prestashop.key))) if self.prestashop.key else "No API Key")
        self.gls_folder_label.set(self.gls_folder if self.gls_folder else "No Folder")

    def open_api_key_file(self):
        if not os.path.isfile(API_KEY_SAVE_FILE):
            return
        fernet = Fernet(self.__crypt_key)
        try:
            with open(API_KEY_SAVE_FILE, "rb") as file:
                data = file.read()
        except IOError:
            return
        try:
            api_key = fernet.decrypt(data).decode()
        except InvalidToken:
            return
        self.prestashop.key = api_key

    def save_api_key(self):
        if self.prestashop.key:
            fernet = Fernet(self.__crypt_key)
            encrypted_api_key = fernet.encrypt(self.prestashop.key.encode())
            with open(API_KEY_SAVE_FILE, "wb") as file:
                file.write(encrypted_api_key)

    def choose_csv_customers(self):
        csv_file = askopenfilename(
            title="Open CSV file",
            defaultextension='.csv',
            filetypes=[("CSV Files", "*.csv")]
        )
        if csv_file is not None and len(csv_file) > 0:
            folder, filename = os.path.split(csv_file)
            self.csv_customers.set(filename)
            self.csv_customers_folder = folder.replace("/", "\\")

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read(SETTINGS_FILE)
        self.prestashop.url = config.get("API", "URL", fallback=None)
        self.gls_folder = config.get("GLS WINEXPE", "location", fallback=None)

    def save_settings(self):
        settings = {
            "API": {"URL": self.prestashop.url},
            "GLS WINEXPE": {"location": self.gls_folder if self.gls_folder else str()}
        }
        config = configparser.ConfigParser()
        config.read_dict(settings)
        with open(SETTINGS_FILE, "w") as file:
            config.write(file, space_around_delimiters=False)

    def change_settings(self):
        toplevel = Settings(self)

    def update_customers(self):
        thread = Thread(target=self.update_customers_thread)
        thread.start()

    def update_customers_thread(self):
        self.log.clear()
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
            with open(csv_file, "r", newline="") as file:
                reader = csv.DictReader(file, delimiter=";")
                for row in reader:
                    row.pop("No", None)
                    if any(key not in self.csv_columns_formatter for key in row):
                        continue
                    try:
                        csv_customers[int(row["Identifiant"])] = row
                    except:
                        continue
            nb_last_orders = 20
            self.log.print(f"Getting the last {nb_last_orders} orders...")
            orders = prestashop.get_all(
                "orders",
                display=["id_customer", "id_address_delivery"],
                filters={"current_state": "[3|4]"},
                sort={"id": "DESC"},
                limit=nb_last_orders
            )
            self.log.print("Getting the delivery addresses list...")
            addresses = prestashop.get_all(
                "addresses",
                display=["id", "firstname", "lastname", "address1", "address2", "postcode", "city", "id_country", "phone", "phone_mobile"],
                filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_address_delivery"])}
            )
            self.log.print("Getting the customer infos...")
            customers = prestashop.get_all(
                "customers",
                display=["id", "note", "email"],
                filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_customer"])}
            )
            self.log.print("Getting all country codes...")
            self.all_country_codes = {
                country["id"]: country["iso_code"] for country in prestashop.get_all("countries", display=["id", "iso_code"])
            }
            self.log.print("Linking addresses and customer infos...")
            customer_address_list = [{
                "customer": list(filter(lambda customer: int(customer["id"]) == int(order["id_customer"]), customers))[0],
                "address": list(filter(lambda address: int(address["id"]) == int(order["id_address_delivery"]), addresses))[0]
                } for order in orders]
            self.log.print("Updating customers...")
            for customer_address in customer_address_list:
                customer_id = customer_address["customer"]["id"]
                if customer_id not in csv_customers:
                    csv_customers[customer_id] = dict.fromkeys(self.csv_columns_formatter.keys())
                row = csv_customers[customer_id]
                for column in row:
                    updater = self.csv_columns_formatter[column]
                    if callable(updater):
                        row[column] = str(updater(customer_address))
            self.log.print("Trim any whitespaces...")
            for row in csv_customers.values():
                for column in row:
                    if isinstance(row[column], str):
                        row[column] = row[column].strip()
            output = os.path.join(output_folder, "Client_Prestashop.csv")
            self.log.print(f"Save customers in '{output}'")
            with open(output, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(self.csv_columns_formatter.keys()), delimiter=";")
                writer.writeheader()
                writer.writerows(csv_customers.values())
        except Exception as e:
            error_name = e.__class__.__name__
            error_message = str(e)
            self.log.print(f"{error_name}: {error_message}")
            showerror(error_name, error_message)
        else:
            self.log.print("Update successful")
            showinfo("Update status", "Update done")

def main():
    window = GLSWinEXPCheck()
    window.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())