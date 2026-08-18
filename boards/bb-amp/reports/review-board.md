# bb-amp - P8 board review (adversarial, fresh context)

Scope: mode `learning block-basics:` -> tier `block-only`, binding `canonical`.
Nothing below reports an absent feature class the tier excludes (protection,
filtering, indicators, test points, config, second rail, mechanical/enclosure).
Every claim here was measured from `kicad/bb-amp.kicad_pcb`, the footprint
files, the symbol library and my own plots - not read off the pipeline's
reports. Where a pipeline claim was checked and held, it is recorded as held.

**2 errors, 3 warnings, 1 waiver upheld.**

Renders I made for this review:
- `reports/renders/bb-amp_F-SilkS-only.svg` - F.SilkS + Edge.Cuts, nothing else.
  This is the picture behind finding 1.
- `reports/renders/bb-amp_top-silk-cu.svg` - F.SilkS + F.Cu + Edge.Cuts.
- `reports/renders/bb-amp_bcu-pour-verify.png` - the B.Cu fill polygon drawn
  from its own 528 vertices, with the input pair (cyan) and its pads (red)
  overlaid. This is the picture behind verification 2.

---

## ERROR 1 - the board carries no connector pole legend at all, and the
## schematic says twice that it must

`kicad/bb-amp.kicad_pcb` contains exactly 14 pieces of silkscreen text: the 14
refdes. There is no `gr_text` anywhere on the board and no `fp_text` on F.SilkS
other than each part's own designator. See
`reports/renders/bb-amp_F-SilkS-only.svg`: three screw terminals, seven poles,
zero pole markings.

The design's own artifacts demand otherwise. The schematic sheet carries, in its
own text, both of these:

- `J1 POLE ORDER: IN- / IN+ / GND - the silk legend must read that way`
- `... THE SILK MUST SAY IN- / IN+ / GND.`

and `requirements.md` s2 promises terminals "silkscreened IN+ / IN- / GND /
OUT / +3V3". None of it reached the board.

The only pole-1 indication on any of the three connectors is a 0.21 mm dot
(`fp_circle` at footprint-local (-7.62, 5.30) for J1, (-5.08, 5.30) for J2/J3).
Placed, J1's dot lands at board (14.000, 24.920) - exactly the corner of the
connector's own body outline, i.e. **under the plastic**. After assembly there
is no way to tell pole 1 from pole 3 on any terminal.

All three terminals are hand-soldered and hand-wired by the owner
(`requirements.md` s7), so the silk is the only thing standing between the user
and a miswire. Consequences, worst first:

- **J3 reversed** (pole 1 `+3V3` at x=39.46, pole 2 `GND` at x=44.54, and
  nothing on the board says so): -3.3 V lands on U1 pin 8 and U2 pin 8. Both
  parts are past their absolute-maximum supply pin rating and are destroyed.
  I am *not* reporting the absence of reverse-polarity protection - that is
  correctly excluded at `block-only`. I am reporting that excluding it makes
  the legend load-bearing, and the legend is missing.
- **J1 poles 1/2 reversed**: Vdiff is negated, so U1's output wants
  0.252 - 39.9*Vdiff. Every positive input drives stage 1 below its guaranteed
  0.10 V floor, and the board output sits pinned near the bottom rail across
  the entire 0-20 mV span. It reads as a dead amplifier, not as a wiring error
  - which is the same presentation as the bias-return failure the workspace has
  already recorded as symptomless.
- **J1 poles 2/3 reversed**: the sensor's ground lands on IN+; same saturation.
- **J2 reversed**: reading is zero, or the meter's ground is lifted onto /VOUT.

Is there room? Tight, but yes for the critical one. Measured free F.SilkS bands:
J1 has a clear 0.95 mm strip outboard at x 13.00..13.95 (rotated text) and a
clear ~2.1 mm strip inboard at x 24.80..26.90 between the body and R1. J2 has
only ~0.65 mm (x 48.6..49.25 inboard, R4 blocks the rest) plus the top edge band
y 23.55..24.20 once J2's own refdes is moved. J3 has a ~0.6 mm band at
y 39.50..40.10. So J1 is fixable in place; J2 and J3 realistically want 1.5-2 mm
more board on their edges. Under `canonical` binding that is not a violation of
the earned-outline principle, it *is* the principle - the board becomes what the
placement needs, and a legend the schematic mandates is part of what it needs.

Domain: silk (plus a small `board_edit --outline` grow if J2/J3 are to be
labelled properly).

## ERROR 2 - every human-facing document states the OPPOSITE pole order to the board

