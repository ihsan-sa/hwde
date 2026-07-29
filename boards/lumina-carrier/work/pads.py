import sys
from pathlib import Path
sys.path.insert(0, str(Path(".claude/skills/ai-ee/scripts/lib").resolve()))
import fplib
for f in sys.argv[1:]:
    fp = fplib.parse_footprint(Path(f))
    print("=== ", fp.name, " pads:", len(fp.pads), " copper:", len(fp.copper_pads), " crtyd:", fp.has_courtyard)
    for p in fp.pads:
        print(f"  pad {p.number:>4} type={getattr(p,'type','?')} shape={getattr(p,'shape','?')} at={tuple(round(v,4) for v in p.at)} size={tuple(round(v,4) for v in p.size)} drill={getattr(p,'drill',None)} layers={getattr(p,'layers',None)}")
