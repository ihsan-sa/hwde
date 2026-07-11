# PROGRESS

Build state for the ai-ee skill. One entry per plan step (`ai-ee-implementation-plan.md`).
Session protocol: repo `CLAUDE.md` ("run step N"). Update this file + commit at every session end.

## Status board

| Step | Title | Status | Date |
|---|---|---|---|
| S0 | Repo bootstrap and environment | **done** | 2026-07-06 |
| S1 | Golden board corpus | **done** | 2026-07-11 |
| S2 | kicad-cli wrappers and gate infrastructure | **done** | 2026-07-11 |
| S3 | Geometry library | **done** | 2026-07-11 |
| S4 | Verification suite part 1 (crown jewels) | **done** | 2026-07-11 |
| S5 | Verification suite part 2 + check orchestration | pending | |
| S6 | Parts, library, datasheet tooling | pending | |
| S7 | Schematic generation | pending | |
| S8 | Board setup and reference data | pending | |
| S9 | Placement: seed, metrics, edit ops | pending | |
| S10 | Placement: annealer with routability feedback | pending | |
| S11 | Routing pipeline | pending | |
| S12 | Fab outputs, DFM, ordering | pending | |
| S13 | Agents, orchestrator, SKILL.md | pending | |
| S14 | End-to-end hardening | pending | |

Dependency graph (plan): S0 -> S1 -> S2 -> S3 -> {S4, S5}; S0 -> S6 -> S7; S2 -> S8 -> S9 -> S10 -> S11;
{S5, S7, S8, S11} -> S12 -> S13 -> S14. S4-S7 may run in parallel with S8-S10 (separate sessions/terminals).

## Recommended session setup per step

Set model/effort when launching the session (`/model`); "ultracode" = say the keyword in the
kickoff prompt to allow multi-agent workflows (higher token spend - use where marked).

| Step | Model | Effort | Ultracode | Why |
|---|---|---|---|---|
| S1 | Fable | max | - | Corpus quality gates everything after (plan: "do not economize") |
| S2 | Opus 4.8 | high | - | Well-specified wrappers; evidence-driven |
| S3 | Fable | max | - | Foundational geometry correctness; subtle (arcs, zones, units) |
| S4 | Fable | max | - | Crown-jewel check algorithms |
| S5 | Opus 4.8 | high | yes | Five independent well-specified checks; fan-out + verify vs manifest |
| S6 | Opus 4.8 | high | - | API integrations + quirks; schema-validated extraction |
| S7 | Fable | max | - | Novel library, hard acceptance (electrically identical netlist) |
| S8 | Opus 4.8 | high | - | Reference data transcription (cite sources) + rules_gen |
| S9 | Fable | max | - | Placement seed/metrics + IPC-vs-SWIG edit-path decision |
| S10 | Fable | max | yes | Largest custom artifact (SA annealer); parallel tuning experiments pay |
| S11 | Fable | max | yes | Integration-heavy; separable sub-tracks (plan notes the S11a/b seam) |
| S12 | Opus 4.8 | high | - | Format replication + independent gerber checks |
| S13 | Fable | max | - | The "soft top": agent prompts + orchestrator playbook (reads whole spec) |
| S14 | Fable | max | - | Full-run debugging; the pipeline spawns its own agents |

## Toolchain pins (resolution logic: `.claude/skills/ai-ee/scripts/lib/env.py`)

- **KiCad 10.0.3** = the pipeline pin (kicad-cli + bundled python + file formats). 9.0.5 stays
  installed as fallback (flip via `AIEE_KICAD_CLI`). Rationale: 10.x adds `pcb drc
  --refill-zones --save-board` (headless zone refill without SWIG) and `sch upgrade`; SWIG +
  render verified on both. NEVER mix versions (10-format files unreadable by 9.0 tools).
- Python venv 3.13.5 (`py -3.13`), pins in `requirements.txt` + full freeze `requirements.lock`.
  Key: kicad-python 0.7.1, kiutils 1.4.8, kicad-sch-api 0.5.6, skidl 2.2.3, shapely 2.1.2,
  numpy 2.5.1, gerbonara 1.6.3, easyeda2kicad 1.0.1.
- `tools/` (gitignored, vendored 2026-07-06 from C:/dev/AI-EE): Temurin JRE 25.0.3+9 portable
  (Freerouting 2.2.4 requires Java 25; system Java 24 insufficient) + freerouting-2.2.4.jar.
- Docker 27.1.1 client present; daemon typically down. Not required (JRE path covers Freerouting).

## Verify-later register

