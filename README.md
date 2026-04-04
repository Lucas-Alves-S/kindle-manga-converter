# kindle-manga-converter

Downloads manga chapters from supported sources and converts them to `.mobi` for Kindle.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Firefox + geckodriver — required for Selenium-based downloaders

## Setup

```bash
uv sync
```

That's it.

## Usage

```bash
uv run kmc convert --font <font> --url <url> --comic-name <name> [options]
```

### Flags

| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| `--font` | `-f` | yes | Download source to use (see [Available Sources](#available-sources)) |
| `--url` | `-u` | yes | URL of the chapter to download |
| `--comic-name` | `-n` | yes | Name of the folder the chapter will be saved to |
| `--author` | `-a` | no | Author name embedded in the `.mobi` metadata |
| `--path` | `-p` | no | Destination directory (defaults to `~/Downloads`) |
| `--auto-move` | `-m` | no | Automatically move the converted file to the Kindle mount point |
| `--ignore-pages` | `-i` | no | Skip the first N pages before converting (useful for cover/title pages) |

### Example

```bash
uv run kmc convert -f shueisha -u "https://..." -n "one-piece-ch1" -a "Oda" -p ~/manga -m
```

## Available Sources

### `shueisha`

Downloads from [Shueisha's manga viewer](https://mangaplus.shueisha.co.jp/updates). Uses Selenium with a headless Firefox to scroll through the reader and capture each page as a PNG. Handles double-page spreads by joining them horizontally.

### `cubari`

Downloads from [Cubari](https://cubari.moe). Uses Selenium with a headless Firefox to click the download button and wait for the ZIP archive to be saved, then extracts it automatically.
