from pathlib import Path
from typing import Annotated, Optional

import typer

from commom.converter import generate_mobi
from commom.system import move_to_kindle
from fonts.factory import font_factory

app = typer.Typer()


@app.command()
def convert(
    font: Annotated[str, typer.Option("--font", "-f")],
    url: Annotated[str, typer.Option("--url", "-u")],
    comic_name: Annotated[str, typer.Option("--comic-name", "-n")],
    author: Annotated[Optional[str], typer.Option("--author", "-a")] = None,
    download_path: Annotated[Optional[str], typer.Option("--path", "-p")] = None,
    auto_move: Annotated[bool, typer.Option("--auto-move", "-m")] = False,
):
    source = font_factory(font)
    if download_path:
        base_path = Path(download_path)
    else:
        print(
            f"WARNING - No download path provided, falling back to default({Path.home() / 'Downloads'})"
        )
        base_path = Path.home() / "Downloads"
    source(url, base_path, comic_name)

    full_path = str(base_path / comic_name)
    generate_mobi(full_path, author)

    if auto_move:
        move_to_kindle(str(base_path), comic_name)


if __name__ == "__main__":
    app()
