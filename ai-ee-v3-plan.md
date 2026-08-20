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
    bare-bones leg (owner-launched, added 2026-08-16 from the bb-buck run):
      U16 (URGENT - before any further board run) -> U17 || U19 -> U18
      (needs U17). Hold bb-ldo / bb-adc / bb-amp / bb-mcu until U16+U18
      land, or each inherits bb-buck's unrecorded gates and its
      correct-but-not-canonical geometry.
    harvest leg (added 2026-08-20 from the four-run batch): U20 || U21
      (after the bb close-out resumes settle) -> U22 (owner) -> U8 (owner;
      U20 is a hard prerequisite, U22 strongly preferred first). Optional
      after U8: re-run the bb-ldo brief as an A/B against the taught scorer.
      Hold further learning-target board runs until U8 lands.
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
| U16 | Opus 5 | high | - | no |
| U17 | Opus 5 | xhigh | - | no |
| U18 | Opus 5 | max | - | optional (rule the target table) |
| U19 | Opus 5 | high | - | optional (rule the assembly-cost weight) |
| U20 | Fable | high | - | no |
| U21 | Opus 5 | high | - | no |
| U22 | Fable | high | - | YES (batch rulings on ~86 records) |

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
carrier U21 region (known-bad, defect R1); owner-supplied app notes;
the FIVE bb-* boards' renders as the grading corpus (bb-buck
constrained vs the four canonical boards - aspect-ratio and
connector-placement craft terms come from grading these), plus
bb-ldo's reports/aspect-study/ sweep. Prerequisite: U20 (do not
teach against a known annealer defect).
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

### U16 - Gate results must reach state.json (bb-buck defect, urgent)

**Trigger: BEFORE any further board run.** bb-buck reached P9 with a complete
fab package and six PASSING gate reports on disk while `state.json` recorded
NONE of them: 114 history events, zero gate events, `gates: {}`,
`gates_passed: []`, `resume` still naming P4 erc as the next gate. The
orchestrator ran `gate.py --gate <g> <input> --commit` at every phase but
never `state.py record-gate`, which SKILL rule 3 requires and nothing
enforces. U5's derived disposition held the line (`draft`, unorderable), but
there are no input hashes, so freshness, invalidation and attestation are all
unavailable on a board that otherwise passed everything. This is codex C1's
phase-is-not-a-certificate split, reproduced by our own pipeline.

**Read:** `gate.py`, `state.py` record-gate + set-phase, `statelib.py`
freshness, `recipes/full-run.md` gate steps, `boards/bb-buck/state.json`,
`boards/bb-buck/reports/gate-*.json`.
**Build:** close the hole mechanically, not by prose. Candidates (the session
picks and justifies): `gate.py --workspace <ws>` records the result itself on
every run (recording stays optional for golden/mutant inputs that have no
workspace, so the test corpus is unaffected), the full-run recipe's gate steps
always carry it, and `state.py set-phase` refuses - or at minimum loudly
warns - when advancing past a gate phase whose gate has no recorded result.
Back-record bb-buck's six gates from their committed reports so the board
keeps honest provenance, and re-hash its artifacts (the P6 `move_fp` stale
mark on `gerbers` was never cleared although the package was re-exported).
**Accept:** a scripted P4->P9 dry run leaves every gate recorded WITH input
hashes and `resume` naming the true next gate; a gate run without a workspace
still works (corpus tests green); bb-buck's `resume` reports six gates passed
and fresh; a test pins that every gate step in the full-run recipe carries the
workspace.

### U17 - Editable board outline (`board_edit.py --outline`)

The pipeline can move a part (`place_edit`), edit copper (`route_edit`) and
add/swap/remove parts on a routed board (`board_update`), but NOTHING can edit
Edge.Cuts: the outline is written once at P5 by `board_init --outline` from the
netlist, so changing it means a rebuild that discards placement and routing.
That forces the final size to be guessed before placement exists - the trap
bb-buck hit - and it BLOCKS U18's canonical level, whose whole flow is
place first, then shrink the board to fit.

