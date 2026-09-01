# U22 ruling packet - bb-* harvest (PREP MODE, 2026-08-31)

Prepared unattended per `ai-ee-v3-plan.md` "### U22" prep-mode paragraph. Nothing is
approved and no queue entry is resolved: every row below is a RECOMMENDATION (marked
**REC**) in U14's question-set form - the owner rules each set "as recommended" or
overrides row by row, then the owner session performs the writes (section 7).

Scope: `boards/bb-{adc,amp,buck,ldo,mcu}/research/records/` (82 records) +
`learnings/queue.yaml` (88 pending rows = 12 research-task rows + 76 workspace
learnings). Library (`reference/knowledge/records/`, 16 approved) read only.

## 0. Dedupe stats (in -> out)

| | in | out |
|---|---|---|
| research records | 82 | **81** (1 merge: 2 -> 1, staged `design/u22-staged/records/in-bias-current-return-path.yaml`, maturity `verified`) |
| records if Q1.2 row 1 is taken (fold into a library record) | 81 | 80 |
| queue rows | 88 | 88 (none resolved - owner only). Q6 rules the 76 learnings: 62 promote / 14 decline (10 cross-board duplicates folded into 7 clusters, 3 covered by verified records, 1 superseded pending C4) |

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

| C4 | mcu `2026-08-16-wj500v-5-08-2p-wire-entry-is`: WJ500V-5.08-2P mouth at local **-Y** (side render of the 3D model; "longer 5.5 mm courtyard side is the mouth") | adc `2026-08-19-conn-th-2p-p5-00-wj500v-5`: mouth at local **+Y** (vendor drawing: openings on the 4.50 mm side, matched to the F.Fab +4.52 extent; silk arrows on -y called wrong) | same footprint, same `.wrl`, `rotate 0` in every workspace copy (checked bb-ldo/adc/mcu/buck-5v3a) - so ONE of bb-mcu / bb-adc has its screw terminal facing into the board | owner settles it against the vendor drawing's pin-1 side (or a part in hand) BEFORE any bb-* order; promote only the METHOD row (K1) now; the losing entry is `superseded`. Not averaged. |