| # | Claim | Source | Status |
|---|---|---|---|
| V1 | DSN export / SES import via SWIG | spec P7, S11 | S0: pcbnew imports + board roundtrip + Export/Import symbols PRESENT on 9.0.5 and 10.0.3. Full export smoke incl. wx-assert suppression (LEARNINGS [swig]) at S11. |
| V2 | kicad-sch-api output opens in KiCad 10 | spec sec 9, S7 | S1: YES - three generated schematics ERC-clean under kicad-cli 10.0.3, netlists export, boards pass --schematic-parity. Quirks in LEARNINGS [python] (global labels silently dropped, pin renumbering, mid-wire pins do not connect). S7 builds on this. |
| V3 | `drc --refill-zones` availability | spec sec 1 | RESOLVED S0/S1: verified on real zoned boards (2- and 4-layer goldens): fills + persists via --save-board, plain DRC clean afterwards; the pipeline's ONLY working headless fill (ZONE_FILLER segfaults, LEARNINGS [swig]). S11 re-checks post-SES. |
| V4 | kipy `headless=True` starts `kicad-cli api-server` | spec sec 1 | RESOLVED S0: NO api-server subcommand in 9.0.5/10.0.3; kipy 0.7.1's server helper targets newer KiCad. Working IPC: sandboxed-GUI launch (smoke_ipc.py, verdict `gui-sandboxed-ok`). Headless alternative: SWIG bundled python. Decide edit path at S9. |
| V5 | JLCPCB Parts API (credentialed) | spec sec 1, S6 | Needs access application; jlcparts SQLite fallback path untested. S6. |
| V6 | JLCDFM upload (no public API) | spec P9 | Semi-manual by design; S12. |
| V7 | Freerouting batch flags + result parsing | LEARNINGS [freerouting] | Prior-attempt facts; re-verify on our own DSN at S11. |
| V8 | IPC API feature coverage for placement edits (move/rotate via kipy 0.7.1 on KiCad 10) | spec P6 | Connection verified S0; edit-op coverage untested until S9. |
| V9 | cpl-rotation mutant catchable at DFM | S2 finding, spec P9 | S2: committed cpl-rotation board does NOT fail `--schematic-parity` under 10.0.3 (manifest note stale). Designated catcher is dfm_check (S12) via CPL polarity - must not rely on parity. |
| V10 | Flipped (back-side) footprint pad geometry | S3, spec 6.3 | **RESOLVED S3 (Fable review)**: built a SWIG-flipped fixture (flip_fixture.py); pcbnew bakes the mirror INTO the file (locals mirrored, angles negated, layers renamed B.*), so the front-side transform covers flipped parts with NO special handling. geom's original mirror+swap DOUBLE-flipped - removed; 15/15 pads exact vs pcbnew; regression test in test_geom.py. |
| V11 | "Remove unused inner via pads" not modeled | S3 | geom treats a through via as copper on ALL inner layers (matches corpus + oracle default). A board enabling JLC's inner-pad removal would over-count inner via copper. Revisit at S8 rules / S12 DFM if used. |

## S0 - Repo bootstrap and environment (2026-07-06) - DONE

**Built:** repo skeleton per spec sec 2 (`.claude/skills/ai-ee/{SKILL.md stub, commands, agents,
scripts/lib, reference, templates}`); `scripts/lib/env.py` (single-source tool discovery, AIEE_*
env overrides, KiCad-10 pin); `scripts/check_env.py` (JSON contract, remediation strings, `--full`
live probes); `scripts/smoke_ipc.py` (IPC reachability probe, 3 strategies); venv + pinned deps;
pytest harness (`tests/test_check_env.py`, 4 tests) + `check.cmd`/`Makefile`; `LEARNINGS.md`
seeded (10 entries, prior-attempt facts attributed); git repo initialized; `tools/` vendored.

**Smoke-test results (plan-mandated four):**
1. `kicad-cli version`: 9.0.5 and 10.0.3 both installed and runnable (8.0 also present, ignored).
   Pinned 10.0.3.
2. `pcb render`: available on both.
3. IPC headless (kipy): kicad-python 0.7.1 `KiCad.__init__` has NO headless param; kipy/server.py
   drives `kicad-cli api-server`, which exists in NEITHER installed KiCad. Sandboxed-GUI IPC
   verified working: pcbnew.exe + scratch `KICAD_CONFIG_HOME` (api.enable_server pre-set, lib
   tables seeded -> no first-run dialogs) -> kipy connect, get_version, get_board all OK
   (verdict `gui-sandboxed-ok`; a pcbnew window appears during the probe). User config untouched.
4. `drc --refill-zones`: 10.0.3 yes (+ `--save-board`), 9.0.5 no.

Extra probes: SWIG pcbnew roundtrip (CreateEmptyBoard/Save/LoadBoard) PASS on both bundled
pythons; ExportSpecctraDSN/ImportSpecctraSES present on both. `check_env.py --full`: exit 0,
21 checks, 1 designed warning (ipc-headless, since no true headless server exists at this pin).

**Deviations from spec/plan (with reasons):**
1. Host is Windows 11; spec sec 1 says Linux/macOS. Everything S0 needs verified natively on
   Windows; `env.py` is OS-aware (POSIX branches present but untested here). Continuing on Windows.
2. No `make` on host -> `check.cmd` is the local entry point; `Makefile` kept for POSIX/CI.
3. KiCad pinned **10.0.3**, not the spec's default 9.0.x ("10.x acceptable"): gains headless zone
   refill (V3) + `sch upgrade` (helps V2); SWIG verified equally on both. 9.0.5 = tested fallback.
