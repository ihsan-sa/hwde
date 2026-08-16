# P8 board review - bb-buck (adversarial, fresh context)

2 errors / 11 warnings / 3 waivers recommended. Machine checks were green when I
started; everything below is what they cannot see, plus a verdict on every warning
they did emit and an audit of the three resolutions taken this phase.

Renders I generated and reference below (all in `reports/renders/`):
`bb-buck_top.png`, `bb-buck_bottom.png`, `bb-buck_iso.png`, and two elevation views
I added specifically to settle the terminal question:
`bb-buck_edge-left.png` (camera on the LEFT board edge) and
`bb-buck_edge-bottom.png` (camera on the BOTTOM board edge).

Coordinates are board-global mm (the same frame the check reports use); board-local
mm are given in brackets where it helps. Board origin offset is (26.07, 34.48).

---

## ERRORS

### 1. Neither screw terminal carries any polarity or function silk (silk)

`J1` (31.670, 53.380) and `J2` (48.770, 53.880).

Every one of the 20 F.SilkS text items on this board is a refdes. There is no `+`,
no `-`, no `VIN`, no `5V`, no `OUT` anywhere on F.SilkS or B.SilkS, and there are
zero board-level text objects. Look at `bb-buck_top.png`: the only characters on the
board are reference designators.

The intent *was* captured - J1 and J2 each carry a `Note` property reading
"DC INPUT 18-30V, LEFT edge, wire opening off-board" / "DC OUTPUT 5V 2A, BOTTOM
edge, wire opening off-board" - but both are `hide=yes` on F.SilkS, so they never
plot and never reach the fab.

The only polarity indication that exists is each footprint's 0.3 mm pin-1 dot, and
both are placed at the exact corner of the connector body outline: J1's at
(26.370, 48.300) [0.30, 13.82], J2's at (43.690, 59.180) [17.62, 24.70]. Both are
under the plastic body after assembly. So the assembled board has no polarity mark
at all - this is the "polarity marks visible AFTER assembly" failure in its purest
form.

J1 and J2 are the *same part*: KF128-5.08-2P, LCSC C474952, same size, same colour,
same screw orientation. Nothing on the assembled board distinguishes the 24 V input
from the 5 V output, or + from - on either.

This is not mode-excluded. requirements.md s2 requires "+ / -" on J1 and that J2 be
"silk-labelled distinctly (VIN vs 5V OUT) so the two cannot be confused at the
bench". s8 states outright that "the board has no reverse-polarity protection by
mode, so the silk marking is the only defense against a swapped supply", and the
constraints.json `placement.edges` note for J2 repeats it: "distinct silk (+/- vs
5V OUT) is the only defence against a swap." The mode removed the *protection*; it
explicitly did not remove the *marking* - the marking is what the mode's own
reasoning leans on.

Consequences, both real at the bench: reversed supply leads destroy U1 (accepted in
s8 only because silk was assumed present); and landing the bench supply on J2 puts
24-30 V across a 25 V-rated output bank while back-feeding through U1's low-side
body diode.

Fix: four short silk strings - `+`/`-` beside J1's two pins and `VIN` on its body,
`+`/`-` beside J2's two pins and `5V OUT` on its body - placed so they sit *outside*
the 10.16 x 10.5 mm connector body outlines and remain readable after assembly.
There is clear board space above J1 (y_local 12-13.8) and left of J2.

### 2. Only 9 thermal vias under U1's exposed pad; the datasheet minimum is 12 (router)

U1 EP at (38.970, 41.480) [12.9, 7.0], pad 2.5 x 3.5 mm.

The in-pad array is 3 x 3 at 0.85 mm pitch, 0.30 mm drill / 0.60 mm pad, centred on
the EP. The LMR33630 datasheet Sec 10.1.1 is imperative and specific: *"Use a
minimum 4 x 3 array of 10-mil thermal vias to connect the PAD to the system ground
plane heat sink. The vias must be evenly distributed under the PAD."* That is 12
vias **under the pad**, and the board has 9 - 75 % of the stated floor.

The pipeline's own rule (`constraints.json _review_enforced (1)`, ">= 16 vias within
4.6 mm") *is* met: I count 18 GND vias within 4.6 mm of U1's centre. But that rule
counts vias out in the surrounding F.Cu island, which reach B.Cu through a much
longer lateral path than a via inside the pad. The datasheet's rule is about the
pad, and it is the one that governs the joint's own heat path.

