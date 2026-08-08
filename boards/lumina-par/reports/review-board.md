# LUM-PAR-A board review (P8, adversarial)

Reviewer: fresh-context P8 board reviewer. No part of this board was placed or
routed by me. Every number below is measured from
`kicad/lumina-par.kicad_pcb` or from an artifact named inline; renders are the
ones I generated at `reports/renders/lumina-par_{top,bottom,iso}.png`.

Board-local coordinates are ICD frame (origin = board top-left, x right, y
down). PCB-absolute = board-local + (54.9375, 57.1925). Both are given where
it matters; the JSON carries PCB-absolute so `fix_dispatch` can find things.

**Gate state I am reviewing against, not from:** erc 0/0, place 0/0,
drc_routed 0/0, verify PASS (0 failing, 3 waived, 57 warnings). Nothing below
is contradicted by a gate - that is the point. Where a gate is structurally
incapable of seeing a defect, I say which gate and why.

**5 errors, 15 warnings, 4 waiver recommendations.**

---

## Errors

### E1. H1's mounting hole is cut open by the RJ45 notch - the corner has no standoff

H1 sits at board-local (5.000, 5.000) with a 3.2 mm drill. The RJ45 relief's
left wall is an `Edge.Cuts` line at x = 6.000 (absolute 60.9375) running the
full 26 mm of the notch. Hole centre to that edge is **1.000 mm** against a
1.600 mm hole radius, so:

- **1.04 mm2 of the 8.04 mm2 hole lies outside the board** (13 %). The hole is
  not a hole: it opens into the notch as a **2.50 mm wide slot**.
- An M3 screw at H1 has no material on the notch side. An 11 mm F-F standoff
  body (~5 mm across) overhangs by 4.95 mm2, an M3 pan head (5.5 mm) by
  6.50 mm2, a plain washer (6.0 mm) by 8.25 mm2.
- What is left of the 6 mm finger between the board edge and the notch is
  **1.4 mm of FR4 at the narrowest**, with a routed slot through it - a crack
  initiator at exactly the corner a technician grips while unmating.

Visible in `lumina-par_iso.png` (near-left corner, marked H1: compare its
scalloped opening against the closed circle at H4) and in
`lumina-par_top.png` at the top-left of the notch.

**Root cause is in ICD-01, not in this board.** s7.1 puts the four corner
holes at a 5 mm inset; s7.6 starts the RJ45 relief at x = 6 and says "the
outline rectangle, corner radius and 5-hole pattern are **unchanged**". A
3.2 mm hole centred at x = 5 needs material out to x = 6.6. The two clauses
cannot both hold, and **every LUMINA daughter inherits the collision** - the
carrier does not, because it has no notch. Per ICD s10 this is a blocking
issue against LUM-CAR-A, not a local variant.

**Why no gate sees it.** KiCad's `edge_clearance` constraint applies to copper
items; H1 is `MountingHole_3.2mm_M3`, an NPTH pad with no copper layer, so
DRC has nothing to test. `check_*` has no mechanical-outline check at all.

Two candidate fixes, both needing the carrier owner: move H1 to (3.0, 5.0)
(1.4 mm to the edge, 1.4 mm to the notch - still poor), or start the notch at
x = 8 and shorten it to 28 mm. Neither is this board's call.

### E2. The ICD s9 bench-hazard silkscreen is claimed in the design doc and does not exist on the board

`reports/design_doc/lumina-par-design-doc.tex` states, twice, that the marking
is fitted: *"TP103 carries the ICD s9 bench-hazard silkscreen"* (test-point
table) and *"TP501, TP502 ... ICD s9 bench-hazard silkscreen"*.
`requirements.md` s2.5 makes it mandatory: *"Any test point fitted must carry
the ICD s9 bench-hazard warning."*

The board carries **no silkscreen text of any kind other than component
reference designators**. There are zero `gr_text` items on the board, and every
`fp_text` that is not a refdes is on `F.Fab` / `B.Fab`, which is not
fabricated. Confirmed visually: no legend anywhere in `lumina-par_top.png` or
`lumina-par_bottom.png`.

