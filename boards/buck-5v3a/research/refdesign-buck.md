# Reference design research: buck (AP6335x family)

Block: regulator (buck-5v3a). Read `.claude/skills/ai-ee/reference/topologies/buck.md` first;
deltas against it are called out inline. Primary source for all AP6335x facts below:
**Diodes Incorporated, "AP63356Q/AP63357Q" datasheet, document DS41948 Rev.1-2, Sept 2020**
(https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308101545_Diodes-Incorporated-AP63357QZV-7_C3194572.pdf
- identical document serves both LCSC SKUs C3194571/C3194572). Section numbers below are the
datasheet's own "Application Information" numbered sections (1-15) plus named tables/figures.

## 1. AP6335x external component table, 5V/3A

Family is **ADJUSTABLE-ONLY. The "Fixed" catalogue attribute the scout flagged does not
apply to either shortlisted SKU** - checked and closed:
- DS41948 s10 "Setting the Output Voltage": "The AP63356Q/AP63357Q has adjustable output
  voltages starting from 0.8V using an external resistive divider" - R1 = R2*(VOUT/0.8V - 1).
- Ordering Information table (DS41948 p.26) has no Fixed/Adjustable column at all - only
  "Operation Mode: PWM Only" (AP63356QZV-7) vs "PFM/PWM" (AP63357QZV-7). No Fixed SKU exists
  in this family.
- Cross-check: LCSC's own parametric attribute for both C3194571 (AP63356QZV-7) and C3194572
  (AP63357QZV-7) reads "Output Type: Adjustable" (fetched live from lcsc.com product pages).
- Likely source of the scout's confusion: buck.md s4 already documents a real Fixed/Adjustable
  split inside the *sibling* AP63200-series (AP63203 fixed vs AP63200/1 adjustable, DS41326).
  That trap is real for that family; it does not carry over to AP6335x, which has no fixed SKU.

