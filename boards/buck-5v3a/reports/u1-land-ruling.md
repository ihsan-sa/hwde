# U1 (AP63356QZV-7, V-DFN3020-13/SWP Type A1) - land ruling

## ANSWER

**Answer (a), with a correction to its premise. The recommended land pattern has EXACTLY 9 copper
lands. There is NO exposed pad, NO thermal/belly pad, and NO central land of any kind. The
EasyEDA/LCSC footprint's 9 pads are CORRECT in count and correct in position; it is NOT missing
pads. The "13" in the package name counts PACKAGE TERMINALS, not PCB lands: VIN and GND each
occupy a multi-terminal run that the vendor's own land pattern solders with ONE land each.**

The theta_JA=25 C/W argument for a belly pad is refuted - see section 4. The `fp_verify` error
"copper pad count 9 != datasheet 13" is a FALSE POSITIVE and should be waived, not fixed.

---

## 1. Decisive evidence: the vendor's Suggested Pad Layout

Source A: datasheet on disk, `boards/buck-5v3a/parts/C3194571.pdf`, **page 27 of 28**
(AP63356Q/AP63357Q, doc DS41948 Rev. 1-2, Sept 2020), section "Suggested Pad Layout",
drawing titled "V-DFN3020-13/SWP (Type A1)".

Source B (independent vendor primary source, same drawing published standalone):
**https://www.diodes.com/assets/Package-Files/V-DFN3020-13-SWP-Type-A1.pdf** , dated 2020-09-01,
"Package Outline Dimensions" + "Suggested Pad Layout". Fetched and read; the drawing and the
dimension table are byte-for-byte the same content as datasheet p.27.

Read visually at 18x-22x zoom. The drawing contains three kinds of land, and the multiplicity is
annotated on the drawing itself:

| annotation | count | size (mm) | what it is |
|---|---|---|---|
| `X1(2x)` / `Y1(2x)` | **2** | 0.80 W x 1.450 H | the two large end lands |
| `X2` / `Y2` | **1** | 0.30 W x 1.725 H | narrow centre land (NOT a thermal pad) |
| `X(6x)` / `Y(6x)` | **6** | 0.60 W x 0.30 H | signal lands, two columns of 3 |
| | **9 total** | | |

The multiplicity suffixes `(2x)` and `(6x)` are printed on the drawing. 2 + 1 + 6 = 9. There is no
fourth land type and no unannotated land.

**Arithmetic proof that the drawing closes at 9 and cannot hide a 10th land** (dimension table,
same page): overall pattern height `Y3 = 2.825`. Building it up from the parts:

```
Y1 (large land)      1.450
G  (gap)          +  0.175
3 small lands at C=0.45 pitch, each Y=0.30 -> 2*0.45 + 0.30 = 1.200
                  ---------
                     2.825  == Y3   EXACT
```

and across: overall pattern width `X3 = 2.30`, which equals the two 0.60-wide signal-land columns
plus the gap between them. Every millimetre of the stated envelope is accounted for by the 9
lands. A thermal pad has nowhere to be.

## 2. The package outline (why "13"), and the Pin Assignments cross-check

Datasheet p.27 "Package Outline Dimensions", bottom view, read at 22x zoom. What the drawing
actually shows as physical terminals:

- one **large terminal at top-right**, callout `1`, dimensioned `L1 = 0.60 W x L2 = 1.525 H`,
  carrying two side-wettable flank notches at `e1 = 0.575` spacing, with the pin-1 chamfer (R0.15)
  on its inboard corner;
- one **large terminal at top-left**, callout `12`, same L1/L2 geometry, also two flank notches;
- one **narrow centre bar**, callout `13`, width = `b` (0.20 typ), running from the top edge to
  just past the package centreline;
- **3 small terminals down the right edge and 3 down the left edge**, width `b = 0.20`, length
  `L = 0.40`, pitch `e = 0.45`.

The callouts `1`, `12`, `13` on lands that are physically continuous is the whole explanation. The
numbering runs 1..13 around the part; the datasheet's 9 named electrical pins map onto it as:

- VIN  = terminals **1-3** (one continuous land, callout shows the extreme number `1`)
- EN, FB, COMP, PG, BST, NC = terminals **4-9** (the six small ones, one land each)
- GND  = terminals **10-12** (one continuous land, callout shows the extreme number `12`)
- SW   = terminal **13** (the centre bar)

3 + 6 + 3 + 1 = 13 terminals -> 9 lands. The 3-per-large-terminal grouping is *inferred* from the
callout numbers `1` and `12` bracketing exactly six small terminals; the drawing itself only draws
2 wettable-flank notches per large terminal, so the exact internal split could be other than 3/3.
**This inference is not load-bearing:** whichever way the terminal numbers divide, both the package
outline and the suggested pad layout show each large terminal as ONE continuous piece of metal
soldered by ONE land.

