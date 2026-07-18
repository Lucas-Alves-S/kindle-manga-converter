import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

IMAGE_URL_PATTERN = re.compile(r'data-src="(https://cdn\.mangaflair\.com/[^"]+)"')


def download(url: str, base_path: Path, folder_name: str):
    """Fetch a mangaflair chapter page and download each page image into folder_name."""
    destination_folder = os.path.join(base_path, folder_name)
    os.makedirs(destination_folder, exist_ok=True)

    headers = {"User-Agent": USER_AGENT}

    print("INFO - Fetching chapter page")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    image_urls = list(dict.fromkeys(IMAGE_URL_PATTERN.findall(response.text)))
    if not image_urls:
        raise Exception("ERROR - No page images found on mangaflair page")

    print(f"INFO - Found {len(image_urls)} pages, downloading")
    for index, image_url in enumerate(image_urls, start=1):
        ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
        file_name = os.path.join(destination_folder, f"{index:03d}{ext}")

        img_response = requests.get(image_url, headers=headers, timeout=30)
        img_response.raise_for_status()
        with open(file_name, "wb") as f:
            f.write(img_response.content)
        print(f"INFO - Downloaded page {index:03d}")

    print("INFO - Download complete!")
