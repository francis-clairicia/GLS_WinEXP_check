# -*- coding: utf-8 -*

import sys
from prestashop import PrestaShopAPI, PrestaShopAPIError
import tkinter as tk
from window import Window

WEBSERVICE_LINK = "https://www.atlantic-paintball.fr/api/"

class APIKeyPrompt(tk.Toplevel):
    def __init__(self, master, message: str):
        tk.Toplevel.__init__(self, master)
        self.protocol("WM_DELETE_WINDOW", self.stop)
        self.resizable(width=False, height=False)
        self.title("Error on getting API Key")
        self.transient(master)
        self.quit_window = False

        self.entry = tk.Entry(self, font=("", 15))
        self.entry.bind("Return", lambda event: self.destroy() if len(self.entry.get()) > 0 else None)

        tk.Label(self, text=message, font=("", 20)).grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        tk.Label(self, text="API Key: ", font=("", 15)).grid(row=1, column=0, padx=20, pady=20)
        self.entry.grid(row=1, column=1, padx=20, pady=20)

    def stop(self):
        self.quit_window = True
        self.destroy()

class GLSWinEXPCheck(Window):
    def __init__(self):
        Window.__init__(self, title="Prestashop customer check for GLS Winexpé")
        self.menu_bar.add_section("Fichier")
        self.menu_bar.add_section_command("Fichier", "Quitter", self.stop, accelerator="Ctrl+Q")

        self.prestashop = PrestaShopAPI(WEBSERVICE_LINK, id_group_shop=1)
        self.after(100, self.check_api_key)

    def stop(self):
        self.prestashop.close()
        self.destroy()

    def check_api_key(self):
        try:
            self.prestashop.get_key_from_file()
        except PrestaShopAPIError as e:
            toplevel = APIKeyPrompt(self, e.message + "\n" + "Please enter a new key")
            self.wait_window(toplevel)
            if toplevel.quit_window:
                self.stop()
                return
            try:
                key = toplevel.entry.get()
            except tk.TclError:
                pass
            else:
                self.prestashop.key = key
                self.prestashop.save_api_key()

def main():
    # 
    # result = get_last_addresses_and_customers_who_make_order(prestashop, limit=10)
    # # print(json.dumps(result, indent=4))
    # csv_header, csv_rows = make_csv_rows(result, prestashop)
    # # print(csv_rows)
    # csv_file = "output.csv"
    # try:
    #     with open(csv_file, 'w', newline='') as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=csv_header, delimiter=";")
    #         writer.writeheader()
    #         for row in csv_rows:
    #             writer.writerow(row)
    # except IOError:
    #     print("I/O error")
    window = GLSWinEXPCheck()
    window.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())