The board is **pole 1 = IN-, pole 2 = IN+, pole 3 = GND** (J1 pad 1 -> /IN_N ->
U1.1 `-IN`; pad 2 -> /IN_P -> U1.4 `+IN`). This was a deliberate P6 swap to
uncross the pair, and it is right.

But the documents a human reads at H4 all say the other thing:

| artifact | says | correct? |
|---|---|---|
| `kicad/bb-amp.kicad_sch` (text notes) | IN- / IN+ / GND | YES |
| `log/P6-digest.md` | pole 1 = IN-, pole 2 = IN+ | YES |
| `architecture/blocks.md` B1 | "3-pole ... IN+ / IN- / GND" | **NO** |
| `requirements.md` s2 (x2) and 9a Q2 | "3 poles (IN+, IN-, GND)" | **NO** |
| `reports/design_doc/bb-amp-design-doc.tex/.pdf` (4 places) | IN+ / IN- / GND | **NO** |

The design doc was generated 2026-08-16 21:28, i.e. at H1, and was never
regenerated after the 2026-08-17 swap. It is the artifact H4 actually reads.

On its own this is documentation drift. Combined with ERROR 1 it is a wiring
error waiting to happen: the board has no legend, so the user consults the
design doc, and the design doc is wrong. Either fix alone closes the loop;
neither has been done.

Domain: review (fix = update blocks.md B1 + requirements.md s2/9a Q2 to match
the schematic, and regenerate the design doc).

---

## WARNING 3 - verify_all ran 2 of its 8 checks; the verify gate reports 8 of 8

`reports/verify_all.json` (and the identical `kicad/reports/checks/summary.json`)
records `coverage.ran = [check_diffpair, check_silk]` and
`skipped_error = {check_return_path: "no constraints", check_current: "no
constraints", check_decoupling: "no decoupling", check_creepage: "no
constraints", check_thermal: "no constraints", check_pdn: "no
constraints/decoupling"}`. verify_all was invoked without `--constraints` and
without `--decoupling`, even though `kicad/constraints.json` and
`kicad/decoupling.json` both exist - and their digests are recorded in
`gate-verify.json`'s own `record_result.inputs`.

`reports/gate-verify.json` then reports `coverage.ran` = all eight,
`passed` = all eight, `skipped_error = {}`. A reader of the gate cannot see the
hole. Per my own brief, a skipped check is a hole, not a pass - so I closed it
myself. Re-running all six against the real constraint files:

| check | result |
|---|---|
| check_return_path | pass, but `checked: []` - needs a `high_speed` list, which this board has none of. Vacuous. |
| check_current | **real pass** - +3V3 needs 0.005 mm, board has 0.2 mm |
| check_creepage | pass, `checked: []` - the only `voltage_pair` is 0.025 V. Vacuous, and correct: nothing here is above 30 V |
| check_thermal | pass, `checked: []` - no thermal list. Vacuous, and correct: 2.3 mW total |
| check_decoupling | **real pass** - C1 1.50 mm / 2.69 nH, C3 1.53 mm / 2.71 nH, C2 bulk 15.99 mm / 12.97 nH, each with its own GND via within 1.11 mm |
| check_pdn | **real pass** - +3V3 has 3 caps, 10.2 uF, 1 bulk |

So **no defect is hiding behind the hole**, and the board's real return-path
question is answered directly in verification 2 below. The finding is that the
gate's coverage reporting is wrong and would hide a real hole on the next board.

Domain: review.

## WARNING 4 - the ERC gate's evidence is stale

`reports/gate-erc.json` (P4) records
`sch: sexpr_no_uuid:f12934c5dab8276...`. The current schematic hashes to
`sexpr_no_uuid:54a2c346e578e343a...` (I computed it with the pipeline's own
`statelib.hash_artifact`). The J1 pad-net rewire at P5/P6 - which required a P5
re-init because `board_update` refuses pad-net rewires - changed the schematic
after ERC passed, and ERC was never re-run. The green ERC gate on record does
not describe the shipped schematic.

I re-ran it: **0 violations on 54a2c346**. Nothing is hiding here either.
Schematic-to-board net parity *is* covered independently - `drc-routed.json` ran
with `parity: true` against the current files and found 0.

Domain: review.

## WARNING 5 - six clearances sit on the 5 mil fab floor on a board with room to spare

Measured edge-to-edge on F.Cu, pad rotations corrected:

