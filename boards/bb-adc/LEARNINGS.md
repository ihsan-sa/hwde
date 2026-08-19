# LEARNINGS - bb-adc (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-adc` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-16 [P0][modes][check_requirements][pipeline] A blockquoted brief silently disables the ENTIRE U18 mode leg of check_requirements.py

`modeslib.detect` skips lines beginning with `>` and lets the first PLAIN line of the
brief decide the token. Write the owner's brief as a markdown blockquote - the obvious
way to mark "these are their words, verbatim" - and `detect` returns `None`. The
consequence is not a failure but a silence: `req_mode_unnamed` and
`req_mode_unmarked_size` can never fire, so a requirements.md that names no mode and
states an unmarked HARD size passes the lint clean. What you get instead is a
`req_mode_stray` WARNING whose text points the wrong way ("section 1 names a build mode
but no brief/ file opens with a mode token"), which reads as a cosmetic complaint about
section 1 rather than as "your mode checks are all switched off".

Verified on this run: with the brief blockquoted, exit 0 / status pass / one stray
warning; with the token as the first plain line, exit 0 / 0 violations and
`brief_token` populated in the report. Both are exit 0 - the difference is only visible
in the report body, which is why it can pass unnoticed.

The mechanical half of U18 is NOT affected: `state.py mode` records the resolved mode
into state.json independently, so `board_init`'s refusal of a fixed `--outline` still
bites. Only the lint goes blind.

Fix here: the brief's first plain line IS the token line; provenance ("owner brief,
verbatim, received <date>") goes BELOW a rule, not above the token. Sibling workspace
bb-mcu had the same shape at the time of writing.

## 2026-08-16 [P1][parts][adc][jlc] JLC's "External" reference attribute lies for 8-pin MCP3202: VDD and VREF are ONE physical pin

Scouting 12-bit SPI SARs with a separate reference input, the MCP3202 ranks first on
every catalog axis that parts_search can see - better stock (1347) and lower price
($2.06) than the MCP3201 - and its JLC attribute row claims an External reference.
It is disqualified anyway: in the 8-pin package MCP3202 bonds VDD and VREF to a single
pin, so the reference cannot be set below the supply. On a board whose whole accuracy
argument rests on an external 2.5 V-class reference, that silently turns the design
ratiometric to the host's +/-5 % rail.

Only the datasheet (DS21290F) shows it; the catalog attribute does not. The general
form: for a converter, "has an external reference" is a PIN-MAP question, and the pin
map lives in the datasheet's package section, not in a distributor attribute. Check it
per package variant, not per part family - the 8-pin and 14-pin members of one family
differ exactly here.

Second finding from the same sweep: of the SARs the scout surfaced, every one with
16-bit-class accuracy (ADS8318 / ADS8681 / ADS8688) requires >=4.5 V AVDD.
**CORRECTED at P2 - do not carry the generalisation.** The architect found ADS8326
(16-bit, 2.7-5.5 V supply, external VREF, +/-2.5 LSB INL max) in stock, which
falsifies "nothing that accurate runs natively at 3.3 V". The true statement is
narrower: the 16-bit parts with the WIDEST input ranges and on-chip attenuators need
>=4.5 V, because the attenuator needs the headroom - not 16-bit accuracy as such.
A one-sweep absence is evidence about the sweep, not about the catalogue.

## 2026-08-16 [P2][parts][adc][accuracy] A 12-bit part's "+/-5 LSB gain error" is a BIGGER voltage than a 16-bit part's, and ranking SARs on INL hides it

P1 ranked 12-bit SARs and reported INL per candidate, which is the spec everyone
quotes. MCP3201-B's own DS21290F also specifies **gain error +/-5 LSB MAX and offset
+/-3 LSB**, and at 12 bits over a 5 V full scale one LSB is 1.22 mV - so the gain
term alone is 6.10 mV, **1.22x the entire +/-5 mV error budget** of this board. The
part was the P1 lead candidate and would have failed the board's headline spec on a
datasheet number nobody had read.

The mechanism generalises and is counter-intuitive: DC error specs denominated in
LSB shrink 16x in VOLTAGE going from 12-bit to 16-bit at the same full scale. So a
16-bit converter quoting "+/-16 LSB gain error" is FOUR TIMES BETTER in volts than a
12-bit one quoting "+/-5 LSB". Resolution and accuracy move together in the spec
table, in the opposite direction to the intuition that a coarser part has an easier
job. "12-bit or better" in a brief is a resolution floor; it says nothing about the
DC error, and on an accuracy-driven board the higher-resolution part is often the
cheaper way to buy accuracy.

Selection rule to carry: for a converter on a DC-accuracy board, rank on OFFSET,
GAIN and INL **as maxima, converted to millivolts at the terminal** - never on INL
alone, and never in LSB. Parts that specify only typicals for offset and gain are
disqualified by that alone: an unbounded term cannot enter an error budget.

## 2026-08-16 [P1][parts][jlc][sourcing] One LCSC search term returns six clone brands under a precision part's MPN pattern, and a clone's offset spec can be 300x looser

Searching JLC for an AD8605-pattern precision op-amp returns the genuine
Analog-Devices row alongside six clone-brand rows sharing the same MPN pattern and
pinout. Pulling one clone's own datasheet (brand TECH PUBLIC) gives 5 mV MAX input
offset voltage against the genuine part's reputation of tens of microvolts - 30 to
300x looser, on a part number a BOM would treat as equivalent.

On an 0.1 %-class board that single number IS the whole budget: 5 mV of offset
against a +/-5 mV total error target at 25 C. The failure mode is the bad kind - the
board assembles, powers up, converts, and is simply wrong by a percent, with a BOM
line that reads like the right part.

Generalises past this part: for any part whose VALUE is a precision spec (offset,
tempco, initial accuracy, ratio match), the LCSC brand column is a selection
criterion, not metadata. Pin the manufacturer, not just the MPN, and pin it in
parts.json so P3 cannot silently resolve to a cheaper row. Catalog attributes are
not a substitute - they are frequently copied from the original part's datasheet.

## 2026-08-16 [P1][analog][accuracy][divider] Source impedance and divider total resistance are ONE decision, and 'high input impedance' can be the thing that breaks the budget

The loading error a resistive attenuator adds is Rs/Rtot of reading - source
impedance over divider total resistance. This board's answered specs (source
<= 1 kohm, board presents >= 100 kohm) are individually reasonable and jointly
impossible at 0.1 %: 1 kohm into 100 kohm is 1 % = 50 mV against a 5 mV budget, a
10x miss hiding inside two numbers that each look conservative.

Pushing Rtot up to fix it runs into the opposite wall. Buffer input bias current
flows through the divider's Thevenin resistance, so that error term grows with Rtot
exactly as the loading term shrinks. Minimising the sum for Rs = 1 kohm and a
200 pA-max buffer puts the optimum near 6 Mohm, and the residual is ~1.5 mV - a
third of the budget spent on nothing but impedance choice. Above ~1 Mohm the node
also becomes a leakage problem (a 1 Gohm flux path to a 3.3 V rail is millivolts of
error), which is what guard rings are for.

And the parts fight back: ratio-matched resistor NETWORKS - the parts whose whole
purpose is ratio accuracy and TCR tracking - top out around 100 kohm per element, so
the megohm-class divider that fixes loading cannot use one. Megohm class means
discrete pairs, where ratio error is ~sqrt(2) x tolerance and ratio TCR error is
~sqrt(2) x TCR because the two parts do not track.

