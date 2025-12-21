import base64
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# ==========================================
URL = "https://mangaplus.shueisha.co.jp/viewer/5000834"
BASE_PATH = Path.home() / "Downloads"
FOLDER_NAME = "Chainsaw Man 223"
AUTHOR = "Tatsuki Fujimoto"
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
        import wmi

        c = wmi.WMI()

        for drive in c.Win32_LogicalDisk():
            if drive.VolumeName and drive.VolumeName.lower() == kindle_name.lower():
                return drive

    except Exception as e:
        print(f"Erro ao tentar acessar o WMI: {e}")
        return None

    return None


def scroll_until_all_images_loaded(driver, total_pages):
    previous_count = 0
    stable_scrolls = 0
    max_stable_scrolls = 5

    while True:
        imagens = driver.find_elements(By.CLASS_NAME, "zao-pages-container")
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


def download_img(driver, img, src, file_name, idx):
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

    if src.startswith("blob:"):
        # execute_async_script espera callback ser chamado
        data_url = driver.execute_async_script(js_blob_to_base64, img)
        if data_url is None:
            print(f"⚠️ {idx:02}.png não pôde ser baixada do blob.")
            return
        header, encoded = data_url.split(",", 1)
        data = base64.b64decode(encoded)
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"📥 {idx:02}.png baixada do blob.")
    elif src.startswith("data:image"):
        header, encoded = src.split(",", 1)
        data = base64.b64decode(encoded)
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"💾 {idx:02}.png salva de data URL.")
    else:
        img_data = requests.get(src).content
        with open(file_name, "wb") as f:
            f.write(img_data)
        print(f"🌐 {idx:02}.png baixada de URL direta.")


def baixar_imagens_blob(url: str, base_path: str, folder_name: str):
    pasta_destino = os.path.join(base_path, folder_name)
    os.makedirs(pasta_destino, exist_ok=True)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
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
    total_pages = int(text.split("/")[-1].strip()) - 3

    # scroll_until_all_images_loaded(driver, total_pages - 3)

    for index in range(1, total_pages + 1):
        try:
            current_fathers = driver.find_elements(
                By.XPATH,
                "//div[@class='zao-pages-container'][.//div[@class='zao-image-container']]",
            )
            tentativas_scroll = 0
            max_tentativas = 8

            while index > len(current_fathers):
                print(f"⏳ Aguardando carregamento da página {index}...")
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
                    print(
                        f"🛑 Fim do conteúdo alcançado na página {len(current_fathers)}. Encerrando downloads."
                    )
                    break

            if index > len(current_fathers):
                break
            father = current_fathers[index - 1]

            driver.execute_script("arguments[0].scrollIntoView();", father)

            children = father.find_elements(By.CSS_SELECTOR, ".zao-page")
            if len(children) == 1:
                file_name = os.path.join(pasta_destino, f"{index:02}.png")
                img = children[0].find_element(
                    By.CSS_SELECTOR, ".zao-image-container img.zao-image"
                )
                src = img.get_attribute("src")
                download_img(driver, img, src, file_name, index)
            else:
                sub_folder = os.path.join(pasta_destino, f"{index:02}")
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
                    output_folder=pasta_destino,
                    output_filename=f"{index:02}.png",
                )
        except StaleElementReferenceException:
            print(f"⚠️ Elemento da página {index} ficou obsoleto. Tentando recuperar...")
            time.sleep(2)
            index -= 1
            continue

    driver.quit()
    print("✅ Todas as imagens foram baixadas com sucesso!")

    generate_mobi(pasta_destino)
    shutil.rmtree(pasta_destino)

    if platform.system() == "Windows":
        kindle = find_kindle_letter("Kindle")
        if kindle:
            kindle_letter = kindle.DeviceID
            caminho_origem = os.path.join(base_path, f"{folder_name}.mobi")
            caminho_destino_pasta = os.path.join(kindle_letter, "documents")
            caminho_destino_final = os.path.join(
                caminho_destino_pasta, f"{folder_name}.mobi"
            )

            if not os.path.exists(caminho_origem):
                print("❌ Erro: falhou ao converter para arquivo mobi")
                raise

            try:
                shutil.move(caminho_origem, caminho_destino_final)
                print(
                    f"✅ Sucesso! O arquivo '{folder_name}.mobi' foi movido para: {caminho_destino_final}"
                )

            except Exception as e:
                print(f"❌ Erro ao mover o arquivo: {e}")
                raise

            try:
                kindle.Stop()
            except Exception as e:
                print(f"❌ Erro ao desmontar kinlde: {e}")
                raise


def join_images_horizontally(
    folder_path, output_folder: Optional[str], output_filename
):
    image_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith((".png", ".jpg", ".jpeg"))
    ]

    image_files.sort(reverse=True)

    try:
        images = [Image.open(x) for x in image_files]
    except Exception as e:
        print(f"Erro ao abrir imagens: {e}")
        return

    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new("RGB", (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    output_path = os.path.join((output_folder or folder_path), output_filename)
    new_im.save(output_path)
    shutil.rmtree(folder_path)


def generate_mobi(folder_path: str):
    if platform.system() == "Windows":
        comando = "kcc"
    else:
        repo_path = Path.home() / "GitHub/kcc"
        comando = str(repo_path / ".venv" / "bin" / "kcc-c2e")

    if not os.path.exists(comando) and platform.system() != "Windows":
        print(f"❌ Erro: Binário do KCC não encontrado em: {comando}")
        return

    subprocess.call(
        [
            comando,
            "-p",
            "K11",
            folder_path,
            "-m",
            "-u",
            "-r",
            "1",
            "-c",
            "2",
            "-a",
            AUTHOR,
            "-f",
            "MOBI",
        ]
    )


if __name__ == "__main__":
    baixar_imagens_blob(URL, BASE_PATH, FOLDER_NAME)
