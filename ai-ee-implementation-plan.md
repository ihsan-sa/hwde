# ai-ee — Implementation Plan (session-sized steps)

Companion to `ai-ee-spec.md`. Each step is scoped to one fresh Claude Code session to keep context clean. Kick off each with: `Implement Step N of ai-ee-implementation-plan.md. Read only the files listed under "Read" for that step, plus PROGRESS.md.`

## Conventions (apply to every session)

- Repo root contains `SPEC.md` (the spec), this plan, and `PROGRESS.md`.
- **Session start:** read `PROGRESS.md`, this step's entry, and the listed spec sections. Nothing else unless blocked.
- **Session end:** all acceptance tests pass in CI (`pytest` + step-specific commands); update `PROGRESS.md` with: step status, deviations from spec (with reason), new "verify-later" items, interface changes affecting later steps. Commit.
- **Verify-at-implementation items:** the spec flags several unverified claims (DSN export path, kicad-sch-api KiCad 9 round-trip, `drc --refill-zones` on 9.0, IPC headless mode behavior). The step that first touches each one begins with a smoke test; if the claim fails, record the working alternative in `PROGRESS.md` before building on it.
- **Delegation:** within a session, delegate bulk file edits and boilerplate to subagents; keep the session's own context for design decisions and test debugging.
- Scripts follow the spec §6 contract: argparse, JSON out, exit 0/1/2, no interactivity.

## Dependency graph

```
S0 → S1 → S2 → S3 → {S4, S5}          (verification track)
S0 → S6 → S7                           (schematic track)
S2 → S8 → S9 → S10 → S11               (board track; S11 needs S2 DSN smoke test)
{S5, S7, S8, S11} → S12 → S13 → S14
```
S4–S7 can run in parallel with S8–S10 across different sessions if desired.

---

### S0 — Repo bootstrap and environment
**Read:** spec §1 (toolchain, environment), §2 (layout).
**Build:** skill directory skeleton per §2; Python venv + pinned deps; `scripts/check_env.py` (KiCad ≥ 9.0.5 present, kicad-cli on PATH, IPC deps, Java/Docker for Freerouting, easyeda2kicad); CI harness (pytest + a `make check` entry point); empty `PROGRESS.md` template.
**Smoke tests (record results):** `kicad-cli version`; `kicad-cli pcb render` availability; IPC headless (`kipy` with `headless=True`) connects and reads a trivial board; `kicad-cli pcb drc --refill-zones` flag presence.
**Accept:** `check_env.py` exits 0 on the dev machine and prints actionable remediation when a dep is removed; smoke-test results recorded in PROGRESS.md.

### S1 — Golden board corpus
**Read:** spec §6.5.
**Build:** `tests/golden/` with three boards: (1) 2-layer STM32 blinky-class, (2) 4-layer USB-FS + buck, (3) 4-layer sub-GHz RF front end. Source from permissively-licensed open designs or draw minimally; each must be ERC/DRC-clean in KiCad 9 with zones filled and saved. Then generate mutant variants via small scripts (not hand edits, so mutations are reproducible): plane split under a clock trace, missing return via at a layer transition, undersized power trace, decoupler moved 15 mm from its pin, diff-pair skew, silk-over-pad, CPL rotation error. Manifest `tests/golden/manifest.yaml` mapping each mutant → the check that must catch it.
**Accept:** golden boards pass `kicad-cli sch erc` / `pcb drc` clean; mutation scripts run deterministically; manifest complete.

### S2 — kicad-cli wrappers and gate infrastructure
**Read:** spec §3 (gate concept), §6.1, §6.2 (`render.py`).
**Build:** thin wrappers `scripts/kc.py` (erc, drc, gerbers, drill, pos, step, render, sch-pdf, netlist) normalizing JSON reports into one violation schema `{check, severity, pos, layer, net, refs, msg}`; `scripts/gate.py --gate <name>` evaluating pass criteria from a `gates.yaml`; git-commit-on-gate-pass helper.
**Accept:** wrappers produce normalized JSON for all three golden boards; a seeded DRC violation fails `gate.py` with exit 1 and correct coordinates.