TP103 is a bare 1.5 mm pad on `+48V_SW` at board-local (22.06, 71.31) - 
57 V worst case, on a fixture that floats at PoE potential with no chassis
earth. ICD s9's published consequence of clipping an earthed probe or a
non-isolated USB-UART there is not merely shock and damage: it **breaks PD
signature detection outright**, because detection currents are a few hundred
microamps. TP501/TP502 are bare thermocouple pads on GND - the same floating
return.

A safety marking that the design record asserts and the fabricated board will
not have is worse than one that was never promised: the next person reads the
design doc, believes the board is marked, and does not add it.

### E3. U341 has 6 thermal vias where its three identical siblings have 8, and the gate cannot see the difference

Measured inside each declared thermal pad's polygon (+0.05 mm halo):

| ref | declared `min_vias` | vias found |
|---|---|---|
| U301 | 9 | 8 |
| U321 | 9 | 8 |
| **U341** | 9 | **6** |
| U361 | 9 | 8 |
| D301 / D321 / D341 / D361 | 4 each | **0 each** |

The 8-not-9 result on three drivers is the documented geometric maximum at the
0.5 mm hole-to-hole floor and is fine. **U341 at 6 is not** - it is a 25 %
conduction deficit against three parts that are the same footprint, the same
power (0.15 W declared) and the same channel topology, with no recorded
reason. On a fixture whose whole purpose is colour consistency (PAR-REQ-06,
carried at reduced confidence since AMD-01), a thermally asymmetric channel is
a chromatically asymmetric channel.

**Why no gate sees it.** `check_thermal` only emits its `thermal_vias`
violation when `need_vias` is true - that is, when the copper-area model alone
cannot reach `dt_c`. At 0.15 W and 0.14 W it can, so `need_vias` is False and
**all eight declared `min_vias` floors are never evaluated**. The board
declares eight thermal-via requirements and the P8 suite tests none of them.
`check_thermal` reports `pass` with 0 violations, truthfully, about something
else.

The four catch diodes at zero vias are carried separately as W4 - their
declared floor of 4 may not even be geometrically achievable in a 1.05 x 1.5 mm
land, which is itself a constraints defect rather than a layout one.

### E4. The J3/J4 pin-1 marker is unprintable, is the wrong shape, and points at the wrong row

Three separate defects in one 0.12 mm feature.

**(a) It will not print.** The marker on both connectors is an `fp_circle` with
`center` and `end` 0.03 mm apart - radius 0.03 mm - stroked at **0.06 mm**
with `fill no`. Outside diameter 0.12 mm. JLC's silkscreen minimum line width
is ~0.153 mm. This is roughly a third of the minimum feature and will be
dropped or smeared by the screen. J3's marker is at board-local
(13.81, 73.27), J4's at (55.66, 73.33), both on `B.SilkS`.

This is systemic, not local: **89 silk graphics on this board are stroked at
0.06 mm and 43 at 0.12 mm**, all below the fab floor. The DRU does carry
`aiee_silk_width_floor` at 0.150 mm, but its condition is
`A.Type == 'text' && ...`, so it constrains only text objects. No rule anywhere
tests graphic silk width, which is why drc_routed is 0/0.

