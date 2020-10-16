# GLS WinEXP check

A program to check customers' addresses on PrestaShop for GLS' WinEXPé software.

With the Prestashop app webservice and an API Key for authentication,
you can make a CSV file of your customers according to the last orders and import it to the GLS WinEXPé software.

## Usage

Into GLS, export your customers addresses into a CSV file anywhere in your computer.
Launch __GLS WinEXP check__, select that CSV File and click on "__Mettre à jour__" to update the addresses
automatically with your Prestashop web app according to the last orders performed.

By default, the CSV file updated will be in the __{GLS Installation folder}/DAT/CsIMP/__ folder and named "Clients_Prestashop.csv".

## GLS Import Models

In order to use the CSV File created for importing to GLS software, you need the provided model "Prestashop.ini".

This file must be in __{GLS Installation folder}/DAT/ConsDscr/__ folder.

## Configuration

In the "Général" table, you must give the API URL of your Prestashop app, the API Authentication Key, and the GLS installation folder.

This software will only use __GET__ HTTP request method. The API Key must have access to the resources below:
- `addresses`
- `customers`
- `orders`
- `countries`
- `order_states`

See more on [the Prestashop Webservice API](https://devdocs.prestashop.com/1.7/webservice/).
