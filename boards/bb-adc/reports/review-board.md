# review-board - bb-adc, P8 adversarial board review

Fresh-context review of `kicad/bb-adc.kicad_pcb` (54.75 x 34.92 mm, 2L, 1 oz,
JLC2313_1.6, 25 footprints, 21 nets). Gates going in: `erc` PASS,
`drc_routed` PASS 0/0, `sim` PASS, `verify` PASS with one waiver.

Build mode `learning block-basics:` -> scope tier **block-only**, binding
**canonical**. Absent protection, ESD, indicators, test points, second rails
and filtering the datasheet does not require are OUT OF SCOPE and are not
reported below. The outline was judged against the 54.75 x 34.92 the placement
EARNED (`reports/board_edit-fit.json`, from a 63.95 x 66.03 provisional), never
against a stated number.

Renders made for this review: `reports/renders/bb-adc_top.png`,
`bb-adc_bottom.png`, `bb-adc_iso.png`.

**5 errors, 5 warnings, 2 waivers recommended.** (W2 below is a waiver verdict,
not a finding, so it carries no entry in `review-board.json`.)

---

## E1 - J1's wire entry faces INTO the board. The terminal is 180 degrees out.

`reports/renders/bb-adc_top.png` - the two dark throats in the green terminal
body are on its EAST face, pointing at R1. The west face, 1.0 mm from the board
edge, is a closed wall.

Proved from the library, not from the render. In
`lib/aiee.pretty/CONN-TH_2P-P5.00_WJ500V-5.08-2P.kicad_mod` the pads sit at
local `(+/-2.54, 0)` and the body spans local y `-5.64 .. +4.52`. The vendor 3D
model (`aiee.3dshapes/...wrl`, VRML y = -footprint y) has two openings 3.0 mm
wide spanning z 3.0 .. 9.8 mm, centred on x = +/-2.54 - i.e. directly in line
with the two pins - in the face at footprint y = **+4.50**. The opposite face
(y = -5.50) is solid except for ribs at z 0..1.0 and 6.5..6.69. The wire entry
is therefore the face NEARER the pins, which is also how this class of block is
built.

J1 is placed at (24.500, 39.060) rot 90, which maps footprint +y to board +x.
The throats open EAST at x = 29.0, 2.2 mm from R1's pad and 11 mm from the west
edge the body is parked against.

Three artifacts say this is wrong:

- `kicad/constraints.json` `placement.edges` J1: *"Screw terminal, opening
  outward."*
- `requirements.md` s5: *"the screw terminal and the host header sit on
  different board edges with their openings facing outward, so the analog input
  wiring does not have to cross the digital header to reach the bench."*
- the schematic's J1 note: *"ANALOG IN 0-5V: 1=SIG (Rs<=200ohm), 2=GND. LEFT
  edge, opening outward"*.

Consequence: the field lead must be inserted from the board's interior and then
laid back across the 1 Mohm divider string, the buffer and the J2 ribbon to
reach the bench - the exact geometry the constraint exists to forbid, and a
metre of unscreened wire draped over a guarded 240 kohm node.

Fix: rotate J1 to rot -90. Pads keep x = 24.5; `/AIN_RAW` and `GND` swap to
y = 36.520 / 41.600, so both need re-routing. The body then spans x 20.0..30.0
- 2.0 mm off the west edge and 1.2 mm from R1's pad, so a ~1 mm westward nudge
is worth taking with it. See also W6: the footprint's own silk arrows point at
the closed wall.

## E2 - J2 carries no pin-1 mark that survives assembly, and the schematic makes one mandatory

The schematic says it twice, once in capitals with asterisks:

> NOTE 6 `*** J2 MIS-MATE IS DESTRUCTIVE AND UNPROTECTED: pin 1 = +3V3 and
> pin 6 = GND, so a 180 degree reversal shorts the host's rail to its own
> ground through the cable. No series protection, no reverse diode, no keyed
> housing - all excluded by the scope tier. P6 must silk a pin-1 marker and a
> 1..6 legend. ***`

The board's pin order confirms the hazard exactly: J2 = +3V3 (y 33.650), GND
(36.190), /CS (38.730), /SCLK (41.270), /DOUT (43.810), GND (46.350). Reversed,
the host's 3V3 lands on board pin 6 = GND.

