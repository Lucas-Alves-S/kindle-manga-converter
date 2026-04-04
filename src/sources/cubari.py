import os
import time
import zipfile
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def download(url: str, base_path: Path, folder_name: str):
    destiny_folder = base_path / folder_name
    os.makedirs(destiny_folder, exist_ok=True)

    existing_zips = set(base_path.glob("*.zip"))

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", str(base_path))
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/zip,application/x-zip-compressed,application/octet-stream",
    )
    options.set_preference("browser.download.manager.showWhenStarting", False)

    service = Service()
    driver = webdriver.Firefox(service=service, options=options)

    print("INFO - Opening cubari page")
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    download_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".ico-btn.download"))
    )
    download_btn.click()

    print("INFO - Waiting for download to complete...")
    timeout = 300
    elapsed = 0
    downloaded_file = None

    while elapsed < timeout:
        time.sleep(2)
        elapsed += 2
        current_zips = set(base_path.glob("*.zip"))
        new_zips = current_zips - existing_zips
        complete = [f for f in new_zips if not f.name.endswith(".part")]
        if complete:
            downloaded_file = complete[0]
            break

    driver.quit()

    if not downloaded_file:
        raise Exception("ERROR - Download timed out or no ZIP file found")

    zip_path = base_path / f"{folder_name}.zip"
    if downloaded_file != zip_path:
        os.rename(downloaded_file, zip_path)

    print("INFO - Extracting archive...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(destiny_folder)
    os.remove(zip_path)

    print("INFO - Download and extraction complete!")
