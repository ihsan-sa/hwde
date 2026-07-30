"""Validate the local->absolute text transform, then emit the naive all-targets ops file."""
import json, math, sys

BASE = r'C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk'
WO = json.load(open(r'C:/dev/ai-ee3/boards/lumina-carrier/log/workorders/wo-silklegibility.json', encoding='utf-8'))
TGT = WO["targets"]["per_footprint_local_y"]
SKIP = set(WO["requirement"]["out_of_scope_refs"])

inv = json.load(open(f'{BASE}/inv.json', encoding='utf-8'))
geom = json.load(open(f'{BASE}/geom.json', encoding='utf-8'))
gm = {f["ref"]: f for f in geom["footprints"]}

def to_abs(fx, fy, fdeg, lx, ly):
    th = math.radians(fdeg)
    return (fx + lx * math.cos(th) + ly * math.sin(th),
            fy - lx * math.sin(th) + ly * math.cos(th))

# --- validate transform against KiCad's own reported text position
bad = []
for f in inv["footprints"]:
    ref = f["ref"]
    r = f["props"]["reference"]
    ax, ay = to_abs(f["x"], f["y"], f["deg"], r["lx"], r["ly"])
    g = gm[ref]["ref_text"]
    if abs(ax - g["x"]) > 1e-3 or abs(ay - g["y"]) > 1e-3:
        bad.append((ref, round(ax, 4), round(ay, 4), g["x"], g["y"]))
print("transform mismatches:", len(bad), bad[:5])

# --- missing targets?
names = {f["name"].split(":")[-1] for f in inv["footprints"] if f["ref"] not in SKIP}
missing = sorted(n for n in names if n not in TGT)
print("footprint names without a target:", missing)

ops = []
for f in inv["footprints"]:
    ref = f["ref"]
    if ref in SKIP:
        continue
    fn = f["name"].split(":")[-1]
    ty = TGT[fn]
    ax, ay = to_abs(f["x"], f["y"], f["deg"], 0.0, ty)
    ops.append({"op": "move_text", "ref": ref, "field": "reference",
                "x": round(ax, 4), "y": round(ay, 4)})
json.dump({"version": 1, "ops": ops}, open(f'{BASE}/ops_naive.json', 'w', encoding='utf-8'), indent=1)
print("naive ops:", len(ops))
