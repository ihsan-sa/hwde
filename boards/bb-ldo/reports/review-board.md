# bb-ldo - board review (P8, adversarial, fresh context)

Board: `kicad/bb-ldo.kicad_pcb`, 50.000 x 26.420 mm, 2 layers, 5 parts.
Mode `block-basics` / scope `block-only` / binding `canonical` - protection,
filtering, indicators, test points, config and mechanical are SCOPE, and their
absence is not reported below. The board size is compared only to what the
design earned and recorded, never to any stated number.

Renders made for this review (all in `reports/renders/`):
`bb-ldo_top.png`, `bb-ldo_bottom.png`, `bb-ldo_iso.png`, and two I added
because the top-down 3D view is actively misleading about connector
orientation: `bb-ldo_left.png`, `bb-ldo_right.png`.

Coverage note: `reports/checks/summary.json` does not exist on this workspace.
The equivalent record is the `coverage` block in `reports/gate-verify.json`:
all 8 required checks RAN, `skipped_error` empty, `not_applicable` empty. So
there is no hole from a skipped check. Advisory legs `check_irdrop` and
`check_pdn_z` both pass. `dfm_check` / `fab_export` have not run - that is P9,
not a hole at P8.

---

## 1. Verdict on waiver 1 - check_thermal `thermal_area` (ERROR, waived)

**SOUND. The waiver should stand.** I re-derived every load-bearing claim
rather than accepting it, and two of them were the ones that could have
silently invalidated the whole thing. Both hold.

*The clamp is real, and it is in the source, not in the argument.*
`check_thermal.py` sets `A_SAT_MM2 = 645.0` and
`REACH_MM = sqrt(645/pi) = 14.33`, then computes
`a_eff = min(645, net_copper  intersect  circle(part_centroid, 14.33))` and
`theta_ja(a) = 55 + (174-55)*exp(-a/350)` clamped at `A_SAT`. Two independent
ceilings therefore bind at the same number: the credited area can never exceed
645 mm2 because that is the *area of its own reach circle*, and the model
clamps at 645 anyway. `theta_ja(645) = 73.85 C/W`. The board's target is
`dt_c 65` at 1.00 W, i.e. 65 C/W. **No 2-layer layout of any kind can pass
this check at this target** - not a better pour, not a bigger board, not a
different placement. The gate is unreachable by construction, which is exactly
what a waiver is for.

*The delivered copper is what the waiver says it is - I measured it myself
from the routed board's filled polygons, not from the P6 estimate.*

| claim in the waiver | my measurement | verdict |
|---|---|---|
| 1199.221 mm2 contiguous F.Cu +3V3 pour | **1199.221 mm2** | exact |
| ONE island, 0 mm2 orphaned | one filled outline, contains U1 pad 4 | confirmed |
| 1085.679 mm2 within 25 mm of the tab | **1086.18 mm2** (circle discretisation) | confirmed |
| (checker's own figure) 584.97 mm2 | **585.76 mm2** inside r=14.33 at U1's pad centroid (29.515, 32.91) | confirmed |

Reach-circle budget, which is the honest way to read the 585: the circle is
645.12 mm2; 16.72 mm2 of it falls off the board edge (the board is 26.42 mm
tall, the circle is 28.66 mm across); 42.64 mm2 is carved by pads, the +5V
corridor and clearances. **The pour occupies 91 % of every square millimetre
the checker could ever credit.** There is no layout headroom left inside the
model.

*The claim that could have killed the waiver, and did not.* The whole waiver
rests on the tab being poured SOLID. If the zone had been left on KiCad's
default thermal relief, U1's tab would reach 1199 mm2 of copper through four
0.5 mm spokes and the delivered theta_JA would be far worse than the checker's
own pessimistic number - and nothing in the gate record would have shown it.
Checked directly: the zone carries `(connect_pads yes (clearance 0.5))`, and
geometrically U1 pad 4's full 8.424 mm2 is merged into the pour (ring probe:
copper on 72/72 of a circle at r=2.2 mm around the tab). U1.2, C2.1 and J2.1
are likewise fully merged. **The heat path is genuinely unobstructed.**

*Two caveats that do not change the verdict but belong in the record:*

