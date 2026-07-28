# Library edits - boards/pd-trigger/lib/aiee.pretty

Hand edits to pulled easyeda2kicad footprints. Every edit here was made by the P3
librarian agent under explicit orchestrator approval. Re-pulling a part with
`lib_pull.py --overwrite` DISCARDS these edits - re-apply from this file if that happens.
(Do not re-pull just to "clean up": the EasyEDA CAD endpoint rate-limits after ~3 passes,
and symbol pulls are not idempotent for names containing a space or `/`.)

Untouched by every edit below: all SMD pad geometry (position, size, shape, layers), all
courtyard geometry, all 3D model references, all `(property "LCSC Part" ...)` values.
Only `F.SilkS` graphics, two mechanical hole padstacks, and the `(model ...)` path string
changed.

## 2026-07-28 - P3 librarian

### Edit 0 (housekeeping, all 16 footprints): absolute 3D model paths

`lib_pull.py` was invoked with a RELATIVE `--out-dir`, and easyeda2kicad copies that
string verbatim into every footprint:

- BEFORE: `(model "boards/pd-trigger/lib/aiee.3dshapes/<name>.wrl"`
- AFTER:  `(model "C:/dev/ai-ee3/boards/pd-trigger/lib/aiee.3dshapes/<name>.wrl"`

KiCad resolves a relative model path against the project dir (`boards/pd-trigger/kicad/`),
where it does not exist, so STEP export and 3D render would have silently dropped all 16
models. Absolute paths match the run (b) `boards/usb-buck/lib` library. Path string only;
no geometry touched. All 16 referenced `.wrl` files verified present.

### Why edits 1-3

Three library-inherent defects found during P3 verification, all measured against real DRC
(scratch board: one instance of each of the 16 footprints, 30 mm apart, bare 2-layer board
with an Edge.Cuts rect, `kicad-cli 10.0.3 pcb drc --severity-all`, board-setup defaults
clearance 0.20 mm / min annular 0.10 mm - only intra-footprint findings can appear).

Pre-edit total: **17 violations = 4 errors + 13 warnings**, concentrated in 4 footprints.

### 1. USB-C-SMD_MC-311D.kicad_mod  (C5184243 GCT USB4105-GF-A-120, J1)

The land pattern itself is an exact match to the GCT drawing (rev B3 sheet 1/2) on every
published dimension and was NOT touched. The defect is in the two locating-peg holes.

- CHANGED both peg pads `thru_hole` -> `np_thru_hole`:
  - `(pad "" np_thru_hole circle (at 2.89 -1.30) (size 0.65 0.65) (drill 0.65) (layers *.Cu *.Mask))`
  - `(pad "" np_thru_hole circle (at -2.89 -1.30) (size 0.65 0.65) (drill 0.65) (layers *.Cu *.Mask))`
  - As pulled, copper diameter == drill diameter (0.65 == 0.65), giving 0.000 mm annular
    ring -> `annular_width` error x2 and `padstack` "PTH pad hole leaves no copper"
    warning x2; and each peg sat 0.1801 mm from the outer GND pad (`A1-B12` / `B1-A12`)
    -> `clearance` error x2 (rule 0.2000 mm).
  - They are mechanical, not electrical: the GCT drawing's bottom view shows `2x 0.50`
    plastic locating pegs, and the recommended PCB layout calls them `2x 0.65` holes with
    no solder area. The pin table lists only A1-A12/B1-B12 and SHELL - the pegs are not
    contacts. NPTH is the correct padstack; it also removes the floating copper annulus
    that sat 0.18 mm from a 5 A GND pad.
  - Position, diameter and drill are unchanged, so the 0.65 mm hole the datasheet asks for
    is still drilled in exactly the same place.
- DELETED `(fp_circle (center -4.47 -2.83) (end -4.44 -2.83) (layer F.SilkS) (width 0.06))`
  - r 0.03, stroke 0.06 (below JLC's 0.15 mm minimum line width, so it cannot print),
    drawn at the first courtyard vertex, no semantics. It overlapped shell-stake pad 1's
    copper by 0.057 mm and produced the `silk_over_copper` "Silkscreen clipped by solder
    mask" warning.
- Result for this footprint: **4 errors + 3 warnings -> 0**.

### 2. LED0603-RD.kicad_mod  (C7496813 TUOZHAN red, D5)

- DELETED `(fp_circle (center -0.80 0.40) (end -0.77 0.40) (layer F.SilkS) (width 0.06))`
  - r 0.03, stroke 0.06, sat 0.060 mm inside pad 1's copper (pad 1 = -0.75,0.00,
    size 0.80 x 0.80). Produced 1 `silk_over_copper` warning. Same defect and same fix as
    run (b) (`boards/usb-buck/lib/EDITS.md`).
- **Polarity cue confirmed intact after the edit** (this footprint keeps TWO independent
  cathode cues, both pointing at pad 1, which is what the symbol calls `K`):
  - the chamfered outline end over pad 1 (`(-1.19,+/-0.75)` -> `(-1.49,+/-0.45)` ->
    `(-1.49,+/-0.35)`), and
  - the diode glyph, whose triangle apex `(-0.12,-0.01)` points at pad 1 with its base bar
    at x = +0.22.
  - 16 F.SilkS elements remain, worst gap to copper 0.055 mm (pre-existing, DRC-clean).