**(b) It is a circle, not a triangle.** ICD s3 ("Position 1 is silkscreen-marked
with a triangle on **both** boards") and s7.4 mechanism 5 ("A pin-1 triangle at
position 1 of both blocks on **both** boards") both specify a triangle.

**(c) It marks the wrong row.** After the reverse-mount flip, footprint pad 1
is at board-local (15.379, 74.730) on J3 and (57.029, 74.730) on J4. The
carrier's position 1 - per ICD s7.2 rev A7, the re-issued as-built table - is
at (15.380, 77.270) and (57.030, 77.270): **the other row**. So the daughter's
pin-1 mark sits 2.54 mm from the carrier's and identifies the contact that
mates with the carrier's position **2**.

ICD s7.4 lists five anti-mis-mate mechanisms and silkscreen is the fifth. Here
it does not merely fail to help - a technician who checks that the two pin-1
marks line up will read a one-row offset and conclude the pair is mis-seated
when it is correct. Both connector bodies also sit over their own silk (the
sockets are 8.5 mm and cover the outline), so the corner mark is the only part
of it visible after assembly, and it is the part that is wrong.

### E5. The board's J3/J4 pad numbering is the mirror of the ICD map that requirements.md prints as authoritative

**The mating geometry is correct - I verified all 38 positions and found no
electrical error.** Every net on the daughter lands on the carrier pin
carrying the same net under ICD s7.2 rev A7:

- J3: `+48V_SW` on daughter pads 2/4/6 at board-local y = 77.269, which is
  where the carrier's positions 1/3/5 are; GND opposite at y = 74.730 against
  the carrier's 2/4/6; `+12V` on 10/12, `+3V3` on 11/13, GND on 7/8/9/14 - 
  all matching the carrier pin at the same (x, y).
- J4: PWM0 on daughter pad 2 (carrier position 1), PWM1 on pad 1, PWM2 on 6,
  PWM3 on 5, `I2C_SCL` on 17 (carrier 18), `I2C_SDA` on 20 (carrier 19),
  `ADC0` on 19 (carrier 20), `ADC1` on 22 (carrier 21), `ID_ADC` on 21
  (carrier 22), `ENABLE` on 24 (carrier 23), `FAULT` on 23 (carrier 24), and
  every carrier PWM4-7 / DSPI position landing on an unconnected daughter pad.

**The problem is that the daughter's pad numbering is now offset by one row
from ICD position numbering** - board pad *n* carries ICD position *n*+1 for
odd *n* and *n*-1 for even *n*, on both connectors - and nothing in the
project's documents says so:

- `requirements.md` s2.1 still prints *"Pin map (ICD s3.1), authoritative, do
  not re-derive: 1/3/5 `+48V_SW`; 2/4/6/7/8/10/13 `GND`; 9/11 `+12V`; 12/14
  `+3V3`"*. On this board J3.1 is GND and J3.2 is `+48V_SW`.
- s2.2 likewise prints *"`PWM0..7` at positions 1,2,5,6,7,8,11,12"*. On this
  board J4.1 is PWM1.

Anyone who brings this board up with a meter against `requirements.md` reads a
57 V rail on the wrong pin. This is the same class of defect as the row-swap
that was caught this session, one artifact downstream - and it is the artifact
a bench technician actually opens. It needs a daughter-side pad table stating
that daughter pad *n* mates carrier position *n*-/+1, published in
`requirements.md` s2.1/s2.2 and the design doc, before this board is handled
powered.

---

## Warnings

### W1. In1.Cu is not the solid GND plane the whole return-path argument rests on

`architecture/constraints.json` justifies leaving GND out of `power[]` on the
grounds that *"the requirement is structural instead (solid In1, per-channel
harness returns, 7 connector GND pins ...)"*. Measured, In1.Cu carries
**226 mm of foreign track and 106 foreign vias**:

| net on In1.Cu | length | board-local extent |
|---|---|---|
| `+3V3` | 87.2 mm | (40.7, 25.4) -> (91.6, 68.9) |
| `/NTC_LED` | 58.9 mm | (45.7, 13.2) -> (90.3, 73.4) |
| `/LED0_A` | 38.8 mm @ 0.4 mm | (52.5, 17.2) -> (62.0, 51.3) |
| `/EN_OK` | 14.2 mm | (34.4, 30.6) -> (46.3, 33.7) |
| `/thermal/CMP_LED` | 14.1 mm | (85.7, 58.6) -> (93.3, 69.5) |
| `/ADC0` | 12.6 mm | (51.5, 55.0) -> (79.9, 74.7) |

In2.Cu (+12V) carries a further 166 mm and 195 foreign vias, including
`/SHUNT0` 9.1 mm and `/LED0_A` 7.9 mm.

