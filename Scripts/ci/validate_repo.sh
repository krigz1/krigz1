#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 Scripts/ci/scan_bidi_unicode.py "$ROOT_DIR"

while IFS= read -r -d '' f; do
  python3 - <<'PY' "$f"
import json,sys
p=sys.argv[1]
with open(p,encoding='utf-8') as fh:
    json.load(fh)
PY
  echo "JSON OK: $f"
done < <(find . -type f -name '*.json' -not -path './.git/*' -print0)

while IFS= read -r -d '' f; do
  python3 - <<'PY' "$f"
import json,sys
p=sys.argv[1]
with open(p,encoding='utf-8') as fh:
    for i,l in enumerate(fh,1):
        s=l.strip()
        if not s:
            continue
        json.loads(s)
PY
  echo "JSONL OK: $f"
done < <(find . -type f -name '*.jsonl' -not -path './.git/*' -print0)

echo "validate_repo.sh: PASS"
