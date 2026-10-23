# scrubname

Strip region and revision tags from ROM filenames, leaving just the game name.

```
Super Mario World (USA) (Rev 1).sfc          ->  Super Mario World.sfc
Pokemon - Red Version (USA, Europe) [!].zip  ->  Pokemon - Red Version.zip
Metroid (Europe) (En,Fr).nes                 ->  Metroid.nes
Final Fantasy VII (USA) (Disc 1).chd         ->  Final Fantasy VII (Disc 1).chd
```

## Install

Download the binary for your OS from the [latest release](https://github.com/SamuelArther/scrubname/releases/latest) and put it somewhere on your `PATH`. On Windows, rename `scrubname-windows.exe` to `scrubname.exe`.

Or, with Python 3.9+:

```
pip install git+https://github.com/SamuelArther/scrubname
```

## Usage

```
cd path/to/roms
scrubname
```

scrubname lists every rename it plans and asks for confirmation before touching anything.

| Option | Description |
| --- | --- |
| `DIRECTORY` | Folder to scan (default: current folder) |
| `-r`, `--recursive` | Include subfolders |
| `-n`, `--dry-run` | Show the changes without renaming |
| `-y`, `--yes` | Rename without asking |
| `--version` | Print the version |

## Behavior

- Every `(...)` and `[...]` tag is removed, except disc and track markers such as `(Disc 1)` and `(Track 02)`, so multi-part games keep distinct names.
- If two files would end up with the same name (for example `Tetris (World).gb` and `Tetris (Japan).gb`), the first is renamed and the rest are skipped with a warning. Nothing is ever overwritten.
- When `.bin` tracks are renamed, the `FILE` lines in the matching `.cue` sheet are updated so the game still loads.
- Archives (`.zip`, `.7z`, `.rar`) are renamed, but their contents are left alone.
- Only ROM, disc image and archive extensions are touched. Other files are ignored.

There is no undo, so run with `-n` first on a large collection.

## License

[MIT](LICENSE)