4. Spec's kipy-headless claim corrected (V4) - smoke evidence recorded, sanctioned alternatives named.
5. `tools/` (JRE 25 + freerouting jar) vendored from prior attempt C:/dev/AI-EE rather than
   downloaded (identical artifacts, saves ~200 MB fetch); gitignored, remediation strings cover re-fetch.
6. Python 3.13.5 rather than the 3.11 floor (all pinned deps import clean; recorded in case a
   later dep needs 3.11 - flip by recreating the venv).

**Interface notes for later steps:**
- ALL scripts resolve external tools via `scripts/lib/env.py`; tests override with AIEE_* vars.
  A set-but-invalid override fails loudly (tested) - never silently falls back.
- check_env JSON shape: `{script, status: pass|fail, resolved{...}, checks[{name, status:
  pass|warn|fail, detail, remediation?}]}`; exit 0/1/2. The normalized VIOLATION schema for
  gates comes at S2 (this is separate).
- S9 decision input (V4/V8): IPC = sandboxed-GUI process per edit session (window appears) vs
  SWIG bundled python (headless; mind LEARNINGS [swig] bulk-Remove corruption). Both verified live.
- S11: SWIG Specctra symbols present on the 10.0.3 pin; wx-assert suppression required
  (LEARNINGS [swig]); Freerouting invocation facts in LEARNINGS [freerouting]; JRE at
  `tools/jre/jdk-25.0.3+9-jre/bin/java.exe` (env.py finds it).
- skidl/kicad_sch_api import-time stdout noise: redirect around imports in any JSON-emitting
  script (check_env does this; copy the pattern).

**New verify-later items:** V7, V8 (registered above).

## S1 - Golden board corpus (2026-07-11) - DONE

**Built:** three generated golden boards (schematic + board from ONE design module each, so
netlists match by construction) in `tests/golden/`:
- `blinky2` - 2-layer STM32F103C8 blinky: AMS1117-3.3, 8 MHz crystal (Crystal_GND24 3225),
  LED chain, SWD + 5V headers, B.Cu GND pour + F.Cu fan-out pour. 16 fps, 60 track segs, 25 vias.
- `usbbuck4` - 4-layer (Sig/GND/Pwr/Sig) STM32F103 USB-FS device: AP63203 buck, micro-B, USB
  diff pair, MCO clock-out header with F->B transition + return via at (141.9,123.4), In2 = 3V3
  plane + VBUS island + GND strip under the MCO B.Cu corridor.
- `rf4` - 4-layer sub-GHz front end: RFM95W-868S2 module, pi match (C-L-C), 0.35 mm 50-ohm feed
  at y=122 over solid In1 GND to an edge-mount SMA, coplanar F.Cu pour, ~90 vias (fence rows,
  perimeter ring, module field) as the S4 performance stress case.
All three: `kicad-cli sch erc` = 0, `pcb drc --schematic-parity --severity-all` = 0 (warnings
included). Renders eyeballed (kicad-cli pcb render).

**Generator infra** (`tests/golden/generators/`): `gen.py` (driver: sch -> netlist -> netmap ->
board -> refill -> ERC/DRC report, exit 0/1/2), `sch_build.py` (kicad-sch-api: grid-snapped pin
stubs + local labels, power-rail clusters with PWR_FLAG endpoints, pin-number fixups, minimal
.kicad_pro authority), `pcb_build.py` (bundled-python SWIG: footprints/tracks/vias/zones/silk from
the design module, pad nets from the netlist netmap, --pads-out coordinate dumps), plus
`design_<board>.py` modules (stdlib-only, imported by both builders).

**Mutants** (`tests/golden/mutations/*.py` -> committed under `tests/golden/mutants/<name>/`):
7 deterministic text-surgery scripts (exact-match asserts, fixed UUIDs, kicad-cli refill;
double-run byte-identical): plane-split-under-clock (rf4 In1 keepout slot under the feed, fill
area drop 15.4 mm^2 verified), missing-return-via (usbbuck4 MCO transition), undersized-power-
trace (blinky2 3V3 neck 0.8->0.16 mm, DRC-quiet vs 0.127 floor), decoupler-moved (blinky2 C1
15.7 mm from U1.48, legally rewired), diffpair-skew (usbbuck4 +6.2 mm DM meander), silk-over-pad
(blinky2 D1), cpl-rotation (blinky2 D1 180 deg + pad-net swap = mounted backwards). All mutants
DRC-quiet except silk-over-pad's 2 intended silk warnings; cpl-rotation intentionally fails
--schematic-parity (that inconsistency IS the defect; documented in manifest).

**Manifest:** `tests/golden/manifest.yaml` - every mutant -> designated check + expected
net/layer/coordinates/thresholds (the S4/S5/S12 acceptance arbiter). Checks referenced:
check_return_path x2, check_current, check_decoupling, check_diffpair, check_silk, dfm_check.

**Tests:** `tests/test_golden.py` (25 tests; live-toolchain ones marked `smoke`): goldens
ERC/DRC/parity clean, saved fills present, each mutation deterministic + effective, committed
mutants present, manifest complete/consistent. `check.cmd` green (29 tests, ~60 s).

