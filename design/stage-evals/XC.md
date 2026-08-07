# XC (cross-cutting: orchestrator, state, reporting, cost) - T6 evaluation (2026-08-06)

## Verdict

correctness 7.5, output_quality 8, token_cost 4, wall_time 7, knowledge_level 6.
The orchestration layer demonstrably shipped three boards with 0-2 human
interactions and full state audit trails; its weak axis was cost discipline
(every spawn at session default, one work order per single review finding, no
spawn accounting anywhere) and prose duplication inside the capped SKILL.md.

## Findings

- Digest discipline (5-10 lines) collapsed 2-8x on all three post-v1 lumina
  runs (carrier digests 23-82 lines); usb-buck has no P5 digest at all.
- report_gen's before-every-checkpoint mandate: zero recorded executions in
  any live run history (the design docs in the repo were generated post-run).
- gate.py --commit staged with repo-root `git add -A` - any unrelated dirty
  file rode along in ~10 gate commits per run (ladder row 59).
- fix_dispatch wrote one order per single review finding: pd-trigger P8's 10
  one-violation orders = 10 fixer spawns for ~40k tokens each if the playbook
  is followed literally.
- No spawn/token records anywhere; live tier choices survive only as digest
  prose. state.json artifacts registry effectively dead (4 of 6 boards).
- SKILL.md carried duplicated (route_cleanup twice) and script-owned prose at
  its hard 286-line cap.

## Applied

- XC-2 (batch H, b19d6b8): fix_dispatch merges same-fixer clusters of <=2
  violations into one order (cap 8, union region/kinds/refs). 10 singles
  across 2 domains -> 2 orders in tests.
- XC-3 == P8B-2 (batch H): gate.py --commit scopes staging to the workspace
  derived from the gate input; outside-dirty paths reported as excluded, never
  swept. Plus stale-fill preflight (`require_fresh_fills` on drc_routed).
- XC-6 (batch H): P6 interim drc gate now runs schematic parity - a parity
  break surfaces before routing, not after (saves a full re-route cycle).
- XC-7 (batch H): tests/test_report.py git-status diff scoped to the
  workspace under test; concurrency false-reds gone (verified live with dirty
  files present).
- XC-4 (batch A, 5520483): state.py set-phase warns (warn-only) when the
  departed phase's digest is missing or >15 lines.
- XC-1 + XC-5 (close commit, this session): SKILL.md surgery - cut the
  duplicated route_cleanup prose, the script-owned P6 silk caveat, the
  obsoleted drill/placelib/order_quote Known-limits lines; added the spawn-tier
  table + spawn-ledger step 5; P0 delegate protocol, P3 extract reuse, P5/P9/
  P10 inline defaults, verify-waivers pointer, design-hash latch prose fix.
  286 -> 281 lines (cap test green).

## No change

- render.py: thin, correct, SPEC-6; nothing to fix.
- gates.yaml severity calibration (beyond the P6 parity flag): proven across
  4 boards.
- state.py core surfaces (snapshot/restore/budget/record-gate/issue/decision):
  genuinely used as documented in all four run histories.

## Deferred / rejected

- XC-8 T7 handoff (record): log --event needs a name whitelist/length cap
  (carrier stored paragraphs as event keys); artifacts registry needs an
  auto-register hook or removal; spawn ledger data should become a state v2
  first-class record. Spec in the XC eval JSON.
- Sub-agent model tiers for the ORCHESTRATOR itself: out of scope (the
  orchestrator is the session, not a spawn).

## Bench

No XC bench stage. All XC items bench-neutral; collateral sweeps in batches
H/A confirmed zero drift on all pre-existing fixtures.

## Cost & tiers

Whole-run estimates and the tier table live in `overview.md` (the SKILL.md
"Spawn tiers" block is the operative copy). Requirements-analyst kept
fable/high against the XC draft's sonnet/medium - the P0 lens carried
stronger evidence at negligible absolute cost. The spawn ledger (SKILL step 5)
exists precisely to replace these estimates with measurements; T7 should
promote it into state v2.
