# -*- coding: utf-8 -*

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
        PrestaShopAPIError.__init__(self, "Request Error", message)
        self.url = url
        self.status_code = status_code

    @classmethod
    def from_prestashop_response(cls, url: str, status_code: int, errors: List[Dict[str, Union[int, str]]]):
        message = f"Can't access to resource at url {url}"
        for error in errors:
            message += "\n" + "- Prestashop error code {code}: {message}".format(**error)
        message += "\n" + f"(Response status code: {status_code})"
        return cls(url, status_code, message)

class PrestaShopAPIFilter:

    @staticmethod
    def field_in_list(iterable, key=None) -> str:
        if not callable(key):
            key = lambda e: e
        return "[" + "|".join(dict.fromkeys(str(key(element)) for element in iterable)) + "]"

    @staticmethod
    def field_not_in_list(iterable, key=None) -> str:
        return "!" + PrestaShopAPIFilter.field_in_list(iterable, key)

    @staticmethod
    def field_equal_to(*values: Union[int, str]) -> str:
        return PrestaShopAPIFilter.field_in_list(values)

    @staticmethod
    def field_not_equal_to(*values: Union[int, str]) -> str:
        return PrestaShopAPIFilter.field_not_in_list(values)

    @staticmethod
    def field_greater_than(value: Union[int, str]) -> str:
        return f">[{value}]"

    @staticmethod
    def field_lower_than(value: Union[int, str]) -> str:
        return f"<[{value}]"

    @staticmethod
    def field_in_range(start: Union[int, str], end: Union[int, str]) -> str:
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

class PrestaShopAPI:

    def __init__(self, api_url=None, api_key=None, id_shop=None, id_group_shop=None):
        self.__api_URL = str()
        self.__api_key = None
        self.__session = requests.Session()
        self.__closed = False
        self.__session.headers = {
            "Output-Format": "JSON",
            "User-Agent": "api.prestashop.python/user-" + "".join(random.sample(string.ascii_letters + string.digits, 32))
        }
        self.url = api_url
        self.key = api_key
        self.__default_params = dict()
        if isinstance(id_group_shop, int):
            self.__default_params["id_group_shop"] = str(id_group_shop)
        elif isinstance(id_shop, int):
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
            self.__api_URL = url + ("/" if url != "" and not url.endswith("/") else "")

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
        try:
            response = self.__session.request("GET", URL, params=dict(**self.__default_params, **params), timeout=10)
        except Exception as e:
            raise PrestaShopAPIRequestError(URL, -1, str(e)) from None
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code != 401 or response.text == "401 Unauthorized":
                raise PrestaShopAPIRequestError(URL, response.status_code, str(e)) from None
        content_type = response.headers["Content-Type"].split(";")[0]
        if (content_type not in ["application/json", "application/vnd.api+json"]):
            raise PrestaShopAPIRequestError(URL, response.status_code, "Expected JSON content type but got '{result}'".format(result=content_type))
        result = response.json()
        if "errors" in result:
            raise PrestaShopAPIRequestError.from_prestashop_response(URL, response.status_code, result["errors"])
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

    def get_all(self, resource: str, display=None, filters=None, sort=None, limit=None) -> List[Dict[str, Any]]:
        result = self.__get(resource, params=self.build_params(display=display, filters=filters, sort=sort, limit=limit))
        if isinstance(result, dict):
            result = result[resource]
        return result

    def get(self, resource: str, id: Union[int, str]) -> Dict[str, Any]:
        result = self.__get(resource, id)
        result = result[tuple(result.keys())[0]]
        return result
