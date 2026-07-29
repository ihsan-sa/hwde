"""Per-footprint audit: courtyard, silk, pin-1 marker heuristics, pad extents."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(".claude/skills/ai-ee/scripts/lib").resolve()))
import fplib

pretty = Path("boards/lumina-carrier/lib/aiee.pretty")
rows = []
for f in sorted(pretty.glob("*.kicad_mod")):
    fp = fplib.parse_footprint(f)
    txt = f.read_text(encoding="utf-8", errors="replace")
    silk_items = len(re.findall(r'\(fp_(line|circle|arc|poly|rect|text)', txt))
    # silk graphics on F.SilkS only
    silk_layer = len(re.findall(r'\(layer F\.SilkS\)', txt)) + len(re.findall(r'\(layer "F\.SilkS"\)', txt))
    # small circles/dots = candidate pin-1 markers
    dots = re.findall(r'\(fp_circle \(center ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)[^)]*\(layer ([\w.&]+)\)[^)]*\(width ([\d.]+)\)', txt)
    cu = fp.copper_pads
    xs = [p.center[0] for p in cu]; ys = [p.center[1] for p in cu]
    p1 = next((p for p in cu if p.number == "1"), None)
    rows.append(dict(name=fp.name, file=f.name, pads=len(cu), crtyd=fp.has_courtyard,
                     silk=fp.has_layer_kind("SilkS"), silk_items=silk_layer,
                     dots=[(d[4], d[5], round(float(d[0]),2), round(float(d[1]),2)) for d in dots],
                     pad1_shape=(p1.shape if p1 else None),
                     extent=(round(max(xs)-min(xs),2), round(max(ys)-min(ys),2)) if cu else None))
for r in rows:
    print(f"{r['name'][:46]:<46} pads={r['pads']:>3} crtyd={str(r['crtyd']):<5} silk={r['silk_items']:>2} "
          f"pad1={str(r['pad1_shape']):<7} ext={r['extent']} dots={r['dots'][:3]}")
