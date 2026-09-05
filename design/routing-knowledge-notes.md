# hwde PCB Skill — Routing, Placement, Verification, and Knowledge Architecture

> **Provenance:** external design notes from an owner conversation with another
> agent (received 2026-08-06). Kept verbatim below the adoption block. Tool
> claims are that document's own; where they conflict with `LEARNINGS.md`,
> LEARNINGS (machine-verified on this host) wins.
>
> **Adoption status (2026-08-06 verdict, folded into `ai-ee-v2-plan.md`):**
> - Already built in v1 (doc re-derived it): mutation corpus (S1), locked
>   critical pre-route via DSN `(type protect)` guide wires (route_critical),
>   findings-not-geometry gates, derived-feature suite (return path,
>   constriction, diff-pair, plane health, decap loop nH), script-only rule
>   derivation, custom DRU pushdown, refill-before-DRC, stage-scoped agents.
> - Contradicted/nuanced by machine-verified learnings: FR 2.2.4 DSN reader
>   wedges on guide-wire copper (V14); "LLM never emits geometry" is too
>   absolute — coordinate-level place_edit/route_edit with DRC as sole oracle
>   shipped lumina-carrier (refined rule: never WITHOUT a deterministic
>   re-check); power-as-pours doesn't hold on 2L; the netclass-matrix lever is
>   poisoned until rules_gen stops flattening (plan T1).
> - Adopted → plan steps: maturity ladder + triage rules → T4/convention;
>   intra-block placement templates → T6; DSN post-process assertions → T1;
>   trigger-indexed remediations → T4; per-stage frozen fixtures + composite
>   score + ablation method → T5/T6.

---

Design notes for a Freerouting-based PCB pipeline combining scripts and LLM stages.

