# refdesign-afe: bb-adc AFE topology research

Block: `afe` - 0-5 V single-ended input -> >=12-bit SAR -> 3.3 V-only domain,
0.1 % class (+/-5 mV @ 25 C, +/-12 mV over 0-50 C, at J1, uncalibrated).
Source <=1 kohm, board input impedance >=100 kohm at J1 (requirements.md Q9).

`reference/topologies/` contains only `buck.md` - nothing matches an AFE/ADC
block, so there is no prior topology note to extend; this is fresh research.
Sibling scouts' `research/adc.json` / `afe-support.json` were not read;
everything below is class-level, not tied to a specific shortlisted MPN.

## Bottom line

T2 (bare divider into the SAR) and T4 (host rail as VREF) both fail on
physics/arithmetic, not preference. T1 and T3 converge on the same real
circuit: attenuate, buffer, reference externally. The only real decision
T1-vs-T3 represents is **what the attenuator is made of** - two generic
0.1 % discrete resistors put the entire +/-12 mV over-temp budget at risk
from TCR MISMATCH alone; a tracked/matched attenuator (T3) makes that term
negligible. Reference and buffer selection are separate, additive budget
items under both T1 and T3.

## T1 - divider + buffer + external reference

Structure: resistive attenuator (5 V -> ADC FS) -> rail-to-rail precision
buffer -> SAR input; external reference (2.048/2.5/4.096 V class) -> SAR
VREF (+ its own buffer/bypass, see Reference section).

**Buffer is not optional, specifically because of Q9.** The divider IS the
block's input impedance at J1 - nothing else sits there. To read >=100 kohm
at J1 its legs must be ~100-150 kohm each for any sane divide ratio, so its
Thevenin resistance (R1||R2) is tens of kohm: two orders of magnitude above
what a SAR sampling node can settle against directly (T2). The buffer's job
is entirely to bridge that: high-Z in, low-Z fast out.

**Error budget, 25 C (estimate, part-class level, not a specific MPN):**
- Reference initial accuracy, 0.05-0.1 % class: 2.5-5 mV
- Divider ratio initial error, two 0.1 % resistors, worst case linear: up to
  7-10 mV (RSS ~5 mV) - drops with tighter tolerance or a trimmed network
- Buffer Vos, precision part: <1 mV. ADC offset/INL, decent 12-16 bit: 1-3 mV
- **Sum: can land inside +/-5 mV, but only with deliberately tight parts,
  not the loosest ones that meet resolution alone.**

**Error budget, 0-50 C (+/-25 C from a 25 C reference, standard TCR-spec
convention):**
- Reference tempco, 15-25 ppm/C class: 1.9-3.1 mV
- **Divider TCR MISMATCH, two untracked discrete 0.1 % thin-film resistors
  (typical catalog TCR 25-50 ppm/C each, untracked): worst-case mismatch
  50-100 ppm/C x 25 C = 1250-2500 ppm = 6.25-12.5 mV.** Can alone consume the
  whole +/-12 mV budget - a TOLERANCE spec bounds ratio at one temperature,
  it does not bound TCR TRACKING between two discrete parts from possibly
  different lots. This is the load-bearing footgun of a naive T1.
- Buffer/ADC drift: low single-digit mV combined.
- **Sum: MARGINAL TO FAILING on the divider term alone** unless the
  resistors are chosen/sourced specifically for tracking, not just
  tolerance - exactly what T3 buys structurally.

Sources: TI "Optimize Your SAR ADC Design" (Bonnie Baker),
https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/14/4478.PA_2D00_001--Optimize_5F00_SAR_5F00_converter_5F00_design-REV-b.pdf;
ADI "Front-End Amplifier and RC Filter Design for a Precision SAR ADC",
https://www.analog.com/en/resources/analog-dialogue/articles/front-end-amp-and-rc-filter-design.html;
TCR-vs-tolerance distinction (general precision-resistor practice): Electronics
Weekly, "How to: design guide for precision resistors",
https://www.electronicsweekly.com/news/products/passives/how-to-design-guide-for-precision-resistors-2009-08/
- the 25-50 ppm/C figure is catalog-level knowledge for 0.1 %-tolerance
thin-film resistors, an estimate, not a chosen part's spec.

