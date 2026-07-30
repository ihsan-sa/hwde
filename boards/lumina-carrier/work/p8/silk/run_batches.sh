#!/bin/sh
# Apply the batches to $1 (a board path) and DRC after each. Exits 1 on any regression.
set -e
PCB="$1"
TAG="$2"
PY=C:/dev/ai-ee3/.venv/Scripts/python.exe
S=C:/dev/ai-ee3/.claude/skills/ai-ee/scripts
W=C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk
for n in 1 2 3 4 5; do
  echo "=== batch $n ==="
  "$PY" "$S/place_edit.py" --pcb "$PCB" --ops "$W/ops_batch$n.json" \
      --out-report "$W/${TAG}_apply$n.json" > /dev/null
  "$PY" "$S/kc.py" drc "$PCB" --parity --all-track-errors \
      --out "$W/${TAG}_drc$n.json" > /dev/null || true
  "$PY" -c "
import json,sys,collections
d=json.load(open(r'$W/${TAG}_drc$n.json',encoding='utf-8'))
c=d['counts']
print('batch $n -> total', c['total'], dict(collections.Counter(x['check'] for x in d['violations'])))
sys.exit(1 if c['total'] else 0)
"
done
echo "ALL BATCHES CLEAN"
