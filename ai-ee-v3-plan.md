# ai-ee v3 plan - teach the stages, harden the releases (U-steps)

Drafted 2026-08-13 from: the 2026-08-07 lumina-carrier retrospective
(`boards/lumina-carrier/reports/retrospective-2026-08-07.md`), the external
codex review (`C:\Users\ihsan\Downloads\AI-EE3-Project-Review-2026-08-09.md`,
finding IDs C1-C9/H1-H11 cited below), the 2026-08-09 live-run LEARNINGS
(sbuck-5v3a + rf-term-150w), and the owner design session of 2026-08-13.

Same session protocol as v1/v2 (repo `CLAUDE.md` "run step N"): U<N> steps live
HERE. One step per isolated session; read only what the step lists; PROGRESS.md
v3 board tracks state; session end = suite green (modulo the standing AP63203
`net` test) + PROGRESS entry + commit.

## Design decisions this plan encodes (owner-ruled 2026-08-13)

1. **Learning mode.** Per stage: a learner agent owns the stage's artifacts
   (agent contract, templates, cost terms, bench scorer), spawns ISOLATED
   instances of the stage agent on frozen inputs, the owner grades renders,
   the learner converts each critique into an artifact edit, re-runs fresh.
   The OWNER is the scorer; session close = commit + anchor + document. The
   frozen graded fixture + scorer terms are the RECORDING of the owner's
   scores - they guard production runs where the owner is absent. Generic
   across stages; buck placement is cycle 1.
2. **Knowledge library.** One in-repo, class-indexed library
   (`reference/knowledge/`) that stage agents and learner agents share.
   Records carry application classes (power-loop, EMI, thermal-via, ...),
   applicability keys (topology, package, interface), a checkable rule where
   one exists, prose rationale, and a source pointer down to the PDF page.
   Retrieval is TRIGGERED, not judged: P2's block list keys class injection
   into P6/P7 spawn prompts; P3's package keys package records; a violation
   kind keys its remediation (exists since T4).
3. **Workspace learnings + promotion.** Every run captures learnings in the
   workspace itself; a run-close step compiles them into a stage-tagged
   promotion queue; a separate promotion pass (owner at run end, OR a general
   agent across many runs, OR a stage learner pre-session) moves entries to
   their ladder level. rf-de-20m's 66-entry queue is the standing backlog and
   the acceptance fixture.
4. **Cross-stage feedback.** Deliver constraints earlier instead of running
   stages concurrently: deterministic layout-implication fields at P3;
   budgeted backward spawns (placement files an issue, spawns a part-sourcer
   with a narrow brief, applies via `board_update` + `state.py edit --class`);
   ONE WRITER per artifact always - reads and read-only scouts are free,
   backward writes go through board_update. Stage gates stay as the points
   where artifacts freeze.
5a. **Coverage-gated design (owner-ruled 2026-08-15).** "I know enough to
   design this" becomes a checkable claim, the U2 move applied to knowledge:
   - Records gain `level` (principle/topology/family/part/instance),
     `envelope` (dimensions chosen per record by what the mechanism actually
     varies with - hot-loop scales with edge rate/hard-switching, not vin;
     creepage scales with volts), `maturity`
     (draft -> verified -> approved -> proven), `generalizes` links (specific
     records point at their principle parents; a principle-only match on a
     new domain narrows research to the APPLICATION delta, not the physics).
   - The trigger is structural, never self-assessed: (1) deterministic query
     (class keys + envelope containment + maturity floor), (2) a narrow
     schema-forced agent mapping for fuzzy record->slot remainder (it
     classifies, it may NOT declare sufficiency), (3) a mechanical cutoff
     per decision class from coverage-checklist records.
   - Maturity governance: `approved` requires OWNER sign-off (teaching or
     promotion review); `proven` upgrades AUTOMATICALLY from T11 bench
     evidence - reality outranks review. Early on only `approved` satisfies
     coverage (bootstrap mode); research frequency decays as approvals and
     bring-up evidence accumulate.
   - Research launch is ALWAYS AUTO on a gap (owner ruling): no approval
     checkpoint, but a per-gap depth cap and per-run research cap that
     CHECKPOINT VISIBLY when hit - never silent truncation.
   - Research outputs are workspace-first (draft records + quarantined
     sources + promotion-queue entry), promoted via the U6 pass. Researcher
     agents alone get web tools, restricted to a vendor-domain allowlist;
     design/fixer agents stay locked down.