**Cross-check, Pin Assignments figure, datasheet p.1 (TOP view), and it agrees exactly.** The
figure draws the top row as three lands - `1` VIN (large, left), `9` SW (centre), `8` GND (large,
right) - and two columns of three below: `2` EN / `3` FB / `4` COMP down the left, `7` NC / `6` BST
/ `5` PG down the right. Nine lands drawn, nine lands named, no unnamed land in the figure. Mirror
the top view to a bottom view and VIN lands on the right, which is where the outline drawing puts
callout `1`. Consistent.

**No land is shown that the pin table does not name.** This directly answers question 3 of the
brief: no.

## 3. Land map (vendor values, datasheet drawing orientation: body D=2.00 wide x E=3.00 tall)

| land | pin name | pin no. | pkg terminals | land size (mm) | position |
|---|---|---|---|---|---|
| large, left of top row (top view) | VIN | 1 | 1-3 | 0.80 x 1.450 | top-left corner of pattern |
| narrow, centre of top row | SW | 9 | 13 | 0.30 x 1.725 | centred; extends 0.275 further outboard than the two large lands |
| large, right of top row | GND | 8 | 10-12 | 0.80 x 1.450 | top-right corner of pattern |
| small | EN | 2 | 4 | 0.60 x 0.30 | left column, 1st below the large land, gap G = 0.175 |
| small | FB | 3 | 5 | 0.60 x 0.30 | left column, 2nd, pitch C = 0.45 |
| small | COMP | 4 | 6 | 0.60 x 0.30 | left column, 3rd, pitch C = 0.45 |
| small | PG | 5 | 7 | 0.60 x 0.30 | right column, 3rd |
| small | BST | 6 | 8 | 0.60 x 0.30 | right column, 2nd |
| small | NC | 7 | 9 | 0.60 x 0.30 | right column, 1st below the large land |

Envelope: `X3 = 2.30` wide x `Y3 = 2.825` tall measured to the large lands' outer edge; the SW
centre land protrudes a further 0.275 outboard, so the true envelope is 2.30 x 3.10.
Other vendor dims: `C = 0.45` (signal pitch), `G = 0.175` (large-land-to-first-signal-land gap).

Package terminals for reference: `b = 0.15/0.20/0.25` terminal width, `L = 0.35/0.40/0.45` signal
terminal length, `L1 = 0.55/0.60/0.65` and `L2 = 1.475/1.525/1.575` large terminal, `e = 0.45 BSC`,
`e1 = 0.575 BSC`, `e2 = 0.475 BSC`, `D = 2.00 BSC`, `E = 3.00 BSC`, `A = 0.80/0.85/0.90`.

## 4. Thermal characteristics - what the datasheet actually quotes, and why it does not imply a belly pad

Datasheet p.4, "Thermal Resistance (Note 6)":

- `theta_JA` Junction to Ambient, V-DFN3020-13/SWP (Type A1) = **25 C/W**
- `theta_JC` Junction to **Case** = **5 C/W**
- Note 6: *"Test condition for V-DFN3020-13/SWP (Type A1): Device mounted on FR-4 substrate,
  four-layer PC board, 2oz copper, with minimum recommended pad layout."*

Three points that dismantle the "25 C/W requires a belly pad" inference:

1. **It is theta_JC, not theta_JC(bottom).** The brief correctly notes that a theta_JC(bottom)
   figure would be strong evidence of a bottom thermal land. Diodes does **not** quote
   theta_JC(bottom). It quotes plain "Junction to Case", which carries no bottom-land implication.
   The evidence the brief was looking for is absent.
2. **"minimum recommended pad layout" is the 9-land pattern of p.27.** Diodes is explicitly stating
   that 25 C/W is achieved *with that pattern*, i.e. with no thermal pad, on 4-layer 2oz FR-4.
