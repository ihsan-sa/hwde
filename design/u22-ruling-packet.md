# U22 ruling packet - bb-* harvest (PREP MODE, 2026-08-31)

Prepared unattended per `ai-ee-v3-plan.md` "### U22" prep-mode paragraph. Nothing is
approved and no queue entry is resolved: every row below is a RECOMMENDATION (marked
**REC**) in U14's question-set form - the owner rules each set "as recommended" or
overrides row by row, then the owner session performs the writes (section 7).

Scope: `boards/bb-{adc,amp,buck,ldo,mcu}/research/records/` (82 records) +
`learnings/queue.yaml` (88 pending rows = 10 research-task rows + 78 workspace
learnings). Library (`reference/knowledge/records/`, 16 approved) read only.

## 0. Dedupe stats (in -> out)

| | in | out |
|---|---|---|
| research records | 82 | **81** (1 merge: 2 -> 1, staged `design/u22-staged/records/in-bias-current-return-path.yaml`, maturity `verified`) |
| records if Q1.2 row 1 is taken (fold into a library record) | 81 | 80 |
| queue rows | 88 | 88 (none resolved - owner only); Q6 lists learning-level duplicates |

The harvest was topology-partitioned (one research task per block), so the SAME rule
appearing on two boards is rare; most cross-workspace neighbours share a class, not a
mechanism (Q1.3). Contradictions are listed in Q3 and never averaged.

## 1. Q1 - dedupe / merge proposals

### 1.1 Merges (same rule, sources accumulate)

| # | records | why one record | **REC** |
|---|---|---|---|
| 1 | bb-amp `in-bias-current-return-path` (principle, draft, task in-1, INA333) + `in-bias-return-path-required` (topology, verified, task in-2, AD8226 + AN1298) | Same rule: both inputs need a DC path to the amplifier's ground. The verified record's own envelope note says "the requirement itself does not scale" - its `ibias_ua` 5-35 nA envelope is the AD8226's spec span (U14 mistake 1), so by the U14 discipline this is a **principle**. | **Accept merge.** Staged: principle, no envelope, 5 sources (AD8226 p22/p5 + AN1298 p14 verified 2026-08-16; INA333 p16/p17 carried from the draft, NOT second-read - see Q5). On approval: `research.py promote` the staged file, mark both workspace records `status: superseded`. `in-bias-return-resistor-sizing-ad8226` (part) and `in-bias-return-sizing` (topology) stay as the sizing children. |

### 1.2 Overlap with the approved library (owner edits an approved record, or keeps both)

| # | workspace record | library record | finding | **REC** |
|---|---|---|---|---|
| 1 | bb-buck `buck-precision-en-fixed-softstart` (principle) | `buck-en-softstart-sequencing` (principle, approved) | Same rule ("read the EN pin's own behaviour before adding parts"). New record adds: EN "do not float" on this part class, precision start/UVLO thresholds, fixed soft-start. Both principle -> a `generalizes` link is illegal (U14 deviation 2). | **Fold into the library record**: 3 facts + 6 sources accumulate, re-approve with the ruling as note. (Override: keep both, unlinked - costs a permanent duplicate injection.) |
| 2 | bb-buck `buck-integrated-fet-bypass-trio` (topology, integrated-fet) | `buck-bst-fb-output-caps` (family, integrated-fet, approved) | Both cover BST/VCC/input bypass on integrated parts; trio = three short-loop PLACEMENT items, library = values. Not read side by side this session. | **Keep both**; owner reads both once at approval; if the values duplicate, drop them from the trio's `rule` and leave the loops. |
| 3 | bb-buck `buck-ep-agnd-thermal-via-array` (topology, integrated-fet) | `buck-thermal-via-and-via-current` (topology, pdiss_w<=5) | Different mechanism: EP is AGND -> the via array is a reference-integrity item, not only heat/current. | **Keep both, no envelope union** (dims differ because the mechanisms differ). |
| 4 | bb-buck `buck-dc-input-hot-plug-overshoot` (topology, source_kind dc-input) | `buck-upstream-inrush-limit` (topology, source_kind usb/usb-pd/poe) | Complementary partition of `source_kind`; mechanisms differ (LC hot-plug ring vs. source current budget). | **Keep both; do NOT union `source_kind`** - the record text says so itself. |
| 5 | bb-buck `buck-sync-hot-loop-cin-placement` (topology, sync) | `buck-freewheel-diode-snubber-placement` (async) / `buck-cin-co-ground-separation` (hard) | Sync-side complement of the async record; already `generalizes: [buck-input-hot-loop]`. | **Keep**; link stands. |
| 6 | bb-buck `buck-cmode-inductor-window` (family, cmode) | `buck-inductor-selection` (topology) | Child, already `generalizes` it. | **Keep**; link stands. |