**Read:** `board_init.py` outline/corner-radius/cutout construction,
`place_edit.py` + `lib/place_swig.py` (the staged-worker-verify-swap pattern to
copy), `route_edit.py`, `lib/geom.py` outline parsing, `invalidation.yaml`,
`dfm_check.py` edge legs, U1's gerblib outline snap/arc work.
**Build:** `board_edit.py` - outline ops on an EXISTING board (resize to WxH,
shrink-to-fit the current placement + margin, corner radius, edge cutouts),
applied with the place_edit contract: validate, stage inside the board dir,
SWIG worker, independent re-parse verifying the new outline geometry, atomic
swap, byte-identical rollback on any failure. REFUSE (with the offending list,
never a silent clip) when a footprint, copper item or keepout would fall
outside the new boundary or violate edge clearance; a `--report-only` mode
names what must move first. New `outline_change` edit class in
`invalidation.yaml` (stale: place, drc_routed, verify, dfm, gerbers; zones
need a refill; human_hold 2). Recipe step for the shrink-to-fit flow.
**Accept:** on a frozen routed fixture, a resize that keeps everything inside
applies and re-parses to the exact new outline with copper untouched and DRC
no worse; a resize that would orphan a part refuses and names it; rollback is
byte-identical; the edit class stales exactly the mapped set; shrink-to-fit on
the bb-buck placement reproduces a legal outline no larger than its bbox +
margin.

### U18 - Learning mode: a target learning outcome drives scope AND binding

bb-buck was correct but not canonical: the owner's 35x25 outline (given at H1)
bound every later stage, so placement optimized to FIT rather than to teach the
basics. Learning mode fixes the general case - and per the owner ruling
(2026-08-16) the mode is driven by a TARGET LEARNING OUTCOME which derives both
dials, rather than by two flags the caller sets independently.