The `/LED0_A` run is a 38.8 mm slot straight down the middle of the driver
band - the P8 fix that took `check_current` from 36 to 0 bought its IPC width
by cutting the reference plane. `+3V3` and `/NTC_LED` between them thread the
plane over most of the board's width and height.

**The plane is not fragmented, and I want that on the record separately:** the
In1 GND fill is 5833 mm2 in 5 pieces - one of 5826 mm2 plus four slivers of
0.75-2.70 mm2 between J3's pads at board-local x 17-24, each touching 1-3 THT
pads and therefore connected through the barrels. Nothing is orphaned. The
defect is slot topology, not islands.

The only check that would see this is `check_return_path`, and it is scoped to
the four nets declared in `constraints.high_speed`. Six nets cut the plane;
none of the six is checked as a victim.

### W2. The right-hand 12 mm strip has no reference plane at all - and the independent over-temperature comparator lives in it

Both pours stop at board-local **x = 88 over the full 80 mm height**
(zone outlines (54.937, 57.192)-(142.937, 137.192) on In1 and In2). ICD s7.6
only reserves y 25-55 in that column. The removal outside 25-55 is a choice,
not a constraint.

U401 (LM339LV, TSSOP-14) spans board-local x 89.1-93.0, y 61.5-67.1 - **6.5 mm
clear of the reserved column and entirely off both planes** - with R403-R416,
C401-C403 and D401 around it. Measured in the (84, 54)-(100, 78) box: 50.0 mm2
of In1 GND (all of it at x < 88), 6.1 mm2 of F.Cu GND, 0.9 mm2 of B.Cu GND and
**4 GND vias**. Over the whole x > 88 strip (956 mm2 of board) there is
2.39 mm2 of F.Cu GND and 0.83 mm2 of In1 GND.

This block is the board's hardware backstop: `/FAULT` is driven by U401.1/2/13/14
wire-OR'd to the carrier. `architecture/p4-wiring-notes.md` s3 records that the
LM339LV has **no internal hysteresis**, so all of it is external (R405-R412).
A comparator bank with external-only hysteresis, no ground reference and four
switching converters 25 mm away is how a few millivolts of offset becomes
chatter on the fixture's fault line. `check_return_path` never looks here.

The plane can legally be restored at x 88-100 for y < 23 and y > 57, which
covers the whole analog block while leaving the ICD column void intact.

### W3. PWM0-3 return through the +12V plane, not GND - 11 of the 13 return-path warnings say so and the class matters more than the geometry

Stackup from the board: F.Cu | 0.2444 | In1(GND) | 1.0650 | In2(+12V) | 0.2444 |
B.Cu. **Every B.Cu trace on this board references In2 = +12V**, 0.244 mm away,
not GND at 1.31 mm.

| net | total | on B.Cu |
|---|---|---|
| `/control/PWM0` | 38.6 mm | 29.6 mm |
| `/control/PWM1` | 50.3 mm | 28.8 mm |
| `/control/PWM2` | 52.6 mm | 38.3 mm |
| `/control/PWM3` | 45.0 mm | 36.2 mm |
| `/SHUNT0` | 72.0 mm | 48.3 mm |
| `/SHUNT2` | 42.8 mm | 23.3 mm |
| `/SHUNT1` | 55.4 mm | 19.4 mm |

`constraints.high_speed` declares `"reference": "GND"` with `t_rise_ns: 2.0`
for all four PWMs. Eleven of the thirteen `check_return_path` warnings carry
`waiver_class: "cross_net_reference"`, `reference_declared: "GND"`,
`reference_net: "+12V"` - the checker is telling you it measured a different
plane from the one declared, and then measuring corridor voids in it.

