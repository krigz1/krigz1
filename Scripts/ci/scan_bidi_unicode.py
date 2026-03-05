#!/usr/bin/env python3
import argparse
import os
import sys

BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF}

def scan_file(path: str):
BIDI = set(list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)))
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF}

def scan_file(path: str) -> list[str]:
    issues = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception as e:
        return [f"READ_ERROR: {e}"]

    for idx, ch in enumerate(text):
        cp = ord(ch)
        if cp in BIDI or cp in ZERO_WIDTH:
            line = text.count("\n", 0, idx) + 1
            col = idx - text.rfind("\n", 0, idx)
            kind = "BIDI" if cp in BIDI else "ZERO_WIDTH"
            issues.append(f"{kind} U+{cp:04X} line {line} col {col}")

    return issues

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--extensions", default=".json,.jsonl,.md,.txt,.yml,.yaml")
    args = parser.parse_args()
            issues.append(f"{kind} U+{cp:04X} at line {line}, col {col}")
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--extensions", default=".json,.jsonl,.md,.txt,.yml,.yaml")
    args = ap.parse_args()

    exts = set(e.strip().lower() for e in args.extensions.split(",") if e.strip())
    root = os.path.abspath(args.root)

    any_fail = False
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            p = os.path.join(dirpath, fn)
            issues = scan_file(p)
            if issues:
                any_fail = True
                print(f"[BIDI/ZW DETECTED] {p}")
                for it in issues[:50]:
                    print(f"  - {it}")
                if len(issues) > 50:
                    print(f"  - ... ({len(issues)-50} more)")

    if any_fail:
        sys.exit(1)

if __name__ == "__main__":
    main()
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
