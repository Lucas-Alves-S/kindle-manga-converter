import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from commom.images import download_img, join_images_horizontally


def total_pages_loaded(driver):
    try:
        element = driver.find_element(
            By.CSS_SELECTOR, "p[class^='Viewer-module_pageNumber_'] span"
        )
        text = element.get_attribute("textContent")
        return text != "1 / 0" and text != ""
    except Exception:
        return False


def scroll_until_all_images_loaded(driver, total_pages):
    previous_count = 0
    stable_scrolls = 0
    max_stable_scrolls = 5

    while True:
        imagens = driver.find_elements(By.CLASS_NAME, "zao-pages-container")
        current_count = len(imagens)

        if current_count >= total_pages:
            break

        if current_count == previous_count:
            stable_scrolls += 1

        else:
            stable_scrolls = 0

        if stable_scrolls >= max_stable_scrolls:
            break

        previous_count = current_count
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
        time.sleep(1)


def download(url: str, base_path: Path, folder_name: str):
    destiny_folder = os.path.join(base_path, folder_name)
    os.makedirs(destiny_folder, exist_ok=True)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    service = Service()
    driver = webdriver.Firefox(service=service, options=options)

    print("INFO - Downloading comic")
    driver.get(url)
    time.sleep(5)

    wait = WebDriverWait(driver, 15)
    wait.until(total_pages_loaded)

    page_number_p = driver.find_element(
        By.CSS_SELECTOR, "p[class^='Viewer-module_pageNumber_'] span"
    )
    text = page_number_p.get_attribute("textContent") or ""
    total_pages = int(text.split("/")[-1].strip()) - 2

    for index in range(1, total_pages + 1):
        try:
            current_fathers = driver.find_elements(
                By.XPATH,
                "//div[@class='zao-pages-container'][.//div[@class='zao-image-container']]",
            )
            tentativas_scroll = 0
            max_tentativas = 8

            while index > len(current_fathers):
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                time.sleep(1.5)
                new_fathers = driver.find_elements(
                    By.XPATH,
                    "//div[@class='zao-pages-container'][.//div[@class='zao-image-container']]",
                )

                if len(new_fathers) == len(current_fathers):
                    tentativas_scroll += 1
                else:
                    tentativas_scroll = 0

                current_fathers = new_fathers

                if tentativas_scroll >= max_tentativas:
                    break

            if index > len(current_fathers):
                break
            father = current_fathers[index - 1]

            driver.execute_script("arguments[0].scrollIntoView();", father)

            children = father.find_elements(By.CSS_SELECTOR, ".zao-page")
            if len(children) == 1:
                file_name = os.path.join(destiny_folder, f"{index:02}.png")
                img = children[0].find_element(
                    By.CSS_SELECTOR, ".zao-image-container img.zao-image"
                )
                src = img.get_attribute("src")
                download_img(driver, img, src, file_name, index)
            else:
                sub_folder = os.path.join(destiny_folder, f"{index:02}")
                os.makedirs(sub_folder, exist_ok=True)
                for new_index, sibling in enumerate(children, start=1):
                    file_name = os.path.join(sub_folder, f"{new_index:02}.png")
                    img = sibling.find_element(
                        By.CSS_SELECTOR, ".zao-image-container img.zao-image"
                    )
                    src = img.get_attribute("src")
                    download_img(driver, img, src, file_name, new_index)
                join_images_horizontally(
                    sub_folder,
                    output_folder=destiny_folder,
                    output_filename=f"{index:02}.png",
                )
        except StaleElementReferenceException:
            time.sleep(2)
            index -= 1
            continue

    driver.quit()
    print("INFO - Download complete!")