### 3. LED0603-RD_GREEN.kicad_mod  (C965805 XINGLIGHT yellow-green, D3 and D6)

- DELETED `(fp_circle (center -0.80 0.40) (end -0.77 0.40) (layer F.SilkS) (width 0.06))`
  - Same artifact; 0.060 mm inside pad 1 (pad 1 = -0.80,0.00, size 0.80 x 0.80);
    1 `silk_over_copper` warning per instance (2 instances on this board).
- **Polarity cue confirmed intact**: the solid cathode bar
  `(fp_poly (pts (xy -0.2999 -0.4000) (xy -0.2999 0.4000) (xy -0.0999 0.4000)
  (xy -0.0999 -0.4000) ...) (fill solid))` - a 0.20 x 0.80 mm printable bar on the pad-1
  side - plus the chamfered outline end over pad 1. Symbol pin 1 = `K`, so cue and symbol
  agree. 11 F.SilkS elements remain, worst gap 0.1001 mm (the bar; pre-existing).

### 4. SW-SMD_6P-L7.6-W6.0-P2.54-LS9.3-BL.kicad_mod  (C7421520 3-position DIP switch, SW1)

- DELETED all five `fp_text user` marks on `F.SilkS` (each was 3 lines: the text, its
  `effects`, and the closing paren):
  - `(fp_text user ON (at -3.13 -1.88 0.00) (layer F.SilkS) ...)`
  - `(fp_text user 1 (at -2.67 2.74 0.00) (layer F.SilkS) ...)`
  - `(fp_text user 2 (at -0.25 2.74 0.00) (layer F.SilkS) ...)`
  - `(fp_text user 3 (at 2.29 2.74 0.00) (layer F.SilkS) ...)`
  - `(fp_text user KE (at 2.16 -1.90 0.00) (layer F.SilkS) ...)`
  - All five sat INSIDE the switch body outline (body/courtyard spans x +/-3.81,
    y +/-3.00), i.e. under the part and invisible after assembly, while colliding with the
    footprint's own silk outline segments -> 8 `silk_overlap` "Silkscreen clearance"
    warnings per instance. The user-facing profile table goes on B.SilkS at layout time
    per the architecture, so nothing readable is lost.
- KEPT unchanged: the three solid `fp_poly` slider-position indicators, the three switch
  body outlines, the outer body rectangle, and the 0.06 pin-1 dot at (-3.81, 4.65) (that
  one is 0.66 mm clear of copper and trips nothing). The standard
  `(fp_text reference REF**)` / `(fp_text value ...)` / `(fp_text user %R)` items are
  untouched.
- Result for this footprint: **8 warnings -> 0**.

### Declined by the orchestrator (documented, NOT edited)

- **U1 `ESSOP-10_L4.9-W3.9-P1.0-LS6.0-TL-EP` thermal pad keeps 100% paste.** Pad 11 is a
  3.30 x 2.10 mm aperture with full `F.Paste` coverage. Accepted for prototype qty 10;
  carried as an ORDER-DOC item for H5 human_steps, not a library change.
- **D1 `WSON-6_L2.0-W2.0-P0.65-BL-EP` pad deviation stays.** Pads are 0.40 mm wide vs TI's
  example layout 0.30 (0.25 mm inter-pad gap instead of 0.35), and the thermal land is
  1.60 x 1.00 vs TI's 1.60 x 1.10. Fabricable and DRC-clean.
- **The remaining 0.06 mm artifact dots stay** in C0603, C1206, F1206, R0603, R0805 and
  R1206 (each 0.05-0.07 mm inside pad 1), and the 0.15 mm circle that overlaps the
  ESSOP-10 thermal pad by 0.013 mm. Measured: none of the seven trips DRC (KiCad's
  clipped-by-mask test needs the item to straddle the mask aperture by more than a hair),
  and none is printable except the ESSOP one. Left alone deliberately - re-check if a
  future board sets a non-zero solder-mask expansion.

### Verification (all re-run after the edits)

| Check | Result |
|---|---|
| `kicad-cli 10.0.3 fp export svg` over the whole `.pretty` | 16/16 plotted, 0 errors -> `reports/fp_svg/` |
| Rendered delta, LED0603-RD / LED0603-RD_GREEN / USB-C | the artifact `<circle>` is gone from each rendered SVG |
| Rendered delta, SW-SMD_6P | "ON" / "KE" / "1" / "2" / "3" no longer present; slider indicators and outlines unchanged |
| Geometric re-measure (stroke edge to pad copper edge) | 0 silk elements overlap copper in the 4 edited footprints (LED-RD worst 0.055, LED-GREEN 0.1001, SW1 0.225, USB-C 0.1847) |
| Cathode cue survival | LED0603-RD: chamfer + glyph apex both at pad 1; LED0603-RD_GREEN: solid bar + chamfer at pad 1; both match symbol pin 1 = `K` |
| Scratch-board DRC, `kicad-cli pcb drc --severity-all`, 1 instance of all 16 footprints | **17 -> 0 violations** (was 4 errors + 13 warnings) |
| `fp_verify.py` re-run on U1 (untouched footprint) | pass, 0 violations, pitch 1.0 mm, 11 pads |
