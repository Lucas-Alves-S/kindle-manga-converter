import os
import shutil
import subprocess
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def generate_mobi(folder_path: str, author: Optional[str]):
    print("INFO - Beginning conversion process")
    kcc_path = os.getenv("KCC_PATH")
    if kcc_path:
        command = kcc_path
    else:
        print("WARNING - KCC_PATH not set in .env, falling back to kcc-c2e from PATH")
        command = "kcc-c2e"

    if not author:
        print("WARNING - No author name provided, falling back to default(kcc)")

    try:
        subprocess.run(
            [
                command,
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
                author or "kcc",
                "-f",
                "MOBI",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"ERROR - KCC conversion failed with exit code {e.returncode}")
    except Exception as e:
        raise Exception(f"ERROR - Check if the comic link is valid - {e}")

    print("INFO - Conversion complete!")
    shutil.rmtree(folder_path)
