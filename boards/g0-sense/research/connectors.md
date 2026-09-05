# connectors - candidate research (g0-sense)

Block: connectors and electromechanical/indicator parts. Five sub-functions:
USB-C power receptacle, Qwiic JST SH connector, 0.1in headers (SWD/UART,
unpopulated), NRST tactile button, user+power LEDs. All candidates verified
live via `parts_search.py` (JLCPCB), stock/price as of this run. Full sweeps:
`research/raw/connectors-sweep.json`. Prices are the qty-1 break, which is
also the break that applies at this board's build qty of 5 (no candidate's
first price tier breaks below qty 5).

## 1. USB-C receptacle (power-only, 16-pin)

Must-haves: 16P (power-only pinout, D+/D- present but left NC per
requirements.md), exposes CC1/CC2 for 5.1k pulldowns, SMD reflow pads,
handles 5V/<1A with margin.

| rank | mpn | lcsc | current | stock | price@1 | basic | KiCad fp | datasheet |
|---|---|---|---|---|---|---|---|---|
| 1 | TYPE-C-31-M-12 | C165948 | 20V/5A | 371,004 | $0.1855 | no | YES (exact) | yes |
| 2 | TYPE-C16PIN | C393939 | 30V/3A | 439,594 | $0.0686 | no | none (needs pull) | yes |
| 3 | TYPE-C-3.1-16PIN | C7507405 | 3A/5V | 13,772 | $0.0705 | no | none | none on file |
| 4 | TYPE-C-16PIN-0 | C53207865 | 20V/3A | 903 | $0.0665 | no | none | none on file |

No JLC Basic 16P USB-C receptacle exists (checked with `--basic-only`, zero
rows across several query phrasings) - Extended is the only tier available
for this part class, which is what the brief anticipates by naming this
connector as an Extended exception.

**Top pick and why:** C165948 (Korean Hroparts Elec, TYPE-C-31-M-12). It is
the only one of the four with a ready-made KiCad footprint
(`Connector_USB.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod`,
confirmed present in this image's library). That removes an entire class of
risk this repo's own LEARNINGS documents for pulled 16P USB-C footprints
(plated peg holes registering as DRC errors, silk-vs-copper clearance
violations, off-origin Reference text). C393939 (SHOU HAN) is 2.7x cheaper
and has the deepest stock of any candidate by far, but has no vendor-specific
KiCad footprint in the library, so picking it commits P4/P8 to a pulled or
hand-built footprint.

**Mount type / THT-leg flag (read this before P3 picks a part):** EVERY 16P
candidate checked in this price class is a hybrid part, not full-SMD. Direct
evidence:
- C165948's KiCad footprint pads: 16x SMD roundrect signal pads + **4x
  `thru_hole` oval pads named "SH"** (plated, shield/ground) + 2x
  `np_thru_hole` circular alignment holes.
- C393939's vendor drawing (pulled PDF, read directly per the
  vendor-drawing-over-catalog-field rule): 16 SMD signal pads + **2x
  0.65mm-dia THT shield/mounting legs**, same hybrid pattern.

Both candidates FLAG THE SAME WAY the brief warned about: the shield/ground
return needs a through-hole solder joint for mechanical strength, and JLC
economy PCBA is SMT-reflow only. This means, whichever 16P part P3 finally
picks, **the assembly plan needs an explicit answer for those 1-4 THT
legs** - options are (a) accept them as unsoldered/tack-soldered plated
mechanical pegs (common in practice; electrically the shield is often also
carried redundantly through a few of the "GND" SMD signal pads, so leaving
the THT legs cold does not necessarily orphan the shield net - verify this
against the specific part's pinout at P3/P4), (b) a manual hand-solder step
added to the assembly process after the economy PCBA run, or (c) a different
JLC assembly tier that includes THT placement. This is a decision for the
architect/part-sourcer, not this scout - flagging it because it changes the
assembly plan and the brief asked for it explicitly.

**Orientation/rotation risk:** USB-C receptacles are a known JLC CPL
rotation-error class industry-wide (the housing/courtyard can look
deceptively symmetric). This repo's own LEARNINGS (2026-07-28,
placement/kicad) independently confirms the mating-direction trap for USB-C:
the WRL bounding box is a coincidence trap and mating direction must be read
from the WRL or an orthographic side render, not the silk outline or
courtyard shape. Recommend P6/P8 double-check the final CPL rotation for
whichever part is chosen against its datasheet pin-1/orientation marker
before order submission.