## T2 - divider, no buffer - DISQUALIFIED (settling physics, not preference)

**Vendor equation (independently verified, see caution below).** TI SBAA173A
gives the SAR acquisition-time equation:

```
t_acq_min = (R_source + R_filt) x C_sample x ln(2^(N+1))
```

`ln(2^(N+1))` = time constants needed to settle to 1/2 LSB for N bits.
Evaluated: N=12 -> 9.0 tau, N=14 -> 10.4 tau, N=16 -> 11.8 tau. Source: TI
SBAA173A, https://www.ti.com/lit/an/sbaa173a/sbaa173a.pdf, Sec. 4 (minimum
acquisition time). CAUTION: an early automated fetch of this same PDF
mis-read the exponent (13, 15, 17) as if it were already the tau count,
skipping the ln(2)=0.693 multiply - re-derived by hand above; do not reuse
"13/15/17 time constants" as a number, it is wrong. Companion source: TI
SBAA256, "Driving a SAR ADC directly without a front-end buffer circuit",
https://www.ti.com/lit/SBAA256 - TI's own worked direct-drive case (their
ADS7056 example), confirming this is a recognized but boundary-constrained
technique, not a default.

**Worked example (labeled representative, not a specific chosen ADC).** A
representative 12-16 bit, <=10 kSa/s-class precision SAR: C_sample ~ 20-45
pF, minimum acquisition time ~350 ns-1.5 us (typical published range for
this class, estimate). Midpoint (30 pF, 700 ns, N=12):

```
Rs_max = 700e-9 / (30e-12 x 9.0) = ~2.6 kohm
```

A divider sized to present >=100 kohm at J1 (Q9) has Thevenin resistance in
the tens of kohm (legs ~100-150 kohm each) - roughly 10-20x over this limit.
**This is a settling failure, not just an accuracy shortfall**: the sampling
cap does not reach 1/2 LSB inside the acquisition window, so codes are wrong
before any reference/offset/drift term is even considered.

**The 10 kSa/s ceiling does not rescue this.** Common misreading: acquisition
time is fixed by the ADC's internal SCLK-count timing per conversion,
independent of how rarely conversions are triggered - idling longer between
conversions does not lengthen any single acquisition window. Some parts allow
stretching acquisition via external CONVST hold, but that trades RC settling
error for sampling-cap droop from leakage during the longer hold - not a
free escape hatch.

**The stated conflict, confirmed:** T2 needs Thevenin source Z in the low
single-digit kohm to settle; Q9 needs the board to present >=100 kohm at J1.
A plain two-resistor divider cannot satisfy both - this is exactly why
T1/T3 (divider PLUS buffer) exist: the buffer reconciles "high-Z to the
source" with "low-Z to the SAR."

ERROR BUDGET SKETCH: not meaningful - functional failure precedes it.

## T3 - integrated precision attenuation

Two sub-options, both solving T1's TCR-tracking footgun differently:

**T3a - integrated difference amp / ADC driver, AD8275-class.** AD8275:
G=0.2 laser-trimmed difference amp, gain drift 1 ppm/C MAX, CMRR 80 dB,
settling 450 ns, internal matched/trimmed resistors so ratio AND tempco
tracking are both done on-die. MSOP-8. Source: AD8275 datasheet Rev. B,
https://www.analog.com/media/en/technical-documentation/data-sheets/AD8275.pdf;
product page https://www.analog.com/en/products/ad8275.html. Listed on LCSC
(AD8275ARMZ, C462177), so at least orderable through the JLC supply chain;
assembly tier is a component-scout/BOM question, not resolved here.
**What it costs, specifically here:** AD8275's G=0.2 is sized for +/-10
V-class instrumentation inputs -> ~0-4 V, not a 0-5 V unipolar input into a
3.3 V-domain SAR. Used as-is (0-5 V x 0.2 = 0-1 V) it wastes dynamic range
against a 2.5-3.3 V reference - roughly 1.3-1.7 effective bits given away.
The CLASS is right; this specific ratio is not a clean fit - look for the
same class nearer 0.5-0.66, or accept the cost, or use T3b. Mode-tension flag
(not resolved here): requirements.md Sec. 6 names only "the converter" and "a
precision voltage reference" as allowed Extended-tier when Basic stock is
thin, not an attenuator/level-translator IC - if the winning part is
thin-stocked, that is a BOM-policy call for the architect, analogous to the
second-rail tension already flagged in Sec. 1.

