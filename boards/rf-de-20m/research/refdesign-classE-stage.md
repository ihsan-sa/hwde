# refdesign-classE-stage.md - Class E power stage (EPC2019 + LMG1020)

Topology, operating point and both parts are FROZEN (requirements.md Section 3/10). This file
extracts layout/design DECISIONS from primary sources only - no topology alternatives proposed.

Sources fetched (primary unless marked): full text pulled and read, not summarized from search
snippets, except where marked [search-only].

- **WP010** - D. Reusch, "Optimizing PCB Layout" (EPC White Paper, 2019).
  https://epc-co.com/epc/Portals/0/epc/documents/papers/Optimizing%20PCB%20Layout%20with%20eGaN%20FETs.pdf
- **WP008** - A. Lidow, J. Strydom, "eGaN FET Drivers and Layout Considerations" (EPC White Paper, 2016).
  https://epc-co.com/epc/Portals/0/epc/documents/papers/eGaN%20FET%20Drivers%20and%20Layout%20Considerations.pdf
- **AN009** - "Assembling eGaN FETs and Integrated Circuits" (EPC App Note, rev July 2021).
  https://epc-co.com/epc/Portals/0/epc/documents/product-training/Appnote_GaNassembly.pdf
- **AN021** - Y. Zhang, M. de Rooij, "eGaN FETs for Low Cost Resonant Wireless Power Applications" (EPC App Note, 2018).
  https://epc-co.com/epc/Portals/0/epc/documents/application-notes/an021%20fets%20for%20low%20cost%20class%20e%20wipo.pdf
- **EPC2019DS** - EPC2019 datasheet, rev October 2022. https://epc-co.com/epc/Portals/0/epc/documents/datasheets/EPC2019_datasheet.pdf
- **LMG1020DS** - LMG1020 datasheet, TI SNOSD45B, rev October 2018. https://www.ti.com/lit/gpn/LMG1020
- **Sokal2001** - N. O. Sokal, "Class-E RF Power Amplifiers," QEX, Jan/Feb 2001, pp.9-20 (mirror).
  https://people.physics.anu.edu.au/~dxt103/160m/class_E_amplifier_design.pdf
- **W8JI** - T. Rauch, "RF Choke Selection Guide" (practitioner reference, not peer-reviewed/vendor).
  https://www.w8ji.com/rf_plate_choke.htm

---

## 0. Flag before anything else: part-physical mismatch vs. the brief

EPC2019DS (current rev) does **not** match the "1.35 mm chip-scale LGA" description in this
board's brief/requirements. Actual: **die-form part, 2.77 x 0.95 mm, 7 elongated solder bars in
a single row** (not a square BGA grid). Pinout: pad1 Gate, pad2/4/6 Source, pad3/5 Drain, pad7
Substrate (tied to Source). This is exactly the "interleaved-row LGA" geometry WP010's Fig.1-2
describes (alternating drain/source bars), NOT the 2D ball-grid case shown in most of WP008's
figures - so via-per-bar guidance (Decision 2) applies, not a 2D via-array-per-ball.
Also: **Coss/Qoss numbers differ from this board's frozen network math.** EPC2019DS lists
COSS = 135 pF typ / 163 pF max and QOSS = 20-24 nC (VGS=0V, VDS=100V), vs. the "Coss 110 pF /
Qoss 18 nC @ 100 V" figures already baked into requirements.md's C_shunt=317pF split. See OPEN.

---

## 1. EPC eGaN FET layout rules (highest-priority output per owner)

**D1. Interleave drain/source current paths; use the source pad nearest the gate as the
gate-return "star" point.** eGaN LGA/solder-bar parts without a dedicated gate-return pin should
have the die's nearest source pad(s) serve as the star ground for both gate and power loops, with
gate-loop and power-loop currents kept orthogonal or opposing. Interleaving drain/source current
directions (in copper traces, in the solder bars themselves, and in the vias below them) creates
small opposing-field loops that self-cancel and cut total loop inductance.
*Maps directly onto EPC2019's actual pinout*: pad2 (Source, adjacent to pad1 Gate) is the natural
Kelvin/gate-return point; pads 3/5 (Drain) and 4/6 (Source) alternate exactly as WP010 describes.
Source: WP010, Introduction + Fig.1-2.