5b. **Codex adoption is scoped.** Adopt C1 (release attestation), C4 (gate
   report validation, scoped commits), C7 (strict verify coverage), H1 (BOM
   assembly classes), H5 (promotion discipline), H9 (durable waivers - inside
   U5). C3/C5/C6 are queued as U12, REQUIRED before order credentials are
   ever wired. Codex P2/P3 (packaging, CI, repo restructure, storage
   separation) are deferred until after T11 + U10 hardware/live evidence.

## Conventions (additive to v2's)

- v2 conventions apply (SPEC 6 script contract, smoke-test verify-later
  claims on first touch, bench re-baseline in the same commit as its cause).
- LEARNINGS discipline: every entry gets its `design/ladder-triage.md` row in
  the same session (`test_every_learnings_entry_has_a_triage_row` enforces).
- Parallel-wave file ownership: LEARNINGS.md is append-only - rebase before
  commit on conflict. In wave 1, U4 owns `SKILL.md`; U1/U2/U3 do not edit it.
  In wave 2, U5 edits only the `order` verb in `tasks.yaml`; U6 only appends
  its new verb row.
- Board files: read-only unless the step names the edit. lumina-carrier is
  ORDERED hardware - constraints/sidecar fixes only (U1), never copper.

## Status board -> PROGRESS.md "v3 status board"

## Dependency / wave map

    U0 (alone, first)
    wave 1: U1 || U2 || U3 || U4          (after U0)
    wave 2: U5 (needs U2+U3) || U6 (needs U4)
    wave 3: U7 (needs U6; light overlap ok with T11)
    wave 4: U8 (EXCLUSIVE - owner present)
    wave 5: U9 (needs U4+U8) -> U10 (needs U8; U9 preferred first)
    later:  U11 (after U10), U12 (before order credentials, anytime)
    coverage leg (owner-launched, added 2026-08-15): U13 (unattended,
      needs U4+U7) -> U14 (owner, short) || U15 (unattended; owns
      tasks.yaml while U14 owns records - parallel-safe). U8 does not
      require them, but teaches against a stronger library after U14.
    T11 (v2 plan): as soon as boards arrive; any wave except during U8.

## Session setup

| Step | Model | Effort | Ultracode | Owner present |
|---|---|---|---|---|
| U0 | Opus 5 | high | - | no |
| U1 | Fable | max | - | no |
| U2 | Fable | high | - | no |
| U3 | Opus 5 | high | - | no |
| U4 | Fable | high | - | no |
| U5 | Fable | max | yes (adversarial review, T8 pattern) | no |
| U6 | Opus 5 | high | - | optional (promotion rulings) |
| U7 | Fable | max | - | no |
| U8 | Fable | max | - | YES (interactive teaching) |
| U9 | Opus 5 | high | - | no |
| U10 | Fable | max | - | checkpoints (H2-H4) |
| U11 | Fable | max | - | YES |
| U12 | Opus 5 | high | yes (concurrency/corruption fault injection) | no |
| U13 | Fable | high | - | no |
| U14 | Opus 5 | high | - | YES (short: rule levels/envelopes/approvals) |
| U15 | Fable | max | - | no |

---

### U0 - Ops + evidence sweep (run first, alone)