**T3b - matched resistor network + separate buffer, LT5400-class.** LT5400:
quad matched resistor network, matching 0.01 % (A grade) / 0.025 % (B
grade), TEMPERATURE TRACKING 0.2 ppm/C TYPICAL (the match BETWEEN the
resistors, not either one's absolute TCR), <2 ppm long-term drift/2000 hr,
MSOP-8, rated +/-75 V. Source: LT5400 datasheet,
https://www.analog.com/media/en/technical-documentation/data-sheets/5400fc.pdf.
Ratio stays fully choosable (wire the four resistors as needed) at the cost
of still needing a separate buffer (own Vos/drift/CMRR budget, as T1) and
still needing the external reference (as T1/T3a) - T3b removes only the
divider-TCR-mismatch risk, nothing else.

**Error budget, over 0-50 C (+/-25 C convention, either sub-option):**
- Attenuator tempco: AD8275 1 ppm/C x 25 C = 25 ppm = 125 uV. LT5400
  0.2 ppm/C x 25 C = 5 ppm = 25 uV. Either way, negligible - drops out.
- Reference tempco (still required, as T1): 1.9-3.1 mV at 15-25 ppm/C.
- Buffer (T3b only) / ADC drift: low single-digit mV.
- **Sum: comfortably inside +/-12 mV, with margin left over** - unlike naive
  T1, the attenuator no longer eats most of the over-temp budget.
- 25 C sum: similar to T1 (reference + buffer + ADC dominate); attenuator's
  contribution is now trimmed initial gain error, well under 0.1 %.

## T4 - ratiometric, VREF = 3.3 V host rail, no external reference - DISQUALIFIED

Clean negative result. Requirements.md Q7 (ANSWERED, now a requirement):
host rail is 3.3 V +/-5 % (3.135-3.465 V) with "tens of mV noise." Two
independent, either-alone-sufficient disqualifiers:

1. **DC tolerance.** +/-5 % of a 3.3 V-referenced full scale is +/-165 mV
   (+/-250 mV referred to the 5 V input span) - 20-50x the +/-5 mV(25 C) /
   +/-12 mV(0-50 C) budget, before any other error source.
2. **Noise floor.** "Tens of mV" of rail noise alone, ignoring DC tolerance
   entirely, is already 6-10x the 25 C budget.

**Why "ratiometric" thinking does not rescue this.** True ratiometric
cancellation needs the SAME rail to excite the sensor AND serve as the ADC
reference, so the rail's error cancels in the ratio (numerator/denominator).
This board's input is an INDEPENDENT external 0-5 V source unrelated to the
3.3 V rail - using the rail as VREF here is not ratiometric measurement, it
is "reference with 5 % uncorrected tolerance," which fails on arithmetic
alone. Source: Jason Sachs, "Tolerance Analysis",
https://www.embeddedrelated.com/showarticle/1353.php (states the
shared-excitation requirement for cancellation; otherwise reference
variability is a direct accuracy driver). NOTE: TI has a directly-titled app
note, "Ratiometric Data Acquisition of Remote Sensors" (SBOA628,
https://www.ti.com/lit/an/sboa628/sboa628.pdf), found in search results but
its PDF did not parse through the fetch tool - NOT used as a source for any
number above; the disqualification rests entirely on the board's own
answered Q7 tolerance plus arithmetic, which needs no external citation.

No rescue path inside `block-only` scope: one channel, no way to
independently measure the rail to calibrate it out - adding one is just T1's
external reference again under a different name.

ERROR BUDGET SKETCH: +/-165 to +/-250 mV DC alone, both temperatures - fails
by more than an order of magnitude before drift is even considered.

## ADC input drive / RC network (cross-cutting)

- Settling equation (verified above): `t_acq_min = (Rs + Rfilt) x Csample x
  ln(2^(N+1))`. Source: TI SBAA173A Sec. 4.
- Standard buffered topology: small series isolation R (10-50 ohm class) plus
  a local cap AT the ADC input pin - the cap is the charge reservoir for the
  sampling transient, the series R isolates the buffer's output stage from
  the ADC's switched capacitive load so the buffer stays stable (unbuffered
  RC straight off an op-amp output can ring or fail to close loop gain into
  a hard capacitive load). Worked vendor example: ADA4807-1 (180 MHz) driving
  a 16-bit, 1 MSPS SAR with Rext=20 ohm, Cext=2.7 nF - far faster than this
  board's 10 kSa/s ceiling needs, so bandwidth/settling margin here is
  generous; the real constraint on this board is precision (offset, drift,
  Ibias), not speed. Source: Digikey, "Analog Basics-Part 5: Tackling
  Difficult Input Driving Issues for the SAR ADC",
  https://www.digikey.com/en/articles/analog-basics-part-5-tackling-difficult-input-driving-issues-for-the-sar-adc.