## 2. JST SH 1.0mm 4-pin (Qwiic/STEMMA-QT)

Must-have: right-angle/horizontal SH-1.0 4-pin (the Qwiic mechanical
standard).

| rank | mpn | lcsc | stock | price@1 | basic | KiCad fp |
|---|---|---|---|---|---|---|
| 1 | SM04B-SRSS-TB(LF)(SN) | C160404 | 39,690 | $0.2131 | no | YES (exact, JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal) |
| 2 | XY-SM04B-SRSS-TB | C51940130 | 5,425 | $0.0392 | no | same family (clone) |
| 3 | HX SH-1.0-4PWT | C22461259 | 4,778 | $0.0395 | no | same family (clone) |

Genuine JST (C160404) is the MPN the Qwiic/STEMMA-QT standard is built
around and has an exact KiCad footprint in `Connector_JST.pretty`. Both
clones (XYECONN, hanxia) are ~5.4x cheaper and copy the same body/pinout, so
they should sit in the same footprint - no clone-specific datasheet was
found for the XYECONN part, so a dimension re-check against JST's own
drawing is cheap insurance if the clone is picked. No JLC Basic SH-1.0 4-pin
exists (checked; this connector class is Extended-only on JLC, consistent
with the brief's Extended exception for named connectors).

## 3. 0.1in (2.54mm) headers - 1x4 THT, SWD and UART (ships unpopulated)

Per requirements.md section 7 (already decided): both headers ship DNP -
JLC economy PCBA is SMT-only, so this is a footprint/BOM reference, not an
assembly part. Any generic 1x4 2.54mm THT header is mechanically
interchangeable and matches KiCad's standard
`Connector_PinHeader_2.54mm.pretty/PinHeader_1x04_P2.54mm_Vertical`
footprint (confirmed present in this image's library) - one header MPN
covers both the SWD and UART footprints (2x qty needed per board).

| rank | mpn | lcsc | stock | price@1 | datasheet |
|---|---|---|---|---|---|
| 1 | HX PZ2.54-1x4P ZZ | C32713270 | 158,769 | $0.0335 | yes |
| 2 | PZ2.54-1X4P-H25 | C42431787 | 24,411 | $0.0212 | none on file |
| 3 | B-2100S04P-A110 | C124378 | 116,170 | $0.0559 | yes (-40..105C rated) |

Recommend C32713270 for the BOM DNP line (best stock + has a datasheet on
file); price is immaterial since it is not populated at assembly.

## 4. Tactile push button (NRST)

Must-have: SMD, small (brief names 3x2.5mm or 4.2x3.2mm class), JLC Basic
preferred.

| rank | mpn | lcsc | footprint (LxW) | height | basic | stock | price@1 |
|---|---|---|---|---|---|---|---|
| 1 | TS-1187A-B-A-B | C318884 | 5.1 x 5.1 mm | 1.5mm | **yes** | 962,845 | $0.0205 |
| 2 | HX 3x4x2-2P-1.6N | C49234124 | 4 x 3 mm | 2mm | no | 230,605 | $0.0254 |
| 3 | TS263065A ... | C49023761 | 3 x 2.6 mm | 0.65mm | no | 7,241 | $0.0572 |
| 4 | HX 2.75x3x1.4-4P-1.6N | C55200584 | 3.4 x 2.75 mm | 1.4mm | no | 86 | $0.0596 |

No candidate found in the exact 3x2.5mm/4.2x3.2mm classes named by the
brief that is also JLC Basic - the only Basic tactile switch found
(C318884) is 5.1x5.1mm, noticeably larger. Ranked it #1 anyway per the
brief's own "JLC Basic preferred" instruction and because it is one of the
most widely reused JLC Basic buttons with no known footprint/DRC issues (no
setup fee, huge stock margin). C49234124 (4x3mm, Extended) is the closest
size match if the smaller footprint matters more than Basic status.

**Risk flag:** C49023761 (TS263065A ...) is smallest+lowest-profile of the
four and closely matches the brief's named size class, but this exact MPN
is a documented risk in this repo's own LEARNINGS
(2026-07-28, `[easyeda2kicad][parts]` "Symbol pulls are NOT idempotent for
names with spaces or '/'"): the part's own name broke `lib_pull`'s symbol
pull silently while still reporting "pulled". If P4 picks this part,
verify the pulled symbol by hand rather than trusting `lib_pull`'s status
field. C55200584's stock (86 pcs) covers a 5-board build with zero spare
margin - fine for this run, not reorder-safe.

## 5. LEDs (user + power), 0603 SMD

Must-have: 0603, JLC Basic preferred, low-current operation (this board
should drive LEDs well below their rated test current) - Vf and mcd
reported so the architect can size series resistors off 3.3V.

| rank | mpn | lcsc | color | basic | test cond. | Vf typ | Iv (min-max) | stock | price@1 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | KT-0603R | C2286 | red | **yes** | IF=20mA | 1.8-2.4V | 145-300mcd | 5,413,261 | $0.0074 |
| 2 | KT-0603W | C2290 | white (cool, CCT 40-100k K) | **yes** | IF=5mA | 2.6-3.1V | 145-360mcd | 1,542,923 | $0.0122 |
| 3 | KT-0603G | C12624 | emerald green | no | IF=5mA | 2.6-3.1V | 210-430mcd | 278,476 | $0.0122 |
| 4 | KT-0603B | C2288 | blue | no | IF=5mA | 2.6-3.1V | 70-175mcd | 213,979 | $0.0103 |

All four are the same Hubei KENTO Elec KT-0603 family (pulled datasheets
directly, not just the JLC catalog fields). Two colors already directly
specify Iv at 5mA (green, blue, white) - exactly one of the brief's two
requested test points. None specify 2mA; the datasheet's own Iv-vs-If
curve for the red part is sub-linear at low current (not a straight line
through the origin), so 2mA values below are read off that curve, not a
bin spec:

- **Red (KT-0603R):** only specified at IF=20mA (Vf 1.8-2.4V typ, Iv
  145-300mcd, typ ~220mcd). Curve-read estimate: roughly 80-110mcd @ 5mA,
  30-45mcd @ 2mA.
- **Green/Blue/White:** directly specified at IF=5mA (see table). At 2mA,
  expect roughly 40-60% of the 5mA value for these InGaN dies (they are
  closer to linear at low current than the red AlGaInP die, but no direct
  2mA datasheet point exists for any of them either).

**Vf flag for the architect:** red's Vf (1.8-2.4V) is nearly a volt lower
than green/blue/white's (2.6-3.1V). At 3.3V supply, that is the difference
between a series resistor with real headroom (red) and one with only
0.2-0.7V of headroom (green/blue/white) at whatever low current is chosen -
worth checking resistor tolerance and Vf bin spread doesn't push a
green/blue/white LED's required resistor value negative or unstable at the
low end of the current target.

## Open risks summary

- USB-C: every practical 16P candidate at this price point has THT
  shield/mounting legs - a full-SMT USB-C receptacle does not exist in this
  size/price class on JLC. Assembly-plan decision needed (see section 1).
- USB-C: no KiCad-standard footprint for the cheapest/highest-stock part
  (C393939); picking it means a pulled or hand-built footprint.
- JST SH: Extended-only part class on JLC (no Basic SH-1.0 4-pin found).
- Button: the closest-size-match part (C49023761) has a known symbol-pull
  gotcha in this repo's LEARNINGS; verify by hand if picked.
- LED: no datasheet gives Iv at 2mA for any color; all 2mA figures above are
  curve/ratio estimates, not vendor bin specs.
