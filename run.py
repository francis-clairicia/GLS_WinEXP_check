# -*- coding: utf-8 -*

import sys
import time
import json
import csv
from functools import wraps
from prestashop import PrestaShopAPI

WEBSERVICE_LINK = "https://www.atlantic-paintball.fr/api/"
WEBSERVICE_KEY = "1W48RXRVBQ8L89W9XUTNBWWVVTM268F2"

def check_execution_time(function):
    
    @wraps(function)
    def wrapper(*args, **kwargs):
        print("Launching '{func_name}' function".format(func_name=function.__name__))
        start = time.time()
        to_return = function(*args, **kwargs)
        exec_time = time.time() - start
        print("'{func_name}' function execution time: {time} seconds".format(func_name=function.__name__, time=exec_time))
        return to_return
    
    return wrapper

# @check_execution_time
def get_last_addresses_and_customers_who_make_order(prestashop: PrestaShopAPI, limit=10):
    orders = prestashop.get_all("orders", display=["id_customer", "id_address_delivery"], filters={"current_state": 3}, sort={"id": "DESC"}, limit=limit)
    addresses = prestashop.get_all("addresses", display="full", filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_address_delivery"])})
    customers = prestashop.get_all("customers", display="full", filters={"id": PrestaShopAPI.field_in_list(orders, key=lambda order: order["id_customer"])})
    return [{
        "customer": list(filter(lambda customer: int(customer["id"]) == int(order["id_customer"]), customers))[0],
        "address": list(filter(lambda address: int(address["id"]) == int(order["id_address_delivery"]), addresses))[0]
        } for order in orders]

def make_csv_rows(customer_address_list: list, prestashop: PrestaShopAPI) -> dict:
    No_value = iter(range(len(customer_address_list)))
    all_country_codes = {country["id"]: country["iso_code"] for country in prestashop.get_all("countries", display=["id", "iso_code"])}
    columns = {
        "No": lambda param: next(No_value) + 1,
        "Identifiant": lambda param: param["customer"]["id"],
        "Nom": lambda param: "{firstname} {lastname}".format(**param["address"]),
        "Nom Contact": lambda param: "{firstname} {lastname}".format(**param["address"]),
        "Code Produit": lambda param: None,
        "COMPTE GLS": lambda param: None,
        "Chargeur 2": lambda param: 0,
        "Adresse 1": lambda param: param["address"]["address1"],
        "Adresse 2": lambda param: param["address"]["address2"],
        "Adresse 3": lambda param: None,
        "Code Postal": lambda param: param["address"]["postcode"],
        "Ville": lambda param: param["address"]["city"],
        "Code Pays": lambda param: all_country_codes[int(param["address"]["id_country"])],
        "TEL": lambda param: param["address"]["phone"],
        "Mobile": lambda param: param["address"]["phone_mobile"],
        "Note": lambda param: param["customer"]["note"],
        "Mail": lambda param: param["customer"]["email"],
        "Code NUIT": lambda param: 0
    }
    csv_rows = list()
    for obj in customer_address_list:
        csv_rows.append({column_name: column_field(obj) for column_name, column_field in columns.items()})
    return list(columns.keys()), csv_rows

def main():
    prestashop = PrestaShopAPI(WEBSERVICE_LINK, WEBSERVICE_KEY, id_group_shop=1)
    result = get_last_addresses_and_customers_who_make_order(prestashop, limit=10)
    # print(json.dumps(result, indent=4))
    csv_header, csv_rows = make_csv_rows(result, prestashop)
    # print(csv_rows)
    csv_file = "output.csv"
    try:
        with open(csv_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_header, delimiter=";")
            writer.writeheader()
            for row in csv_rows:
                writer.writerow(row)
    except IOError:
        print("I/O error")
    return 0

if __name__ == "__main__":
    sys.exit(main())