| gap | between |
|---|---|
| 0.1287 mm | R2.2 (/VREF_SET) <-> trk +3V3 |
| 0.1287 mm | U1.5 (GND) <-> trk +3V3 |
| 0.1287 mm | U1.6 (/VREF) <-> trk +3V3 |
| 0.1287 mm | U1.7 (/AMP1_OUT) <-> trk +3V3 |
| 0.1287 mm (x2) | U2.6 (/FB2) <-> trk /AMP1_OUT |
| 0.1341 mm | R3.2 (GND) <-> trk /VREF_SET |

`bb-amp.kicad_dru`'s `aiee_clearance_floor` is 0.1270 mm and
`jlc_capabilities.yaml` `2layer_1oz` `min_clearance_mm` is 0.1270 mm, so KiCad
DRC passes and `dfm_check` passes all eight sub-checks. This is legal - it is
1.7 um of margin on the fab floor, chosen by the router on a 47.98 x 28.251 mm
board carrying 14 parts and 74 track segments. Nothing forced any of them.

Two of the six are on nodes where a short is **silent rather than obvious**:
/FB2 shorted to /AMP1_OUT collapses G2 from 3.49 to 1, so the board still
amplifies - at 39.9 V/V instead of 139.2 - and presents as a calibration problem
rather than a fault. That is worth knowing at bring-up (see below).

Electrical leakage across 0.1287 mm is **not** a concern here and I checked the
worst case explicitly: +3V3 to /VREF_SET, the 9.24 k Thevenin divider node.
Even at a badly contaminated 100 Mohm surface resistance the pedestal shifts
282 uV, i.e. 2.0 uV RTI, and it is a static term that calibrates out.

Domain: router.

---

## Waiver verdict - check_silk / C4 misattribution: UPHELD, with a caveat on the reasoning

Verified independently. The `C4` refdes sits at (42.300, 33.975). U2's silk
outline spans x 40.35..43.82, y 29.96..35.12 and the SOP-8 plastic body spans
x 40.35..44.25, y 30.09..34.99 - so the label is inside U2's outline and under
U2's body. After assembly it is invisible; before assembly it reads as U2's
designator while C4's actual body at (40.30, 36.60) carries no label at all.
U2's own designator is 2.6 mm to the left, outside the outline, so it is not
displaced. KiCad's DRC reports 0 silk findings; `dfm_check`'s silk group passes;
JLC places C4 from the CPL, not the silk. **Cosmetic. The waiver stands.**

One caveat, on the reasoning rather than the verdict. The waiver argues that
adding ~1.5 mm of board height "fights the earned-outline principle on a board
whose binding makes size an OUTPUT of the placement". `reference/build-modes.md`
says the opposite: at `canonical` the board *becomes what the placement needs*,
and legible silk is part of what it needs. That matters practically, because
ERROR 1 forces a silk pass and probably a small grow anyway - C4 should be
re-placed in that same pass rather than carried as a standing waiver.

I checked every other refdes on the board by pad-extent distance and found no
second misattribution. `C1` at (33.635, 25.900) is the nearest miss - it sits
1.6 mm above U1's silk box - but it is 1.875 mm from C1's own body against
4.18 mm to U1's centre, and it is clear of both plastic bodies after assembly.

---

## What I tried to break and could not

These are the load-bearing claims. I measured each from the board rather than
believing the reports, and each one held.

**1. The input pair.** True, exactly as claimed.

- `/IN_N`: one F.Cu segment, (19.300, 27.460) -> (30.090, 28.100), width 0.309,
  0 vias. Length = sqrt(10.79^2 + 0.64^2) = **10.808963 mm**.
- `/IN_P`: one F.Cu segment, (19.300, 32.540) -> (30.090, 31.900), width 0.309,
  0 vias, **10.808963 mm**. Delta **0.000000 mm**.
- Mirroring `/IN_P` about y = 30.0000 reproduces `/IN_N` endpoint for endpoint
  (60 - 32.540 = 27.460; 60 - 31.900 = 28.100). Deviation 0.
- All 74 track segments on the board are on F.Cu. **Zero B.Cu tracks.** The
  nearest via to the corridor is 7.13 mm away.
- Full neighbourhood within 4 mm, recomputed independently: 15 items on each
  leg, pairwise identical, with exactly two departures. `/RG_A`-track to
  `/IN_N` is 0.9719 mm where `/RG_B`-track to `/IN_P` is 0.9852 mm - a 13 um
  difference. And the `/IN_P` leg has J1's GND pole at 3.7255 mm where the
  `/IN_N` leg has a +3V3 track at 3.9618 mm; GND is an *end* pole of a 3-pole
  terminal and cannot be mirrored, so that one is geometry, not workmanship.
  The reports' phrase "mirror-identical item by item" is true of the eight
  nearest items and very nearly true of all fifteen.
