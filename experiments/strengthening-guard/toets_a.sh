#!/bin/bash
# Toets A opnieuw: bron 283e83d:CLAUDE.md, vertelling 234ec9c:CLAUDE.md (alleen lezen).
set -e
cd "$(dirname "$0")"
root=$(git rev-parse --show-toplevel)
git -C "$root" show 283e83d:CLAUDE.md > /tmp/wachter_A_bron.md
git -C "$root" show 234ec9c:CLAUDE.md > /tmp/wachter_A_vertelling.md
python3 -B wachter.py --json /tmp/wachter_A_bron.md /tmp/wachter_A_vertelling.md > /tmp/wachter_A.json || true
cmp -s /tmp/wachter_A.json A_UITKOMST.json && echo "zelfde uitkomst als A_UITKOMST.json" || echo "ANDERE uitkomst dan A_UITKOMST.json"
