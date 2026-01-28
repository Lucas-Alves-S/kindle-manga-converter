import base64

import shutil
from typing import Optional
import os
from PIL import Image
import requests


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
        data_url = driver.execute_async_script(js_blob_to_base64, img)
        if data_url is None:
            return
        header, encoded = data_url.split(",", 1)
        data = base64.b64decode(encoded)
        with open(file_name, "wb") as f:
            f.write(data)
    elif src.startswith("data:image"):
        header, encoded = src.split(",", 1)
        data = base64.b64decode(encoded)
        with open(file_name, "wb") as f:
            f.write(data)
    else:
        img_data = requests.get(src).content
        with open(file_name, "wb") as f:
            f.write(img_data)


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
        raise Exception(f"ERROR - opening images: {e}")

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
