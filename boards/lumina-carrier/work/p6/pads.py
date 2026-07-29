import sys
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib")
import placelib
from pathlib import Path
m = placelib.PlaceModel(Path(sys.argv[1]))
for ref in sys.argv[2].split(","):
    f = m.footprints[ref]
    print(f"--- {ref} {f.fpid} pos={f.pos} ang={f.angle}")
    for p in f.pads:
        print(f"    pad {p.number:>4s} net={p.net!s:22s} local=({p.local[0]:7.3f},{p.local[1]:7.3f}) size={p.size}")
