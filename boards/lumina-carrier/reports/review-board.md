# P8 board review - LUM-CAR-A (lumina-carrier)

**Reviewer:** verify-reviewer subagent, fresh context. I did not place or route this board.
**Date:** 2026-07-29
**Board:** `kicad/lumina-carrier.kicad_pcb`, 100.0 x 80.0 mm, 4 layer JLC04161H-3313,
In1.Cu = GND, In2.Cu = +3V3. Outline bbox `[19.58, 57.132, 119.58, 137.132]`.
Coordinates below are **board-relative** (subtract the origin `(19.58, 57.132)` from
absolute; the JSON sidecar carries absolute).

**Renders I made for this review:** `reports/renders/lumina-carrier_top.png`,
`reports/renders/lumina-carrier_bottom.png`, `reports/renders/lumina-carrier_iso.png`.
**Measurement scripts:** `work/p8/review/audit1..6.py`, results in the matching `.json`.

**Verdict: 4 errors, 8 warnings, 3 waivers recommended.** None of the 12 is a
re-triage of the 118 known `verify` findings - I did not re-measure those. Two of the
four errors are cross-artifact drift against binding documents; two are layout
defects that every machine check passed by construction.

**What I checked and found clean is listed in section 3.** Read it - three of the
things I was asked to be most suspicious about are genuinely correct, including the
antenna keepout, and the checkpoint should not spend time on them.

---

## 1. Errors

### E1. Mounting-hole pattern contradicts the frozen ICD: 94 x 74 built, 90 x 70 frozen

Measured hole centres, board-relative: **H1 (3, 3), H2 (97, 3), H3 (97, 77),
H4 (3, 77)**, all 3.2 mm. That is a **94.0 x 74.0 mm rectangle at a 3.0 mm inset**.
H5 is at exactly (46, 74) as frozen.

`architecture/connector-icd.md` rev A6 s7.1, headed *"The common LUMINA footprint -
every board inherits this"*, states: **"4x M3 (3.2 mm) at 5 mm inset = a 90 x 70 mm
hole rectangle, plus a 5th M3 at (46, 74)"**. `architecture/requirements.md` Q3 says
the same and adds the reason: *"identical on every LUMINA board so any daughter bolts
to the same standoffs"*.

Root cause is documented and was missed rather than unknown. `brief/05-lumina-closed-decisions.md`
MECH-01 says plainly: *"The radius is clamped to the mounting-hole inset, which is
`margin / 2` - so 3.0 mm at the default `--margin 6`... To get R > 3, pass a larger
`--margin` (e.g. `--margin 10` gives inset 5)"*. P5 ran at the default margin, got a
3 mm inset, and `log/P5-digest.md` records *"MECH-01 and the MECH-02 H1 proposal both
satisfied"* - the corner radius was verified against the report, the **inset was never
compared to the ICD**.

**Consequence.** ICD-01 is binding: *"Daughter runs treat the frozen ICD as a hard
input and never redefine it."* `lumina-par` has completed P0 and `lumina-strobe`
exists. Any daughter that drills per s7.1 misses **all four standoffs by 2 mm in x and
2 mm in y** and cannot be bolted down. It is not fixable on the daughter side.

Secondary, and the reason the ICD's 5 mm was the better number: at a 3 mm inset with
a 3.0 mm corner radius the hole wall is **1.3966 mm from the board edge** (measured),
and the hole centre sits exactly at the corner-arc centre. An M3 washer (7 mm OD) or a
5.5 mm A/F standoff flange overhangs the rounded corner. At a 5 mm inset it would be
3.4 mm.

**Not waivable.** One line fixes it either way - re-run `board_init` with
`--margin 10`, or re-issue the ICD at 94 x 74 - but it must be decided before any
daughter is fabricated, and the choice belongs to the owner because it changes either
this board or two others.

### E2. The 25 MHz oscillator is 115.6 mm of copper with 10 vias, routed to 1.05 mm from the board edge

