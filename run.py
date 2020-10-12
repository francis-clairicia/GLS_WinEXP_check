# -*- coding: utf-8 -*

import sys
from prestashop import PrestaShopAPI
from window import Window

WEBSERVICE_LINK = "https://www.atlantic-paintball.fr/api/"

class GLSWinEXPCheck(Window):
    def __init__(self):
        Window.__init__(self, title="Prestashop customer check for GLS Winexpé")
        self.menu_bar.add_section("Fichier")
        self.menu_bar.add_section_command("Fichier", "Quitter", self.stop, accelerator="Ctrl+Q")

        self.prestashop = PrestaShopAPI.with_api_key_in_file(WEBSERVICE_LINK, id_group_shop=1)

    def stop(self):
        self.prestashop.close()
        self.destroy()

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