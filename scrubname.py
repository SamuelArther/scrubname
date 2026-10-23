"""scrubname - strip region/revision tags from ROM filenames.

    "Super Mario World (USA) (Rev 1).sfc"  ->  "Super Mario World.sfc"
    "Pokemon - Red Version (USA, Europe) [!].zip"  ->  "Pokemon - Red Version.zip"

Every (...) and [...] group is removed except disc/track markers such as
"(Disc 1)" or "(Track 02)", which are kept so multi-part games don't collide. When a .bin
referenced by a .cue is renamed, the .cue's FILE lines are rewritten to match.
"""

import argparse
import os
import re
import sys
from pathlib import Path

__version__ = "1.0.0"

ROM_EXTS = {
    # archives
    ".zip", ".7z", ".rar",
    # Nintendo
    ".nes", ".fds", ".unf", ".unif", ".sfc", ".smc", ".fig", ".swc", ".bs",
    ".n64", ".z64", ".v64", ".ndd", ".gb", ".gbc", ".gba", ".agb", ".vb",
    ".nds", ".dsi", ".3ds", ".cia", ".cci", ".cxi", ".gcm", ".gcz", ".rvz",
    ".wbfs", ".wad", ".wua", ".wux", ".rpx", ".xci", ".nsp", ".min",
    # Sega
    ".sms", ".gg", ".sg", ".md", ".gen", ".smd", ".32x", ".gdi", ".cdi",
    # Sony / disc images
    ".iso", ".cue", ".bin", ".img", ".chd", ".cso", ".pbp", ".mdf", ".mds",
    ".ccd", ".sub", ".m3u",
    # other systems
    ".a26", ".a52", ".a78", ".j64", ".lnx", ".pce", ".sgx", ".ngp", ".ngc",
    ".ws", ".wsc", ".col", ".int", ".vec", ".st", ".adf", ".d64", ".t64",
    ".tap", ".prg", ".crt", ".rom", ".mx1", ".mx2", ".dsk",
}

TAG = re.compile(r"\s*(\([^()]*\)|\[[^\[\]]*\])")
KEEP_TAG = re.compile(r"^\((disc|disk|cd|side|tape|track)\s+[\w ]+\)$", re.IGNORECASE)
CUE_FILE = re.compile(r'^(\s*FILE\s+)"([^"]+)"(.*)$', re.IGNORECASE)


def scrub(stem: str) -> str:
    """Return the stem with every non-disc tag removed."""
    cleaned = TAG.sub(lambda m: m.group(0) if KEEP_TAG.match(m.group(1)) else "", stem)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .-_")
    return cleaned or stem


def find_roms(root: Path, recursive: bool):
    walker = root.rglob("*") if recursive else root.iterdir()
    return sorted(p for p in walker if p.is_file() and p.suffix.lower() in ROM_EXTS)


def plan_renames(files):
    """Map old path -> new path, skipping anything that would collide."""
    plan, skipped = {}, []
    taken = {str(p).lower() for p in files}
    for path in files:
        new_name = scrub(path.stem) + path.suffix
        if new_name == path.name:
            continue
        target = path.with_name(new_name)
        key = str(target).lower()
        same_file = key == str(path).lower()  # case-only change
        if not same_file and key in taken:
            skipped.append((path, target))
            continue
        taken.discard(str(path).lower())
        taken.add(key)
        plan[path] = target
    return plan, skipped


def rewrite_cues(plan):
    """Point each .cue's FILE lines at the renamed tracks. Returns count fixed."""
    renamed = {old.name.lower(): new.name for old, new in plan.items()}
    folders = {new.parent for new in plan.values()}
    cues = [cue for folder in folders for cue in folder.glob("*.cue")]

    fixed = 0
    for cue in cues:
        raw = cue.read_bytes()
        text = raw.decode("utf-8", errors="surrogateescape")
        changed = False
        lines = []
        for line in text.splitlines(keepends=True):
            m = CUE_FILE.match(line.rstrip("\r\n"))
            if m and m.group(2).lower() in renamed:
                ending = line[len(line.rstrip("\r\n")):]
                line = f'{m.group(1)}"{renamed[m.group(2).lower()]}"{m.group(3)}{ending}'
                changed = True
            lines.append(line)
        if changed:
            cue.write_bytes("".join(lines).encode("utf-8", errors="surrogateescape"))
            fixed += 1
    return fixed


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="scrubname",
        description="Strip region/revision tags like (USA) (Rev 1) [!] from ROM filenames.",
    )
    ap.add_argument("directory", nargs="?", default=".", help="folder to scan (default: current)")
    ap.add_argument("-r", "--recursive", action="store_true", help="include subfolders")
    ap.add_argument("-n", "--dry-run", action="store_true", help="show changes without renaming")
    ap.add_argument("-y", "--yes", action="store_true", help="rename without asking")
    ap.add_argument("--version", action="version", version=f"scrubname {__version__}")
    args = ap.parse_args(argv)

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"scrubname: not a directory: {root}", file=sys.stderr)
        return 2

    files = find_roms(root, args.recursive)
    plan, skipped = plan_renames(files)

    for old, new in plan.items():
        print(f"  {old.relative_to(root)}\n    -> {new.name}")
    for old, new in skipped:
        print(f"  SKIP {old.relative_to(root)} ({new.name} already exists)")

    print(f"\n{len(files)} ROM file(s) found, {len(plan)} to rename, {len(skipped)} skipped.")
    if not plan or args.dry_run:
        return 0
    if not args.yes:
        try:
            if input("Rename them? [y/N] ").strip().lower() not in ("y", "yes"):
                print("Nothing changed.")
                return 0
        except EOFError:
            return 0

    done = 0
    for old, new in plan.items():
        try:
            os.rename(old, new)
            done += 1
        except OSError as e:
            print(f"  FAILED {old.name}: {e}", file=sys.stderr)
    cues = rewrite_cues(plan)
    print(f"Renamed {done} file(s)" + (f", updated {cues} .cue file(s)." if cues else "."))
    return 0 if done == len(plan) else 1


if __name__ == "__main__":
    sys.exit(main())
