import sys, json
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib")
import placelib
from pathlib import Path
m = placelib.PlaceModel(Path(sys.argv[1]))
print("outline bounds", [round(v,3) for v in m.outline.bounds])
for ref in sorted(m.footprints):
    f=m.footprints[ref]
    b=f.extents_abs().bounds
    print(f"{ref:6s} {getattr(f,'fpid',getattr(f,'name','?')):50s} pos=({f.pos[0]:8.3f},{f.pos[1]:8.3f}) ang={f.angle:6.1f} side={f.side:6s} mov={f.is_movable} bbox=[{b[0]:7.2f},{b[1]:7.2f},{b[2]:7.2f},{b[3]:7.2f}] wh=({b[2]-b[0]:6.2f},{b[3]-b[1]:6.2f})")
print("N=",len(m.footprints))
