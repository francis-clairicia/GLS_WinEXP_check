# -*- coding: utf-8 -*

import os
import random
import string
import requests
from typing import Union, Optional, List, Dict, Any
from cryptography.fernet import Fernet, InvalidToken

class PrestaShopAPI:

    def __init__(self, api_url: str, api_key: str, id_shop=None, id_group_shop=None):
        self.__api_URL = str(api_url) + ("/" if not str(api_url).endswith("/") else "")
        self.__api_key = str(api_key)
        self.__session = requests.Session()
        self.__closed = False
        self.__session.auth = (self.__api_key, "")
        self.__session.headers = {
            "Output-Format": "JSON",
            "User-Agent": "api.prestashop.python/gls-" + "".join(random.sample(string.ascii_letters + string.digits + string.punctuation, 32))
        }
        self.__default_params = dict()
        if isinstance(id_group_shop, (int, str)):
            self.__default_params["id_group_shop"] = str(id_group_shop)
        elif isinstance(id_shop, (int, str)):
            self.__default_params["id_shop"] = str(id_shop)

    def __del__(self):
        self.close()

    def close(self):
        if not self.__closed:
            self.__session.close()
            self.__closed = True

    @staticmethod
    def crypt_key() -> bytes:
        return b'5h2mNznxqzsh8pwr-LxBCu_68VXILaejCibEgYS1F6w='

    @classmethod
    def with_api_key_in_file(cls, api_url: str, api_key_file="api.key", id_shop=None, id_group_shop=None):
        if not os.path.isfile(api_key_file):
            raise FileNotFoundError(f"{api_key_file} doesn't exists.")
        key = PrestaShopAPI.crypt_key()
        fernet = Fernet(key)
        with open(api_key_file, "rb") as file:
            data = file.read()
        api_key = fernet.decrypt(data).decode()
        return cls(api_url, api_key, id_shop, id_group_shop)

    def save_api_key(self):
        key = PrestaShopAPI.crypt_key()
        fernet = Fernet(key)
        encrypted_api_key = fernet.encrypt(self.__api_key.encode())
        with open("api.key", "wb") as file:
            file.write(encrypted_api_key)

    @property
    def key(self) -> str:
        return self.__api_key

    def __get(self, resource: str, id_resource: Optional[Union[int, str]] = None, params: Optional[Dict[str, Any]] = {}) -> requests.Response:
        URL = self.__api_URL + str(resource) + "/"
        if isinstance(id_resource, (int, str)):
            URL += str(id_resource)
        params_for_api = self.__default_params.copy()
        params_for_api.update(params)
        response = self.__session.request("GET", URL, params=params_for_api)
        response.raise_for_status()
        content_type = response.headers["Content-Type"].split(";")[0]
        if (content_type != "application/json"):
            raise TypeError("Expected 'application/json' content type but got '{result}'".format(result=content_type))
        return response

    @staticmethod
    def build_params(display=None, filters=None, sort=None, limit=None) -> Dict[str, str]:
        params = dict()
        if isinstance(display, str):
            if display == "full":
                params["display"] = "full"
            else:
                params["display"] = f"[{display}]"
        elif isinstance(display, (list, tuple)):
            params["display"] = "[" + ",".join(str(field) for field in display) + "]"
        if isinstance(filters, dict):
            for field, pattern in filters.items():
                params[f"filter[{field}]"] = pattern
        if isinstance(sort, dict) and all(order.upper() in ("ASC", "DESC") for order in sort.values()):
            params["sort"] = "[" + ",".join(f"{field}_{order.upper()}" for field, order in sort.items()) + "]"
        if isinstance(limit, int):
            params["limit"] = str(limit)
        elif isinstance(limit, (list, tuple)) and len(limit) == 2:
            params["limit"] = "{0},{1}".format(*limit)
        return params

    @staticmethod
    def field_in_list(iterable, key=None) -> str:
        if not callable(key):
            key = lambda e: e
        return "[" + "|".join(dict.fromkeys(str(key(element)) for element in iterable)) + "]"

    @staticmethod
    def field_in_range(start: int, end: int) -> str:
        return f"[{start},{end}]"

    @staticmethod
    def field_starts_with(pattern: str) -> str:
        return f"[{pattern}]%"

    @staticmethod
    def field_ends_with(pattern: str) -> str:
        return f"%[{pattern}]"

    @staticmethod
    def field_contains(pattern: str) -> str:
        return f"%[{pattern}]%"

    def get_all(self, resource: str, display=None, filters=None, sort=None, limit=None) -> List[Dict[str, Any]]:
        try:
            response = self.__get(resource, params=self.build_params(display=display, filters=filters, sort=sort, limit=limit))
        except (requests.HTTPError, TypeError) as e:
            print(f"Error on searching {resource}: {e}")
            return list()
        result = response.json()
        if "errors" in result:
            return list()
        if isinstance(result, dict):
            result = result[resource]
        return result

    def get(self, resource: str, id: Union[int, str]) -> (Dict[str, Any], None):
        try:
            response = self.__get(resource, id)
        except (requests.HTTPError, TypeError) as e:
            print(f"Error on searching {resource}/{id}: {e}")
            return None
        result = response.json()
        if "errors" in result:
            return None
        result = result[tuple(result.keys())[0]]
        return result