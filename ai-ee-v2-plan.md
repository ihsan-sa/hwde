# ai-ee — v2 Plan (session-sized T-steps)

Companion to `ai-ee-implementation-plan.md` (v1, S-steps, complete). Same protocol:
one fresh session per step, kicked off with **"run step T<N>"** (repo `CLAUDE.md`).
Sources folded in: the post-order repo/LEARNINGS audit (2026-08-06), the external
routing/knowledge design notes (`design/routing-knowledge-notes.md`), and two owner
directives: (1) task-based entry — the skill acts like an EE picking up a project in
any state; the full pipeline becomes a special case; (2) cheap per-stage tuning
benches. Plus one owner-mandated step: a per-stage deep-evaluation + improvement
fan-out (T6).

## Conventions (inherit v1, plus)

- Session start: read `PROGRESS.md` (v2 status board) + this step's entry. Grep
  `LEARNINGS.md` for the step's listed tags BEFORE writing code. Nothing else
  unless blocked.
- Session end: `check.cmd` green; PROGRESS.md v2 board row + step entry updated;
  commit. Do NOT start the next step.
- **Parallel-session hygiene (wave 1 runs up to 4 terminals):** commit ONLY your
  own files by explicit path — never `git add -A`; `gate.py --commit` sweeps dirty
  trees (LEARNINGS 2026-07-27 [skill][git]). PROGRESS/LEARNINGS are append-only;
  resolve overlap by rebase, never rewrite others' entries.
- Scripts follow SPEC.md §6 contract (argparse, JSON stdout or --out, exit 0/1/2,
  ASCII-safe, no interactivity).
- Every fix ships a regression fixture; boards that failed join the corpus.
- The maturity-ladder rule (design notes §6) governs all new knowledge: if a
  script can check it, it does not go in a prompt. SKILL.md must not grow
  (baseline 286 lines).

## Dependency graph

```
T0 (anytime, first — trivial ops)
{T1, T2, T3, T4}          wave 1 — mutually parallel, disjoint areas
{T1, T2, T4} → T5 → T6    T6 EXCLUSIVE (edits scripts pipeline-wide; run nothing beside it)
T6 → T7 → {T8 ∥ T9} → T10
T11: anytime after T0, gated on boards arriving; do not overlap T6
```

Board runs (lumina-par P3 resume, lumina-strobe P4 resume via `/ai-ee --resume`)
are NOT plan steps; run them any time after T1+T2 land — they double as live
validation for later steps.

## Session setup per step

| Step | Title | When / deps | Parallel with | Model | Effort | Ultracode | Spend |
|---|---|---|---|---|---|---|---|
| T0 | Ops sweep | now | any | Sonnet 5 | medium | - | tiny |
| T1 | Fab-truth hardening | wave 1 | T2 T3 T4 | Opus 5 | high | - | small |
| T2 | Gate blind-spot fixes | wave 1 | T1 T3 T4 | Fable 5 | max | yes | medium |
| T3 | Library + authoring hygiene | wave 1 | T1 T2 T4 | Opus 5 | high | - | small |
| T4 | Ladder triage + trigger-indexed refs | wave 1 | T1 T2 T3 | Opus 5 | high | yes | small–medium |
| T5 | Stage bench + frozen fixtures + scores | after wave 1 | — | Fable 5 | max | yes | medium |
| T6 | Per-stage deep eval + improve (fan-out) | after T5, **exclusive** | nothing | Fable 5 | max | yes | **large** |
| T7 | Freshness state + invalidation map | after T6 | — | Fable 5 | max | - | medium |
| T8 | Incremental board update | after T7 | T9 | Fable 5 | max | yes | large |
| T9 | External-board intake | after T7 | T8 | Opus 5 | high | - | medium |
| T10 | Task router + SKILL v2 | after T8+T9 | — | Fable 5 | max | - | medium |
| T11 | Hardware bring-up leg | boards arrived | any but T6 | Opus 5 | high | - | small |

Why the tiers: Fable max where the artifact is novel or correctness is subtle
(gate algorithms, bench metric design, state semantics, board mutation, the
router "soft top", and the T6 judgment fan-out); Opus 5 high where the work is
well-specified transcription/plumbing; Sonnet for ops. Ultracode where
independent sub-tasks fan out and adversarial verification pays.

---

### T0 — Ops sweep
**Ask the owner at session start for the lumina-carrier JLC web order number**
(the API create never succeeded — 4L refusal; the board was ordered manually, and
the workspace does not know).
**Build/do:** refresh pd-trigger tracking (`order_track.py`; last fetch 2026-07-29
"Pending Review", order W2026073002475378). Record the carrier web order number
into `boards/lumina-carrier/fab/order.json` and probe whether `order_track` can
see web-created orders (resolves a live unknown). Verify tree clean.
**Accept:** fresh `tracking.json` for pd-trigger; carrier order recorded; findings
appended to LEARNINGS `[ordering]` if the web-order visibility answer is
non-obvious; repo clean.