The decision to take from this: fix the source-impedance contract and the divider
value TOGETHER, as one number pair, before choosing any part - and put the resulting
input impedance on the silkscreen, because it is a specification of the instrument,
not an implementation detail.

## 2026-08-16 [P2][parts][reference][analog] A reference family's dropout is PER MEMBER and not monotonic in output voltage - the 2.048 V part has the worst dropout in its family

The ADR45xx family sells on "low dropout, 300 mV at 2 mA". That number carries the
footnote **(VOUT >= 3 V)** and applies to NEITHER low-voltage member. The spec
tables instead condition the datasheet on `VIN = 3 V to 15 V` and give a per-member
dropout row over -40..+125 C, at no load AND at 2 mA:

| member | VOUT | DROPOUT max | floor = max(3.0, VOUT+VDO) | margin on a 3.135 V rail |
|---|---|---|---|---|
| ADR4520 | 2.048 V | **1 V**   | 3.048 V | 87 mV  |
| ADR4525 | 2.5 V   | **500 mV**| 3.000 V | 135 mV |
| ADR4530 | 3.0 V   | 100/300 mV| 3.100 V | fails  |

The counter-intuitive part, and the whole point of the entry: dropout is NOT
monotonic in output voltage, and the LOWEST-output member has the WORST dropout.
The instinct that "less output voltage leaves more headroom" is wrong here - a
2.048 V reference on a 3.3 V rail has LESS margin than a 2.5 V one. Two members of
one family, one datasheet, opposite answers.

**Corrected mid-run.** This entry first claimed the 2.5 V member needed 3.50 V and
"cannot work", by taking the 2.048 V member's 1 V dropout and applying it across
the family - the same class of error as trusting the family headline, one level
down. A fresh-context second reader caught it by reading the sibling member's own
row. Reading the spec table instead of the headline is only half the discipline;
the other half is reading the row for the EXACT part number, because a "family
datasheet" is several parts' datasheets stapled together.

(On this board the choice stayed at 2.048 V anyway, but for an unrelated reason:
equal-element strings can only realise ratios n_b/(n_t+n_b), and 2.048 V lands
K = 0.4 = 2/5 with five resistors and 97.7 % range utilisation, where 2.5 V would
need nine to eleven elements for comparable headroom or clip at exactly 5.000 V.)

Two further traps in the same spec:
- Dropout is DEFINED as the differential at which VOUT has ALREADY degraded by
  0.1 %. On a board whose whole budget is 0.1 %, "in spec at dropout" means the
  reference is already spending 41 % of the budget. Margin to dropout is margin to
  a degraded point, not to a cliff.
- TI's REF70 shows the same pattern from the other side (`VIN_min = VOUT + VDO`
  but with a FIXED 2.75 V floor below VOUT = 2.5 V), and its revision history
  changed VIN_min twice inside one revision. A cached distributor attribute is
  never evidence for this parameter.

Rule to carry: for any reference under ~2.5 V out, read the SPEC TABLE's VIN
condition and the dropout row for THAT EXACT member - not the family headline, not
a sibling member's row, and never a catalogue voltage-range attribute. Then check
whether the VIN table condition (here a flat 3 V) binds ABOVE VOUT + VDO, because
when it does it is the real floor and the dropout row is irrelevant.

## 2026-08-16 [P1][P2][research][env] analog.com and mouser.com time out from this sandbox; farnell.com is the working ADI-datasheet mirror and is already allowlisted

Four independent agents this session failed to reach `analog.com`, and two failed
on `www.mouser.com/datasheet/...`. Both are on the fetch allowlist, so the failure
is network reachability from this host, not policy. That matters because ADI now
owns Linear and Maxim, so a large share of precision-analog primary material -
references, precision amplifiers, matched networks, the MT-series notes - is behind
that one unreachable host.

The workaround that WORKED, without touching the allowlist: `www.farnell.com/
datasheets/<id>.pdf` serves ADI datasheets and is already an allowlisted domain.
That is how the ADR4520 dropout question was settled. Caveat found in the same
pass: the Farnell mirror served **Rev 0 (2012)** while current ADI/LCSC copies are
a later revision, so a mirror is good enough to SETTLE a question and not good
enough to COMMIT a part - re-confirm the load-bearing row against the current
revision before ordering.

Also refused, and correctly: `www.lcsc.com/datasheet/<C-id>.pdf` is an HTML viewer
shell, not a PDF; research.py fetch rejects it under `--expect pdf`. The wmsc.lcsc
stem is the real PDF path.

Practical ordering for a researcher on this host: ti.com first (fast, deep, and
its cross-vendor app notes cover most analog topologies), vishay.com for passives,
farnell.com as the ADI mirror, and do not spend depth-cap attempts on analog.com.