**D2. Via spec for dual-sided/filled-via LGA termination (4-layer+), by voltage class.**
Two vias per pad side, staggered (not clustered) to avoid PCB tear zones (or request 45-degree
fiber-grain rotation from the fab). For 200 V devices (EPC2019 is 200 V): **8 mil (200 um)
drilled hole, 12 mil (300 um) annular ring.** (40/100 V devices get a smaller 6 mil/8 mil spec -
not applicable here.) If a via must land inside a device pad, it must be a filled/capped microvia
(6 mil drill/8 mil annular ring, not exceeding pad width) - an uncapped in-pad via lets solder
wick away during reflow, varying die standoff and hurting cleaning, tilt, and thermal cycling.
Source: WP008, "Suggested Layouts" (Single/Dual-sided/Filled-via termination), p.4-5.

**D3. Prefer the "optimal" stacked self-cancelling loop over lateral or vertical conventional
loops.** Route the top-layer power loop directly over an inner-layer (Layer 2) return path of the
same shape, rather than (a) a same-layer loop backed by a shield plane ("lateral") or (b) a
top/bottom split loop ("vertical"). The optimal loop needs no shield layer, is largely
independent of total board thickness, but is strongly dependent on the top-to-inner-layer
spacing (minimize it). Measured: **~65% lower loop inductance than the best conventional
(lateral or vertical) loop**; quantified benefit at the device level: an eGaN FET design with
loop inductance reduced from 1.6 nH to 0.4 nH cut voltage overshoot from 100% to 30% of Vin and
gained ~4% efficiency; optimal-vs-conventional layout gave "500% increase in switching speed with
a 40% reduction in voltage overshoot." Source: WP010, "Optimal eGaN FET Layout," Table I, Fig.3,
Fig.7, p.6.

**D4. Gate loop inductance has a hard ceiling set by the part's narrow Vgs window.**
Overshoot-free gate loop inductance: **L_G <= 1/4 x (R_G + R_Source)^2 x C_GS**. A gate drive
pull-down resistance <=0.5 ohm is EPC's blanket recommendation for higher-voltage eGaN parts to
suppress Miller (dv/dt-induced) turn-on - **but this specific 0.5-ohm ceiling is explicitly
waived for parts with a "good Miller ratio" (Q_GD / (Q_GS x V_TH) < 1)**. Computing EPC2019's own
ratio from its own datasheet numbers (Q_GD=0.6 nC, Q_GS=0.8 nC, V_TH typ=1.4 V):
0.6 / (0.8 x 1.4) = **0.54 < 1** - EPC2019 qualifies as a good-Miller-ratio part, so the strict
sub-0.5-ohm floor does not strictly bind here; LMG1020's own >=2 ohm floor (D8) can be used
without reopening Miller turn-on risk, subject to the L_G ceiling above. Source: WP008, "Driving
eGaN FETs" + "Gate drive loop inductance," p.1,3, Eq.1-2 (ratio arithmetic is this agent's
substitution of EPC2019DS values into EPC's own published formula, not a separate opinion).

