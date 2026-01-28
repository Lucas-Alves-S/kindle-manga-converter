from .shueisha import download as shueisha_download


def font_factory(font: str):
    match font.lower():
        case "shueisha":
            return shueisha_download

    raise Exception(f"{font} is not configurated yet")
