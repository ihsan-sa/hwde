"""Record the placement-oracle trap and two reusable KRT findings. Idempotent."""
import io

P = r'C:\dev\ai-ee3\LEARNINGS.md'

E1 = ("## 2026-07-29 [place][gates][routing] STOP: after P7 begins, `gate place` and `check_decoupling` are "
      "NOT valid oracles for a placement change - only DRC is")
T1 = E1 + """
**This mistake shorted a board and both checkers said PASS.**

On lumina-carrier I moved C35 by +0.300 mm to widen a fan-out corridor on a board that already carried
**3089 routed segments**. I validated the move the way P6 taught me to:

    gate place            -> PASS (0 failing)
    check_decoupling      -> unchanged, no new warnings

Then DRC found **6 new errors including `shorting_items` and `solder_mask_bridge`**: the pad had landed
on an existing `/ETH_RSTn` run at y 85.55.

**Both oracles are structurally blind to routed copper.** `place_metrics`/`placelib` reason about
courtyards, pad extents, keepouts and the outline. `check_decoupling` reasons about cap-to-pin distance
and loop inductance. **Neither one looks at a single track or via.** They are complete oracles at P6,
when there is no copper, and they silently stop being complete the instant the router lays the first
segment - and nothing in the pipeline tells you that transition happened.

**Rule: any footprint move after routing has started must be validated with `kc.py drc` (or the
`drc_routed` gate), not with the place gate.** Use the place gate as a NECESSARY-but-not-sufficient
pre-filter: it still catches courtyard and keepout illegality, which DRC will not phrase as such.

Two aggravating factors worth knowing:
- The correct sequence is snapshot -> move -> **DRC** -> place gate -> check_decoupling, and revert on
  any new DRC violation. I had the snapshot (which is why the revert was clean) but ran the checks in
  the wrong order and stopped at the first PASS.
- The same move was ALSO built on a bad measurement: the corridor figure read the footprint's `(at ...)`
  ORIGIN y rather than the **pad-1 centre** y, off by exactly 0.700 mm - so a claimed 1.681 mm corridor
  was really 0.981 mm. When measuring clearance to a specific pad, resolve the pad, never the footprint
  origin; on a 0603 they differ by roughly half the pad pitch.
- And it could not have worked regardless: the true blocker was a **void in the In1 GND fill** created
  by neighbouring plane vias' clearance holes, so a via in that corridor would have connected to
  nothing. Check that a plane actually has copper where you intend to land a stitching via.
"""

E2 = ("## 2026-07-29 [routing][krt] KRT's iteration cap, not the rip set, is usually what blocks a long haul - "
      "and its own diagnostic tells you which")
T2 = E2 + """
Two long nets on lumina-carrier (`/FAULT` 68 mm, `/ADC0` 59 mm) defeated roughly ten rip-set attempts.
The ladder's own diagnostic line explained why:

    Coverage: 1863/13659 frontier cells attributed to routed nets; 11796 static/unrippable

**86 % of the frontier was static**, i.e. pads, keepouts, plane edges and locked copper - things no rip
set can move. Ripping more nets could not help by construction. Raising `--max-iterations` from the
200000 default to **4000000** routed both nets on the first try.

Read that coverage line before choosing a rip set. High static fraction -> raise iterations. Low static
fraction -> a rip set may genuinely help.

Second finding from the same board: **broad rip sets trade nets 1-for-1.** One set fixed STATUS+RXD0 but
broke BOOT+I2C_SDA; the next fixed BOOT but broke ENABLE_M+ETH_RSTn. What converged was **one target net
at a time, with only its own hint list, gate after each attempt, and keep the result only if strictly
better** - otherwise revert. Keep a snapshot ladder so "strictly better" is enforceable.
"""

E3 = ("## 2026-07-29 [krt][clearance] KRT's `--clearance` is a CAP on the netclass map, not a floor - "
      "but `--net-clearances` is not capped")
T3 = E3 + """
On a board with a hand-written HV rule (0.635 mm on the 48 V nets) and a 0.2 mm general floor:

- Passing `--clearance 0.2` **silently produced 480 HV violations.** The flag caps the netclass map, so
  it pulled the HV nets DOWN to 0.2 mm rather than raising anything.
- Passing an explicit **`--net-clearances` file is NOT capped** (only the auto-read path is), which is
  how per-net HV clearance survives while everything else keeps the floor.

Also: KRT cannot read a `.kicad_dru`. Every `PWR_*` netclass in the `.kicad_pro` carried 0.2 mm and the
0.635 mm existed only in the DRU file, so the router had no way to know about it except the explicit
net-clearances file. If a hand-written DRU rule is the only thing holding a safety clearance, the
autorouter is not enforcing it - pass it explicitly and re-run DRC after.

Practical note: Git-Bash mangles a leading `/` in net names on the command line, so pass net lists via a
JSON job file rather than argv.
"""


def main() -> None:
    text = io.open(P, encoding='utf-8').read()
    added = []
    for title, body in ((E1, T1), (E2, T2), (E3, T3)):
        if title not in text:
            text = text.rstrip('\n') + '\n\n' + body.strip() + '\n'
            added.append(title.split(']')[-1].strip()[:56])
    io.open(P, 'w', encoding='utf-8').write(text)
    print('appended %d learning(s):' % len(added))
    for a in added:
        print('   -', a)


main()