Recommended BOM for VOUT=5V, internal compensation (COMP tied to GND - simplest option, no
external R5/C5/C6 needed), from DS41948 Table 1 ("Recommended Components Selections Using
Internal Compensation", 5.0V row):

| Ref | Value | Note |
|---|---|---|
| R1 (FB top) | 157 kOhm | sets VOUT with R2 per Eq.5 (VFB=0.800V typ, 0.792-0.808V range) |
| R2 (FB bottom) | 30 kOhm | |
| C4 (FB feed-fwd, optional) | OPEN | table says not needed at 5V; range is 10-220pF if added for transient response |
| L | 6.8 uH | Eq.6 method; 2.2-10uH recommended range, DCR < 30 mOhm for efficiency, Isat >= 1.35x Iload (>=4.7A here) |
| C1 (Cin) | 10 uF ceramic | "10uF or greater sufficient for most applications" (s12); RMS rating > half max load current |
| C2 (Cout) | 2 x 22 uF ceramic | 22-68uF ceramic range (s13); check against Eq.8/9 if a specific transient spec is given |
| C3 (BST) | 100 nF ceramic | "sufficient" (s14) - required, not optional, matches house buck.md s4 |

If external compensation is later wanted (e.g. to hand-tune bandwidth/phase margin), Table 2
5.0V row instead uses C2=3x22uF, R5=38 kOhm, C5=3.3 nF, C6=OPEN - DS41948 s15 gives the full
derivation method and a worked 5V/24Vin/3.5A example landing on R5=42.2k/C5=1.2nF/C6=15pF/
C4=10pF, ~41.7kHz bandwidth, 65.6 deg phase margin, -13.2dB gain margin.

**Soft-start**: internal, fixed, tSS = 4 ms typ (electrical table + s1). No SS pin, no external
cap, not adjustable - simpler than buck.md's general expectation of a possible SS pin.

**EN pin** (s3): self-starts. Internal 1.5uA pull-up from the internal LDO-regulated VCC
guarantees EN reaches its logic-high threshold (1.18V typ, 1.15-1.21V) if left floating -
device "automatically enables" as VIN rises. Can also be tied directly to VIN (high-voltage
pin). EN logic-low threshold 1.08V typ (1.02-1.14V) - below this, internal SS discharges and
the device disables. Confirms buck.md s6's general "many parts auto-start" pattern for this
specific part.
EN doubles as a programmable-UVLO pin: an external R3/R4 divider off VIN (Fig.37, Eq.1-2,
using the 1.5uA + 4uA hysteresis pull-up currents) can raise the UVLO threshold above the
default. Not needed here - default VIN UVLO (3.08V falling / 3.3-3.6V rising POR) is far below
our 7V minimum input.

**FSEL/MODE/SYNC pin: none exists.** Confirmed from the pin table (9 functional pins: VIN,
EN, FB, COMP, PG, BST, NC, GND, SW - pin 7 is NC, no internal connection) and the package/pin
assignment figure. PWM-only vs PFM/PWM is fixed by part number (AP63356Q vs AP63357Q), not
pin-selectable. The nearest thing to a "mode pin" is COMP: tying COMP to GND selects internal
loop compensation; leaving it floating and adding an RC network selects external compensation
(s15, first paragraph).

PG pin (s6, if ever wanted): open-drain, weak internal 5 MOhm pull-up, held low during
soft-start and on >20% output UVP; PG rise delayed 1.5ms, fall delayed 220us (anti-glitch).
Not used per this board's binding answer A6 (no PG required) - safe to leave open/NC-tied.

## 2. Vendor layout rules (for P6 placement/P7 routing)

DS41948 "Layout" section, "PCB Layout" (9 numbered rules, p.25) plus Figure 47 recommended
placement:

1. 3.5A load current -> heat dissipation is the driving constraint. **2oz copper on both top
   and bottom layers recommended.**
2. **Input capacitor(s) as close across VIN and GND as possible** (matches house buck.md s3
   hot-loop rule exactly - no delta).
3. **Inductor as close to SW as possible.**
4. **Output capacitor(s) as close to GND as possible.**
5. **FB network (R1/R2/C4) as close to the FB pin as possible.**
6. On 4+ layer boards, dedicate the 2nd and 3rd layers to GND for thermal performance.
7. Via-stitch heavily around the GND pin and under the GND copper, to all GND layers ("as
   many vias as possible" - no numeric count given).
8. Via-stitch heavily around the VIN pin and under the VIN copper, to all VIN layers (same
   qualitative-only guidance).
9. Figure 47's recommended floorplan (left to right, top to bottom): VIN pad block with C1
   bridging directly to the adjacent GND pad block; SW copper directly below/right of the IC
   feeding the inductor L; L feeds the VOUT/output-cap (C2) block on the far side from VIN;
   FB network (R1/C4 stacked, R2) sits below the IC on the side away from SW, with a short
   dashed route from the output node to FB and from FB/COMP back toward the IC - i.e. FB
   senses at the output-cap node, not at the inductor, and never crosses SW copper. BST cap
   (C3) sits directly adjacent to the BST/SW pins.

**Thermal-pad via count/size gap**: the datasheet gives no explicit via count or diameter for
the exposed pad itself - only the qualitative "as many as possible" language above. theta-JA
= 25 C/W is a *tested* number (Note 6, elec. characteristics table) specifically for "FR-4
substrate, four-layer PC board, 2oz copper, with minimum recommended pad layout" - if this
board ends up 2-layer or lighter copper, treat 25 C/W as optimistic and re-derive/verify via
thermal sim or measurement (flag for P2/P5 stackup decision, not decided here).

Eval-board equivalent: DS41948 does not publish a separate gerber/eval-board layout beyond
Figure 47's abstracted recommended-layout diagram; that figure is the vendor's most concrete
layout artifact and is what's summarized above.

## 3. Errata / footguns

**40V/400ms transient vs 35V DC abs-max** - confirmed exact numbers, Absolute Maximum Ratings
table (DS41948 p.4): "VIN Supply Pin Voltage: -0.3 to +35.0 (DC); -0.3 to +40.0 (400ms)".
This board's steady-state max input is 18V (binding answer A1: bench/AC-DC source, not
automotive - no load-dump/ISO7637-2 campaign), so there is large headroom under 35V DC; the
40V/400ms allowance only matters for hot-plug/cable-inductance ringing transients, which A1
already flags as needing "a modest input TVS" - not this device's own limiting factor for
this application.

**VDFN-13 exposed-pad soldering**: package is V-DFN3020-13/SWP "Type A1", 3x2mm, **with
wettable flanks** (DS41948 Description + Package Outline page) - wettable flanks let AOI see
a visible solder fillet on a leadless part, which is a real assembly/inspection benefit for
JLCPCB SMT, not a footgun. Moisture Sensitivity Level 1 per J-STD-020 (Mechanical Data, p.27)
- no dry-pack/bake-out handling required, unlimited floor life. No vendor-stated stencil
aperture or reflow-profile guidance specific to the exposed pad beyond the qualitative via
rules in section 2 above.

**Minimum on-time / duty at 18Vin->5Vout: not a risk.** Electrical Characteristics table
(p.5): ton_min = 100ns typ, fsw = 450kHz typ (400-500kHz range). Required duty at 18V in / 5V
out ~= 5/18 = 27.8% -> ton ~= 618ns, >6x the minimum. Even at the part's absolute max VIN of
32V, duty ~= 15.6% -> ton ~= 347ns, still >3x the minimum. No pulse-skipping/dropout concern
anywhere in this board's 7-18V input window.

**PFM vs PWM light-load ripple - decides which sibling to use.** This is the load-bearing
call for this block:
- AP63356Q: "Pulse Width Modulation (PWM) Regardless of Output Load" (feature list, s1) -
  ripple stays small and consistent at all loads including near-zero, by design.
- AP63357Q: forced PWM at heavy load, but below a ~700mA COMP-clamped PFM peak-inductor-
  current threshold it enters PFM to save power (s2), reaching 86% efficiency at 5mA (vs.
  AP63356Q's 258uA quiescent current query - AP63357Q's Iq is 22uA typ, ~12x lower). The
  datasheet's own scope captures show the tradeoff directly: Fig.20 (AP63356Q, 50mA, PWM)
  shows a small, regular ripple envelope; Fig.32 (AP63357Q, 50mA, PFM) shows a visibly larger,
  bursty/ragged ripple envelope at the same 50mV/div scale. At full load (3.5A) both parts
  look the same (Fig.21 vs Fig.33) because both run PWM above the PFM threshold.
- **This board's binding spec (A3) requires <=50mV pk-pk ripple over the full 0-3A load
  range, which includes light/no-load** - there is no stated minimum load. AP63357Q's PFM
  mode is the efficiency-optimized choice but trades ripple amplitude at light load for it;
  AP63356Q's forced-PWM-always behavior is the safer pick to guarantee the ripple spec across
  the whole stated load range, at the cost of somewhat worse light-load efficiency (irrelevant
  here - this is a 15W mains-fed power board, not a battery/standby design). **Recommend
  AP63356Q (PWM-only) over AP63357Q for this board's ripple requirement.** If a future
  revision needs standby-efficiency headroom, AP63357Q remains the drop-in alternate with the
  ripple caveat noted.

## 4. Reverse-polarity P-MOSFET gate clamp (upstream of the regulator)

Source (app note / tutorial, not a primary datasheet - marked as such per rules):
**components101.com, "Design Guide - PMOS MOSFET for Reverse Voltage Polarity Protection
Circuit"** (https://components101.com/articles/design-guide-pmos-mosfet-for-reverse-voltage-polarity-protection).

- **Gate resistor**: sets Zener bias current and gate discharge speed. Article's own range
  split: 100-330 Ohm for circuits "susceptible to sudden polarity reversal" (this board's
  screw-terminal field wiring is exactly that case - a technician can swap the two wires at
  any time); 1k-50k Ohm only where reversal during operation is implausible. Recommend the
  100-330 Ohm band for this board.
- **Zener rule**: pick a Zener voltage below the chosen MOSFET's Vgs(max) rating, so the
  gate is clamped before the gate oxide is stressed - the failure mode prevented is **gate
  rupture/breakdown from Vgs overvoltage**, which would occur if the full (possibly TVS-
  clamped) input voltage appeared gate-to-source with no clamp in place. Article's example:
  9.1V Zener for a 10V Vgs(max) part (their simulation used 6.8V Zener + 100 Ohm resistor for
  the same reason - conservative margin below Vgs(max)).
- **Board-specific grounding of this rule** (cross-checked against this board's own upstream
  shortlist, `research/powerpath.json`): the top-ranked reverse-polarity PMOS candidate,
  AOD403 (ElecSuper datasheet Rev-1.4, TO-252/DPAK), has **Vgs(max) = +-25V** (Absolute
  Maximum Rating table). The top-ranked input TVS candidate, SMBJ20A, clamps at Vc = 32.4V
  under surge - i.e. **higher than the FET's 25V Vgs(max)**. This is precisely why the Zener
  gate clamp is necessary here, not optional: without it, a surge event that drives the input
  toward the TVS's 32.4V clamp voltage would put close to that same voltage across the FET's
  gate-source if the gate were only resistor-pulled to source, exceeding Vgs(max) and risking
  gate rupture. A Zener in the 15-18V range (comfortably below the 25V Vgs(max), well above
  the FET's Vgs(th) so it stays fully enhanced across the whole 7-18V operating range) with a
  100-330 Ohm gate resistor satisfies both the components101 rule and this board's own
  TVS/PMOS pairing. Final Zener/FET pairing is P2's part-selection call, not decided here.

## Open items / conflicts

None between sources on the core AP6335x facts (datasheet text, ordering table, and LCSC's
own live parametric attributes all agree: adjustable-only, no Fixed SKU). One judgment call
surfaced above (PFM vs PWM sibling choice) with a recommendation, not a conflict.
