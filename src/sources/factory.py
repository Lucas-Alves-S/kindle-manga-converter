from .cubari import download as cubari_download
from .shueisha import download as shueisha_download


def source_factory(source: str):
    match source.lower():
        case "shueisha":
            return shueisha_download
        case "cubari":
            return cubari_download

    raise Exception(f"{source} is not configured yet")
