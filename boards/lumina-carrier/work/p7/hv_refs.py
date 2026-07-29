"""hv_refs.py - list every footprint that carries a 48 V pad.

The same-courtyard exclusion in the HV_48V_* rules has to cover exactly these
refdes: inside one of them the spacing around an HV pin is package geometry,
outside them 0.635 mm is a real routing constraint.

usage: python hv_refs.py [board.kicad_pcb]
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402

HV = {"V48_RAW", "V48_RTN", "+48V_SW"}
pcb = sys.argv[1] if len(sys.argv) > 1 else str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
bg = geom.BoardGeom.from_file(pcb)
refs = sorted({p.ref for p in bg.pads_of() if p.net in HV})
print(len(refs), "footprints carry a 48 V pad:")
print(" ".join(refs))
print()
print("".join(" && !(A.intersectsCourtyard('%s') && B.intersectsCourtyard('%s'))"
                % (r, r) for r in refs))