Individually the deficits are 0.13-1.75 mm2 and are not worth a fix. **The
class is:** roughly 133 mm of 2 ns-edge PWM and 91 mm of shunt-gate drive
inject their return current into the rail that feeds all four LED channels.
`+12V` is well bypassed to GND (2 x 22 uF 1210 plus 4 x 4.7 uF at the drivers)
so it is a serviceable AC ground - but that is an argument that should be
written down and waived, not left as eleven silent warnings whose text says
the reference is wrong.

Recommendation: either declare `+12V` as the reference for the B.Cu segments
and re-run, or move PWM0-3 to F.Cu where In1 GND is 0.244 mm away. Do not
leave the declaration and the copper disagreeing.

### W4. Four declared thermal sites have zero of their required vias - and the requirement may be impossible as written

D301/D321/D341/D361 each declare `min_vias: 4` in `constraints.json`; each has
**0**. Their GND land is 1.05 x 1.5 mm. Four 0.45 mm vias at the 0.5 mm
hole-to-hole floor do not fit in 1.6 mm2; two might. So this is a constraints
defect as much as a layout one - but it is a declared requirement that is
unmet and unmeasured (see E3 for why `check_thermal` is silent). The declared
0.14 W is the shunted-idle case, which is the *worst* case at unchanged channel
current, so it is a steady-state number on a continuous-duty board.

### W5. 42 refdes name the wrong part - that is a mis-build mechanism on this board, not cosmetics

All 42 `check_silk` warnings are `silk_misattributed`: **27 % of the 155
reference designators sit closer to a neighbouring part than to their own.**
The worst are effectively touching:

- R410 - **0.00 mm** from U401
- C363 - 0.06 mm from L361
- C204 - 0.09 mm from J4
- R342 - 0.12 mm from U201
- R416 - 0.15 mm from R414
- R411 0.23 mm from R412, R412 0.19 mm from H3, R344 0.23 mm from R205, H3 0.29 mm from R411, R325 0.41 mm from R214 ...

Ordinarily this is a warning you take on the chin. Not here. **30 parts on this
board are DNP** (C106-C108, C210-C213, C303/C323/C343/C363, D201-D204, Q101,
Q102, R101-R104, R210-R213, R304/R324/R344/R364, U204) and - per the already
logged BOM item - they will ship. A build operator resolving "which of these
two 0603s is C363 (DNP) and which is L361 (fit)" from a legend that is 0.06 mm
from the wrong part will get it wrong, and the shunt-FET snubbers and the
converter-idle one-shot are precisely the parts that must **not** be fitted on
branch A. `check_silk` even names the scripted fix
(`place_edit.py move_text`). This is real risk; I do not recommend waiving it.

### W6. `check_pdn`'s "+3V3 has no bulk reservoir" is a false alarm, and the reason it fired is worse than the warning

The rail does have bulk: **C103 and C104 are 10 uF 16 V X7R 0805 on
`+3V3`/GND**. The warning listed only C201, C202, C203, C205, C401.

`check_pdn` inventories only capacitors listed in `kicad/decoupling.json`.
Absent from that file: **C101, C102, C103, C104, C105, C402, C403** - both
`+3V3` bulk parts, both 22 uF `+12V` bulk parts, and both ADC filters. So the
PDN check is blind to 7 of the board's capacitors, and `check_decoupling`
(which reported `pass`) is working from the same partial list.

Verdict on the warning itself: **waive** - the hardware claim is wrong. The
finding is the metadata gap, which silently narrows two P8 checks.

### W7. Both bulk reservoirs are parked in the vacant left third, far from entry and far from load

| cap | board-local | to its J3 entry pad | to nearest load |
|---|---|---|---|
| C103 (10 uF, +3V3) | (10.3, 71.3) | 18.1 mm | 26.6 mm (U203); U202 70.6, U401 81.1 |
| C104 (10 uF, +3V3) | (3.6, 41.1) | 41.7 mm | 47.5 mm (U203) |
| C101 (22 uF, +12V) | (34.6, 40.3) | 38.0 mm | 14.2 mm (U361) |
| C102 (22 uF, +12V) | (52.1, 76.6) | 26.5 mm | 24.8 mm (U301) |