- Why unbuffered/badly-buffered drivers fail to settle: charge injected back
  onto the source by the SAR's own sampling switch ("kickback") must
  re-settle within the acquisition window; too little bandwidth/too much
  output impedance means it doesn't, corrupting that conversion. Source: ADI
  MT-021, "ADC Architectures II: Successive Approximation ADCs",
  https://www.analog.com/media/en/training-seminars/tutorials/MT-021.pdf.

## Buffer amplifier selection rules (T1/T3b)

1. Settle to within 1/2 LSB of target resolution inside the acquisition
   window (same equation/tau counts above, applied to the amplifier's own
   settling spec rather than a passive RC).
2. Stable driving the ADC's capacitive load - via the series isolation R
   above, not by omitting it.
3. **Rail-to-rail OUTPUT does not mean rail-to-rail AT LOAD.** No real output
   stage reaches the literal rail; headroom shrinks further under load
   current, and gain/linearity degrade within roughly 50-200 mV of either
   rail as output transistors approach saturation. If this block's full
   scale sits near 0 V or near the amp's positive rail, verify margin at the
   actual load, not just the "rail-to-rail" claim. Sources: EDN, "What does
   'rail to rail' output operation really mean?",
   https://www.edn.com/what-does-rail-to-rail-output-operation-really-mean/;
   ADI, "Rail-to-Rail: Railroading and the Electronics of Op Amps",
   https://www.analog.com/en/resources/technical-articles/railtorail-railroading-and-the-electronics-of-op-amps.html.
4. **Input bias current class matters more here than usual**, because it
   multiplies against the divider's Thevenin resistance (tens of kohm,
   forced by Q9). Standard bipolar input (Ibias tens-hundreds of nA) at
   50 kohm: 100 nA x 50 kohm = 5 mV alone - the entire 25 C budget. A
   CMOS/JFET precision part (Ibias pA-class) at the same 50 kohm: negligible.
   A hard buffer-class constraint, not a nice-to-have. Source: ADI MT-038,
   "Op Amp Input Bias Current",
   https://www.analog.com/media/en/training-seminars/tutorials/MT-038.pdf.

## Reference decoupling and reference drive

- SAR reference pins draw a large, fast charge-transfer current once per
  conversion ("reference kickback"); most SAR ADCs specify a bulk/bypass cap
  in the 1-22 uF range at the reference pin as the charge reservoir.
- Must re-settle to within the ADC's resolution before the NEXT conversion,
  not just once at power-up, and more demanding as resolution rises. A
  buffer is needed when the reference IC's own output impedance/bandwidth
  can't re-settle the bulk cap in time; for >16-bit parts vendor material
  cites reference-buffer output impedance as low as 50 milliohm needed. This
  board's 12+ bit target is less demanding but the mechanism is the same -
  check against whichever specific ADC + reference land here.
