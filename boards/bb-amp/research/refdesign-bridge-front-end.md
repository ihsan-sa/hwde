# refdesign-bridge-front-end - bb-amp

Block: bridge-sensor front end, single 3.3 V supply, 350 ohm bridge, 0-20 mV in,
gain ~150-165 V/V, pedestal ~0.1 V, flat to 1 kHz (~1%), 12-bit usable after
calibration. No topology doc exists in `reference/topologies/` for this block,
so this file covers the whole topology, not a delta. TOPOLOGY DECISIONS with
citations only - no schematic, no part selection (component-scout's job).

## Sources (primary unless flagged)

| Tag | Document | URL |
|---|---|---|
| [TI-INA333] | TI, *INA333 Micro-Power, Zero-Drift In-Amp*, SBOS445C, Jul2008-rev Dec2015 | ti.com/lit/ds/symlink/ina333.pdf |
| [TI-INA828] | TI, *INA828 50-uV Offset, 7-nV/rtHz In-Amp*, SBOS792A, Aug2017-rev Jan2018 | ti.com/lit/ds/symlink/ina828.pdf |
| [TI-TIDUB00] | TI Designs, *Single-Supply Strain Gauge Bridge Reference Design*, Claycomb, Nov2015 | ti.com/lit/pdf/tidub00 |
| [TI-SBOA247] | TI, *Analog Eng. Circuit: Single-Supply Strain Gauge Bridge Amp*, SBOA247A, rev Apr2023 | ti.com/lit/pdf/sboa247 |
| [TI-SBOA356] | TI, *Cascading Precision Op Amp Stages for Optimal AC/DC Performance*, Olson, Aug2020 | ti.com/lit/pdf/sboa356 |
| [ADI-AD8237] | Analog Devices, *AD8237 Micropower, Zero-Drift, True Rail-to-Rail In-Amp*, Rev.0, 2012 | analog.com/media/en/technical-documentation/data-sheets/ad8237.pdf |
| [ADI-REFPIN]* | ADI article, *Drive the REF Pin ... Without an Op Amp* (MAX4194 vs MAX9922 comparison) | analog.com/.../drive-the-ref-pin-of-new-generation-instrumentation-.../ |
| [ADI-AD8221]* | Analog Devices, *AD8221* datasheet, RFI-filter section | analog.com/media/en/technical-documentation/data-sheets/ad8221.pdf |

`*` = repeated analog.com fetch timeouts left only a search-engine paraphrase
of these two; corroboration only, never sole support for a load-bearing
number. Every load-bearing number below rests on a full-text-read [TI-*] or
[ADI-AD8237] source.

---

## 1. The canonical single-supply bridge front end

**D1. Vendors build this as: bridge -> one monolithic in-amp -> REF pin sets
the pedestal -> single-ended output.** No discrete front-end op-amp in the
shipped reference designs. TI drives the bridge straight into an INA333, REF
from a precision reference, single RG sets gain [TI-TIDUB00 s2-3, Fig.2/A-1].
TI's "Analog Engineer's Circuit" builds the same function from two op-amps
instead of a monolithic part, but the topology is identical [TI-SBOA247 p1] -
build from this shape whether the final part is monolithic or discrete.

**D2. A resistor from the bridge's low side to ground (or a matched pair) both
limits bridge current and centers the in-amp's common-mode inside its linear
range - not optional, it is how every cited design keeps the diamond-plot
swing budget (s6) usable.** [TI-TIDUB00]: R4=0, R5=1.27k pulls Vcm to ~2.4V on
a 5V rail ("Vcm of 1.5V to 3.5V produces the largest possible output voltage
swing"). [TI-SBOA247] design notes 3,6: "R8 and R9 set the common-mode voltage
... and limit the current through the bridge." [TI-INA333] Fig.35
"Single-Supply Bridge Amplifier" (3V rail): series R1 "creates proper
common-mode voltage, only for low-voltage operation." bb-amp's bridge already
sits at ~1.65V CM by design (own 3.3V excitation, shared ground - Q1), so this
board doesn't need the resistor to CREATE the CM point, but the same cited
mechanism is why the input network still needs deliberate current/CM control.

**D3. Gain: one external resistor for a classic monolithic in-amp**
(`G=1+100k/RG` [TI-INA333]) **or two ratio-matched resistors for an ICF
part** (`G=1+R2/R1` [ADI-AD8237 Table 7]) - a separate pair from, with
different matching rules than, any REF-divider pair (s2).

---

## 2. The REF/pedestal mechanism - load-bearing, cross-checked

Decides whether bb-amp needs a second active part (a REF buffer).

**D4. Classic (3-op-amp-derived) monolithic in-amps: REF MUST be low-impedance.
Stated as an operating requirement, not a suggestion, identically across two
TI parts:** [TI-INA333] Pin Functions: **"This pin must be driven by low
impedance or connected to ground."** Section 8.2: **"This connection must be
low-impedance to assure good common-mode rejection. Although 15 ohm or less of
stray resistance can be tolerated ... small stray resistances of tens of ohms
in series with the REF pin can cause noticeable degradation in CMRR."**
[TI-INA828] Pin Functions: **"This pin must be driven by a low impedance
source"** (its own REF R_IN=40k describes the pin's input impedance, not the
tolerable source impedance - that's the 15-ohm figure above).

**D5. ICF in-amps: REF is high-impedance by construction; a bare divider does
NOT degrade CMRR.** [ADI-AD8237] "Using the Reference Pin" (verbatim):
**"Traditional instrumentation amplifier architectures require the reference
pin to be driven with a low impedance source. In these traditional
architectures, impedance at the reference pin degrades both CMRR and gain
accuracy. With the AD8237 architecture, resistance at the reference pin has no
effect on CMRR."** Gain compensates instead: `G=1+(R2+R3||R4)/R1` with a bare
divider shown driving REF directly (Fig.72). Spec table confirms the
mechanism: REF differential/CM impedance is specified at the same
**100 Mohm||5pF / 800 Mohm||10pF** level as the signal inputs (footnote:
"Valid for REF and FB pair, as well as +IN and -IN") - orders of magnitude
above the "tens of ohms" that perturbs a classic REF.

**D6. Cross-check (two vendors, full text): TI's classic-derived family
(INA333, INA828) states the low-Z REF requirement identically; ADI's ICF
family (AD8237, same architecture as AD8420) states the opposite and explains
why (REF/FB compared inside the loop at matched common-mode via the ALS
technique, not summed through an external divider) - a search-paraphrased ADI
article corroborates the same split but is not load-bearing [ADI-REFPIN]*.
Consequence: bb-amp's ~0.1V pedestal is a real node feeding REF - a classic
in-amp needs an active low-Z REF driver (buffer op-amp or a reference IC, as
in [TI-TIDUB00]'s REF5025), likely justifying a second active part; an ICF
part needs only a divider off 3.3V. Scope-relevant fork - flag for P2.**

---

## 3. Gain-bandwidth reality at G~150-165, corner ~7 kHz

**D7.** Board math (requirements.md s9a): 1% droop at 1kHz on a single real
pole puts -3dB at ~7kHz; at gain 150-165 that needs ~1MHz gain-bandwidth in
the gain path.

**D8. The lowest-power zero-drift/chopper in-amp is disqualified by
bandwidth, not precision.** [TI-INA333] Frequency Response: **BW(-3dB)=150kHz
@G=1, 35kHz @G=10, 3.5kHz @G=100, 350Hz @G=1000.** At G~150-165, bandwidth is
well under 3.5kHz - roughly half the 7kHz target, before any margin. Yet its
DC precision is exactly what this board wants: **"Low Drift: 0.1 uV/degC,
G>=100"** - over 0-50degC that's ~5uV, i.e. it alone would consume roughly the
board's entire ~5uV RTI budget (requirements.md s9a) before CMRR/noise are
added. **Central tension: the part with the wanted drift lacks the needed
bandwidth; the part class with the bandwidth isn't the low-drift one (D10).**

**D9. An ICF zero-drift part gets close but is marginal, and needs a strapped
pin to get there.** [ADI-AD8237] "Architecture": **"For gains >= 10, the
bandwidth mode pin (BW) can be tied to +VS ... increase the gain bandwidth
product ... to 1 MHz. Otherwise, connect BW to -VS for a 200 kHz [GBW]."**
Table 2 (VS=5V, high-BW mode): 100kHz@G=10, 10kHz@G=100, 1kHz@G=1000
(~1MHz GBW, consistent). At G~150-165 that interpolates to **~6-6.7kHz** -
under the 7kHz target with zero margin, and only with BW correctly strapped to
+VS (wrong strap = 5x worse). Also chops internally (~27kHz ALS clock) - not
all zero-drift parts are low-bandwidth (contrast D8), but chopping brings the
ripple footgun of E6.

**D10. A non-zero-drift, wideband precision in-amp clears bandwidth easily but
may blow the drift budget alone.** [TI-INA828]: BW(-3dB)=2.0MHz@G=1,
640kHz@G=10, 260kHz@G=100, 33kHz@G=1000; interpolating to G~150-165 gives
**~160-180kHz** (>20x margin). But input-stage offset drift is **0.5uV/degC
typ** - over 0-50degC that's ~25uV, ~5x the board's whole ~5uV RTI budget.
TI's own bridge design anticipates this exact fork: **[TI-TIDUB00] s7.3:
"Other instrumentation amplifiers can be used... the INA188 for a low drift
solution, the INA827 for applications that require a higher bandwidth, or the
INA122 for a lower power solution with higher gain."** TI names bandwidth vs.
drift as the same substitution axis this block sits on. Whether INA828-class
drift is acceptable once P2's full RSS/calibration budget is run is a
P2/component-scout question - flagged OPEN.

**D11. Where vendors put gain when one in-amp can't do both: split it, MOST of
the gain in the first (precision) stage, pedestal injected at the LATER
stage.** [TI-SBOA356] gives the rule with an equation: two-stage offset
`Voso = Vosi1*(GA1*GA2) + Vosi2*GA2` (Eq.3) - **"the Vosi of the first op amp
is amplified by the gain of the entire system. The Vosi of the second op amp
is amplified only by the gain of the second stage."** Rule of thumb, quoted:
**"design for most of the gain to be applied in the first stage... this
ensures most of the output noise and Voso is due to the first op amp stage."**
Quantified (Table 7-1, same 1000V/V total, 2nd stage 100x worse device):
input-referred offset std-dev grows from **5.15uV (G1=200,G2=5) to 25.06uV
(G1=10,G2=100)** as gain shifts to the back stage - ~5x worse for identical
total gain. Pedestal placement: [TI-SBOA247]'s 2-stage circuit injects Vref at
the SECOND (gain) stage through a ratio-matched network (design note 7: "R1
must equal R3 and R2 must equal R4" to avoid degrading CMRR) - keeps the
pedestal off the limited-swing first stage and lets its own matching cost land
on the stage with margin to spare.

**Unresolved tension (flagged, not closed here):** SBOA356's front-loaded-gain
rule fights `BW=GBW/Gain` for a zero-drift front end - more front-end gain
eats its own bandwidth first. Vendor-shown escapes: (a) non-chopper high-GBW
first stage takes most of the gain (D10's drift risk), or (b) modest
front-end gain keeps bandwidth over 7kHz, rest of gain in stage 2 (smaller
drift penalty, scaled 1/GA1 per D11). P2 sizing call, needs a specific pair.

---

## 4. Input network - required vs. optional at `block-only`

**D12. REQUIRED by every cited datasheet: a DC return path for input bias
current.** [TI-INA333] s8.2.2.5: **"The input impedance ... is extremely high
- approximately 100 Gohm. However, a path must be provided for the input bias
current of both inputs ... Without a bias current path, the inputs float to a
potential that exceeds the common-mode range ... and the amplifiers will
saturate."** [ADI-AD8237] "Input Bias Current Return Path": **"The input bias
current ... must have a return path to ground. When the source ... cannot
provide a return current path, create one."** Both vendors: correctness
requirement, not conditioning - IN SCOPE. bb-amp's J1 3rd pole (GND, tied to
the bridge's excitation return, Q2) IS that return path - confirming the
brief's own reasoning.

**D13. RFI/EMI input RC filtering is OPTIONAL for parts that already filter
on-chip.** [TI-INA333] s10.1: **"the INA333 ... incorporating passive RC
filters with an 8-MHz corner frequency at the VIN+ and VIN- inputs ...
demonstrates remarkably low sensitivity ... Strong RF fields may continue to
cause varying offset levels ... and may require additional shielding."**
[ADI-AD8237]: **"contains an on-chip RFI filter that is sufficient for a
majority of applications. For applications where additional ... immunity is
needed, an external RFI filter can also be applied,"** with equations for the
OPTIONAL network: `f_diff=1/(2*pi*R*(2Cd+Cc))`, `f_cm=1/(2*pi*R*Cc)`, worked
R=10k 1%, Cc=1nF 5%, Cd=10nF. CMRR consequence of a mismatched filter
(search-paraphrased, [ADI-AD8221]*): R*Cc mismatch between + and - inputs
degrades CMRR, mitigated by Cd ~10x Cc. Both candidate families already carry
sufficient on-chip filtering, so an ADDED external RC network is conditioning
the datasheet doesn't require - out of `block-only` scope unless the chosen
part lacks on-chip filtering.

**D14. Series input protection resistors are OPTIONAL and explicitly
conditional, not blanket.** [TI-INA333] s8.2.2.10: **"If the input signal
voltage can exceed the power supplies by more than 0.3 V, the input signal
current should be limited to less than 10 mA ... Some signal sources are
inherently current-limited and do not require limiting resistors."**
[ADI-AD8237] "Input Protection": same conditionality, `R_protect >
(Vin-Vs)/5mA`, only "if the application requires voltages beyond these
ratings." bb-amp's source (350 ohm bridge, -1mV to +25mV around 1.65V CM,
s9a Q1/Q5) never approaches either rail and is inherently current-limited by
the bridge's own 350 ohm - it does not meet either datasheet's trigger. This
directly supports the brief's exclusion of protection parts at `block-only`.

---

## 5. Layout constraints (vendor wording, for P6/P7 interface-spec)

- **L1. Trace symmetry, bridge/CM-resistor traces short and balanced:**
  [TI-TIDUB00] s5.1: "traces for the bridge and common mode resistors were
  kept as short and balanced as possible to minimize ... differential voltage
  ... due to trace impedance mismatch."
- **L2. Gain resistor at the device pins:** [TI-TIDUB00] s5.1: "Rg was placed
  as close to the pins of U1 as possible to minimize stray capacitance and
  trace impedance." [TI-INA333] s8.2.2.1: "careful matching of any parasitics
  on both RG pins maintains optimal CMRR over frequency."
- **L3. Impedance-match both input paths, including added source resistance,
  right at the pins:** [ADI-AD8237] Layout, "CMRR over Frequency": "Poor
  layout can cause some of the common-mode signal to be converted to a
  differential signal ... when the path to the positive input pin has a
  different frequency response than ... the negative input pin ... Place
  additional source resistance in the input path ... close to the in-amp
  inputs to minimize interaction ... with the parasitic capacitance from the
  PCB traces."
- **L4. Decoupling directly at the supply pins, ground plane under the
  chain:** [TI-INA333] s10.1: ground plane, components close to device pins,
  "0.1-uF bypass capacitor closely across the supply pins." [ADI-AD8237]:
  "0.1 uF ... as close as possible to each supply pin ... Keep the traces ...
  short to minimize interaction of the trace parasitic inductance with the
  shared [bulk] capacitor."
- **L5. REF ties to the LOCAL ground reference:** [ADI-AD8237] "Reference":
  "output voltage ... is developed with respect to the potential on the
  reference terminal. Take care to tie REF to the appropriate local ground."
- **L6. Connector placement follows the CM-resistor connection, not vice
  versa:** [TI-TIDUB00] s5.1: J1 "placed on the bottom of the PCB to allow for
  a close connection of R4 and R5."
- **L7. Bandwidth-mode strap is a fixed net, not an assembly option:** if an
  ICF part is used, [ADI-AD8237] requires BW hard-tied to +VS to get the
  1 MHz GBW this block's math needs (D9) - a P5/P6 net, not a DNP/config
  strap (which would be out of `block-only` scope).

---

## 6. Errata / footguns for this circuit class at 3.3 V

- **E1. The "diamond plot" - output swing and input common-mode trade off,
  worse at low supply.** [TI-INA333] s7.4.2: "the linear common-mode input
  range is related to the output voltage of the complete amplifier" (Figs
  20-23 plot a diamond/hexagon that visibly shrinks from 5V to 1.8V). Same
  mechanism on ADI's cover Fig.2: "TRADITIONAL IN-AMP (RAIL-TO-RAIL OUT)"
  plots as a hexagon pinching to near-zero swing at CM extremes, against
  AD8237's own larger rectangle - ADI markets ICF specifically because this
  bites at low VS. Mechanism: internal stages are headroom-limited and
  common-mode is subtracted internally, not free, so it competes with the
  signal for rail budget. bb-amp's Vcm=1.65V (mid-rail) is the BENIGN point
  on this plot (requirements.md s9a already says so) - correct citation why,
  and a reviewer check on wherever the final gain/swing corner lands.
- **E2. REF pin loading - see s2 in full.** Restated as errata: a classic
  in-amp REF driven from a bare divider is a silent CMRR killer (INA333:
  "tens of ohms... noticeable degradation"); the identical mistake is a
  non-issue on an ICF part (AD8237: "no effect on CMRR"). Mismatching the
  architecture to the REF-drive assumption is the single most likely P4
  schematic error on this block.
- **E3. Gain-resistor tolerance/tempco is NOT covered by the in-amp's own
  gain-error spec once external.** [TI-INA333]: "Gain vs temperature, G>1:
  +-15 to +-50 ppm/degC ... Does not include effects of external resistor RG."
  [TI-SBOA247] design note 2: "Low tolerance resistors must be used to
  minimize the offset and gain errors due to the bridge resistors." For a
  2-resistor ICF gain network, [ADI-AD8237] "Gain Accuracy": "two 1%
  resistors can cause approximately 2% maximum gain error at high gains" -
  ratio-match between two external parts, worse tolerance stacking than a
  single-RG case unless TCR-matched.
- **E4. Self-heating in the bridge/CM-setting resistors is a named error
  source.** [TI-SBOA247] design note 6: "limitations on the current through
  the bridge due to self-heating effects of the bridge resistors and strain
  gauge." [TI-TIDUB00]: "High accurate low drift resistors were used to
  prevent a change in resistance due to heating while handling ... or from
  self-heating due to bridge current" - controlled for even in a passive
  network in the reference vendor design.
- **E5. Near 0V output can look deceptively "normal" under input overload.**
  [TI-INA333] s7.4.2: "Input overload conditions can produce an output
  voltage that appears normal ... the output ... is near 0 V even though both
  inputs are overloaded" - a genuinely overloaded input reads as if the
  signal went to zero, not as an obvious rail-clip. How close to 0V the
  output can legitimately swing is load-dependent: [TI-INA333] "(V-)+0.05V
  typ" at RL=10k; [ADI-AD8237] +0.05-0.07V at 10k, tightening to
  +0.02-0.03V at 100k - both consistent with bb-amp's ~0.05-0.1V pedestal
  floor (s9a Q6); bb-amp's >100k load (Q8) is the favorable case for P2's
  swing check.
- **E6. Chopper/ALS clock feedthrough ripple, ICF/zero-drift parts only.**
  [ADI-AD8237] "Clock Feedthrough": ~27kHz internal chop clock; ripple
  "typically 100 uV RTI when the bandwidth is greater than the clock
  frequency ... may be necessary to use additional filtering." At G~150-165
  the ~6-7kHz closed-loop bandwidth (D9) sits below the 27kHz clock, which
  should suppress most of this - a part-specific check, not an assumption.

---
