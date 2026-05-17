import os
import platform
import shutil
import subprocess


def find_kindle_windows(kindle_name):
    try:
        import wmi  # type: ignore

        c = wmi.WMI()
        for drive in c.Win32_LogicalDisk():
            if drive.VolumeName and drive.VolumeName.lower() == kindle_name.lower():
                return drive
    except Exception as e:
        raise Exception(f"ERROR - trying to access WMI: {e}")
    return None


def find_kindle_linux(kindle_name):
    """
    Kindles on Linux are typically mounted at:
        /media/<user>/<kindle_name>  (Ubuntu/Debian)
        /run/media/<user>/<kindle_name>  (Fedora/Arch)
    """
    username = os.getenv("USER") or os.getenv("LOGNAME", "")
    search_roots = [
        f"/media/{username}",
        f"/run/media/{username}",
        "/media",
        "/run/media",
    ]
    for root in search_roots:
        candidate = os.path.join(root, kindle_name)
        if os.path.isdir(candidate):
            return candidate
    return None


def move_to_kindle(base_path: str, folder_name: str):
    """Move the generated .mobi to the Kindle's documents folder and unmount the device."""
    print("INFO - Moving file to Kindle")
    system = platform.system()
    origin_path = os.path.join(base_path, f"{folder_name}.mobi")

    if not os.path.exists(origin_path):
        raise Exception("ERROR - Failed converting .mobi file")

    if system == "Windows":
        kindle = find_kindle_windows("Kindle")
        if not kindle:
            raise Exception("ERROR - Kindle not found")

        kindle_letter = kindle.DeviceID
        destination_path = os.path.join(kindle_letter, "documents", f"{folder_name}.mobi")

        try:
            shutil.move(origin_path, destination_path)
            print(f"INFO - File '{folder_name}.mobi' moved to {destination_path}")
        except Exception as e:
            raise Exception(f"ERROR - Failed to move file: {e}")

        try:
            kindle.Stop()
        except Exception as e:
            raise Exception(f"ERROR - Failed to unmount Kindle: {e}")

    elif system == "Linux":
        kindle_path = find_kindle_linux("Kindle")
        if not kindle_path:
            raise Exception(
                "ERROR - Kindle not found, make sure it is connected and mounted"
            )

        destination_path = os.path.join(kindle_path, "documents", f"{folder_name}.mobi")

        try:
            shutil.move(origin_path, destination_path)
            print(f"INFO - File '{folder_name}.mobi' moved to {destination_path}")
        except Exception as e:
            raise Exception(f"ERROR - Failed to move file: {e}")

        try:
            result = subprocess.run(
                ["findmnt", "-n", "-o", "SOURCE", kindle_path],
                capture_output=True,
                text=True,
                check=True,
            )
            device = result.stdout.strip()
            subprocess.run(["udisksctl", "unmount", "-b", device], check=True)
            print("INFO - Kindle unmounted")
        except subprocess.CalledProcessError as e:
            raise Exception(f"ERROR - Failed to unmount Kindle: {e}")

    else:
        print(f"WARNING - Functionality not yet implemented for {system}")