**Provenance:** Tool behaviour, file formats, and CLI flags are sourced (links in
[References](#references)). The layered architecture, knowledge maturity ladder, and feedback-loop
design are proposed here, reasoned from the stated constraints — not documented standards.

---

## 1. Core principle

**The LLM never emits geometry.**

Routing is a constrained geometric search over a shared occupancy map. A model emitting coordinates
token-by-token has no working memory of what is already occupied, so DRC violations compound and
early net choices lock in bad topology with no rip-up mechanism.

The model produces a **plan** — a machine-checkable constraint spec. A deterministic solver produces
the geometry.

This principle recurs at every layer:

| Layer | LLM emits | Solver/script produces |
|---|---|---|
| Routing | Netclasses, rules, priorities | Traces, vias |
| Placement | Relative constraints (`near`, `symmetric_about`) | Coordinates |
| Verification | Nothing — it reads findings | Measurements |

### Budget rule

LLM calls scale with the number of distinct **decisions**, not the number of geometric objects.
Never call per-trace. Call per-netclass and per-functional-block. A 200-net board should be roughly
5 calls, not 200.

---

## 2. Freerouting is an executor, not a designer

SI/PI/EMI intent, trace sizing, connection strategy, and plane strategy are all expressible as DSN
content. The goal is not to make Freerouting understand design intent — it is to write a richer DSN.

### Three levers

**1. Netclass rules.** KiCad's DSN export writes per-netclass clearance, track width, via diameter
and drill. Freerouting maintains a clearance *matrix* between classes, so class-to-class clearance is
available — not just a global value. Analog-to-switching separation lives here.

**2. Keepouts.** DSN carries `wire_restrict`, `via_restrict`, and `poly_restrict` areas. Used in
practice for things like protecting GND via groups in HF designs. Applies to antenna keepouts,
analog islands, under-inductor exclusions.

**3. Pre-routed locked wiring — the highest-leverage lever.** Pre-routed traces go in the DSN wiring
section; Freerouting treats existing traces as fixed and routes only the remaining unconnected nets.

The consequence: Freerouting never needs to understand decoupling. Script the decap loops, power
path, crystal, feedback node, and diff pairs; lock them; let Freerouting fill in general nets around
them. Power nets are excluded entirely and handled as pours — the CLI supports ignoring net classes
such as GND and VCC directly.

### Known tool caveats

- KiCad DSN export has had fidelity bugs, including netclass clearances written incorrectly and
  copper-to-hole clearance ignored in favour of the Default netclass — producing Freerouting output
  that violates DRC. **Post-process the DSN and assert on it rather than trusting the export.**
- CLI DRC has open reports of not matching interactive DRC for some custom rules involving component
  classes. Validate parity on your specific rule set.

---

## 3. Top-level pipeline

| # | Stage | Owner | Artifact | Test type |
|---|---|---|---|---|
| 1 | Net classification | LLM (1 batched call) | `net_classes.json` | Labelled golden set; per-class precision/recall |
| 2 | Rule derivation | Script | Widths, clearances, impedance | Unit tests vs. IPC-2152 / IPC-2221 |
| 3 | Stackup + pour plan | LLM proposes, script validates | Layer roles, pour nets | Invariant assertions |
| 4 | Placement | Sub-pipeline (§4) | Positions, rotations | Objective metrics |
| 5 | Critical pre-route | Script templates | Locked wiring | Geometric assertions |
| 6 | DSN emit | Script | `.dsn` | Schema + round-trip test |
| 7 | Freerouting | Solver | `.ses` | Completion %, vias, length |
| 8 | Import + audit | Script | Board + findings | DRC + derived SI checks |

Notes:

- Stage 1 is the only stage that genuinely needs LLM evals.
- Stage 2 must never touch an LLM. It is table lookup; a model computing trace width from current is
  a liability.
- **Every stage boundary is a frozen fixture.** Golden artifact in, golden artifact out. This is what
  stops a placement regression from cascading into a routing test failure.

### Finding the bottleneck empirically

Ablation. Replace stage N with a hand-authored artifact, re-run end-to-end, measure the delta on the
composite score. Largest delta is the bottleneck.

Prior: placement, since Freerouting output quality is largely determined before it starts.

---

## 4. Placement sub-pipeline

"LLM groups, script legalizes" is too coarse. Placement decides routability, SI, PI, and EMI before
a single trace exists, and needs the same decomposition as routing.

### Constraint vocabulary

The LLM emits **relative constraints**, never coordinates.

- `near(C12, U3.pin7, 1.5mm, same_side)` — checkable, composable, solvable
- `C12 at (14.2, 8.6)` — requires a global occupancy map the model does not have

Vocabulary: `near`, `adjacent_to_pin`, `same_side`, `align`, `symmetric_about`, `inside_region`,
`order_along_axis`, `minimize_loop([...])`, `orientation`.

This makes placement solvable and gives a test surface independent of whether the result is *good*.

### Sub-stages

| # | Stage | Owner |
|---|---|---|
| 0 | Mechanical anchors (connectors, mounts, antenna, indicators) | Given — read from constraints, not decided |
| 1 | Block partitioning | LLM (semantic clustering of netlist) |
| 2 | Topology recognition + role assignment | LLM (classification) |
| 3 | Intra-block placement | **Script — parameterized templates** |
| 4 | Block floorplan | LLM proposes adjacency weights; script solves |
| 5 | Legalization + orientation for routability | Script |
| 6 | Congestion-driven refinement | Script measures; LLM edits constraints |

### Stage 3 is where SI/PI/EMI actually lives — and it must be code

Parameterized templates, written once, covering most real designs:

- Buck converter hot loop (Cin+ → HS FET → LS FET → Cin−) minimized in area
- Feedback divider at the FB pin, sense trace routed away from the switch node
- Decap loop area minimized
- Crystal load caps symmetric, with guard
- Kelvin connections on sense resistors

Roughly 20 templates covers the common ground. Asking a model to reason about loop inductance
freehand on every board will never be as reliable.

This reduces stage 2 to pure classification:

> "This is a synchronous buck; U3 = controller, C4/C5 = Cin, L1 = inductor, C8 = Cout,
> R2/R3 = FB divider, SW = switch node."

Cheap, batched, testable against a labelled golden set.

### Placement metrics

HPWL, ratsnest crossings, decap distance-to-pin, crossings-under-ICs.

---

## 5. Verification

**Rule: the LLM never reads geometry.** Raw `.kicad_pcb` is tens of thousands of coordinate lines the
model cannot compute over. Extract *derived features* and hand it a findings list.

### Extraction stack

- `kicad-cli pcb drc --severity-all --format json` — emits a schema'd report
  (`schemas.kicad.org/drc.v1.json`) with `violations[]` carrying type, severity, description, and
  item positions with UUIDs.
- `--refill-zones` / `--save-board` (KiCad 10) — use these; stale zone fills produce false clearance
  results.
- **KiCad custom DRC rules** — underrated. A large fraction of SI/PI checks can be expressed in
  KiCad's native rule DSL rather than reimplemented in Python, and then surface in the same JSON.
  Audit what can be pushed down. Validate CLI/interactive parity (see §2 caveats).
- `kicad-cli pcb export ipc2581` — structured board data if native-format parsing is undesirable.
- `pcbnew` + Shapely — for everything KiCad will not compute.

### Derived features to build

This is the part no tool provides.

| Feature | Computation | Catches |
|---|---|---|
| **Return path** | Per segment, resolve reference plane from stackup; test whether copper exists beneath. Emit discontinuities (split crossings, layer changes, plane edges) with distance to nearest stitching via of the return net | Radiated emissions, crosstalk |
| **Loop areas** | Enclosed area of each decap and hot loop — one scalar per instance. Directly computable once stage-2 role assignment identifies the pads | PI/EMI — the primary number |
| **Constriction** | Minimum copper cross-section along each power path vs. required current | 5 A through a 0.3 mm neck |
| **Plane health** | Connected-component analysis per pour (islands, orphans); morphological erosion for necking width; via-row slot detection | Return path integrity |
| **Coupling proxy** | Parallel run length between net pairs within N× dielectric height, same-layer and broadside. Report worst K | Crosstalk |
| **Conformance** | Width histogram vs. class target; diff-pair skew and gap variance; length-match spread | Rule drift |

### Two artifacts from one extraction

1. **Findings list** for the LLM — `{check_id, severity, nets, refdes, location, measured, threshold,
   delta}`, sorted by severity × delta, capped at ~50. The model reads this and decides what to
   change *in the plan*.
2. **Composite scalar** for CI/regression. This is what tells you whether a change helped.

### Verify the verifier

The failure mode is a checker that reports clean on a bad board.

Build a corpus of boards with **deliberately injected defects** — decap moved 8 mm away, trace
crossing a plane split, hot loop rotated open, necked power path — and assert each check fires with
the expected severity and location. Mutation testing for the extraction layer.

Without this, a clean report means nothing and every downstream LLM decision is built on it.

---

## 6. Knowledge indexing

### Maturity ladder

The failure mode is not volume — it is knowledge sitting at the wrong level. Triage each item:

| Level | Form | Context cost | Guarantee |
|---|---|---|---|
| 0 | Prose in the prompt | Every run | A hope |
| 1 | A check that measures it | Zero | You find out afterward |
| 2 | A check with a failing threshold | Zero | It cannot ship broken |
| 3 | A template that makes it correct by construction | Zero | It cannot be built broken |

**If a script can check it, it does not belong in the prompt.**

Worked example — same knowledge, four homes, wildly different reliability:

- L0: "Keep decap loops small"
- L1: `loop_area_mm2` measured and reported
- L2: Threshold that fails the run
- L3: Decap placement template

**Health metric: SKILL.md should shrink over time.** If it is growing, knowledge is not climbing.

### Index by trigger, not by topic

Organizing as `si/`, `pi/`, `emi/`, `thermal/` is a library taxonomy — useless at runtime, because
the agent never knows "I need EMI knowledge." It knows *"stage 2 detected a synchronous buck"* or
*"check `reference_discontinuity` fired 6 times."*

Key references on values the pipeline already computes:

| Trigger | Reference |
|---|---|
| Detected topology | `references/topologies/buck.md` |
| Net class | `references/netclasses/switch-node.md` |
| Finding type | `references/remediations/<check_id>.md` |

Retrieval becomes deterministic lookup, not semantic search.

This aligns with documented skill structure: references are organized by variant so only the relevant
file is read, under a three-level loading system — metadata always in context, SKILL.md body on
trigger (under ~500 lines ideal), bundled resources only as needed.

**Scripts execute without being loaded at all.** Exploit this hardest: IPC-2152 tables, impedance
formulas, and template geometry live in `scripts/` at zero context cost while remaining fully
available.

### Fan out per stage

The classifier agent gets the netlist and the taxonomy, and nothing about routing. The floorplan
agent gets blocks and adjacency rules, and no IPC tables.

Set a per-stage context budget. Treat overruns as a signal: a stage whose context keeps growing is
telling you its knowledge needs to move down the ladder.

---

## 7. Feedback loops

Keep the two strictly separate.

**Inner loop (within a run):** findings → plan edit → re-run. Ephemeral. Nothing persists.

**Outer loop (across runs):** append-only ledger, triaged into durable artifacts.

```
{run_id, board_id, stage, check_id, severity, measured, threshold, agent_action, resolved}
```

### Triage rules

**The outer loop must never resolve a failure by appending prose to the prompt.** That is how skills
rot.

| Observation | Correct response |
|---|---|
| Same `check_id` recurs despite existing guidance | Knowledge must become a check or template. Rewording is the wrong fix and will keep failing |
| Rule violated, and the reference containing it was never loaded | The **trigger key** is wrong, not the content. Different fix entirely |
| Check fires, agent's fix reliably works | Leave it. Functioning as designed |
| Check never fires across the corpus | Dead weight or broken. Run against a mutated board to determine which |

Distinguishing row 2 from row 1 is what stops endless rewriting of prompts that were never being
read.

### Fitness function

- Every fix ships with a regression fixture — the board that failed joins the corpus
- Composite verification score is the fitness function: change a threshold, template, or prompt,
  rescore against the frozen corpus, revert if it does not improve
- **Score per stage as well as end-to-end**, using golden inter-stage artifacts. Otherwise a routing
  gain masks a placement regression and you optimize into a local minimum

Scoring dimensions: completion %, via count, total length, DRC violations, plus derived SI checks
(reference-plane discontinuities without nearby stitching via, decap loop area, stub length, traces
crossing splits).

---

## 8. Open items

- Build the mutation corpus (§5) — prerequisite for trusting any other metric
- Run stage ablation (§3) to confirm or refute the placement-bottleneck prior
- Audit which derived checks can be pushed into KiCad's custom DRC DSL, and validate CLI/interactive
  parity
- Post-process and assert on DSN output rather than trusting KiCad export fidelity
- Inventory the intra-block template set; confirm whether ~20 covers the target board classes

---

## References

- [KiCad CLI documentation (10.0)](https://docs.kicad.org/10.0/en/cli/cli.html) — `pcb drc` flags,
  `export ipc2581`
- [KiCad DRC JSON schema example](https://gitlab.com/kicad/code/kicad/-/work_items/22330) — report
  structure
- [CLI vs. interactive DRC parity issue](https://gitlab.com/kicad/code/kicad/-/work_items/24211) —
  custom rule caveat
- [Freerouting issue #574](https://github.com/freerouting/freerouting/issues/574) — `kicad-cli` DRC
  integration discussion


---

## T6 position record (P8A-6, 2026-08-06): NO generic free-form waiver list in constraints

Question asked by the T6 P8 evaluation: is the waiver mechanism expressive enough? After the
land_pattern_pitch class (T6) joined return_path's cross-net class, the answer is yes for every
class observed across six boards - and deliberately so. Both shipped waiver classes are
AUTO-DERIVED from ground truth (return_path: stackup geometry; creepage: same-footprint
identity), so they cannot rot, cannot be fat-fingered onto a real defect, and need no per-board
authoring. A free-form constraints `waivers[]` (match by check/kind/net/ref) would let a board
run silence anything - exactly the check-weakening T6 is forbidden to do, made ambient. The H4
wholesale-waiver failure on lumina-carrier shows humans under pressure waive coarsely. The
HUMAN-approved per-finding path exists at the GATE instead (gate.py --waivers sidecar, T6
P8B-4: mandatory reason + approved, refs-subset matching, never agent-invented). Revisit only
if a third class appears that ground truth cannot derive.