What is actually on the silk: one line at y = 34.920 dividing the pin-1 cell,
and an `fp_circle` at (69.250, 32.380) of radius **0.03 mm** stroked 0.15 -
a 0.21 mm blob sitting exactly on the corner where two 0.25 mm outline strokes
meet, so it is swallowed by the outline. Both live inside the silk rectangle
x 69.250..71.750 by y 32.380..47.620 = 2.50 x 15.24 mm, which is *under* the
header's 2.54 x 15.24 mm plastic body. There is no "1", no 1..6 legend and no
rail names anywhere.

After assembly nothing is readable from the mating side. `bb-adc_top.png` shows
the black body filling a plain white rectangle. The only surviving indicator is
pad 1's square shape, visible only from the bottom (`bb-adc_bottom.png`).

Fix: silk text west of x = 69.25 - there is clear board from x 66.4 to 69.25
for most of the run, and the C1/C2 refdes can move. A "1" plus the six names is
what the schematic asked for.

## E3 - J1 has no SIG/GND marking, and the design doc says it does

`reports/design_doc/bb-adc-design-doc.tex` publishes:

> `J1` | 2-pole 5.08 mm THT screw terminal, **silk-marked SIG and GND** |
> 1=`/AIN_RAW`, 2=`GND`

`requirements.md` s2 states the same requirement, and s8 makes it load-bearing:
*"the board has no input protection by mode, so the silk marking and the
owner's answer to Open question 5 are the only defenses against a wrong
connection."*

The board's silkscreen contains 25 texts. All 25 are reference designators.
There is no SIG, no GND, no polarity legend. J1's pin-1 dot (`fp_circle` at
(29.000, 44.270), radius 0.03) sits on the body corner and is covered by the
10.0 x 10.76 mm plastic body, so it does not survive assembly either.

A published claim that the artifact does not carry is a defect in both.

## E4 - the contracted input-impedance numbers are missing from the silkscreen

The P2 ruling that narrowed the owner's answered Q9 (`requirements.md` s9,
`architecture/blocks.md`, and the design doc's decision log) reads:

> the contract is now **source <= 200 ohm** ... and **board presents
> 1.00 Mohm** ... **Both numbers go on the silkscreen.** ... the contract
> belongs on the silk because input impedance is a specification of the
> instrument

Neither number appears on F.SilkS or B.SilkS. This one matters more than
ordinary legend text: the ruling NARROWED what may legally be connected to the
terminal by 5x, and the silk was named as the place that travels with the
board. A 1 kohm source - inside the envelope the owner originally answered -
now produces 5 mV of loading error, the entire 25 C budget, with nothing on the
hardware to say so.

## E5 - GND copper sits inside the closed guard ring

**First, the closure, re-proved geometrically and independently of any render -
the ring IS closed, with margin.**

1. Polygon evidence. The `/AIN_BUF` zone's filled polygon on F.Cu is a single
   island whose ring has exactly **one interior hole**, area 7.951 mm2, bounds
   (41.106, 38.523) - (44.494, 42.416). Zone copper 17.176 mm2; 19.08 mm2 with
   the net's own pads and the U3.1/U3.4 stub, matching the 19.03 mm2 claimed.
2. Raster evidence. Rasterised at 2.5 um over an 8.2 x 8.8 mm box, a flood fill
   started from every `/AIN_DIV` cell and allowed to spread through *all*
   non-`/AIN_BUF` space, 8-connected so it can leak diagonally (the
   conservative direction), never reaches the box border.
3. Margin. Eroding the guard copper by 200 um on every edge (19.11 -> 10.18 mm2
   of pour) leaves the ring still closed. Closure in the as-built copper is not
   marginal; the "does not close at 0.2 mm" figure describes re-pouring at a
   larger zone clearance, not the copper on this board.
4. Drive. The zone is on `/AIN_BUF` and is galvanically continuous with U3
   pin 1 (OUT) and pin 4 (-IN) - same potential, low impedance, as record
   `resistive-attenuator-high-z-tap-guard-and-leakage` requires. Clearance to
   the node is a uniform 0.1275 mm all the way round. The 19.08 mm2 plate adds
   ~0.5 pF to the follower output over the 1.53 mm core; no stability cost, and
   R6 = 49.9 ohm isolates the 1 nF bucket regardless.

**The defect is what the closed ring encloses along with the node.** Inside the
guarded enclosure there are two GND conductors: U3 pin 2 (V-) and a 0.6 mm GND
via at (41.850, 39.850). Measured F.Cu surface gaps at the tap:

