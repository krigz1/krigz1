#!/usr/bin/env python3
import argparse
import os
import sys

IGNORED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}

BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF}


def scan_file(path: str) -> list:
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

    exts = set(e.strip().lower() for e in args.extensions.split(",") if e.strip())
    root = os.path.abspath(args.root)

    any_fail = False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
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
                    print(f"  - ... ({len(issues) - 50} more)")

    if any_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()