- Power-up settling: a low-pass-filtered reference can settle meaningfully
  slower at power-up than while already running - relevant because this
  board's ONLY supply (3.3 V from the host) arrives at board power-up, so
  first-conversion validity after power-on should be checked, not assumed.
  Source: ADI, "Successive-Approximation ADCs: Ensuring a Valid First
  Conversion", https://www.analog.com/en/resources/analog-dialogue/articles/successive-approximation-adcs.html.

## Layout notes (feed P6/P7 directly)

- Reference bypass cap within ~0.1 in (2.5 mm) of the reference pin, short
  low-inductance connection (target <2 nH), SAME layer as the ADC (no via
  between pin and cap); each reference/ground pin pair gets its own return,
  not shared through a via field. Source: TI Precision Hub, "SAR ADC PCB
  Layout: The reference path",
  https://e2e.ti.com/blogs_/archives/b/precisionhub/posts/sar-adc-pcb-layout-the-reference-path.
- Partition analog/digital regions with a solid ground plane under the ADC;
  keep the SPI clock especially short and isolated from other digital AND
  from the analog input/reference nodes - clock edges are the fastest,
  most coupling-prone signal here. Cross analog/digital traces at 90 degrees
  where they must coexist; for a high-resolution target, prefer not crossing
  at all. Source: TI Precision Hub (above) + ADI, "Design Reliable Digital
  Interfaces for Successive-Approximation ADCs", https://www.analog.com/en/resources/analog-dialogue/articles/design-reliable-digital-interfaces.html.
- Guard the high-impedance divider/attenuator node: a guarded, solder-mask-
  relieved ring at the sensed node's own potential around the divider
  mid-point trace and ADC input pin, breaking surface leakage paths from
  flux/dust/moisture before they reach it. Source: Microchip, "Leakage
  Currents", https://developerhelp.microchip.com/xwiki/bin/view/products/amplifiers-linear/operational-amplifier-ics/precision-design/leakage-currents/.
- J1 entry: route signal and return from the board edge straight to the
  divider/attenuator, minimal shared path with any digital return current -
  the 100 kohm-class input impedance here is far more leakage/coupling-
  sensitive than a typical signal, so it should not share a return or run
  adjacent to J2's digital lines (consequence of the two connectors on
  different edges, already assumed in requirements.md Sec. 5).

## Errata / footguns

- **Divider TCR mismatch (T1-naive), not divider TCR itself.** Detailed
  above - a 0.1 % tolerance spec does not bound temperature TRACKING between
  two discrete resistors. The single most decision-relevant footgun found.
- **Buffer input bias current x divider Thevenin resistance.** Detailed
  above - fixes the buffer's required input-current CLASS once the
  divider's Thevenin resistance is set by Q9.
- **Surface/flux leakage into the high-Z divider node.** JLCPCB's default
  assembly has no board-wash step; no-clean flux residue, dust, and humidity
  can create leakage paths competing with the divider's own currents at the
  100 kohm scale. Guard ring (layout notes) and/or a post-assembly clean
  mitigate it - a real risk at this board's forced impedance, not a generic
  caution. Source: same Microchip leakage-currents page.
- **Reference re-settling per conversion, not just at power-up** - detailed
  above; check against the specific ADC+reference pairing once chosen.
- **Self-heating of the divider resistors: CHECKED, does NOT apply here.**
  Flagged since the task named it as a candidate footgun. A divider sized to
  >=100 kohm at 5 V full scale dissipates V^2/R = 25/100000 = 250 uW or
  less - negligible self-heating-driven TCR error at this impedance. Real
  concern for a low-impedance Kelvin-sense divider, not this one, precisely
  because Q9 forces high impedance. Recording the negative finding so it
  isn't silently re-raised later as a generic worry that doesn't apply.
- **Open risk, not yet a footgun:** whichever ADC gets shortlisted needs its
  OWN minimum-acquisition-time and C_sample checked against the T2 formula
  above before final buffer/RC values are set - the numbers used above are
  explicitly representative/estimated, not the chosen part's real numbers.