Y10 (25 MHz) sits at (56.92, 16.97) / (59.12, 15.07). U10 (W5500) XI/XO are at
(77.10, 17.30) / (76.60, 17.30) - **17.5 mm away**. Both oscillator resistors are at
the **top board edge**, roughly 14 mm north of everything they belong to:

| Ref | Value | Role | Position (rel) | To top board edge |
|---|---|---|---|---|
| R36 | 0 R jumper 0603 | series damping, XO -> XO_XTAL | (49.02, 1.05)-(49.02, 2.55) | **1.05 mm** |
| R35 | 1 M 0603 | feedback, XI <-> XO | (68.92, 1.62)-(70.42, 1.62) | **1.62 mm** |

Measured routed copper on the three oscillator nets:

| Net | F.Cu | B.Cu | vias |
|---|---|---|---|
| `/eth/XI` | 37.549 mm | 8.148 mm | 6 |
| `/eth/XO` | 32.641 mm | 10.158 mm | 2 |
| `/eth/XO_XTAL` | 24.971 mm | 2.100 mm | 2 |
| **total** | **95.161 mm** | **20.406 mm** | **10** |

C30 (27 pF) is 2.3 mm from the Y10 pin it loads; **C31 (27 pF) is 7.5 mm** from its.

**Root cause.** `kicad/constraints.json` group `eth_xtal` is `anchor: Y10, members:
[C30, C31]`. **R35 and R36 were never added to the group**, so the anneal was free to
place them, and it put both against the top edge. The separation constraints only push
Y10 *away* from J1 and the switchers; nothing pulled the oscillator network *together*.

**Why nothing caught it.** `/eth/XI`, `/eth/XO` and `/eth/XO_XTAL` are **not** in
`constraints.json` `high_speed`, so `check_return_path` never evaluated the
oscillator's reference continuity. `check_diffpair` only looks at the two declared ETH
pairs. `drc_routed` is clean because none of this violates a rule.
`requirements.md` s10's layout sign-off gates list diff pairs, magnetics isolation,
DC-DC loop area and CAR-REQ-18 thermal - **the crystal is not on that list either.**

**Consequence.** Three separate ones, worst first:
1. A 25 MHz oscillator loop terminating **1.05 mm from a board edge**, on a product
   whose only external cable is a 100 m Ethernet run. This is the canonical
   CISPR 32 / EN 55032 radiated-emissions failure, with harmonics well past 250 MHz.
2. A 0 R **series damping** jumper placed 28 mm from the driver pin, with ~45 mm of
   trace in series with it, cannot damp anything. It is decoration where it sits.
3. ~115 mm of copper plus 10 vias adds several pF of stray to a 27 pF load network:
   frequency offset against 100BASE-TX's +/-50 ppm budget, and reduced oscillator
   negative-resistance margin - a start-up failure that shows up on some units over
   temperature, not on the bench.

**Fix is placement, not routing:** add R35 and R36 to the `eth_xtal` group and
re-place the island next to U10's XI/XO pins. On a routed board that means a local
rip-up; `LEARNINGS` already records that DRC is the only oracle for such a move.

### E3. U21's only input capacitor is 9.2 mm from its VIN pin, and there is no HF ceramic at all

U21 = **TPS563201DDCR**, a synchronous buck making +3V3 from +12V. Pads at
x 42.52-46.32: VIN on pins 3 and 5 (`+12V`), GND on pin 1, SW on pin 2.

The only +12 V capacitor anywhere near it is **C55, 22 uF 25 V X5R 1206, at
(36.83, 55.87) / (40.01, 55.87)**. `check_decoupling`'s own numbers: **9.89 mm
Manhattan, 8.99 mm euclidean, 8.378 nH** to U21 pin 3. There is **no 100 nF or 1 uF
ceramic on U21's VIN at all**. C52/C53 (22 uF) are the 48->12 *output* caps, 32+ mm
away.

