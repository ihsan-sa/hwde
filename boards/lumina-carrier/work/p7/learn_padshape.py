"""Record the pad-shape measurement trap. Idempotent."""
import io

P = r'C:\dev\ai-ee3\LEARNINGS.md'
TITLE = ("## 2026-07-29 [geometry][creepage][measurement] A pad-gap formula is only valid for one pad SHAPE - "
         "using the wrong one moves the answer by 0.3-0.5 mm in either direction")

ENTRY = TITLE + """
Measuring the cable-side/PHY-side barrier on lumina-carrier's magjack, I produced **three different
numbers for the same pair of pads** - 1.451, then 1.148, then 1.613 mm - and reported two of them
upstream before the third settled it. The cause was never the parser; it was applying a formula that
did not match the pad shape.

    circle-circle : gap = hypot(dx, dy) - (r1 + r2)                       <- radial form
    oval          : stadium - distance between the two spine SEGMENTS, minus radii
    rect-rect     : per-axis - dx = |dx_c| - (w1+w2)/2 ; dy likewise ;
                    gap = hypot(max(dx,0), max(dy,0))

**The radial form is EXACT for circles and overestimates rectangles** (by 0.303 mm on one diagonal
pair here). **The rect form is EXACT for rectangles and underestimates circles** (by 0.465 mm on the
same pair). I used each on the wrong shape in turn, so I first over-reported a gap, then "corrected"
a number that had been right, declared a false failure, and shrank a pad that did not need shrinking.

KiCad tells you the shape in the pad header - `(pad "2" thru_hole circle ...)` - and it is the second
token after the pad number. Read it. THT signal pads are usually `circle`; board-lock and shield tabs
are often `oval`; SMD pads are `rect`/`roundrect`. A single footprint routinely mixes all three, so a
gap tool that assumes one shape is wrong somewhere in every real footprint.

Write ONE shape-aware helper and use it everywhere. A capsule model covers all three: a circle is a
degenerate segment with a radius, an oval is a segment along its long axis with radius = half the
short axis, and only true rectangles need the per-axis form.

Two second-order lessons:
- **The direction of the error matters more than the size.** Over-reporting a gap hides a real
  violation; under-reporting invents one and invites you to "fix" correct hardware. I did both, and
  the under-report was worse - it cost a pad shrink and a retraction.
- **Re-deriving a number is not the same as re-deriving it correctly.** When a measurement is
  contested, fix the METHOD and state which model you used, rather than producing another figure.
"""


def main() -> None:
    text = io.open(P, encoding='utf-8').read()
    if TITLE in text:
        print('already present')
        return
    io.open(P, 'a', encoding='utf-8').write(
        ('' if text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')) + ENTRY)
    print('appended pad-shape learning (%d chars)' % len(ENTRY))


main()