**Deviations from spec/plan (with reasons):**
1. rf4 uses an RFM95W module + discrete pi match instead of a bare QFN transceiver: AX5043's
   symbol has two power_out VDD_ANA pins (tying them is an ERC error by pin matrix); CC1200's
   0.5 mm-pitch 32-QFN fan-out was not hand-routable to DRC-clean within session budget. The
   module still provides every S1 mutant target (50-ohm feed over In1, matching parts, via
   density) and spec 6.5 only asks for a "4-layer RF" fixture.
2. Boards drawn minimally via generator scripts rather than sourced from open designs (plan
   allows either): generation keeps the corpus hermetic (embedded symbols/footprints, severity
   config in checked-in .kicad_pro) and makes regeneration + mutation reproducible.
3. Goldens are committed AND regenerable; regeneration reassigns UUIDs, so after any
   `gen.py --board X` run the mutation scripts must be re-run (test suite only hashes
   script-output determinism, not committed bytes).
4. cpl-rotation mutant is representable on the board only as a polarity inconsistency (see
   manifest note); the "pure CPL file" variant belongs to S12's bom_cpl outputs.
5. kicad-sch-api wheel is 0.5.6 as pinned (its __version__ string lies "0.5.5").

**Interface notes for later steps:**
- S2: normalize wrappers against these boards; ERC/DRC JSON parsing patterns (incl. multiline
  netlist regex, exit-code-equals-count) already exist in generators/gen.py - lift from there.
- S3: goldens carry SAVED fills (test-guarded); zone-freshness work can diff against
  `--refill-zones --save-board` output. Stackup: 4-layer boards have default-stackup dielectric
  constants only (SetStackupDescriptor path failed under SWIG; note in pcb_build).
- S4/S5/S12: `manifest.yaml` is the acceptance contract; net names from local labels carry a
  leading "/" ("/MCO", "/USB_DP"); power nets are bare (+3V3, GND, VBUS). Expected regions/
  thresholds per mutant recorded there.
- Regen flow: `gen.py --board <b> --parity` (all three) then re-run all 7 mutation scripts.
- Board-gen for S7-S11: pcb_build.py's design-module contract (tracks/vias/zones/silk dicts) and
  sch_build.py's conventions (grid snap, stub+label, rails, fixups) are reusable as-is.

**New verify-later items:** none added; V2 evidenced (full resolution at S7), V3 resolved for
generation-side fills (S11 re-checks after SES import).

## S2 - kicad-cli wrappers and gate infrastructure (2026-07-11) - DONE

**Built** (all under `.claude/skills/ai-ee/`):
- `scripts/kc.py` - the single place that drives kicad-cli and reads its JSON. Subcommands:
  `erc`, `drc` (-> normalized violations, exit 1 if any); `gerbers`, `drill`, `pos`, `step`,
  `render`, `sch-pdf`, `netlist` (export wrappers, exit 2 on failure). Normalized violation
  schema `{check, severity, pos, layer, net, refs, msg}` (+ `source`, `items` for traceability).
  Importable: `run_erc/run_drc/render_png/export_*` functions and the pure parsers
  (`parse_drc_data`, `parse_erc_data`, `normalize_violation`) used by gate.py, render.py, tests.
- `scripts/render.py` - SPEC 6.2 multi-view wrapper (`--views top,bottom,iso --w 2400`),
  thin driver over `kc.render_png`; consistent `<stem>_<view>.png` naming for VLM review.
- `scripts/gate.py` - `--gate <name>` from gates.yaml: runs the gate's kc report (or `--report`
  a pre-made one), evaluates, exit 0/1/2. `--list` lists gates. `--commit MSG` = the
  git-commit-on-gate-pass helper (stages+commits only on pass, skips when clean, never pushes).
- `reference/gates.yaml` - gate definitions S2 can evaluate: `erc` (P4, clean=err+warn),
  `drc` (P6, err only), `drc_routed` (P7, parity+all-track-errors, err+warn). Later gates
  (verify S5, dfm S12) append here.
- `tests/test_kc_gate.py` - 29 tests (11 pure normalizer/gate-logic + git-helper, 18 `smoke`).

**Smoke/acceptance evidence** (live 10.0.3): kc erc+drc report `status:pass`, `total:0` on all
three goldens; `erc`/`drc_routed` gates PASS on all three. Seeded a track_width ERROR (narrow a
golden segment to 0.05 mm < 0.127 floor) -> `gate.py --gate drc` FAILS exit 1 with the violation
at the narrowed segment's coordinates (net + pos verified). `check.cmd` green: **58 passed**,
check_env exit 0.

**Environment fix (machine state):** a persistent User-level `AIEE_KICAD_CLI` pinned KiCad 9.0.5,
which cannot load the 10-format goldens (exit 3, no report) - it silently overrode the documented
10.0.3 pin. Removed it (user: "do what you think best"); env.py now resolves 10.0.3 by preference.
See LEARNINGS [kicad-cli][windows]. An already-open shell still inherits the old value until
restarted; `unset AIEE_KICAD_CLI` if a session's goldens "fail to load".