**Why the check passed it.** `check_decoupling` classed a 22 uF part as `bulk` and
applied the loose bulk limit. Its model is a *decoupling* loop. What matters on a
synchronous buck is the *commutation* loop: with two FETs and no diode softening, the
input ceramic carries the full trapezoidal switch current, and TI's TPS563201
datasheet layout section requires it **directly across pins 3 and 1**. 9.9 mm with no
ceramic at the pin is the single worst power-stage layout defect on the board.

**Consequence.** Several volts of VIN ringing at every switching edge and a large
radiating current loop sitting 18 mm from J4. The rail this converter produces feeds
the ESP32-S3, the W5500 and **J3 pins 12 and 14 out to every daughter board**.

### E4. 57 V sits 0.2031 mm from a +3V3 branch, and the resolution reverses two binding documents

I measured this pair independently: **`/poe/POE_TAP_A2` to `/poe/LED_Y_A` on F.Cu =
0.2031 mm**, at (25.67, 8.78) / (25.57, 8.60) - track to track, in the north pocket
8.6 mm from the top board edge. That agrees with `work/p8/creepage_adjudication.json`
item 2.

What the adjudication does not state is **what is on the other side of that gap.**
`/poe/LED_Y_A` has exactly two pads: J1 pin 17, and **R7 pin 2. R7 is 330 R 0603 and
its pin 1 is on `+3V3`.** So the failure product of that 0.2031 mm gap is **57 V
injected onto the +3V3 rail through 330 R, unclamped** - and +3V3 leaves the board on
J3 pins 12 and 14. No PESD device sits on any LED net: D31/D32/D40/D41/D42 are all on
expansion signals (ENABLE_M, FAULT_M, ID_ADC, ADC0, ADC1) and D10 (TPD4E1U06) clamps
only the MDI. This is a whole-family kill, not a local one, and it is the worst
consequence on the board.

The adjudication resolves the pair as *"PASSES with +0.0731 mm"* by applying IPC-2221
row **B4** (0.13 mm, permanent polymer coating). Both binding artifacts refuse that
row in as many words:

- `architecture/connector-icd.md` rev A6 s5.1: *"**The 0.13 mm 'permanent polymer
  coating' column (B4) is NOT claimed.** Standard LPI soldermask is not a qualified
  conformal coating, and `check_creepage.py` implements only the uncoated columns - a
  layout designed to 0.13 mm fails P8 with no waiver mechanism."*
- `kicad/lumina-carrier.kicad_dru` header: *"The B4 'permanent polymer coating'
  column (0.13 mm) is **deliberately NOT claimed**"*.

I am not disputing that the B4 reading is defensible - it is widely accepted, and the
adjudication discloses the doubt honestly (mask registration tolerance, coverage
thinning). My objection is narrower and I think it holds: **B4 cannot be adopted in a
`work/` JSON while the frozen ICD that three boards inherit says the opposite.** The
same ICD section derives the 0.635 mm board-wide figure that s5.4 then imposes on
every daughter's 48 V copper, and that derivation exists *because* B4 was refused.
Adopting B4 here without a rev A7 leaves the family with two contradictory rules and
no record of which governs.

**Recommendation independent of which row wins:** give this one pair a physical
mitigation - reroute `LED_Y_A` out of the tap pocket, or clamp +3V3 - because right
now the highest-consequence gap on the board is defended only by soldermask. I accept
the adjudication's other ten items as package-internal and did not re-open them.

---

## 2. Warnings

### W1. Every ICD-mandated silkscreen marking is absent; there is no board-level silk at all

Measured: board-level graphics are **8 primitives, all on `Edge.Cuts`. Zero
`gr_text`, zero `gr_text_box`, zero board-level silkscreen graphics.**