| path | gap |
|---|---|
| `/AIN_DIV` trace -> GND via (41.850, 39.850) | **0.227 mm** |
| `/AIN_DIV` trace -> U3.2 pad | 0.289 mm |
| U3.3 pad -> U3.2 pad | 0.350 mm |
| `/AIN_DIV` -> nearest guard copper | 0.1275 mm (but on the *outside* of all three) |

The guard intercepts nothing on those three paths, and they carry the largest
potential difference anywhere near the node.

Priced with `architecture/blocks.md` s3.6's *own* model - a 1 Gohm surface path
under no-clean flux plus humidity, "and JLC does not wash boards":

- the +3V3 path the guard was built to stop drives 3.3 - 2.0 = 1.3 V ->
  1.3 nA -> 1.3 nA x 240 kohm / 0.400 = **0.78 mV** at the terminal (the
  document's own number);
- the unguarded GND path drives the full node voltage, 2.000 V at a 5.000 V
  reading -> 2.0 nA -> **1.20 mV** at the terminal.

Error-budget row 9, "Divider-node leakage, GUARDED (estimate)", carries
**0.10 mV**. It is understated about 12x for the path that now dominates, and
row 9 is the table's only +/-3x estimate. RSS at 25 C moves 3.23 -> 3.44 mV
(still inside the 5.00 mV target) and the worst-case sum moves up ~1.1 mV, so
the board still closes its spec - but the guard's stated 3.3e5 collapse factor
does not hold for the leakage term that matters, and a 0.1 %-class instrument
publishing 3.25 mV RSS should not rest on a number that is wrong by an order of
magnitude.

Split of the fix:

- The GND via at (41.850, 39.850) is a free routing choice. It sits 0.65 mm
  south of U3.2, i.e. on the pin-3 side. Moving it north or west of the pad, or
  outside the ring entirely, restores 0.227 -> >0.5 mm. **This is the part to
  fix.**
- The U3 pin2/pin3 0.350 mm channel is irreducible in SOT-23-5 at the fab
  floor: a guard trace needs 0.127 + 2 x 0.127 = 0.381 mm and only 0.350 mm
  exists. It has to be re-stated in row 9, not fixed in copper. (Also note that
  a stated purpose of the guard was to keep the board's dominant uncertainty on
  vendor maxima rather than on a leakage estimate - that argument is weakened
  by exactly this much.)

Not raised as drift, for the record: the guard is single-sided where the record
asks for "both sides of the board". That is an explicit recorded trade in
`constraints.json` corridors R3->U3 ("here the back face is the unbroken B.Cu
GND pour that D1 requires, so the ring is single-sided by a recorded trade").
B.Cu under the node measures 100 % GND pour. The trade is legitimate; what it
never records is the record's own price for it - bulk leakage falls only about
one order of magnitude, set by board thickness and ring width.

---

## W1 - the one verify_all WARNING is a false positive, and its cause is a real hole

`check_pdn` / `pdn_no_bulk`: *"power rail +3V3 has 2 cap(s) but no bulk
reservoir (>= 1 uF); only ceramics hold it"*, refs C4, C6.

Wrong on the facts. C1 = 10 uF X5R 0805 sits on +3V3/GND at (68.000, 34.920),
0.925 mm (pad edge) from J2 pin 1 - precisely the "bulk 10 uF at the RAIL
ENTRY" that `constraints.json`'s `entry` group specifies and earns by
arithmetic. The rail has its reservoir.

The cause is that `kicad/decoupling.json` lists six associations - C2, C3, C4,
C5, C6, C8 - and **omits C1**. C7 is correctly absent (signal-path charge
bucket, not decoupling). So `check_pdn` counted 0.2 uF, and, more to the point,
`check_decoupling` never examined the rail-entry bulk at all: it passed by not
being asked.

**Verdict: waive the warning, fix the metadata.** Add `{"cap": "C1", "ic":
"J2", "pin": "1", "rail": "+3V3", "value": "10uF 25V X5R"}` and re-run so the
bulk is actually checked rather than assumed.

## W2 - the /CS return-path waiver: I agree, and here is the independent check

Both of the waiver's reasons hold up.

*(a) Out of model* - verified. F.Cu carries exactly one zone, `/AIN_BUF`
(19.08 mm2, 12+ mm west of the crossing). There is no GND zone on F.Cu at all,
so `check_return_path`'s adjacent-layer model gives every B.Cu trace zero
reference copper by construction. The reported "0.03 mm / 0.20 mm2" is what
survives of the 1.93 mm tunnel after the checker's own excision disks around
the two /CS vias (0.3 mm via radius + 0.5 mm zone clearance = 0.8 mm each). It
is a bookkeeping remainder, not a measurement of anything physical.

*(b) Topologically forced* - verified. At U1 the order down the page is /SCLK
(y 39.680), /DOUT (40.330), /CS (40.980); at J2 it is /CS (38.730), /SCLK
(41.270), /DOUT (43.810). /CS must cross both other signals: a 3-cycle, and one
layer cannot resolve it.

*(c)* Refusing to shorten the tunnel 0.09 mm so the excision disks overlap, at
the cost of ~0.04 mm of via-to-trace DRC margin, is the right call. Spending
manufacturing margin to land inside a checker's arithmetic is a bad trade.

**Uphold the waiver.** One thing to name that the checker did *not* report, on
the other side of the same geometry: the B.Cu tunnel plus its two via antipads
cut a ~1.2 mm-wide slot in the GND pour, and both `/SCLK` (y 39.680) and
`/DOUT` (y 40.330) cross it on F.Cu at x ~ 66. Each crossing happens to fall
inside a /CS via's excision disk, so neither surfaced. At 5 ns edges the added
return inductance is ~1 nH and the site is 12+ mm east of the analog section,
so I do not escalate it - but it is a second reason the next-revision fix the
waiver already names (J2 pin order CS, DOUT, SCLK) is worth doing: it removes
the slot as well as the bookkeeping.

## W3 - 87 mV of reference headroom, with the rail noise not yet subtracted

`blocks.md` s8.2 records the number honestly: the ADR4520's guaranteed input
floor is 3.048 V (VOUT 2.048 + VDO_max 1.000 at no load and at 2 mA, record
`series-voltage-reference-input-headroom-gate`), against the 3.135 V worst-case
rail - **87 mV**.

The layout does not eat it: J2 pin 1 to U2 is ~18.9 mm of 0.5 mm 1 oz copper
= ~19 mohm, and at the 2.7 mA peak draw that is 0.05 mV. Good.

What is not in the recorded analysis is the rail spec the owner answered in Q7:
"tens of millivolts of noise". A 40-50 mV negative excursion eats half to all
of the margin, and below the floor VOUT has *already* degraded 0.1 % = 2 mV,
which maps one-for-one to gain error = 5 mV at the terminal
(`sar-adc-reference-sets-the-gain`). C1 (10 uF) + C4 (0.1 uF) + C5 (2.2 uF on
the output, holding a 14 uA load) absorb a short dip; a sustained low rail they
do not. None of the six sim benches covers input headroom.

Recommend a bring-up line rather than a board change: measure VIN at U2 pin 2
and require >= 3.05 V under the host's worst rail.

## W4 - the mounting holes are a trapezoid, not a rectangle

H1 (22.450, 48.500), H2 (22.450, 23.000), H3 (68.300, 23.000), H4 (65.000,
48.500). H4 is 7.75 mm in from the east edge where H3 is 4.45 mm.

Forced, and I can see why: H4 at (68.3, 48.5) would drive its 3.6 mm courtyard
into J2's (x 69.250..71.750, y 32.380..47.620) on a 34.92 mm-tall board whose
15.24 mm header is centred at y = 40. `requirements.md` s5 asked for "4 x M3
clearance holes (3.2 mm) inset from the corners" and explicitly allows two on
opposite corners if the outline is too small, so this is inside the letter of
the requirement and the board still mounts on four points.

Reported so the choice is visible: any bench plate or standoff set has to be
drilled to a trapezoid, and nothing in the artifacts says so.

## W5 - requirements.md still describes a J2 the board improved on

`requirements.md` s2 / Q6 says "4 signal pins for SPI, so 6 pins for SPI".
The board fits 6 pins as three signals plus a second ground: +3V3, GND, /CS,
/SCLK, /DOUT, GND. That is better, and it is deliberate and recorded
(`constraints.json` edges J2: "ground adjacent to the digital group at both
ends of it"). The stale sentence is in the P0 artifact only. No board change -
sync the document so the artifact set stops disagreeing with itself.

## W6 - the J1 footprint's silk insertion arrows are on the wrong face

`CONN-TH_2P-P5.00_WJ500V-5.08-2P.kicad_mod` draws two filled arrow polygons at
local x -3.0..-2.0 and +2.08..+3.08, running from local y -5.5 to -2.5 and
pointing inward - i.e. on the y = -5.64 face. The wire throats are in the
y = +4.50 face (E1). On the placed board the arrows land at board y ~ 41.56,
x 19.0 -> 22.0, pointing the operator at the closed west wall.

Independent of how E1 is resolved, the footprint is internally inconsistent and
misinforms whoever wires the terminal. Fix the library part, not just the
placement. (The footprint name also says `P5.00` while the pads are correctly
at 5.080 mm pitch - cosmetic, but it is the same file.)

---

## Verified clean

Recorded so a later reader knows these were checked, not skipped.

- **`/AGND_SENSE` is intact and nothing defeats it.** The net is exactly
  {U1.3, R5.2, R8.1}. Two F.Cu tracks (7.183 mm R5.2 -> U1.3, 1.950 mm
  R5.2 -> R8.1), **zero vias, zero B.Cu copper**, and there is no F.Cu GND zone
  anywhere on the board, so there is no pour contact to have. R8 is on the
  FRONT side at (49.800, 44.300). The sense tap is R5's own bottom pad, so the
  string's 5 uA return through R8 is outside the sensed node. Nearest GND
  copper is U1 pin 4 at 0.243 mm - VSSOP-8 0.65 mm pitch, unavoidable and
  harmless. The single-point tie holds.
- **Single-sided assembly holds.** 0 SMD pads on B.Cu, 0 flipped or back-side
  footprints. B.Cu carries the GND pour and one 1.93 mm /CS track.
  `bb-adc_bottom.png` shows THT pads and four holes only.
- **Placement separations from `constraints.json` all pass with margin:**
  R1-R5/U3 vs J2 19.238 mm (>= 10), R1-R5 vs U1 5.676 mm (>= 5), U2/C5 vs J2
  12.181 mm (>= 5), U2 vs H1/H2 29.771 mm and vs H3/H4 8.521 mm (>= 5).
  D2's 2.5 mm SPI-to-analog routing floor holds at 2.605 mm pad-to-pad (U1's
  own pins) and 3.911 mm trace-to-trace.
- **Decoupling geometry matches the records.** C2 (0.1 uF) 0.722 mm from U1
  pin 8 with C8 (10 uF) behind it at 3.640 mm - "smaller capacitor closest to
  the pin" (`sar-adc-supply-bypass-and-rail-isolation`). C3 (47 uF) 1.291 mm
  edge / 2.290 mm centre from U1 pin 1, same layer, no via between pad and cap
  (spec <= 2.5 mm). C5 0.917 mm from U2 pin 6; C3 + C5 = 49.2 uF, inside the
  ADR4520's 1-100 uF window.
- **Outline earned, not given.** Edge.Cuts 18.00..72.75 x 18.03..52.95 =
  54.75 x 34.92 mm, from the 63.95 x 66.03 provisional via
  `board_edit --outline fit` (`reports/board_edit-fit.json`). Judged against
  what the design earned.
- **No block or interface is missing.** B1 (R1-R5), B2 (U3 + C6), B3 (U1 + R6/
  C7 + R7/C2/C8), B4 (U2 + C4/C5), C1 rail entry, R8 sense tie - all present.
  J1 2-pole 5.08 THT, J2 6-pin 2.54 single row, 4 x M3 3.2 mm all present.
  Power3V3 at 0.5 mm on +3V3 (44.07 mm of track) and the 0.6 mm VREF segment
  C3.1 -> U1.1 (2.290 mm) are both on the board as cited.
- **check_silk's blind spot, named.** It passed, and correctly: it checks
  silk-over-pad, legibility and refdes attribution. It has no concept of a
  *required* marking, nor of whether a marking survives assembly. E2/E3/E4 all
  live in that gap.

## Waivers recommended

1. **Uphold** the existing `check_return_path` /CS waiver (W2). Both stated
   reasons verified independently; the residual is a checker artifact.
2. **Waive** the `check_pdn` `pdn_no_bulk` warning on +3V3 (W1) - the bulk
   exists - but treat the incomplete `decoupling.json` as a defect to fix, not
   as part of the waiver.

## Open - what I could not settle

- E1's wire-entry direction rests on the vendor 3D model plus the pin-offset
  geometry, not on a vendor mechanical drawing I fetched. The two sources
  inside the footprint disagree with each other, so confirm against the
  WJ500V-5.08-2P drawing before rotating the part. Either way the footprint is
  self-contradictory and W6 stands.
- The 1.20 mV in E5 scales linearly with the real surface-insulation
  resistance, which is an estimate (blocks.md prices it +/-3x). A washed board
  makes it negligible; a humid, unwashed one makes it worse.
- Whether the trapezoidal hole pattern (W4) is a real nuisance depends on a
  bench plate I cannot see.