### 1.3 Cross-workspace neighbours checked and KEPT SEPARATE (same class, different mechanism)

| group | records | why not one record |
|---|---|---|
| decoupling / return-path principles | mcu `decoupler-is-the-local-source`, `supply-pin-pair-decoupling`, `supply-return-continuity`; amp `inamp-supply-decoupling-and-local-ground`; adc `precision-buffer-pin-decoupling-and-input-routing`, `sar-adc-supply-bypass-and-rail-isolation` | digital edge current spikes / per-pin-pair count / 50 mV return budget / precision supply quality / RFI-as-offset / RC rail isolation - five mechanisms, vendor pages per topology |
| constraints-emission | adc `sar-adc-constraints-emission`, amp `in-constraints-emission`, buck `buck-constraints-emission-layout-groups` (+ lib `buck-constraints-emission`) | per-topology emission CONTRACTS (what a block must emit into constraints.json); same pattern, different content - like the U14 precedent |
| high-Z node vs aggressors | adc `sar-adc-high-z-node-vs-digital-aggressors` (error_budget_mv<=20), amp `in-aggressor-separation` (draft; output-to-input ratio) | different aggressor (digital edges into converter nodes vs. the amplifier's own output back into its input) |
| leakage / guarding | adc `resistive-attenuator-high-z-tap-guard-and-leakage` (rthev>=100k), amp `in-leakage-symmetry-and-guarding` (draft; rsource<=1M) | same physics (I_leak x R_node) but different remedy set (guard vs. symmetry-first) -> contradiction C1 in Q3 |
| thermal | ldo `copper-is-the-heatsink` (principle), `tab-copper-area-theta-ja`, `live-tab-thermal-vias`; mcu `package-power-budget`; adc `resistive-attenuator-self-heating-and-gradient` | copper-as-heatsink vs. live-tab stitching vs. package budget vs. resistor gradient |
| sequencing | mcu `analog-rail-tracks-digital-rail`; buck `precision-en-fixed-softstart`; mcu `swd-debug-port-nrst-on-the-header` | rail tracking vs. enable pin vs. reset pin |
| switched-cap charge (within bb-adc) | `sar-adc-acquisition-charge-transfer` (principle) <- `precision-buffer-sar-charge-bucket-interface`, `sar-adc-input-settling-and-source-impedance` (linked); `series-voltage-reference-switched-cap-load`, `sar-adc-reference-bypass-and-recharge`, `sar-adc-reference-charge-loop` (unlinked) | one principle seen from buffer / input / reference; **REC** add `generalizes: [sar-adc-acquisition-charge-transfer]` to the three unlinked records (cross-topology parent is legal: principle > topology) |

## 2. Q2 - level + "what does this rule scale with" sanity

All 82 envelope notes were checked against the U14 test ("where does this stop being
TRUE?", not "what numbers does it carry"). Flagged rows below; every other verified
record: **REC approve level + envelope as proposed** (their notes name a real bound:
switching kind, load kind, control kind, node impedance, error budget, output voltage
for the low-VOUT dropout effect, dissipation for the free RC isolation, etc.).

| # | record | as proposed | problem | **REC** |
|---|---|---|---|---|
| 1 | amp `in-bias-return-path-required` | topology, ibias_ua 5-35 nA | part spec span, rule does not scale | merged -> principle (Q1.1) |
| 2 | amp `in-bias-return-failure-signature` | topology, ibias_ua 5-35 nA (AD8226 Table 3) | bound is one part's Ib span; `applies.parts` is already [AD8226] | level **part** (honest to its bound); alt: topology with `ibias_ua: {max: 0.1}` |
| 3 | adc `precision-buffer-pin-decoupling-and-input-routing` | topology, board_layers {min: 2} | vacuous on every ai-ee board = filler envelope (U14 mistake 2) | **principle**, drop envelope |
| 4 | adc `precision-buffer-rail-to-rail-output-floor` | family, vout_min_v 0-0.1 | "family" with no family key (no parts, no *_kind) | **topology**, same envelope |
| 5 | adc `precision-buffer-zero-drift-source-impedance-ceiling`, `-zero-drift-speed-vs-impedance-trade`, `-chopper-artifacts-into-sampler` | family / family / topology, numeric or load_kind only | the family is "zero-drift", but nothing keys it - not retrievable by kind | add `amp_kind: {in: [zero-drift]}` (cot/cmode precedent); levels stand |
| 6 | ldo `linear-regulator-fixed-variant-min-load` | family, iout_a {max: 0.8} | 0.8 A is where the SPEC ROWS stop (U14 mistake 1); the rule is bounded by the variant | envelope `variant_kind: {in: [fixed]}` (declarable at P2), keep family |
| 7 | mcu `swd-debug-port-nrst-on-the-header` | family, vio_v 2.7-3.6 | its own note says the reset-pulse spec exists over 2.4-3.6 (500 ns); sibling record uses 2.4-3.6 for the same parts | widen to **2.4-3.6** with the 500 ns clause in `rule` (see C2) |
| 8 | amp `in-terminal-selection` | family, rsource_ohm {min: 1} | "family" with no key | **topology** |
| 9 | amp `in-cable-shield-termination` | topology, vcm_v 0-5 | bound = the witnessed 5 V single-supply regime, not the mechanism | accept as proposed (flagged); alt `supply_kind: {in: [single]}` |
| 10 | adc `resistive-attenuator-tcr-tracking-not-absolute-tcr`, `series-voltage-reference-tempco-box-and-hysteresis` | topology, ambient range -55/-40..125 | spec-range envelopes (rule stays true outside; only the numbers stop being characterised) | accept (board_layers precedent, U14) - flagged so the owner can rule "principle" instead |
| 11 | dim vocabulary drift | adc `ambient_max_c` vs mcu `tamb_max_c`; adc `iout_max_ua` vs ldo/lib `iout_a`; amp `vs_v` / mcu `vio_v` / lib `vin_v`; amp `f_signal_hz` | P2 must declare every dim by exact name or the record sits provisional forever (LEARNINGS 295) | normalise at promotion: `tamb_max_c` -> `ambient_max_c`; `iout_max_ua` -> `iout_ua`; keep `vs_v`/`vio_v`/`vin_v` (different rails) but add all new dims to `agents/architect.md` + `reference/constraints_schema.md` |

## 3. Q3 - contradictions (listed, never averaged - the owner picks)

| # | A | B | disagreement | **REC** |
|---|---|---|---|---|
| C1 | adc `resistive-attenuator-high-z-tap-guard-and-leakage`: a guard is worth its copper above **100 kohm** node impedance (source written for 10 M-1 G) | amp `in-leakage-symmetry-and-guarding` (draft): below **1 Mohm** symmetry suffices, guard above | when does a guard earn its layout cost: 100k vs 1M | keep both thresholds in their own records (single-ended tap vs. differential pair where symmetry is an option); do not average; the in- record needs its second read first |
| C2 | mcu `swd-debug-port-nrst-on-the-header`: vio_v 2.7-3.6 | mcu `swd-debug-port-stm32f0-internal-pulls`: vio_v 2.4-3.6 | same parts, two supply bands | take Q2 row 7 (both records' own pages support 2.4-3.6) |
| C3 | amp in-1 `in-bias-current-return-path`: **principle** | amp in-2 `in-bias-return-path-required`: **topology** + Ib envelope | level of the same rule | principle (Q1.1) |

No contradiction of an engineering NUMBER was found between records of different boards.

## 4. Q4 - approvals (owner-only flip; nothing set here)

- **Records**: **REC approve** all verified records - 75 workspace records (76 verified
  minus the one merged away) + the staged merge = **76**, after the Q2 edits on rows
  2-8 and the Q1.2 row-1 fold. Approval note = the record's envelope note (the U14
  form: "what it scales with"). Draft records (Q5) are NOT approvable.
- **Checklists** (9, all `maturity: draft`, every row `min_level: topology`):
  `linear-regulator`, `mcu`, `swd-debug-port`, `inamp`, `in`, `precision-buffer`,
  `resistive-attenuator`, `sar-adc`, `series-voltage-reference`. **REC approve** (U14
  precedent) AFTER the owner session runs coverage on the synthetic ldo/adc/inamp/mcu
  workspaces: any row whose only covering record is a principle (e.g. a `decoupling`
  or `return-path` row on `mcu`, where 5 of 8 records are principles) must drop to
  `min_level: principle` first (U14 mistake 3).
- **Research-task queue rows** (10: adc 4, amp 4, buck 1, ldo 1, mcu 2... see
  `queue.yaml` titles "research task ..."): **REC `promoted` / kind `knowledge_record`
  / artifacts = the promoted `reference/knowledge/records/<id>.yaml` paths** once
  `research.py promote` has run; the bb-amp in-1 row (1 verified record) resolves
  with the merge + Q5 outcome.

## 5. Q5 - bb-amp stalled drafts (6; `research.py status` exits 1 until ruled)

| record | **REC** | why |
|---|---|---|
| `in-bias-current-return-path` | superseded by the staged merge; its INA333 p16/p17 citations ride in the merge marked "not second-read" - **REC one second read of those two pages** (`research.py verify`) before approval, or `--accept-drafts` if the owner accepts AD8226+AN1298 as sufficient | rule already verified via in-2 |
| `in-bias-return-sizing` | **second read** (keep) | the topology-level sizing fork (rsource/ibias) that in-2 only has at part level |
| `in-leakage-symmetry-and-guarding` | **second read** (keep) | complements the attenuator guard record; carries C1 |
| `in-path-symmetry-sets-cmrr` | **second read** (keep) | the only record stating CMRR = path mismatch x Vcm; envelope note coherent |
| `in-aggressor-separation` | **second read** (keep) | ratio-based envelope is coherent (vout_v>=1, vsig_mv<=100) |
| `inamp-gain-pin-and-input-node-parasitics` | **second read** (keep) | only 2 sources; if the reader refutes, decline `not_actionable` |

None may be approved at `draft`. Budget: 6 second reads; alternative is `research.py
close --accept-drafts` (outcome `verified_with_drafts`, they still cannot satisfy
coverage until approved). The write that clears the exit-1 is `learnings.py compile
--workspace boards/bb-amp` - owner's call when (U21 note).

## 6. Q6 - workspace learnings (78 rows)

Per-row recommendations (promoted kind/level/target or declined reason, already-landed
check against root LEARNINGS + U16-U21, cross-board duplicates, contradictions) are
produced in this track's journal dir (`queue-recs-A.md` bb-adc+bb-amp, `queue-recs-B.md`
bb-buck+bb-ldo+bb-mcu) and are folded into this section by the next prep iteration.
Known cross-board duplicate clusters to rule ONCE: connector wire-entry orientation
(bb-mcu WJ500V / bb-amp KF128 / bb-adc CONN-TH footprint), stitch_vias in-pad + hole-edge
model (bb-ldo x2, bb-adc), planes_gen `connect: solid` (bb-buck, bb-ldo), provisional
outline binds placement (bb-ldo, bb-mcu, bb-amp), fetch allowlist hosts dark (bb-adc,
bb-mcu), Freerouting cannot parse (bb-ldo x2).

## 7. Owner-session mechanics (after the rulings)

1. Per approved record: `research.py promote --workspace boards/bb-X --record <id>`
   (copies sources, rewrites citations); apply Q2 edits; set `maturity: approved` +
   `approval: {by: owner, date, note}`; staged merge: copy
   `design/u22-staged/records/in-bias-current-return-path.yaml` into the library (its
   sources are already repo-relative), mark the two workspace originals superseded.
2. Q1.2 row 1: edit `buck-en-softstart-sequencing` in place, re-approve.
3. `knowledge.py --validate --strict`; re-render topology views that exist.
4. `learnings.py resolve --batch boards/bb-X/learnings/rulings-<date>.yaml` per board
   (research-task rows + Q6 rows), then `learnings.py validate` + `triage`.
5. Root LEARNINGS + `design/ladder-triage.md` rows come from the `root_learnings`
   resolutions (the tool writes them).
6. Acceptance: zero pending across the five queues; coverage at the default floor on
   synthetic ldo/adc/inamp/mcu workspaces shows the new domains covered.

Prep-mode facts for the record: staged record validated with `knowledge.py --validate
--strict --records-dir design/u22-staged/records` (green); workspace dirs validate
strict-green apart from workspace-relative source paths (resolved by `promote`) and
bb-buck's two `generalizes` into the library (resolve once co-located).