### T1 — Fab-truth hardening (the "0/0 ≠ fabricable" class)
**Grep LEARNINGS:** `[board_init]`, `[rules_gen]`, `[dfm]`, `[ordering]`,
`[stackup]`, `[jlcapi]`.
**Defects (all machine-verified on live runs):** `board_init` ships
`min_track_width: 0.1` (below EVERY JLC profile — bit two boards) and
`min_hole_to_hole: 0.25` at severity WARNING (hid two real defects until P9);
`rules_gen` flattens every power net into one "Power" netclass at the widest
width (20 mA nets routed at 5 A width); JLC Open API `pcb/create` refuses
4-layer boards with unclassified code 2 while `calculate` accepts them;
`reference/stackups.yaml` contained JLC04161H-3313 which JLC does not offer;
`derive_copper_oz` silently defaulted to 1 oz on unparsable headings; the order
latch binds to the gerber zip sha256, which changes on every export
(self-invalidating).
**Build:** fab floors sourced from the selected JLC capability profile in ONE
place, injected by `board_init` at ERROR severity; `rules_gen` derives per-net
width from per-net current (netclass split), never flattens; `ordering.md` +
`order_submit.py` encode 4L = web-manual path (guard `--api-create` on layer
count with a clear message); rebuild `stackups.yaml` from JLC's live offering
(verify each entry against the site/API and mark it live-verified); make
`derive_copper_oz` fail loud; replace the latch fingerprint with a normalized
design hash (strip timestamps/serials from gerber content before hashing).
**Accept:** regression tests — board_init'd project floors ≥ chosen profile
minimums at ERROR; netclass widths differ per current on a two-rail fixture; 4L
create attempt exits with the guard, 2L path unchanged; stackups entries all
carry verification provenance; suite green.

### T2 — Gate blind-spot fixes (crown-jewel repairs)
**Grep LEARNINGS:** `[check_creepage]`, `[check_current]`, `[check_diffpair]`,
`[check_return_path]`, `[gates]` (all four defects were found live on
lumina-carrier; the entries carry exact repro geometry).
**Build:** `check_creepage` — report ALL violating pairs (worst-per-net-pair
hid 216 siblings), accept net-PAIR voltage input (net-to-reference cannot
express a bridge input; a 0.33 mm 57 V gap passed silently), add a
coated-board modifier per the IPC-2221 coated rows, and use pad-shape-correct
gap formulas; `check_current` — plane-fed rails must be expressible (the
net-wide via-count rule is unsatisfiable for them and `overrides` cannot reach
it), add bridge/parallel-path awareness or an explicit advisory downgrade;
`check_diffpair` — include vias AND pads in the connectivity graph (a 0.14 mm
endpoint mismatch silently turned "skew" into total-copper-length);
`check_return_path` — classify expected reference per stackup so an
F/GND/3V3/B board does not fail every B.Cu trace by construction; formalize the
waiver CLASS.
**Accept:** one new mutant/fixture per fix, derived from the cited LEARNINGS
geometry, firing with correct location; all goldens + existing mutants
unchanged; suite green. Ultracode: fan the four checks out to parallel
builders, adversarially verify each against its fixture before merging.

