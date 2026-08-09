set -e
cd C:/dev/ai-ee3
P=.venv/Scripts/python
S=.claude/skills/ai-ee/scripts
B=C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb
R=C:/dev/ai-ee3/boards/rf-de-20m/route
git checkout -- boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb
# 1. +40V B.Cu bus bridge vias - BARE board (a via added into a filled zone
#    of a foreign net takes that zone's net, not the op's)
$P $R/bridge_vias.py
$P $S/route_edit.py --pcb $B --ops $R/ops_bridge.json --out-report $R/edit_bridge.json >/dev/null
# 2. GND pours only
$P $R/planes.py gnd
$P $S/planes_gen.py --pcb $B --constraints $R/planes_gnd.json --out-report $R/planes_gen_gnd.json >/dev/null
# 3. hand copper: spiral lands, EPC drain escapes, gate legs
$P $S/route_edit.py --pcb $B --ops $R/ops_lands.json --out-report $R/edit_lands.json >/dev/null
$P $R/gate_tracks.py >/dev/null
$P $S/route_edit.py --pcb $B --ops $R/ops_gates.json --out-report $R/edit_gates.json >/dev/null
$P $R/die_fanin.py >/dev/null
$P $S/route_edit.py --pcb $B --ops $R/ops_fanin.json --out-report $R/edit_fanin.json >/dev/null
# 4. GND stitching, while only GND is poured
$P $S/stitch_vias.py --pcb $B --nets GND --max-vias 400 --dry-run --out-report $R/stitch_dry.json >/dev/null
$P $R/planes.py all
$P $R/stitch_filter.py
$P $R/apply_ops.py $R/ops_stitch.json $R/edit_stitch.json
# 4b. EPC2019 thermal via field - placed while only GND is poured, so the
#     vias keep their net and the /SW pour flows around them afterwards
$P $R/thermal_vias.py
$P $R/apply_ops.py $R/ops_thermal.json $R/edit_thermal.json
# 5. power pours
$P $R/planes.py pwr
$P $S/planes_gen.py --pcb $B --constraints $R/planes_pwr.json --out-report $R/planes_gen.json >/dev/null || true
# 6. drop planes_gen's dangling /SW thermal vias in L202.2 (F.Cu-only SMD pad,
#    nothing for them to land on below)
$P -c "
import sys,json; sys.path.insert(0,'$S')
from lib.geom import load_board
b=load_board('$B')
ops=[{'op':'remove','uuid':v.uuid} for v in b.vias_of(net='/SW')]
json.dump({'version':1,'ops':ops},open('$R/ops_rmvia.json','w'),indent=1)
print('dangling /SW vias:',len(ops))"
if [ "$($P -c "import json;print(len(json.load(open('$R/ops_rmvia.json'))['ops']))")" != "0" ]; then
  $P $S/route_edit.py --pcb $B --ops $R/ops_rmvia.json --out-report $R/edit_rmvia.json >/dev/null
fi
# 7. one via per orphaned F.Cu GND island (stitch_vias grid cannot land in
#    the small EPC2019 lobes)
$P $R/island_vias.py
$P $R/apply_ops.py $R/ops_island.json $R/edit_island.json
echo "rebuild ok"
# 8. remaining signal nets via KRT (Freerouting 2.2.4 wedges reading this
#    design - see reports/route-notes.md)
rm -rf $R/krt
$P $R/krt_finish.py
# 9. plane repair + final refill/DRC + geometric acceptance
cp $B $R/pre-plane_repair.kicad_pcb
$P $S/plane_repair.py --pcb $B --out-report $R/plane_repair.json || echo "plane_repair exit $?"
$P $S/kc.py drc --refill --save-board --parity --all-track-errors --out $R/drc_final.json $B >/dev/null
$P $S/gate.py --gate drc_routed $B --out C:/dev/ai-ee3/boards/rf-de-20m/reports/gate-drc_routed.json || true
$P $R/verify_geom.py || true
