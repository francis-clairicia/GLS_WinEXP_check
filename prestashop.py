# -*- coding: utf-8 -*

import os
import random
import string
import requests
from typing import Union, Optional, List, Dict, Any

class PrestaShopAPIError(Exception):
    def __init__(self, subject: str, message: str):
        Exception.__init__(self)
        self.subject = subject
        self.message = message

    def __str__(self):
        return f"{self.subject}: {self.message}"

class PrestaShopAPIRequestError(PrestaShopAPIError):
    def __init__(self, url: str, status_code: int, message: str):
        PrestaShopAPIError.__init__(self, "Request Error", f"'{url}' -> {message} (Status code: {status_code})")
        self.url = url
        self.status_code = status_code

class PrestaShopAPI:

    def __init__(self, api_url=None, api_key=None, id_shop=None, id_group_shop=None):
        self.__api_URL = str()
        self.__api_key = None
        self.__session = requests.Session()
        self.__closed = False
        self.__session.headers = {
            "Output-Format": "JSON",
            "User-Agent": "api.prestashop.python/gls-" + "".join(random.sample(string.ascii_letters + string.digits, 32))
        }
        self.url = api_url
        self.key = api_key
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

    @property
    def url(self) -> str:
        return self.__api_URL

    @url.setter
    def url(self, url: str):
        if url is None:
            self.__api_URL = str()
        else:
            url = str(url)
            self.__api_URL = url + ("/" if not url.endswith("/") else "")

    @property
    def key(self) -> str:
        return self.__api_key

    @key.setter
    def key(self, api_key: str):
        if api_key:
            api_key = str(api_key)
            self.__api_key = api_key
            self.__session.auth = (api_key, "")
        else:
            self.__api_key = None
            self.__session.auth = None

    def __get(self, resource: str, id_resource: Optional[Union[int, str]] = None, params: Optional[Dict[str, Any]] = {}) -> Dict[str, Any]:
        URL = self.__api_URL + str(resource) + "/"
        if isinstance(id_resource, (int, str)):
            URL += str(id_resource)
        response = self.__session.request("GET", URL, params=dict(**self.__default_params, **params))
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code != 401:
                raise PrestaShopAPIRequestError(URL, response.status_code, str(e))
        content_type = response.headers["Content-Type"].split(";")[0]
        if (content_type != "application/json"):
            raise PrestaShopAPIRequestError(URL, response.status_code, "Expected 'application/json' content type but got '{result}'".format(result=content_type))
        result = response.json()
        if "errors" in result:
            raise PrestaShopAPIRequestError(URL, response.status_code, result["errors"][0]["message"])
        return result

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
        result = self.__get(resource, params=self.build_params(display=display, filters=filters, sort=sort, limit=limit))
        if isinstance(result, dict):
            result = result[resource]
        return result

    def get(self, resource: str, id: Union[int, str]) -> (Dict[str, Any], None):
        result = self.__get(resource, id)
        result = result[tuple(result.keys())[0]]
        return result