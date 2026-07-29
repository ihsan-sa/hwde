"""Append the strict-interior containment learning. Re-reads before writing so a
concurrent run's append is not clobbered. Idempotent on the title.
"""
import io

P = r'C:\dev\ai-ee3\LEARNINGS.md'
TITLE = ("## 2026-07-29 [geometry][keepout][planes] Keepout checks need STRICT-interior containment: "
         "plane regions deliberately ABUT the band they exclude")

ENTRY = TITLE + """
Verifying that the ESP32-S3 antenna band was copper-free on lumina-carrier, a hand-written check
reported **14 violations** on In1.Cu and In2.Cu. All 14 were false.

The cause is structural, not a coding slip. The recipe that carves a hole out of a plane uses three
positive rectangles per layer, because a single positive rectangle cannot have a hole - so the middle
region is authored to **stop exactly at the keepout's edge** (`ex2 - 10`, i.e. x = 109.58, the band's
left boundary). Its fill polygon therefore *legitimately* carries vertices lying precisely ON the
boundary. An inclusive test (`BAND[0] <= x <= BAND[2]`) counts every one of them as copper inside the
band. A strict test with a small epsilon (`BAND[0] + EPS < x < BAND[2] - EPS`) returns zero.

**Any containment test against a deliberately-abutting region must be strict, not inclusive.** This
will bite every future keepout, courtyard, plane-void, board-edge and exclusion-zone check, because
"the excluded region and the thing excluded from it share an edge" is the normal case, not the
exception - that is what makes the exclusion exact.

The dangerous part is the failure direction: an inclusive test cries wolf on a board that is
**correct**, and the obvious "fix" is to tear up good copper or shrink a plane that was already right.
Fix the checker, not the board. Confirm by sweeping epsilon (0.00 / 0.01 / 0.10 / 0.50 mm) - if the
count collapses to zero at any nonzero epsilon, every hit was a boundary artifact and the geometry was
never wrong.

Related: no gate in the pipeline checks a keepout band at all. `constraints.json.placement.keepouts`
is read only by the P6 placement scripts; the router and `planes_gen` never see it, so an F.Cu/B.Cu
keepout RULE AREA has to be added at P7 and the inner-layer exclusion has to come from the plane
region shaping. Verifying it is therefore a manual geometric step - which is exactly why the checker
being trustworthy matters.
"""


def main() -> None:
    text = io.open(P, encoding='utf-8').read()
    if TITLE in text:
        print('already present - no change')
        return
    io.open(P, 'a', encoding='utf-8').write(
        ('' if text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')) + ENTRY)
    print('appended learning (%d chars)' % len(ENTRY))


main()