**Deviations from spec/plan (with reasons):**
1. No separate `lib/` normalizer module: the normalized schema + parsers live in `kc.py` and are
   imported by gate.py/render.py/tests (repo pattern: gen.py imports sch_build/pcb_build). One
   source of truth for kicad-cli JSON without a thin extra module.
2. `render` exists BOTH as a `kc.py` subcommand (single view) and as `render.py` (the SPEC 6.2
   multi-view `--views` entry the P6/P8 agents call by name). render.py delegates to
   `kc.render_png`; no logic duplicated.
3. gates.yaml holds only the three gates S2 can actually evaluate; `verify` (S5) and `dfm` (S12)
   gates are deferred to their steps (documented in the file header), not stubbed.
4. Gates never refill/save zones - evaluation must not mutate the board. The routing flow's
   refill is a separate explicit op (route_auto.py, S11), not a gate side effect.

**Interface notes for later steps:**
- Normalized violation schema is the pipeline-wide contract (S4/S5 checks emit the SAME shape;
  cluster_violations.py groups on region/net/type; fixers read pos/net/refs). Import parsers from
  `scripts/kc.py`. Nets keep the golden convention (local-label nets `/NAME`, power nets bare).
- kc.py `run_drc(cli, pcb, parity=, all_track_errors=, refill=, save_board=)`; `run_erc(cli, sch)`.
  Both return `{status, counts{total,by_severity,by_source}, violations[]}`.
- gate.py `evaluate(name, gate_dict, kc_report) -> result`; `run_report_for_gate(gate, input)`;
  `git_commit_on_pass(msg, cwd)`. gates.yaml gate = `{phase, tool:erc|drc, drc_options,
  fail_severities, max_count, description}`. Orchestrator (S13) reads gates.yaml for the gate table.
