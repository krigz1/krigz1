#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
ZERO_WIDTH = set(range(0x200B, 0x2010)) | {0xFEFF}
TARGET_EXT = {".json", ".jsonl", ".md", ".txt"}
SKIP_DIRS = {".git", "Binaries", "Intermediate", "Saved"}


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in TARGET_EXT:
            yield p


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    found = False
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        line = 1
        col = 0
        for ch in text:
            if ch == "\n":
                line += 1
                col = 0
                continue
            col += 1
            cp = ord(ch)
            if cp in BIDI or cp in ZERO_WIDTH:
                found = True
                print(f"{path}:{line}:{col}: U+{cp:04X}")
    if found:
        print("Found bidi/zero-width characters.")
        return 1
    print("No bidi/zero-width characters found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