- Worth stating because it is a real strength nobody claimed: the two *closest*
  neighbours to each input trace are the RG pads (U1.2 at 0.1405 mm, R1.1 at
  0.6924 mm on the `/IN_N` side; the mirror on the other). An in-amp holds its
  RG pins at essentially the input pins' own potential, so the nearest copper to
  each high-impedance input is at ~0 V relative to it. The neighbours are
  self-guarding as well as symmetric. There is no leakage driving force within
  4 mm of either input.

**2. The ground reference.** True, and I verified it three ways rather than
trusting `plane_repair`.

- The B.Cu zone contains exactly **one** `filled_polygon`, 528 vertices. One
  island, no split.
- Shoelace area of that polygon: **1236.8224 mm2**. `planes_gen.json` recorded
  1236.822 at 04:39:18 on the pre-route board (digest `c466f7d5...`); the final
  board is `2b314ae7...`. Bit-identical - **routing removed nothing**, which
  follows from there being zero B.Cu copper other than the pour.
- I sampled the pour every 0.25 mm along the centreline of each input trace.
  The only void on either leg is the first 1.26 mm out of J1 - J1's own
  through-hole antipad - and it is identical on both legs.
- I sampled 2400 points across the corridor (x 18.0..31.5, y 25.0..35.0) and
  mirrored each about y = 30.0: **zero asymmetric samples**. The reference under
  the pair is continuous and mirror-symmetric.
- See `reports/renders/bb-amp_bcu-pour-verify.png`. It also shows something the
  reports do not: all three GND through-hole pads (J1.3, J2.2, J3.2) carry
  4-spoke thermal reliefs into the 1236 mm2 pour, so the hand-soldered terminals
  are actually solderable. On a board like this that is a real hazard, and it is
  handled.

**3. Topology and pin maps.** No correct-but-wrong connection found.

I read the pin numbers out of `lib/aiee.kicad_sym` rather than assuming them:
AD8226ARZ = 1 `-IN`, 2 `RG/2`, 3 `RG`, 4 `+IN`, 5 `-VS`, 6 `REF`, 7 `VOUT`,
8 `+VS`; OPA2333AIDR = 1 `OUTA`, 2 `INA-`, 3 `INA+`, 4 `V-`, 5 `INB+`,
6 `INB-`, 7 `OUTB`, 8 `V+`. Both are the real parts. The board's 11 nets land
exactly on the intended topology. R5 does return to `/VREF` and not to GND. C4
is on `/VREF_SET`, the divider node, and not on the buffer output. R1 sits
across U1 pins 2-3 with `/RG_A` and `/RG_B` at 2.2597 mm each - equal to seven
digits - and mirror-placed about y = 30. G1 = 1 + 49.4k/1.27k = 39.898,
G2 = 1 + 24.9/10.0 = 3.49, G = 139.24, Vped = 3.3 * 10.0/131.0 = 0.25191 V.
R1's long axis is along y, so both of its terminations sit at the same x - the
correct orientation against a left-to-right thermal gradient, though on a 2.3 mW
board nothing dissipates enough to make it matter.

**4. The recorded accuracy miss - re-derived, arithmetic is right, not
re-reported.** (0.5 + 2/39.9) * 25 = 13.8 uV typ and (2 + 10/39.9) * 25 =
56.3 uV max offset drift; (100 + 25 + 50) ppm/degC * 25 degC * 20 mV = 87 uV max
gain drift at full scale, ~30 uV typ; pedestal ratio-TCR 25-50 ppm/degC *
25 degC * 0.252 V / 139.24 = 1.1-2.3 uV RTI. Every term reproduces. On the rail
sensitivity: bench b6 measures dVout/dVs = 0.0771, i.e. 0.0771/139.235 =
554 uV RTI per volt, so 5 uV RTI is spent by 9.0 mV = 0.27 % of 3.3 V. The
record's 548 uV/V and 0.28 % use the ideal divider ratio 0.0763 and agree to two
digits. The reasoning is sound and the miss is honestly stated.