ICD s7.4 lists four independent reverse-insertion mechanisms; mechanism 5 is
*"a pin-1 triangle at position 1 of both blocks on both boards, **plus a `^^ RJ45`
edge arrow on the carrier** and a matching arrow on every daughter."* The arrow does
not exist. The pin-1 markers **do** - J3 and J4 each carry a silk circle 1.747 mm from
pin 1 - so half of that clause is delivered.

Also absent: board name, revision, date, and **any 48 V or "non-isolated" hazard
marking anywhere on a board that carries 57 V to a user-serviceable connector inside a
sealed enclosure**.

`check_silk` passed with 0 findings because it hunts silk-over-pad and clipping, not
missing required markings. That is a hole, not a pass. Severity is warning only
because it is a silk-layer edit with zero electrical risk - but it is an undelivered
ICD clause, so it should not close silently.

### W2. 9.8 mm2 of copper sits in the declared antenna keepout, in an 18.7 mm2 band no DRC rule covers

**The load-bearing requirement passes, and I verified it from the datasheet rather
than from the render.** `reports/fp_verify_U30_C2913198.json` records the vendor land
pattern: *"pin 1 and pin 40 are the two pads closest to the antenna end"*, *"7.49
(module top edge to the start of the pads)"*, *"ANTENNA AREA: the top 18 x 6 mm of the
land pattern is drawn as 'Antenna Area' and carries no copper"*. U30 is at (83.05,
40.0) rotated -90, pin 1 at (92.0, 31.1) and pin 40 at (92.0, 48.9), so the antenna
end faces **+x, toward the right board edge**, and the Antenna Area is
**x 93.94-99.94, y 30.35-49.65**.

Copper inside that area: **0.0000 mm2 on F.Cu, In1.Cu, In2.Cu and B.Cu.** Nearest
copper is **1.35 mm** (the In1 GND pour edge and the In2 +3V3 pour edge) and
**1.47 mm** (two GND stitching vias). The P5 plane-patch step was done and H1-Q8's
*"no copper, no pour, no plane under the antenna on any layer"* is met. The module
falls 0.06 mm short of overhanging the right edge, which is unavoidable at a fixed
100 x 80 outline and is already recorded in `constraints.json`.

The residual is a DRC blind spot rather than a present defect. `constraints.json`
declares a 10 x 22 mm keepout (x 90-100, y 29-51 = **220.0 mm2**) but only
**201.276 mm2** is authored as rule areas - `antenna_core_keepout` (x 93.02-100,
y 29-51) and `antenna_margin_keepout` (x 90-93.02, **y 32.068-47.868**). The uncovered
**18.724 mm2** is two slivers at x 90-93.02, y 29-32.068 and y 47.868-51, and
**100 % of the in-keepout copper is in them** (0.0000 mm2 lies inside any rule area):

| Layer | copper in declared keepout | inside a rule area | in the uncovered sliver |
|---|---|---|---|
| F.Cu | 6.6623 mm2 | 0.0000 | 6.6623 |
| In1.Cu | 0.5651 mm2 | 0.0000 | 0.5651 |
| In2.Cu | 0.5651 mm2 | 0.0000 | 0.5651 |
| B.Cu | 2.0204 mm2 | 0.0000 | 2.0204 |

Occupants: `+3V3` 1.3636 mm2 (F.Cu), `GND` 1.5722 (B.Cu) + 0.7002 (F.Cu), `/ADC0`
0.5051, `/FAULT` 0.1663 (B.Cu), `/ADC1` 0.0504, U30's own pads 1/2/39/40, and **two
0.6/0.3 mm GND vias at (92.17, 31.268) and (92.17, 49.068) spanning all four copper
layers** - i.e. plane-layer copper inside the declared keepout, 1.47 mm from the
antenna area.

The rule areas were carved around the copper rather than the copper moved out of the
keepout, so DRC now green-lights any future reroute that walks copper further toward
the antenna. **Either shrink the declared keepout to what is actually enforced and
record why, or extend the rule areas and move those two vias.** Do not leave the
declared and enforced regions different sizes.

