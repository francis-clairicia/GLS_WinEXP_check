# -*- coding: Utf-8 -*

import requests

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

LATEST_RELEASE_URL = "https://api.github.com/repos/francis-clairicia/GLS_WinEXP_check/releases/latest"

response = requests.get(LATEST_RELEASE_URL)
response.raise_for_status()

release = response.json()

for file in release["assets"]:
    print((file["name"], sizeof_fmt(file["size"])))
    # response = requests.get(file["browser_download_url"], stream=True)
    # with open(file["name"], "wb") as stream:
    #     for chunk in response.iter_content(chunk_size=128):
    #         stream.write(chunk)
