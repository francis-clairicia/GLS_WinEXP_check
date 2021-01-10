# -*- coding: Utf-8 -*

import tkinter as tk
from tkinter.messagebox import showerror
from tkinter.filedialog import askdirectory
from .prestashop import PrestaShopAPI

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
        self.protocol("WM_DELETE_WINDOW", self.stop)
        self.text_font = text_font = ("", 12)
        self.page = page
        self.api_URL = tk.StringVar(value=self.master.prestashop.url)
        self.api_key = tk.StringVar(value=self.master.prestashop.key)
        if page == Settings.GENERAL:
            self.title("Configuration - Général")
            self.gls_folder = tk.StringVar(value=self.master.gls_folder)
            self.auto_check_update = tk.BooleanVar(value=self.master.auto_check_update)
            prestashop_frame = tk.LabelFrame(self, text="Prestashop")
            prestashop_frame.grid(row=0, columnspan=3, sticky=tk.EW, padx=30)
            tk.Label(prestashop_frame, text="API URL:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Entry(prestashop_frame, textvariable=self.api_URL, font=text_font, width=40).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Label(prestashop_frame, text="API Key:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            self.api_key_entry = tk.Entry(prestashop_frame, textvariable=self.api_key, font=text_font, width=40, show="*")
            self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Button(prestashop_frame, text="Afficher/Cacher", font=text_font, command=self.toogle_key).grid(row=1, column=2, padx=10, pady=10, sticky=tk.W)
            gls_frame = tk.LabelFrame(self, text="GLS WinEXPé")
            gls_frame.grid(row=1, columnspan=3, sticky=tk.EW, padx=30)
            tk.Label(gls_frame, text="Dossier d'installation\nGLS WinEXPé:", font=text_font).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Entry(gls_frame, textvariable=self.gls_folder, font=text_font, width=40, state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
            tk.Button(gls_frame, text="Choisir", font=text_font, command=self.choose_gls_folder).grid(row=0, column=2, padx=10, pady=10)
            updater_frame = tk.LabelFrame(self, text="Mises à jour")
            updater_frame.grid(row=2, columnspan=3, sticky=tk.NSEW, padx=30)
            tk.Checkbutton(updater_frame, text="Vérifier les nouvelles mises à jour au démarrage du logiciel", font=text_font, variable=self.auto_check_update, onvalue=True, offvalue=False).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        elif page == Settings.ORDERS:
            self.title("Configuration - Commandes")
            self.order_state_list = dict()
            self.order_select_mode = tk.StringVar(value=self.master.order_select_mode)
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
            tk.Label(self, text="Mode de selection des commandes:", font=text_font).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            order_select_mode_frame = tk.Frame(self)
            order_select_mode_frame.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
            for i, (select_mode, select_text) in enumerate(self.master.all_order_select_modes.items()):
                tk.Radiobutton(order_select_mode_frame, text=select_text, value=select_mode, variable=self.order_select_mode).grid(row=i, sticky=tk.W)
            tk.Label(self, text="Nombre maximum de commandes\nà récupérer:", font=text_font).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
            tk.Spinbox(self, from_=1, to=50, increment=1, textvariable=self.nb_orders, font=text_font, width=3).grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        tk.Button(self, text="Sauvegarder", font=text_font, command=self.save_and_quit).grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        tk.Button(self, text="Quitter", font=text_font, command=self.stop).grid(row=3, column=1, columnspan=2, padx=10, pady=10)

    def stop(self):
        self.master.settings_toplevel.pop(self.page)
        self.destroy()

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
            self.master.settings_toplevel.pop(self.page, None)
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
                self.master.auto_check_update = self.auto_check_update.get()
            elif self.page == Settings.ORDERS:
                self.master.order_select_mode = self.order_select_mode.get()
                self.master.order_state_list = list(state for state, var in self.order_state_list.items() if var.get())
                self.master.nb_last_orders = int(self.nb_orders.get())
        except Exception as e:
            return showerror(e.__class__.__name__, str(e))
        self.master.save_settings()
        self.master.save_api_key()
        self.master.update_stringvars()
        self.stop()