### W3. Four unfiltered, unclamped 55-73 mm traces run from the RJ45's LED pins into the PHY

| Net | routed length | endpoints | protection at the jack |
|---|---|---|---|
| `/poe/LED_G_A` | 72.628 mm F.Cu | J1.15 -> R8 (96.45, 9.46) | none |
| `/poe/LED_Y_A` | 65.037 F + 1.844 B | J1.17 -> R7 (70.67, 28.87) | none |
| `/ETH_LED_LINK` | 8.497 F + **55.554 B.Cu** | J1.16 -> **U10 pin 25 direct** | none |
| `/ETH_LED_ACT` | 3.844 F + **67.960 B.Cu** | J1.18 -> **U10 pin 27 direct** | none |

Two pads per net: **no series resistor, no shunt capacitor, no ESD clamp**. The 330 R
parts (R7, R8) are on the anode side only and sit 44-70 mm from the jack; R8 is at the
opposite corner of the board from J1.

The RJ45's LED pins sit inside the connector shell millimetres from the MDI contacts
and are a well-known cable-borne ESD and surge ingress path. Here they give a
transient a direct 55-68 mm run into two W5500 pins with nothing in the way, while
D10's TPD4E1U06 protects only the four MDI lines. The same 65-73 mm runs are efficient
radiators that terminate at the connector face - exactly where emissions couple onto
the cable.

**Cheap now, a respin later:** 100-220 pF to GND at the jack end on all four, keeping
the existing series R. Or accept and record.

### W4. 100 V buck input ceramics are 7.4-8.6 mm from VIN; the HF cap is 4.6 mm

U20 = **SCT2A25STER**. VIN = pad 3 (`V48_RAW`), SW = pad 5, GND = pads 6/8/9.
`check_decoupling`'s own measurements to pin 3:

| Cap | Value | Manhattan | loop |
|---|---|---|---|
| C61 | 100 nF 100 V 0805 | **5.16 mm** (4.57 euclid, 0.65 mm GND leg, 1 via) | 5.067 nH |
| C51 | 2.2 uF 100 V 1210 | **7.37 mm** | 6.159 nH |
| C50 | 2.2 uF 100 V 1210 | **8.64 mm** | 7.048 nH |

**No ceramic straddles VIN-to-GND at the pin**, so the input loop is ~5-8 nH and the
48 V switch node will ring at every edge. `/pwr/SW` carries **33.56 mm2 of copper**
over a 7.8 x 14.8 mm bbox with 2 layer transitions - more dV/dt surface than a
100 V / 2 A converter needs. `check_decoupling` passed all three because 5.067 nH is
inside its 10 nH mid-class limit; that limit is a decoupling limit, not a commutation
limit.

Two things here are **right** and worth crediting, which is why this is a warning and
not an error: In1 GND is solid directly under the whole converter (**107.07 mm2 of GND
inside the 115 mm2 switch-node bbox**), so the HF return image hugs the forward path;
and the In2 +3V3 plane is deliberately kept out of the buck region (**0.00 mm2 of
+3V3 under the switch-node bbox**). That stackup decision is doing real work.

### W5. U22's thermal land carries 15 unplugged 0.3 mm vias-in-pad - the same construct P5 removed from U30

In the U22 footprint, pad 21 is an F.Cu 3.4 x 6.5 mm heatsink land plus a B.Cu
3.2 x 5.8 mm land plus **15 x `thru_hole circle` size 0.6 drill 0.3, `layers "*.Cu"`,
`pad_prop_heatsink`, net GND** - inside the paste aperture.

`log/P5-digest.md` records removing exactly this construct from the ESP32-S3
footprint, with the reasoning: *"thermal vias under a ground land belong to the board,
not the footprint - P7 stitching places them against the real GND pour... and that
also removes the via-in-pad solder-wicking risk already on the P9 list."* The
reasoning was never applied to U22.

