import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def generate_mobi(folder_path: str, author: Optional[str]):
    print("INFO - Beginning conversion process")
    try:
        if platform.system() == "Windows":
            command = "kcc"
        else:
            repo_path = Path.home() / "GitHub/kcc"
            command = str(repo_path / "venv" / "bin" / "kcc-c2e")

        if not author:
            print("WARNING - No author name provided, falling back to default(kcc)")

        if not os.path.exists(command) and platform.system() != "Windows":
            raise Exception(f"ERROR - KCC binary not found: {command}")

        subprocess.call(
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
        )
        print("INFO - Conversion complete!")
    except Exception as e:
        raise Exception(f"ERROR - Check if the comic link is valid - {e}")
    finally:
        shutil.rmtree(folder_path)
