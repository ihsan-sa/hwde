# LEARNINGS - bb-amp (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-amp` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-16 [P2][research][knowledge][interface:in] research task interface-in-1: 1 verified record(s) for interface:in
Gap: research interface 'in': produce its coverage checklist, then populate it
Operating point: {"gap_mm": 0.25, "max_skew_mm": 2.0, "max_uncoupled_mm": 5.0, "term_pair_mm": 2.5}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- in-terminal-thermal-emf [thermal] boards/bb-amp/research/records/in-terminal-thermal-emf.yaml
Refuted (left draft, not promotable):
- in-aggressor-separation: 01258b p17 callouts 1/6/7 and ina333 p20 are transcribed accurately - sensor traces are separated from power (top layer) and digital (bottom layer) traces to reduce crosstalk; the Difference Amplifier is as close to the sensor as possible and on the opposite PCB surface from the microcontroller, minimizing electrical and thermal crosstalk; power traces kept short, straight and above ground plane; and p20 gives keep traces short, use a PCB ground plane, surface-mount parts as close to the device pins as possible, 0.1 uF bypass across the supply pins, with Figure 40 showing VIN- and VIN+ entering as an equal-width parallel pair with nothing between them and the gain resistor straddling both RG pads. REFUTED on the reference rule. No cited page states unbroken reference copper or no split, slot or void under the pair - ina333 p20 says only, when possible, use a printed-circuit-board ground plane, and the p17 callouts say nothing about plane continuity. The same app note contradicts the rule one page past the citation: 01258b p18 Figure 41, 3rd Layer Ground Plane, shows a deliberate full-height FR4 gap splitting the reference plane between the amplifier side and the sensor/cold-junction side (callouts 10, 13, 14), with the analog signals crossing it through a narrow ground plane extension and digital traces routed under that extension with series resistors in the gap (callout 19). The vendor trades plane continuity away for thermal gradient, which is the dominant error term here. Second: the headline aggressor, the amplifier own output, appears on no cited page - the vendor design example names power and the microcontroller as the aggressors (callouts 1, 6, 7, 17), and 01258b p12 to p13 in fact prescribes surrounding the sensitive input with copper driven from VOUT. Plausible reasoning at G about 150, but unwitnessed by this ledger and stated flatly in rule.aggressors. Minor: the p4 citation drops the source hedge - low profile parts MAY have the additional advantage of reduced electrical crosstalk.
- in-bias-current-return-path: ina333 p16 and p17 re-read. Everything factual checks out verbatim: 100 Gohm input impedance, Ib typically +-70 pA, a path must be provided for the input bias current of both inputs, and the saturation sentence is word for word. Figure 34 on p17 really does draw all three claimed forms - floating microphone/hydrophone with a matched 47k/47k pair to a common ground node, thermocouple with a single 10k to ground, and a transformer whose grounded centre tap is annotated Center tap provides bias current return. REFUTED on the failure signature: the prose states the output is typically parked near a rail, but s8.2.2.6 sits on the SAME cited page 17 and says the opposite - input overload conditions can produce an output voltage that appears normal, and with both input amplifiers at their swing limits the difference measured by the output amplifier is near zero, so the output of the INA333 is near 0 V even though both inputs are overloaded. slyt226 p1 says the same thing in its opening column: saturation causes the INA output voltage, although of wrong value, to appear normal to the following processing circuitry. A reader trusting this record would hunt for a stuck rail and miss the actual symptom, which is a plausible-looking near-zero output. Second, smaller: the fourth legal form in rule.legal_forms (source already referenced to that ground via a third wire) is not one of the three in Figure 34 and is not stated on p16 - it is an uncited inference presented as vendor fact.
- in-bias-return-sizing: ina333 p16 re-read: the quoted fork is verbatim (if the differential source resistance is low the return path can be connected to one input; with higher source impedance, using two equal resistors provides a balanced input with possible advantages of lower input offset voltage as a result of bias current and better high-frequency common-mode rejection). Figure 34 on p17 does show a 47k/47k pair and a single 10k. REFUTED on the envelope. rsource_ohm is capped at 10 kohm and the envelope_note justifies it by saying that above it the bleeder pair becomes a dominant gain-error and noise term - but p16 recommends the two-equal-resistor form precisely FOR higher source impedance, so the record excludes from its envelope the exact regime its own rule field high_source_resistance describes. The 10 kohm number appears nowhere on p16 or p17. Second, the cross-vendor substitution is not safe for SIZING: the 47k and 10k examples are keyed to the INA333 CMOS input at 70 pA typ, yet the envelope admits ibias up to 100 nA, and at the bipolar AD8226-class bias this board actually uses a 47k pair develops roughly a millivolt of offset against the 5 uV referred-to-input budget fixed in requirements 9a. The envelope_note hedge that a higher-bias input needs proportionally smaller resistors does not repair an envelope that still admits 100 nA while carrying the 70 pA sizing examples. Third: nothing on p16 or p17 mentions Johnson noise or source loading, so both stated bounds are uncited.
- in-leakage-symmetry-and-guarding: 01258b p12 holds as cited: Figure 26 is the Thevenin source with RP1 to RP4 to all other nearby voltage nodes including ground, the typical values are RP about 1000 Gohm at low humidity and contamination and about 1 Gohm at high humidity and contamination, guard rings have no solder mask, are biased at the same voltage as the sensitive node and need to be driven by a low impedance source, and Figure 28 is the SMD unity-gain buffer guard ring. REFUTED on the p13 citation. Page 13 carries only Figures 29 to 32 - the unity-gain buffer equivalent circuit, the non-inverting gain amplifier and the transimpedance amplifier - plus the VOS across RP2 argument and the sentence the leakage current is typically reduced by a factor of about 1000. The section title claimed for p13 and two of its three claims are wrong for that page: Guard Rings on Both PCB Surfaces, the through-hole packages sentence and both jumper-trace sentences (any jumper traces connected to traces with guard rings also need guard rings; it is better when possible to avoid jumper traces for critical nodes) are all on p14. Substantive second point: every guard ring in this app note, Figures 28 through 33, is driven from the output of a SINGLE-ENDED op amp at the one sensitive node potential. The record transplants that to a differential input pair whose two inputs sit at different potentials by the signal, without saying what a differential guard would be driven from or that a single ring cannot sit at both potentials. Finally the equal-neighbourhood symmetry regime, which is the part that actually governs this board at 175 ohm source impedance, is the record own reasoning - it is on neither p12 nor p13 nor the ina333 page cited.
- in-path-symmetry-sets-cmrr: sboa582 p4 and p5 re-read. Transcription is clean: Equation 7 is CMRR_R = (G+1)/(4t), Equation 8 is the parallel combination 1/CMRR_D = 1/CMRR_A + 1/CMRR_R, the CM-to-differential sentence is verbatim, and Figure 2-4 does show CMRR_R flat and dominant with CMRR_A rolling off and crossing near 100 kHz. p4 does carry the worked case - a 1 kohm resistor at +-0.5 pct spanning 995 to 1005 ohm, Figure 2-3 with 995/1005/1005/995, the 150 dB OPA387 specification and a worst-case CMRR_D of only 40 dB. REFUTED on transfer to this interface. Every circuit in sboa582 (Figures 2-1, 2-3, 3-1, 3-2) is a FOUR DISCRETE RESISTOR difference amplifier in which G and t belong to the same gain-setting network, and the worked case is at Gain = 1 V/V per the Figure 3-2 caption. The record asserts rather than argues that the same algebra governs STRAY trace asymmetry. It does not: ina333 p16 puts the in-amp input impedance at about 100 Gohm, so mismatched series trace resistance draws essentially no current and converts essentially nothing at DC, and t has no counterpart in a bare trace pair. The headline claim that CMRR at this interface is set by input-path mismatch and not by the amplifier CMRR spec therefore does not follow for an in-amp fed from a 350 ohm bridge with no fitted input network - the in-amp internally trimmed network still dominates, and the genuine stray mechanism is mismatched shunt RC over frequency, which is what slyt226 p1 is actually about. The ina333 p15 corroboration is verbatim but is about the RG gain-set pins and their stability limit of a few pF, not about the input pins.
Draft coverage checklist(s) for the owner to approve:
- in boards/bb-amp/research/checklists/in.yaml (6 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/ina333.pdf tier cross-vendor sha256 446404e162fb <https://www.ti.com/lit/ds/symlink/ina333.pdf>
- research/sources/slyt226.pdf tier cross-vendor sha256 5445be9fcda2 <https://www.ti.com/lit/an/slyt226/slyt226.pdf>
- research/sources/01258b.pdf tier cross-vendor sha256 7301002f0c7d <https://ww1.microchip.com/downloads/en/appnotes/01258b.pdf>
- research/sources/sboa582.pdf tier cross-vendor sha256 0e4c756533ab <https://www.ti.com/lit/pdf/sboa582>
Task file: boards/bb-amp/research/tasks/interface-in-1.json

## 2026-08-16 [P2][research][knowledge][block:B1] research task block-inamp-1: 6 verified record(s) for block:B1
Gap: research block 'inamp': produce its coverage checklist, then populate it
Operating point: {"board_layers": 2, "calibration_kind": "zero-span-downstream", "err_budget_uv_rti": 5, "f3db_hz": 41000, "f_signal_hz": 1000, "gain_split_kind": "two-stage", "gain_stage1_vv": 39.9, "gain_stage2_vv": 3.49, "gain_vv": 139.2, "inamp_arch_kind": "three-opamp", "iq_ma": 0.65, "load_kohm_min": 100, "noise_nv_rthz_rti": 22.2, "output_stage_kind": "rrio-opamp", "pdiss_w": 0.0023, "ref_drive_kind": "buffered", "rsource_ohm": 350, "source_kind": "bridge-external-excitation", "supply_kind": "single", "tamb_c_max": 50, "tamb_c_min": 0, "vcm_v": 1.65, "vin_diff_mv_fs": 20, "vin_diff_mv_max": 25, "vout_max_v": 3.037, "vout_min_v": 0.113, "vped_v": 0.252, "vs_tol_pct": 5, "vs_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- inamp-gain-partition-first-stage [selection] boards/bb-amp/research/records/inamp-gain-partition-first-stage.yaml
- inamp-headroom-escape-gain-in-difference-amp [selection] boards/bb-amp/research/records/inamp-headroom-escape-gain-in-difference-amp.yaml
- inamp-internal-node-headroom-inequalities [selection] boards/bb-amp/research/records/inamp-internal-node-headroom-inequalities.yaml
- inamp-internal-node-saturation [selection] boards/bb-amp/research/records/inamp-internal-node-saturation.yaml
- inamp-ref-pin-drive-impedance [feedback] boards/bb-amp/research/records/inamp-ref-pin-drive-impedance.yaml
- inamp-supply-decoupling-and-local-ground [decoupling, return-path] boards/bb-amp/research/records/inamp-supply-decoupling-and-local-ground.yaml
Refuted (left draft, not promotable):
- inamp-gain-pin-and-input-node-parasitics: REFUTED on the envelope, which overreaches the ledger's own PDF. The vendor prose is fine: AD8226 PDF p.22 (printed p.21) prints the input-path matching paragraph and the gain-pin parasitic-capacitance paragraph verbatim as quoted, and PDF p.6 Table 3 confirms CMRR min 86/90 dB at G=1, 106 at G=10, 120 at G=100 and G=1000 for DC to 60 Hz, and 80/90/90/100 dB at 5 kHz. But envelope f_signal_hz max 5000 rests on envelope_note's claim that 5 kHz is 'the highest frequency at which the cited part specifies CMRR at all' and that 'above it there is no vendor number for the copper to preserve'. That is false about this same data sheet: printed p.13 (PDF p.14) carries Figure 27 'CMRR vs. Frequency, RTI' and Figure 28 'CMRR vs. Frequency, RTI, 1 kohm Source Imbalance', both plotted from 0.1 Hz to 100 kHz for G = 1/10/100/1000. Figure 28 is the vendor's own measurement of precisely this record's mechanism - a deliberate source imbalance and the CMRR it costs across frequency - and it was never read. The consequence is load-bearing rather than cosmetic: this board's chain is specified to f3db = 41 kHz, so a 5 kHz envelope reads as 'the matching rule stops applying inside our own bandwidth', which inverts the record's own mechanism, under which the error GROWS with frequency. Fix: cite Figures 27 and 28, widen or drop the frequency cap, and use Figure 28 to quantify the source-imbalance claim instead of asserting it. Minor: gain_pin_layout ('Rg directly across the Rg pins') is not on printed p.21; it is supported by Table 6 pin 2,3 'Place a gain resistor between these two pins' on PDF p.9, which the record does not cite.
Draft coverage checklist(s) for the owner to approve:
- inamp boards/bb-amp/research/checklists/inamp.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_Analog-Devices-AD8226ARZ-R7_C34250.pdf tier vendor-layout sha256 ea42b3f336e4 <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Analog-Devices-AD8226ARZ-R7_C34250.pdf>
- research/sources/1811012120_Analog-Devices-AD8227ARMZ-R7_C150954.pdf tier vendor-layout sha256 ea42b3f336e4 <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1811012120_Analog-Devices-AD8227ARMZ-R7_C150954.pdf>
- research/sources/2168367.pdf tier vendor-layout sha256 e99737516d60 <https://www.farnell.com/datasheets/2168367.pdf>
- research/sources/slyt226.pdf tier cross-vendor sha256 5445be9fcda2 <https://www.ti.com/lit/an/slyt226/slyt226.pdf>
Task file: boards/bb-amp/research/tasks/block-inamp-1.json

## 2026-08-16 [P2][research][knowledge][block:B1] research task block-inamp-2: 2 verified record(s) for block:B1
Gap: research block 'inamp': populate diff-pair
Operating point: {"board_layers": 2, "calibration_kind": "zero-span-downstream", "err_budget_uv_rti": 5, "f3db_hz": 41000, "f_signal_hz": 1000, "gain_split_kind": "two-stage", "gain_stage1_vv": 39.9, "gain_stage2_vv": 3.49, "gain_vv": 139.2, "inamp_arch_kind": "three-opamp", "iq_ma": 0.65, "load_kohm_min": 100, "noise_nv_rthz_rti": 22.2, "output_stage_kind": "rrio-opamp", "pdiss_w": 0.0023, "ref_drive_kind": "buffered", "rsource_ohm": 350, "source_kind": "bridge-external-excitation", "supply_kind": "single", "tamb_c_max": 50, "tamb_c_min": 0, "vcm_v": 1.65, "vin_diff_mv_fs": 20, "vin_diff_mv_max": 25, "vout_max_v": 3.037, "vout_min_v": 0.113, "vped_v": 0.252, "vs_tol_pct": 5, "vs_v": 3.3}
Missing classes: diff-pair

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- inamp-cmrr-over-frequency-and-source-imbalance [diff-pair] boards/bb-amp/research/records/inamp-cmrr-over-frequency-and-source-imbalance.yaml
- inamp-input-network-differential-cap-dominance [diff-pair] boards/bb-amp/research/records/inamp-input-network-differential-cap-dominance.yaml
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2168367.pdf tier vendor-layout sha256 e99737516d60 <https://www.farnell.com/datasheets/2168367.pdf>
Task file: boards/bb-amp/research/tasks/block-inamp-2.json

## 2026-08-16 [P2][research][knowledge][interface:in] research task interface-in-2: 7 verified record(s) for interface:in
Gap: research interface 'in': populate return-path, diff-pair, emi, selection, constraints-emission (application delta only - principle parents exist)
Operating point: {"dt_c": 1, "err_rti_mv": 0.005, "f3db_hz": 41000, "f_signal_hz": 1000, "gap_mm": 0.25, "ibias_ua": 0.035, "max_skew_mm": 2.0, "max_uncoupled_mm": 5.0, "mismatch_pct": 1, "rsource_ohm": 350, "term_pair_mm": 2.5, "vcm_v": 1.65, "vout_v": 3.04, "vsig_mv": 20}
Missing classes: return-path, diff-pair, emi, selection, constraints-emission

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- in-bias-return-failure-signature [return-path] boards/bb-amp/research/records/in-bias-return-failure-signature.yaml
- in-bias-return-path-required [return-path] boards/bb-amp/research/records/in-bias-return-path-required.yaml
- in-bias-return-resistor-sizing-ad8226 [return-path] boards/bb-amp/research/records/in-bias-return-resistor-sizing-ad8226.yaml
- in-cable-shield-termination [emi] boards/bb-amp/research/records/in-cable-shield-termination.yaml
- in-constraints-emission [constraints-emission] boards/bb-amp/research/records/in-constraints-emission.yaml
- in-input-path-equivalence [diff-pair] boards/bb-amp/research/records/in-input-path-equivalence.yaml
- in-terminal-selection [selection] boards/bb-amp/research/records/in-terminal-selection.yaml
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2168367.pdf tier vendor-layout sha256 e99737516d60 <https://www.farnell.com/datasheets/2168367.pdf>
- research/sources/an1298-instrumentation-amplifier-application-note.pdf tier cross-vendor sha256 88e867197d15 <https://www.renesas.com/en/document/apn/an1298-instrumentation-amplifier-application-note>
- research/sources/how-monitor-sensor-health-instrumentation-amplifiers.pdf tier cross-vendor sha256 46a3c2c44da0 <https://www.renesas.com/en/document/whp/how-monitor-sensor-health-instrumentation-amplifiers>
- research/sources/691361100003.pdf tier vendor-layout sha256 a45b83daedc9 <https://www.we-online.com/components/products/datasheet/691361100003.pdf>
Task file: boards/bb-amp/research/tasks/interface-in-2.json

## 2026-08-16 [P4][spice][sim-analyst] `.meas ac rms` is FREQUENCY-WEIGHTED, which is how you get integrated noise out of ngspice without `.noise`
ngspice has no way to report integrated noise into a measure - `.measure` is documented for
ac/dc/tran/sp only, and the `.noise` totals never reach the "Measurements for" block the
runner parses. The way through: inject the RTI noise DENSITY as a plain AC source, then
`.meas ac x rms vm(out) from=f1 to=f2`; total rms = x * sqrt(f2-f1). Verified on this host
against a closed-form RC integral (fc = 100 Hz over 1..10 kHz): analytic 0.124137, measured
0.124537 on `.ac lin` and 0.124539 on `.ac dec` - so the weighting is by frequency, not by
sweep point, and a decade sweep is fine. `integ` matches the same closed form to 5 digits
(528.834 vs 528.83). ONE source only: `.ac` superposes sources COHERENTLY, so two noise
sources add as voltages, not in quadrature - lump the whole RTI density into one and list
in the header what you left out and why. Second engine fact from the same session: a prior
measure's result IS available to `.meas <n> param='<prior> ...'` but NOT to
`.meas <n> when v(x)='<prior>-3'` - `when` values are substituted at parse time and the run
dies with "Undefined parameter". Hard-code the trigger level and say in the sidecar that a
wrong gain therefore shows up as a MISSING measure (still an error) rather than a bad one.

## 2026-08-16 [P4][spice][sim-analyst] Pad every .dc/.ac sweep: the FIRST point can converge to junk and `at=` on the LAST point errors out
On a 5-op-amp chain (three inside the AD8226 macromodel, two OPA2333 halves) ngspice 46
reported "Dynamic gmin stepping failed / True gmin stepping failed / source stepping failed"
at the first point of `.dc Vd -0.001 0.025` and returned a bogus operating point there:
`v(amp1)` read 0.1025 V (pinned to the model's output clamp) where the correct answer is
0.2123 V, while every later point - which converges from the previous solution - was exact.
At the other end, `at=0.025` on the last point of the same sweep failed with "out of
interval". Both vanish if the range is padded (`-0.002 .. 0.026`) so that no MEASURED point
is a sweep endpoint. Costs nothing, and without it a bench silently reports a wrong number
rather than failing. Two related traps found the same session: `.meas tran ... fall=last`
with no `from=/to=` scans the WHOLE run (a settling-time measure on the first step returned
the recovery edge of an overload 2 ms later - 2020 us instead of 23.6 us), and there is no
`i(x1.r2)` vector for a resistor inside a subcircuit - derive branch currents from node
voltages in a `param=` instead.

## 2026-08-16 [P4][spice][sim-analyst] A behavioural op-amp needs its anti-windup on the INTEGRATOR node, and its swing clamp AFTER ro - the datasheet swing number is already loaded
Two defects measured in one agent-authored generic op-amp macromodel, both of which produced
plausible-looking wrong answers rather than errors. (1) Clamping only the output buffer
leaves the R||C integrator node free: 1 ms of a +25 mV overload charged it to ~160 V at the
slew limit, and the bench then showed the amplifier NEVER recovering - a fake overload-
recovery failure. Clamp the integrator node itself (stiff diode pair to rail +- a small
anti-windup headroom) so recovery costs headroom/slew-rate. (2) Clamping ahead of the
open-loop output resistance and then dropping ro*Iload on top DOUBLE-COUNTS the load: a
datasheet "output swing 30 mV from the rail at RL = 10 k" is already a loaded figure, and
stacking a 1 kohm ro on it put the clip level at 3.152 V instead of ~3.27 V - inside the
gate window by 2 mV, i.e. it would have passed while being wrong. Put the swing clamp on
the output NODE and leave ro free to do its real job (AC output impedance and capacitive-load
stability). Corollary for the sidecar: state that the recovery TIME is then a property of
the anti-windup headroom you chose, not a datasheet number, and gate it as a warning.

## 2026-08-16 [P4][sim-analyst][inamp] A series isolation resistor only isolates when it is comparable to the op-amp's open-loop ro - and Figure-15-class overshoot curves are UNITY-GAIN numbers
bb-amp's R6 was added at P3 at 100 R because OPA2333 Figure 15 shows small-signal overshoot
reaching roughly the mid-30 % range by CL = 1 nF and requirements allow 1 nF of output cable.
Both halves of that reasoning failed on the bench. First, an overshoot-vs-CL curve is taken
in unity gain; the stage it was applied to runs at a noise gain of 3.49, which moves the loop
crossover from 350 kHz to 100 kHz and is worth roughly 25 degrees of phase margin - the same
macromodel that reproduces Figure 15 (32 % at 1 nF in unity gain) gives 6.6 % for the actual
stage with NO R6 at all. Second, an out-of-loop series R isolates by putting a zero at
1/(2*pi*R6*CL) against the pole at 1/(2*pi*(ro+R6)*CL), so its authority is set by R6/ro:
at ro = 1-2 kohm, R6 = 100 R moved overshoot by 0.3 to 1.3 points, while R6 = 1 kohm halved
it. Rule: size an isolation resistor against the op-amp's OPEN-LOOP output resistance, not
against the load, and re-read any capacitive-load figure for the gain it was measured at.
Also: when the datasheet states ro only at one frequency (2 kohm at 350 kHz here, no DC or
closed-loop figure anywhere), calibrate ro against the vendor's own overshoot curve inside
the bench, keep the literal number as a pessimistic bracket, and carry BOTH through every
conclusion.

## 2026-08-16 [P4][sim-analyst][inamp] Build the in-amp from its OWN published 3-op-amp structure and the REF-impedance defect becomes a gate failure instead of a review opinion
Modelling the AD8226 as its published topology - two preamps with 24.7k feedback around the
external RG, then a difference amplifier from four 50k resistors with REF at the end of one
of them - costs about fifteen lines and makes three separate things emergent rather than
asserted: the gain law G = 1 + 49.4k/RG comes from the resistors, internal Node 1 is a real
node you can probe (`v(x1.xu1.nd1)` works), and any impedance in series with REF reproduces
the datasheet's own 2*(50k+Rref)/(100k+Rref) uneven amplification exactly. That last one
turns "the REF buffer is not optional" from a design-review claim into a measured gate bound:
deleting the buffer and driving REF from the bare 9.24 k divider Thevenin moved the CMRR
bench from 0.134 mV to 17.06 mV over a 0.2 V common-mode sweep, 57x over its window, and
moved the reference node itself by 16.9 mV. Seed exactly that defect to prove the bound
before shipping it.

## 2026-08-16 [P4][sim-analyst][datasheet] A datasheet stability curve is taken AT A STATED GAIN - a unity-gain overshoot figure does not transfer to a stage running at higher noise gain
The error this board actually made, and the reason a part was designed in and then removed
one phase later. OPA2333 Figure 15 ("SMALL-SIGNAL OVERSHOOT vs LOAD CAPACITANCE") shows
overshoot reaching roughly the mid-30 % range by CL = 1 nF, and requirements allowed 1 nF of
output cable, so P3 added R6 = 100 R as an isolation resistor. What the figure does not say
on its face - its test conditions are not labelled on the page, only the page-level
"TA = +25C, VS = +5V" note - is that an overshoot-vs-CL curve is a UNITY-GAIN measurement,
the worst case for a voltage-feedback amplifier. The stage it was applied to runs at a noise
gain of 3.49, which moves the loop crossover from GBW to GBW/3.49 and is worth roughly 25
degrees of phase margin against the identical load. Measured in one bench: the same
calibrated macromodel gives 32.0 % for a plain unity buffer into 1 nF (reproducing Figure 15,
which is how the model was calibrated) and 6.6 % for the real stage into the same 1 nF with
NO isolation resistor. The part was never needed. Rules: (1) before designing a part in on
the strength of a capacitive-load, overshoot, phase-margin or settling curve, find the GAIN
the curve was taken at and re-ask the question at the gain you are actually running - and if
the datasheet does not label the figure, say so and treat unity gain as the assumption;
(2) a stability curve read at the wrong gain is not conservative, it is simply a different
circuit; (3) put the calibration instance IN the bench (here a unity buffer reproducing
Figure 15 alongside the real stage) so a reader can audit the transfer instead of trusting
it. Corollary already recorded above: an out-of-loop series resistor only isolates in
proportion to R/ro, so 100 R against a 1-2 kohm open-loop output impedance moved overshoot
by 0.3 to 1.3 points - it would not have done the job even if the job had existed.


## 2026-08-17 [P6][board_init][board_edit][build-modes] `outline_bbox` is a BBOX, not a size - and the "generous provisional room" auto picked was the wrong ASPECT, not the wrong area

`reports/board_init.json` records `"outline_bbox": [13.0, 13.0, 41.02, 57.69]` - min/max corners.
The P5 digest (and the P6 spawn brief that quoted it) both read that as "41.0 x 57.7 mm". The board
is 28.02 x 44.69 mm. That is not a rounding difference: it inverts which dimension is scarce. The
canonical layout for this block is a WIDE board (J1 on the left edge, J2 on the right edge, a two-IC
chain between them), and it does not fit in 28 mm of width at any packing density - while the AREA
auto chose (1252 mm2) is within 8 % of what the layout finally needed (1259 mm2 of content). Two
rules: (1) print `w x h` derived from the bbox, never the bbox corners, in any prose a later stage
reads; (2) at a `canonical` binding `--outline auto` is only sized, never shaped - check the aspect
against the block's own layout before treating the provisional room as roomy.

## 2026-08-17 [P6][board_edit][placement] `--outline fit` CLIPS to the CURRENT outline, so "place canonically, then fit" only works if you GROW the room first

`board_edit.content_bounds()` intersects the union of courtyards/copper/rule-areas with the current
outline before taking the bbox - deliberately, so fit can never invent a containment violation. The
consequence for the canonical flow is an ordering constraint nobody states: if the placement you want
extends past the provisional edge, `--outline fit` measures only the part that was inside and returns
a SMALLER board, silently. The working order is grow (`--outline WxH`, generous in both axes) ->
place -> `--outline fit`. `--outline WxH` also refuses while the CURRENT placement has anything
outside the NEW rect, so the grow rect has to cover the union of the old and new placements, or the
placement has to be applied first. Companion fact: fit is idempotent (re-running with the same margin
reproduces the same rect), so the orchestrator's own post-gate fit is a no-op confirmation.

## 2026-08-17 [P6][placement][kicad][render] The KF128 top-view "teeth" are the connector's REAR, not its wire entry - and the 3D model is rotated 180 from the footprint

The KF128-5.08 3D model is instantiated with `(rotate (xyz 0 0 180))`, so a top render shows the body
mirrored relative to the footprint silk. In the top view all three terminals appeared to have their
funnel-like triangles facing the board interior, which reads as "all three are backwards"; they are
the rear ledge. The footprint silk is the truthful cue (three notched rectangles at local y
+3.33..+5.30 = the wire entry, at local +Y), and the orthographic side render is decisive: with
J1 at 270, J2 at 90 and J3 at 0, `render.py --views left,right,front` shows 3 / 2 / 2 dark wire
cavities face-on in the left / right / front views respectively. Confirms the 2026-07-28 and
2026-08-09 root entries: mouth at local +Y, so 0 = out the BOTTOM edge, 90 = RIGHT, 180 = TOP,
270 = LEFT. Never grade a connector's mating direction from the top render.


## 2026-08-17 [P6][P4][placement][diff-pair][inamp] A connector's pole ORDER against the IC's pin order forces exactly one crossing on the input pair - and it is a free schematic fix, measured both ways

bb-amp's J1 was drawn (IN+, IN-, GND) on poles 1/2/3 while the AD8226's inputs run (-IN, RG, RG,
+IN) on pins 1..4. Those two orders are reversed, so /IN_P and /IN_N must swap exactly once between
connector and amplifier. This is TOPOLOGICAL, not a placement failure: rotation preserves orientation,
so I enumerated all eight combinations (J1 on each of four edges x U1's input face toward it) and
every one interleaves. Rotating BOTH parts mirrors both orders and preserves the interleave; only a
reflection of one of them fixes it, and a front-side SMD part cannot be reflected.

Measured, same placement, only the two pad-net assignments changed (J1.1 <-> J1.2):
  before   /IN_P, /IN_N HPWL 15.23 mm each, board HPWL 173.45, crossings_signal 6 (incl. IN_N x IN_P)
  after    /IN_P, /IN_N HPWL 11.43 mm each, board HPWL 165.85, crossings_signal 5 (pair gone)
  geometry start dy -/+2.540 -> end -/+1.900, dx 10.790, euclid 10.8090 on BOTH legs, delta 0.000000
  routing  two straight F.Cu segments at the netclass width, ZERO vias, kicad-cli --severity-all
           reports 0 non-unconnected findings and 0 remaining unconnected on either input net
Before the swap the same placement needed a via pair on one leg (~0.6 pF of imbalance, ~-123 dB at
1 kHz by in-input-path-equivalence's 1.1 ppm/pF) plus a slot in the B.Cu reference under the input
region, which blocks.md section 5 item 6 forbids.

Rules: (1) at P4, order a multi-pole input terminal to MATCH the amplifier's pin order along the
facing direction, not to match the schematic's reading order - it costs nothing and it is the
difference between a zero-via pair and a pour slot under the input; (2) P6 cannot fix it, so a
placement agent that finds an unavoidable pair crossing should report the pole swap rather than
spend vias on it; (3) a `board_update` will NOT carry a pad-net rewire (it refuses by design) - the
fix costs a P5 re-init, so it is cheapest caught at P4 review.
