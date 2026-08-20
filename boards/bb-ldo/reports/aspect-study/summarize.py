import json, sys
from pathlib import Path
ST = Path(r"C:/dev/ai-ee3/boards/bb-ldo/reports/aspect-study")
names = sys.argv[1:] or ["base","a255","a189","a160","a160e","a147","a121",
                         "a109","a100","a100e","f189","f100","s1201","s1150"]
rows = []
print(f"{'case':7} {'W':>7} {'H':>7} {'area':>7} {'asp':>5} {'pour':>8} {'isl':>3} "
      f"{'a_eff':>7} {'theta':>6} {'rise-65':>7} {'r15':>7} {'r20':>8} {'r25':>8} "
      f"{'legal':>5} {'tabxy':>16}")
for n in names:
    f = ST / "cases" / n / "measure.json"
    if not f.is_file():
        continue
    d = json.loads(f.read_text())
    pm = ST / "cases" / n / "place_metrics.json"
    v = json.loads(pm.read_text()).get("violations", []) if pm.is_file() else None
    kinds = sorted({x["kind"] for x in v}) if v is not None else ["?"]
    o, t, p = d["outline"], d["thermal_reach"], d["pour_fcu"]
    rows.append({"case": n, **o, **{k: v2 for k, v2 in t.items()
                                    if not k.startswith("_")},
                 "pour_mm2": p["area_mm2"], "islands": p["islands"],
                 "orphan_mm2": p["orphan_mm2"],
                 **{k: v2 for k, v2 in d["tab_discs"].items()
                    if not k.startswith("_")},
                 "gnd": d["bcu_gnd"], "legality": kinds})
    print(f"{n:7} {o['w']:7.3f} {o['h']:7.3f} {o['area_mm2']:7.1f} {o['aspect']:5.2f} "
          f"{p['area_mm2']:8.2f} {p['islands']:3d} {t['a_eff_mm2']:7.2f} "
          f"{t['theta_ja_c_per_w']:6.2f} {t['margin_c']:7.2f} "
          f"{d['tab_discs']['r15']:7.1f} {d['tab_discs']['r20']:8.2f} "
          f"{d['tab_discs']['r25']:8.2f} "
          f"{'OK' if kinds == [] else ','.join(kinds)[:20]:>5} "
          f"{str([round(x,2) for x in d['tab_discs']['tab_center']]):>16}")
(ST / "results.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