### S3 — Geometry library
**Read:** spec §6 intro, §6.3 headers.
**Build:** `scripts/lib/geom.py`: parse `.kicad_pcb` s-expressions → per-layer, net-indexed shapely geometry (tracks as buffered polylines, pads, vias, zone fill polygons, board outline); stackup model (layer order, dielectric heights, εr from board file); unit handling; caching. Include zone-fill freshness detection (refuse to run on stale/unfilled zones; trigger refill via IPC or the S0-verified path).
**Accept:** round-trip sanity on golden boards (copper area per net within tolerance of KiCad's report); documented API used by S4/S5; performance <5 s parse on the largest golden board.

### S4 — Verification suite, part 1 (the crown jewels)
**Read:** spec §6.3 in full (algorithms are specified there), §P8 table.
**Build:** `check_return_path.py`, `check_decoupling.py`, `check_current.py` exactly per spec algorithms, on `geom.py`. Evaluate kicad-happy's corresponding analyzers first (one subagent, timeboxed): wrap if correct on our mutants, else implement fresh. Either way the mutant corpus is the arbiter.
**Accept:** every relevant S1 mutant caught with correct net + coordinates; zero false positives on the three golden boards; each check <30 s on the RF board.

### S5 — Verification suite, part 2 + orchestration of checks
**Read:** spec §6.3 remainder, §P8, §4 (fix-loop protocol).
**Build:** `check_diffpair.py`, `check_creepage.py`, `check_thermal.py`, `check_silk.py`, `check_pdn.py`; `verify_all.py` (parallel runner, merged summary); `cluster_violations.py` (group by region/net/type for fixer dispatch).
**Accept:** full mutant manifest coverage — every mutant caught by its designated check, goldens clean; `verify_all.py` summary schema stable and documented.

### S6 — Parts, library, datasheet tooling
**Read:** spec §P3, §6.1.
**Build:** `parts_search.py` (JLCPCB Parts API if credentialed, cached jlcparts SQLite fallback, web-search last resort; parametric filters; basic/extended + stock in output); `lib_pull.py` (easyeda2kicad wrapper + project lib-table registration); `datasheet_extract.py` (PDF → schema-validated pinout/decoupling/land-pattern JSON; LLM-assisted extraction is acceptable here but output must validate against the JSON schema); `fp_verify.py` (footprint pad geometry vs. land-pattern JSON, SVG overlay diff).
**Accept:** for 5 test parts (MCU, buck, USB connector, crystal, 0603 R): search returns in-stock LCSC hits; pulled footprints load in KiCad; `fp_verify.py` flags a deliberately corrupted footprint and passes correct ones; datasheet JSON validates.

### S7 — Schematic generation
**Read:** spec §P4, §6.2 (`schlib.py`), §5 (grounding rule).
**Smoke test first:** kicad-sch-api output opens clean in KiCad 9/10 (upgrade via `kicad-cli sch upgrade` if needed — KiCad 10). Record path chosen.
**Build:** `schlib.py` helpers (`place_ic_with_decoupling`, `power_flag`, `hier_pin`, auto-wire-by-pin-position, hierarchical sheet stitching); the generator-script pattern (`kicad/gen/<sheet>.py` is source, `.kicad_sch` is build output); `netlist_audit.py` (netlist vs. constraints.json: interfaces exist, `_P/_N` pairing, power-tree connectivity); decoupler↔pin association metadata emitted for S4's `check_decoupling.py` and S9 clustering.
**Accept:** regenerate golden board 1's schematic from a generator script: ERC clean, netlist electrically identical to the original (same nets/pin memberships), audit passes.

### S8 — Board setup and reference data
**Read:** spec §P5, §2 (`reference/`).
**Build:** `reference/jlc_capabilities.yaml`, `reference/stackups.yaml` (JLC standard stackups with impedance geometries, from JLC published data — cite source URLs in the file), `reference/jlc_rotations.csv` (vendor from the maintained community table), `.kicad_dru` templates; `board_init.py` (project from template, netlist import, stackup, outline, mounting holes); `rules_gen.py` (constraints.json → net classes + custom DRC rules: clearance, widths from current table, via defs, diff-pair geometry, keepouts).
**Accept:** from golden board 2's netlist + a constraints.json: initialized board passes DRC setup checks; generated rules demonstrably enforced (a violating test track fails DRC with the custom rule named).

### S9 — Placement: seed, metrics, edit ops
**Read:** spec §P6 stages 1 and 3, §6.2.
**Build:** `place_seed.py` (hard constraints → clusters → block-adjacency arrangement; satellite locking uses S7's decoupler↔pin metadata); `place_metrics.py` (HPWL, crossings, congestion grid, decoupler distances, courtyard overlaps); `place_edit.py --ops` (atomic move/rotate op lists via IPC headless).
**Accept:** seed placement of golden board 2 from scratch: legal (no overlaps, connectors on edges), metrics JSON emitted; an op list applies and is idempotent on re-application failure (rollback).

### S10 — Placement: annealer with routability feedback
**Read:** spec §P6 stage 2, §1 placement row (benchmark context).
**Build:** `place_anneal.py`: SA over cluster positions/rotations; cost = HPWL + overlap + congestion + crossing + rule terms; adaptive temperature; deterministic per seed; top-N candidate output. Routability feedback mode: periodic capped-effort Freerouting pass on snapshots, completion % blended into cost (requires S11's DSN path — if built before S11, stub the feedback behind a flag and wire it in S11).
**Accept:** on golden board 2 stripped of placement: annealer beats seed placement by ≥20% HPWL; with feedback enabled, fast-route completion ≥98%; runtime <30 min on dev hardware; results reproducible per seed.

### S11 — Routing pipeline
**Read:** spec §P7 in full.
**Smoke test first:** DSN export — try SWIG `pcbnew` Specctra export; else vendor the Python DSN writer. Same for SES import. Record choice.
**Build:** `route_critical.py` (diff pairs, power, RF — evaluate KiCadRoutingTools primitives, wrap or vendor), `planes_gen.py`, `route_auto.py` (DSN → Freerouting CLI with net exclusions/locking → SES import → refill), `stitch_vias.py`, `plane_repair.py`, `route_cleanup.py`, `route_edit.py`. Freerouting retry ladder (escalating pass counts / via costs) and the sanctioned P7→P6 backward edge (placement micro-adjust request format).
**Accept:** golden board 1 and 2, from placed-unrouted: 100% routed, `kicad-cli pcb drc --schematic-parity --all-track-errors` = 0, plane-repair mutant fixed automatically, `verify_all.py` (S5) passes on the result.

### S12 — Fab outputs, DFM, ordering
**Read:** spec §P9, §P10, §6.4.
**Build:** `fab_export.py` (JLC-spec gerber/drill/pos), `bom_cpl.py` (JLC BOM/CPL format + rotation corrections), `dfm_check.py` (gerbonara-based checks vs. `jlc_capabilities.yaml` — the independent second geometry path), `order_quote.py` / `order_submit.py` (JLCPCB API if credentialed; both stop before payment; manifest + hash written).
**Accept:** golden board 2 package uploads clean to JLCPCB's web viewer (manual verification, once); `dfm_check.py` catches the silk and rotation mutants; CPL rotations spot-checked against JLC's rendered preview for 3 polarized parts.

### S13 — Agents, orchestrator, SKILL.md
**Read:** spec §3, §4, §5, §7 in full. This is the only session that reads the whole spec.
**Build:** all `agents/*.md` role prompts per §5 rules; `commands/ai-ee.md`; SKILL.md orchestrator playbook (phase machine, gate table from `gates.yaml`, agent-selection guidance per domain, fix-loop protocol, `--resume` from state.json, human checkpoint presentation format); `state.json` read/write helpers; violation→fixer dispatch wiring using S5's clusterer.
**Accept:** dry-run P4→P8 on golden board 1 with mutations injected mid-pipeline: orchestrator dispatches fixers, gates re-pass, state.json accurately reflects history; a killed-and-resumed session continues from the last gate.

### S14 — End-to-end hardening
**Read:** PROGRESS.md deviations list; spec §7, §9.
**Build/run:** three full `/ai-ee` runs: (a) golden-board-1-class brief (should be near-hands-off), (b) golden-board-2-class brief, (c) one novel brief chosen by the human. Fix everything that breaks; convert every manual intervention into either a script, an agent-prompt fix, or a documented human checkpoint. Final pass: reconcile SKILL.md and SPEC.md against as-built reality; freeze v1.
**Accept:** run (a) completes brief→order-ready package with ≤5 human interactions (spec M5 bar); all regression tests green; PROGRESS.md closed out with a v1 known-issues list.

---

## Sizing notes
- Heaviest sessions: S4, S10, S11, S13. If any exceeds a session's practical context/time budget, split at the natural seam noted in its Build list (e.g., S11 → S11a export/import+autoroute, S11b critical-net scripts+hygiene) and record the split in PROGRESS.md.
- S1's golden boards are the leverage point for everything after — do not economize there.