**5. Geometry, connectors, edges.** Board is one `gr_rect` Edge.Cuts,
(13.000, 23.549) - (60.980, 51.800) = 47.980 x 28.251 mm, earned at P6 under
`canonical`; no stated dimension exists to drift from. I derived each
connector's wire-entry direction from the footprint's own entry notches
(local +y) and its placed rotation: J1 (rot -90) opens toward -x, J2 (rot +90)
toward +x, J3 (rot 0) toward +y. **All three face off their own board edge**,
screws up, with 1.0 mm of board beyond each body. Closest copper to any board
edge is 1.1459 mm. There is no F.Cu pour, so nothing couples into the input pair
from a top fill.

---

## Bring-up - what to check first, in this order

The workspace already records that a missing input bias-current return has no
diagnostic symptom. Given this board's actual failure modes, the ordering that
matters is:

1. **Before power, ring out J3.** There is no legend and no reverse protection.
   J3 pole 1 (`+3V3`) is the pole nearer J1; pole 2 (`GND`) is the far one.
   Confirm continuity from the intended +3V3 wire to U1 pin 8 / U2 pin 8 with the
   supply off. Reversing J3 destroys both ICs and nothing on the board prevents it.
2. **Power through a current limit and read Iq.** Bench b7 says 529 uA at
   3.465 V. Above ~1 mA means a bridge or a reversed part; near zero means no rail.
3. **Measure /VREF before anything else - it is the most diagnostic node on the
   board.** Expect 0.2519 V. R5's pad 2 at (42.95, 36.60) is an accessible 0603
   land on that net. /VREF proves the divider, the buffer and the rail in one
   reading, and it is completely independent of the input. Do not use the output
   to judge health first: with J1 open the output can sit near the pedestal *or*
   walk to a rail, and neither tells you anything.
4. **Split the chain.** Short the two inputs together and tie them to ~1.65 V.
   /AMP1_OUT (probe U2 pin 5) must read 0.252 V, and J2 must read 0.252 V. That
   single test separates stage 1 from stage 2 and would immediately catch the
   /FB2-to-/AMP1_OUT short that WARNING 5 makes possible - G2 would be 1, so J2
   would track /AMP1_OUT instead of standing off it.
5. **Probe U1 pins 1 and 4 directly with the sensor connected.** Both must sit
   near 1.65 V. Either one at a rail means the bias return is missing - J1 pole 3
   not landed, or the sensor's excitation return not actually shared.
6. **Prove the input polarity before trusting any reading.** Apply a small known
   positive Vdiff. The output must move *up* from 0.252 V. If it slams *down* to
   ~0.03 V, poles 1 and 2 are swapped - and with no legend on the board and a
   design doc that states the opposite order, this is the single most likely
   failure a first build will have. It looks exactly like a dead amplifier.
7. **Check the slope, not just that it moves.** 139.24 V/V; 10 mV in should give
   1.645 V out. A working-looking 39.9 V/V is the silent signature of item 4's
   short.
8. **Two things that will look like faults and are not.** (a) Moving the rail
   3.135 -> 3.465 V moves the zero by ~25 mV at the output - that is the designed
   0.0763 V/V pedestal-to-rail ratio, and it is the dominant post-calibration
   error term. (b) The chain is open to 41 kHz: bench b5 reads 0.72 uVrms RTI to
   1 kHz but 4.05 uVrms to 41 kHz. A wideband meter will show ~5.6x the design
   noise. Band-limit the reader to ~1 kHz. Also, do not bench this board against
   Q7's 5 uV RTI - it is recorded as 13.9 uV typ / 56.4 uV worst case and is
   performing to spec when it misses.

## Open

- The AD8226's "REF source impedance below 2 ohm" rule is met only to ~700 Hz.
  Bench b9 measures the U2A buffer at 0.43 mohm DC, 0.17 ohm at 60 Hz, 2.86 ohm
  at 1 kHz and 116 ohm at 41 kHz, so above ~700 Hz the buffer's rising Zout -
  not the AD8226 - sets this board's CMRR (90.8 dB at 1 kHz, ~59 dB at 41 kHz).
  This is already recorded as a FINDING in b9's bounds and in the schematic
  notes, and it is defensible *here* only because requirements Q1 pins the common
  mode statically at 1.65 V with nothing at 1 kHz to reject. I am not
  re-reporting it. I am flagging it as the one property of this board that is
  correct because of an assumption in the requirements rather than because of the
  circuit, and therefore the first thing that breaks if this block is reused with
  a moving common mode. The schematic already says so; it deserves to survive
  into the knowledge record.
- What I could not judge from the board and the renders: whether the wire bundles
  from three terminals on three different edges physically clear each other on a
  real bench. The geometry looks fine (three separate edges, 1.0 mm of board
  beyond each body, wire entries all facing outward) but I did not model bend
  radius or ferrule length.
