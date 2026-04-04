from .cubari import download as cubari_download
from .shueisha import download as shueisha_download


def font_factory(font: str):
    match font.lower():
        case "shueisha":
            return shueisha_download
        case "cubari":
            return cubari_download

    raise Exception(f"{font} is not configurated yet")
