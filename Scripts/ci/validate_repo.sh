#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 "$ROOT_DIR/Scripts/ci/scan_bidi_unicode.py" "$ROOT_DIR" --extensions ".json,.jsonl,.md,.txt,.yml,.yaml"

echo "[validate_repo.sh] JSON parse check..."
python3 - <<'PY'
import json, os, sys

root = os.getcwd()
fail = False

def is_jsonl(path):
    return path.endswith(".jsonl")

def check_json(path):
    global fail
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        print(f"[JSON ERROR] {path}: {e}")
        fail = True

def check_jsonl_file(path):
    global fail
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except Exception as e:
                    print(f"[JSONL ERROR] {path}:{i}: {e}")
                    fail = True
    except Exception as e:
        print(f"[JSONL READ ERROR] {path}: {e}")
        fail = True

for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        if fn.endswith(".json"):
            check_json(p)
        elif fn.endswith(".jsonl"):
            check_jsonl_file(p)

if fail:
    sys.exit(1)

print("[validate_repo.sh] OK")
PY