## 2026-08-16 [P2][research][knowledge][block:B1] research task block-resistive-attenuator-1: 6 verified record(s) for block:B1
Gap: research block 'resistive-attenuator': produce its coverage checklist, then populate it
Operating point: {"ambient_max_c": 50, "board_layers": 2, "coupling_kind": "dc", "element_count": 5, "element_kind": "discrete-equal-string", "error_budget_mv": 5.0, "guard_kind": "driven-guard", "pdiss_w": 2.5e-05, "ratio": 0.4, "rthev_ohm": 240000, "rtot_ohm": 1000000, "source_kind": "dc-input", "source_z_max_ohm": 200, "tcr_ppm_per_c": 10, "tol_pct": 0.02, "vin_max_v": 5.0, "vout_max_v": 2.048}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- resistive-attenuator-bottom-node-is-a-reference [return-path] boards/bb-adc/research/records/resistive-attenuator-bottom-node-is-a-reference.yaml
- resistive-attenuator-high-z-tap-guard-and-leakage [creepage] boards/bb-adc/research/records/resistive-attenuator-high-z-tap-guard-and-leakage.yaml
- resistive-attenuator-loading-source-and-load [feedback] boards/bb-adc/research/records/resistive-attenuator-loading-source-and-load.yaml
- resistive-attenuator-ratio-from-relative-specs [selection] boards/bb-adc/research/records/resistive-attenuator-ratio-from-relative-specs.yaml
- resistive-attenuator-self-heating-and-gradient [thermal] boards/bb-adc/research/records/resistive-attenuator-self-heating-and-gradient.yaml
- resistive-attenuator-tcr-tracking-not-absolute-tcr [selection, thermal] boards/bb-adc/research/records/resistive-attenuator-tcr-tracking-not-absolute-tcr.yaml
Draft coverage checklist(s) for the owner to approve:
- resistive-attenuator boards/bb-adc/research/checklists/resistive-attenuator.yaml (6 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/incresarr.pdf tier vendor-appnote sha256 5a4c3b36a3a0 <https://www.vishay.com/docs/28194/incresarr.pdf>
- research/sources/snoa664.pdf tier cross-vendor sha256 f6ab3bc54fee <https://www.ti.com/lit/an/snoa664/snoa664.pdf>
- research/sources/nonlinea.pdf tier vendor-appnote sha256 649dd7b461c8 <https://www.vishay.com/docs/60108/nonlinea.pdf>
- research/sources/sprad89.pdf tier cross-vendor sha256 ef908df544ab <https://www.ti.com/lit/pdf/sprad89>
Task file: boards/bb-adc/research/tasks/block-resistive-attenuator-1.json

## 2026-08-16 [P2][agents][parallel][pipeline] The session scratchpad is shared across concurrently running agents and its filenames are not collision-safe

A researcher writing a PDF crop helper to the session scratchpad as `crop.py` had it
OVERWRITTEN mid-run by a sibling agent doing the same thing under the same obvious
name. No damage this time - the first agent had finished cropping - but the failure
mode is silent and ugly: agent A's script is replaced by agent B's between A writing
it and A running it, so A executes B's code and reports results for the wrong input.

The scratchpad path is per-SESSION, not per-agent, and a full-run spawns many agents
concurrently. Obvious names collide precisely because they are obvious: `crop.py`,
`tmp.json`, `extract.py`, `out.pdf`. Nothing in the harness namespaces them.

Two habits fix it, and orchestrators should put one of them in the spawn prompt when
running agents in parallel: give every scratch file a name unique to the agent's task
(`crop-<task-id>.py`), or have each agent create and work inside its own subdirectory
of the scratchpad. Prefer the subdirectory - it also keeps a failed run's debris
identifiable afterwards.

Worth noting the same hazard is already handled correctly one level up: research
outputs are workspace-first (`<ws>/research/...`) and gate commits are workspace-
scoped, which is why four concurrent researchers could not corrupt each other's
records. Only the scratchpad is unprotected.

## 2026-08-16 [P2][research][agents][pipeline] A second reader's non-binding "blemish" note made a CORRECT record wrong - flag-without-refute has a cost

The research loop has two verdicts, `verified` and `refuted`, and a reader that
notices something minor naturally reaches for a third thing: an advisory note in its
OPEN block. On this run one such note said a figure "reads ~7 %/~15 % against the
record's ~10 %/~20 % (endpoints right)" and did NOT refute. The researcher applied it
as a correction. A later fresh reader then extracted the plot geometry with
PyMuPDF `page.get_drawings()` and measured the truth: **9.8 % at 100 pF and 24.6 % at
300 pF** - the ORIGINAL numbers were the accurate ones, and the "fix" made the record
wrong. The same extraction showed the curve spans only 10.4-604.5 pF, so a third
recorded value "at 1 nF" was off the end of a curve that does not go there.

Why it happens: an advisory note carries the full authority of the reviewer ROLE
while skipping the evidentiary bar of a refutation. A refutation must name a
page-level finding and it flips a record's state, so it gets weighed. A nit reads as
free to apply, so it gets applied - unweighed, by an agent with no standing to
disagree, and often in a later session with none of the reader's context.

Two rules that follow. For readers: if a number is wrong, REFUTE it with the
measurement behind it; if you are not confident enough to refute, mark the note
explicitly do-not-act-without-verifying, and say what measurement would settle it.
For orchestrators relaying nits: pass them as "take or leave, with a one-line reason
either way", never as a fix list - the relay is where an advisory silently becomes an
instruction.

The deeper lesson is about METHOD, not process. Every figure error in this run - in
both directions - came from reading a rendered plot by eye. Every correct settlement
came from extracting the underlying vector geometry or from calibrating a crop
against two known points on the same axes. On a curve whose whole content is a value
at a coordinate, eyeballing is not evidence, and a second eyeball is not a check.

## 2026-08-16 [P2][research][knowledge][block:B4] research task block-series-voltage-reference-1: 7 verified record(s) for block:B4
Gap: research block 'series-voltage-reference': produce its coverage checklist, then populate it
Operating point: {"ambient_max_c": 50, "board_layers": 2, "error_budget_mv": 5.0, "headroom_mv": 1087, "initial_accuracy_max_pct": 0.02, "iout_max_ua": 50, "load_kind": "switched-cap", "output_cap_kind": "datasheet-defined", "pdiss_w": 0.001, "ratiometric_kind": "non-ratiometric", "source_kind": "dc-input", "tempco_max_ppm_per_c": 2, "topology_kind": "series", "vin_min_v": 3.135, "vin_nom_v": 3.3, "vout_v": 2.048}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- series-voltage-reference-error-stack [selection] boards/bb-adc/research/records/series-voltage-reference-error-stack.yaml
- series-voltage-reference-input-headroom-gate [selection] boards/bb-adc/research/records/series-voltage-reference-input-headroom-gate.yaml
- series-voltage-reference-kelvin-and-ir-drop [return-path] boards/bb-adc/research/records/series-voltage-reference-kelvin-and-ir-drop.yaml
- series-voltage-reference-output-cap-window [decoupling] boards/bb-adc/research/records/series-voltage-reference-output-cap-window.yaml
- series-voltage-reference-solder-shift-and-grade [sourcing] boards/bb-adc/research/records/series-voltage-reference-solder-shift-and-grade.yaml
- series-voltage-reference-switched-cap-load [decoupling] boards/bb-adc/research/records/series-voltage-reference-switched-cap-load.yaml
- series-voltage-reference-tempco-box-and-hysteresis [thermal] boards/bb-adc/research/records/series-voltage-reference-tempco-box-and-hysteresis.yaml
Draft coverage checklist(s) for the owner to approve:
- series-voltage-reference boards/bb-adc/research/checklists/series-voltage-reference.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/1599556.pdf tier vendor-layout sha256 86a26b56d5ad <https://www.farnell.com/datasheets/1599556.pdf>
- research/sources/ref70.pdf tier cross-vendor sha256 f32fd3b59b43 <https://www.ti.com/lit/ds/symlink/ref70.pdf>
- research/sources/ref35.pdf tier cross-vendor sha256 a3ba3224bd4f <https://www.ti.com/lit/ds/symlink/ref35.pdf>
- research/sources/snaa320b.pdf tier cross-vendor sha256 3142297a839c <https://www.ti.com/lit/pdf/snaa320>
Task file: boards/bb-adc/research/tasks/block-series-voltage-reference-1.json

## 2026-08-16 [P2][research][knowledge][block:B3] research task block-sar-adc-1: 10 verified record(s) for block:B3
Gap: research block 'sar-adc': produce its coverage checklist, then populate it
Operating point: {"ambient_max_c": 50, "board_layers": 2, "calibration_kind": "uncalibrated", "csample_pf": 48, "error_budget_mv": 5.0, "fclk_khz": 500, "fsample_max_ksps": 10, "gain_err_max_pct": 0.0244, "inl_max_lsb": 2.5, "input_kind": "pseudo-differential-unipolar", "interface_kind": "spi", "iref_max_ua": 7, "offset_max_uv": 1000, "pdiss_w": 0.001, "reference_kind": "external", "resolution_bits": 16, "rsource_ohm": 240000, "source_kind": "dc-input", "tacq_us": 9, "vdd_v": 3.3, "vref_v": 2.048}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- sar-adc-acquisition-charge-transfer [selection] boards/bb-adc/research/records/sar-adc-acquisition-charge-transfer.yaml
- sar-adc-analog-ground-and-remote-sense [return-path] boards/bb-adc/research/records/sar-adc-analog-ground-and-remote-sense.yaml
- sar-adc-constraints-emission [constraints-emission] boards/bb-adc/research/records/sar-adc-constraints-emission.yaml
- sar-adc-conversion-window-noise-timing [sequencing] boards/bb-adc/research/records/sar-adc-conversion-window-noise-timing.yaml
- sar-adc-high-z-node-vs-digital-aggressors [emi] boards/bb-adc/research/records/sar-adc-high-z-node-vs-digital-aggressors.yaml
- sar-adc-input-settling-and-source-impedance [selection] boards/bb-adc/research/records/sar-adc-input-settling-and-source-impedance.yaml
- sar-adc-reference-bypass-and-recharge [decoupling] boards/bb-adc/research/records/sar-adc-reference-bypass-and-recharge.yaml
- sar-adc-reference-charge-loop [power-loop] boards/bb-adc/research/records/sar-adc-reference-charge-loop.yaml
- sar-adc-reference-sets-the-gain [selection] boards/bb-adc/research/records/sar-adc-reference-sets-the-gain.yaml
- sar-adc-supply-bypass-and-rail-isolation [decoupling] boards/bb-adc/research/records/sar-adc-supply-bypass-and-rail-isolation.yaml
Draft coverage checklist(s) for the owner to approve:
- sar-adc boards/bb-adc/research/checklists/sar-adc.yaml (7 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/ads8326.pdf tier vendor-layout sha256 eb82600a4c45 <https://www.ti.com/lit/ds/symlink/ads8326.pdf>
- research/sources/sbaa256b.pdf tier vendor-appnote sha256 1a227467c5bd <https://www.ti.com/lit/an/sbaa256/sbaa256.pdf>
- research/sources/spraby5.pdf tier vendor-appnote sha256 40639c4ad630 <https://www.ti.com/lit/an/spraby5/spraby5.pdf>
- research/sources/00688b.pdf tier cross-vendor sha256 781a43aca4e6 <https://ww1.microchip.com/downloads/en/Appnotes/00688b.pdf>
Task file: boards/bb-adc/research/tasks/block-sar-adc-1.json

## 2026-08-16 [P2][research][knowledge][block:B2] research task block-precision-buffer-1: 9 verified record(s) for block:B2
Gap: research block 'precision-buffer': produce its coverage checklist, then populate it
Operating point: {"ambient_max_c": 50, "board_layers": 2, "cload_pf": 1000, "error_budget_mv": 5.0, "gbw_khz": 350, "ib_max_pa": 400, "input_kind": "cmos", "load_kind": "switched-cap", "pdiss_w": 0.0001, "rsource_ohm": 240000, "settle_ppm": 8, "settle_window_us": 9, "source_kind": "dc-input", "swing_kind": "rrio", "topology_kind": "unity-follower", "vdd_v": 3.3, "vin_max_v": 2.048, "vos_drift_max_uv_per_c": 0.05, "vos_max_uv": 10, "vout_max_v": 2.048, "vout_min_v": 0.0}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- precision-buffer-capacitive-load-isolation [feedback] boards/bb-adc/research/records/precision-buffer-capacitive-load-isolation.yaml
- precision-buffer-chopper-artifacts-into-sampler [emi, selection] boards/bb-adc/research/records/precision-buffer-chopper-artifacts-into-sampler.yaml
- precision-buffer-pin-decoupling-and-input-routing [decoupling, emi, return-path] boards/bb-adc/research/records/precision-buffer-pin-decoupling-and-input-routing.yaml
- precision-buffer-rail-to-rail-output-floor [selection] boards/bb-adc/research/records/precision-buffer-rail-to-rail-output-floor.yaml
- precision-buffer-riso-settling-stability-collision [selection, feedback] boards/bb-adc/research/records/precision-buffer-riso-settling-stability-collision.yaml
- precision-buffer-sar-charge-bucket-interface [selection, feedback] boards/bb-adc/research/records/precision-buffer-sar-charge-bucket-interface.yaml
- precision-buffer-settles-not-bandwidth [selection] boards/bb-adc/research/records/precision-buffer-settles-not-bandwidth.yaml
- precision-buffer-zero-drift-source-impedance-ceiling [selection] boards/bb-adc/research/records/precision-buffer-zero-drift-source-impedance-ceiling.yaml
- precision-buffer-zero-drift-speed-vs-impedance-trade [selection] boards/bb-adc/research/records/precision-buffer-zero-drift-speed-vs-impedance-trade.yaml
Draft coverage checklist(s) for the owner to approve:
- precision-buffer boards/bb-adc/research/checklists/precision-buffer.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/sprpeo2.pdf tier vendor-appnote sha256 7e71f72b8bc3 <https://www.ti.com/lit/ml/sprpeo2/sprpeo2.pdf>
- research/sources/sboa418.pdf tier vendor-appnote sha256 2360f1247772 <https://www.ti.com/lit/pdf/sboa418>
- research/sources/sboa586a.pdf tier vendor-appnote sha256 476e2f692e90 <https://www.ti.com/lit/pdf/sboa586>
- research/sources/opa333.pdf tier vendor-layout sha256 df60da715484 <https://www.ti.com/lit/ds/symlink/opa333.pdf>
Task file: boards/bb-adc/research/tasks/block-precision-buffer-1.json

## 2026-08-16 [P3][parts][jlc][sourcing] LCSC's own datasheet URL can resolve to a "Datasheet temporarily unavailable" stub, and parts_search does not filter that pattern

Sourcing the voltage reference, the LCSC datasheet URL listed for BOTH grades of the
part resolved to a stub page reading "Datasheet temporarily unavailable" rather than
to a PDF. `parts_search.py` already drops JLC placeholder ROWS (no-brand, no-datasheet,
~$0.04 entries), but a real, branded, in-stock part whose datasheet LINK is a stub
passes through as fully sourced. The role's own rule - "no fetchable datasheet =
unverified" - then bites at extraction time, one phase later than it should.

The recovery that worked: the genuine document was reachable through an independent
distributor mirror (`docs.rs-online.com`), cross-checked for page count and file size
against a third listing before being trusted. Two mirrors agreeing on a 32-page,
~1 MB file is decent evidence you have the real document.

Two things fell out of the same episode, both worth more than the stub itself:

**Do not trust an AI web-search summary for a datasheet revision.** Two separate
search summaries confidently asserted this part was at "Rev G, 05/15/2024" and
"Revision B". Direct inspection of the PDF shows **Rev 0, 4/12** - and that Rev 0 IS
the current revision, still in distribution fourteen years on. A revision claim is
exactly the kind of fact that reads as trivially checkable and is therefore rarely
checked; here it decided whether an 87 mV headroom margin was still valid.

**Reaching a document through a mirror is not the same as knowing it is current.**
The first pass settled the spec from a mirror and correctly logged "Rev 0 (2012) -
re-confirm against the current revision before BOM release". Closing that item needed
a SECOND, independent channel, not a re-read of the same file. The distinction between
"this is what the document says" and "this document is current" has to be carried
explicitly, because the first is cheap and the second is not.

## 2026-08-17 [P4][schlib][python] `place_ic_with_decoupling`'s default `caps_dx` is too small for this library's 2-pin symbols, and it fails as a confusing label-guard error

The default `caps_dx=12.7` puts adjacent decoupling caps 12.7 mm apart. Every 2-pin
symbol pulled into `lib/aiee.kicad_sym` has its pins at +/-5.08 mm from the anchor
(measured: R0805, C0402, C0603, C0805, C1210 all +/-5.08; the 1 nF C0603 alone is
+/-3.81), so a cap's pin-2 stub ends 7.62 mm right of its anchor and the NEXT cap's
pin-1 label anchor lands 7.62 mm left of its own - i.e. exactly on the neighbour's
stub wire. Generation then dies with

    ValueError: label 'VDD_ADC' at (132.08, 114.3) lands on an existing wire run
    (132.08, 114.3)-(134.62, 114.3) - it would merge nets

which names the LABEL, not the spacing, and sends you looking at the net contract.
The guard is doing its job - two nets really would have merged - but the fix is
`caps_dx=25.40`, which is what bb-buck already passes explicitly on every call.
Rule for this library: never take the default; 25.40 mm is the working minimum for a
row of these caps, and the failure is at build time, not silent.

## 2026-08-17 [P4][schematic][erc] KiCad 10.0.3 ERC is indifferent to `no_connect`-typed pins - marker or no marker - so the NC marker is documentation, not compliance

The ADR4520 carries four NIC pins plus a factory test pin, all hand-typed `no_connect`
in the project library (a P3 edit that must survive any re-pull, decision 69a).
Probed both ways on a one-part scratch sheet through `kc.py erc`: five NC markers ->
0 errors / 0 warnings; the same five pins left completely alone -> also 0/0. So the
ERC gate cannot tell "deliberately unconnected" from "forgotten", and neither reading
is enforced by the tool. The markers are placed anyway, because the only place the
datasheet's "Do not connect" can live in the artifact is the artifact.

Same session, second cosmetic fact with a real consequence: `schem_refdes` does not
rotate field text but KiCad does (LEARNINGS root, 2026-08-09), and on a rot-90 symbol
that lands the Value as a VERTICAL string. A 27-character Value ("2-pos 5.08mm screw
terminal") on a connector near the left border then runs clean off an A4 sheet - no
warning, `place_report.residue` still empty, visible only in the rendered PDF. J1 got
the rotation (it separates two otherwise-overprinted net labels) and a short MPN Value
to pay for it.

## 2026-08-17 [P4][schematic][analog] schlib guards labels-landing-on-wires; a hand-drawn wire needs the MIRROR check, and on this board that guard is the only thing between a correct netlist and a silently wrong one

`Sheet._assert_label_clear` rejects a LABEL whose anchor lands on an existing wire run.
Nothing checks the other direction, and this board needs the other direction: `U1`'s
-IN is a dedicated sense run drawn as an explicit multi-segment wire to `R5`'s bottom
pad, carrying no label of its own, so the geometry IS the connection. A segment
crossing any foreign label anchor or pin would merge the sense net into whatever it
touched, and every downstream gate would still pass - ERC sees one net either way,
`netlist_audit` sees `U1.3` on `GND` either way, and both readings are electrically
"correct" because there really is one net.

`gen/root.py` therefore ships `sense_run()`, which builds the path and asserts each
segment clear of every label anchor (recomputed from `Sheet._pin_nets`) and every pin
of every placed component, endpoints excepted. It is also called BEFORE the remaining
labels are placed, so schlib's own guard covers everything that follows: the two
directions together are complete. Verified after the build by dumping the exported net
memberships (14 real nets, `U1.3` and `R5.2` together on `GND` and nothing else joined)
and by asserting all four wire segments are present in the saved file.

## 2026-08-18 [P4][schematic][analog][layout] SUPERSEDES the 2026-08-17 sense-run entry: a remote sense must be its OWN NET with a single-point tie PART - "electrically one net" is the wrong unit of analysis once a pour exists

The 2026-08-17 entry above reasoned that `U1` -IN and the attenuator's bottom node are
electrically one net, so the schematic's job was the WIRE and `constraints.json`'s
`R5` -> `U1` corridor would carry the Kelvin intent into copper. **Both halves are
wrong, and the adversarial review (E1) found it.**

1. **"One net" stops being true the moment a plane is poured.** On the netlist `U1.3`
   was one of SIXTEEN `GND` nodes, indistinguishable from `U1.4`. `planes_gen` connects
   every node of the pour's net, so pin 3 gets a thermal to the B.Cu pour at the
   converter exactly as pin 4 does - and the measurement is then referenced to the pour
   AT THE CONVERTER, which is the error the sense exists to cancel. The drawn wire does
   not survive netlist export; only nets do.
2. **A corridor is a KEEP-CLEAR SWATH, not a connectivity rule.** It reserves area. It
   cannot stop a pour from tying a node, and no gate reads it as if it could.

The fix that works is structural: `/AGND_SENSE` as its own net with exactly three nodes
(`U1.3`, `R5.2`, `R8.1`) and `R8`, a 0 ohm link, as the ONE tie to `GND` at the string
bottom. The pour cannot swallow a net that is not `GND`, so the isolation is now
enforced by connectivity rather than by intent. Residual after the split:
`K*(V_sig - V_S) + Vos`, where the only error term is the J1-return-to-string-bottom
pour offset, input-referred at UNITY and carrying only the string's own 5 uA - sub-1 uV.
`R8` adds ~0.25 uV, leaving -IN six orders inside the -0.3/+0.5 V window.

**The transferable rule: any Kelvin / remote-sense / star-point node needs a NET of its
own and a physical single-point tie (0 ohm link or a deliberate junction), never a
shared ground net plus a placement hint.** Cost here was one Basic 0402-class part from
the same reel family as R6/R7. Corollary worth its own line: `netlist_audit`'s
`_constraint_nets` covers `high_speed`, `power`, `voltages`, `thermal` and `diff_pairs`
- it does NOT read `placement.corridors[].net`, so a corridor naming a net that does not
exist passes silently. Sheets.md s6's "an entry naming a net that does not exist fails
silently" applies to corridors with no gate behind it; check it by hand at P4.

## 2026-08-18 [P4][parts][lib_pull][erc] A freshly pulled symbol comes back with `input` pins into a library whose other symbols were already retyped - and the whole-library fixer would undo a hand-edit

Adding `R8` mid-P4 meant one new `lib_pull.py --lcsc C21189` into a library that P3 had
already put through `lib_pin_types.py` plus a hand-edit. Two things fell out.

**The pull is untyped.** `0603WAF0000T5E` arrived with BOTH pins typed `input` while its
siblings `0603WAF499JT5E` / `0603WAF100JT5E` (same family, same reel, pulled at P3) were
`passive`. Two `input` pins on a passive net is an ERC error waiting to happen, and the
difference is invisible unless you dump pin types - `schlib.py --pins` reports it.

**The whole-library fixer is not the answer.** `lib_pin_types.py` takes `--lib` and no
symbol filter, and it has no NC concept: running it would silently revert `U2`'s five
hand-set `no_connect` pins to `passive` (dry-run-confirmed at P3, decision 69a). So the
repair was a SCOPED text edit - `(pin input line` -> `(pin passive line` inside that one
symbol's block only, with an assert on the expected count - and both facts were verified
afterwards: the new symbol reads `passive`/`passive`, `ADR4520BRZ-R7` still reads
`no_connect` on 1/3/5/7/8. Rule: after any incremental `lib_pull` into an
already-corrected library, diff the pin types of the NEW symbol only, and repair it
scoped. `--overwrite` would have been worse - it re-pulls the parts whose types are the
hand-corrected ones.

## 2026-08-19 [P8][sim][ngspice] `.meas ... param='...'` rejects {braces} - and the measure vanishes with the run still reporting ok

Machine-verified on ngspice 46 through `sim_run.py`. Inside a measure's `param='...'`
expression, `{param_name}` is a hard syntax error - stderr carries `Syntax error:
letter [{]`, `Expression err: ...`, `Cannot compute substitute` - and the measure is
simply ABSENT from the returned dict. `run_circuit()` still returns `status: ok`, so a
deck can lose a third of its measures and look healthy; only counting the measures you
expected catches it. The rules, all probed:

- `param='(vpk-vfin)/vstep*100'` with BARE `.param` names: WORKS.
- `param='(vpk-vfin)/{vstep}*100'`: dropped.
- `AT={t0+tacq}` and `WHEN v(x)={vhi-15.6e-6}`: braces WORK in these clauses.
- a measure RESULT inside a braced clause, e.g. `WHEN v(o1)={vhi+0.5*(vpk1-vfin1)}`:
  rejects the whole circuit (`NameError` from the parser) - braced clauses are resolved
  at parse time, before any measure has a value.

So: braces in `AT=`/`WHEN=`, bare names in `param=`, never a measure result in braces.
The useful corollary is that `param=` over bare `.param` names lets a bounds sidecar gate
a FITTED VALUE directly (`cbulk_uf param='(c5+c3)*1e6'` against the ADR4520's two-ended
1-100 uF window) or a closed-form limit (`qdyn/cbulk*1e6`), with no solver in the path.

## 2026-08-19 [P8][sim][ngspice][opamp] Mixing clamped and unclamped output stages in ONE .dc deck silently corrupts the OTHER instances

`zero-scale-swing` put three copies of the same op-amp boundary model in one `.dc` sweep:
two with `V- = GND` (so at zero scale the output sits exactly ON the `min(max(...))`
rail clamp, where the derivative is zero) and one with `V- = -0.3 V` (TI's contingency
generator, never clamped). The operating point then falls back through `Dynamic gmin
stepping failed` / `True gmin stepping failed` / `source stepping failed` - 63 to 99 of
them across the sweep - and ngspice returns `status: ok` with values that are WRONG FOR
THE INSTANCES THAT WERE FINE ON THEIR OWN: the as-built buffer read a flat ~5 uV across
the whole bottom decade instead of tracking its input, which reads exactly like a real
zero-scale failure. Each instance converges cleanly in isolation.

Two rules. (1) A rail-clamped behavioural output stage and an unclamped one do not share
a DC matrix - sweep the rail between RUNS (it is a `.param`, and that is also how the
seeded defect is applied) rather than between instances. (2) `Warning: ... stepping
failed` on stderr is not cosmetic in a DC bench; treat any of them as invalidating the
whole sweep, because the wrong numbers arrive silently and plausibly. The cheap check
that caught it: run the deck at three `reltol` settings decades apart - real physics is
identical to 5 digits (verified so for every settling number in `acquisition-settling`),
a fallback-corrupted solve is not.

## 2026-08-18 [P8][sim][analog] Seeding a REJECTED PART as the deliberate defect turns a bench into an independent audit of an earlier decision

Every bench on this board was calibrated by mutating one value to the defect it exists
to catch, confirming the bound trips, and reverting. For the settling bench the obvious
mutation was a wrong resistor - but substituting the **rejected amplifier** was
available for free, and it did something a value-mutation cannot.

The OPA333 had been rejected at P2/P3 on three arguments assembled from datasheet
numbers: a GBW floor of 48/(2*pi*t_acq) = 849 kHz against its 350 kHz, its own measured
40.4 us settling curve, and an isolation-resistor interval that looked empty (that third
argument was later WITHDRAWN as an overreach - the vendor equation gives an optimum, not
a maximum). Dropping its model into the settling bench moved the settling error from
**0.136 uV to 4509 uV** - a 33,000x miss of a 15.6 uV budget.

Why this is worth more than an ordinary seeded defect: the rejection had been argued
across two phases, partly on a leg that turned out to be wrong, and re-derived from a
different datasheet's timing section. A defect seed that reproduces a REAL earlier
decision closes the loop on it with a different method entirely - simulation rather than
datasheet arithmetic - and would have flagged a rejection made for bad reasons.

Generalise: when a bench needs a seeded defect and the project has already REJECTED a
candidate for that exact role, seed the rejected candidate. It costs nothing extra, it
proves the bound discriminates on the axis that actually decided the design, and it
audits a decision that otherwise never gets re-tested.

## 2026-08-19 [P7][stitch_vias][drc][kicad] stitch_vias' hole-to-hole model is 0.3 mm too permissive - KiCad measures hole EDGE to hole EDGE, so the tool ships DRC errors it cannot see

stitch_vias' docstring pins its spacing model as "EDGE_GAP = 0.5 - 0.3 = 0.2 mm - identical
to the S11-verified 0.5 mm CENTRE floor for two standard 0.3-drill vias". That equivalence
is wrong, and it is wrong in the unsafe direction.

THE ARITHMETIC. KiCad 10 measures `hole_to_hole` between hole EDGES, so what the rule sees is

    measured = centre_spacing - drill_diameter        (both drills 0.30 mm)

On this board stitch_vias proposed a GND via at (41.85, 39.85) for U3.2 while an existing
0.6/0.3 GND via sat at (41.60, 40.40): centre spacing sqrt(0.25^2 + 0.55^2) = **0.604 mm**,
comfortably past its own 0.5 mm model floor. Applied to a scratch copy of the finished board,
that exact spacing produces a hard error:

    error hole_to_hole | Drilled hole too close to other hole
                       | (rule 'aiee_hole_to_hole_floor' min 0.4995 mm; actual 0.3042 mm)

0.604 - 0.30 = 0.304, matching the reported 0.3042 exactly. So a 0.5 mm hole_to_hole rule needs
**0.8 mm centre-to-centre** for two 0.3-drill vias, not 0.5 mm: everything stitch_vias places in
the (0.5, 0.8) mm band next to an existing same-net via is a violation its own check passes and
the gate then fails on. The band widens with drill size - the floor is always
`rule + drill_a/2 + drill_b/2` centre-to-centre.

SECOND TRAP, same op. `already_stitched` is a **0.2 mm pad-centre-to-via proximity test**, so a
pad properly connected by a short track to a via 0.9 mm away is reported as needing stitching at
all. 11 of 12 GND SMD pads here were correctly skipped; the 12th was electrically stitched
already and still generated a proposal.

MITIGATION. Always run `--dry-run` first and treat every proposal as a candidate **LOCATION**,
not as an addition to apply. Measure each proposed `at` against the existing same-net vias with
the arithmetic above before writing anything. On this board the proposed spot was directly under
the pad and strictly better than what was there, so the right answer was not to add the via but
to **REPLACE** the existing one - and the jog track that had forced the offset via disappeared
with it, shortening the op-amp's V- return and leaving more guard copper inside the ring. A
proposal that is illegal as an addition is often correct as a relocation.

## 2026-08-19 [P7][planes_gen][guard-ring][analog] A driven guard ring is a planes_gen zone with connect:solid - and closure is a provable geometric property, not an eyeball

The /AIN_DIV tap on this board (~240 kohm Thevenin) needs a guard ring poured on
/AIN_BUF, the buffer OUTPUT - same potential, low impedance (record
`resistive-attenuator-high-z-tap-guard-and-leakage`). Two things made it buildable
without hand-drawing a trace loop:

1. **planes_gen builds it.** One entry in a `planes` sidecar -
   `{"net":"/AIN_BUF","layer":"F.Cu","region":[40.40,37.90,45.20,43.20],"priority":1,
   "connect":"solid","min_width":0.25}` - and KiCad's own filler forms the ring, because
   the fill flows around every foreign pad at clearance and merges with the same-net pad
   it must be driven from. `connect: solid` is load-bearing: with the default thermal
   relief the fill does NOT merge with U3.1's pad and the ring never closes through it.
   Gotcha: planes_gen REJECTS unknown keys on a `planes` entry - a `_why` string, which
   every other constraints.json section carries, is a hard `CheckError: planes[0]: unknown
   keys ['_why']`. Park the rationale in a sibling key on the sidecar root.

2. **The region is chosen from the CHANNELS, not from the node.** Copper 0.127 wide plus
   2 x 0.127 clearance needs 0.381 mm, so the 0.35 mm SOT-23-5 pin1/pin2 and pin2/pin3
   channels cannot carry the ring at all - the closed ring has to encircle the V- pin
   TOGETHER with the +IN pin, and V- escapes straight down through its own via. The four
   legs run through the channels that DO fit: the 1.5 mm inter-row channel under the
   package (north), the 0.87 mm channels under the two adjacent 0805 bodies (west/east),
   and open board south of the string.

3. **Closure is a test, not a judgement.** Union the net's F.Cu copper (fill + pads +
   tracks); the ring is closed iff that union is ONE polygon carrying an interior ring
   (a hole) that `contains()` the whole guarded net's copper. Here: 1 polygon, 1 hole,
   `contains(/AIN_DIV) == True`, minimum ring copper width 0.612 mm, guard-to-node gap
   exactly 0.127 mm (the DRU floor - the guard sits as tight as it is legal to sit).
   Re-run it after EVERY refill: route_auto, route_edit + refill and plane_repair all
   restate the fill, and a ring that closed before the autoroute is not evidence about
   the ring that ships.

Anything placed inside the ring must exist BEFORE the pour, because KiCad's filler leaves
no room for a via added later: the V- escape via and both /AIN_DIV traces were laid with
route_edit first, and the fill formed around them.

## 2026-08-19 [P8][check_return_path][geom][kicad] `--verify-fill` is broken by a missing `.kicad_dru`, NOT by a fill-model disagreement - and it mis-measures every ai-ee board

`check_return_path --verify-fill` dies on this board with

    StaleFillError: zone 0 on F.Cu: committed fill 17.176 mm^2 differs from fresh 6.613 mm^2 (> 1%)

The tempting reading - "KiCad's filler disagrees with the checker's own independent fill
model, so a `connect: solid` zone cannot be verified" - is WRONG on both halves. There is no
independent model: `geom.BoardGeom.assert_fresh(refill=True)` calls `_refill_copy()`, which runs
the real `kicad-cli pcb drc --refill-zones --save-board` on a temp copy. Both numbers are KiCad's.

The actual cause is a missing sidecar. `_refill_copy` copies the `.kicad_pcb` and, explicitly,
"the sibling .kicad_pro if present (keeps DRC rules identical)" - but **not the `.kicad_dru`**.
Measured three ways on the finished board, reading the guard zone and the GND pour:

    staged files              guard F.Cu     GND B.Cu
    pcb + pro + dru           17.176 mm2     1745.233 mm2   <- EXACTLY the committed fill
    pcb + pro (_refill_copy)   6.613 mm2     1728.589 mm2
    pcb alone                  6.613 mm2     1728.502 mm2

The `.kicad_pro` makes no difference at all; the `.kicad_dru` makes all of it. Without the DRU,
`aiee_clearance_floor (min 0.127 mm)` is gone and KiCad refills at its stock 0.2 mm default. The
loss is not proportional: wider clearance drops narrow passages under the zone's 0.25 mm
min_thickness, those passages vanish, and island removal then culls whatever they were feeding -
so 0.073 mm of extra clearance destroyed 61% of the guard pour.

BLAST RADIUS. `rules_gen` writes a `.kicad_dru` for every ai-ee board, so `--verify-fill`
mis-measures every one of them - this is not a `connect: solid` quirk. The READ path is safe
(the copy is discarded, and the gate does not pass `--verify-fill`), but the same omission in
any WRITE path would commit a silently wrong fill. Verified NOT affected here: planes_gen,
route_auto and route_edit stage the board with its same-stem sidecars, and every fill they
produced matched the pcb+pro+dru number.

## 2026-08-19 [P7][check_return_path][routing] An unavoidable layer-change crossing stops being an ERROR when the crossing lands inside the transition via's excision disk

`check_return_path` grades severity ONLY on centerline crossing length -
`sev = "error" if crossing >= CROSSING_ERROR_MM else "warning"`, and `CROSSING_ERROR_MM = 0.01`.
So shortening or straightening a crossing never clears it; the centerline must not cross
surviving deficit at all. What removes deficit is the excision step: a disk of
`item_radius + ALLOW_CLEARANCE_MM (0.65)` around each single via - 0.95 mm for a 0.6 mm via.

This board's SPI fan needs 2 crossings (J2 orders CS,SCLK,DOUT; the converter orders
CS,DOUT,SCLK - a 3-cycle, so /CS must cross both). The crossings are topologically forced: /CS's
B.Cu tunnel MUST pass under both F.Cu traces, so "move it under bare board" is not available.
What IS available is moving the tunnel so each crossing sits inside a transition via's disk.

    before: one 4.39 mm tunnel, 45 deg diagonal, single via
            /SCLK  ERROR   0.73 mm2, 0.64 mm crossing
            /DOUT  warning 0.09 mm2, 0.00 mm crossing  <- already excised, 0.53 mm from the via
            /CS    ERROR   2.35 mm2, 1.81 mm crossing

    after:  1.93 mm tunnel, PERPENDICULAR, via pair straddling both crossed traces
            (66.000, 40.980) via -> B.Cu -> via (66.000, 39.050); /DOUT crossed at 0.65 mm
            from the south via, /SCLK at 0.63 mm from the north via, both < 0.95 mm
            /SCLK  gone      /DOUT  gone      /CS  error 0.20 mm2, 0.03 mm (-91% / -98%)

/DOUT was the tell: it already passed as a warning purely because its centerline happened to
cross 0.53 mm from the existing via. Reading WHY one of three sibling nets passed gave the rule.

This is physics, not checker-gaming: where the pour void under the aggressor is the transition
via's own antipad rather than a slot, the return current detours around a small disk instead of
running the length of a cut. The routing rule: put the layer transition as close to the crossed
trace as DRC allows (via edge + clearance + half the crossed trace), and cross perpendicular.

COROLLARY, and a real design margin: this board's driven guard ring CLOSES at the DRU's 0.127 mm
clearance and does NOT close at 0.2 mm - refilled at 0.2 the /AIN_BUF pour drops 19.03 -> 8.68
mm2, the entire south leg is culled and the closure test finds ZERO holes. The ring still fills,
still looks like copper in a render, and is no longer a guard. Any change to the clearance floor
or fab class must re-run the closure proof.

## 2026-08-19 [P8][footprint][silk][review] `CONN-TH_2P-P5.00_WJ500V-5.08-2P` draws its silk entry arrows on the OPPOSITE face from its own 3D model's openings - a render of a footprint cannot outrank the part geometry it draws

J1 (library footprint **`CONN-TH_2P-P5.00_WJ500V-5.08-2P`**, `lib/aiee.pretty`) shipped rotated 180 degrees: its wire throats faced
EAST, into the board. A render check had "confirmed" the orientation and passed it. The
render was not misread - the artifact lied.

The footprint contradicts itself. Its pads sit on local y = 0 and its body is ASYMMETRIC
about that pad row: F.Fab spans local y -5.64 .. +4.52 and F.CrtYd -5.5 .. +4.5, so the
**4.50 mm face is local +y** and that is the wire-entry face on the vendor drawing (two
3.0 mm openings, z 3.0-9.8, centred x = +/-2.54; the -y face is a solid wall). But the
two `fp_poly` entry ARROWS on F.Silkscreen are drawn on local **-y** - the solid face.
Arrows and throats point at opposite faces, so any check that reads the silk concludes
the exact opposite of the truth, and does so confidently.

THE TEST THAT WORKS. Measure the body asymmetry about the pad row from fab/courtyard
geometry and match it to the vendor number, then apply the footprint transform yourself.
At rot 90 KiCad maps local +y -> board +x, so the 4.52 face pointed east (into the board);
at rot -90 it maps local +y -> board -x. After rotating, the courtyard reads x[19.955,
30.045] about a pad row at x = 24.500 - west face 4.545 mm, east 5.545 mm - so the 4.50
wire-entry face now points west, out of the board edge. That is a number, not a picture.

CONSEQUENCES BEYOND THE ROTATION. (a) The pads SWAP: a 180-degree rotation of a 2-pin
connector exchanges the nets at the two positions, so every net on it must be ripped and
re-routed - here /AIN_RAW moved from y 41.600 to 36.520 and GND took its place. (b)
place_edit REFUSES a footprint move on a routed board ("rip the affected nets FIRST, then
move, then route fresh"; --allow-routed to override) - obey it, do not reach for the flag
first. (c) THE ARROWS ARE PRINTED SILK, not just a library annoyance - they ship in F.SilkS on
the fabricated board, so a corrected "SIG"/"GND" label and a contradictory arrow end up
millimetres apart and a user who trusts the arrow is actively misled.

FIXING THE ARROWS ON A BOARD INSTANCE IS UNOWNED. No pipeline writer can touch a
footprint's `fp_poly`: place_swig's silk ops are TEXT only (add_text / remove_text /
move_text, and remove_text matches `board.GetDrawings()` - board-frame gr_text - so it
cannot see footprint children); route_edit does tracks/vias; board_edit does Edge.Cuts;
fpfix takes `--lib <dir>.pretty` and never a board. Corrected here with a minimal SWIG
worker following place_edit's own contract (stage a copy beside the board, edit under
bundled python, re-parse + DRC the copy, os.replace only on success). PIPELINE GAP worth
closing: a `mirror_fp_graphic` / `remove_fp_graphic` op on place_swig.

THE MIRROR AXIS IS THE BODY, NOT THE PAD ROW. J1's silk body lines sit at x 19.855-20.105
(west) and 30.015-30.265 (east), so the body's own axis is x = 25.06 - mirroring the arrow
polys about THAT maps them onto the opposite face preserving their exact 0.015 mm abutment
to the body outline, and reflecting along the arrow's own axis reverses head and tail, so
the glyph stays a valid arrow pointing inward. Mirroring about the PAD ROW (x = 24.5)
instead would have overhung the body by ~1 mm and collided with the new "SIG" label.
Arrows moved x[27.000, 30.000] -> x[20.120, 23.120]; DRC 0, check_silk 0.

The LIBRARY is still wrong and is deliberately NOT patched from here (a re-pull reverts
it): anyone reusing `CONN-TH_2P-P5.00_WJ500V-5.08-2P` inherits the same trap.

## 2026-08-19 [P7][guard-ring][silk][drc] Guard-ring leakage is set by what is INSIDE the ring - and the cheapest fix can be re-routing the GUARDED net, not moving the offender

Review priced GND conductors inside the closed /AIN_BUF guard ring at 0.227 / 0.289 /
0.350 mm from the guarded node - about 1.20 mV at the terminal on blocks.md's 1 Gohm
model, against 0.78 mV the guard exists to stop. The ring cannot intercept a leakage path
that STARTS inside it.

U3 pin 2 (V-) is irreducibly inside: the pin2/pin3 channel is 0.350 mm and copper needs
width + 2 x clearance = 0.381 mm at the 0.127 mm floor, so the ring must encircle pin 2
together with pin 3. "Move the via out of the ring" is likewise unreachable - the pad it
serves is inside, so any conductor touching it is inside.

What actually worked was re-routing the GUARDED net. Both sub-0.35 mm paths (0.227 and
0.289) were to the same thing: the /AIN_DIV stub running down the WEST side of the pocket,
right past the GND via and pin 2. /AIN_DIV is a 3-pad net (R3.2, R4.1, U3.3) whose
spanning tree can take the stub off EITHER resistor for the SAME 2.600 mm. Moving it from
R3.2->U3.3 to R4.1->U3.3 - identical length, requirement "keep /AIN_DIV short" untouched
at 4.600 mm total - put the stub on the east side and deleted both paths outright. With
the via also nudged 0.2 mm west, the two GND conductors inside the ring now measure 0.350
mm (pin 2, the irreducible pin gap) and 0.556 mm (the via). Scaling review's own 1/d model
that is roughly 1.20 -> 0.52 mV, i.e. under the 0.78 mV the guard stops.

Generalise: before moving the offending conductor, check whether the GUARDED net has a
degenerate spanning tree. Re-routing the victim can be free where moving the offender is
blocked.

SILK GOTCHA from the same pass: `add_text` at size 0.7 draws a `text_height` DRC error -
board setup enforces a 0.8 mm silk minimum. `check_silk` does NOT catch it (it is lenient
by design and never the oracle); `kicad-cli pcb drc` does. Size every scripted silk string
at >= the board's own minimum and verify with kc drc.

## 2026-08-19 [P6][P8][library][placement] A footprint can contradict ITSELF, and then a render check certifies the wrong orientation

`CONN-TH_2P-P5.00_WJ500V-5.08-2P` in `lib/aiee.pretty` draws its silk wire-entry arrows
on the OPPOSITE face from its own 3D model's openings. The placement agent did the right
thing - it explicitly refused to trust the seed rotation and PROVED the mating direction
with an orthographic side render - and got the wrong answer, because the render faithfully
rendered a lie. The board went to routing with a screw terminal whose wire throats faced
INTO the board: the field lead would have had to enter from the interior and lay back
across the 1 Mohm string and the header ribbon.

A fresh-context reviewer caught it by going to the 3D model's actual opening geometry
(two 3.0 mm openings, z 3.0-9.8 mm, on the local +y face; the opposite face solid) and
applying the rotation transform. The vendor drawing settles it: the body is ASYMMETRIC
about the pin row, 4.50 mm on one side and 3.14 mm on the other, and the openings are on
the 4.50 side. That asymmetry is the check - it is a NUMBER, not a picture.

The rule to carry: **a render of a footprint cannot outrank the part geometry it draws.**
When orientation matters (any connector with a mating direction), verify against a
dimensioned asymmetry - courtyard or fab-layer extents about the pad row - or against the
3D model, and treat footprint silk as decoration. Cost here: a full placement round-trip,
a re-route of two nets, and the discovery that a 180-degree rotation SWAPS THE PADS, so
"just rotate it" without re-routing would have shipped a differently-wrong board.

Two follow-ons worth having. The library footprint is deliberately NOT patched - a re-pull
reverts it - so anyone reusing it inherits the trap. And the wrong arrows were also
PRINTED on the board instance, next to correct SIG/GND text: a user trusting the arrow
over the text is actively misled by the board. Fixing that exposed a pipeline gap - no
scripted op owns footprint-instance graphics (`remove_text` matches `board.GetDrawings()`,
i.e. board-frame `gr_text` only; `route_edit` does copper, `board_edit` does Edge.Cuts,
`fpfix` takes a `.pretty` and never a board), so it needed a one-off SWIG worker built on
`place_edit`'s stage-verify-replace contract. A `mirror_fp_graphic` / `remove_fp_graphic`
op on `place_swig` is the gap worth closing.
