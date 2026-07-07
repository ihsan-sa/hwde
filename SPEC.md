# ai-ee — AI PCB Design Flow Skill: Design Specification

**Target:** Claude Code skill implementing an end-to-end PCB design pipeline: natural-language brief → researched architecture → schematic → placed & routed board → verified → DFM-checked → order-ready fab package.

**Invocation:** `/ai-ee <description>` with optional attached documents (requirements docs, datasheets, reference schematics, mechanical constraints).

**Design philosophy:**
1. **Soft top, firm bottom.** The orchestrator uses model intelligence to decide *which* agents to spawn and in what order. Each spawned agent is narrow-scoped, near-deterministic, and does most of its work by invoking scripts with defined I/O contracts. As models improve, the orchestrator and reviewer agents get smarter for free; the scripts stay correct.
2. **Scripts over judgment wherever possible.** Anything checkable geometrically or numerically (return paths, decoupling proximity, trace width vs. current, DRC, DFM rules) is a script, not an LLM opinion. LLM judgment is reserved for design intent, tradeoffs, and review of rendered output.
3. **Files are the interface; context is disposable.** All state lives on disk. Agents receive file paths + a short brief, and return short summaries + report files. No agent (including the orchestrator) carries design data in its context. Any file edit that is not an agent's primary task is delegated to a sub-agent.
4. **Hard gates with fix loops.** Phase transitions are gated on machine-checkable pass criteria (ERC=0, DRC=0, custom checks pass, DFM pass). Failures spawn fixer agents scoped to violation clusters, then re-run the gate. Bounded retries, then escalate to human.
5. **Optimize for working boards today.** KiCad 9/10, JLCPCB as default fab, LCSC as default parts source. No abstraction layers for hypothetical future EDA tools or fabs.

---

## 1. Toolchain (research findings and choices)

| Function | Tool | Rationale / notes |
|---|---|---|
| EDA core | **KiCad 9.0.x** (10.x acceptable) | kicad-cli covers DRC/ERC/exports; IPC API stable from 9.0 |
| Headless exports, ERC, DRC, renders | **kicad-cli** | `sch erc`, `pcb drc` (JSON output, `--exit-code-violations`, `--all-track-errors`, `--schematic-parity`), gerbers, drill, pos, STEP, `pcb render` (PNG raytrace — feeds vision review). Newer versions add `drc --refill-zones --save-board` (headless zone refill); on 9.0 refill zones via IPC/SWIG script instead — verify at implementation time. |
| Live board manipulation | **kicad-python (kipy)** over the IPC API | Official bindings; supports `headless=True` which starts a `kicad-cli api-server` — no GUI needed. Used for placement/routing edits, zone refill, interactive fix loops. |
| Static file manipulation | **kiutils / raw s-expression parsing** | `.kicad_pcb` and `.kicad_sch` are s-expr text; deterministic checks parse files directly (no KiCad process needed). Zone fill polygons are stored in the file after refill, enabling geometric analysis with shapely. |
| Schematic generation | **kicad-sch-api** (circuit-synth) primary; **SKiDL** as netlist-level fallback | kicad-sch-api writes valid `.kicad_sch` with format preservation, pin-position queries, wires/labels/hierarchy — purpose-built for programmatic generation. SKiDL is mature for netlist+ERC but weak at schematic drawing. |
| Autorouting | **Freerouting 2.2.x CLI** (jar or Docker `ghcr.io/freerouting/freerouting`) | DSN in → SES out, fully headless, net-class ignore lists, pass limits, scoring metrics. DSN export reimplemented in Python (jharris2268 `kicad-freerouting-plugin-alt` approach) so no GUI export step. Known gap: Freerouting's internal clearance DRC is looser than KiCad's — **always** re-run kicad-cli DRC after SES import. |
| Assisted routing / plane hygiene | **KiCadRoutingTools** (drandyhaas) | Deterministic scripts for power routing, diff pairs, GND stitching vias with rise-time-derived spacing, and disconnected-plane-region detection/repair. Vendor these scripts or depend on the repo. |
| Layout/EMC analyzers | **kicad-happy** (aklofas) analyzers as a library of checks | Existing deterministic checks: return-path continuity, plane-void crossings, diff-pair skew, decoupling proximity, trace width vs. current, PDN impedance, thermal estimation, fab release gate. Validated on a 5,800+ project corpus. Reuse what passes evaluation; write our own where scope or quality is insufficient (§6.3). |
| Placement | **Custom SA placer with routability feedback** (§P6); no adequate off-the-shelf open-source option exists | Benchmarked evidence (pyplacer vs. Quilter, Apr 2026, 161-net board): naive SA placement → 93.8% Freerouting completion; commercial placement → 99.4%. Freerouting quality is placement-limited, so placement gets the largest custom-engineering investment in this skill. OpenROAD SA-PCB exists but is Eagle/Bookshelf-oriented and unmaintained; a ~2 kLOC Python SA placer is demonstrated feasible. |
| Parts data | **JLCPCB Parts API** (specs, stock, pricing — part of the official API program) with jlcparts-style cached SQLite fallback; **easyeda2kicad** (`--full --lcsc_id=Cxxxx`) for symbols/footprints/3D | Guarantees orderable, in-stock parts with JLC basic/extended classification (basic = no feeder fee). |
| BOM/CPL fab formatting | **kicad-jlcpcb-tools** conventions (not the GUI plugin) | Replicate its output format: gerber zip, BOM CSV with LCSC field, CPL with rotation-correction table (JLC rotation offsets are a known footgun — vendor the rotation DB). |
| DFM | Local rule engine (gerbonara/pcb-tools parsing + JLC capability table) + **jlcdfm.com** upload as second opinion | JLCDFM: 30+ checks across traces/mask/drill/silk/assembly, PDF report. No public API — browser step or human upload. Local engine catches the big classes pre-upload. |
| Ordering | **JLCPCB official API** (api.jlcpcb.com — requires access application). Confirmed scope: gerber upload, automated pricing, PCB order creation, production tracking, stencil orders, Parts API. Fallback: upload-ready package + deep link for manual submission | Payment is always a human gate regardless of path. |
| Datasheets | LCSC datasheet URLs + web fetch; PDF extraction scripts | Structured extraction of pinout, land pattern, decoupling requirements, layout guidelines into per-part JSON. |