**Read:** `git status`, codex review "Current repository baseline" section,
retrospective, `design/ladder-triage.md` header, LEARNINGS entries 188-239.
**Build/do:**
- Commit the dirty tree in classified pieces: (a) carrier retrospective +
  gate reports/renders/state.json = release evidence; (b) design-doc pdf/tex
  regens (deterministic test regens - commit as-is); (c) the two `.kicad_pro`
  diffs (inspect; commit if benign toolchain resave, else report). Then
  `git push` (58+ commits ahead; zero-cost backup).
- `order_track` refresh for pd-trigger + lumina-carrier; record whether
  delivered (unblocks T11).
- Triage entries 188-236 + 239 into `design/ladder-triage.md`; recompute the
  header summary from the table.
- LEARNINGS entry + row: `test_route_auto_full_flow` fails under full-suite
  parallel load, passes isolated (2026-08-13, Freerouting rung-1 assertion) -
  decide tolerate vs pin.
- Mark `boards/buck-5v3a` superseded by sbuck-5v3a (state note + README line).
- Minimal root `README.md` authority map (codex H7): what this is, maturity
  ("supervised engineering assistant, not unattended release system"), current
  authorities (CLAUDE.md = environment, SKILL.md = operation, SPEC.md =
  historical), safety boundary.
**Accept:** suite green modulo AP63203; `git status` clean except
`boards/xhp-driver/` (U10 owns it); push confirmed; tracking states recorded.

### U1 - Retro-earned checker fixes

**Read:** retrospective s4/s5/s7; LEARNINGS [dfm][gerber][gerbonara],
[decoupling]; `lib/gerblib.py`, `check_decoupling.py`; carrier
`kicad/constraints.json` + `architecture/constraints.json`.
**Build:**
- `gerblib.FabStack.outline`: snap tolerance (1e-5 mm) before polygonize;
  interpolate Edge.Cuts ARCS instead of chording (retro: chords cut rounded
  corners ~0.879 mm inboard -> false copper_to_edge). Regression fixtures:
  carrier gerbers must yield a CLOSED outline and 0 copper-to-edge /
  0 hole-to-edge (retro known-answer); a rounded-corner mutant that fires.
- `check_decoupling`: new switching-regulator input-cap class. Schema: a
  decoupling association may declare `role: reg_input` (P7/S7 emitters +
  intake docs updated); a regulator VIN with no HF ceramic within class
  distance = error. Known-answer: carrier U21 (TPS563201, nearest ceramic
  9.89 mm) MUST fire; all goldens stay clean.
- Carrier data fix (sidecars only, never copper): `V48_RTN` -57 -> 0 in
  `kicad/constraints.json`; reconcile or delete the divergent
  `architecture/constraints.json` copy.
- Re-run `dfm` gate on lumina-par, lumina-strobe, pd-trigger, lumina-carrier
  and `verify` on carrier; record deltas in state (retro predicts carrier
  verify drops ~8 errors; edge checks now actually run repo-wide).
**Accept:** known-answer tests green (U21 fires, carrier outline closes);
golden + mutant corpus unchanged elsewhere; re-run gate reports recorded.

### U2 - Gate report validation + strict verify coverage (codex C4 + C7)

**Read:** codex C4/C7 evidence lines; `gate.py`, `verify_all.py`,
`gates.yaml`, `statelib.py` hashing.
**Build:**
- `gate.py --report` validation: require schema version, producing script
  identity, `status` success, board/input path match, input digest match
  (statelib norms), generation-time staleness bound; malformed/stale/
  wrong-input -> exit 2, never a pass. Missing `violations` key is INVALID,
  not empty.
- `--commit` requires an explicit board scope; refuse pre-staged paths
  outside it; kill the `git add -A` fallback; a requested-but-failed commit
  is an operational error exit.
- `verify_all --strict`: every APPLICABLE check must run; missing input =
  failure, not skip. Applicability declared per board (constraints/board
  type), not inferred from file presence. Summary gains a coverage matrix:
  `{required, ran, passed, failed, waived, not_applicable(reason, approver),
  skipped_error}`. `place_metrics` gets the same treatment.
