# Reference-design research: linear-regulator (bb-ldo)

No `reference/topologies/linear-regulator.md` exists yet (library has `buck.md`
only) - this note is the seed of one; no prior-note delta to research against.

Design point (from requirements.md): 5 V in (4.75-5.25) -> 3.3 V out, 500 mA
continuous, **0.975 W** dissipated at Ta = 50 C, still air, no heatsink,
2-layer JLC board, static resistive load, scope tier `block-only` (no
protection/filtering/indicators beyond datasheet need). Candidates surveyed:
AMS1117-class (bipolar, ESR-dependent), LM1117 (TI, bipolar, ESR-dependent),
MIC29302A (Microchip/Micrel, PNP pass, ESR-tolerant but not ceramic-clean),
AP2114 (BCD Semi / Diodes Inc, CMOS pass, ceramic-stable).

## 1. Capacitors - the ceramic-stable / ESR-dependent split

**AMS1117-class is ESR-DEPENDENT, not ceramic-stable.** Datasheet (Slkor
AMS1117 "1A Low Dropout Voltage Regulator", mirrored via Digikey media store,
https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8122/AMS11173.3SOT223.pdf,
p.5 "Output Capacitor"): "AMS1117 requires a capacitor from VOUT to GND to
provide compensation feedback... Typically, a 10uF tantalum or 50uF aluminum
electrolytic is sufficient. Note: It is important that the ESR for this
capacitor does not exceed 0.5 ohm." No ceramic option is qualified in the
vendor's own text - only tantalum/electrolytic. Input: 10uF tantalum
recommended (p.5). Min output current 3mA typ/10mA max (p.3 table,
1.5V<=(Vin-Vout)<=12V) applies to ALL variants (fixed and ADJ), not just ADJ.

**LM1117 (TI) is the same family, same trap, explicit ESR WINDOW.** TI
datasheet SNOS412Q (rev Jan 2023), https://www.ti.com/lit/ds/symlink/lm1117.pdf,
s.9.2.2.1.3 "Output Capacitor" (p.15): "The minimum output capacitance
required by the LM1117 is 10uF, if a tantalum capacitor is used... The ESR of
the output capacitor should range between 0.3 ohm to 22 ohm." A pure-ceramic
BOM (ESR often < 0.05 ohm) sits BELOW this window - the classic all-ceramic
oscillation trap. Input: "10-uF tantalum on the input is suitable for almost
all applications" (s.9.2.2.1.1, p.14). Min load current: table (p.6) lists
it ONLY against the ADJ variant (1.7 mA typ/5 mA max) - the FIXED-output
rows (1.8/2.5/3.3/5.0) list quiescent current instead, no min-load spec.
This differs from AMS1117 above, which specs min load on all variants -
verify per exact part, don't assume the family behaves uniformly.