### 1.1 Alternatives weighed and rejected (or partially adopted)

**atopile (v0.15, actively developed).** Declarative `.ato` language + compiler: constraint solving, automatic parametric part picking, reusable modules with attached KiCad layouts (registry pull), native `.kicad_pcb` updates, LSP/editor tooling. Strongest existing code-to-board toolchain, and field reports show LLMs write `.ato` competently. **Rejected as backbone** for one decisive reason: it produces no KiCad schematic, so human checkpoint 2 (schematic review — the highest-leverage EE review artifact) degrades to netlist/code review. Secondary reasons: a DSL between the model and the file adds an abstraction the orchestrator can't reach through when things break, and layout reuse from a small module registry rarely covers custom designs. **Adopted from it:** the parametric part-picking pattern (constraints → LCSC query → pick) implemented in `parts_search.py`, and its maintained `easyeda2kicad` fork as the library-pull dependency.

**tscircuit.** React-style web-native board definition with autorouting integration. Not evaluated in depth this round (flagged, not researched to conclusion); its web-platform orientation and non-KiCad-native format make it a poor fit for a local, KiCad-centered, script-verified flow regardless.

**SKiDL as design-capture backbone.** Mature netlist generation + ERC, but schematic drawing is limited to KiCad 5 format — same schematic-review problem as atopile. Retained only as a fallback netlist path.

**Commercial placement/routing services (Quilter, DeepPCB, AutoCuro).** Quilter demonstrably produces near-hand-quality placement (99.4% routability benchmark above). Rejected as dependencies: closed, upload-based, priced per design, and they collapse exactly the placement/routing layer this skill needs to control and verify. The benchmark is instead used as the quality bar for our own placer.

**kicad-happy as the whole pipeline.** It covers analysis, sourcing, and fab-prep of *human-created* designs; it does not generate schematics or layouts. Complementary, not competing — its analyzers are the strongest existing open implementations of several §6.3 checks.

**Environment:** Linux or macOS. Dependencies: KiCad ≥ 9.0.5, Python 3.11+ venv with `kicad-python kiutils kicad-sch-api skidl shapely numpy gerbonara sexpdata`, Java 21+ or Docker for Freerouting, `easyeda2kicad`. `scripts/check_env.py` validates all of this and prints remediation steps; the orchestrator runs it first.

---

## 2. Skill layout