- S12 fab: kc.py exports are thin/JLC-agnostic (Protel ext, X2, layer sets = fab_export.py's job);
  `pos` is forced to mm (kicad-cli default is inches). Reuse `export_gerbers/drill/pos/step`.
- S13: `gate.py --commit MSG` is the per-gate-pass commit helper (SPEC section 4).

**New verify-later items:** V9 (cpl-rotation not caught by parity; DFM must catch it - S12).

## S3 - Geometry library (2026-07-11) - DONE

**Built:**
- `scripts/lib/geom.py` - the single geometry source for the verification suite.
  Parses `.kicad_pcb` s-expressions (sexpdata -> nested lists; NO SWIG/IPC, pure venv)
  into net-indexed, per-layer shapely primitives:
  - tracks (segment + arc) as width-buffered polylines; vias as disks spanning the
    INCLUSIVE copper range (a through via = copper on every inner layer, not just the
    two named); pads (rect/roundrect/oval/circle) with rotation-correct absolute
    centers; zone fills (keyhole rings -> shapely area is exact); board outline
    (gr_rect/poly/circle, or gr_line+gr_arc polygonized).
  - Stackup model: copper order from the board's (layers) list (top->bottom);
    dielectric heights + epsilon_r from a (stackup) block when present, else documented
    FR4 defaults (assumed=True, source recorded). `adjacent()`, `height_between`,
    `epsilon_between`, `is_outer` for S4 return-path / S5 diffpair-skew.
  - Public API for S4/S5: `net_copper(net,layer)` (union of ALL copper), `zone_fill`,
    `layer_copper(layer,net=,exclude=)`, `net_area`/`net_area_by_layer`,
    `tracks_of/vias_of/pads_of/zones_of(net=,layer=,ref=)`, `adjacent_copper`,
    `layers_with_zone`, `outline`. In-process caching (memoized unions +
    `load_board()` mtime cache).
  - Zone-fill freshness: `assert_fresh()` (fast: raise StaleFillError on any unfilled
    zone) and `assert_fresh(refill=True)` (diff committed fills vs a fresh
    `kicad-cli pcb drc --refill-zones --save-board` on a temp copy - the S0 path via
    env.py + kc.run_drc). CLI: `--pcb -> JSON summary`, exit 0/2, `--check-fill` exit 1.
- `tests/golden/generators/area_oracle.py` - bundled-python pcbnew ground truth:
  per-(net,layer) copper area as a SHAPE_POLY_SET union (TransformShapeToPolygon for
  tracks/pads/vias + `zone.GetFilledPolysList(layer)`), the independent second path
  the round-trip test measures geom against.
- `tests/test_geom.py` - 35 tests (25 pure: parser, pad rotation/shape areas, via
  span, stackup from-block + FR4 defaults, freshness, cache, CLI, arc sampler;
  10 smoke: area round-trip vs oracle x3 boards, layer-order match, <5s performance,
  S4/S5 API surface, freshness fast + refill paths).

**Acceptance evidence (live 10.0.3):**
- Copper area per net vs KiCad's own geometry (pcbnew oracle): TOTAL board copper
  within **0.012% / 0.008% / 0.018%** (blinky2/usbbuck4/rf4); worst per-(net,layer)
  with area >1 mm2 is **1.03%** (rf4 GND/In2.Cu, ~73 through-via disks - circle
  faceting); full mutual net coverage (geom invents/drops nothing > 0.05 mm2). Bug
  found + fixed mid-step: vias were read as a literal 2-layer set, dropping inner-layer
  via copper (rf4 GND/In2 was 2.27 vs 22.66) - fixed to expand the from/to span.
- Performance: parse + build + ALL net unions <0.13 s per board (budget 5 s).
- Freshness: all goldens filled; blinky2's committed fill matches a fresh kicad-cli
  refill within 2%.
- `check.cmd` green: **93 passed** (58 prior + 35), check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. Spec 6.3 "epsilon_r from board file": the corpus boards carry NO (stackup) block
   (SWIG BuildDefaultStackupList didn't serialize one; S1 note). geom parses a stackup
   block when present (unit-tested on a synthetic one) but falls back to documented FR4
   defaults (epsilon_r 4.5; JLC-typical 1.6 mm split 0.165/0.67/0.165; 1 oz outer /
   0.5 oz inner) flagged `stackup.assumed=True`. S8's stackups.yaml will supply the
   authoritative table.
2. "KiCad's report" of per-net copper area: kicad-cli exposes no such report, so the
   oracle unions the SAME primitives KiCad's own engine uses (TransformShapeToPolygon +
   GetFilledPolysList). geom and the oracle therefore agree by construction where the
   parse is correct - the honest reading of the acceptance criterion.
3. geom.py is a LIBRARY but also ships the spec 6 CLI contract (argparse/JSON/exit 0/2,
   `--check-fill` exit 1) so it is callable and debuggable standalone.
4. Chose sexpdata (pinned) over kiutils for parsing: full control over pad rotation and
   keyhole zone rings, avoiding kiutils' documented pre-rotation-pad + cp1252 quirks
   (LEARNINGS [python]). Parse is 45 ms on the largest board.
5. Flipped-footprint pad mirroring implemented but corpus-unvalidated (no back-side
   footprints exist) -> V10. "Remove unused inner via pads" DFM option not modeled -> V11.

**Interface notes for later steps:**
- Import: `sys.path.insert(0, SCRIPTS/"lib"); import geom`; then `geom.load_board(pcb)`
  (cached) or `geom.BoardGeom.from_file(pcb)`. Everything is mm (areas mm2, lengths mm).
- Net names keep the golden convention: local-label nets carry a leading "/" ("/MCO",
  "/USB_DP"); power nets are bare (+3V3, GND, VBUS). `bg.nets` = nets carrying copper.
- S4 `check_return_path`: `adjacent_copper(sig_layer)` gives the (above,below) copper
  neighbours; `layers_with_zone(refnet)` says which are planes; `zone_fill(refnet,
  reflayer)` is the reference pour; `layer_copper(reflayer, exclude=refnet)` is the
  "other-net copper / voids" to test the return corridor against. Call `assert_fresh()`
  before trusting zone geometry.
- S4 `check_current`: `tracks_of(net)` (.width/.length/.shape) + `zone_fill(net,layer)`
  for pour neckdown (medial-axis min width is the check's job on the returned polygon).
- S5 `check_diffpair`: `tracks_of(net)` lengths; `stackup.epsilon_between(a,b)` +
  `height_between` for ps skew.
- Vias span the inclusive copper range and pads expand `*.Cu` to all copper - inner-layer
  per-net area is therefore non-trivial; do not assume a through via touches only 2 layers.
- Caching is in-process only (each check re-parses; <0.13 s). No disk cache - unnecessary
  at this speed and avoids shapely-pickle staleness risk.

**New verify-later items:** V10 (flipped-footprint geometry unvalidated - RESOLVED below), V11
(inner via pad removal not modeled).

### S3 Fable review (same day) - 3 bugs found, all fixed + regression-tested

The step ran on Opus 4.8 against the recommended Fable/max; re-reviewed under Fable 5.
Suite grew 35 -> 46 geom tests (104 total). Findings, by severity:

1. **Keepout rule areas broke the freshness gate (S4 blocker).** `(zone ... (keepout ...))`
   never carries fills, so geom counted it as an eternally-unfilled zone and `assert_fresh()`
   raised StaleFillError on the plane-split mutant - the PRIMARY fixture check_return_path
   must analyze. Fixed: rule areas are excluded from the zone list/freshness and exposed as
   `BoardGeom.rule_areas` [{name, layers, outline}] metadata (S9 will want them). Verified on
   the mutant: assert_fresh passes; In1 GND fill drop vs golden = 15.400 mm^2 (exactly the
   S1-recorded value); rule area intersects the manifest region.
2. **Flip transform was wrong (double mirror) - V10 falsified, then resolved.** Empirical
   fixture (flip_fixture.py flips C10 rot-90 + J1 USB micro via pcbnew, dumps ground truth):
   pcbnew bakes the flip into the saved file (pad locals mirrored, angles negated, layers
   renamed B.*). geom's `lx=-lx` + F/B layer swap therefore DOUBLE-flipped: pad centers
   mirrored about the fp origin and layers wrong side. Fixed by DELETING the special case -
   the front-side transform is universal. 15/15 copper pads exact (incl. duplicate-numbered
   SH shield pads); smoke test builds the fixture live each run.
3. **Out-of-range roundrect rratio inflated pads.** rratio > 0.5 (KiCad clamps; easyeda2kicad
   footprints can ship anything) inverted the inner box -> pad polygon LARGER than the pad
   (2.49 vs 2.0 mm^2). Fixed: clamp r to min(w,h)/2; rratio 0.5 = stadium verified analytic.
   (Shapely handles the 0.5 degenerate box correctly - only >0.5 was broken.)

Minor (also fixed): `F&B.Cu` zone-layer shorthand now expands to F.Cu+B.Cu; explicit-stackup
copper thicknesses are read from the block (were silently defaulted); CLI exits 2 on ANY
error (was: unexpected exceptions escaped with a traceback), `--check-fill` failure now says
`status:"violations"` to match exit 1; arc sampler's CW/boundary-crossing branches
verified correct and pinned by tests (were untested); dead code removed (`_flip_layer`,
unused `field` import, stored parse tree).

Interface addition for S4/S5/S9: `bg.rule_areas` (keepouts; never copper, never "unfilled").
Flip-fixture builder: `tests/golden/generators/flip_fixture.py` (bundled python).

## S4 - Verification suite part 1, the crown jewels (2026-07-11) - DONE

**kicad-happy evaluation (plan-mandated, one timeboxed subagent): implement fresh.**
Repo exists (aklofas, MIT, active) but is an agent-skills plugin, not a library: stdlib
radius-SAMPLING geometry (no shapely), plane-split = bbox overlap, return-via distance and all
judgment deferred to its LLM layer; "5,800+ projects validated" = crash-free parsing, not
detector accuracy. Wrapping = adopting a second, weaker geometry stack parallel to geom.py.
Borrowed under MIT: IPC-2152 interpolation table, 0.7 nH/mm trace-inductance heuristic,
threshold-ladder idea. Full brief filed: `C:/dev/ai-library/kicad-happy-analyzers-2026/`.

**Built** (all on geom.py; shared plumbing `scripts/lib/checklib.py` - violation builder in the
S2 normalized schema, report/emit/exit-code contract, CheckError -> exit 2):
- `scripts/check_return_path.py` - per constraints high_speed net: flat-capped corridor
  (k x width, default 3) per signal layer vs the SINGLE connected component of reference-net
  copper on each stackup-adjacent layer (microstrip 1 ref, stripline 2); deficit polygons ->
  violations with polygon + coords + ref layer, severity = centerline crossing (error) vs
  corridor nick (warning). Layer transitions (signal via joining 2+ track layers): if the
  reference (layer, net) set changes, require a same-refnet via spanning both ref layers within
  r = c/(f_knee*20) from t_rise_ns, else return_via_radius_mm, else 2.0 mm; different ref nets ->
  stitching-capacitor search (two-pad footprint bridging both nets within r). Unavoidable
  single-item plane punctures are EXCISED before judging (see LEARNINGS [geometry][shapely]:
  3 FP artifact classes - endpoint caps, own-via/THT annulus corners, lone other-net antipads;
  fix = flat caps + disk excision, slots survive because they are not at vias).
- `scripts/check_current.py` - per constraints power net: every track segment vs IPC-2152
  minimum width (vendored table converted to copper AREA so inner layers scale by stackup
  thickness; (0,0) anchor below 0.5 A ~ chart readings: 0.20 mm @ 0.4 A; dT scaling (10/dT)^0.44;
  worst-case full-budget per segment + optional per-region `overrides` for branch currents);
  pour neckdowns by erosion-connectivity between via attachment points (binary search, reports
  neck width + location); via clusters (union-find, 2 mm) each need ceil(I/0.5A) vias.
- `scripts/check_decoupling.py` - metadata-driven (schema defined here, S7 will emit it;
  hand-written fixtures per golden board): Manhattan pad->pin (Euclidean also reported),
  same-layer rail connectivity -> 0 or 2 rail vias, gnd leg = nearest gnd via distance,
  loop = 0.7 nH/mm x (rail+gnd) + 1 nH/via; value classes bulk >=1uF (20/30 mm, 30/60 nH),
  mid 10nF-1uF (10/15, 10/20), hf <10nF (5/7.5, 6/12); stale metadata (missing ref/pin/net
  mismatch) = error violation kind=metadata_mismatch, not a crash.
- Fixtures: `tests/golden/<board>/constraints.json` + `decoupling.json` (x3 boards) - the
  concrete constraints.json field shapes S4 consumes (high_speed / power entries documented in
  each script docstring; P2/S7/S13 must generate these shapes).
- `tests/test_checks.py` - 51 tests: 30 pure (IPC interpolation/monotonicity, farads/classes,
  severity ladders, radius formula, per-layer reference mapping, corridor artifacts on synthetic
  boards incl. flat-cap + excision regression guards, transitions incl. stitch-cap branch, pour
  necks, decoupling loop/via counting, stale-metadata, exit-2 on unfilled zones) + 20 corpus
  (manifest-driven: 3 goldens x 3 checks clean, 4 S4 mutants caught with manifest coordinates,
  3 non-S4 mutants as negative controls x 3 checks, CLI --out/exit codes/schema keys) + 1 smoke
  (rf4 all three checks < 30 s; actual ~0.9 s total, return_path alone 0.27 s).

**Acceptance evidence:** all four S4 mutants caught with correct net + coordinates
(plane-split: /RF_FEED In1.Cu, polygon intersects manifest region, crossing 1.40 mm;
missing-return-via: /MCO pos [141,123], nearest GND via 3.31 mm > 2.0; undersized: +3V3 exact
segment (118.5,106.95)->(118.5,110.5) 0.16 < 0.20 mm required; decoupler-moved: C1/U1.48
Manhattan 21.0 mm / Euclidean 15.65 mm > 15, error + loop warning). Zero violations on all
three goldens for all three checks; diffpair-skew/silk-over-pad/cpl-rotation mutants also clean
under S4 checks (no cross-contamination). `check.cmd` green: **155 passed** (104 prior + 51),
check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. Spec 6.3 step 2 says reference = "filled-zone polygons"; implemented as ALL reference-net
   copper on the ref layer, then the single connected component under the corridor ("continuous
   reference copper", step 3's own wording) - same-net stitching copper must not FP, floating
   islands must not satisfy.
2. Spec-literal corridors false-positive on every legitimate board (own-via antipads, endpoint
   caps, lone other-net antipads - all three goldens fired). Shipped flat caps + single-item
   excision (LEARNINGS entry); severity-by-crossing-length retained. Other-net THT pad FIELDS
   deliberately not excised.
3. IPC-2152 as a vendored interpolation table (area-based) rather than a formula: the standard
   is chart-based; the IPC-2221 power-law with the usual external k=0.048 would MISS the
   undersized mutant (requires only 0.085 mm @ 0.4 A). Table + (0,0) anchor matches published
   chart readings and the corpus by construction.
4. check_current has no per-branch current attribution (needs a source/sink graph the pipeline
   does not have yet): worst-case full budget per segment + documented per-region overrides.
   Corpus branch widths (0.25 mm risers @ 0.4 A -> 0.20 required) pass with margin by S1 design.
5. check_decoupling thresholds are kicad-happy-informed but loosened to corpus reality (their
   5 mm MED would flag the goldens' legitimate ~7 mm VDDA channel routing); manifest's 15 mm
   hint = mid-class error threshold. Manhattan is the spec metric; the manifest's "15.7 mm" is
   Euclidean - both emitted, both asserted.
6. manifest.yaml plane-split net fixed RF_FEED -> /RF_FEED (S1 entry contradicted the file's own
   net-name convention header; board net is /RF_FEED).
7. Corpus tests are unmarked (hermetic: committed boards + pure venv, no toolchain) unlike S3's
   conservative smoke-marking; only the timing test is `smoke`.

**Interface notes for later steps:**
- Report/violation schema: kc.py-shaped payload {script, status pass|violations|error, board,
  counts{total,by_severity,by_source}, violations[], checked[]} + normalized violations
  {check, severity, pos [x,y], layer, net, refs, msg, source, items} + extras (kind, polygon,
  *_mm). S5 verify_all merges these payloads as-is; kind values: corridor_void,
  no_reference_plane, missing_return_via, missing_stitch_cap, undersized_track, pour_neckdown,
  insufficient_transition_vias, decoupler_distance, decoupler_loop, gnd_stub_long,
  metadata_mismatch.
- constraints.json shapes consumed (P2/S8/S13 generate): high_speed [{net, reference
  str|{layer:net}, k, t_rise_ns, return_via_radius_mm}]; power [{net, current_a, dt_c,
  via_amps, overrides[{near,radius_mm,current_a}]}]. decoupling.json: associations [{cap, ic,
  pin, rail, gnd, value, class?, max_dist_mm?, max_loop_nh?}] - S7 must emit exactly this.
- All three checks assert_fresh() (fast) before reading zones; --verify-fill on
  check_return_path adds the kicad-cli refill diff. Exit 2 on stale fills/missing nets/bad
  metadata files; stale ASSOCIATIONS are exit-1 violations.
- checklib.py is the S5 template: implement check_diffpair/creepage/thermal/silk/pdn as
  run(argv)->(payload,out) + cli_wrap; tests can call run() in-process (see
  tests/test_checks.py run_check).
- Reusable synthetic-board builders for S5 tests: tests/test_checks.py _board/_board4 +
  fill/track/footprint sexpr snippets.
- S7 heads-up: golden decoupling.json files are the metadata CONTRACT fixtures; regeneration
  of goldens does not touch them, but re-associating caps (refs) would.

**New verify-later items:** none. (V9 unchanged - cpl-rotation still S12's to catch.)
