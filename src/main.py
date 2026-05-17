from pathlib import Path
from typing import Annotated, Optional

import typer

from common.converter import generate_mobi
from common.system import move_to_kindle
from sources.factory import source_factory

app = typer.Typer()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


def skip_pages(folder: Path, count: int):
    """Delete the first count images from folder and renumber the remainder from 001."""
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda f: f.name,
    )

    for f in files[:count]:
        f.unlink()
        print(f"INFO - Skipped page: {f.name}")

    remaining = files[count:]
    for i, f in enumerate(remaining, start=1):
        new_name = folder / f"{i:03d}{f.suffix}"
        if f != new_name:
            f.rename(new_name)


@app.command()
def convert(
    source: Annotated[str, typer.Option("--source", "-s")],
    url: Annotated[str, typer.Option("--url", "-u")],
    comic_name: Annotated[str, typer.Option("--comic-name", "-n")],
    author: Annotated[Optional[str], typer.Option("--author", "-a")] = None,
    download_path: Annotated[Optional[str], typer.Option("--path", "-p")] = None,
    auto_move: Annotated[bool, typer.Option("--auto-move", "-m")] = False,
    ignore_pages: Annotated[int, typer.Option("--ignore-pages", "-i")] = 0,
):
    downloader = source_factory(source)
    if download_path:
        base_path = Path(download_path)
    else:
        print(
            f"WARNING - No download path provided, falling back to default({Path.home() / 'Downloads'})"
        )
        base_path = Path.home() / "Downloads"
    downloader(url, base_path, comic_name)

    if ignore_pages > 0:
        skip_pages(base_path / comic_name, ignore_pages)

    full_path = str(base_path / comic_name)
    generate_mobi(full_path, author)

    if auto_move:
        move_to_kindle(str(base_path), comic_name)


if __name__ == "__main__":
    app()
