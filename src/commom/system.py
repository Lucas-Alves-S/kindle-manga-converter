import os
import platform
import shutil


def find_kindle_letter(kindle_name):
    try:
        import wmi  # type: ignore

        c = wmi.WMI()

        for drive in c.Win32_LogicalDisk():
            if drive.VolumeName and drive.VolumeName.lower() == kindle_name.lower():
                return drive

    except Exception as e:
        raise Exception(f"ERROR - trying to access WMI: {e}")

    return None


def move_to_kindle(base_path: str, folder_name: str):
    print("INFO - Moving file to Kindle")
    system = platform.system()
    if system != "Windows":
        print(f"WARNING - Functionality not yet implemented for {system}")
    else:
        kindle = find_kindle_letter("Kindle")
        if kindle:
            kindle_letter = kindle.DeviceID
            origin_path = os.path.join(base_path, f"{folder_name}.mobi")
            destiny_folder = os.path.join(kindle_letter, "documents")
            destiny_path = os.path.join(destiny_folder, f"{folder_name}.mobi")

            if not os.path.exists(origin_path):
                raise Exception("ERROR - Failed converting .mobi file")

            try:
                shutil.move(origin_path, destiny_path)
                print(f"INFO - File '{folder_name}.mobi' moved to {destiny_path}")

            except Exception as e:
                raise Exception(f"ERROR - Failed to move file: {e}")

            try:
                kindle.Stop()
            except Exception as e:
                raise Exception(f"ERROR - Failed to unmount kinlde: {e}")