3. **The sibling part quotes the same numbers for the non-SWP package.** Datasheet DS41949 Rev.3-2
   (AP63356/AP63357, https://www.diodes.com/assets/Datasheets/AP63356-AP63357.pdf, p.5) quotes
   theta_JA = 25 C/W and theta_JC = 5 C/W for "V-DFN3020-13 (Type A)". Same figures, same 9-land
   family. Nothing in either variant references an exposed pad.

**And the vendor states the heat path in words.** Datasheet p.25, section "Layout" / "PCB Layout",
items 7 and 8, verbatim:

> 7. Add as many vias as possible around both the **GND pin** and under the GND plane for heat
>    dissipation to all the GND layers.
> 8. Add as many vias as possible around both the **VIN pin** and under the VIN plane for heat
>    dissipation to all the VIN layers.

Item 6: *"If using four or more layers, use at least the 2nd and 3rd layers as GND to maximize
thermal performance."* Item 1: *"2oz copper for both the top and bottom layers is recommended."*

The word "pad" in the thermal sense, "exposed pad", "thermal pad", "belly pad", or "E-pad" appears
**nowhere** in either datasheet. The vendor names the GND pin and the VIN pin as the heat exits.
Figure 47 "Recommended PCB Layout" (p.25) draws exactly that: vias sitting in and immediately
around the large VIN land and the large GND land, pouring into planes. There is no central land in
Figure 47 either.

Physically this is coherent: the two large lands are 0.80 x 1.450 = 1.16 mm^2 each, plus SW at
0.52 mm^2, so ~3.9 mm^2 of solderable copper under a 6.0 mm^2 package footprint - about 65%
coverage. That is a lot of metal for a 2x3 part even without a centre pad.

## 5. The KiCad footprint on disk - what it actually contains

File: `C:\dev\ai-ee3\boards\buck-5v3a\lib\aiee.pretty\V-DFN3020-13-A_L3.0-W2.0-P0.45-BL-EP_AP6335X.kicad_mod`
(assigned to U1; confirmed as `footprint_file` in `reports/fp_verify/U1_C3194571.json`).
Note the footprint is rotated 90 deg relative to the datasheet drawing: datasheet Y -> footprint X.

Full pad list, all `smd rect`, all on `F.Cu F.Paste F.Mask`, no pad numbered >= 10, no other layers:

| pad | net/pin | at (x, y) mm | size (x, y) mm |
|---|---|---|---|
| 1 | VIN | -0.92, +0.75 | 1.500 x 0.750 |
| 2 | EN | +0.13, +0.85 | 0.200 x 0.600 |
| 3 | FB | +0.58, +0.85 | 0.200 x 0.600 |
| 4 | COMP | +1.03, +0.85 | 0.200 x 0.600 |
| 5 | PG | +1.03, -0.85 | 0.200 x 0.600 |
| 6 | BST | +0.58, -0.85 | 0.200 x 0.600 |
| 7 | NC | +0.13, -0.85 | 0.200 x 0.600 |
| 8 | GND | -0.92, -0.75 | 1.500 x 0.750 |
| 9 | SW | -1.03, 0.00 | 1.730 x 0.350 |

Pad-to-pin assignment is CORRECT: pads 1 and 8 are the two large lands (VIN, GND), pad 9 is the
narrow centre land (SW), pads 2-7 are the six signal lands. This matches section 3 exactly.

### Conformance to the Diodes land pattern

| Diodes dim | value | footprint equivalent | delta |
|---|---|---|---|
| `X3` overall (across columns) | 2.30 | 2.30 (pads at y=+/-0.85, len 0.600 -> +/-1.15) | **0.000 exact** |
| `C` signal pitch | 0.45 | 0.45 (x = 0.13 / 0.58 / 1.03) | **0.000 exact** |
| `X` signal land length | 0.60 | 0.600 | **0.000 exact** |
| `Y3` large-land edge to signal-land edge | 2.825 | 2.80 (x = -1.67 .. +1.13) | -0.025 |
| `G` large-to-signal gap | 0.175 | 0.20 | +0.025 |
| `Y1` large land length | 1.450 | 1.500 | +0.050 |
| `X1` large land width | 0.80 | 0.750 | -0.050 |
| `Y2` centre land length | 1.725 | 1.730 | +0.005 |
| `X2` centre land width | 0.30 | 0.350 | +0.050 |
| `Y` signal land width | **0.30** | **0.200** | **-0.100  <-- only real deviation** |

**Verdict: the footprint is the Diodes recommended land pattern, not a corrupted one.** Nothing is
missing. Nine lands is right. The envelope and pitch close to 0.00-0.03 mm.

### Actionable defects found (all minor; none is a missing pad)

1. **Signal lands are 0.10 mm too narrow.** Pads 2-7 are `0.200 x 0.600`; Diodes specifies
   `0.300 x 0.600` (`Y = 0.30`). EasyEDA used the terminal width `b = 0.20 typ` instead of the
   recommended land width. At `b_max = 0.25` the terminal overhangs the land by 0.025 mm per side.
   Fix: set pads 2..7 size to `0.300 0.600`, positions unchanged. Resulting land-to-land gap
   becomes 0.45 - 0.30 = 0.15 mm, and gap to pads 1/8 becomes 0.15 mm - both manufacturable.
2. **`(attr through_hole)` on an all-SMD footprint** (line 2). Wrong; should be `smd`. Affects
   DFM classification, pick-and-place export and BOM/CPL generation.
3. **Courtyard is undersized and is in fact the body outline.** `F.CrtYd` is the rectangle
   (-1.74, -1.00) to (+1.26, +1.00), i.e. exactly the 3.00 x 2.00 body. It does not enclose the
   pads: pad 9 reaches x = -1.895 and pads 2-7 reach y = +/-1.15. Needs to be re-cut around the
   real pad envelope plus clearance.
4. **Footprint origin is offset ~0.24 mm from the body centre** in x (body spans -1.74..+1.26).
   Cosmetic/placement-convention only; does not affect solder joints.
5. Optional: pad 9 could go to `0.300` wide and pads 1/8 to `0.800 x 1.450` to be exactly on the
   vendor drawing. Low value - current values are within 0.05 mm.

### `fp_verify` correction

`reports/fp_verify/U1_C3194571.json` currently raises `severity: error`,
`"copper pad count 9 != datasheet 13"`. **This is a false positive and should be waived.** Its
`land_pattern.notes` field also contains a wrong claim, produced from text extraction without
reading the drawing:

> "the Suggested Pad Layout drawing shows 13 total physical solder lands (read as approx. 6 small
> pads per side + 2 larger end pads per side ...)"