At JLCPCB PCBA, paste wicks down 15 barrels during reflow: voids under the eFuse's
thermal pad (degrading the theta-JA the design relies on) and solder protrusions on
B.Cu. JLC does not plug or tent via-in-pad unless resin plugging is ordered *and*
stated in the fab notes - and `fab/` is empty, P9 has not run, so nothing declares it.

Compounding: `constraints.json` `thermal` declares **only U20**. `check_thermal`
passed having evaluated **1 of 3 dissipating parts** - U22 (48 V eFuse, 1.0 A ILIM)
and U21 were never modelled, so the voiding has no modelled consequence either.

### W6. J1's two board locks are netless conductors 0.66 mm from 57 V, and nothing can check them

Two netless plated pads at **(15.29, 11.041)** and **(26.72, 11.041)**, 3.2 mm,
spanning all four copper layers. J1 pins 7, 8, 9 and 10 are also netless 4-layer PTH.
Nearest 48 V copper:

| Netless hole | Nearest 48 V net | Gap |
|---|---|---|
| (26.72, 11.041) board lock | `/poe/POE_TAP_A2` | **0.6617 mm** |
| (15.29, 11.041) board lock | `/poe/POE_TAP_B1` | **0.6621 mm** |
| (16.56, 19.931) pin 9 | `/poe/POE_TAP_B1` | 0.6646 mm |
| (15.29, 17.391) pin 10 | `/poe/POE_TAP_B2` | 0.6700 mm |

In the physical LPJG0926HENL the board locks are part of the stamped shield -
continuous with the shell and with a shielded patch cable's connector body. On the
board they carry **no net and no declared voltage**, so `check_creepage` cannot
evaluate them (it derives dv from `constraints.json` `voltages`) and the `.kicad_dru`
rules cannot see them (they key on `A.NetName`).

**After measuring, the verdict does not change:** 0.6617 mm clears the 0.635 mm
binding requirement, so this is a blind spot rather than a shortfall. Net the board
locks and pins 7-10 to `/poe/SHIELD` or to a declared 0 V NC net so the number is
defended by a check instead of by luck.

**The related item that is a genuine structural hole.** `log/P7-digest.md` already
records shield tab pad 19 -> tap pad 11 = 0.6029 mm and pad 20 -> pad 14 = 0.6127 mm,
*"0.032 mm short of the 0.635 mm adopted board-wide"*. I re-measured **0.6037 mm at
(27.89, 14.60)** and **0.6134 mm at (14.11, 14.60)** and agree. What P7 did not do is
**add a rule**: it added `poe_tap_differential_pair` for A1-A2 / B1-B2 in that same
phase but left tap-to-SHIELD unruled. So:

> Of the **seven** nets `constraints.json` `voltages` declares at 57 V, the
> `.kicad_dru` enforces 0.635 mm on **three** (`+48V_SW`, `V48_RAW`, `V48_RTN`). The
> four `/poe/POE_TAP_*` nets are enforced at 0.60 mm by `check_creepage` at best, and
> by nothing in DRC except against each other (0.60 mm) and against the MDI (1.30 mm).

That is why the 0.6037 mm gap and the 0.2031 mm gap of E4 both exist on a board with
0 DRC errors, and why either can silently erode on the next reroute. SHIELD is
correctly bonded (R6 1 M + C3 1 nF 2 kV - a proper Bob-Smith bond, not a hard tie), so
it floats at ~GND and the full 57 V sits across that 0.60 mm.

### W7. 57 V copper 1.12 mm from the bare left board edge

`V48_RAW`'s closest approach to the outline is **1.12 mm on F.Cu at (1.12, 28.068)**
(In1/In2 5.72 mm, B.Cu 5.62 mm) - the 100 V bulk-cap column (C2/C4/C5/C6, 10 uF 100 V
1210) against the left edge. `+48V_SW` is 1.8805 mm from the bottom edge at
(14.53, 78.12), which is J3 pin 1's own pad and is frozen by ICD s7.2.