1. The waiver says the two vendor sweeps "agree within ~1 C/W where they
   overlap". They do not overlap: AMS gives 65 C/W at 1000 mm2 and TI gives
   66 C/W at 645 mm2, which are different areas. The correct statement is that
   they *bracket* - two vendors, two test boards, both landing in the
   mid-60s C/W over the area band this board occupies. That is still good
   evidence; it is just not a point-for-point agreement, and the waiver
   overstates it slightly.
2. The margin is thin and everything in it is estimated. Tj 110-115 C against
   125 C is 10-15 C, sitting on a model both vendors hedge in their own words
   ("a rough guideline... some experimentation will be necessary"; "not part
   of the TI component specification"), plus an ASSUMED 5 mA Iq (power_tree
   gap 1 - the part's max is typically 10 mA, worth ~+1.6 C). **Bring-up
   measurement of the tab temperature at full load in still air should be an
   explicit acceptance step before any quantity order**, not an optional
   nicety. The waiver already says as much; make it a condition.

## 2. Verdict on waiver 2 - check_current `insufficient_transition_vias` x3

**SOUND on the current question. The topology claim is true.** Verified
against the board, not the prose:

- `J1.2` (GND) and `J2.2` (GND) are both `thru_hole` pads with
  `(layers "*.Cu" "*.Mask")`, i.e. their barrels penetrate F.Cu and B.Cu
  directly. Confirmed visually in `bb-ldo_bottom.png`: both show a four-spoke
  thermal relief into the plane, while J1.1 (+5V) and J2.1 (+3V3) show an
  isolating antipad.
- The B.Cu GND zone is a single unbroken island of 1226.833 mm2 covering the
  whole board. Ring probes at r=1.25 mm confirm 4-spoke relief on both GND
  terminals (20/72 of the ring is copper) and full isolation on both rail
  terminals (72/72 clear).
- Therefore the 0.515 A load return runs J2.2 -> B.Cu -> J1.2 and **never
  passes through any of the three stitch vias**. Those three vias serve only
  C1.2, C2.2 and U1.1 - U1's ground/quiescent current and capacitor ripple,
  milliamps. The heuristic's per-via 0.515 A attribution is wrong here, and
  the check labels itself advisory for exactly this reason.

**But the waiver answers the ampacity question and leaves a different one
open**, which I have raised separately as finding 2 below: those same vias are
the *only* connection between each F.Cu GND pad and the plane, because F.Cu
carries no GND copper at all (it is the +3V3 pour). One via, no redundancy,
and for U1.1 the failure consequence is not "warm via" but "regulator loses
its ground reference". That is a reliability argument the ampacity waiver
never addresses, and it is not covered by it.

---

## 3. Findings, worst first

### F1 (ERROR) Three unfilled vias sit inside SMT solder pads

`reports/renders/bb-ldo_top.png` shows nothing here - it is under the parts.
The geometry:

| via | lands in | pad size | overlap | note |
|---|---|---|---|---|
| (17.318, 32.910) | **C2.2** (GND, tantalum) | 2.185 x 3.780 | fully inside (0.283 mm2) | 0.65 mm from pad centre |
| (24.820, 37.310) | **C1.2** (GND, tantalum) | 1.530 x 1.296 | 0.209 mm2 inside | 0.65 mm from pad centre |
| (27.677, 30.064) | **U1.1** (GND, the regulator) | 2.500 x 1.100 | 0.144 mm2, **centre on the pad boundary** | drill breaks the pad edge |

Assembly is JLCPCB economy PCBA, which does not fill or plug vias. Paste
apertures equal the pads (`pad_to_mask_clearance 0`), so paste is printed
directly over open 0.3 mm barrels. At reflow the solder wicks into the barrel
and the flux volatiles have nowhere to go (the back side is tented), giving a
starved and voided joint. Two of the three are polarised tantalum
terminations, where a void under one termination also tilts the part.

U1.1 is the worst instance and deserves its own sentence: the via centre sits
0.004 mm inside the pad edge, so 0.146 mm of the drilled hole is *outside* the
mask/paste aperture, under a mask sliver that will not tent at that size - and
this pad is the regulator's only ground connection.

Root cause, so the fixer does not just move three vias and leave the trap
armed: `stitch_vias.py` documents its candidates as "rings just past the pad
edge" but `RING_RADII = (0.65, 0.9, 1.15)` are measured from the pad **centre**
(`ring_candidates(pad.center, bearing)`), and `via_check` only tests foreign
copper, so a same-net pad overlap is never rejected. Any pad with a half-extent
over 0.65 mm gets a via inside it. That is most tantalum and SOT pads.

Fix and its price: move each via 0.4-0.6 mm further out and let the tool's
existing `add_track` stub carry it (the code already emits one when the disc
misses the pad). A 0.6 mm via with its 0.5 mm zone clearance removes 2.01 mm2
of pour; three of them cost about 6 mm2 of the 585 mm2 effective copper, i.e.
roughly 0.1 C/W. That is a rounding error against a 10-15 C margin, and the
right trade.

### F2 (WARNING) U1's ground reaches the plane through exactly one via

F.Cu carries no GND copper anywhere - the top layer is the +3V3 heatsink pour
by design. So U1.1's single 0.3 mm via at (27.677, 30.064) is the *entire*
ground path of the regulator. If that barrel is open or cracked (and per F1 it
is the joint most likely to be compromised), U1 has no ground reference and
its output rises toward VIN: **5 V on a rail specified at 3.20-3.40 V**, into
whatever the owner has wired to J2, on a board that by accepted scope has no
protection anywhere. The ampacity waiver's cross-section argument is correct
and does not touch this.

Add a second via on U1.1 (and, while there, on C2.2 which is the compensation
capacitor's only return). Cost is 2.01 mm2 of pour each. This is redundancy,
not ampacity - do not let it be re-argued as the waived question.

### F3 (WARNING) J2 pin 1 is solid-poured to 1199 mm2 and then hand-soldered

`planes` declares `{"layer": "F.Cu", "net": "+3V3", "connect": "solid"}`, which
is exactly right for U1's tab and is why waiver 1 holds. But the setting is
zone-wide, and J2.1 (+3V3) is a **through-hole screw-terminal pin that
`requirements.md` s.7 says is hand soldered after PCBA**. Measured: J2.1's full
3.142 mm2 is merged into the pour, with copper on 72/72 of a ring at r=1.6 mm -
a completely solid tie to 1199 mm2 of 1 oz copper.

This is the classic un-solderable joint: the iron cannot raise the pad because
the plane drains it, and the operator either gives up with a cold joint on the
3.3 V output pin or overheats the board trying. Every other hand-soldered pin
on this board is fine - J1.2 and J2.2 already get four-spoke relief from the
B.Cu zone, and J1.1 is isolated on both layers. J2.1 is the single exception.

Fix: a per-pad `(zone_connect 1)` on J2.1 only. It sits 17.49 mm from the tab,
outside the checker's 14.33 mm reach entirely, and the relief removes about
2.93 mm2 of pour out in the partial-effectiveness band - thermally free. If
instead this is left as-is, say so in the fab/assembly note so whoever solders
it brings a preheater.

### F4 (WARNING) The board is built at 0.127 mm clearance, not the 0.2 mm its netclasses declare

Measured pad-to-pour gap on every isolated pad on the board: **0.127 mm
exactly** (C1.1, C1.2, C2.2, J1.1, J1.2, J2.2, U1.1, U1.3 - all identical).
But `bb-ldo.kicad_pro` puts +5V, +3V3 and GND in netclasses `Pwr_0p255mm` /
`Pwr_0p2575mm` with `"clearance": 0.2`, and the zone itself declares
`(connect_pads yes (clearance 0.5))`. Neither took effect.

The likely mechanism, for the fixer to confirm: `bb-ldo.kicad_dru` contains

```
(rule "aiee_clearance_floor"
	(constraint clearance (min 0.1270mm))
)
```

with **no condition**, so it matches every object pair on the board, and a
matching custom rule outranks the netclass value it was meant to floor. The
file's own header comment says "Baseline (fab floor) first, per-net design
rules last (later rule wins)" - but `rules_gen` emits per-net rules for
`track_width` only, never for `clearance`, so nothing ever wins it back.

Consequence here is mild - 0.127 mm is JLC's stated 2-layer minimum and DRC is
clean at 0/0 - but the board is fabricated with zero etch and registration
margin where the design intended 57 % more, and the delivered pour is very
slightly larger than `thermal_area.json` modelled (it assumed the 0.2 mm
figure). The reason it is a finding rather than a note is that this is a
generated-rules defect that will apply to every board this pipeline makes,
including ones where the difference is a safety clearance rather than an etch
margin.

### F5 (WARNING) `check_thermal`'s via warning is suppressed by a constraint, not by a waiver

`check_thermal` computes `need_vias = (dt/power) < theta_ja(A_SAT)`, which on
this board is `65 < 73.85` -> True, and would then emit a `thermal_vias`
warning for `len(vias) < min_vias`. It does not, because
`constraints.json thermal[0].min_vias = 0` makes the test `0 < 0`.

**The engineering is right** - the tab pour is +3V3 and B.Cu is a continuous
GND plane, so a stitch via there is a short, and `state.json` records the
12 -> 0 correction on a schematic-reviewer finding with a verified knowledge
record behind it. I am not asking for it to change.

The finding is about the audit trail: a checker warning was silenced by a
constraint value, so `gate-verify.json` reports `warning: 3` when the honest
count of "things this checker wanted to say" is 4, and the reasoning lives in
a `_min_vias_why` comment rather than in `verify-waivers.json` where a reviewer
looks. Either add a third waiver record restating that reasoning, or have the
gate surface constraint-suppressed checks. Whoever reads only the gate JSON
cannot currently see that this decision was made.

### F6 (WARNING) The outline's area was earned; its aspect ratio was not

The binding is `canonical`, so geometry is an output, and the *area* genuinely
is one - 50.000 x 26.420 mm came out of `board_edit --outline fit` over a
thermally-driven placement, and `thermal_area.json` shows the work. The
*aspect ratio* did not. It is fixed by `constraints.json placement.edges`,
which pins J1 to the left edge and J2 to the right edge. Two 10.16 mm-deep
connectors on opposite ends plus U1+C1+C2 between them cannot fit in less than
about 50 mm of width, and the height then follows from the vertical stagger.

That matters because heat spreads radially. At the same 1321 mm2 of board, a
squarer outline with the tab near the centre would put roughly 1300 mm2 inside
25 mm of the tab instead of the delivered 1086 mm2 - about +200 mm2 of
effective copper, worth roughly 1.4 C/W off theta_JA on the AMS table's own
slope, i.e. about 10 % of the 10-15 C junction margin.

**Recommend waiving this for this build.** The gain is real but small, the fix
is a re-placement plus a re-route plus a re-pour, and the delivered layout is
already the best of the three the pipeline produced (the P6 record shows
cand1's 517 mm2 within 25 mm being overruled for the delivered 1086). It is
logged because it is the same species as the bb-buck defect this run exists to
teach - a geometry input that bound the design without ever being earned -
just a much smaller instance, and because at `canonical` binding nothing else
in the pipeline will ever notice it.

### F7 (WARNING) No hot-surface legend on a board whose top copper is the radiator

At the design point the tab copper sits around 95 C and the pour is 65-80 C
across most of the top face; the whole board is the heatsink, so there is no
cool place to hold it. `requirements.md` s.8 records this as a live bench
hazard ("typically 80-110 C surface"). There is no legend anywhere on the board
saying so - the top silk carries only the terminal legend and refdes, and the
bottom silk is completely empty (`bb-ldo_bottom.png`).

One `gr_text` on the empty bottom copper, or beside U1 on top, costs nothing
and is not an excluded feature class (`indicators` means LEDs, not legend).
Noting plainly that requirements s.8 says the hazard is "not a scope item to
fix" - true of the *hazard*; this is about labelling it. A waiver is entirely
reasonable if the owner wants the board bare.

### F8 (WARNING) C2's 3D model is the wrong case size

`CAP-SMD_L7.3-W4.3.kicad_mod` references
`lib/aiee.3dshapes/CASE-E_L7.3-W4.3-H4.1.wrl`, and the render literally has
"CASE-E" printed on the body (`bb-ldo_top.png`, centre-left). The ordered part
is `293D226X9016D2TE3`, package `CASE-D-7343-31(mm)` per `parts/parts.json` -
EIA 7343-31, 3.1 mm max height, against the model's 4.3 mm case at 4.1 mm.

Zero consequence today: height is unconstrained, there is no enclosure, and the
land pattern and courtyard are correct for 7343 either way. It is logged
because the 3D model is the artifact any later mechanical or enclosure check
will read, and it is currently 1.0 mm wrong.

---

## 4. Checked hard and cleared (with the numbers, so it is not re-checked)

**Connector orientation - the top-down render lies about this.** In
`bb-ldo_top.png` both terminals appear to have their wire openings facing the
board interior, which would be a serious defect. They do not. Three
independent artifacts agree that both wire entries face **outward**:
(a) the WRL mesh has two 4.0 x 5.5 mm rectangular openings centred exactly on
the pin x-positions on the footprint -y face and nothing comparable on +y;
(b) the footprint's two silk arrows sit on that same -y face pointing inward,
the standard wire-insertion marking; (c) `bb-ldo_left.png`, rendered for this
review, shows J1's cage openings squarely facing the camera at -X while J2
presents its back. J1's entry face is 0.86 mm inside the left board edge, J2's
0.86 mm inside the right. **Correct.** What the top view shows on the inboard
faces is a shallow moulded recess, not a hole.

**Terminal legend, after assembly.** The P4 schematic review's ERROR
(`connector-polarity-unmarked`) and WARNING (`connector-input-output-ambiguous`)
are both closed by the P6 silk, and closed properly: `GND` at y=37.37 and
`+5V` at y=42.45 are aligned pin-for-pin with J1.2 and J1.1; `+3V3` at 23.37
and `GND` at 28.45 with J2.1 and J2.2; `IN` and `OUT` at 1.6 mm sit on each
connector's centreline. All seven texts sit 2.9-3.1 mm inboard of the
connector bodies, i.e. **outside them - they survive the connector being
fitted**, visible in `bb-ldo_top.png`. Sizes 1.2/1.6 mm at 0.2 mm stroke,
comfortably over the 0.15 mm DRU floor and JLC's legibility limit. One
residual, judged and not escalated: read from the wire-insertion side the
labels are behind a ~10 mm tall block, so they are legible from above rather
than from the front, and there is no room outboard to move them (0.86 mm to the
edge).

**Capacitor polarity, after assembly.** C2's added `+` at (24.800, 29.400) is
directly over pad 1 at x=24.788 - the anode, on +3V3 - 0.52 mm clear of the
body silk and outside the courtyard, so it is visible with the part fitted
(`bb-ldo_top.png`, and the zoomed body in the centre crop shows the model's
own light anode stripe on that same right-hand end, agreeing with the mark).
C2's native marks are indeed useless: the band at local x=+2.20 is under the
7.3 x 4.3 body and the pin-1 dot is a 0.03 mm radius circle. C1 needs no added
mark - its footprint's own `+` glyph lands at (29.500, 38.810), outside its
courtyard on the anode side, and its model stripe agrees. **Both correct and
both legible.**

**Hand-solder access.** J1 and J2 are the only hand-soldered parts and they
solder from the bottom, where B.Cu carries nothing but the GND plane and three
tented vias - no SMT parts, no obstructions (`bb-ldo_bottom.png`). C1 and C2
are on the opposite face, 8.3 mm and further from the nearest THT pin; **an
iron at J1 or J2 cannot reach them.** The only hand-solder problem on this
board is F3.

**Screwdriver and part-height access.** The terminals are the tallest parts by
far and their screws face straight up with nothing over them; nearest neighbour
to J1 is C2 at 0.500 mm of courtyard gap, which is body-to-body clearance, not
an access path. No tall part shadows either connector (`bb-ldo_iso.png`).

**The hot part's neighbours.** Worked the gradient rather than assuming it:
theta_JA ~62 C/W decomposes as roughly 15 (junction-tab) + 30 (spreading in
35 um copper, ln(20/1.5)/(2*pi*k*t)) + 15 (board to air over 2642 mm2 at
h_eff ~25 W/m2K), which reproduces the 60-65 C/W estimate. That puts the tab
copper near 95 C and, at C1's 8.24 mm and C2's 9.18 mm from the tab, the
copper at **74-78 C** - under the 85 C tantalum derating knee, and both parts
run at 21-31 % of their 16 V rating, so the derated limit (about 10.7 V above
85 C) is never approached. **Not a finding.**

**C2's ESR over temperature.** The open P4 item (`cout-esr-floor-unguaranteed`)
gets slightly better at the operating point, not worse: solid MnO2 tantalum ESR
*falls* with temperature (roughly 0.85x at 125 C), so 0.8 ohm at 25 C is about
0.68-0.72 ohm at C2's ~75 C - still 2.3x above the 0.3 ohm floor the record
carries. The one thing that follows for the recorded bring-up test: run the
ring-count measurement at **thermal steady state at full load**, not cold, so
it lands on the minimum-ESR corner rather than the maximum-ESR one.

**Copper eaten by routing.** The +5V corridor (0.386 mm track, 0.127 mm each
side) runs along the bottom edge and takes about 7.6 mm2 of the 42.64 mm2 lost
inside the reach circle. It cannot be moved out - it has to reach U1.3, which
is inside. The pour stays one island around it. Nothing else carves the field.

**IR drop against dropout.** `check_irdrop`: +5V path resistance 23.5 mohm,
worst drop 12.1 mV at U1, grid converged (Richardson delta 0.037). At the
4.75 V low-line corner that leaves 1.4375 V of headroom against a 1.3 V max
dropout spec - the board's own copper spends about 8 % of the dropout margin.
Acceptable, and already inside the P2 analysis.

**Cross-artifact.** Every `requirements.md` s.2 interface is on the board
(J-in +5V/GND, J-out +3V3/GND, nothing else). Every `architecture/blocks.md`
block is present: B1=J1, B2=U1+C1+C2+the pour, B3=J2. R1's absence is a
recorded decision, not drift (fixed-variant minimum load, verified record).
The pour delivers 1199 mm2 against the architecture's ">= 1000 mm2 contiguous
with the tab". Stackup matches: 2 layers, 0.035 mm copper, 1.6 mm, HASL,
`JLC2313_1.6`. No mounting holes stated, none present (answer 9). Board size
is the earned 50.000 x 26.420 mm. The only drift found is F4 (declared vs built
clearance) and F8 (3D model case size).

**Fiducials.** Not required - JLC economy assembly panelises and carries
fiducials on its own rails, and there are four SMT parts. Not reported.

---

## 5. Waivers recommended

- **Waiver 1 (`thermal_area`): uphold**, with the two corrections in section 1
  folded into the record (the "agree within 1 C/W" wording, and bring-up tab
  temperature made an explicit acceptance condition rather than a suggestion).
- **Waiver 2 (`insufficient_transition_vias`): uphold** for the ampacity
  question it actually answers. It does not cover F2, and F2 should not be
  closed by pointing at it.
- **F6 (aspect ratio): recommend waiving** for this build - real but small
  (~1.4 C/W), and the fix is a full re-placement.
- **F7 (hot-surface legend): waivable** if the owner wants the board bare;
  requirements s.8 already rules the hazard itself out of scope.
- F1, F2, F3, F4, F5, F8: recommend fixing. F1+F2 are the same three vias and
  should be one work order; F3 is a one-pad property; F4 is a `rules_gen` fix
  plus a re-pour; F5 is a record, not a board change.

## 6. Open - what I could not settle from the board and renders

- **Absolute theta_JA.** Everything above is model and vendor table. The
  delivered board could be 55 C/W or 70 C/W and no artifact in this workspace
  can tell which. Only a thermocouple on the tab at 1.00 W in still air
  settles it, and the whole 10-15 C margin lives inside that uncertainty.
- **Whether the DRU really outranks the netclass** (F4's mechanism). The
  0.127 mm gap is measured and certain; the attribution to
  `aiee_clearance_floor` is inference from the rule file. A one-line
  experiment (add a conditioned per-net clearance rule, re-fill, re-measure)
  proves it.
- **The WJ500V's true body height.** The 3D model is 14.0 mm tall including
  the screw heads, which is taller than typical for a 5.08 mm block. Height is
  unconstrained here so it changes nothing, but I could not confirm it against
  a vendor drawing (no web access) and it is the same library that got C2's
  case size wrong.
- **Solder-joint outcome of F1.** Whether those three via-in-pad joints
  actually void is a process question. If the fix is declined, it can only be
  settled by X-ray or by a cross-section on the first article.
