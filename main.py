import base64
import os
import shutil
import subprocess
import time
import wmi

import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# ==========================================
URL = "https://mangaplus.shueisha.co.jp/viewer/5000869?timestamp=1762770081325"
BASE_PATH = str(Path.home / "Downloads")
# FOLDER_NAME = "Chainsaw Man 219"
# FOLDER_NAME = "One Piece 1165"
FOLDER_NAME = "Jujutsu Kaisen Modulo 10"
# ==========================================


def total_pages_loaded(driver):
    try:
        element = driver.find_element(
            By.CSS_SELECTOR, "p[class^='Viewer-module_pageNumber_'] span"
        )
        text = element.get_attribute("textContent")
        return text != "1 / 0" and text != ""
    except Exception:
        return False


def find_kindle_letter(kindle_name):
    try:
        c = wmi.WMI()

        for drive in c.Win32_LogicalDisk():
            if drive.VolumeName and drive.VolumeName.lower() == kindle_name.lower():
                return drive.DeviceID

    except Exception as e:
        print(f"Erro ao tentar acessar o WMI: {e}")
        return None

    return None


def scroll_until_all_images_loaded(driver, total_pages):
    previous_count = 0
    stable_scrolls = 0
    max_stable_scrolls = 5

    while True:
        imagens = driver.find_elements(By.CSS_SELECTOR, "img.zao-image")
        current_count = len(imagens)
        print(f"Imagens carregadas: {current_count} / {total_pages}")

        if current_count >= total_pages:
            print("✅ Todas as páginas carregadas!")
            break

        if current_count == previous_count:
            stable_scrolls += 1
            print(
                f"🔄 Nenhuma nova imagem. Tentativa {stable_scrolls}/{max_stable_scrolls}"
            )
        else:
            stable_scrolls = 0

        if stable_scrolls >= max_stable_scrolls:
            print("⚠️ Rolagem parece travada. Encerrando tentativa.")
            break

        previous_count = current_count
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
        time.sleep(1)

    print("✅ Rolagem completa")


def baixar_imagens_blob(url: str, base_path: str, folder_name: str):
    pasta_destino = os.path.join(base_path, folder_name)
    os.makedirs(pasta_destino, exist_ok=True)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Firefox(service=service, options=options)

    print("🌐 Acessando página...")
    driver.get(url)
    time.sleep(5)

    wait = WebDriverWait(driver, 15)
    wait.until(total_pages_loaded)

    page_number_p = driver.find_element(
        By.CSS_SELECTOR, "p[class^='Viewer-module_pageNumber_'] span"
    )
    text = page_number_p.get_attribute("textContent")
    total_pages = int(text.split("/")[-1].strip())

    scroll_until_all_images_loaded(driver, total_pages)

    imagens = driver.find_elements(By.CSS_SELECTOR, "img.zao-image")

    if not imagens:
        print("⚠️ Nenhuma imagem encontrada.")
        driver.quit()
        return

    # ------------------------------------------------------------------- ChatGPT fez essa parte aqui -------------------------------------------------------------------
    js_blob_to_base64 = """
    const img = arguments[0];
    const callback = arguments[1];

    try {
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const dataURL = canvas.toDataURL('image/png');
    callback(dataURL);
    } catch (e) {
    callback(null);
    }
    """

    for idx, img in enumerate(imagens, start=1):
        src = img.get_attribute("src")
        nome_arquivo = os.path.join(pasta_destino, f"{idx:02}.png")

        if src.startswith("blob:"):
            # execute_async_script espera callback ser chamado
            data_url = driver.execute_async_script(js_blob_to_base64, img)
            if data_url is None:
                print(f"⚠️ {idx:02}.png não pôde ser baixada do blob.")
                continue
            header, encoded = data_url.split(",", 1)
            data = base64.b64decode(encoded)
            with open(nome_arquivo, "wb") as f:
                f.write(data)
            print(f"📥 {idx:02}.png baixada do blob.")
        elif src.startswith("data:image"):
            header, encoded = src.split(",", 1)
            data = base64.b64decode(encoded)
            with open(nome_arquivo, "wb") as f:
                f.write(data)
            print(f"💾 {idx:02}.png salva de data URL.")
        else:
            img_data = requests.get(src).content
            with open(nome_arquivo, "wb") as f:
                f.write(img_data)
            print(f"🌐 {idx:02}.png baixada de URL direta.")
    # ------------------------------------------------------------------- ChatGPT fez essa parte aqui -------------------------------------------------------------------

    driver.quit()
    print("✅ Todas as imagens foram baixadas com sucesso!")
    generate_mobi(pasta_destino)
    shutil.rmtree(pasta_destino)

    kindle = find_kindle_letter("Kindle")
    caminho_origem = os.path.join(base_path, f"{folder_name}.mobi")
    caminho_destino_pasta = os.path.join(kindle, "documents")
    caminho_destino_final = os.path.join(caminho_destino_pasta, f"{folder_name}.mobi")

    if not os.path.isdir(caminho_destino_pasta):
        print("❌ Kindle nao conectado ao computador")
        return

    if not os.path.exists(caminho_origem):
        print("❌ Erro: falhou ao converter para arquivo mobi")
        raise

    try:
        shutil.move(caminho_origem, caminho_destino_final)
        print(
            f"✅ Sucesso! O arquivo '{folder_name}.mobi' foi movido para: {caminho_destino_final}"
        )
        return True

    except Exception as e:
        print(f"❌ Erro ao mover o arquivo: {e}")
        return False


def generate_mobi(folder_path: str):
    subprocess.call(
        [
            "kcc",
            "K11",
            folder_path,
            "-m",
            "-u",
            "-s",
            "-c",
            "2",
            "-r",
            "1",
            "-f",
            "MOBI",
        ]
    )


if __name__ == "__main__":
    baixar_imagens_blob(URL, BASE_PATH, FOLDER_NAME)