- Release contexts (gates.yaml verify-for-release, later U5) use strict.
**Accept:** tamper suite green: error-shaped / empty / stale / wrong-input /
wrong-tool reports all refused; unscoped commit refused; carrier's historic
"dfm pass with edge checks silently skipped" scenario now yields a visible
`skipped_error` -> fail under strict.

### U3 - BOM assembly classes + first-class DNP (codex H1, C9)

**Read:** codex H1/C9; `bom_cpl.py`, parts.json shapes; rf-term hand-authored
`fab/BOM.csv` (R1 off-board); rf-de board-local DNP filter + its 9 sites.
**Build:** `assembly_class` per part: `{smt_placed, hand_install, off_board,
dnp, customer_supplied, select_on_test}`. BOM lists ALL intended parts with
class + instructions column; CPL = `smt_placed` only. DNP lives in canonical
parts data, not board-local filters. Port rf-de's 9 DNP sites and rf-term's
R1 (`off_board`, select-on-test, BeO note) into canonical data. `dfm_check`
consumes classes (missing-LCSC on non-placed parts is not a warning;
missing on `smt_placed` IS a failure).
**Accept:** regenerating rf-term BOM/CPL preserves R1 + instructions
(byte-diff vs current hand-authored semantics); regenerating rf-de BOM/CPL
omits exactly the 9 DNP refs with no board-local filter in the loop;
`bom_cpl.json` evidence no longer reports pass with `bom_complete: false`.

### U4 - Knowledge library + trigger-keyed retrieval

**Read:** design decision 2 above; T4 remediations (`reference/remediations/`),
`reference/topologies/buck`, `datasheet_extract.py`, SKILL.md spawn steps,
`agents/placement.md` + `router.md`.
**Build:**
- `reference/knowledge/records/*.yaml`, schema-validated:
  `{id, classes[], applies{topologies[], packages[], interfaces[]},
  rule (machine-checkable fields) | null, prose, sources[{file, page}],
  status, origin}`. Lint like `validate_registry` (every named script/flag/
  path must exist).
- App-note ingestion: `datasheet_extract --app-note` variant - extracts
  layout rules into record-shaped output + grounding payload; PDFs stored
  under `reference/knowledge/sources/`.
- Retrieval wiring (deterministic, no agent judgment): orchestrator spawn
  step reads the P2 block list -> injects matching class records into P6/P7
  spawn prompts; P3 part packages key package records into part-sourcer /
  placement inputs; violation-kind -> remediation stays as-is. SKILL.md edit
  budget <= 10 lines (spawn-step pointer only).
- Migrate `topologies/buck` content into records (file may remain as a
  generated view).
**Accept:** a synthetic board declaring a buck block gets power-loop/EMI
records in its P6 spawn prompt (test-pinned); records lint green; app-note
extraction round-trips on one real buck app note.

### U5 - Release attestation + durable waivers (codex C1 + H9) [ultracode]

**Read:** codex C1/H9 + "Release manifest design" section; `statelib.py`,
`state.py`, `order_submit.py`, tasks.yaml `order` verb; U2's coverage matrix.
**Build:**
- Derived release disposition (never hand-set): `{draft,
  engineering-validated, release-candidate, order-ready, ordered, built,
  bring-up-passed, derated, rework-required, blocked}`.
- Immutable attestation manifest binding: normalized source+generated hashes,
  gate report digests + U2 coverage matrix, waivers, fab zip/BOM/CPL hashes,
  manufacturing options (copper oz, stackup id, finish, layer count),
  human approvals, known restrictions. Any bound-input change invalidates.
- Durable waivers: fingerprint = check + kind + net + refs + rounded pos +
  artifact hash + checker version; expiry/approver; a changed artifact or
  checker invalidates unless re-approved (kills the empty-ref subset match).