```
.claude/skills/ai-ee/
├── SKILL.md                     # orchestrator playbook (the "soft top")
├── commands/ai-ee.md            # /ai-ee slash command → loads SKILL.md, starts Phase 0
├── agents/                      # subagent role prompts (markdown, one per role)
│   ├── requirements-analyst.md
│   ├── research-*.md            # component-scout, reference-design, interface-spec, power-architect
│   ├── architect.md
│   ├── part-sourcer.md
│   ├── librarian.md
│   ├── schematic-block.md       # instantiated once per hierarchical sheet
│   ├── schematic-reviewer.md    # adversarial
│   ├── board-setup.md
│   ├── placement.md
│   ├── router.md
│   ├── verify-reviewer.md       # adversarial, consumes renders + check reports
│   ├── fixer.md                 # generic, instantiated per violation cluster
│   ├── dfm.md
│   └── ordering.md
├── scripts/                     # deterministic core (the "firm bottom") — §6
├── reference/
│   ├── jlc_capabilities.yaml    # fab rule tables per layer count / copper weight
│   ├── jlc_rotations.csv        # CPL rotation corrections
│   ├── stackups.yaml            # JLC standard stackups w/ impedance data (JLC06161H-3313 etc.)
│   ├── design_rules/            # .kicad_dru templates per board class
│   └── checklists/              # per-domain review checklists (power, RF, MCU, USB, ...)
└── templates/                   # blank .kicad_pro/.kicad_sch/.kicad_pcb, title blocks
```

Each design run creates a project workspace:

```
<board-name>/
├── brief/            # user inputs, uploaded docs
├── state.json        # single source of truth for pipeline state (§4)
├── requirements.md   # Phase 0 output, human-approved
├── architecture/     # block diagram (mermaid+md), power tree, stackup decision, interface budget
├── research/         # per-topic research reports (md + json)
├── parts/            # parts.json (BOM-of-record), per-part datasheet-extract JSON, datasheet PDFs
├── lib/              # project symbol/footprint/3D libs pulled via easyeda2kicad
├── kicad/            # <name>.kicad_pro / .kicad_sch (hierarchical) / .kicad_pcb / .kicad_dru
├── routing/          # DSN/SES files, freerouting logs & scores
├── reports/          # erc.json, drc.json, checks/*.json, renders/*.png, review-*.md
├── fab/              # gerber zip, BOM.csv, CPL.csv, dfm-report, order manifest
└── log/              # per-agent transcripts summaries, gate history
```

---

## 3. Pipeline

Phases are **firm** (fixed sequence, defined entry/exit gates). Within each phase, the orchestrator decides **which** agents to spawn, how many, and with what emphasis — that set is derived from the design's domains (an RF PA board spawns different research/review agents than a USB-C dev board).

```
P0 Intake ─ P1 Research ─ P2 Architecture ─[H]─ P3 Parts+Library ─ P4 Schematic ─[G:ERC,H]─
P5 Board Setup ─ P6 Placement ─[G:overlap,H-opt]─ P7 Routing ─[G:100% routed, DRC=0]─
P8 Verification ─[G:checks]─ P9 DFM+Fab Outputs ─[G:DFM]─ P10 Ordering ─[H:pay]
[G] = machine gate   [H] = human checkpoint
```

### P0 — Intake
Orchestrator (no subagents yet): copy inputs to `brief/`, run `check_env.py`, then spawn **requirements-analyst** to produce `requirements.md`: function, interfaces, power budget, environment, size/mounting constraints, quantity, budget, assembly (JLC PCBA vs. hand solder), and **explicit unknowns as questions**. Orchestrator asks the user the questions in one batch (never trickle). Nothing proceeds on guessed requirements for safety-relevant items (mains, batteries, high current).

### P1 — Research (parallel)
Orchestrator selects research agents based on `requirements.md`. Standard roster (spawn only what applies):
- **component-scout** (per major function): candidate ICs, filtered by LCSC stock/price via `parts_search.py`, output ranked table with rationale.
- **reference-design**: finds vendor reference designs / hackable open-source boards for each major block; extracts topology decisions, not files.
- **interface-spec**: per high-speed or standards-bound interface (USB, Ethernet, RF), extracts layout constraints — impedance targets, max skew, spacing, connector pinouts — into `research/constraints.json` (machine-readable; consumed by P5 rule generation and P8 checks).
- **power-architect**: input range → rail tree, topology per rail (LDO vs buck), efficiency/thermal first pass.

