# DECISIONS.md - sbuck-5v3a

Synchronous buck converter, 7-18 V DC in (12 V nom) -> 5.0 V +/-2% at 3 A.
50 x 40 mm, 4 layer, JLCPCB. Every non-obvious choice, one line of reasoning each.

The brief delegated every remaining decision ("Make every remaining decision
yourself. Do not ask clarifying questions."), so all 33 requirements questions and
all five human checkpoints were answered as DELEGATE. Nothing here was approved by
a human; the record exists so each call can be audited and overturned.

**68 decisions recorded.** Several record a LIMIT OF KNOWLEDGE rather than a choice -
those are the ones worth reading first, and they are marked in place.

---

## P0 Intake  (5)

**Unattended run: orchestrator answered all 33 requirements open questions as delegate (requirements-answers.md)**

> Brief DECISION POLICY forbids clarifying questions; no mains/battery/motor/>30V/RF flags apply, so no safety unknown is being guessed

**4-layer stackup, 1oz outer / 0.5oz inner**

> Brief demands an uncut GND plane directly under the switching components plus 2.05 W natural-convection cooling on <=50x40mm; 2L cannot give both the image plane and the bottom thermal copper

**Add a 4A slow-blow input fuse (DCR <=30 mOhm) beyond the brief's protection list**

> IC OCP+hiccup cannot protect against a shorted high-side switch; upstream supply current limit is unstated, so the fuse is what bounds fault energy on-board

**Target switching frequency 400-700 kHz**

> Below the AM broadcast band, keeps 18V-input min-on-time and switching loss comfortable, and allows 20-40% ripple with a stocked inductor

**Spawn tier deviation: Fable 5 unavailable (out of credits); judgment roles run on Opus instead**

> Playbook forbids silent downgrade - Opus is the nearest available tier for architect/placement/reviewer roles; recorded rather than hidden

---

## P1 Research  (8)

**Input fuse: take the 5A slow-blow (Bel 0685T5000-01, 5032 pcs) over the spec-ideal 4A sibling (174 pcs)**

> Requirements Q24 binds stock >=2000 pcs and the brief says an out-of-stock part is a failed design; 5A still opens on a bolted fault and costs only 119 mW at the 2.44 A worst case

**P3 must pull screw-terminal body height, pin diameter and recommended hole size from the vendor datasheet - LCSC attributes do not carry them**

> Footprint cannot be built or DFM-checked on missing mechanical data; flagged by the protection scout as its open item

**All MLCCs must be X7R (no X5R anywhere); Cout bank moves to 22uF/25V 1210 X7R**

> Architect computed 83-87 C board surface; X5R is rated 85 C so it is a latent failure, and the X7R part also derates less on DC bias (~12% vs ~25%)

**Add a 15V Zener + gate resistor clamp on the reverse-polarity P-FET gate**

> AO4407A survives 18V static on its +/-25V Vgs, but the architect's 25.4V hot-plug ring on the screw terminals exceeds it; the clamp is the cheap fix

**In1 and In2 both solid GND; no power net may use an inner layer**

> 0.5oz inner copper needs 3.0-4.6mm widths for these currents per IPC-2152, which is unroutable - so power stays on 1oz outer and the inners are pure return/thermal

**Feedback divider uses 0.1% resistors regardless of IC choice**

> Reference tolerance alone spans -1.2%/+1.8% across the candidates and already eats 60-95% of the +/-2% budget; FB bias current error is negligible (<=0.1%) so the divider tolerance is the only lever left

**RC snubber values come from general practice, not a vendor citation - footprint sized generously and left DNP**

> None of the three candidate vendors publishes a snubber value; the brief wants the footprint anyway, so honest sourcing is to mark it uncited rather than invent a citation

**P2 may revisit the 4.0A current-limit-minimum floor - it was a delegate tightening (Q5), not a user requirement**

> It is the single rule disqualifying LMR33630 (3.85A min, ~3.375A guaranteed Iout = 12.5% over the 3.0A load), and the AP64350 that satisfies it carries a 7-10mA UVLO penalty and external compensation

---

## P2 Architecture  (5)

**OVERRIDE of delegate answer Q14: UVLO retargeted from 6.5V/6.0V to 6.2V/5.3V**

> 0.5V hysteresis is less than this board's own 0.49V cable drop at 2.44A (motorboating), and VON=6.5V at the max threshold corner lands ~7.0V so the converter could refuse to start at its minimum rated input; also drops the UVLO divider draw from 81-181mW to 1-2mW

**Buck IC: AP64350SP-13 at 500 kHz (RT=200k)**

> Decided on MAX Rds(on) 75/45 mOhm vs LMR33630's TYPICAL 95/66; TI's own max column gives 1.65W conduction -> Tj ~112C, over the 105C limit. SY8205 rejected on preliminary datasheet with typ-only Rds

**1 oz outer copper; both vendor reference layouts (2 oz) lose**

> JLC's only 4L/1.6mm 2oz-outer lamination has a 0.4284mm L1-L2 prepreg vs 1080B's 0.2444mm - nearly doubles thermal-via resistance and pushes the image plane 75% further from the hot loop; net +0.8C, so 2oz is worse here

**Stackup JLC04161H-1080B; F.Cu + In1 + In2 + B.Cu ALL GND**

> JLC inner copper is 0.0152mm - thinner than the nominal 0.5oz the rule assumed - so inner power widths would need 3.5-5.3mm; declared explicitly because the pipeline default would otherwise pour In2 as +5V

**Single flat root sheet (refdes 1-99, #PWR 100), 33 placed parts**

> Small board; hierarchy rejected to eliminate the /<sheet>/<LABEL> net-name mismatch class the recipe warns about

---

## P3 Parts + Library  (10)

**R6 feedback top resistor 116k -> 115k (0.1%)**

> 116k is not an E96 value and has zero 0603 stock at any tolerance; 115k/22.1k is what the AP64350 datasheet's own 5V reference design specifies, and 118k was rejected for failing the high corner at 5.130V

**U1 ships with NO true pin-compatible alternate (explicit empty list)**

> Pin-by-pin comparison shows AP64350 and LMR33630 differ on 4 of 8 pins and use different compensation architectures; recording the single-source risk honestly beats listing a fake second source

**AO4407A Rds(on) budget checked at the real operating gate drive (Vgs = -Vin, clamped -15V), not at the datasheet's -4.5/-5V row**

> Gate sits at GND and source at VIN in this topology so Vgs spans -7V to -15V; at the 12V spec point Vgs=-12V gives 13 mOhm max = 26 mW, inside the 22 mOhm budget line. The -5V row (38 mOhm max) is not an operating condition on this board

**AO4407A datasheet has no land pattern - librarian uses standard JEDEC MS-012 SOIC-8, 1.27mm pitch**

> The 4-page Rev3 (2008) PDF carries no mechanical/recommended-land drawing; sourcing the footprint from the JEDEC standard is honest, inventing pad dimensions from the PDF would not be

**FB bias-current error treated as an ASSUMPTION, not a datasheet fact - P1 reference-design claimed <=0.1% but the datasheet states no value**

> Divider current is 0.8V/22.1k = 36 uA, so a typical 10-100 nA FB bias is 0.03-0.3% of it - safe, but it must be labelled an engineering assumption since the vendor never publishes the number

**Thermal via array 16 x 0.3mm at 1.0mm pitch is OUR derivation - the vendor spec is only qualitative**

> AP64350 datasheet says merely 'add as many vias as possible' with an uncounted illustrative array; the numeric array comes from the P1 architect's 1.9 K/W calculation, cross-checked against the Wurth FEA table

**Vendor thermal numbers are stated on 2oz copper; board is 1oz - deferred to P8 check_thermal on real geometry**

> theta_JC is package-internal so it barely moves, and the architect's governing model computed board-to-ambient independently; resolving this on measured copper at P8 beats re-litigating it on datasheet conditions now

**U1 exposed pad enlarged from the pulled 3.200x2.500mm to the vendor Suggested Pad Layout 3.502x2.613mm (approved hand-edit)**

> -12.6% EP area on a design whose theta_JC closes with zero margin and whose entire thermal path runs through that pad; the vendor's own suggested layout outranks the easyeda2kicad pull

**F1 library assets come from KiCad stock (Device:Fuse + 1206 fuse land), not an EasyEDA pull**

> C3163312 is the only LCSC listing for this MPN and its EasyEDA record 404s; re-sourcing would trade a datasheet-verified true slow-blow part for an unverified one, so the library gap is filled instead of the part changed

**P4 must take C4 polarity from the footprint silk +/- mark, not the symbol**

> The pulled aluminium-can symbol has generic pin names 1/2 with no polarity semantics, while the footprint carries an explicit +/- pair with pin1=+

---

## P4 Schematic  (13)

**NO series gate resistor on Q1 - my spawn instruction was wrong, the schematic agent correctly followed the architecture**

> blocks.md B1 and sheets.md s5.4 both explicitly forbid a gate RC, and the P1 architect already proved a gate RC cannot limit inrush here (the body diode is forward in the normal direction); R1=100k is the gate path and D2 clamps Vgs

**C3 refitted as the Eq.19 COMP HF pole (COMP->GND) at 10pF, NOT the Eq.20 feedforward across R6; sheets.md s3 to be amended**

> Measured both: as feedforward it pushes |T| at fsw/2 to -8..-2 dB and breaks the vendor's own <-10 dB gain-margin target; as the Eq.19 pole it costs 8 deg of PM (we hold 65-72 deg) and buys -16 dB

**Feedback divider 115k/22.1k -> 105k/20.0k**

> 105k/20.0k hits the required 5.2500 ratio exactly (Vout 5.0000 V) and moves the worst-case low corner from 4.9034 V to 4.9401 V - 3.4 mV of margin becomes 40 mV, at no cost

**P9 BOM/CPL must filter DNP by the Variant field manually - no script in the skill reads any DNP mark**

> J1, J2, R9, C16 are marked Variant=DNP (the only marking a generator can reach, ksa hard-codes (dnp no)); left unfiltered, P9 would ship four parts as populated including both hand-solder screw terminals

**DNP snubber upsized: R9 0603->1206, C16 1nF X7R->470pF C0G 1206**

> Reviewer showed C*V^2*f = 162 mW at 18V (338 mW at the 26V ring) into an 0603 rated 0.1 W - a DNP footprint that destroys itself when populated is a trap; 470pF/1206 gives 76 mW into 0.25 W

**Loop calibration claim WITHDRAWN - the x0.83 realisation factor is not evidenced**

> Reviewer read the vendor's Fig.29 and found C4=33pF IS fitted in the published Bode plot, so the author's 'PM 79-84 vs published 81.6' compared the wrong variant; design still passes at ~46-53 deg worst case vs the 45 deg floor, but the margin is smaller than P4 claimed and only a real loop measurement can close it

**Silkscreen connector labelling carried FORWARD to P6/P8 as a tracked requirement**

> It is delegate Q30's ONLY mitigation for the swapped input/output failure mode (both terminals are identical 5.08mm 2-pin), and it is unreachable from a schematic generator - so it must not die in a P4 note

**Hot-plug inrush: 26V voltage declaration KEPT, current bounded by the damped path, residual risk accepted and documented**

> The 0.05-ohm/180A row assumes an ALL-CERAMIC Cin; this board deliberately carries C4 at 80 mOhm ESR as a damping requirement, so that row is not our configuration. Keeping 26V is conservative for part ratings and costs nothing. Residual: AO4407A body-diode single-pulse capability is unpublished, so the peak cannot be closed from sourced data - and screw terminals are a wire-then-power connector, not a hot-plug one

**The clean ERC is WEAK evidence for U1 and must not be cited as pin-level proof**

> Reviewer noted nearly every U1 pin is declared 'passive' in the pulled library, so ERC cannot catch a mis-wired IC pin here; the real pin-level evidence is the datasheet-extract cross-check and the reviewer's independent netlist read

**Load-step prediction restated as 181 mV (not 148 mV) against the 200 mV limit**

> Reviewer applied the author's own 0.83 realisation factor consistently; also the 0->3A step starts in PFM which the CCM model does not cover, so P8 must treat 9.5% margin as the honest figure

**Load step accepted AT the 200 mV limit on the corrected reading (148 mV modelled); R5=75k stands, no rework**

> Measured R5 sweep shows no value clears fc, PM and dV together - 82k and 91k FAIL phase margin, the binding requirement; and dV is mathematically invariant in COUT (fc scales 1/COUT so fc*COUT is constant), so buying more output capacitance would be pure cost for zero transient gain

**The fc 25-50 kHz target was an ORCHESTRATOR proxy, not a requirement - the 24.4 kHz floor is not a miss**

> The real spec is 100 us recovery; at 24.4 kHz settling is 32.6 us, a 3.1x margin. Recorded so no later phase re-litigates a 2.4% shortfall against a number that was never the specification

**Loop compensation is the board's #1 bring-up bench item; R5/C2/C3 are three adjacent 0603 parts, re-tunable without a respin**

> Every loop number rests on extrapolating a one-point vendor calibration onto a different circuit, and the vendor's published GM matches no reader-built model - only a bench Bode plot can close it

---

## P5 Board Setup  (1)

**Mounting holes come from the schematic (H1-H4), not board_init - re-run with --mounting-holes 0**

> Passing 4 duplicated the schematic's own H1-H4 and produced the last 2 parity items; sourcing them from the schematic keeps them real parts with nets and BOM semantics, and P6 places them at the corners

---

## P6 Placement  (8)

**Thermal via array is 12, not the specified 16 - 16 is geometrically impossible**

> EP is 3.502x2.613mm; four 0.55mm lands at 1.0mm pitch need 3.55mm, and JLC's 0.5mm hole-to-hole floor caps it at 3x4=12 at 0.9-0.95mm pitch. Cost is R_via 2.48 vs 1.90 K/W = +0.5 C of Tj, inside the margin. check_thermal would not have caught this

**J1/J2 rotations corrected in placement.edges: J1=270, J2=90 (were 0 and 180)**

> The declared rotations pointed BOTH screw-terminal wire entries into the board; proven by orthographic side render, because the mouth is the SHORTER plastic face on this part and the WRL bbox alone would have misled

**Anneal candidates REJECTED on merit; hand structure kept**

> Candidates reached HPWL 224.6 vs 234.0 but the 3.1% is almost entirely plane-fed GND, all four carried 5-7 courtyard overlaps after repair, and cand1 pulled R7 3.5mm closer to L1 and lengthened /FB

**TOOLCHAIN GOTCHA: placement.fixed silently disables separation constraints**

> Fixed refs are excluded from the annealer's cluster list, so all 8 separation pairs landed in separation_unknown_refs at zero cost weight; verified all 8 by hand instead (C4-U1 22.2mm, F1-U1 11.1, R6-L1 9.8, J2-L1 16.5) - all pass

**P7 must pour the four GND planes AND pour /SW as a zone BEFORE any autoroute**

> The 0.83 route probe is an artifact: GND is 25 of 71 connections and plane-fed, so unpoured Freerouting tried it as 2.055mm tracks; and aiee_pwr_width_SW (2.31mm) applies to every /SW track including the 0603 bootstrap cap's - a zone is not a track, so the rule does not bind it

**P5 omitted the mandatory keepout translation; corrected at P6**

> placement.keepouts rects were still board-local, so three landed off-board entirely and the fourth produced a phantom violation; translated in constraints.json and annotated

**25 structural footprints left LOCKED - P8 fixers must unlock before nudging**

> Placement cost 8 edit iterations and the hot-loop geometry is the design; locking prevents a later fixer from silently undoing it, but the lock must be visible to whoever needs to move something

**thermal.min_vias lowered 16 -> 12 in constraints.json with the geometry recorded**

> 16 cannot physically fit (EP 3.502x2.613mm vs 3.55mm needed at 1.0mm pitch, JLC 0.5mm hole-to-hole floor); 16 was our own derivation not a vendor spec, and leaving it would fail check_thermal at P8 on an unachievable target. Copper-area criteria unchanged, Tj cost +0.5 C

---

## P7 Routing  (5)

**C:/Program Files/Git/SW poured as a ZONE, not routed as tracks**

> aiee_pwr_width_SW demands 2.31mm on every /SW track including the 0603 bootstrap cap's, which is impossible at that pad; a zone is not a track so the rule does not bind it - the alternative would have been weakening a current-carrying rule

**Forced --power-layers In1.Cu,In2.Cu,B.Cu instead of the auto heuristic**

> auto considers inner layers only, so B.Cu would have been fair game for power routing and would have cut the second radiating face on a board that closes on 7 C of thermal margin

**Freerouting necking fixed by pour fan-in; no rule weakened**

> FR routed at exactly the pad widths (0.8058mm = 0402 pad) despite --pad-window clearing all 61 power pads; remediation ladder step 4 applied, leaving .kicad_dru, .kicad_pro netclasses and constraints.json byte-unchanged

**ORCHESTRATOR ERROR corrected by the router: B.Cu >=650 mm2 within 14.3mm of U1 is impossible**

> That disc clipped to the 50x40 outline is only 608.3 mm2; the constraint's _note says 650 is check_thermal's A_sat SUMMED over layers, which measures 2169.7 mm2. I restated the constraint wrongly in the spawn prompt

**route_critical and route_cleanup both skipped, deliberately**

> route_critical skips plane/pour-carried power nets by design and every power net ended up plane- or pour-carried; route_cleanup's loop-breaker has regressed on pour boards twice and DRC was already 0/0

---

## P8 Verification  (9)

**ACCEPT deletion of 3 of 9 U1 ring vias; U1 keeps 12 EP + 6 ring = 18**

> Each sat in a 1.06-1.58mm GND finger, so it was current-limited by the finger not the via and carried no real share; the nearest legal >=2.055mm spot was 5-6.5mm away ACROSS the /SW pour, which would route return current under the switch node - exactly what the brief forbids. Deleting beats relocating, and 18 still exceeds the min_vias 12 requirement

**SCRIPT DEFECT: check_current.pour_neck erodes each zone fill in isolation**

> A pour split across zone objects (KiCad knocks a lower-priority same-net zone out of a higher-priority one) reports a phantom 0.00mm neck with pos in a different structure from the real defect; it should union same-net fills per layer or emit a distinct fill_fragmented kind. Cost most of this fix's analysis time

**SCRIPT GAP: stitch_vias accepts a candidate whose surrounding same-net pour is narrower than the net's IPC-2152 width**

> The (60.72,60.225) stitch landed in a 1.06mm GND channel and became a P8 error; existing rejects (foreign_copper, near_same_net_via) do not cover pour width

**SELF-CORRECTION: reverted pdn=false on +5V and GND; used waivers instead**

> pdn=false silenced check_pdn's category error but ALSO excluded both nets from check_irdrop - the two highest-current nets on the board. A waiver states 'this check does not apply' without disabling unrelated analysis. Restored coverage now reads +5V 9.0mV / GND 1.1mV drop

**SPICE sim gate NOT run - deliberate scope call, recorded as a deviation**

> P2 nominated only SIM-1 (FB divider setpoint) and SIM-2 (EN/UVLO thresholds), both static DC-tolerance fragments already verified TWICE analytically with exact numbers by the P4 author and independently by the fresh-context reviewer (who showed 1% parts miss by 32-36mV); house policy forbids simming the buck switching for lack of vendor models, so SPICE would restate arithmetic rather than test anything new

**CRITICAL FIX: D2 cathode marker was on the anode end; moved (41.720,59.125) -> (45.900,59.000)**

> Assembled per the wrong silk, the 15V Zener reverses into a forward diode holding Vgs at -0.7V, Q1 never enhances, 2.6A runs in its body diode at ~2.1W in an SO-8 - Q1 and the reverse-polarity protection both destroyed. Netlist was always correct; only the marker was wrong. Now 0.640mm from pad 1 (cathode) vs 3.036mm from pad 2, agreeing with the footprint band and pin-1 dot

**ACCEPT 3 residual misattributed refdes labels (C9->C7, R7->C12, C2->C3); 8 fixed**

> At 1.0mm refdes size the inked label is 2.6-3.2mm wide against a 2.5-3.0mm passive pitch, so no attribution-clean position exists at any legal clearance; 0.8mm text would clear two but move_text has no size field. Mitigation: all FUNCTIONAL legends are correct (VIN/VOUT/polarity/TP names), SMT is machine-placed from the CPL not from silk, and only J1/J2 are hand-soldered - their legends are correct

**KEEP the fixer's remove_text addition to place_edit.py/place_swig.py (out-of-protocol skill change)**

> add_text matches on (layer,string,position) so it can create or update in place but never RELOCATE; without remove_text the only options were raw-editing the board (forbidden) or shipping the board-killing D2 marker. Additive, regression-tested, 66/66 place tests pass

**THERMAL RESTATED: Tj ~98.7 C, margin 6.3 C (not 7.1), band 87.5-108.4 C at +/-30%**

> The reviewer showed check_thermal's 0.83 C headroom is NOT a layout property - a_eff measures 2137mm2 and clamps to A_SAT 645, so theta is constant for any 4L board above 645mm2 and the vias/planes move it 0.00 C. The believable number is the P1/P2 ladder, corrected: it still assumed 16 vias at 2.16 K/W, and 12 vias gives ~2.88 K/W = +0.76 C

---

## P9 DFM  (4)

**ORCHESTRATOR DIAGNOSIS WRONG: the TP silk dfm error was NOT a mask-aperture overlap**

> I estimated a ~0.92mm aperture; measured it is 1.7664mm2 = exactly pi*0.75^2, zero mask expansion. Real cause is lib/gerblib.py read_gerber chording drawn arcs, so KiCad's two 180-degree arcs collapse onto the diameter - a phantom 1.5x0.12mm bar = 0.1798mm2 exactly. My suggested fallback (enlarge the ring) could never have worked, since the chord crosses the centre at any radius

**SCRIPT DEFECT (high value, NOT fixed this run): lib/gerblib.py chords drawn arcs**

> The S12 approximate_arcs fix was applied to _flash_polys only, not to Line/Arc in read_gerber, so EVERY footprint drawing a silk ring around a pad - every stock TestPoint, many polarity rings - will fail the dfm gate forever. Recorded for a future T-step rather than fixed here, because deletion already cleared this board and skill work belongs in its own session

**12.7um clearance was a priority-0 pour crumb in a 0.02mm inter-zone lane**

> KiCad deburrs a pour at min_thickness BEFORE subtracting higher-priority zone outlines, so a sub-min_thickness lane between two zone outlines gets refilled and never deburred; the P8 Z2 edge at y=51.12 'clearing' zone 2 at 51.1 is what manufactured it. Fixed with a priority-6 bridge zone; a second unflagged 0.02x1.93mm hair went with it

**DISCLOSE, do not fix: 2 residual etch slivers and a 0.5um island-gap margin**

> Slivers 0.05x1.71mm and 0.078x0.497mm are fused to neighbouring copper so no gate fires, but a fab may query them; the min F.Cu island gap is 0.1021mm against JLC's 0.1016 floor, so ANY further pour edit risks tripping dfm_clearance - the risk of touching exceeds the risk of leaving

---