- `order` verb + `order_submit` preconditions consume ONLY the attestation;
  a manufacturing-option override (the pd-trigger 1 oz case) invalidates it.
- Migrate stm32-blinky + usb-buck as the two reference attestations.
- Ultracode adversarial review of the policy (T8's 5-lens find+refute shape).
**Accept:** order REFUSES lumina-carrier and rf-de-20m in their current
recorded states even with fresh dfm; a one-coordinate board nudge, a waiver
edit, or a copper-weight change each invalidate; the two reference boards
attest green end-to-end.

### U6 - Workspace learnings + promotion pass (codex H5)

**Read:** design decision 3; `boards/rf-de-20m/LEARNINGS.md` (66 entries +
queue); T4 triage format; `recipes/full-run.md`, `recipes/review.md`.
**Build:**
- Standard workspace `LEARNINGS.md` format (dated, tagged, stage-tagged) +
  machine-readable promotion queue (`learnings/queue.yaml` per workspace:
  `{entry, stage, proposed_level, targets, status}`).
- Run-close step appended to full-run + review + fix recipes: compile the
  workspace's new entries into the queue.
- `promote` verb + recipe, three operator modes over the SAME queue: owner
  at run end; general agent sweeping all workspaces; stage-scoped learner
  pull. Promotion writes to the ladder level: script check / cost term /
  template / prompt line / knowledge record (U4) / bench item; marks the
  queue entry resolved; global entries also land in root LEARNINGS + triage.
**Accept:** rf-de's 66-entry queue processed end-to-end - each entry promoted
or explicitly declined with a reason; tasks.yaml row + recipe lint green;
a golden-workspace dry run compiles a queue from injected entries.

### U7 - Learning mode harness

**Read:** design decision 1; v2 plan appendix (bench tuning loop);
`bench.py`; `agents/placement.md`; U4 record contract; U6 queue format.
**Build:**
- `learn` verb (tasks.yaml + recipe + SKILL verb-line, same commit) +
  `agents/learner.md`: the learner owns ONE stage's artifact set (agent
  contract, templates, cost terms, scorer) and may not touch other stages;
  loop = spawn isolated stage agent on frozen input -> render -> owner
  grades -> learner converts the critique into a CLASSED artifact edit
  (prompt / template / cost-term / scorer / record) -> fresh re-run.
- Scorer-divergence rule in the contract: when the owner's verdict and the
  bench score disagree, the scorer is missing a term - fixing the scorer IS
  session work, because the recorded scorer replays the owner's judgment on
  production runs.
- Exit checklist (mechanical, in the recipe): freeze owner-approved output
  as a graded bench fixture (`--baseline`), commit scorer terms, index new
  records, root LEARNINGS + triage rows, re-run the stage's OTHER frozen
  fixtures for regression, commit.
- `bench.py` additions only if the flow needs them (graded-fixture capture
  helper); pre-load the learner with the stage's promotion-queue entries
  (U6) and knowledge classes (U4).
**Accept:** `learn` plans on a real workspace with every step bound;
fixture-freeze round-trips (approve -> baseline -> `--compare` exits 1 on a
seeded regression); learner contract passes registry lint; dry-run with a
scripted stand-in critique produces a classed edit + exit checklist.

### U8 - Buck placement teaching, cycle 1 (owner present, EXCLUSIVE)

**Read:** `design/stage-evals/P6.md` deferred specs (hot-loop template,
corridor primitive, blocker eviction); sbuck-5v3a final placement;
carrier U21 region (known-bad, defect R1); owner-supplied app notes.
**Build (via the U7 loop, owner grading):** buck hot-loop template shipped;
scorer terms the owner rules (candidates: hot-loop area, input-cap-to-VIN
distance by class, thermal-via fit per package, FB-node keepouts); >= 2
graded fixtures committed (sbuck region + one more; carrier U21 as the
negative known-answer); app notes ingested as power-loop/EMI records.
**Accept:** owner closes the session satisfied; exit checklist complete;
`pd_trigger_place` + `golden_blinky2_place` scores not regressed; the new
graded fixtures baselined.