Each writes `research/<topic>.md` + structured JSON, returns ≤10-line summary. Orchestrator reads summaries only.

### P2 — Architecture
**architect** agent consumes research JSONs + requirements → `architecture/`:
- Block diagram (mermaid) with signal + power flow
- Power tree with per-rail current budgets
- Stackup selection from `reference/stackups.yaml` (layer count, controlled-impedance geometry from JLC's published stackup data)
- Hierarchical sheet plan: named blocks with their nets/interfaces — this becomes the schematic sheet structure and later the placement grouping
- `architecture/constraints.json`: merged, resolved constraint set (net classes, impedance targets, current-carrying nets with amps, diff pairs, guarded nets)

**Human checkpoint 1:** user approves architecture. Cheapest place to change direction.

### P3 — Parts & Library
- **part-sourcer**: turns every block into exact orderable MPNs. Rules: prefer JLC *basic* parts for passives; check stock ≥ 5× build qty; verify package hand-solderability if not PCBA; pin-compatible alternate for every single-source IC. Output `parts/parts.json`: `{ref_prefix_hint, mpn, lcsc, value, package, basic/extended, stock, price, alternates[]}`.
- **librarian**: for each part, pull symbol/footprint/3D via `lib_pull.py` (easyeda2kicad wrapper) into `lib/`, register in project lib tables. **Footprint verification is mandatory** (top-3 real-world failure mode): `fp_verify.py` renders the footprint to SVG with dimensions and diffs pad pitch/size/count against the datasheet land pattern extracted by the datasheet agent; mismatches are human-flagged with side-by-side images. Pin-1 marking and polarity indicators checked.
- **datasheet-extractor** (one per nontrivial IC, parallel): PDF → `parts/<lcsc>.json` with pinout (pin/name/type), decoupling requirements, exposed-pad rules, layout notes, absolute maximums. This JSON is the ground truth the schematic agents wire against — never wire from model memory of a pinout.

### P4 — Schematic
One **schematic-block** agent per hierarchical sheet (parallel where independent). Each agent:
1. Writes a small generator script `kicad/gen/<sheet>.py` using kicad-sch-api (script-generated schematic = reviewable, re-runnable, diffable — the schematic *source* is the Python, the `.kicad_sch` is build output).
2. Uses only pins from the datasheet-extract JSON; unconnected input pins are an error, not a warning.
3. Standard idioms enforced by shared helpers in `scripts/schlib.py`: decoupling cap per power pin (value from datasheet JSON), power flags, test points on rails and key signals, hierarchical labels matching `architecture` interface names, no-connect flags explicit.
Top-sheet agent stitches sheets. Then:
- Gate: `kicad-cli sch erc --format json --exit-code-violations` must be clean (exclusions require written justification in `reports/erc-waivers.md`).
- `netlist_audit.py`: cross-check generated netlist against `architecture/constraints.json` (every declared interface net exists, diff pairs named `_P/_N`, power tree connectivity matches).
- **schematic-reviewer** (adversarial, fresh context): reviews rendered schematic PDFs (`kicad-cli sch export pdf`) + netlist against per-domain checklists in `reference/checklists/` (e.g., buck: bootstrap cap, feedback divider Kelvin point, catch diode/synchronous config; USB: CC resistors, ESD, shield strategy). Findings → fixer agents → re-gate.

**Human checkpoint 2:** user reviews schematic PDF. Blocking.

### P5 — Board Setup
**board-setup** agent, entirely script-driven:
- `board_init.py`: create `.kicad_pcb` from template, import netlist, set stackup from `stackups.yaml`, board outline from mechanical constraints (or auto-size after placement estimate), mounting holes, origin/grids.
- `rules_gen.py`: generate `.kicad_dru` + net classes from `constraints.json`: clearances, track widths (per-current via IPC-2152 approximation for power nets), via definitions, diff-pair gap/width from stackup impedance table, keepouts (antenna, mounting), courtyard rules. KiCad custom DRC rules are the enforcement backbone — anything expressible as a rule becomes one so the standard DRC gate carries it for free.

### P6 — Placement
Placement receives the largest engineering investment in the pipeline: benchmark evidence shows autorouter completion is placement-limited (93.8% vs. 99.4% routability between naive-SA and commercial placement on the same board), and every downstream check depends on it. Three stages:

1. **Structured seed** — `place_seed.py`: hard constraints first (connectors on declared edges, mounting holes, mechanical keepouts, antenna zones), then hierarchical-sheet groups arranged by block-diagram adjacency. Satellites locked to parents as rigid clusters: decouplers at their IC power pins (pin association known from schematic generation), crystal + load caps, feedback dividers, bulk caps at regulators. Clusters, not individual parts, are the placement unit.
2. **SA refinement with routability in the loop** — `place_anneal.py`: simulated annealing over cluster positions/rotations. Cost = HPWL + courtyard-overlap penalty + grid congestion + net-crossing estimate + rule terms (analog/digital separation, thermal spreading, high-current path length). Periodically (every k accepted-move epochs) run a fast Freerouting pass (low effort, capped passes) on a snapshot and blend **actual routing completion %** into the cost — this closes the specific gap the benchmark identified between naive SA and commercial placers. Deterministic given a seed; emits `place_metrics.json` per candidate; keeps top-N candidates.
3. **Agent selection + repair** — **placement** agent reviews top-N candidates via metrics + `kicad-cli pcb render` top/bottom PNGs, picks one, and issues targeted group/ref move-rotate operations through `place_edit.py` (IPC headless; never raw file edits) for concerns the cost function can't express (connector ergonomics, silkscreen real estate, assembly access). Budget: 8 edit iterations.

Gate: zero courtyard overlaps, connectors on declared edges, decoupler distance ≤ per-part limit, fast-route completion ≥ 98%. Optional human look at the render.

### P7 — Routing
Ordered, mostly deterministic:
1. **Critical nets first, by script** (`route_critical.py`, built on KiCadRoutingTools primitives): diff pairs (impedance geometry from stackup, skew-matched), high-current power (width from current table, or copper pours), RF nets (CPWG geometry, via fencing), sensitive analog. The **router** agent decides *ordering and strategy* per net from `constraints.json`; scripts execute.
2. **Plane pours**: `planes_gen.py` — GND pours on designated layers, power pours/islands per power tree, thermal vias under exposed pads, refill.
3. **Freerouting for the remainder**: `route_auto.py` → export DSN with critical nets + pours locked/fixed and GND/power net classes excluded → Freerouting CLI (pass limit, score logging) → import SES → refill zones. DSN export is not in kicad-cli; two viable paths, decided at implementation: (a) SWIG `pcbnew` Specctra export call (present in KiCad 9/10, removed in 11 — acceptable per the "works now" mandate), (b) vendored pure-Python DSN writer (the kicad-freerouting-plugin-alt approach). SES import likewise via SWIG or Python parser.
4. **Post-route hygiene**: `stitch_vias.py` (GND stitching at rise-time-derived pitch), `plane_repair.py` (detect plane regions split by routing; repair or flag), `route_cleanup.py` (remove loops, 90° corner smoothing).
5. Gate: 100% nets routed (`kicad-cli pcb drc --schematic-parity --all-track-errors`, DRC = 0). Unroutable nets after N freerouting retries with escalating via cost/pass settings → router agent re-strategizes (layer reassignment, placement micro-adjust request back to P6 for the affected group — the only sanctioned backward edge in the pipeline).

### P8 — Verification (the differentiator)
All deterministic checks run from `verify_all.py` (parallel, each emits `reports/checks/<name>.json` with pass/fail + violation coordinates):

| Check | Method (see §6.3) |
|---|---|
| Return path continuity | Geometric: trace vs. reference-plane polygon analysis per high-speed net |
| Return via at layer transitions | Signal via → same-net-reference or GND via within rise-time-derived radius |
| Plane splits / voids under critical nets | Zone polygon subtraction, void-crossing detection |
| Decoupling proximity + via inductance | Cap pad → IC power pin distance and via count on the loop |
| Trace width vs. current | IPC-2152 approximation per power net segment |
| Diff pair skew & gap consistency | Segment-level length + spacing extraction |
| PDN sanity | Bulk+ceramic per rail vs. power tree; plane connection widths |
| Thermal | Dissipation estimate per regulator/FET vs. copper area + via count |
| Creepage/clearance | For >30 V nets, IPC-2221 spacing on same layer |
| Silkscreen/assembly | Ref-des legibility, polarity marks, pin-1, silk-over-pad |
| Fab release gate | All nets routed, BOM complete (every ref has LCSC), gerber layer completeness, drill validity |

Then **verify-reviewer** (adversarial, fresh context): consumes check JSONs + renders (top/bottom/angled via `pcb render`) + schematic PDF, hunts for what scripts can't see (blocked antenna keepout, connector orientation absurdity, EMI-hostile aesthetics). Findings triaged by orchestrator → fixer agents → re-run `verify_all.py`. Loop until clean or human-waived.

### P9 — DFM & Fab Outputs
**dfm** agent:
- `fab_export.py`: gerbers + drill (JLC settings: Protel extensions off/X2 per current JLC guidance, mask/paste layers, edge cuts), pos file, `fab/BOM.csv` + `fab/CPL.csv` in JLC format with rotation corrections from `reference/jlc_rotations.csv`, gerber zip.
- `dfm_check.py`: gerber-level checks against `jlc_capabilities.yaml` (min trace/space for copper weight, min drill, annular ring, hole-to-hole, copper-to-edge, mask sliver, silk width) using gerbonara. This is a second, independent geometry path — it catches export-stage errors DRC can't.
- JLCDFM upload for the fab's own 30+ checks (no public API: agent prepares the zip and either drives a browser if available or instructs the human; report findings folded back into fix loop).
- Gate: local DFM clean; JLCDFM no errors (warnings reviewed).

### P10 — Ordering
**ordering** agent: quote matrix (qty × surface finish × solder-mask color × assembly), lead times; assemble order manifest. If JLCPCB API credentials configured, place the order via API up to the payment step. **Payment/final submission is always human.** Post-order: write `fab/order.json` (order number, spec snapshot, gerber hash) for traceability.

---

## 4. Orchestration mechanics

**Orchestrator = the `/ai-ee` session.** Its context budget is protected ruthlessly:
- It never opens design files. It reads `state.json`, agent summaries (≤10 lines each), and gate results.
- Every spawn is a Task-tool subagent with: role prompt from `agents/`, the specific file paths it needs, its output contract, and its termination condition. Nothing else.
- Any agent needing an edit outside its primary task spawns its own sub-agent for it (e.g., the router agent needing a footprint fix delegates to a librarian sub-agent).
- After each phase the orchestrator writes a phase digest to `log/` and may **compact or restart itself**: `state.json` + digests are sufficient to resume `/ai-ee --resume <dir>` from any gate. This makes context rot survivable, not just mitigated.

**state.json (schema sketch):**
```json
{
  "board": "rf-amp-ctrl", "phase": "P7", "gates": {"P4": {"erc": 0, "human": "approved@..."}},
  "artifacts": {"schematic": "kicad/x.kicad_sch", "pcb": "...", "constraints": "..."},
  "open_issues": [{"id": 41, "src": "check.return_path", "net": "SPI_CLK", "status": "fixing", "agent": "fixer-7"}],
  "budgets": {"fix_loops_P8": 3, "freerouting_retries": 2},
  "decisions": [{"what": "4-layer JLC06161H-3313", "why": "USB HS + buck", "phase": "P2"}]
}
```

**Fix-loop protocol (uniform across gates):** gate fails → orchestrator clusters violations (by net/region/type via `cluster_violations.py`) → one fixer agent per cluster, in parallel where regions don't overlap → fixers edit via scripts/IPC only → re-run the gate. Max N loops (per-gate budget), then escalate to the human with a rendered, annotated summary. Fixers must not expand scope: a fixer for a clearance cluster may not "improve" unrelated routing.

**Concurrency & consistency:** the `.kicad_pcb` is single-writer. Parallel fixers on the same board file are serialized by the orchestrator unless they operate on disjoint scripted operations queued through `place_edit.py`/`route_edit.py` (which apply an operation list atomically). Git commit after every gate pass — rollback is `git checkout`.

---

## 5. Agent design rules (applies to every `agents/*.md`)

1. **One job.** Stated in the first line of the role prompt. Anything else → delegate or return.
2. **Script-first.** The prompt lists the scripts the agent is allowed to use and the order of preference. Manual file editing is a last resort and must be flagged in the summary.
3. **Grounding.** Wiring/pinout facts come only from `parts/<lcsc>.json` or datasheet PDFs on disk. Constraints come only from `constraints.json`. Prompts explicitly forbid recalling pinouts or footprint dimensions from memory.
4. **Output contract.** Every agent ends with: files written (paths), gate-relevant results, ≤10-line summary, open questions. Orchestrator parses only this.
5. **Fresh eyes for review.** Reviewer agents never share context with the agents whose work they review, and their prompts frame the task adversarially ("find the reason this board fails bring-up").
6. **Determinism budget.** If an agent finds itself making the same class of judgment call repeatedly, it should propose (in its summary) a new script for `scripts/` — the skill accretes determinism over time.

---

## 6. Script inventory (I/O contracts)

All scripts: Python, argparse, JSON to stdout or `--out <file>`, exit 0/1/2 (pass / violations / error), no interactivity. Shared geometry lib `scripts/lib/geom.py` (s-expr parse → shapely primitives per layer, net-indexed).

### 6.1 Infrastructure
- `check_env.py` — validate KiCad/Java/Python deps, versions, lib paths.
- `parts_search.py --query|--filters` — LCSC/JLC search (cached DB + live), returns ranked JSON with stock/price/basic-flag.
- `lib_pull.py --lcsc Cxxxx` — easyeda2kicad wrapper; registers in project lib tables.
- `fp_verify.py --footprint <fp> --datasheet-json <json>` — pad geometry diff vs. land pattern; emits SVG overlay.
- `datasheet_extract.py --pdf <f>` — pinout/decoupling/layout-notes extraction (LLM-assisted via a dedicated sub-agent, but schema-validated output).

### 6.2 Generation
- `schlib.py` — kicad-sch-api helpers: `place_ic_with_decoupling()`, `power_flag()`, `hier_pin()`, auto-wire by pin position.
- `board_init.py`, `rules_gen.py` — §P5.
- `place_seed.py`, `place_anneal.py --seed N --candidates M [--route-feedback]`, `place_metrics.py`, `place_edit.py --ops ops.json` — §P6. The annealer is the single largest script (~2 kLOC class); it gets its own test corpus of placement problems with known-achievable routability.
- `planes_gen.py`, `route_critical.py`, `route_auto.py`, `stitch_vias.py`, `plane_repair.py`, `route_cleanup.py`, `route_edit.py` — §P7.
- `render.py --views top,bottom,iso --w 2400` — kicad-cli render wrapper, consistent naming for VLM review.

### 6.3 Verification (the crown jewels — specified precisely)

**`check_return_path.py`** — per net in `constraints.json[high_speed]`:
1. Extract net's track segments per layer; determine each segment's reference layer(s) from the stackup (adjacent plane(s); microstrip = one, stripline = two).
2. Load the reference layer's filled-zone polygons for the reference net (GND unless specified).
3. Buffer the trace centerline by `k × trace_width` (k default 3, ~return-current spread) → corridor polygon. Violation if corridor ∩ (plane voids ∪ zone gaps ∪ other-net copper on the ref layer) ≠ ∅, i.e., the return corridor is not fully contained in continuous reference copper.
4. At every layer transition of the net: if reference plane changes net or side, require a same-reference-net via (or stitching cap for different DC nets) within radius r = c/(f_knee × 20) per rise time in constraints (default 2 mm). 
5. Output: per-net pass/fail, violation polygons with coordinates + layer, severity by crossing length.

**`check_decoupling.py`** — from schematic gen metadata (cap↔pin association): Manhattan distance pad-to-pin, number and length of vias in the loop, loop-inductance estimate (via ≈1 nH heuristic + trace inductance); thresholds per cap value class.

**`check_current.py`** — per power net: min copper cross-section along the path (track width × copper weight, pour neckdowns via polygon medial-axis min-width), vs. IPC-2152 external/internal curves for the rail's budgeted current at ΔT=10 °C. Via count check for layer transitions (≥1 via per 0.5 A default).

**`check_diffpair.py`** — pair matching by `_P/_N`: intra-pair skew (mm and ps via stackup εr), gap deviation histogram, uncoupled-length total, symmetry of vias.

**`check_creepage.py`**, **`check_thermal.py`**, **`check_silk.py`**, **`check_pdn.py`** — per §P8 table; each ≤300 lines, one concern.

**`verify_all.py`** — runs the suite in parallel, merges to `reports/checks/summary.json`.
**`cluster_violations.py`** — groups all open violations by (region, net, type) for fixer dispatch.

Where a kicad-happy analyzer already implements a check well, wrap it rather than rewrite — but every wrapped check gets a golden-board regression test in our own repo (below), so its behavior is pinned.

### 6.4 Fab
- `fab_export.py`, `dfm_check.py`, `bom_cpl.py`, `order_quote.py`, `order_submit.py` (API path, stops before payment).

### 6.5 Test fixtures
`tests/golden/` — 3 known-good reference boards (2-layer MCU, 4-layer USB+buck, 4-layer RF) and mutated known-bad variants (plane split under a clock, missing return via, undersized power trace, wrong-rotation CPL). CI: every check script must flag every seeded defect and pass every golden board. This is what makes the "firm bottom" trustworthy.

---

## 7. Human checkpoints (fixed)

| # | After | Blocking | Content |
|---|---|---|---|
| 1 | P2 | yes | Architecture: blocks, stackup, cost estimate, key part choices |
| 2 | P4 | yes | Schematic PDF + reviewer findings + waivers |
| 3 | P6 | optional (on by default) | Placement render |
| 4 | P8 | yes | Verification summary + annotated renders + any waivers |
| 5 | P10 | yes, always | Order review + payment |

Everything else is autonomous. Checkpoints present a digest + render, never raw logs.

---

## 8. Implementation plan for Claude Code (build order)

Milestones below give the dependency logic; the session-by-session execution breakdown (one self-contained brief per Claude Code session, with acceptance tests) is in the companion document `ai-ee-implementation-plan.md`.

**M1 — Spine (build first, end-to-end on a trivial board):** skill skeleton, `check_env.py`, state machine, P0/P5 templates, `board_init.py`, `rules_gen.py`, `fab_export.py`, ERC/DRC gate wrappers. Milestone test: hand-written schematic → gerbers, fully headless.

**M2 — Schematic generation:** `schlib.py`, schematic-block + reviewer agents, `netlist_audit.py`, datasheet extraction, `fp_verify.py`, `lib_pull.py`. Milestone: brief → ERC-clean hierarchical schematic for the 2-layer golden board.

**M3 — Placement & routing:** `place_seed.py` + metrics + IPC edit loop; DSN exporter + Freerouting integration; `route_critical.py`, `planes_gen.py`, plane repair, stitching. Milestone: golden board 2 routes to DRC=0 unattended.

**M4 — Verification suite:** §6.3 scripts + golden/mutant test corpus + verify-reviewer + fix-loop machinery. Milestone: all seeded defects caught; fixers clear them autonomously.

**M5 — Research/architecture front-end + DFM/ordering back-end:** research agents, architect, part-sourcer, `dfm_check.py`, BOM/CPL, quote/order. Milestone: `/ai-ee "USB-C powered dual-channel RF power monitor"` → order-ready package with ≤5 human interactions.

Build M1–M3 against golden board 1 before touching M4/M5 breadth. Each milestone lands with its regression tests; the skill's SKILL.md is updated last, once agent/scripts contracts are stable, so the orchestrator playbook documents reality rather than intent.

---

## 9. Known limits (stated, not hidden)

- Freerouting output quality is placement-limited (benchmarked); this design compensates with the routability-in-the-loop annealer and by scripting critical nets first. Expect the router agent + fixers to do real work on ≥4-layer dense boards regardless.
- No field solver: impedance comes from fab stackup tables, SI checks are geometric/heuristic. Adequate through USB HS / 100 MHz-class SPI / sub-GHz RF with discipline; not a substitute for simulation on multi-GHz serdes. openEMS integration is a possible later phase, deliberately out of scope now.
- JLCDFM has no API; that step is semi-manual.
- kicad-sch-api officially validates output against KiCad 7/8 format; KiCad 9/10 open older formats natively and KiCad 10 provides `kicad-cli sch upgrade`. Verify round-trip at the start of the schematic milestone.
- DSN export/SES import rely on either SWIG bindings (deprecated, removed in KiCad 11) or a vendored Python implementation — both flagged verify-at-implementation; the pipeline is pinned to KiCad 9/10 either way.
- Schematic-side IPC API coverage is still limited in KiCad 9; schematic work is file-based by design.
- Facts in this spec taken from vendor docs/benchmarks are current as of July 2026; anything marked "verify at implementation" was not directly tested and must be smoke-tested in the target environment before being built upon.
