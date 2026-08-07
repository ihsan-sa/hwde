# T6 stage evaluations - overview (2026-08-06)

Owner-mandated per-stage deep evaluation + improvement fan-out (v2 plan T6).
Method: 16 read-only stage evaluators (11 stages, doubled lenses on P3/P6/P7/P8 +
one cross-cutting) -> synthesis (~118 proposals, ~60 accepted after dedup) ->
11 sequential self-verifying apply batches (commits `T6 Batch A..K`) -> these
records. Per-stage detail: `P0.md` .. `P10.md`, `XC.md` in this directory.
The eval JSONs (full proposal texts incl. deferred specs) are preserved in the
T6 session workflow transcripts; every deferred item's spec is summarized in
its stage file's Deferred section.

## Consolidated cost table (est. tokens/run, before -> after T6)

Basis: spawn counts from the four full-run state.json/digest histories, prompt +
input sizes, per-stage evaluator estimates. Estimates, not measurements - the
new spawn ledger (SKILL.md spawn template step 5) exists to replace this table
with measured data.

| Stage | Before | After | Main lever |
|---|---|---|---|
| P0 intake | 8-20k | ~same | (lint adds <1k; req-analyst stays top-tier) |
| P1 research | 250-500k; carrier-class 1.5-3M | 150-350k; 0.8-1.5M | scout JSON contract, size discipline, reference/interfaces+topologies seeds |
| P2 architecture | ~80k median | ~80k (+15-25k when sim nominated) | (quality fixes, not cost) |
| P3 parts+library | 130k blinky / 250k typical / ~700k carrier | 90k / 170k / ~400k | grounding-payload trim, batched paced pulls, passive auto-pick, extract reuse |
| P4 schematic | ~150k flat, 400k+ hier | ~140k / ~420k | save-time field placement kills cosmetic fix loops |
| P5 board setup | ~20k | ~10k | inline default (spawn = exception) |
| P6 placement | ~150k | ~90k | silk_place solver (30-160 hand ops -> script), templates |
| P7 routing | 100-150k clean; 400k-1M failure tail | 100-150k; 200-400k tail | pad-window probe, KRT facts in route_critical |
| P8 verification | ~180k median | ~140k | fix_dispatch batching, reviewer->domain routing, remediation refs firing |
| P9 DFM | ~20k | ~10k | inline default |
| P10 ordering | 15-25k | 5-10k | inline default |
| **Full run** | ~1.5M (2L) / ~2.2M (4L) / ~3.5M (carrier-class) | ~0.9M / ~1.4M / ~2.2M | tier table (~45% of spawn volume downgraded with deterministic backstops) |

## Per-agent model/effort table (now in SKILL.md "Spawn tiers")

| Tier | Roles |
|---|---|
| fable/max | router (novel board; proven-chain re-run: sonnet/medium) |
| fable/high | architect, placement, schematic-reviewer, verify-reviewer, requirements-analyst |
| fable/medium | schematic-block (thin root-stitch: sonnet/high) |
| opus/high | research-interface-spec, research-power-architect, sim-analyst, fixer (copper/route) |
| sonnet/high | research-component-scout, research-reference-design, part-sourcer, datasheet-extractor |
| sonnet/medium | librarian, fixer (silk/sch/parts/fab), placement (backward-edge re-spawn) |
| inline-default | board-setup, ordering, dfm (spawn = exception path) |

Rationale anchors: roles downgraded all have a deterministic verifier behind
them (fp_verify, ERC gate, dfm gate, canned-API tests) or a fresh-context
reviewer above them; roles kept at fable demonstrably overruled their inputs on
live runs (premise falsification, board-saving review findings). Deviation from
the XC evaluator: requirements-analyst kept fable/high (P0 lens evidence -
cross-document conflict catches at negligible absolute cost). Escalate one tier
when a role must overrule its inputs; never silently downgrade.

## Bench movement (committed re-baselines, all same-commit with their cause)

| Fixture | T5 | post-T6 | Why |
|---|---|---|---|
| pd_trigger_arch (P2) | 91.0 | 100.0 | power_no_consumers false positives fixed (series escape) |
| pristine_lib (P3) | - | 100.0 | NEW stage: fpfix vs real DRC, known-answer 16->0 |
| usbbuck_sch (P4) | - | 90.95 | NEW hierarchical fixture (multi-sheet scoring) |
| blinky2_sch / pd_trigger_sch (P4) | 62.0 / 95.0 | unchanged | frozen gradient fixtures |
| pd_trigger_board_init (P5) | 100.0 | 100.0 | rules_gen leg added (netclass split now baseline-tracked) |
| pd_trigger_place (P6) | 18.53 | 48.02 | scorer aligned with annealer objective (GND flight-lines, bulk caps) |
| golden_blinky2_place (P6) | 53.36 | 72.36 | same |
| pd_trigger_route / usbbuck4_route (P7) | 91.5 / 92.54 | unchanged | frozen boards |
| carrier_verify (P8) | 37.6 | 68.2 | T2-key adoption + land_pattern_pitch waiver class; 47 true defects pinned as known-answer |
| pd_trigger_verify (P8) | 100.0 | 94.4 | NEW derived 5A return-net coverage fires 56 advisory warnings (0 errors - gate holds) |
| mutant_planesplit_verify (P8) | 99.5 | 99.4 | TRUE silk_misattributed found in rf4 golden (C14) - pinned, not silenced |
| mutant_returnvia_verify (P8) | 99.5 | 99.5 | unchanged; known-answer fires |
| mutant_gndchoke_verify (P8) | - | 94.8 | NEW mutant: the pd-trigger 5A GND-choke class |
| pd_trigger_dfm / mutant_cpl_dfm (P9) | 98.0 / 99.4 | unchanged | mutant catching intact |
| pd_trigger_order (P10) | 100.0 | 100.0 | unchanged (dead fixture arg dropped) |