**Read:** `reference/build-modes.md` (ultra-bare-bones becomes the block-only
scope tier - reuse it, never duplicate it), `agents/requirements-analyst.md`,
`agents/architect.md`, `agents/placement.md`, both reviewer contracts,
`recipes/full-run.md`, U17's outline flow, U7's `learn` verb + `bench.py
--freeze`.
**Build:** in `build-modes.md`, a learning mode declared as
`learning <target>:` where the target names the outcome. A target entry binds:
- **scope tier** - `block-only` (= today's ultra-bare-bones contract),
  `block+interfaces`, or `product` (protection, filtering, connectors, thermal,
  enclosure fit - what a shippable version of that block needs). "Buck stage
  placement" gets block-only; "production buck" gets product.
- **binding level** - `canonical` (geometry is an OUTPUT: board size, aspect
  and outline follow the reference layout, and any stated dimension that
  fights it LOSES), `bounded` (canonical + ~30 %), `constrained` (the stated
  size binds - what bb-buck accidentally ran), `product` (size, cost and
  thermal all bind).
- **stage under study** (optional) - what the run is meant to teach, which
  names the deliverable to freeze as a bench fixture.
Rules: every relaxed spec is a `state.py decision` and appears in the H1
checkpoint ("ignoring 35x25: the canonical hot-loop layout wants ~45x30") -
relaxation is never silent. The mode relaxes GEOMETRY, cost and packaging
only; never the electrical spec, safety questions, gates, coverage or
research. `canonical` uses U17's flow: provisional outline -> canonical
placement -> shrink to fit -> route once. Reviewers do not report a relaxed
spec as drift. Wire the target through P0 (mark relaxable specs), P2
(geometry as output), P6 (follow the reference layout), and the reviewers.
**Accept:** the same brief at `canonical` and at `constrained` produces
different outlines, with the canonical run recording the relaxation decision
and ending no larger than its own placement needs; a `product`-scope target
admits the protection/filtering blocks that block-only excludes (and the
reviewers flag their ABSENCE at that tier); router `--validate` green; the
mode table is test-pinned against build-modes.md.

### U19 - Bottom-side placement the annealer can DISCOVER

`place_edit` applies an absolute `{"op":"flip","side":"back"}`, `place_seed`
honors a `side` constraint, and the annealer's cost model is already
side-aware (obstacles carry a side; courtyard overlap counts only between
same-side or through-hole bodies). But `place_anneal._propose()` only ever
returns `(component, centre, angle)` - no move changes a part's side - so the
optimizer can respect a side it was GIVEN and can never find that moving a
part to the back tightens a loop or saves area.

**Read:** `place_anneal.py` (`_propose`, `_slide`, the cost terms, obstacle
side handling), `place_seed.py` side constraints, `placelib`, `place_metrics`,
T8's front-side-only region-scan note in `board_update.py`.
**Build:** a side-flip move in `_propose` (guarded by constraints: parts fixed
to a side, connectors, anything the placement group pins), with an
assembly-cost term so back-side parts are not free - a second reflow side is a
real cost, and the term's weight is an owner ruling to record. Satellites must
follow their anchor's side. Report per-candidate side counts in the metrics so
a reviewer sees the tradeoff.
**Accept:** on a fixture where a back-side placement is measurably better, the
annealer finds it and the result re-parses with the part on B.Cu, its
satellites with it, and DRC no worse; side-pinned parts never move; with the
assembly term at its default a board that does not need two sides stays
single-sided (no gratuitous flipping); existing P6 bench fixtures do not
regress.

### U20 - place_anneal must not degrade declared decoupling

Evidence: root LEARNINGS 2026-08-19 - `place_anneal` RE-DERIVES every
satellite slot from `place_seed`, cannot preserve a hand-placed decoupler,
and on bb-adc the re-derived slots FAIL the board's own declared cap
distances while the place gate still passed (the gate's decoupler leg reads
class defaults, not the board's declared per-association limits). The
highest-value placement output is silently degraded on every board.

**Read:** that LEARNINGS entry + its triage row; `place_anneal.py` (bodies /
satellite slotting), `place_seed.py` satellite derivation, `placelib`,
`decoupling.json` association contract (max_dist_mm / max_loop_nh),
`check_decoupling` distance model, `place_metrics` + the place gate's
decoupler leg, bb-adc's frozen board + sidecars (the live fixture).
**Build:** (1) a satellite whose EXISTING placement satisfies its declared
limits is preserved relative to its anchor - anneal moves the cluster, never
re-slots the member; re-derivation only when the existing slot is illegal or
colliding. (2) Hand-placed / locked satellites never re-slot. (3) Candidate
REJECTION, not scoring: any candidate violating a declared per-association
distance is discarded before ranking. (4) The place gate + place_metrics
read declared per-association limits FIRST, class defaults only as fallback
- bb-adc's escape closes. Bench: re-baseline only what legitimately moves.
**Accept:** a bb-adc-derived fixture reproduces the violation pre-fix and is
clean post-fix; a hand-placed decoupler survives an anneal run unmoved
relative to its anchor; place gate fails a board violating its own declared
distances; existing P6 fixtures no regression; suite green.

### U21 - unverified research is loud, never silent

Evidence: bb-amp closed P9 with SIX draft records (the inamp input-stage
rules - bias return, CMRR symmetry, guarding) that the second reader never
cleared. Drafts never inject, so the board was designed WITHOUT its hardest
knowledge - and nothing flagged the stall anywhere.

**Read:** `research.py` (verify / close / status), `researchlib` task
ledger, `knowledgelib` workspace-record folding + coverage buckets,
`recipes/research.md` + `recipes/full-run.md` run-close, bb-amp's research
dir (the fixture).
**Build:** `research.py close` refuses (exit 1, naming the records) while
any task record is still draft, unless `--accept-drafts` records an explicit
state decision; the run-close step surfaces "N draft records never verified"
into the digest, a state decision and the promotion queue; the coverage
report gets a distinct `draft_unverified` bucket (not folded into
provisional); `research.py status` counts verified vs draft per task.
**Accept:** a synthetic task with a lingering draft refuses close and the
override leaves a decision; bb-amp's history reproduces the miss pre-fix;
coverage on a workspace with draft-stalled records names them in their own
bucket; suite green.

### U22 - cross-run promotion + approval pass (OWNER PRESENT)

Input: the five bb-* workspaces' harvest - ~86 research records and ~78
workspace learnings with every queue entry `pending`. This step is
LOAD-BEARING, not housekeeping: records satisfy coverage at the default
floor only once APPROVED, so until this pass runs, every future board in
these domains re-researches what the batch already learned.

**Read:** `recipes/promote.md` + `learnings.py`, `knowledgelib` validate
--strict + envelope grammar, the U14 batching pattern (4 batched question
sets, owner takes/overrides recommendations), all five `learnings/queue.yaml`
+ `research/records/`.
**Do:** cross-workspace dedupe FIRST (same rule from multiple boards -> one
record, sources accumulate, envelopes union only where the mechanism is
identical; contradictions surfaced to the owner, never averaged); level +
"what does it scale with" sanity per U14 discipline; batch the owner rulings;
promote approved records into `reference/knowledge/records/` (maturity
`approved`, approval note = the ruling); resolve every queue entry
promoted/declined with a reason; root LEARNINGS + triage rows for the
promotions.
**Accept:** zero `pending` entries across all five workspaces;
`knowledge.py --validate --strict` green; dedupe stats reported (in ->
out); coverage at the DEFAULT floor on synthetic ldo/adc/inamp/mcu
workspaces shows the new domains covered by approved records.

## Not in this plan

- Codex P2/P3 (packaging, CI, repo restructure, LFS/storage separation):
  revisit after T11 + U10 land hardware/live evidence.
- lumina-par / lumina-strobe resumes (task mode, anytime; check the
  phantom-3313 stackup inheritance first - retro s6).
- T11 hardware bring-up: unchanged, lives in `ai-ee-v2-plan.md`. Before
  carrier power-on: R1 rework (100 nF at U21 pin 3 -> the GND via at rel
  46.302, 57.191). pd-trigger runs derated until 1 oz thermal validation.
