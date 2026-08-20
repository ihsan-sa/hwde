#!/usr/bin/env bash
# run_case.sh NAME  -- build + measure one aspect-study candidate.
# Base board = the pre-P7-routing snapshot (the P6 placement, NO tracks/zones),
# so every candidate is measured on the same unrouted footing.
set -u
ROOT=C:/dev/ai-ee3
PY=$ROOT/.venv/Scripts/python.exe
S=$ROOT/.claude/skills/ai-ee/scripts
ST=$ROOT/boards/bb-ldo/reports/aspect-study
NAME=$1
D=$ST/cases/$NAME
PCB=$D/kicad/bb-ldo.kicad_pcb

mkdir -p "$D/kicad"
cp $ROOT/boards/bb-ldo/kicad/bb-ldo.kicad_pro "$D/kicad/" 2>/dev/null
cp $ROOT/boards/bb-ldo/kicad/bb-ldo.kicad_dru "$D/kicad/" 2>/dev/null
cp $ROOT/boards/bb-ldo/kicad/constraints.json "$D/kicad/" 2>/dev/null
cp $ROOT/boards/bb-ldo/kicad/decoupling.json  "$D/kicad/" 2>/dev/null
cp $ROOT/boards/bb-ldo/state_snapshots/pre-P7-routing/kicad/bb-ldo.kicad_pcb "$PCB"

if [ -f "$D/ops.json" ]; then
  echo "--- place_edit $NAME"
  "$PY" $S/place_edit.py --pcb "$PCB" --ops "$D/ops.json" \
        --out-report "$D/place_edit.json" >/dev/null || { echo "PLACE FAIL $NAME"; exit 2; }
fi

if [ -n "${WH:-}" ]; then
  echo "--- board_edit $NAME -> $WH"
  "$PY" $S/board_edit.py --pcb "$PCB" --outline "$WH" --anchor topleft \
        --no-record --out-report "$D/board_edit.json" >/dev/null || { echo "OUTLINE FAIL $NAME"; exit 2; }
fi

echo "--- planes_gen $NAME"
"$PY" $S/planes_gen.py --no-thermal-vias --pcb "$PCB" --constraints "$D/kicad/constraints.json" \
      --out-report "$D/planes_gen.json" >/dev/null || { echo "PLANES FAIL $NAME"; exit 2; }

"$PY" $S/place_metrics.py --pcb "$PCB" --constraints "$D/kicad/constraints.json" \
      --decoupling "$D/kicad/decoupling.json" --out "$D/place_metrics.json" >/dev/null
echo "place_metrics exit=$?"
"$PY" $S/check_thermal.py --pcb "$PCB" --constraints "$D/kicad/constraints.json" \
      --out "$D/check_thermal.json" >/dev/null
echo "check_thermal exit=$?"
"$PY" $ST/measure.py --pcb "$PCB" --out "$D/measure.json" >/dev/null
echo "=== $NAME done"
