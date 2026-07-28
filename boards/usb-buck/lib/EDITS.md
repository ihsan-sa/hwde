# Library edits - boards/usb-buck/lib/aiee.pretty

Hand edits to pulled easyeda2kicad footprints. Every edit here was made by the P3
librarian agent under explicit orchestrator approval (run (a) D2 precedent: minimal,
documented, verified). Re-pulling a part with `lib_pull.py --overwrite` DISCARDS these
edits - re-apply from this file if that happens.

Untouched by every edit below: all pad geometry (position, size, shape, layers, drills),
all courtyard geometry, all 3D model references, all `(property "LCSC Part" ...)` values.
Only `F.SilkS` graphics changed.

## 2026-07-28 - P3 librarian, approved by orchestrator

### Why

Two library-inherent silk defects found during P3 verification:

1. **Silk printed on pad-1 copper.** `C0603`, `C0805`, `R0603` and
   `LED-SMD_L1.6-W0.8-R-RD` each carried a tiny easyeda2kicad artifact circle on
   `F.SilkS` sitting on or inside pad 1 (measured stroke-edge-to-copper-edge gaps
   -0.110, -0.105, -0.092 and -0.100 mm). The circles are drawn at the footprint's
   first courtyard vertex, carry no semantics, and at 0.06-0.10 mm stroke are below
   JLC's 0.15 mm minimum silkscreen line width, so they cannot print anyway. The LED's
   one produced a real `silk_over_copper` "Silkscreen clipped by solder mask" DRC
   warning (see verification below).
2. **U2's pin-1 mark does not print.** The `TSOT-26` (AP63203 buck) pin-1 indicator was
   a zero-area `fp_poly` (3 collinear points, `stroke width 0`) plus a 0.06 mm-stroke
   dot, with the only real marker circle on `Cmts.User` - a non-fabricated layer. A
   rotated buck is a dead board, and the CPL preview needs a visible pin-1 mark.

Acceptance rule set by the orchestrator for the four footprints in (1): after the edit
every remaining `F.SilkS` element must clear pad copper by >= 0.15 mm, and the LED must
keep its (verified-correct) chamfered cathode-end cue.

### C0603.kicad_mod  (C14663 100nF; also used by C1653, C19666, C15849)

- DELETED `(fp_circle (center -0.80 0.40) (end -0.77 0.40) (layer F.SilkS) (width 0.06))`
  - r 0.03, stroke 0.06, outer radius 0.06; sat 0.05 mm inside pad 1's copper
    (pad 1 = -0.70,0.00, size 0.80 x 0.90 -> x[-1.10,-0.30] y[-0.45,0.45]). Gap -0.110 mm.
- CHANGED stroke width `0.25 -> 0.20` on all 10 remaining `F.SilkS` outline elements
  (6 `fp_line`, 4 `fp_arc`). No coordinate changed.
  - Needed to meet the >= 0.15 mm rule: at 0.25 the body-outline lines at y = +/-0.71
    cleared pad copper by only 0.135 mm and the corner arcs by 0.131 mm. Narrowing the
    stroke moves each edge out by 0.025 mm -> 0.160 and 0.156 mm. 0.20 mm is still well
    above JLC's 0.15 mm minimum line width, and the outline keeps a uniform stroke.
- Worst remaining silk-to-copper gap: **0.156 mm** (was -0.110).

### C0805.kicad_mod  (C15850 10uF; also used by C45783)

- DELETED `(fp_circle (center -1.00 0.63) (end -0.97 0.63) (layer F.SilkS) (width 0.06))`
  - Gap -0.105 mm (inside pad 1: -1.00,0.00 size 1.410 x 1.350).
- Nothing else changed - the remaining outline (0.15 stroke) already cleared copper by
  exactly 0.150 mm.
- Worst remaining silk-to-copper gap: **0.150 mm** (was -0.105).

### R0603.kicad_mod  (C21190 1k; also used by C25804, C22843)

- DELETED `(fp_circle (center -0.80 0.40) (end -0.77 0.40) (layer F.SilkS) (width 0.06))`
  - Gap -0.092 mm (inside pad 1: -0.75,0.00 size 0.806 x 0.864).
- Nothing else changed - remaining outline already at 0.153 mm.
- Worst remaining silk-to-copper gap: **0.153 mm** (was -0.092).

### LED-SMD_L1.6-W0.8-R-RD.kicad_mod  (C2286 red LED, D1)

- DELETED `(fp_circle (center 0.80 -0.40) (end 0.85 -0.40) (layer F.SilkS) (width 0.10))`
  - r 0.05, stroke 0.10, outer radius 0.10, centred exactly on pad 1's top-left corner
    (pad 1 = 0.75,0.00 size 0.80 x 0.80 -> x[0.35,1.15] y[-0.40,0.40]). Gap -0.100 mm.
    This is the element that tripped KiCad DRC.