The drawing shows **3 small lands per side (6 total, annotated `X(6x)`), 2 large lands total
(annotated `X1(2x)`), and 1 centre land = 9**. There are not 6 small pads per side and there are
not 2 large pads per side. `land_pattern.pad_count` should be **9 lands / 13 terminals**, and the
pad-size expectation should be recorded per land class (0.60x0.30 x6, 0.80x1.450 x2, 0.30x1.725
x1) rather than as a single value - which is also what produced the second, misleading
`pad_size` warning.

## 6. Consequence for the thermal analysis

**NO.** There is no belly pad, therefore no via array under a belly pad exists as a heat path; the
sole conductive escape from the die is the VIN land (1.16 mm^2) and the GND land (1.16 mm^2), so
the thermal model must place the vias in and immediately around those two lands, per Diodes p.25
items 7-8 and Figure 47.

Two caveats for whoever redoes the numbers:

- `theta_JA = 25 C/W` is **not** invalidated - it is the vendor figure for this exact 9-land
  pattern - but it is conditional on Note 6's construction: FR-4, four layers, 2oz copper, with
  2nd and 3rd layers as GND (p.25 item 6). This board is 4L JLC04162H-7628A with 2oz outers
  (state.json, P1 human approval), which matches the intent; confirm the inner-layer copper weight,
  since JLC 4L inners are commonly lighter than 2oz and Note 6's "2oz copper" is unqualified.
- Because the heat leaves through VIN and GND rather than a centre pad, the via count and plane
  connection on those two specific 0.80 x 1.450 lands is the dominant layout lever. They are small:
  expect roughly 2 vias per land in-pad (as Figure 47 draws) plus a dense ring immediately outboard.
  In-pad vias on 0.80 x 1.450 lands will need tenting/plugging called out for JLCPCB or they will
  wick paste.

---

### Sources

- `C:\dev\ai-ee3\boards\buck-5v3a\parts\C3194571.pdf` - AP63356Q/AP63357Q datasheet, doc
  DS41948 Rev. 1-2, September 2020. Pages read visually: p.1 (Pin Assignments), p.4 (Thermal
  Resistance + Note 6), p.25 (Layout, Figure 47), p.26 (Ordering/Marking), p.27 (Package Outline
  Dimensions + Suggested Pad Layout).
- https://www.diodes.com/assets/Package-Files/V-DFN3020-13-SWP-Type-A1.pdf - Diodes Incorporated
  standalone package-outline + suggested-pad-layout sheet for V-DFN3020-13/SWP (Type A1),
  dated 2020-09-01. Independent confirmation of the 9-land pattern.
- https://www.diodes.com/assets/Datasheets/AP63356-AP63357.pdf - AP63356/AP63357 datasheet,
  DS41949 Rev. 3-2, p.5 thermal table (Type A: 25 / 5 C/W) and p.26 PCB Layout.
- `C:\dev\ai-ee3\boards\buck-5v3a\lib\aiee.pretty\V-DFN3020-13-A_L3.0-W2.0-P0.45-BL-EP_AP6335X.kicad_mod`
- `C:\dev\ai-ee3\boards\buck-5v3a\reports\fp_verify\U1_C3194571.json`

Note: www.diodes.com/part/view/AP63356Q returns HTTP 403 to automated fetch; the two asset PDFs
above are on the same vendor domain and were retrieved directly.