### U9 - Cross-stage rails (P3 screens + budgeted backward spawns)

**Read:** design decision 4; LEARNINGS 2026-08-09 (SO-8EP via capacity,
DB128L orientation, netclass-floor vs stubs); `datasheet_extract.py`,
part-sourcer + placement contracts, `board_update.py`, invalidation map.
**Build:**
- P3 `layout_implications` extraction fields: thermal-via capacity,
  orientation constraints, courtyard area vs board budget, pitch vs routing
  floor, wire-entry direction. Part-sourcer scores candidates on them;
  placement templates consume them. Known-answers: SO-8EP (max 12 vias,
  4x4 impossible) and DB128L orientation, as fixtures.
- Backward-spawn protocol in placement/router recipes: file an issue, spawn
  part-sourcer/scout with a narrow brief, apply results via `board_update` +
  `state.py edit --class` (invalidation map re-gates). Spawn budget per
  stage (default 2) in `budgets`; spawn ledger tags cross-stage spawns.
  One writer per artifact stands; scouts are read-only.
**Accept:** P3 on the sbuck netlist emits the SO-8EP known-answer; a
simulated placement dead-end round-trips issue -> spawn -> board_update ->
correct stale-gate set; budget exhaustion checkpoints to the owner.

### U10 - xhp-driver brief + full run (first live validation)

**Read:** owner's brief input; SKILL v2 front door; U8 outputs; V20 register.
**Build/do:** write `boards/xhp-driver/brief/` with the owner; run the full
pipeline on it (first live run carrying taught buck knowledge + U-wave
mechanisms). Close V20 items it exercises (route_cleanup live leg, silk
solver at scale, spawn-tier downgrades). Workspace learnings + run-close
queue per U6.
**Accept:** normal pipeline acceptance (gates through P9); V20 register
updated with live evidence; promotion queue compiled at close.

### U11 - P7 routing teaching, cycle 2 (owner present; after U10)