No contradiction of an engineering NUMBER was found between RECORDS of different boards; C4 is between two workspace learnings and has a physical consequence.

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
- **Research-task queue rows** (12: adc 4, amp 4, buck 1, ldo 1, mcu 2; see
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

## 6. Q6 - workspace learnings (76 rows; ruled once per duplicate cluster)

All 76 non-research queue rows, each with a **REC**. `promote` = `status: promoted,
kind: root_learnings` unless another kind is named (the tool appends the root row +
triage row; the ladder column is the triage row's `now -> target` and owner artifact).
`decline` carries its DECLINE kind. Landed check = against root `LEARNINGS.md`
(cited by line) and the verified bb-* records (Q4). Batch-file shape:
`boards/rf-de-20m/learnings/rulings-2026-08-14.yaml`; entry ids are the `entry:` keys.

**Stats: 76 in -> 62 promote (61 root_learnings + 1 prompt_line) / 14 decline
(10 duplicate, 3 covered by a verified record, 1 superseded pending C4).**

### 6.0 Cross-board duplicate clusters (rule once)

| K | cluster | lead (promote) | folded (decline `duplicate`) | one root row says |
|---|---|---|---|---|
| K1 | connector mating direction | adc `2026-08-19-conn-th-2p-p5-00-wj500v-5` | adc `2026-08-19-a-footprint-can-contradict-itself-and-then` (same event retold); amp `2026-08-17-the-kf128-top-view-teeth-are-the` (confirms root L2902; adds: KF128 3D model carries `rotate 180`, teeth = rear); mcu `2026-08-16-wj500v-5-08-2p-wire-entry-is` -> `superseded`, see **C4** | verify a connector's mating face from a DIMENSIONED asymmetry (fab/courtyard about the pad row vs the vendor drawing) or the 3D model - never from silk or a top render; a 180 rotation of a 2-pin part SWAPS its nets; no scripted op owns footprint-instance graphics (`place_swig` gap: `mirror_fp_graphic`/`remove_fp_graphic`) |
| K2 | stitch_vias in-pad | ldo `2026-08-18-stitch-vias-places-vias-inside-large-pads` | ldo `2026-08-20-the-in-pad-defect-reproduces-on-new` | `RING_RADII` from pad CENTRE + `via_check` blind to own pad + no F.Cu stub with a pad via; adc hole-EDGE row (6.1 #19) is a second, separate stitch_vias defect |
| K3 | zone pad connection | buck `2026-08-16-planes-gen-s-default-thermal-relief-pad` | ldo `2026-08-18-no-scripted-way-to-set-a-per` (the inverse case: solid pour, hand-soldered pin, no per-pad relief) | zone `connect` is per-ZONE only: `connect: solid` in a planes-only sidecar rescues a stranded pad; there is no per-pad override either way -> `planes_gen` per-pad `connect` (L3) |
| K4 | provisional outline binds | mcu `2026-08-16-placement-edges-pins-the-connectors-to-the` | ldo `2026-08-18-a-provisional-outline-binds-placement-just-as` (88 vs 50 mm number folded); ldo `2026-08-18-silk-place-solves-against-the-outline-on` (already the lead's second-order trap) | at a `canonical` binding with any `placement.edges`: **place -> fit -> silk -> gate** (root L4586/L4603 are the bb-buck mirror, stated size); amp's two fit rows (6.2 #7, #8) and ldo aspect row (6.4 #19) are distinct mechanisms, kept |
| K5 | fetch allowlist != reachable | adc `2026-08-16-analog-com-and-mouser-com-time-out` (carries the remedy: farnell mirror) | mcu `2026-08-16-being-on-the-fetch-allowlist-says-nothing` | allowlist membership says nothing about reachability; st.com/analog.com/mouser.com dark from this host, farnell.com is the ADI mirror -> `research.py` reachability probe + mirror table (L1) |
| K6 | Freerouting DSN wedge | ldo `2026-08-20-freerouting-cannot-read-this-board-at-all` (residual only) | ldo `2026-08-20-freerouting-2-2-4-cannot-parse-this` | the wedge itself is landed (root L435 2026-07-23, L3662); residual = route_auto still burns every rung x 600 s on a wedge knowable from the first log line -> abort the ladder on a DSN-read StackOverflow (L2) |
| K7 | check_current clustering | ldo `2026-08-18-check-current-charges-every-transition-via-the` | ldo `2026-08-20-via-redundancy-and-check-current-s-clustering` | check_current charges each transition via with the whole net's current, so redundancy is penalised - split across parallel vias (L1 model fix) |

### 6.1 bb-adc (25)

| # | entry | **REC** | ladder / owner | reason, landed check |
|---|---|---|---|---|
| 1 | `2026-08-16-a-blockquoted-brief-silently-disables-the-entire` | promote | L2 -> L2, `scripts/lib/modeslib.py` | PIPELINE BUG: `detect` skips `>` lines, lint goes silently blind; not in root |
| 2 | `2026-08-16-jlc-s-external-reference-attribute-lies-for` | promote | L0 -> L3, NEW `reference/part_errata.yaml` | MCP3202 VDD=VREF one pin; catalog attribute wrong; triage already names the errata file as owner x2 |
| 3 | `2026-08-16-a-12-bit-part-s-5-lsb` | promote | L0 -> L0, `agents/part-sourcer.md` | rank converters by error in VOLTS at the target resolution; knowledge_record candidate later (principle) |
| 4 | `2026-08-16-one-lcsc-search-term-returns-six-clone` | promote | L0 -> L1, `scripts/parts_search.py` | manufacturer column + clone warning; not in root |
| 5 | `2026-08-16-source-impedance-and-divider-total-resistance-are` | decline `duplicate` | - | rule lives in verified `resistive-attenuator-loading-source-and-load` + `sar-adc-input-settling-and-source-impedance` (Q4); a root row would be a second home |
| 6 | `2026-08-16-a-reference-family-s-dropout-is-per` | decline `duplicate` | - | verified `series-voltage-reference-input-headroom-gate` states `specified_per_member` and the inverse-to-Vout split |
| 7 | `2026-08-16-analog-com-and-mouser-com-time-out` | promote (K5 lead) | L0 -> L1, `scripts/research.py` | see K5 |
| 8 | `2026-08-16-the-session-scratchpad-is-shared-across-concurrently` | promote | L0 -> L3, `scripts/state.py` (per-agent scratch subdir) | parallel agents collide on filenames; not in root |
| 9 | `2026-08-16-a-second-reader-s-non-binding-blemish` | promote `prompt_line` | L0, `agents/research-second-reader.md` | one line: a non-binding note is never applied; flag-without-refute has a cost |
| 10 | `2026-08-16-lcsc-s-own-datasheet-url-can-resolve` | promote | L0 -> L1, `scripts/parts_search.py` | filter the "temporarily unavailable" stub pattern |
| 11 | `2026-08-17-place-ic-with-decoupling-s-default-caps` | promote | L0 -> L3, `scripts/schlib.py` | derive `caps_dx` from symbol width; error message misattributes |
| 12 | `2026-08-17-kicad-10-0-3-erc-is-indifferent` | promote | L0 -> L2, `scripts/netlist_audit.py` | audit NC-typed pins that carry a net, ERC will not (root L657 is the export sibling, not this) |
| 13 | `2026-08-17-schlib-guards-labels-landing-on-wires-a` | promote | L2 -> L3, `scripts/schlib.py` | extend the guard to hand-drawn wires (mirror check) |
| 14 | `2026-08-18-supersedes-the-2026-08-17-sense-run` | promote | L0 -> L2, `scripts/netlist_audit.py` | a sense line is its OWN net + single-point tie PART once a pour exists; electrical parent = `series-voltage-reference-kelvin-and-ir-drop` |
| 15 | `2026-08-18-a-freshly-pulled-symbol-comes-back-with` | promote | L0 -> L3, `scripts/lib_pull.py` + `scripts/lib_pin_types.py` | retype on pull, per symbol, never clobber hand edits; sibling of buck #1 (same owner, different defect) |
| 16 | `2026-08-19-meas-param-rejects-braces-and-the-measure` | promote | L0 -> L2, `scripts/sim_run.py` | count `.meas` vs results, fail on a vanished measure; root L2706/L3947 cover `param=` forms, not this |
| 17 | `2026-08-19-mixing-clamped-and-unclamped-output-stages-in` | promote | L0 -> L3, NEW `reference/sim/opamp_behavioural.cir` | same owner as amp #3/#5 (one behavioural op-amp template) |
| 18 | `2026-08-18-seeding-a-rejected-part-as-the-deliberate` | promote | L0, `agents/sim-analyst.md` | bench-design heuristic; prose is its level |
| 19 | `2026-08-19-stitch-vias-hole-to-hole-model-is` | promote | L0 -> L2, `scripts/stitch_vias.py` | floor = rule + drill_a/2 + drill_b/2 centre-to-centre; `already_stitched` 0.2 mm test; root L2954 is THT-drill blindness, a different defect |
| 20 | `2026-08-19-a-driven-guard-ring-is-a-planes` | promote | L0 -> L2, NEW `scripts/check_guard.py` (closure is provable) | separate from K3 (uses `connect: solid` but the fact is the closure proof) |
| 21 | `2026-08-19-verify-fill-is-broken-by-a-missing` | promote | L0 -> L3, `scripts/lib/geom.py` `_refill_copy` copies the `.kicad_dru` | ROOT CAUSE of root L2967 (which blamed a custom DRU); mis-measures every ai-ee board; owner may retire L2967's reading in its triage note |
| 22 | `2026-08-19-an-unavoidable-layer-change-crossing-stops-being` | promote | L2 -> L2, `scripts/check_return_path.py` | false positive: exempt crossings inside the transition via's excision disk |
| 23 | `2026-08-19-conn-th-2p-p5-00-wj500v-5` | promote (K1 lead) | L0 -> L2, `scripts/fp_verify.py` (mating-face asymmetry check) + NEW `reference/part_errata.yaml` | see K1 and **C4** - the orientation CLAIM (+Y) is contested; promote the METHOD, hold the number |
| 24 | `2026-08-19-guard-ring-leakage-is-set-by-what` | promote | L0, `agents/router.md` | leakage = what is INSIDE the ring; re-route the guarded net before moving the offender |
| 25 | `2026-08-19-a-footprint-can-contradict-itself-and-then` | decline `duplicate` | - | K1: same event as #23, folded |

### 6.2 bb-amp (15)

| # | entry | **REC** | ladder / owner | reason, landed check |
|---|---|---|---|---|
| 1 | `2026-08-16-meas-ac-rms-is-frequency-weighted-which` | promote | L0 -> L3, `agents/sim-analyst.md` bench recipe | integrated noise without `.noise`; root L3939's ten traps do not include it |
| 2 | `2026-08-16-pad-every-dc-ac-sweep-the-first` | promote | L0 -> L3, `scripts/sim_run.py` (pad sweeps by default) | first point junk / `at=` on last point errors |
| 3 | `2026-08-16-a-behavioural-op-amp-needs-its-anti` | promote | L0 -> L3, NEW `reference/sim/opamp_behavioural.cir` | template owner shared with #5 and adc #17 |
| 4 | `2026-08-16-a-series-isolation-resistor-only-isolates-when` | decline `duplicate` | - | verified `precision-buffer-capacitive-load-isolation` (R_O x C_LOAD, R_ISO) + `-riso-settling-stability-collision`, envelope `topology_kind: unity-follower` |
| 5 | `2026-08-16-build-the-in-amp-from-its-own` | promote | L0 -> L3, NEW `reference/sim/opamp_behavioural.cir` (3-op-amp in-amp variant) | REF-impedance defect becomes a gate failure |
| 6 | `2026-08-16-a-datasheet-stability-curve-is-taken-at` | promote | L0, `agents/datasheet-extractor.md` (record the gain a curve is taken at) | not covered by the records' unity-follower envelope wording |
| 7 | `2026-08-17-outline-bbox-is-a-bbox-not-a` | promote | L0 -> L3, `scripts/board_init.py` (report `outline_wh_mm`) | K4-adjacent, distinct: bbox read as size inverted the scarce axis |
| 8 | `2026-08-17-outline-fit-clips-to-the-current-outline` | promote | L0 -> L2, `scripts/board_edit.py` (warn when content exceeds the outline) | K4-adjacent, distinct: `content_bounds` intersects with the current outline -> grow first |
| 9 | `2026-08-17-the-kf128-top-view-teeth-are-the` | decline `duplicate` | - | K1: confirms root L2902; the `rotate 180` model note is folded into the K1 root row |
| 10 | `2026-08-17-a-connector-s-pole-order-against-the` | promote | L0, `agents/schematic-block.md` | pole order vs IC pin order is a free P4 fix; measure both ways |
| 11 | `2026-08-17-diff-pairs-conflates-route-these-symmetrically-with` | promote | L0 -> L3, `reference/constraints_schema.md` + `scripts/rules_gen.py` + `scripts/check_diffpair.py` (`symmetry_only`) | PIPELINE BUG seen in four phases; the 1.37 mm class width ships silently |
| 12 | `2026-08-17-a-late-pin-change-must-sweep-every` | promote | L0 -> L2, `scripts/netlist_audit.py` (artifacts that STATE pin order agree with the netlist) | process rule with a checkable core |
| 13 | `2026-08-17-kicad-draws-text-box-overflow-instead-of` | promote | L0 -> L3, `scripts/schlib.py` (size text boxes to content) | no gate sees it |
| 14 | `2026-08-20-envelope-authoring-not-citation-accuracy-is-where` | promote | L0, `agents/research-second-reader.md` (read the envelope's DIRECTION first) | root L4280 is the principle ruling; "runs backwards" is a new failure signature |
| 15 | `2026-08-20-a-blind-re-read-is-worth-running` | promote | n/a (process), `agents/research-second-reader.md` | prices the repair; keep as prose |

### 6.3 bb-buck (8)

| # | entry | **REC** | ladder / owner | reason, landed check |
|---|---|---|---|---|
| 1 | `2026-08-15-an-already-retyped-pulled-library-can-still` | promote | L0 -> L2, `scripts/lib_pin_types.py` (BOOT/BST pin class) | one pin escapes the retype; sibling of adc #15 |
| 2 | `2026-08-15-the-runner-s-injected-rshunt-1e9-is` | promote | L0 -> L1, `scripts/sim_run.py` (report rshunt injection at the measured node; overridable) | root L983/L3978 mandate rshunt=1e9; this is its cost on high-Z nodes |
| 3 | `2026-08-15-a-switcher-s-dc-setpoint-is-simmable` | promote | L0 -> L3, `agents/sim-analyst.md` (Tier-B VCVS boundary model) | not in root |
| 4 | `2026-08-15-an-in-stock-lcsc-part-can-have` | promote | L0 -> L1, `scripts/lib_pull.py` (distinct "no CAD record" outcome) | not in root |
| 5 | `2026-08-16-planes-gen-s-default-thermal-relief-pad` | promote (K3 lead) | L0 -> L3, `scripts/planes_gen.py` (per-pad `connect`) | see K3; corollary "island count is not connectivity" rides in the row |
| 6 | `2026-08-16-read-pad-extents-from-geom-pads-of` | promote | L0 -> L3, `scripts/lib/geom.py` (API note + lint on raw `size` reads) | pad carries its own rotation |
| 7 | `2026-08-16-a-tht-footprint-with-attr-through-hole` | promote | L2 -> L2, `scripts/bom_cpl.py` (THT rows need an explicit assembly-class decision) | root L3255 is the classing base; this is its THT gap |
| 8 | `2026-08-16-the-dfm-gate-reported-pass-with-its` | decline `duplicate` | - | root L4083 (2026-08-09) is the same defect, triage row owns `scripts/gate.py`; the "read `coverage.skipped_error` on every non-strict gate" line is that row's target |

### 6.4 bb-ldo (21)

| # | entry | **REC** | ladder / owner | reason, landed check |
|---|---|---|---|---|
| 1 | `2026-08-16-a-pulled-symbol-s-reversed-pin-angles` | promote | L0 -> L3, `scripts/lib_pull.py` (normalise pin angles on pull) | rotating the part is not the fix |
| 2 | `2026-08-16-hang-a-rail-s-power-symbol-in` | promote | L0 -> L3, `scripts/schlib.py` | 2.54 mm pitch: power symbol in its own cluster |
| 3 | `2026-08-16-a-pulled-2-pin-passive-names-its` | promote | L0 -> L3, `scripts/lib_pull.py` (hide pin names on 2-pin passives) | names print on the body |
| 4 | `2026-08-16-two-pins-of-one-part-are-two` | promote | L0 -> L2, `scripts/netlist_audit.py` (unnamed rail nets; same-part pins on distinct nets) | ERC stayed 0/0 |
| 5 | `2026-08-17-planes-gen-would-have-via-stitched-the` | promote | L0 -> L2, `scripts/planes_gen.py` (honour `constraints.thermal[].min_vias`, incl. 0) | live-tab short forbidden by verified `linear-regulator-live-tab-thermal-vias`; the two numbers never meet |
| 6 | `2026-08-17-route-auto-s-krt-finish-connects-plane` | promote | L0 -> L2, `scripts/route_auto.py` (KRT finish never traces plane-net SMD pads) | root L3586 is the hand-KRT rule; the automatic finish pass does the same |
| 7 | `2026-08-17-out-report-into-a-missing-directory-crashes` | promote | L0 -> L3, `scripts/route_critical.py` (mkdir parents before the board write) | trivial fix; crash lands after the board is written |
| 8 | `2026-08-18-a-provisional-outline-binds-placement-just-as` | decline `duplicate` | - | K4 |
| 9 | `2026-08-18-silk-place-solves-against-the-outline-on` | decline `duplicate` | - | K4 (the lead already carries "re-run silk_place after the fit") |
| 10 | `2026-08-18-stitch-vias-places-vias-inside-large-pads` | promote (K2 lead) | L0 -> L2, `scripts/stitch_vias.py` | see K2 |
| 11 | `2026-08-18-no-scripted-way-to-set-a-per` | decline `duplicate` | - | K3 (inverse case folded into the root row) |
| 12 | `2026-08-18-check-current-charges-every-transition-via-the` | promote (K7 lead) | L1 -> L1, `scripts/check_current.py` (split current across parallel vias) | see K7; root L3798 (`pour_neck`) is a different leg |
| 13 | `2026-08-18-at-block-only-thermal-is-the-whole` | promote | L0, `agents/architect.md` | at block-only the datasheet copper table IS the spec; framing rule, prose is its level |
| 14 | `2026-08-20-planes-gen-has-no-re-pour-path` | promote | L0 -> L3, `scripts/planes_gen.py --repour` or `route_edit` zone op | roots L2586/L4526 are adjacent (no resize; outline does not follow); the duplicate-zone + no-delete path is new |
| 15 | `2026-08-20-centring-both-edge-connectors-on-a-small` | promote | L0 -> L1, `scripts/silk_place.py` (report the binding obstacle) | the obstacle was a neighbour's polarity marker |
| 16 | `2026-08-20-freerouting-cannot-read-this-board-at-all` | promote (K6 residual) | L1 -> L2, `scripts/route_auto.py` (abort ladder on DSN-read StackOverflow; `--timeout-s` 120 meanwhile) | wedge itself landed (root L435/L3662) |
| 17 | `2026-08-20-the-in-pad-defect-reproduces-on-new` | decline `duplicate` | - | K2 |
| 18 | `2026-08-20-via-redundancy-and-check-current-s-clustering` | decline `duplicate` | - | K7 |
| 19 | `2026-08-20-moving-the-edge-parts-in-fixes-the` | promote | L0 -> L1, `scripts/check_thermal.py` (report min short dimension = 2 x (reach + inset)) | K4-adjacent, distinct: ASPECT is derivable; 22-candidate study |
| 20 | `2026-08-20-silk-can-pass-check-silk-and-real` | promote | L0 -> L2, `scripts/check_silk.py` (visibility leg) | passes check_silk + DRC while invisible |
| 21 | `2026-08-20-freerouting-2-2-4-cannot-parse-this` | decline `duplicate` | - | K6 |

### 6.5 bb-mcu (7)

| # | entry | **REC** | ladder / owner | reason, landed check |
|---|---|---|---|---|
| 1 | `2026-08-16-wj500v-5-08-2p-wire-entry-is` | decline `superseded` **after C4 is settled** | - | contradicts adc #23 on the same footprint (see C4); if the owner finds -Y is right, this row is promoted instead and adc #23's orientation claim is corrected |
| 2 | `2026-08-16-placement-edges-pins-the-connectors-to-the` | promote (K4 lead) | L0 -> L3, `reference/recipes/resize-board.md` + `agents/placement.md` (order) + `scripts/gate.py` (place gate at canonical grades edges against the FITTED outline) | see K4; the recipe line is a 2-line edit if the owner prefers `prompt_line` now |
| 3 | `2026-08-16-a-pulled-tht-footprint-was-under-drilled` | promote | L0 -> L2, `scripts/fp_verify.py` (drill vs stated pin, square-pin diagonal) + P3 roster extracts THT connector datasheets | PIPELINE BUG; **side finding for the owner: `boards/bb-ldo/lib/aiee.pretty/CONN-TH_2P-P5.00_WJ500V-5.08-2P.kicad_mod` still carries the 1.30 mm drill** (bb-adc/bb-mcu/buck-5v3a copies are 1.50) |
| 4 | `2026-08-16-fp-verify-never-compares-row-spacing-mm` | promote | L0 -> L2, `scripts/fp_verify.py` | field exists in land_pattern, never compared |
| 5 | `2026-08-16-being-on-the-fetch-allowlist-says-nothing` | decline `duplicate` | - | K5 |
| 6 | `2026-08-16-silk-place-skips-board-only-refs-by` | promote | L0 -> L2, `scripts/silk_place.py` (solve or explicitly skip-and-report board_only refs) | a mounting hole's refdes ended up labelling the IC; root L3103 is attribution-blindness, different |
| 7 | `2026-08-16-backticks-in-a-bash-tool-argument-are` | promote | n/a (host/tool fact), sibling of root L4310 | a `state.py decision` lost a word to command substitution |

## 7. Owner-session mechanics (after the rulings)

1. Per approved record: `research.py promote --workspace boards/bb-X --record <id>`
   (copies sources, rewrites citations); apply Q2 edits; set `maturity: approved` +
   `approval: {by: owner, date, note}`; staged merge: copy
   `design/u22-staged/records/in-bias-current-return-path.yaml` into the library (its
   sources are already repo-relative), mark the two workspace originals superseded.
2. Q1.2 row 1: edit `buck-en-softstart-sequencing` in place, re-approve.
3. `knowledge.py --validate --strict`; re-render topology views that exist.
4. `learnings.py resolve --batch boards/bb-X/learnings/rulings-<date>.yaml` per board
   (Q4 research-task rows + Q6 rows; shape = `boards/rf-de-20m/learnings/rulings-2026-08-14.yaml`;
   `root_learnings` rows take `--now-level/--target-level/--owner` from the Q6 ladder column),
   then `learnings.py validate` + `triage`.
5. Root LEARNINGS + `design/ladder-triage.md` rows come from the `root_learnings`
   resolutions (the tool writes them).
6. Acceptance: zero pending across the five queues; coverage at the default floor on
   synthetic ldo/adc/inamp/mcu workspaces shows the new domains covered.

Prep-mode facts for the record: staged record validated with `knowledge.py --validate
--strict --records-dir design/u22-staged/records` (green); workspace dirs validate
strict-green apart from workspace-relative source paths (resolved by `promote`) and
bb-buck's two `generalizes` into the library (resolve once co-located).
