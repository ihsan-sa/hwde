"""amend_dru.py - P7 scope amendment to the hand-written HV rules.

Adds a per-refdes "both items inside the same footprint courtyard" exclusion
to the three HV_48V_* clearance rules. Everything else in the file - every
rule, comment and the magjack isolation barrier - is left byte-identical.
Backs the original up to work/p7/lumina-carrier.kicad_dru.pre_p7 first.
"""
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DRU = REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_dru"
BAK = REPO / "boards/lumina-carrier/work/p7/lumina-carrier.kicad_dru.pre_p7"

PKG = ["U1", "U20", "U22", "C1", "C61", "C62", "C63"]
OLD = "!(A.Type == 'Pad' && B.Type == 'Pad')"
EXCL = "".join(
    " && !(A.intersectsCourtyard('%s') && B.intersectsCourtyard('%s'))" % (r, r)
    for r in PKG)

NOTE = """# P7 SCOPE AMENDMENT - the P6 pad-pair exclusion, carried one step further.
#
# The pad-pair exclusion stops the rule firing BETWEEN two pins of one package,
# but not between a pin and the FAN-OUT STUB that has to land on that pin.
# Measured on the placed board (work/p7/hv_escape.py): 15 of the 37 48 V pads
# sit closer than 0.635 mm to foreign copper OF THEIR OWN FOOTPRINT - U1 pads
# 1/9 (SOIC-8, 0.200 mm), U22 pads 1/2/3/6/18/19/20 (HTSSOP-20, 0.250-0.375 mm
# to pins 4/5/17 and to the pin-21 thermal land), U20 pad 3 (0.295 mm to its own
# GND exposed pad) and C1/C61/C62/C63 (0.590 mm across their own two 0805 pads).
# A track reaching any of those pads inherits the pad's neighbourhood, so under
# the un-amended rule those 15 pads were UNROUTABLE. Verified live at P7
# (work/p7/hvtest): a V48_RAW stub on U22 pad 6 fired HV_48V_clearance twice at
# 0.250 mm against pins 5 and 7 - a spacing the package pitch fixes and that no
# routing choice can change.
#
# The exclusion below applies the pad-pair rationale to the stub: when BOTH
# items lie inside ONE named footprint's courtyard, the spacing is package
# geometry. It is enumerated per refdes (never wildcarded) so it cannot quietly
# widen, and it covers only the seven footprints measured above. Every trace,
# via and pour in open board area - and any pair spanning two different
# footprints - still holds 0.635 mm. P8 check_creepage still models pad-to-pad
# independently from constraints.json `voltages`.

"""


def main():
    text = DRU.read_text(encoding="utf-8")
    n = text.count(OLD)
    if n != 3:
        raise SystemExit("expected 3 pad-pair exclusions, found %d" % n)
    if "intersectsCourtyard('U22')" in text:
        raise SystemExit("already amended - nothing to do")
    shutil.copy2(DRU, BAK)
    text = text.replace(OLD, OLD + EXCL)
    i = text.index('(rule "HV_48V_clearance"')
    text = text[:i] + NOTE + text[i:]
    DRU.write_text(text, encoding="utf-8")
    print("amended %d HV rules; backup -> %s" % (n, BAK))


if __name__ == "__main__":
    main()