**D5. Common-source inductance (CSI) is a second-order but real effect - and asymmetric.** CSI
opposes the gate drive during di/dt (raises switching loss, hence D1's push to minimize it), but
some CSI also *reduces* Miller-turn-on risk of the *complementary* device in a half-bridge by
adding a damping voltage. Not directly applicable to our single ground-referenced switch (no
complementary device), so CSI should simply be minimized per D1/D2/D3 without the half-bridge
trade-off. Source: WP008, "Effect of common source inductance (CSI)," p.3.

---

## 2. LMG1020 layout + application rules

**D6. Ground return: Layer-2 plane directly under the driver+FET, single-point-connected.**
"To minimize gate drive loop inductance, the source return should be on layer 2 of the PCB,
immediately under the component (top) layer. Vias immediately adjacent to both the FET source
and the LMG1020 GND pin connect to this plane... take care to connect the GND plane to the source
power plane only at the FET to minimize common-source inductance and to reduce coupling to the
ground plane." A four-layer-or-higher board is stated as **required**, not optional, to reach
rated performance (matches this board's already-frozen 4-layer requirement). Source: LMG1020DS,
Section 10.1, 10.1.1 "Gate Drive Loop Inductance and Ground Connection."

**D7. Bypass capacitor: two-stage, top-layer, adjacent to the IC.** >=0.1 uF up to 1 uF, X7R or
better, placed on the top layer immediately adjacent to VDD/GND using large power planes;
preferred body types LICC / IDC / feed-through / LGA (lowest ESL); plus a second, larger (1 uF)
cap placed as close as practical. TI's own layout example (Fig.15) uses a 0402 primary cap
directly beside the 6-ball WCSP; Section 9 additionally recommends the combination "0.1 uF of
0402 or feed-through capacitor (closest to LMG1020) and a 1 uF 0603 capacitor," with a
three-terminal/feed-through cap as the lowest-ESL option. Source: LMG1020DS, Section 9 "Power
Supply Recommendations," Section 10.1.2 "Bypass Capacitor," Fig.15-16.

**D8. Gate resistor floor: >=2 ohm at each OUTH and OUTL.** "TI recommends using at least a 2-ohm
resistor at each OUTH and OUTL to avoid voltage overstress due to inductive ringing. Ringing
overshoot must not exceed the maximum absolute supply voltage." For fast/strong turn-off, OUTL's
resistor (R2) can be shorted directly to the gate; for symmetric drive it's acceptable to short
OUTH/OUTL together onto one resistor. Since our design is single-ended (one FET, no
complementary device to match), a single shared resistor is a legitimate simplification to carry
into the schematic phase. Source: LMG1020DS, Section 8.2 "Typical Application," Section 8.2.1.

**D9. WCSP ball map and minimum pulse width.** 6-ball WCSP (YFF), 0.8 x 1.2 mm body, 0.4 mm ball
pitch: A1=VDD, A2=OUTH, B1=GND, B2=OUTL, C1=IN+, C2=IN-. Min input pulse width **1 ns**;
propagation delay 2.5 ns typ / 4.1 ns max (turn-on), 2.6 ns typ / 4.3 ns max (turn-off). TI's own
bring-up test (Fig.14) drives a FET at **40 V bus, 60 A, with a 1.5 ns pulse / 300 ps fall
time** - i.e. TI validated this exact driver at our exact bus voltage. In that same test (Fig.13),
the driven FET's drain still shows **~20 V of overshoot "due to the inductance in the power
loop"** even in TI's own reference setup - direct, part-specific corroboration that D1-D3's loop
geometry work, not the driver IC, is what controls overshoot at 40 V. Source: LMG1020DS, Section
5 "Pin Configuration," Section 6.6 "Switching Characteristics," Section 8.2.5 "Application
Curves."

**D10. Absolute ceiling on the gate node is set by EPC2019, not by LMG1020.** LMG1020's own OUTH
pin absolute max is 5.75 V; EPC2019's Vgs absolute max is **+6 V / -4 V** (10 V total window) with
recommended drive 5 V ON / 0 V OFF ("negative voltage not needed" per EPC2019DS's own
application note). At 5 V nominal drive, headroom to the FET's +6 V ceiling is only **1 V** -
tighter than LMG1020's own 5.75 V pin rating. D8's >=2 ohm floor plus D4's loop-inductance ceiling
must be sized against this 1 V ceiling, not against LMG1020's. Source: EPC2019DS "Maximum
Ratings" table + "Application Notes" box; LMG1020DS Section 6.1 "Absolute Maximum Ratings."

**D11. Ground-bounce mitigation options (not obviously needed here, keep as fallback).** IN- can
be tied to VDD and driven as the (inverting) PWM input in a positive-feedback arrangement for
better noise immunity, optionally with a 100-ohm series current-limit resistor and small input
RC filtering; a common-mode choke on IN+/IN- is TI's recommendation for severe ground-bounce
cases (e.g. a source current-sense resistor in the gate-drive-loop path - not applicable to this
board, which has no sense resistor in the switch source). Source: LMG1020DS, Section 8.2.2.1
"Handling Ground Bounce."

---

## 3. Class E design practice at HF/VHF

**D12. Exact Sokal design coefficients for our chosen Q_L=5** (already used to derive this
board's frozen L_s/C_s in requirements.md - cited here for traceability): normalized
P.R/(Vcc-Vo)^2 = 0.51659; C1(=C_shunt).2*pi*f*R = 0.20907; C2(=C_series).2*pi*f*R = 0.63467.
These are Sokal's continuous-function fits (accurate to +-0.15%) to exact numerical solutions,
superseding the older Q_L-independent (Q_L->infinity) constants 0.1836/0/0.3672 that AN021 uses
for its 6.78 MHz reference design. Source: Sokal2001, Table 1, Eq.4-9, p.11-13.

**D13. RF choke sizing floor (drain-feed inductor, separate from the resonant tank).** AN021
gives, for a single-ended Class E stage (citing Kazimierczuk 1984): **omega x L_RFck / R_load >
22** so the choke's AC ripple contribution to the design equations is negligible (a looser >11
bound also appears in some derivations). At R_opt=4.614 ohm, f=20 MHz: L_RFck > 22 x 4.614 /
(2*pi*20e6) ~= **0.81 uH as an order-of-magnitude floor** - more margin is safer. Sokal's own
paper gives no closed-form optimum below ~3 MHz-and-up designs: "it is advisable to use large
inductances so that the inductors can operate as open circuits at the operating frequency" - i.e.
this is a floor, not a target, and oversizing has no design-equation penalty (only cost/size).
Source: AN021 p.2 (eq. omega.L_RFck/R_load>22); Sokal2001 p.11.

**D14. Self-resonance must sit ABOVE the operating frequency - and this is the dominant real-world
failure mode, more than the inductance floor.** Per a long-running HF/VHF power-amplifier
choke-design reference: operating a choke *above* its self-resonant frequency is "catastrophic" -
the choke turns net capacitive, presents very LOW impedance at the switch node while carrying
very HIGH internal RF voltage, and can arc across its own winding. Practical rule of thumb: the
choke needs "several thousand ohms" of impedance across the whole operating range, verified
empirically (dummy load + RF detector sweep), not by inductance-value calculation alone, because
winding self-capacitance and proximity to nearby copper/ground both pull the real SRF down from
the datasheet number. This directly reinforces requirements.md's already-frozen binding
constraint ("must be a real RF choke with self-resonance well above 20 MHz") with a mechanism and
a test method. [Practitioner source, not vendor/peer-reviewed - flagged accordingly.] Source:
W8JI, "RF Choke Selection Guide."

**D15. Harmonic suppression at our exact Q_L, unfiltered.** For Q_L~=5.1 (our design is Q_L=5):
2nd harmonic ~= -20 dBc (~1% of fundamental power) from the load network alone, with no added
filter; 3rd harmonic ~= -36 dBc (~0.025%). Even-order harmonics could be further cancelled with a
push-pull circuit if ever revisited (not applicable to this single-ended, frozen topology). This
is real suppression, but nowhere near what any transmit/EMC compliance would require - consistent
with requirements.md Section 8 item 3 (dummy-load-only, not a certifiable transmitter). Source:
Sokal2001, "Harmonic Filtering and Associated Changes to Design Equations," p.13.

**D16. Load-mismatch sensitivity, quantified (not just qualitative).** Ideal Class E switch
voltage stress is 3.56 x Vdd; EPC's own measured differential eGaN Class E amplifier (EPC9051,
tested across an AirFuel-class reflected-impedance range) shows peak stress reaching **as high as
7x Vdd** once load impedance moves off the nominal design point - "despite the high efficiency,
it is challenging to design a class E amplifier that works for a wide load impedance range."
This is a directly-cited, quantified confirmation of the load-sensitivity hazard already
owner-acknowledged in requirements.md Section 8 item 4 / Q11 (this board is explicitly frozen to
dummy-load-only operation because of exactly this effect). Source: AN021, "Class E amplifier
design basics," p.2.

---

## 4. Thermal handling of chip-scale/solder-bar eGaN GaN

**D17. Use EPC2019's own datasheet thermal numbers, not the generic eGaN-family estimate.**
EPC2019DS (device-specific, current rev): R-th,JC = 2.7 C/W, R-th,JB = 7.5 C/W, R-th,JA = 72 C/W
(1 sq-in of single-layer 2 oz copper on FR4). This differs materially from WP008's generic
family-wide estimate ("~40 C/W in still air... on one square inch of 2 oz Cu" for "eGaN FETs" as
a class, with "~8 C/W R-th,JC for small-area FETs" as a different family-wide bucket) - use the
part-specific EPC2019DS numbers for any thermal budget math, not the WP008 generic figures. This
board's single-sided top-assembly plan means heat leaves via: die -> solder bars -> PCB copper
(top + inner planes through a via array) -> bottom copper -> external heatsink - closer to WP008's
"double-sided cooling with thermal pad" case than its "single-sided, no backside cooling" case,
but neither of WP008's two idealized numbers plug in directly; this needs explicit modeling at
the interface-spec/thermal phase, not a single borrowed R-th number. Source: EPC2019DS, "Thermal
Characteristics"; WP008, "Single-Sided Cooling" / "Double-Sided Cooling," p.6-7.

**D18. Double-sided-cooling benchmark, for context.** EPC's water-cooled "best case" rig
(pneumatic-plunger Kelvin test fixture) measures 12-14 C.mm^2 normalized R-th,JA when cooling is
primarily through the silicon substrate; realistic thermal-pad-based dual-side cooling of
multiple die under one shared heatsink achieved ~6 C/W into the heatsink + ~15 C/W into the board.
Heatsink must be electrically isolated from the die (FET substrate = Source potential) unless the
TIM itself is an electrical insulator. Source: WP008, "Double-Sided Cooling," p.6-7.

**D19. EPC2019-specific assembly/via precedent exists and is directly on-point.** AN009 uses
EPC2019 paired with an LM5113 driver (an earlier EPC-recommended low-side/half-bridge driver,
same functional role as our LMG1020) as its own worked X-ray inspection example of good vs. bad
reflow (Fig.21-22). Binding process numbers carried forward for the interface-spec/stack-up
phase: SMD (solder-mask-defined) footprint is mandatory, not NSMD; min via hole 6 mil / min
annular ring 5 mil / min 10 mil wall-to-wall via spacing; in-pad vias must be filled+capped;
ENIG finish preferred over HASL (150 uin Ni / 3-5 uin Au); max die placement pressure 50 psi;
peak reflow 235-250 C over a 3-5 min profile. **For 200 V-class devices (EPC2019 is 200 V)**, AN009
recommends a minimum 12-mil core thickness between layers 1-2 (and mirrored 3-4) specifically for
creepage - vs. 5 mil for 100 V-class parts - directly relevant given requirements.md's own
>=215 V peak creepage/clearance constraint on the drain net. Source: AN009, "Vias," "Layer
stack-up," Fig.20-22, p.3-4,7.

---

## 5. Known footguns driving the EPC2019 gate

**D20. The absolute Vgs window is genuinely narrow: -4 V / +6 V, and the FET's rating is the
tighter ceiling.** See D10: at 5 V nominal drive, only 1 V of headroom to +6 V abs max exists,
and the FET's own +6V rating is tighter than the driver's own 5.75V pin rating - so gate-loop
ringing (D4, D6) is the dominant risk, not the driver. EPC2019 itself is rated 0 V OFF ("negative
voltage not needed" - EPC2019DS's own note), so a negative-bias scheme is explicitly NOT called
for by the manufacturer; the mitigation path EPC and TI both point to is loop-inductance
minimization (D1-D4, D6) plus TI's own >=2-ohm gate-resistor floor (D8), not negative bias or an
external clamp. Source: EPC2019DS "Application Notes" box + "Maximum Ratings"; WP008 "Driving
eGaN FETs," Table 1.

**D21. Good Miller ratio removes one common footgun class.** EPC2019's Q_GD/(Q_GS x V_TH) = 0.54
(<1, see D4) means dv/dt-induced Miller turn-on during the OFF state is a lesser risk for this
specific part than for a "bad Miller ratio" eGaN device - the usual <=0.5-ohm pull-down mandate is
explicitly waived by EPC's own stated condition. Do not over-design the pull-down resistor smaller
than LMG1020's >=2-ohm floor (D8) on this basis. Source: WP008 Eq.1 + EPC2019DS charge table
(arithmetic is this agent's substitution, formula and threshold are EPC's).

**D22. Body-diode conduction loss is real but easily bounded by dead-time - not applicable to a
half-bridge here, but relevant to gate-drive dead-time choices if a future revision reconsiders
duty cycle margins.** eGaN "body diode" forward drop (~2 V typ per WP008's family table) is higher
than silicon's but has zero reverse-recovery charge; keeping any non-conduction interval to "just
a few nanoseconds... virtually eliminates body diode losses." Lower-priority for this design
(single-switch Class E has no complementary-device dead time to manage) but worth carrying if the
50% nominal duty cycle from an adjustable external generator (I1) ever drifts. Source: WP008,
"Gate Drive Dead-Time," p.2.

---

## OPEN - conflicts / discrepancies between sources (do not silently resolve)

1. **EPC2019 physical package**: this board's brief/requirements.md describes a "1.35 mm
   chip-scale LGA." The current EPC2019 datasheet (rev Oct 2022) describes a 2.77 x 0.95 mm
   die-form part with 7 solder bars in a row - a materially different footprint shape (row of
   bars, not a square grid). Flag for the interface-spec/footprint phase to re-verify against the
   datasheet directly before finalizing the footprint.
2. **Coss/Qoss numeric mismatch**: requirements.md/root LEARNINGS.md carry "Coss 110 pF, Qoss
   18 nC @ 100 V" (used to derive the frozen C_shunt=317pF = Coss + ~200pF split). EPC2019DS
   (current rev) instead lists COSS 135 pF typ/163 pF max and QOSS 20-24 nC at the same VGS=0V,
   VDS=100V condition. This is load-bearing for the shunt-cap split and should be re-verified
   against the datasheet by the phase that owns that number - not silently corrected here.
3. **Gate pull-down resistor guidance, partially conflicting on its face**: WP008's generic
   <=0.5-ohm-for-higher-voltage-parts rule vs. LMG1020's own >=2-ohm floor. Resolved in D4/D21 by
   EPC's own stated exception (good Miller ratio) rather than left as a true conflict - but the
   final R1/R2 values still need bench/sim verification against both the D4 loop-inductance
   ceiling and D10's 1V gate headroom; this agent does not choose those values.
4. **RF choke SRF guidance has two flavors in the literature** ("SRF at or near the operating
   frequency" for narrowband choking vs. "SRF well above" for wideband noise blocking - seen in
   the initial web search pass, not confirmed against a primary source). requirements.md already
   freezes "self-resonance well above 20 MHz," and D14's practitioner source supports that
   direction (SRF must be above, not at, the operating point, because operating above SRF is the
   catastrophic failure mode) - no change recommended, just noting the ambiguity existed in
   the broader literature before landing on the frozen, above-SRF interpretation.