**MIC29302A (Microchip/Micrel) is ESR-TOLERANT but WARNS AGAINST low-ESR
ceramic explicitly - the inverse trap.** Datasheet DS20005685A/MIC29302A
Rev 2.0 (Oct 2014), https://ww1.microchip.com/downloads/en/DeviceDoc/MIC29302A.pdf,
p.11 "Capacitor Requirements": "This capacitor need not be an expensive
low-ESR type; aluminum electrolytics are adequate. In fact, EXTREMELY
LOW-ESR CAPACITORS MAY CONTRIBUTE TO INSTABILITY. Tantalum capacitors are
recommended for systems where fast load transient response is important."
Stable with 10uF at full load; smaller currents allow smaller caps. When fed
from a high-AC-impedance source, add 0.1uF between IN and GND. Min load:
10 mA minimum "to swamp any expected leakage current" (p.11 "Minimum Load
Current") - applies regardless of fixed/adjustable.

**AP2114 (BCD Semiconductor / Diodes Inc) is genuinely ceramic-stable - a
CMOS-pass design, different compensation from the three bipolar/PNP parts
above.** Datasheet (BCD Semiconductor, "1A Low Noise CMOS LDO Regulator with
Enable AP2114", Prelim Rev 1.3 Oct 2010; original diodes.com URL 403'd,
retrieved via futureelectronics.com mirror
https://www1.futureelectronics.com/doc/BCD%20SEMICONDUCTOR/AP2114H-2.5TRG1.pdf),
p.1 Features: "Stable with 4.7uF Flexible Cap: Ceramic, Tantalum and Aluminum
Electrolytic." The electrical-characteristics table (p.6, AP2114-1.2 variant)
is measured with CIN = COUT = 4.7uF CERAMIC explicitly as the test condition
- confirms the ceramic claim is what the vendor actually characterizes
against, not just a features-page assertion.

**Cross-check (2 sources, load-bearing):** the ESR-window number for the
1117-class agrees across TI's LM1117 (0.3-22 ohm) and the AMS1117 clone's
implicit ceiling (<=0.5 ohm, no floor stated) - consistent enough to treat
"1117-class parts need tantalum/electrolytic ESR, not bare ceramic" as
settled. The ceramic-stable claim for AP2114 is corroborated by its own test
condition using ceramic caps throughout the electrical table, not just the
features bullet - two independent statements in the same document.

## 2. Thermal layout - copper area vs theta_JA (the load-bearing section)

**LM1117 gives an actual copper-area sweep - the most citable table found.**
TI SNOS412Q, s.9.5.1.1 "Heat Sink Requirements", Table 9-2 + Figures 9-11/
9-12 (pp.18-19). SOT-223 sweep is explicitly **1 oz copper**; TO-252 (DPAK)
sweep is explicitly **2 oz copper** (figure captions state this - the two
packages are NOT compared on the same copper weight).

SOT-223, 1 oz, TOP-SIDE COPPER ONLY:
| top area (in^2) | theta_JA (C/W) |
|---|---|
| 0.0123 (pad only) | 136 |
| 0.066 | 123 |
| 0.3 | 84 |
| 0.53 | 75 |
| 0.76 | 69 |
| 1.0 | 66 |

SOT-223, 1 oz, BOTTOM-SIDE COPPER ONLY (via-fed, 0 top): 0.2in^2->115,
0.4->98, 0.6->89, 0.8->82, 1.0->79. **Bottom-only copper is ~20% WORSE than
top-only copper at equal area** (79 vs 66 C/W at 1 in^2) - the tab solders
to the TOP layer; reaching the bottom layer costs via resistance. Split
top+bottom at equal total area lands between the two (e.g. 0.5+0.5 in^2 ->
70 C/W) but does not beat top-only. **Direct answer to "how much does a
2-layer bottom pour really buy": less than the same copper on top, by
roughly a fifth, for a non-exposed-pad package like SOT-223.**

TO-252 (DPAK), 2 oz, same layout grid: 1 in^2 top-only -> **47 C/W**; 1 in^2
bottom-only -> 57 C/W (same ~20% top-beats-bottom pattern). TO-252 at 2 oz
beats SOT-223 at 1 oz by a wide margin at any matched area (47 vs 66 C/W at
1 in^2) - partly package, partly the 2 oz vs 1 oz copper thickness TI chose
to characterize each package at (not an apples-to-apples package
comparison).

**MIC29302A states its headline theta_JA is conditional on a SPECIFIC
copper spec - not JEDEC 1 in^2.** Package Thermal Resistance table (p.3):
TO-263 (D2PAK) theta_JA = 28 C/W, TO-252 (DPAK) theta_JA = 35 C/W (no
copper area stated on that line). But the "Thermal Design" worked example
(p.10) states explicitly: "The maximum power allowed can be calculated
using the thermal resistance (theta_JA) of the D-Pak (TO252) adhering to
the following criteria for the PCB design: **2 oz copper and 100 mm^2
copper area** for the MIC29302A." 100 mm^2 = 0.155 in^2 - a much SMALLER
area than TI's 1 in^2 sweep point, yet MIC29302A's headline number (35 C/W)
already beats LM1117's TO-252-at-1-in^2 number (47 C/W) - consistent with
MIC29302A's D2PAK/DPAK-with-larger-die-and-lower-RthJC construction, not a
contradiction, but it means the two vendors' headline numbers are NOT
comparable without checking what each one actually assumed.

**AMS1117 clone datasheet gives only a single bare-minimum-pad number, no
sweep.** Slkor datasheet Abs Max Ratings (p.2): SOT-223 theta_JA = **150
C/W**, TO-252 = 125 C/W, SOT89 = 225 C/W, with PD max 600/900/400 mW
respectively - no copper-area statement at all, and 150 C/W is WORSE than
even TI's "pad only, 0.0123 in^2" data point (136 C/W) for the same
package, meaning this AMS1117 clone's headline number assumes even less
copper than a bare recommended land pattern, or a different (less
conservative) test methodology. **Do not use a vendor's single headline
theta_JA number to size this board's copper - use a copper-area sweep
(LM1117's) or an explicit stated criterion (MIC29302A's), and treat a bare
single number as a worst case, not a design target.**

**AP2114 gives NO theta_JA at all - only theta_JC (junction-to-case).**
BCD datasheet p.6: SOT-223 theta_JC = 50.9 C/W, TO-252-2 = 35 C/W,
TO-263-3 = 22 C/W, SOIC-8 = 74.6 C/W, PSOP-8 = 43.7 C/W. theta_JC excludes
the board entirely (die-to-tab only) - a design using AP2114 cannot size
board copper from the datasheet alone and must fall back to a generic
board thermal model or bench measurement. **Gap, not a decision - flag for
P2/P3.**

**Pipeline note (not a vendor citation - project fact):** this repo's
`check_thermal` gate already implements a first-principles copper-spreader
theta_JA model (not a lookup table) and was validated to within 5% of a
vendor JEDEC-board number elsewhere in this project (AP63356Q, 25.3 vs
25 C/W); the same investigation found board AREA dominates theta_JA more
than inner-layer copper weight for small boards (LEARNINGS.md 2026-08-09,
tag `check_thermal`/`thermal`/`stackup`). Relevant here because
`board_edit --outline fit` (P6/P7) will size this board's outline against
exactly that mechanism - the vendor tables above bound what "enough copper"
looks like, but the gate's own model is what actually scores the built
board.

## 3. Layout constraints

- **Input cap at the VIN pin, short leads** - stated by every source above
  (LM1117 p.14, AMS1117 p.5, MIC29302A p.11) as the baseline; none of the
  four datasheets calls out a hot-loop or Kelvin-sense requirement beyond
  this - linear regulators have no switch node, so the vendor layout
  sections are much thinner than a buck's (contrast `buck.md`'s five loop/
  FB-route entries).
- **Ground/tab topology differs by part and MATTERS for the copper pour
  design:** LM1117 and AMS1117 (3-pin SOT-223/TO-252, GND on the ADJ pin
  for fixed variants) have the **TAB = VOUT** (TI pinout figures 6-1..6-4,
  p.3: "Tab is VOUT"; AMS1117 pinout p.2 same convention) - the tab-side
  copper pour used for heatsinking IS the output net, and must be
  electrically isolated from any GND pour, not simply tied into it.
  MIC29302A (5-pin TO-263/TO-252, ADJ output) has **TAB = GND** ("GND: TAB
  is also connected internally to the IC's ground on both packages",
  p.2 Pin Description) - its heatsink copper can join the board's GND pour
  directly. This is a genuine part-class fork that affects whether the
  thermal copper is a "quiet" GND fill or a "hot" VOUT island needing
  isolation - confirm the specific chosen part's pinout before laying out
  the pour.
- **MIC29302A eval-board layout (p.14-15, its own PCB Layout
  Recommendations section)** places the input caps (ceramic + tantalum)
  and output caps (ceramic + tantalum) immediately flanking the IC on the
  top layer, with a dedicated PGND pour; no split analog/power ground shown
  (single-rail, no feedback-noise-sensitive stage on this simple board type
  unlike a buck).
- **ADJ/feedback divider placement** - MIC29302A explicit rule
  ("Adjustable Regulator Design", p.11): keep total (R1+R2) low enough to
  pass the 10 mA minimum load through the divider itself when the divider
  IS the only load path; AMS1117 (p.5) gives the same CADJ-bypass-impedance
  rule as LM1117 (`1/(2*pi*fRIPPLE*CADJ) < R1`). Not applicable if the
  chosen part is a FIXED-output variant (this board's `+/-3%` accuracy spec
  is satisfiable by a fixed part per requirements.md answer 5 - no external
  divider needed).

## 4. Errata / footguns

- **Dropout headline vs datasheet reality:** AMS1117 clone's own table
  (p.3) gives dropout 1.30V typ / 1.40V max AT 1A - noticeably worse than
  the ~1.1V figure commonly repeated online for "AMS1117". Always read the
  SPECIFIC manufacturer's table, not a generic AMS1117 blurb - the part
  name is used by many fabs with different dies (see counterfeit note
  below). At our board's 500 mA (half the tested 1A point) the curve
  (Typical Performance Characteristics, p.4) is well below 1.3V, but the
  datasheet does not tabulate a 500 mA point explicitly - only 1A is
  guaranteed-spec'd.
- **AP2114 dropout figures disagree between the features page and the
  electrical table I could access:** front page states "Low Dropout
  Voltage (3.3V): 450mV (Typ.) @ IOUT=1A" but the Electrical Characteristics
  table I retrieved (p.6) is for the **AP2114-1.2 variant** and shows
  VDROP typ/max = 1200/1300 mV at 1A - because at Vin=2.5V (that table's
  test condition) and Vout=1.2V, 1A load pushes the 1.2V part itself into
  dropout, so the two numbers are not directly comparable (different Vout
  variant, different test Vin). **Not cross-checked against the -3.3
  variant's own electrical table - flag as unconfirmed if AP2114 is
  selected; refetch the -3.3 table before relying on the 450 mV figure.**
- **Minimum load current is NOT uniform across the candidate class** - a
  cross-part inconsistency worth flagging given this board's "static
  resistive load" could plausibly sit near zero mA during bench idle:
  AMS1117 3mA typ/10mA max (all variants), MIC29302A 10mA min (all
  variants), LM1117 fixed-output variants have NO stated min-load
  (only the ADJ variant does, 1.7/5mA) - LM1117 fixed is the outlier that
  tolerates near-zero load; the other two do not.
- **Quiescent/ground current is not always flat vs load.** MIC29302A
  (PNP pass topology) ground current SCALES with output current - table
  (p.3): 5mA typ/20mA max at 750mA out, up to 60mA typ/150mA max at 3A out
  (roughly 2% of Iout, confirmed by the vendor's own PD formula "ground
  current is approximated by 2% of IOUT", p.10). AP2114 (CMOS pass) is the
  opposite: quiescent current is a near-constant 60uA typ regardless of
  load (p.6) - a genuine topology-driven difference in the input-current
  budget, not just a part-to-part number difference.
- **Thermal shutdown thresholds differ across the class:** AMS1117 150 C
  (10 C hysteresis, p.3), MIC29302A 125 C (used as TJMAX throughout its
  app-note math, p.10), AP2114 160 C (25 C hysteresis, p.6), LM1117 125 C
  recommended max junction (s.9.5.1.1, p.18: "junction temperature of the
  LM1117 must be within the range of 0C to +125C"). requirements.md
  section 4 assumed "~75 C/W or better for a 125 C part" - true for
  LM1117/MIC29302A but conservative (more margin available) if AMS1117 or
  AP2114's higher shutdown thresholds are used as the design ceiling
  instead; recommend still designing to 125 C Tj max regardless of the
  part's actual shutdown point, since shutdown itself is a fault response,
  not a steady-state operating target.
- **Counterfeit/clone variance is a real, citable risk specifically for
  AMS1117-class jellybean parts.** The "AMS1117" datasheet retrieved here
  is itself branded **Slkor**, not the original Advanced Monolithic
  Systems - it was the top hit for "AMS1117 3.3 SOT-223 datasheet" and
  is a second-source/clone die by construction. The part number is used by
  numerous fabs with non-identical dies; the thermal and dropout numbers
  above should be read as "this specific vendor's clone," not as a
  guaranteed property of any board-house-supplied "AMS1117" part. If
  AMS1117-class is selected, pin the exact manufacturer/part number in the
  BOM and do not assume datasheet numbers transfer across suppliers.

## Sources consulted

1. TI LM1117 datasheet SNOS412Q, rev Jan 2023 - https://www.ti.com/lit/ds/symlink/lm1117.pdf
2. Slkor AMS1117 datasheet (clone/second-source) - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8122/AMS11173.3SOT223.pdf
3. Microchip/Micrel MIC29302A datasheet Rev 2.0, Oct 2014 - https://ww1.microchip.com/downloads/en/DeviceDoc/MIC29302A.pdf
4. BCD Semiconductor AP2114 datasheet, Prelim Rev 1.3, Oct 2010 (mirror; diodes.com 403'd) - https://www1.futureelectronics.com/doc/BCD%20SEMICONDUCTOR/AP2114H-2.5TRG1.pdf
5. Project fact (not vendor): `LEARNINGS.md` 2026-08-09 `[check_thermal][thermal][stackup]` entry, this repo