`+3V3` arrives on two pins of a 2.54 mm connector - tens of nH of loop - and
its only reservoir is 18 mm away in the opposite corner from every load. The
four per-channel 4.7 uF input caps do the real work on `+12V`; C101/C102 at
26-38 mm from the connector are contributing little at the entry and little at
the loads.

The cause is visible in `lumina-par_top.png`: the whole left third (x 0-36,
y 26-80) is empty apart from the DNP branch-B front end, while the analog
block is squeezed out past the plane edge at x > 88 (W2) and 42 refdes collide
(W5). The annealer had a large free region and used it for the parts that
least needed it.

### W8. Antenna column: verified genuinely clear, nothing orphaned, two residuals

Answering the specific question directly. Measured copper strictly inside the
board-local rect (88, 25)-(100, 55):

```
F.Cu   0.0000 mm2      In1.Cu 0.0000 mm2
In2.Cu 0.0000 mm2      B.Cu   0.0000 mm2
```

The rule area `aiee_antenna_column_no_copper` is present on all four layers at
absolute (142.937, 82.192)-(154.937, 112.192), which is the ICD rect
translated exactly. The inner pours stop at x = 142.937 as intended. Visible as
the bare right-hand column in `lumina-par_top.png`.

**Nothing was orphaned by stopping the plane there.** In1 GND fills 5833 mm2 in
5 pieces: one of 5826 mm2, and four slivers of 0.75/1.41/1.94/2.70 mm2 located
at board-local x 17-24, y ~ 75.6-76.0 - between J3's pads, nowhere near the
column - each touching 1-3 through-hole pads and therefore tied through the
barrels. In2 +12V is a single piece of 5859 mm2. No net lost connectivity to
the truncation.

Two residuals:

- **The rule area allows `pads` and `footprints`** (`pads allowed`,
  `footprints allowed`; only tracks, vias and copperpour are `not_allowed`).
  Today the column is clean, but nothing prevents a later `place_edit` or
  `route_edit` from dropping a pad or a part in it, and DRC will not object.
- **Two metal features sit just outside the boundary, in the antenna's near
  field 11 mm above the radiator:** R212's pads at board-local x 87.06
  (0.94 mm west of the wall) and TP102, a bare 1.5 mm pad at (95.81, 22.56),
  2.44 mm north of it. Both compliant with s7.6 as written. Flagging because
  s7.6's rectangle is a minimum, not a guarantee, and Q8 kept the radio a
  supported control path.

### W9. Reverse-mounted THT on a fully populated top side is a hand-solder-only operation and no fab note says so

The mezzanine geometry itself is clean: **J3 and J4 are the only bottom-side
parts on the board** (157 of 159 footprints are F.Cu), their 8.5 mm bodies
leave 2.5 mm for the male insulator in the 11.0 mm gap, and there is nothing
else on B.Cu to foul it. `lumina-par_bottom.png` shows a bare bottom side apart
from the two sockets and routing.

The assembly consequence is the problem. The bodies are on the bottom and the
**38 leads are soldered on the top face, which carries the entire SMD
assembly**. That pair cannot go through a wave or a selective nozzle without
masking the whole top side; it is manual. Nearest top-side parts to a J3/J4
pad: C204 2.96 mm, R201 3.18 mm, U203 3.27 mm, TP103 3.55 mm, R207 3.72 mm - 
workable with a fine conical tip, not with a standard chisel, and U203 is the
EEPROM.

Nothing in the fab package flags it. Quoted as ordinary THT, this gets built
wrong or gets re-quoted late.

### W10. `+48V_SW` clears the binding 0.635 mm by 12 um - less than the etch tolerance

Measured minimum outer-layer copper gap on the 48 V net:

| where | gap | vs ICD 0.635 mm |
|---|---|---|
| F.Cu, `+48V_SW` <-> `+3V3`, board-local (15.96, 71.21) | **0.6470 mm** | +0.012 mm |
| F.Cu, `+48V_SW` <-> GND, (14.07, 76.04) | 0.6516 mm | +0.017 mm |
| B.Cu, `+48V_SW` <-> GND, (14.06, 76.05) | 0.6611 mm | +0.026 mm |