The 0.30 mm barrels partly recover the count: barrel-wall conductance scales roughly
as n x d, so 9 x 0.30 = 2.70 against the datasheet's 12 x 0.254 = 3.05 - about 88 %
of the minimum. Using the design's own 192 K/W-per-via figure, 9 vs 12 in parallel is
21.3 vs 16.0 K/W, ~5 K of extra junction rise at 0.92 W. That does not fail the part
(Tj lands near 123 C against 150 C at 50 C ambient), but it eats most of the 2.06 C
that `check_thermal` reports as margin - and `check_thermal` does not model the array
at all, which is exactly why the constraints file made this review-enforced.

This is cheap to fix and it fits: a 3 x 4 array at the existing 0.85 mm pitch spans
1.70 x 2.55 mm inside a 2.50 x 3.50 mm pad, with 0.3 mm to every pad edge. Add one
row (3 vias). See also warning 4 - adding vias makes the stencil question sharper,
so fix the two together.

---

## WARNINGS

### 3. TP1 sits on a dedicated switch-node spur, and the spur drags /SW into the FB/VCC corner (placement)

TP1 pad at (43.970, 44.380) [17.9, 9.9]; the stub runs from inside L1's pad at
(46.100, 43.000) to TP1, 2.54 mm of 1.52 mm-wide track.

`constraints.json placement.groups[probe]` is explicit: "TP1 must sit INSIDE the
existing /SW copper, not on a spur, so it adds as little area as possible to the
noisiest node." It does not. The existing /SW copper ends at y_local 9.45 (L1.1's pad
edge); TP1 hangs 1.2 mm below it on a dedicated stub.

The area cost is modest - TP1's pad plus its stub is 4.74 mm2, 18 % of the 26.36 mm2
node - and both /SW ceilings still hold (26.36 mm2 against 40; 7.60 mm longest extent
against 8). The real cost is spacing. Measured with and without the stub:

| pair | /SW without the spur | /SW as built | factor |
|---|---|---|---|
| /SW -> /FB | 2.930 mm | **1.038 mm** | 2.8x closer |
| /SW -> /VCC | 1.660 mm | **0.420 mm** | 4.0x closer |
| /SW -> C7 pads (VCC bypass) | 3.848 mm | **0.962 mm** | 4.0x closer |
| /SW -> R1 pads (FB top) | 4.566 mm | **1.948 mm** | 2.3x closer |