### T3 — Library + authoring hygiene
**Grep LEARNINGS:** `[easyeda2kicad]`, `[silk]`, `[parts]`.
**Build:** `lib_pull.py` applies the proven silk-fix recipe at pull time (every
pulled footprint ships silk <0.25 mm from copper; four had a silk dot INSIDE
pad 1 — the 2026-07-28 CORRECTION entry has the measured recipe), runs
`lib_refdes_norm` automatically (blanket (0,-4.0) refdes offsets), and applies
the known plated-peg / DIP-switch fixes where a recipe exists. NEW
`schem_refdes.py`: deterministic schematic refdes/value placement via
kicad-sch-api — offset table per symbol class/orientation + collision nudge;
a cheap-model pass is allowed ONLY for residue the script flags, not as the
primary path.
**Accept:** pulling the known-bad footprint set yields 0 silk DRC errors
post-pull (measured by real DRC, per the CORRECTION entry's method);
`schem_refdes.py` on the s7 fixtures: 0 overlaps, consistent offsets; suite
green.

### T4 — Knowledge ladder triage + trigger-indexed references
**Read:** `design/routing-knowledge-notes.md` §6–7 (maturity ladder + triage
rules) — the governing rubric.
**Build:** triage EVERY LEARNINGS.md entry (~95) onto the ladder (L0 prose →
L1 measured → L2 gated → L3 correct-by-construction): emit
`design/ladder-triage.md` — one row per entry: current level, target level,
owning artifact (check/template/script/ref), status (T1–T3 already promote the
obvious ones — mark them). Add trigger-indexed references:
`reference/remediations/<check_id>.md` for the top ~10 firing check_ids
(content harvested from LEARNINGS + `agents/fixer.md`, keyed by finding type,
NOT by topic); wire `fix_dispatch.py` to emit the matching remediation path
with each finding cluster. Record SKILL.md line count (286) as the health
baseline in PROGRESS.md.
**Accept:** every LEARNINGS entry has a triage row; `fix_dispatch` output
carries remediation pointers (test with a canned findings file); remediation
refs exist and are loadable for the top firing check_ids from the three
shipped-board runs; suite green. Ultracode: fan entries to parallel triage
agents, synthesize, spot-verify 10% adversarially.

### T5 — Stage bench + frozen fixtures + composite scores
**Read:** `design/routing-knowledge-notes.md` §3 (stage boundaries as frozen
fixtures), §5 (derived features), §7 (fitness function). Owner directive: tight
make→test→evaluate→fix loops per stage, cheap enough to iterate in minutes.
**Build:** `scripts/bench.py` — run ONE stage in isolation on a frozen fixture:
stage registry {P2 arch, P4 schematic, P5 board_init, P6 place, P7 route,
P8 verify, P9 dfm, P10 order-dryrun}; emits `score.json` (per-stage
deterministic metrics + wall time + token/cost when a stage is agent-driven)
plus a render where visual. Fixtures: harvest from the six board workspaces —
`state_snapshots/` of lumina-carrier and pd-trigger (SHIPPED designs = highest
value) + goldens/mutants; freeze under `tests/fixtures/stages/` with a
manifest (fixture → stage → provenance). Metrics v0: schematic (wire
crossings, label collisions, refdes overlap, sheet balance), place (HPWL,
ratsnest crossings, decap distance, congestion proxy), route (completion %,
via count, length, DRC), verify/dfm (findings vs known-answer), plus the
derived-SI scalars already computed by the check suite. Record BASELINE scores
for every fixture and commit them.
**Accept:** bench runs every registered stage on ≥1 fixture end-to-end;
baselines committed; score reproducibility bounded (two runs within declared
noise); the tuning-loop usage pattern documented in this file's appendix and
SKILL.md UNCHANGED in size; suite green.

### T6 — Per-stage deep evaluation + improvement (owner-mandated fan-out)
**EXCLUSIVE: no other session may run beside this one — it may edit any stage.**
**Read:** `design/ladder-triage.md` (T4), bench baselines (T5), and per-stage
run evidence: `boards/*/log/P*-digest.md` + workorders from the three shipped
boards.
**Protocol:** for each pipeline stage (P0–P10), 1–2 subagents evaluate the
stage IN ISOLATION: read its scripts + agent prompts, run its bench fixtures,
study its digests/failures across the three real runs, and score it on:
correctness, output quality, token cost, wall time, knowledge level (ladder),
and observed failure modes. Then propose AND apply improvements: script fixes,
prompt tightening, template extraction (start with the classes v1 bled on —
decap loop, crystal island, connector entry, buck hot loop — per design notes
§4 stage 3), and COST optimizations (per-agent model-tier/effort
recommendations, batching, call-count reductions per the §1 budget rule).
Adversarial verify every change: bench score must not regress, full suite must
stay green; merge stage-by-stage (worktree isolation per stage is acceptable).
**Accept:** `design/stage-evals/<stage>.md` for every stage — findings, applied
diffs (or an explicit "no change" verdict with reasons), before/after bench
scores, and a consolidated cost table (est. tokens/run before vs after) +
updated per-agent model/effort table for SKILL.md's orchestrator section;
suite green. This is the plan's biggest spend; do not run it at low effort.

### T7 — Freshness-aware state + invalidation map
**Grep LEARNINGS:** `[pipeline]`, `[ordering]` (the gerber-sha entry: raw file
hashes are NOT design fingerprints — every export mutates them; hash normalized
content).
**Build:** state.json v2 — per-artifact NORMALIZED content hashes (canonical
netlist form; board sans timestamps/UUID churn; gerber normalized per T1) and
gate results keyed to their input hashes (a gate is valid iff hashes match).
`reference/invalidation.yaml`: edit-class taxonomy → {stale artifacts, gates to
re-run, human-hold weight}: move_fp, swap_part_same_fp, swap_part_new_fp,
add_part, del_part, reroute_net, silk_edit, plane_edit, rule_change,
stackup_change. Human-hold weight scales with blast radius (a one-footprint
move must not carry H4 ceremony). `state_migrate.py` upgrades all six existing
workspaces idempotently.
**Accept:** unit tests per edit class; a simulated move_fp on a pd-trigger
fixture marks EXACTLY the mapped set stale and nothing else; migration
idempotent on all six workspaces; suite green.

### T8 — Incremental board update (kills OI-3)
**Grep LEARNINGS:** `[pipeline]` (no incremental board-from-netlist update —
adding ANY part after P5 costs all of P6+P7; root cause of lumina-carrier's
deferred OI-1/OI-2), `[place_edit]` (no add_footprint op; moving a footprint on
a routed board: silk-blind + orphaned GND stubs — the two things nothing does
for you), `[route_edit]`, `[kicad][connectivity]`.
**Build:** `board_update.py` — apply a netlist diff to a placed/routed board
PRESERVING existing copper (SWIG bundled python; reuse place_edit/route_edit
machinery; refill + DRC after every mutation). Three modes: (a)
swap_part_same_fp → fields/BOM/CPL only, geometry byte-stable; (b) add_part →
insert footprint in a declared region, ratsnest stub, hand to the fix loop;
(c) del_part → remove footprint AND its now-orphaned copper stubs (verify via
connectivity, not proximity — a track endpoint inside a via/pad is connected;
inside another track's body is NOT).
**Accept:** mutants on pd-trigger + carrier fixtures: swap diff touches only
fields/BOM/CPL; add preserves existing tracks (sans refill) and reaches DRC
0/0 through the standard fix loop; delete leaves no orphan stubs (connectivity
check) and no silk residue; suite green. Ultracode: adversarial verify — this
is novel geometry surgery.

### T9 — External-board intake
**Build:** `intake.py` — arbitrary KiCad 10 project (KiCad 9 via
`sch/pcb upgrade` first) → new workspace: copy-in (NEVER mutate the source),
state.json v2 with hashes (T7), project-lib registration, baseline gate run
(ERC/DRC/verify/dfm), `netlist_audit`, render set, and a `report_gen` review
digest as the "review this board" deliverable. Guardrails: version-pin checks
via `lib/env.py`; refuse mixed-version projects with a clear message.
**Accept:** intake one golden board + one foreign fixture (e.g., a KiCad demo
project) → valid workspace, gates run, digest emitted, source untouched
(hash-verified); suite green.

### T10 — Task router + SKILL v2 ("the skill is an EE")
**Read:** T4's remediation refs, T7's invalidation.yaml, T8/T9 interfaces.
**Build:** explicit task taxonomy (~12 verbs): review, fix-finding, move,
swap-part, add-part, remove-part, reroute-net, make-footprint, dfm-check,
order, track, resume-phase, full-run. Each verb = a RECIPE (scripts + agents +
gates drawn from the invalidation map + remediation refs + minimal human
holds). Front door: `/ai-ee <task>` matches the explicit table FIRST;
LLM classification only as fallback; unknown → ask. The full pipeline is
re-expressed as the recipe sequence (special case, not a separate code path).
SKILL.md restructured accordingly — hard constraint: ≤ 286 lines (knowledge
displaced into refs/scripts, per the ladder).
**Accept:** dry-run per verb on fixtures (golden path each); full-run
regression on a blinky-class fixture behaves as v1 did; SKILL.md ≤ 286 lines;
suite green.

### T11 — Hardware bring-up leg (run when boards arrive)
**Read:** `boards/pd-trigger/` + `boards/lumina-carrier/` design docs, BOM/CPL,
sim results (`sim` gate outputs carry expected-rail bounds),
`fab/assembly-manual-work.md` (carrier: 47 extended parts).
**Build:** `bringup_gen.py` + `agents/bringup.md` — board-specific bring-up
plan from the design doc: power-on sequence, expected rails WITH sim-derived
bounds, smoke checklist, measurement points (refdes + net + location), rework
candidates; and a capture loop: owner measurements → structured log →
pass/fail vs bounds → findings append to LEARNINGS, defects become mutation-
corpus candidates. First targets: pd-trigger, then lumina-carrier.
**Accept:** generated plans for both real boards reference ONLY real
nets/refdes (validated against the netlist); a sample measurement set
round-trips to pass/fail; suite green.

---

## Not in this plan

- lumina-par / lumina-strobe resumes: `/ai-ee --resume`, anytime after T1+T2.
- SPICE v2 items (vendor model fetch, openEMS/WSL2): tracked in the sim
  amendment of PROGRESS.md; unchanged by this plan.
- Boards → separate GitHub repo (`git subtree split --prefix=boards`): owner
  decision pending; independent of all steps.

## Appendix: the per-stage tuning loop (post-T5 usage pattern, not a step)

Open a session scoped to one stage. `bench.py <stage> --fixture <f>` → read
score.json + render → edit the stage's prompt/template/script → re-bench →
keep iff score improves → commit with the score delta in the message. Cheap
models are fine for the loop driver; the bench is the judge, not the model.