Fab-legal (JLC wants >= 0.3-0.5 mm) and IPC-legal (the edge is not a conductor), and
H1-Q5 gives a sealed plastic enclosure. The exposure is **assembly and service
handling on a live board**, plus edge-router copper smear. Waiver is reasonable if the
48 V silk marking of W1 is added.

**Good news I verified while looking:** all five M3 holes are clear of 48 V. Nearest
48 V copper is H4 **8.936 mm**, H1 **10.572 mm**, H5 **23.299 mm**, H2 **55.349 mm**,
H3 **68.478 mm**. Metal standoffs are not a 48 V hazard on this board.

### W8. Recovery is unreachable with a daughter fitted - both recovery controls sit under it

J2 (1x6 2.54 mm recovery header: GND, +3V3, TXD0, RXD0, EN, BOOT) is at x
73.657-87.881, y 0.739-2.263 - a **vertical** THT header whose pins stand ~8.5 mm
above a board with an 11.0 mm mated stack. A 6-way jumper lead cannot be seated in the
remaining ~2.5 mm. SW1 (SMD tactile) at (61.24-63.1, 0.573-6.163) is also outside the
30 x 26 mm RJ45 notch (x 6-36) and therefore under the daughter.

ICD s7.6 already offers the escape hatch - *"or accept that the daughter must be
removed to recover firmware"* - so this is a recorded consequence, not an oversight.
But `requirements.md` Q9 default (b) chose *"Ethernet OTA normally, plus a 6-pin
header inside the enclosure for recovery"*, and in a **sealed** enclosure recovery now
means opening the box and unbolting five standoffs. That deserves the owner's explicit
acceptance rather than an inherited default.

Minor drift in the same area: J2 spans x 73.657-87.881 while the ICD's recovery-header
exclusion zone is (76, 0)-(98, 20) - the header starts **2.343 mm left** of the region
daughters are told to keep clear. The zone is advisory, but the number should match.

---

## 3. Checked and clean - do not spend checkpoint time here

I was asked to be most suspicious of the antenna keepout, the connector/enclosure
reality and the ICD delivery. Three of those are genuinely correct:

- **The ESP32-S3 antenna area is copper-free on all four layers.** 0.0000 mm2 inside
  the datasheet-derived 18 x 6 mm Antenna Area at x 93.94-99.94, y 30.35-49.65;
  nearest copper 1.35 mm. H1-Q8 is satisfied. See W2 for the margin-band caveat.
- **J3 delivers the ICD s3.1 map pin-for-pin.** 14 pins; **7 GND** (CAR-REQ-13 and
  closed-decisions *"GND is the binding rail"*); 3 x `+48V_SW`, 2 x `+12V`, 2 x
  `+3V3`; **column 4 (pins 7 and 8) is all-GND** - the guard column exists; every
  supply pin has an adjacent GND; rail order along the connector is 48 -> GND -> 12
  -> 3.3.
- **J4 delivers the ICD s3.2 map pin-for-pin.** 24 pins; 8 PWM; GND at positions
  3/4/9/10/13; SPI, I2C, ADC0/ADC1/ID_ADC; ENABLE and FAULT at the far end from the
  PWM group. **No 48 V anywhere on J4.**
- **ICD s7.2 frozen datums hit exactly.** J3 position 1 at (15.380, 77.270), J4
  position 1 at (57.030, 77.270), both even rows at y = 74.730, H5 at (46, 74).
- **J1 fits the daughter's 30 x 26 mm notch.** Courtyard (12.79, 0.001)-(29.21,
  21.741) inside (6, 0)-(36, 26), with 6.79 mm left, 6.79 mm right, 4.26 mm bottom
  margin. The keying interlock of ICD s7.4.1 works, and J1 is the only part that
  breaks the 11.0 mm stack.