All pass. All three are inside a typical +/-0.05 mm outer-layer etch tolerance of
the requirement, so on a bad panel the binding creepage figure is not met.
`check_creepage` demands 0.60 and passes by construction; the DRU rule
`aiee_hv_57v_48V_SW` at 0.635 mm is satisfied by 12 um at the worst point.

ICD s5.2 names the lever and it has not been pulled: *"if P6/P7 needs more
margin, shrink the annulus on the 48 V pads to 1.60 mm before moving anything
else."* J3's pads are still 1.70 mm. Dropping the three `+48V_SW` pads to
1.60 mm buys 0.05 mm at zero routing cost.

### W11. The V48_B 0.590 mm exclusion is correctly scoped - evidence added, not re-opened

Confirming the DRU's own note rather than re-deriving it. Per-neighbour
distance from `/power/V48_B` on F.Cu:

```
0.5900 mm -> /power/Q101_G      (C108's own 0805 land)
0.6626 mm -> GND
0.6637 mm -> /EN_OK
```

The `B.NetName != '/power/Q101_G'` carve-out in `aiee_hv_57v_V48_B` hides
exactly one pair and nothing else on that net drops below 0.635 mm. Q101 is
DNP on branch A so V48_B is never energised on the built board. Carry it on
the branch-B populate checklist, not on this build's defect list.

### W12. The recovery-header choice was made by omission

ICD s7.6 offers a binary: keep board-local (76, 0)-(98, 20) clear enough that a
6-way jumper lead can be attached with the daughter fitted, **or** accept that
the daughter must be removed to recover firmware. The board presents solid FR4
over the whole rect (only H2 is inside it) at an 11.0 mm stack height. A 6-way
jumper on 2.54 mm sockets plus wire bend does not fit in 11 mm, so the board
has chosen option two.

`requirements.md` s5.2, `architecture/decisions.md` and the design doc all
quote the ICD sentence verbatim and none of them records a verdict. The
accepted cost is: unbolt five 11 mm standoffs and unmate a 38-position pair
every time the carrier's firmware needs recovery, on 6-8 fixtures. That is a
decision someone should sign, not inherit.

### W13. The design doc's surviving rationale for J5 says it is on B.Cu; it is on F.Cu