So a feature added purely for measurement convenience quadrupled the switch node's
proximity to the gate-drive rail and nearly tripled it to the feedback node - the two
nets `constraints.json` names as needing distance from /SW. The absolute coupling is
small (tens of femtofarads; order 20 mV of per-cycle glitch on a 1 V reference through
the FB node's own capacitance) and nothing here is illegal, but it is entirely
avoidable: the U1.8 -> L1.1 corridor is 4.7 x 5.4 mm of existing /SW copper and a
1.5 mm pad fits inside it at roughly (44.97, 42.08) [18.9, 7.6], with TP2 following
~2.5 mm below. Deleting the stub also removes 2.5 mm of open-ended 1.52 mm track from
the switch node.

### 4. U1's exposed pad is a single 100 % paste aperture with 9 open via barrels inside it (library)

`aiee:ESOP-8_L4.9-W3.9-P1.27-LS6.0-TL-EP` pad 9: `(layers "F.Cu" "F.Mask" "F.Paste")`,
2.5 x 3.5 mm, no `solder_paste_margin` anywhere on the board.

Two uncontrolled quantities that do not reliably cancel:

- 8.75 mm2 of solid stencil aperture is ~1.05 mm3 of wet paste at a 0.12 mm stencil,
  roughly 0.5 mm3 of metal. IPC-7093 and TI's PowerPAD note (SLMA002) both call for a
  windowed/segmented aperture at ~50-80 % coverage on thermal pads this size,
  precisely to stop the package floating on the EP and tilting the 0.6 mm gull-wing
  joints.
- The pad's mask aperture is 2.5 x 3.5 mm, which opens the mask over all 9 in-pad
  vias regardless of the board's `(tenting (front yes) (back yes))` setting. Nine
  0.3 mm x 1.6 mm barrels hold ~1.0 mm3 - about twice the available solder metal.
  Bottom-side tenting limits how much escapes, and TI's own guidance accepts
  unplugged holes at or below ~0.33 mm, so this is a risk rather than a certainty -
  but it is unmanaged, and the EP is the entire heat path on 2 layers.

Fix: give pad 9 a windowed paste pattern (4-5 apertures, ~70 % coverage) positioned
between the via locations. Do this in the same pass as error 2.

### 5. L1 sits 0.50 mm from the top board edge (placement)

L1 centre (52.670, 41.230) [26.6, 6.75]. Body 12.3 x 12.3 x 8.0 mm
(SMDRI127-150MT / C40000 - note the footprint is *named* RLF12545T, which is a
different part; the pads match the fitted part, so this is a library-naming issue,
not a land-pattern error). Silk/body outline reaches y_local 0.55, courtyard 0.60,
and the true 12.5 mm outline reaches 0.50 mm from the edge. See the top-right of
`bb-buck_top.png` - the inductor is visually flush with the top edge.

JLCPCB's assembly guideline is >= 1 mm component-to-board-edge, and the depanel
question matters more than the placement question: a 12.3 mm, 8 mm-tall part whose
solder joints sit 0.5 mm from a V-scored edge is exposed to snap stress at
depanelisation. Nothing else on the board is under 1 mm except the two terminals
(intentionally, at 0.30 mm, openings at the edge) and C9 at 1.15 mm; C2/C3 are at
1.05 mm.

Fix: either move L1 >= 1 mm off the top edge (there is 12.1 mm of clear board below
it) or specify routed/tab depanelisation rather than V-score in the P9 fab notes.

### 6. Both GND screw-terminal pins are flooded solid into full-board pours on both layers (plane)

J1.2 at (31.670, 55.920), J2.2 at (51.310, 53.880). Both zones carry
`(connect_pads yes (clearance 0.5))` - KiCad's *solid* pad connection. The
`thermal_gap`/`thermal_bridge_width` values present in both zones are inert while
`connect_pads` is `yes`.

Each of those pins is a 1.6 mm drill in a 2.4 mm pad, solidly tied to a 595.5 mm2
1 oz F.Cu pour on top and a 783.3 mm2 pour on the bottom - four solid plane
connections to heat. requirements.md s7 explicitly allows the fallback path
"hand-soldered after SMT", and that is where this bites: a normal iron will not get
a plane-connected 1.6 mm barrel to reflow temperature reliably, and a cold joint on
J2.2 is the 2 A return path. JLC's selective/wave process with preheat copes better,
but the assembly route is not yet decided.

Fix: switch both GND zones to thermal-relief pad connection for through-hole pads
(`connect_pads thru_hole_only` with the existing 0.5 mm gap / 0.5 mm spoke), or add
per-pad thermal relief on J1.2 and J2.2 only. The SMD pads should stay solid.

### 7. The probe pair is mislabelled on the assembled board (silk)

This is my triage of the four `check_silk` refdes-ambiguity warnings. All four are
geometrically real - I reproduced each - and three are cosmetic. One is not:

- **R1 label at (45.698, 46.910), 0.10 mm from TP2** - escalate. TP2 is the scope
  ground pad of the one measurement feature the owner bought at A4, and TP2's *own*
  label sits at (45.470, 49.555) which is inside J2's courtyard, so it disappears
  under the terminal body at assembly. The result is that the assembled board labels
  the scope-ground pad "R1", while R1's actual body is 4.6 mm away. On a board whose
  stated purpose is to be measured, that is a usability defect, not a cosmetic one.
- C3 label at (47.583, 36.780), 0.68 mm from L1 - real, and it lands inside L1's
  courtyard so it also vanishes at assembly. Cosmetic; fix in the same pass.
- C7 label at (45.695, 45.030), 0.03 mm from L1's courtyard edge - real, cosmetic.
- J2 label at (55.525, 52.330), 0.53 mm from C4 - real, cosmetic.

No waiver recommended on any of the four: `place_edit.py move_text` is the cheapest
fix on this list, and it is the same pass that has to add the silk from error 1.

Separately, I confirmed the owner-accepted count of hidden labels is exactly 7 and
found nothing worse hiding under a body: TP2, C5, C8 and C9 under J1; C3 under L1;
L1 under J2; J1 under its own body. The two that carry consequence are TP2 (above)
and L1, which loses its identity entirely after assembly.

### 8. Three of the four output capacitors are 20-26 mm from the inductor, behind a 1.00 mm pour neck (placement)

C4 (57.270, 49.380) is the only output cap near the converter, 8.2 mm from L1.2.
C5/C8/C9 sit at x_local 14.2, y_local 15.6 / 19.1 / 22.6 - 20 to 26 mm from L1.2 -
and reach +5V only through the priority-1 F.Cu zone bridge, whose narrowest section I
measure at **1.002 mm**, at (40.970, 48.750) [14.9, 14.3].

`constraints.json placement.groups[output]` anchors all four on L1. As built the bank
is split 1 + 3. At 400 kHz the ~20 nH of the run to the far three is ~50 mOhm against
their own ~20 mOhm impedance, so roughly only C4 filters the fundamental ripple. The
arithmetic still passes: ripple goes from ~8.3 mV (26 uF effective) to ~14.5 mV
(C4 alone, ~15 uF after bias derating) against A3's 50 mV budget, and loop stability
is untouched because at a ~40 kHz crossover 20 mm of trace is nothing, so all four
caps count for Table 9-2's C_OUT requirement. The stated load is resistive, so there
is no transient case to worry about either.

Reporting it because it is a silent deviation from the architecture with a 1.7x
ripple cost, not because the board fails. If it is accepted, the +5V check_pdn waiver
text should be amended (see waivers below).

### 9. The +5V pour neck is never measured by check_current (review)

`check_current.py` reaches its `pour_neck` evaluation only for entries it treats as
plane-carrying; on this board `GND` (with `plane_fed: true`) gets its pours eroded and
measured, and `+5V` gets `min_track_mm_by_layer: {"F.Cu": 1.52}` and nothing else. The
+5V zone is 18.26 mm2 of real current-carrying pour with a 1.002 mm neck and the
checker never looked at it.

On the merits the neck is fine, and I want to be clear it passes rather than
squeaking by: the 2 A DC load path is L1.2 -> 1.8 mm track -> J2.1 and never crosses
the bridge. What crosses is the ripple share into three caps plus the divider's
39 uA - at most ~0.15-0.2 A against IPC-2152's ~1.6 A capability for 1.00 mm on 1 oz
outer at dT 10, roughly 8x margin.

A second instance of the same blind spot, also benign: `pour_neck` uses *vias* as its
attachment points, so the hot loop's F.Cu ground bridge between C1.2 and U1.1 - which
has no vias by design, correctly - is never tested. I measured it at 0.935-1.230 mm
continuous, against the 0.56 mm that 1.1 A needs. Fine, but untested.

Recorded so the hole is visible, not because either measurement fails.

### 10. The GND F.Cu override is anchored to a checker artifact, not to the copper (review)

Audit of resolution 1. **The 0.6 A figure is honest - conservatively so.** I
reproduced every number in the WO-3 note independently: B.Cu min neck 5.937 mm
against the 1.520 mm requirement (3.91x, one unbroken 783.34 mm2 fill, zero B.Cu
tracks); F.Cu min neck 0.322 mm; each of C2.2, C3.2, C4.2, C5.2, C8.2, C9.2, C10.2
carries 3 vias within 1.5 mm; U1's EP carries 9; both GND terminals are THT so the
2.6 A return enters B.Cu through a 1.6 mm barrel at J2.2 without touching an F.Cu
neck. My own estimate of what actually crosses the 0.32 mm sliver is 30-50 mA - the
sliver is ~20 mOhm against a ~0.7 mOhm via-B.Cu-via shunt, so it takes about 3 % of
any current that wants to pass - i.e. 0.6 A is 12-20x conservative. The engineering
is sound.

Two corrections to the record, and one durable risk:

- The note says the F.Cu pour "splits into 5 mutually-isolated LEAF-TAP via groups".
  It does not: the F.Cu GND fill is a **single connected region of 595.5 mm2** (I
  rasterised it at 0.02 mm and ran connected-component labelling - one component).
  The leaf-tap argument is about current *share*, and in that form it is correct; the
  word "isolated" is not.
- `pour_neck` reports its position as `parts[0].representative_point()` of the eroded
  fill. The override anchor (30.3575, 46.9464) sits in copper that is **7.56 mm wide**
  and about 9 mm from either true pinch at (40.550, 35.141) / (35.150, 35.141) - which
  are slivers along the *top* board edge, squeezed between the 0.5 mm pour inset and
  C2.1/C3.1's +VIN pads. So the override is placed on the checker's reporting artifact
  rather than on the defect.
- The margin is 0.36 mm. I confirmed the note's own measurements: r <= 1.8 mm captures
  0 vias, and the nearest via-cluster centroid (C10.2's, at (32.05, 46.18)) is
  1.858 mm away, so the default r = 2.0 would manufacture a new error. Any repour that
  moves the representative point by more than ~0.36 mm either breaks the fix or
  silently widens it. And because every future F.Cu GND neck on this net would be
  reported at approximately the same point, this single override will suppress them
  too, at any severity, without saying so.

Recommendation: keep the override (the physics is right), but re-anchor it on the
real pinches at (40.550, 35.141) and (35.150, 35.141) with a radius that covers them
and nothing else, and record that `pour_neck`'s reported position is not the neck.

### 11. /SW-to-GND clearance is 0.1275 mm, and the "no pair exceeds 30 V" premise is not true for /SW (review)

Minimum measured at (45.545, 40.757) [19.475, 6.277], between the /SW track into L1
and the F.Cu GND pour. +VIN-to-GND has the same 0.1275 mm minimum at (34.052, 41.746).
Both are the board's DRC floor, so this is a global pour-clearance setting rather than
a routing slip.

The reasoning in `constraints.json _absent_keys` - "no net PAIR on this board exceeds
30 V (check_creepage's derived check engages only ABOVE 30 V)" - holds for every DC
pair, but /SW is not a DC node. It swings 0 to VIN each cycle and overshoots on the
turn-on edge; on a 2-layer board with a 2.3 mm2 loop, 1.2-1.5x VIN is the normal range,
i.e. 36-45 V at the 30 V corner. That puts /SW-GND in IPC-2221's 31-100 V band, where
external conductors under permanent polymer coating (B2) want 0.13 mm. The board has
0.1275 mm.

I am not claiming this board fails - 0.127 mm of masked FR-4 will not break down at
45 V, and this is standard JLC 2-layer practice. I am flagging that the stated basis
for `check_creepage` being a clean no-op has a hole in it, and requirements.md s8
explicitly contemplates the owner lifting the A1 ceiling later, at which point that
hole matters. Recording the switch-node overshoot as a known exception is the fix, not
copper.

### 12. The GND void under L1 was never cut, and cutting it would break the 2-layer story (plane)

`constraints.json _review_enforced (4)` requires "a GND void under the body" for L1.
Measured over L1's 12.3 x 12.3 mm footprint: F.Cu GND covers 68.2 %, and over the
core between the two pads it covers **99.5 %**; B.Cu GND covers 100 % of both.

Two things follow. First, the requirement was silently dropped - nothing in the
pipeline enforces it and no rule area exists anywhere on the board. Second, it should
probably stay dropped: the *only* mitigation this design offers for being 2 layers
where the datasheet asks for 4 is an unbroken B.Cu pour under the hot loop, /SW and
L1, and cutting a void under L1 on B.Cu would directly contradict it. The fitted part
is a shielded/composite drum (SMDRI127-150MT), so copper beneath it is normal
practice and the eddy-loss argument is weak.

Recommendation: waive on B.Cu permanently and amend the constraint to say so;
optionally cut the F.Cu core void only, which costs nothing.

Related, same clause: L1's /SW-side copper is 26.36 mm2 against the ">= 40 mm2 of pad
copper per terminal" in the same rule (the +5V side is 83.4 mm2 and passes). That rule
cannot be met on the /SW side without breaching the "/SW <= 40 mm2" ceiling in clause
(2) of the same file. Since L1 dissipates 0.27 W - below the 0.5 W threshold the
architecture itself uses to decide a part needs a thermal entry - the EMI ceiling
should win and clause (4) should be scoped to the +5V terminal only. No board change.

### 13. The declared 6.5 mm M3 keepouts do not exist (plane)

`_review_enforced (3)` calls for hand-added KiCad rule areas giving a 6.5 mm
mask/copper keepout at each M3 hole, because `planes_gen` cannot void. The board has
**zero** keepout zones; both GND pours run to 0.5 mm from the board edge and up to
both NPTH barrels.

I checked the consequence rather than just the omission, and it is nil: within a
3.25 mm washer radius of H1 (29.570, 37.980) and H2 (57.570, 55.980) there is no
non-GND copper on either layer - no tracks, no pads, and the +5V zone is nowhere near.
A metal M3 screw and washer therefore short top GND to bottom GND, which is harmless
and arguably desirable on a bench article.

Recommendation: waive and close the constraint as satisfied-by-inspection rather than
adding rule areas. Re-check if any future revision routes non-GND copper into a
corner.

---

## Verdicts on the three resolutions taken this phase

**1. The GND `overrides` region at 0.6 A / r 1.5 mm - accept the number, re-anchor the
region.** Full audit in warning 10. Every measurement in the note reproduces exactly;
my independent estimate of the current in the neck is 30-50 mA, so 0.6 A is
conservative by more than an order of magnitude. The radius is safe today (nearest via
cluster 1.858 mm away). What I object to is that the region is keyed to
`parts[0].representative_point()` of an eroded polygon, sits in 7.56 mm-wide copper
9 mm from the actual pinch, and therefore has an unstated blast radius over future
findings on the same net.

**2. Fixing `check_silk.py` rather than waiving TP1/TP2 - correct, and I verified the
geometry.** Both TestPoint footprints carry `fp_circle` r 0.950 mm, stroke 0.120,
`(fill no)` - a ring occupying 0.890 to 1.010 mm - against a 1.50 mm circular pad,
i.e. radius 0.750 mm. Real clearance pad-edge to silk-inner-edge is **0.140 mm**. The
old checker built the circle as a filled disc and so reported 100 % pad coverage; that
was a genuine false positive and fixing the checker was the right call. One residual:
0.140 mm is inside typical silkscreen registration tolerance (+/-0.10 to 0.15 mm), so
the ring may land on the pad in production. Both are bare probe pads and JLC clips
silk over exposed copper anyway, so I am recording this rather than filing it.

**3. The two `check_pdn` waivers - both hold; amend the +5V reasoning.**
- *GND*: sound without qualification. GND is a return net and cannot be decoupled to
  itself; the finding exists only because GND is deliberately declared as a power
  entry to keep pour necks at error severity, which is the right trade. Compensating
  controls verified by me: drc_routed 0/0, no GND error in check_current, and a B.Cu
  trunk measuring 5.937 mm minimum neck against 1.520 mm required on one unbroken
  783.34 mm2 fill.
- *+5V*: the category argument is correct - an output bank hangs on no IC power pin,
  so `check_pdn` is looking for a structure that rightly does not exist. But the stated
  compensating control, "the 4 x 22 uF bank is verified present in the netlist and on
  the board", reads stronger than the layout supports: one of the four is near the
  converter and three are 20-26 mm away behind a 1.00 mm pour neck (warning 8), and
  the P4 SPICE bench gates the DC setpoint, not the bank's HF position. Keep the
  waiver, amend the wording so the record is accurate.

## Verdicts on the remaining machine warnings

- **20 x `insufficient_transition_vias` on GND - waive, all 20.** Every one is an
  isolated single stitching via judged against the whole 2.6 A budget (needs 7). The
  2.6 A return does not pass through any of them: it enters B.Cu at J2.2's 1.6 mm THT
  barrel, and each capacitor's ground already has its own 3-via drop. This is exactly
  the case `plane_fed`'s advisory downgrade exists for. One note rather than a finding:
  the advisory at (43.970, 46.900) is TP2, the scope ground, on a single via - fine for
  a probe return, but a second via there is free.
- **1 x `check_return_path` `corridor_void` on /SW - waive.** 0.46 mm2 of deficit at
  (43.259, 34.891), with `crossing_len_mm: 0.00`. The polygon sits at y 34.84-34.98,
  i.e. inside the pour's own 0.5 mm edge inset at the top board edge. It is where
  copper stops on a 2-layer board, not a split, and no trace crosses it. The /SW
  corridor is otherwise 100 % covered - see below.
- **4 x `check_silk` refdes ambiguity - do not waive, fix.** Triage in warning 7.

## What I checked and found sound

Worth recording, because several of these are the load-bearing claims:

- **Both terminal openings face off-board, on different edges.** This was wrong once
  already, so I settled it two ways. Geometrically: J1 is at rot -90, which maps the
  footprint's wire-entry arrows (local +y) to global -x, putting the opening face
  0.30 mm from the left board edge; J2 is at rot 0, putting its opening face 0.30 mm
  from the bottom edge. Visually: `bb-buck_edge-left.png` shows J1's two square wire
  openings face-on from the left edge, and `bb-buck_edge-bottom.png` shows J2's
  face-on from the bottom edge. Both correct, and on different edges as
  requirements.md s5 demands.
- **The 2-layer mitigation claim is true.** The B.Cu GND fill is a single unbroken
  783.34 mm2 region with zero interior holes and zero disjoint pieces, and it covers
  100.00 % of the hot loop, U1's body and EP, the /SW corridor (with and without the
  TP1 spur), L1's full footprint, the input caps and the output caps. There are no
  B.Cu tracks anywhere. `bb-buck_bottom.png` shows exactly that - bare pour, four THT
  pins, two mounting holes, the EP via array, nothing else.
- **The hot loop is excellent.** C1's +VIN pad is 1.651 mm centre-to-centre from
  U1.2 (0.550 mm pad edge to pad edge) and its GND pad is 1.651 mm from U1.1 PGND, on
  a 1.30 mm-wide direct track and an unbroken 0.935-1.230 mm F.Cu ground bridge
  respectively. The pads are uncrossed - C1.1 (+VIN, y 6.425) faces U1.2 (+VIN,
  y 6.360) and C1.2 (GND, y 5.025) faces U1.1 (PGND, y 5.090). Enclosed loop
  1.65 x 1.40 mm = 2.31 mm2, matching the design intent. C1.2 correctly has *no* vias
  within 2.5 mm - the loop stays on F.Cu with B.Cu as its image plane, which is right.
- **/SW containment holds.** 26.36 mm2 against the 40 mm2 ceiling, longest extent
  7.60 mm against 8 mm, F.Cu only, zero layer transitions, 4.05 mm from the nearest
  board edge and 8.7 mm from J2's nearest pad.
- **U1's pinout is wired correctly**, including pin 3 EN tied to +VIN (the datasheet
  states EN "can be connected directly to VIN" with an abs-max of VIN + 0.3 V) and
  pin 4 PG left open, which the datasheet permits.
- **W2 is satisfied**: R2's ground return is a dedicated 1.52 mm track from
  (37.270, 46.600) to (38.900, 43.100), landing inside the exposed pad, i.e. on AGND.
  The board-wide F.Cu GND pour makes the Kelvin intent partly notional, but
  check_irdrop puts the worst GND drop at 0.609 mV, which is 0.06 % of the 1 V
  reference - negligible.
- **The A3 amendment is on the board**: R1 = 102k, R2 = 25.5k, ratio exactly 4.000,
  5.000 V nominal.
- **The 5 V feedback divider is well separated**: /FB to /SW 1.038 mm even with the
  TP1 spur, /FB guarded by GND pour on both sides, R1/R2 4.6 mm clear of L1's
  courtyard.
- **No courtyard overlaps anywhere**; every interface requirements.md names is
  present (J1, J2, TP1 + TP2 and nothing else); two M3 holes diagonally opposite,
  which requirements.md s5 explicitly sanctions in place of four.
- **Fiducials**: not required. Finest pitch on the board is 1.27 mm (SOIC-8) and JLC
  assembles from panel fiducials at that pitch. Not a finding.
- **P9 has not run** - `boards/bb-buck/fab/` is empty - so the depanel note in
  warning 5 and the stencil change in warning 4 both still land in front of the fab
  package rather than behind it.

## Documentation drift (no board change)

`architecture/blocks.md` is stale against the built board in four places: it lists
H1..H4 (the board has H1/H2, correctly, per requirements s5 and the constraints
keepout note), C1 as 100 nF (built as 220 nF, which is what the LMR33630 layout
section asks for), the output bank as 2 x 22 uF 1206 (built as 4 x 22 uF 1210 per the
P4 fix), and omits C7, C8, C9 and C10 entirely. All four changes are recorded in
`constraints.json` and were owner-approved; only blocks.md was not refreshed.

## Waivers recommended

1. `check_current` `insufficient_transition_vias` x20 on GND - isolated stitching vias
   on a plane-fed net; the 2.6 A return enters B.Cu at J2.2's THT barrel and every
   capacitor ground already has 3 vias.
2. `check_return_path` `corridor_void` on /SW - 0.46 mm2 at the pour's own 0.5 mm edge
   inset, 0.00 mm of trace crossing.
3. Finding 13 (M3 keepouts absent) - verified consequence-free; close the constraint
   as satisfied-by-inspection.

Findings 8 and 12 are also reasonable waiver candidates if the owner accepts the
arithmetic; both are recorded as warnings so the decision is explicit rather than
silent.
