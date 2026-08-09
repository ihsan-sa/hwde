# ERC / schematic-review waivers - sbuck-5v3a P4

ERC gate: **0 errors, 0 warnings** (kc.py erc, exit 0).
Schematic review (fresh context): **0 errors, 7 warnings**. No netlist change was
required by any finding. Full detail: `reports/review-schematic.md` + `.json`.

Two warnings were FIXED rather than waived (see below). Five are waived here.

---

## FIXED, not waived

**F1. DNP snubber overstressed its own resistor.** C*V^2*fsw = 162 mW at 18 V and
338 mW at the declared 26 V ring, into an 0603 rated 0.1 W. A DNP footprint that
destroys itself when populated is a trap, not a feature. Fixed: R9 0603 -> 1206
(>= 0.25 W), C16 1 nF X7R -> 470 pF C0G 1206. New figures 76 mW at 18 V, 159 mW at
26 V. Both values stay inside the documented 10-33 ohm / 470 pF-2.2 nF bring-up
range from blocks.md B9.

**F2. Loop calibration claim withdrawn.** P4 claimed its model was validated against
the vendor Bode plot ("PM 79-84 deg vs published 81.6"). The reviewer read Fig.29
and found the plotted circuit HAS C4 = 33 pF fitted, so the comparison used the
wrong model variant. The x0.83 realisation factor is therefore unevidenced. The
claim is withdrawn from the record; the design is re-stated on its worst reading.

---

## WAIVED

**W1. Loop phase margin is less certain than P4 claimed.**
Reviewer's independent re-derivation reproduces P4's fc/PM/|T| table to the digit,
so the arithmetic is right; what fails is the calibration against the vendor plot.
Worst-case reading gives PM ~46-53 deg against the >= 45 deg requirement.
*Waived because*: it still meets requirement on every reading, and the vendor's own
published GM (-26.8 dB) matches neither model variant (-8.3 with feedforward, -18.4
without), i.e. the vendor's "first-order calculated" model carries HF poles that no
reader-built model reproduces. Closing this needs a real loop measurement or the
vendor's own model - not more reading. **Carried to P8 as a bench item.**

**W2. Load step: 148 mV modelled, 200 mV on the corrected reading - AT the limit.**
SUPERSEDED TWICE, and the honest number got worse each time. The first restatement
(181 mV) still carried the withdrawn 0.83 factor. Re-running the vendor comparison
like-for-like - model WITH C4=33pF and C6=47pF fitted, matching the circuit actually
plotted in Fig.29 - gives a factor of 0.743, not 0.83, and the model is optimistic on
all three axes (fc +35%, PM +19.4 deg, GM +18.5 dB). Applying those offsets:
**dV = 200 mV against a 200 mV limit.** Additionally the 0->3 A step STARTS IN PFM
(automatic PWM/PFM, no MODE pin) which the CCM model does not describe.

*Waived - as an at-limit DISCLOSURE, not a pass* - because:
1. **No R5 value clears all three targets.** Measured sweep, recorded in root.py s2.5a
   so the "just raise R5" reflex is answered in the source: 75k -> PM 45.6 deg / dV
   200 mV; 82k -> PM 44.1 deg FAIL / dV 183 mV; 91k -> PM 39.9 deg FAIL / dV 165 mV.
   Raising fc buys sampling-pole lag. 75k is the only value that keeps phase margin -
   the binding requirement - above its floor.
2. **Adding output capacitance does not help.** fc scales as 1/COUT at fixed
   compensation, so fc*COUT is constant and dV = dI/(2*pi*fc*COUT) is INVARIANT in
   COUT. Buying more caps would be pure cost for zero transient improvement.
3. **It is not a measurement.** It extrapolates a one-point vendor calibration, taken
   at a different operating point, onto a different circuit. It is a plausibility
   band, not a second reading.
4. **The dominant uncertainty is larger than the shortfall.** The COUT derating band
   is +/-13% around its mean with no vendor DC-bias curve behind it.
5. **Re-tunable without a respin**: R5, C2 and C3 are three adjacent 0603 parts.

**Carried to P8 and to bring-up as the board's #1 bench item.**

**W2a. The fc floor of 24.4 kHz is NOT a requirement miss.** The "fc 25-50 kHz"
target was the ORCHESTRATOR's proxy, written into the P4 spawn prompt as a stand-in
for the real requirement, which is "recovery within 100 us". At fc = 24.4 kHz
settling is 5/(2*pi*fc) = **32.6 us, a 3.1x margin on the 100 us spec**. The proxy
was simply stricter than the requirement it stood for. Recorded so that no later
phase re-litigates a 2.4% miss against a number that was never the spec.

**W3. Hot-plug inrush peak cannot be bounded from published data.**
The 57 A figure comes from the 0.30 ohm path row; the 26 V node rating comes from
the 0.05 ohm row of the same table, which assumes an ALL-CERAMIC Cin. At 0.10 ohm
the formula gives 180 A against Q1's -60 A channel IDM.
*Waived because*: this board deliberately does NOT have an all-ceramic Cin - C4
carries 80 mOhm ESR as a stated DAMPING requirement - so the 0.05 ohm row is not
this configuration. The 26 V declaration is kept anyway as conservative headroom for
part ratings. Residual and honest: AO4407A's body-diode single-pulse capability is
not published, and screw terminals are a wire-then-power connector, not a hot-plug
one. **Recorded in DECISIONS.md as an accepted, quantified risk.**

**W4. Q1 gate dv/dt immunity is unbounded.** parts/C16072.json publishes Qg and Rg
but no Ciss/Crss/Coss for the AO4407A.
*Waived because*: the datum does not exist in the sourced datasheet, so no analysis
can close it. Stated as a limit of knowledge rather than assumed benign.

**W5. UVLO effective anti-motorboating margin is 0.32 V, not the 0.41 V argued at
P2** (the fuse and FET drops were omitted from that argument).
*Waived because*: the margin is still POSITIVE, and the raw hysteresis (0.905 V,
VON 6.230 / VOFF 5.325, verified exactly against the vendor's pull-up-inclusive
Eq.2/3) comfortably exceeds the 0.49 V cable drop that motivated the P2 override.
Worst-case VON 6.67 V sits 0.33 V below the 7.0 V minimum input, so the converter
starts across its whole rated range.

---

## Non-violations the reviewer flagged for the record

- **The clean ERC is weak evidence for U1.** Nearly every U1 pin is declared
  `passive` in the pulled library, so ERC structurally cannot catch a mis-wired IC
  pin here. The real pin-level evidence is the datasheet-extract cross-check plus
  the reviewer's independent netlist read. Do not cite "ERC 0/0" as pinout proof.
- The schematic plot is stub-label style, so bring-up needs the netlist alongside it.
- **Silkscreen connector labelling is unreachable from a schematic generator** but is
  delegate Q30's ONLY mitigation for a swapped input/output connection (both
  terminals are identical 5.08 mm 2-pin parts). **Carried to P6/P8 as a tracked
  requirement so it cannot die in a P4 note.**

## Unresolvable from sourced data (stated, not assumed away)

- No vendor DC-bias curve exists for ANY MLCC on this board, so the [75.0, 96.8] uF
  COUT band - and therefore every loop number above - rests on conventional
  estimates. This is why COUT was closed over a band rather than a point.
- No datasheet exists for D1 (KT-0805G), so Vf = 2.8 V is unverified. Bracketed:
  0.82-1.36 mA over any plausible green Vf. Outcome is insensitive.
- No vendor snubber value is published by any of the three candidate ICs.
- FB input bias current is unpublished (irrelevant at a 40 uA divider current).