- **Corner radius 3.0 mm on all four corners**, measured from the Edge.Cuts arcs.
- **SHIELD bonding is correct**: R6 1 M + C3 1 nF 2 kV X7R.
- **The In2 +3V3 plane is deliberately excluded from the 48 V / buck region** while
  In1 GND is solid there. Good, load-bearing decision.
- **ESD clamps are on the daughter-facing signals**: D31 ENABLE_M, D32 FAULT_M, D40
  ID_ADC, D41 ADC0, D42 ADC1, plus D10 TPD4E1U06 on the MDI.
- **Connector orientation and accessibility are sane.** RJ45 on the top edge facing
  out, both expansion connectors on the bottom edge with their pin fields inside the
  land extents the ICD froze, H5 between them for CAR-REQ-15. Nothing tall shadows
  either connector. See `reports/renders/lumina-carrier_top.png`.

---

## 4. Coverage holes - skipped is not passed

1. `constraints.json` `thermal` declares only **U20**. `check_thermal`'s PASS covers
   **1 of 3** dissipating parts; U22 (48 V eFuse at 1.0 A ILIM) and U21 were never
   modelled. See W5.
2. `constraints.json` `high_speed` declares the 4 MDI nets and `/ETH_SCLK` only. The
   **25 MHz oscillator nets are absent**, so `check_return_path` never evaluated them.
   See E2.
3. `.kicad_dru` enforces the 0.635 mm board-wide figure on **3 of the 7** nets
   declared at 57 V. See W6.
4. **P9 has not run - `fab/` is empty.** No gerbers, no drill, no fab notes, no
   BOM/CPL, no via-plugging declaration, no panelization or fiducial decision. There
   are **no fiducials** on the board (JLC does not require them, but the decision has
   not been made). Every fabrication-facing claim in this run is still unverified.
5. `check_diffpair`'s J1 blind spot - true magjack-pad-to-PHY-pad RX skew 6.451 mm /
   43.0 ps hidden behind a 0.98 mm PASS - is a known open owner item, unchanged by
   anything I found.
6. `report_gen.py` looks for `requirements.md` and `brief/brief.md` at the workspace
   root, but the real artifacts are `architecture/requirements.md` and
   `brief/00|01|05-*.md`. The design document therefore renders those sections as
   stubs, so DOC-01's deliverable under-represents the requirements it is meant to
   trace against. (Raised to me by the orchestrator; I confirmed the paths.)

---

## 5. Waivers recommended

Three, each with the reason:

1. **W7 - 57 V at 1.12 mm from the left board edge.** Waive. Fab-legal and IPC-legal;
   the enclosure is sealed non-conductive per H1-Q5; the residual exposure is
   handling a live board during assembly or service. **Condition:** add the 48 V /
   non-isolated silk marking that W1 says is missing, so the person holding the board
   is told.
2. **W6 - the 0.6037 / 0.6134 mm tap-to-SHIELD gaps.** Waive the *numbers* - they are
   J1 lead-frame geometry, already measured and recorded at P7, 0.032 mm short of a
   vendor-derived figure that exceeds IPC's 0.60 mm, and the part carries its own
   2250 VDC hipot barrier. **Do not waive the missing rule:** add a
   `poe_tap_to_shield` DRU rule at 0.60 mm so the gap cannot erode unnoticed, exactly
   as `poe_tap_differential_pair` was added for the same reason.
3. **W8 - recovery under the daughter.** Waive as a recorded design consequence, since
   ICD s7.6 already names the "remove the daughter" branch. **Condition:** the owner
   states the acceptance explicitly, because Q9's default assumed an in-enclosure
   header would be usable and in a sealed box it is not.

**Not waivable:** E1 (a frozen inter-board dimension is wrong in one of two places),
E2, E3 (both are real field-failure mechanisms that no check models), E4 (the
adjudication needs an ICD rev or a mitigation, not a `work/` JSON), W1, W2, W3, W4,
W5.