Scope set by evidence: Freerouting necks tracks to pad width at small-part
stubs (most of verify's current noise); post-route netclass width
enforcement/repair; corridor cost term calibration; net-scoped reroute
primitive (the T10 gap - today it is a hand op-list). Same U7 loop and exit
checklist. Spec the session from U10's routed board + verify findings.

### U12 - Pre-credential order/state safety (codex C3+C5+C6) [ultracode]

**Trigger: schedule before JLCPCB API credentials are EVER wired; anytime
otherwise.** Snapshot/restore containment (reject traversal/absolute/
symlink; staged transactional restore); order latch: OS-exclusive lock across
load->check->create->finalize, unique-temp fsync atomic writes, append-only
attempt journal, corrupt manifest = hard refuse; state/board writer locks +
base-digest compare-and-swap. Fault-injection test suite (concurrent
creators, truncated latch, crash mid-restore). Codex "essential regressions"
list is the test menu.

### U13 - Coverage contracts: levels, envelopes, maturity, the trigger

**Read:** design decision 5a; `knowledgelib.py`, `knowledge.py`,
`reference/knowledge/records/`, `constraints_lint.py` SECTIONS,
`recipes/full-run.md`; U4 + U7 PROGRESS interface notes.
**Build:**
- Schema v2: `level`, `envelope` (unit-suffixed keys, required at
  topology/family/part; principle records carry none), `maturity`,
  `generalizes[]` (targets must exist). Lint enforces all of it; existing
  records tolerate missing new fields as `draft` until U14 backfills.
- New record kind: coverage checklist per topology/interface - the classes
  (and minimum levels) that must be populated before designing it. The
  first research pass on a new topology PRODUCES its checklist; owner
  approves it like any record.
- `knowledgelib.coverage(workspace)` + `knowledge.py --coverage`: per
  block/part/interface slot -> {covered (record ids, envelope + maturity
  floors met), provisional, gap}. Part-level coverage counts the P3
  datasheet layout extraction (thin/empty layout section = a detectable
  gap). Gap entries are research task specs (slot, missing levels, known
  principle parents).
- T11 wiring: a `proven` upgrade path fed by bring-up evidence
  (mechanism built now, exercised at T11).
- Recipe wiring: full-run runs coverage at P2 exit and P3 exit; the
  agent-mapping step (fuzzy record->slot) is a recipe step with
  schema-forced output, logged for audit.
**Accept:** synthetic workspace with a buck block at an operating point
inside/outside record envelopes flips covered<->gap deterministically;
maturity floor enforced (draft never satisfies); checklist gating
test-pinned; lint green on migrated records; coverage report emitted in a
full-run dry-run.

### U14 - Record backfill + approval session (OWNER PRESENT, short)

**Read:** all 16+ records + their cited sources; U13 schema.
**Build/do:** agent proposes level + envelope (with the "what does this
rule scale with" justification, source-checked) + maturity per record; the
owner rules each; all land `approved`. Draft + approve coverage checklists
for buck and the in-fleet interfaces (100BASE-TX, USB-FS). Record the
rulings as LEARNINGS where non-obvious.
**Accept:** every record lint-green at schema v2 with owner-approved
maturity; coverage checklists exist for buck + both interfaces; a
pd-trigger-fixture coverage run reports covered on buck slots.

### U15 - Research verb: acquisition, synthesis, second reader

**Read:** design decision 5a; U13 coverage/gap spec; `datasheet_extract.py`
--app-note flow; U6 queue format; `agents/librarian.md` (naming);
order_submit's exit-2-without-credentials pattern.
**Build:**
- `research` verb (tasks.yaml + recipe + `agents/researcher.md`): input =
  a gap spec. Source-tier policy (part vendor's own layout section >
  vendor app note > cross-vendor app note > forum, never sole-source).
  Researcher agents alone get WebFetch/WebSearch, restricted to a
  vendor/distributor domain allowlist (reference/knowledge/domains.yaml);
  downloads quarantined to `<ws>/research/sources/`.
- Synthesis: mandate VISUAL page reads for cited pages (layout figures are
  the highest-value content; text extraction cannot see them); figure
  descriptions land in record prose; envelope dimensions justified per
  record. Second reader independently re-reads cited pages and refutes ->
  `verified`. Workspace-first storage + promotion-queue entry (U6).
- Auto-trigger wiring: full-run launches research on every gap (owner
  ruling); per-gap depth cap + per-run research cap in `budgets`,
  cap-hit -> visible checkpoint, never silent truncation.
- Distributor APIs (Digikey/Mouser) for parametric data + authoritative
  datasheet links: client built now, exits 2 with the exact missing
  credential until owner registers keys (owner-supplied prerequisite).
- Research-quality bench hook: `bench --freeze`-style capture of
  owner-graded extractions (fixtures accumulate from teaching sessions).
**Accept:** a seeded gap (topology with no records) round-trips gap ->
research -> draft records with page-cited sources -> second-reader
verified -> queue entry, inside the caps; domain-allowlist enforcement
test-pinned (off-list fetch refused); cap-hit checkpoint fires; Digikey
client exits 2 with a precise missing-credential message.

## Not in this plan

- Codex P2/P3 (packaging, CI, repo restructure, LFS/storage separation):
  revisit after T11 + U10 land hardware/live evidence.
- lumina-par / lumina-strobe resumes (task mode, anytime; check the
  phantom-3313 stackup inheritance first - retro s6).
- T11 hardware bring-up: unchanged, lives in `ai-ee-v2-plan.md`. Before
  carrier power-on: R1 rework (100 nF at U21 pin 3 -> the GND via at rel
  46.302, 57.191). pd-trigger runs derated until 1 oz thermal validation.