- CHANGED stroke width `0.25 -> 0.15` on the two interior glyph lines only:
  `(start 0.09 -0.40) (end 0.09 0.38)` and `(start 0.09 -0.00) (end -0.12 -0.00)`.
  - Needed to meet the >= 0.15 mm rule: at 0.25 they cleared copper by 0.135 and
    0.105 mm; at 0.15 they clear by 0.185 and 0.155 mm. 0.15 mm = JLC's minimum
    printable line width. Coordinates unchanged, so the glyph is unchanged in shape.
- **KEPT unchanged**: the chamfered outline end over pad 2
  ((-1.40,-0.70)->(-1.70,-0.40)->(-1.70,0.40)->(-1.40,0.70)) at 0.25 stroke. Pad 2 is
  the cathode (symbol pin 2 = "K"; the KT-0603R datasheet marks pin (1) "+" = anode),
  so the chamfer is the correct and now the only unambiguous cathode cue.
- Worst remaining silk-to-copper gap: **0.155 mm** (was -0.100).
- NOT fixed (out of approved scope, flagged to the orchestrator): the interior
  bar-and-stub glyph still reads as a cathode bar on the pad-1 (anode) side, which
  contradicts the chamfer. Deleting those two lines is the one-line follow-up if a
  human confirms it is misleading.

### TSOT-26_L2.9-W1.6-P0.95-LS2.8-BL.kicad_mod  (C5248536 AP63203 buck, U2)

- ADDED `(fp_circle (center -1.60 1.95) (end -1.45 1.95) (layer F.SilkS) (width 0.15))`
  - 0.30 mm diameter (r 0.15), 0.15 mm stroke -> outer radius 0.225 mm, printable at
    JLC's minimum line width.
  - Placed diagonally off pad 1's outboard corner. Nearest copper is pad 1's corner
    (-1.225, 1.75); centre-to-corner distance 0.425 mm, so the dot clears copper by
    **0.200 mm** (requirement was >= 0.15). Nearest other silk is the pre-existing
    0.06 artifact dot at (-1.45,1.40), 0.285 mm away (clears the 0.25 mm silk-silk
    rule), and the body-outline bracket at (-1.50,0.80), 0.83 mm away.
- Nothing was removed. The zero-area `fp_poly` and the `Cmts.User` circle were left in
  place (harmless; neither prints).
- NOT fixed (out of approved scope for this footprint, which was "add a pin-1 dot"):
  the four pre-existing body-outline corner brackets
  ((+/-1.50,+/-0.80)->(+/-1.43,+/-0.80), 0.20 stroke) clear pad copper by only
  0.105 mm. They do not overlap copper and do not trip DRC. Shortening each 0.07 mm
  stub to end at x = +/-1.48 would raise them to 0.155 mm if wanted.

### Verification (all re-run after the edits)

| Check | Result |
|---|---|
| `kicad-cli 10.0.3 fp export svg` over the whole `.pretty` | 12/12 footprints plotted, 0 errors -> `reports/fp_svg/` |
| Rendered delta, C0603 / C0805 / R0603 / LED | the artifact `<circle>` is gone from each rendered SVG |
| Rendered delta, C0603 stroke width | `stroke-width:0.25` replaced by `0.20`; `0.06` gone |
| Rendered delta, LED stroke widths | `0.10` gone; `0.25` (chamfer/outline) kept; glyph now in the `0.15` group |
| Rendered delta, TSOT-26 | new `<circle r="0.150">` present at the pin-1 position (0.15 left, 0.55 outboard of the old artifact dot) |
| Geometric re-measure (stroke edge to pad copper edge) | C0603 0.156, C0805 0.150, R0603 0.153, LED 0.155, TSOT-26 new dot 0.200 - no element overlaps copper in any of the five |
| Scratch-board DRC, `kc.py drc --severity-all`, one instance of each of the 5 | **1 -> 0 violations**. Before: `silk_over_copper` "Silkscreen clipped by solder mask" on the LED. After: zero, exit 0 |
| `fp_verify.py` re-pass | C0603 pass, C0805 pass, R0603 pass, LED pass (1 `pad_size` warning: 0.80 x 0.80 vs the datasheet's suggested 0.70 x 0.70 - same 0.70 mm inter-pad gap, 0.05 mm more pad per side, pre-existing and not caused by these edits), TSOT-26 pass (1 pre-existing `pad_size` warning) |

Pre-edit copies of all five files were kept for the diff; the edits above are the
complete delta.