**The board is right and the entry direction is correct - I verified it.** J5 is
`S10B-PH-SM4-TB`, side entry, on **F.Cu** at board-local (54.416, 4.967),
rotation 0, not mirrored. The land is asymmetric front-to-back exactly as it
should be: the ten 1.0 x 3.5 mm signal pads sit inboard at y = 7.738 and the
two 1.5 x 3.4 mm board-lock pads sit outboard at y = 2.197, with the silk body
front face drawn at y = 0.167. The wafer opening therefore faces **-y, out
across the top edge**. It clears the RJ45 notch (J5 spans x 42.3-66.6 against
the notch's 6-36) and the recovery keepout (76-98).

But the P4 close-out in `lumina-par-design-doc.tex` reads: *"...and J5 is on
B.Cu inside the ICD's 11.0 mm mezzanine gap where a top-entry PHR-10 housing
plus bend radius would foul the carrier."* J5 is not on B.Cu. A 10-way PH in
the mezzanine gap would be a defect; the board avoided it. The stale sentence
is the record a future reviewer will use to decide not to re-check, and it
happens to describe the failure mode it claims to have avoided.

### W14. No fiducials, with 0.5 mm pitch on the board

Zero fiducial footprints. The board carries 4 x MSOP-10 with exposed pad at
0.50 mm pitch (the TPS92515HV drivers) and 1 x TSSOP-14 at 0.65 mm (U401).
JLCPCB does not require fiducials and registers from the board edge, so this is
not a blocker - but 0.50 mm pitch is where local fiducials start to earn their
place, and the board has 956 mm2 of free space in the right-hand strip and a
whole empty left third to put them in. Low priority; decide once rather than
discovering it at first-article.

### W15. `verify_all`'s constraints-drift warning is expected and should stay expected

`architecture/constraints.json` and `kicad/constraints.json` differ only in the
documented coordinate frame: every `placement.keepouts` rect and every
`planes[].region` in the kicad copy is the architecture copy translated by
(+54.937, +57.192), plus a `_coordinate_frame` key explaining it. I diffed
both files in full; there is no other difference. **Justified waiver** - but it
will fire on every P8 run forever, and the remediation text ("reconcile or
delete the stale twin") is wrong for this board, because the board-local copy
is the source of truth per its own header.

---

## Triage summary of the 57 verify warnings

| source | n | verdict |
|---|---|---|
| `check_return_path`, In2.Cu / `+12V` reference, `waiver_class: cross_net_reference` | 11 | **Waive individually** (0.13-1.75 mm2 each), **escalate as a class** -> W3 |
| `check_return_path`, In1.Cu / GND, PWM1 on F.Cu, 0.14 and 0.29 mm2 at board-local (72.5, 44.6) and (72.1, 45.0) | 2 | **Justified waiver** - antipad-scale voids in an otherwise continuous plane |
| `check_silk` `silk_misattributed` | 42 | **Real risk, do not waive** -> W5 |
| `check_pdn` `pdn_no_bulk` on `+3V3` | 1 | **False alarm, waive the claim** - C103/C104 are 10 uF; the finding is the `decoupling.json` gap -> W6 |
| `verify_all` `constraints_drift` | 1 | **Justified waiver**, permanent by design -> W15 |
| **total** | **57** | 15 waived, 42 escalated |

Plus the 3 waived `check_silk` errors (TP101/102/103 rings): already logged as
a checker bug, not re-opened. I add one datum only - those three test points
are also the ones E2 says should be carrying a hazard legend and are not.

---

## Waiver recommendations for checkpoint 4

1. **11 x `check_return_path` cross-net-reference** - waive the individual
   geometries; require the class decision in W3 to be recorded (declare `+12V`
   as the B.Cu reference, or move PWM0-3 to F.Cu).
2. **2 x `check_return_path` In1/GND corridor voids** - waive outright.
3. **1 x `check_pdn` `pdn_no_bulk`** - waive the hardware claim; open a
   `decoupling.json` completeness item instead.
4. **1 x `verify_all` `constraints_drift`** - waive permanently with a note
   that the twin is intentional and directional.

Not recommended for waiver: the 42 `silk_misattributed` (W5), and all five
errors.

---

## What I could not judge

- **Component heights.** The board has no 3D height data I can trust for
  anything but J3/J4 (8.5 mm from the ICD). L301/L321/L341/L361 are
  `L_Cenker_CKCS4030` - a 4.0 x 4.0 mm part whose height I did not confirm.
  They are on the top side so the 11 mm mezzanine gap is not at risk, but the
  enclosure lid clearance and the J5 harness bend radius over the top edge are
  outside what a render can settle.
- **Whether U301 is genuinely the hottest stage.** RT401 is 2.10 mm from
  U301's pads, sitting over In1 GND, and 19.9-29.0 mm from the other three
  drivers, so it is a channel-0 sensor, not a board-average one. All four
  drivers are declared at an identical 0.15 W in `constraints.json`, so the
  declaration cannot distinguish them; `power_tree.md` gives the red string a
  different duty from G/B/W, which should make one stage hotter than the rest.
  Which channel is red, and whether it is channel 0, is a schematic question I
  did not chase.
- **Pin-1 and polarity marks on the SMD parts after assembly.** I confirmed
  the connector markers (E4) but did not audit all 157 top-side footprints for
  post-assembly visibility of their own polarity marks; with 42 refdes already
  misplaced (W5) it is worth a dedicated pass.
- **The enclosure.** Wall conduction is the load-bearing assumption in ICD
  s7.7.3 and none of it is on this board.
