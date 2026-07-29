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
| S5 | Verification suite part 2 + check orchestration | **done** | 2026-07-22 |
| S6 | Parts, library, datasheet tooling | **done** | 2026-07-22 |
| S7 | Schematic generation | **done** | 2026-07-22 |
| S8 | Board setup and reference data | **done** | 2026-07-22 |
| S9 | Placement: seed, metrics, edit ops | **done** | 2026-07-22 |
| S10 | Placement: annealer with routability feedback | **done** (feedback wired at S11) | 2026-07-23 |
| S11 | Routing pipeline | **done** | 2026-07-23 |
| S12 | Fab outputs, DFM, ordering | **done** | 2026-07-24 |
| S13 | Agents, orchestrator, SKILL.md | **done** | 2026-07-27 |
| S14 | End-to-end hardening | **done** (v1 FROZEN) | 2026-07-28 |

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
| V1 | DSN export / SES import via SWIG | spec P7, S11 | **RESOLVED S11**: ExportSpecctraDSN(board, path) + ImportSpecctraSES(board, path) both work headless on 10.0.3 with the wx recipe (wx.App + DisableAsserts + APP_ASSERT_SUPPRESS); full roundtrip DRC-clean incl. parity. Worker results travel via FILES (wx stdout noise). LEARNINGS [swig][freerouting]. |
| V2 | kicad-sch-api output opens in KiCad 10 | spec sec 9, S7 | **RESOLVED S7** (S1 evidenced flat): hierarchical output too - add_sheet/add_sheet_pin/add_hierarchical_label serialize, 3-sheet hierdemo ERC-clean on 10.0.3, cross-sheet nets + global power nets netlist correctly. Blinky2 regenerated via schlib = netlist IDENTICAL to golden. Quirks in LEARNINGS [python]. |
| V3 | `drc --refill-zones` availability | spec sec 1 | RESOLVED S0/S1: verified on real zoned boards (2- and 4-layer goldens): fills + persists via --save-board, plain DRC clean afterwards; the pipeline's ONLY working headless fill (ZONE_FILLER segfaults, LEARNINGS [swig]). **S11 re-checked post-SES**: imported tracks stale the fills (33 clearance/hole violations) until the kicad-cli refill (then 0); route_auto refills before export AND after import. |
| V4 | kipy `headless=True` starts `kicad-cli api-server` | spec sec 1 | RESOLVED S0: NO api-server subcommand in 9.0.5/10.0.3; kipy 0.7.1's server helper targets newer KiCad. Working IPC was sandboxed-GUI launch (smoke_ipc.py). **S9: that path REGRESSED on this host** ("KiCad is not ready to reply", verdict `unavailable`; LEARNINGS [ipc]). Edit path decided at S9: SWIG bundled python. |
| V5 | JLCPCB Parts API (credentialed) | spec sec 1, S6 | **RESOLVED S6**: the pinned easyeda2kicad 1.0.1 wraps an ANONYMOUS JLCPCB parts search (EasyedaApi.search_jlcpcb_components) that needs NO credential - verified live (18783 hits for "100nF 0603 X7R", Basic/Extended+stock+price). That is parts_search.py's PRIMARY path; the credentialed api.jlcpcb.com (still needs an access application) is unnecessary for search and deferred to S12 ordering. jlcparts SQLite = optional --db cache (none on host; code path unit-tested vs a synthetic DB). Web search = agent last resort (exit 2 when offline+no db). LEARNINGS [parts]. |
| V6 | JLCDFM upload (no public API) | spec P9 | **RESOLVED S12 (as designed semi-manual)**: no public API exists, so the fab's own 30+ checks stay a human/browser step. order_submit.py emits the zip path + jlcdfm.com in its `human_steps`, and the LOCAL engine (dfm_check.py) runs the big classes pre-upload. The upload itself is V15. |
| V7 | Freerouting batch flags + result parsing | LEARNINGS [freerouting] | **RESOLVED S11** on our own DSNs: deterministic set `--gui.enabled=false -mt 1 -is sequential -da --logging.file.enabled=false -mp N -de/-do`; completion parse priority pinned in routelib.parse_fr_log; -da does not stop the one-shot update check. NEW: FR 2.2.4's DSN reader can wedge in infinite recursion on KRT guide-wire copper - route_auto detects (timeout + zero passes) and falls back to KRT (LEARNINGS [freerouting][routing]). |
| V8 | IPC API feature coverage for placement edits (move/rotate via kipy 0.7.1 on KiCad 10) | spec P6 | **RESOLVED S9 (negative)**: kipy's edit API exists (FootprintInstance.position/.orientation + update_items + save) but is UNVERIFIABLE live - the sandboxed-GUI connect layer now fails on this host (V4 note), and headless kipy only lands in KiCad 11 (research: headless-pcb-routing-2026). place_edit.py uses SWIG bundled python (verified: move/rotate/flip/lock applied + independently re-parsed). kipy/IPC = KiCad-11 migration target. |
| V9 | cpl-rotation mutant catchable at DFM | S2 finding, spec P9 | **RESOLVED S12**: dfm_check compares board `pad number -> net` against the netlist's `pin -> net` (parity is net-level and stays blind to the swap, as S2 found). The mutant is caught as `cpl_polarity`, ref D1, **rotation_delta_deg 180.0** - exactly the manifest's expectation - and the pad geometry supplies that angle. Test is HERMETIC (committed s7_regen netlist as oracle). LEARNINGS [dfm][kicad]. |
| V10 | Flipped (back-side) footprint pad geometry | S3, spec 6.3 | **RESOLVED S3 (Fable review)**: built a SWIG-flipped fixture (flip_fixture.py); pcbnew bakes the mirror INTO the file (locals mirrored, angles negated, layers renamed B.*), so the front-side transform covers flipped parts with NO special handling. geom's original mirror+swap DOUBLE-flipped - removed; 15/15 pads exact vs pcbnew; regression test in test_geom.py. |
| V11 | "Remove unused inner via pads" not modeled | S3 | geom treats a through via as copper on ALL inner layers (matches corpus + oracle default). A board enabling JLC's inner-pad removal would over-count inner via copper. S8 did not add it (rules_gen has no via-pad-removal knob); revisit at S12 DFM if used. |
| V12 | Controlled-impedance geometry not validated vs JLC's calculator | S8, spec P5 | S8 `lib/impedance.py` computes trace width/diff gap from IPC-2141A microstrip + the published edge-coupled correction (50R/1.6mm FR4 -> 3.02mm matches textbook ~2.95mm; diff round-trips exactly). These are first-order estimates for sizing DRU rules + S5 targets; only OUTER-layer microstrip is modelled (no inner stripline). Confirm against JLC's online impedance calculator before ordering a controlled-impedance board (S12/S14). |
| V13 | route_cleanup loop-breaker vs plane-mediated connectivity | S11 | **CLOSED S14 (as v1 disposition)**: regressed on ALL THREE live boards (2L x2, 4L would-have via dry-run) - demoted to dry-run-inspect-cherry-pick or skip (router.md + SKILL.md); root cause (union-find/fill edge) documented, not fixed - v1 known-issue #1. |
| V14 | Freerouting 2.2.4 DSN-reader recursion on KRT copper | S11 | PolylineTrace.combine infinite recursion before pass 1 on KRT guide-wire copper; mitigated (wedge detection + KRT fallback). Worth an upstream issue with a minimal DSN repro. |
| V15 | JLCPCB web-viewer upload + polarized-part CPL preview | S12, plan S12 accept | **HUMAN STEP, NOT YET DONE.** Two S12 accept legs need a browser and have no API: (a) upload `usbbuck4_gerbers.zip` to JLC's viewer/quote page and confirm it renders clean, (b) spot-check the rendered CPL preview for 3 polarized parts (D1 LED_0805, plus a diode/electrolytic on a future board). The machine-checkable half (package completeness, hashes, rotation maths) IS tested (test_full_package_flow, test_cpl_rotation_corrections). Do this once before the first real order (S14). |
| V16 | jlc_pricing.yaml staleness + credentialed ordering API | S12 | order_quote's numbers are transcribed headline prices flagged `estimated: true`, never a quote; JLC's real price depends on panelisation/promotions/region. order_submit implements the manifest + human gate but NOT a live api.jlcpcb.com call (that programme needs an approved access application this host does not have) - `--api` exits 2 with the exact missing prerequisite rather than shipping an untested payment path. Re-verify the table (and wire the API behind `_api_submit()`) when credentials exist. |
| V17 | No scripted silk/text move op (refdes/value) | S13 | **RESOLVED S14**: hit on run (a) day one (J1 polarity legend = reviewer ERROR). place_swig/place_edit gained `add_text` (idempotent board-frame silk text) + `move_text` (refdes/value fields), independently sexpdata-verified incl. rotated parents; 9 tests. Drove ~50 move_text refdes sweeps + 3 boards' functional silk packages. fixer.md/fix_dispatch/SKILL.md updated. |

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

## S5 - Verification suite part 2 + check orchestration (2026-07-22) - DONE

**Built** (all on geom.py + checklib.py, S2 normalized-violation schema, spec 6 CLI contract):
- `scripts/check_diffpair.py` - per pair (constraints.json["diff_pairs"] or auto-discovered by
  name suffix): length SKEW (mm + ps) on the BRANCH-FREE trunk (segment-graph Dijkstra between the
  two matched pad terminals - a series-R/pull-up stub joins mid-segment, lands in its own graph
  component, and is naturally excluded); UNCOUPLED length (run of either trace whose partner is
  >coupling_max away); gap histogram (reported, never gated); via symmetry. Catches diffpair-skew.
- `scripts/check_silk.py` - parses silk itself (geom is copper-only): top-level gr_*, footprint
  fp_*, and `(property "Reference"/"Value" ...)` refdes/values, transformed fp_pos+R(-fp_angle).local
  with ABSOLUTE text angle. Silk-over-pad = pad CENTRE under the silk OR silk covers >=50% of the pad
  (touch-only false-positives at the 0.10 mm golden margins); text legibility (height/thickness).
  Catches silk-over-pad.
- `scripts/check_creepage.py` - IPC-2221 Table 6-1 same-layer clearance for net pairs >30 V apart
  (external-uncoated / internal columns + >500 V linear formula; verified values, see LEARNINGS
  research file). Voltage-owner dedup attributes each pair to the higher-|V| net.
- `scripts/check_thermal.py` - theta_JA(area) screen: heatsink copper = the net's copper WITHIN a
  ~1 in reach disk of the part (a distant same-net pour is NOT its heatsink), summed over layers,
  clamped at A_SAT; rise = P*theta_JA; needs-vias flag when the target is below the copper-alone
  (clamped) floor.
- `scripts/check_pdn.py` - per power rail: undecoupled (error) / no-bulk-reservoir (warning); ceramic
  presence reported but NOT gated (input/bulk rails legitimately carry only bulk - the goldens' +5V /
  VBUS do). Reuses check_decoupling.parse_farads.
- `scripts/verify_all.py` - runs all 8 checks (3 S4 + 5 S5) as parallel subprocesses, each ->
  reports/checks/<name>.json, merged to a stable summary (documented in-file). Skips (not fails)
  checks whose inputs are absent; deletes any stale per-check report before each run.
- `scripts/cluster_violations.py` - groups violations by (net, kind, spatial region) into
  fixer-dispatchable clusters with a bounding region + fixer-domain hint.
- `reference/gates.yaml` + `gate.py`: added the `verify` gate (tool: verify -> runs verify_all on the
  board, taking constraints.json/decoupling.json from the board's dir; its {violations,counts}
  summary gates identically to erc/drc - fail on error severity).
- `tests/test_checks_s5.py` - 60 tests: pure (IPC-2221 table, theta_JA model, pair discovery,
  trunk/uncoupled, silk bbox/over-pad, cluster grouping), corpus (3 goldens x 5 checks clean +
  verify_all clean; diffpair-skew and silk-over-pad caught with manifest coords; every mutant a
  negative control on the checks it does not own; full-manifest-coverage via verify_all), CLI/schema
  contract, and a regression per adversarial-review bug (below). 1 smoke (verify_all < 30 s).

**Acceptance evidence:** all three goldens clean under every S5 check AND the merged verify_all
(status pass); diffpair-skew caught (/USB_DP//USB_DM, uncoupled 11.6 mm > 5.0) and silk-over-pad
caught (D1 pad 1 at [132.44,129.5]); full-manifest-coverage test confirms every mutant whose check
exists by S5 (4 S4 + diffpair + silk) is caught by its designated check when the whole suite runs;
cpl-rotation stays dfm_check's (S12). verify_all on rf4 = 0.89 s. `check.cmd` green: **273 passed**,
check_env exit 0.

**Standards research (verified, filed to ai-library/pcb-verification-standards-2026):** IPC-2221
Table 6-1 clearance (external-uncoated / internal + >500 V formula; DC-or-AC-peak, differential) and
a theta_JA-vs-copper-area + thermal-via heuristic, both adversarially re-checked (a 3-agent workflow;
values embedded with source comments). kicad-happy has no creepage/thermal/silk/pdn analyzers.

**Adversarial review (multi-agent workflow) - 10 confirmed bugs found + fixed + regression-tested:**
(1) verify_all read a STALE per-check report when a check errored this run -> unlink before run;
(2) name auto-discovery mis-paired H/L and single-char P/M nets -> dropped those tokens, USB via
DP/DM; (3) thermal heatsink area used the net-WIDE largest layer (a distant pour inflated it) ->
local reach-disk; (4) a diff pair with one unrouted half emitted NaN (invalid JSON, silently disabled
the check) -> not-routed guard; (5) creepage aborted the whole check (exit 2) on one absent listed
voltage net -> skip it; (6) a named diff pair with an absent net aborted the whole check -> per-pair
warning; (7) explicit `diff_pairs: []` triggered auto-discovery -> honor the empty key; (8)
single-copper-layer board crashed epsilon_between (div0) -> FR4 fallback; (9) a silk graphic lacking
both stroke and width crashed the check -> safe width helper; (10) check_pdn dropped micro-sign / RKM
cap values -> parse_farads accepts µ/μ. Refuted findings (7) left as documented by-design.

**Deviations from spec/plan (with reasons):**
1. Spec calls the diff-pair check "skew"; the corpus mutant is a COUPLING defect (meander on the
   SHORTER net -> raw length skew goes DOWN). Caught by uncoupled length, not length matching; both
   reported. Gap "deviation histogram" is report-only (a legit pair fans out at pad breakouts).
2. check_creepage / check_thermal have NO mutant (corpus has no >30 V nets or thermal constraints):
   they are clean-on-goldens by construction and proven by synthetic fixtures. Standards values are
   the correctness anchor. check_pdn ceramic-per-rail is report-only (would FP on the goldens' input
   rails) - spec's "bulk+ceramic per rail" softened to bulk/undecoupled gating.
3. check_silk parses silk in its own module rather than extending geom.py (geom stays copper-only;
   S12 dfm_check may promote silk parsing if it needs the same geometry). Text boxes are approximated
   (calibrated vs pcbnew), so over-pad is judged by pad-centre-in-silk / >=50% area, not bbox touch.
4. verify's gate tool derives constraints.json/decoupling.json from the BOARD's directory (pipeline +
   corpus layout); mutants are tested via verify_all with explicit paths, not the gate.

**Interface notes for later steps:**
- verify_all summary schema (stable): {script, board, status pass|violations|error, counts{total,
  by_severity, by_source, by_check}, checks{<name>:{status pass|violations|error|skipped, counts,
  report, reason?, error?}}, violations[...]}. S13 orchestrator reads this at the P8 gate; S12 can
  add its dfm violations to the same shape.
- New violation kinds (for cluster_violations FIXER_HINTS + S13 fixer dispatch): diffpair_skew,
  diffpair_uncoupled, diffpair_via_asymmetry, diffpair_missing_net, silk_over_pad, silk_illegible,
  silk_thin, creepage, thermal_area, thermal_vias, pdn_undecoupled, pdn_no_bulk.
- constraints.json shapes S5 consumes (P2/S7/S13 generate): diff_pairs[{p,n,gap_mm?,max_skew_mm?,
  max_uncoupled_mm?,coupling_factor?}]; voltages[{net,voltage}]; thermal[{ref,power_w,net,dt_c?,
  min_vias?}]. Absent keys -> that check no-ops cleanly. decoupling.json (S7 emits) drives check_pdn.
- cluster_violations groups a verify_all summary (or any {violations} report) by (net, kind, region);
  each cluster carries a bbox + fixer domain. gate.py `verify` gate is the P8 [G:checks] edge.

**New verify-later items:** none. (Creepage/thermal accuracy is by-design ±30% screen quality; V9
unchanged - cpl-rotation still S12's dfm_check to catch.)

## S6 - Parts, library, datasheet tooling (2026-07-22) - DONE

**Smoke tests first (V5 + easyeda2kicad, all live-verified on this host before building):**
- **V5 RESOLVED cleanly.** The pinned easyeda2kicad 1.0.1 `EasyedaApi` already wraps an ANONYMOUS
  JLCPCB parts search (`search_jlcpcb_components`) returning {lcsc, model, package, stock, type
  Basic/Extended, price, price_breaks, datasheet, attributes} - NO credential (18783 hits for
  "100nF 0603 X7R"; C14663 Basic stock 88M). `get_cad_data_of_component` pulls CAD JSON. The
  spec's credentialed api.jlcpcb.com is unnecessary for search.
- Full export layout confirmed: `<base>.kicad_sym` + `<base>.pretty/<fp>.kicad_mod` +
  `<base>.3dshapes/`. Footprints emit in LEGACY `(module ...)` format but LOAD in KiCad 10
  (`kicad-cli fp upgrade` -> `(footprint ...)`; `fp export svg` renders - needs the output dir to
  pre-exist). Courtyard presence is part-dependent (C1525 0402 HAS one). All in LEARNINGS [parts].
- No PDF lib was installed; added `pypdf==6.14.2` (pure-python) + pinned `jsonschema==4.26.0`
  (was transitive) to requirements.txt/lock + check_env REQUIRED_PACKAGES.

**Built** (all under `.claude/skills/ai-ee/`):
- `scripts/parts_search.py` + `scripts/lib/partslib.py` - ranked LCSC/JLC search. Source ladder:
  live anonymous JLCPCB search -> `--db` jlcparts SQLite cache -> web-search hint (exit 2 when
  offline + no db). Ranking = Basic-first, then stock desc, then price asc (SPEC P3 "prefer Basic").
  Parametric filters (--basic-only/--package/--min-stock/--max-price/--brand/--contains, and
  generic `--filters k=v`). ASCII-safe JSON (ensure_ascii; JLC descriptions carry +/-, mu).
- `scripts/lib_pull.py` + `scripts/lib/fplib.py` - easyeda2kicad wrapper (subprocess `--full`),
  registers the pulled libs in <project>/fp-lib-table + sym-lib-table (idempotent, portable
  ${KIPRJMOD}/../lib/... URIs via os.path.relpath), reports courtyard presence per footprint,
  `--verify-load` confirms KiCad parses them (`fp export svg`). fplib parses BOTH `(module)` and
  `(footprint)` formats into pads (rotation-correct centers, NPTH excluded from copper) + layer
  presence - shared with fp_verify.
- `scripts/datasheet_extract.py` - owns the datasheet-extract JSON Schema (Draft 2020-12: mpn,
  pinout[{pin,name,type}], decoupling, land_pattern{pad_count,pitch_mm,pad_size_mm,...},
  exposed_pad, layout_notes, abs_max). `--pdf` pulls per-page text (pypdf) + emits a grounding
  payload {text_by_page, schema, template} for the LLM datasheet-extractor agent; `--validate`
  schema-checks a filled extraction (exit 0/1 with precise error paths); `--schema` dumps it.
- `scripts/fp_verify.py` - footprint pads vs datasheet land_pattern (on fplib + checklib normalized
  violations): pad_count/pin1/pitch = error, pad_size/courtyard-absent = warning (warnings do NOT
  fail the gate - exit 1 only on error severity). Emits an SVG overlay (rotated pad rects + size
  labels, mismatches reddened) for human review.
- Fixtures `tests/fixtures/parts/cap0402_{legacy,modern}.kicad_mod` (real C1525 pull + its
  kicad-cli-upgraded twin - locks dual-format parsing).
- `tests/test_parts.py` - 33 tests: 27 hermetic (fplib dual-format + NPTH + symbol_names;
  fp_verify good/pad_count/pitch/pin1/courtyard-warning/size-warning/bad-json-exit2 on both fixture
  formats; datasheet schema-valid/validate good+bad+unreadable/pdf-text; partslib normalize+rank+
  filters; parts_search rank/filter/bad-key/offline-exit2/empty-exit0/db-fallback vs a synthetic
  jlcparts DB; lib-table idempotent registration) + 6 `net` (5-category live search returns
  in-stock hits: STM32F103C8T6 / AP63203 / USB Micro B / 8MHz crystal / 10k 0603; live C1525 pull
  loads in KiCad). `net` tests skip when the endpoint is unreachable (offline check.cmd still green).

**Acceptance evidence:** all five S6 accept criteria met live - 5-part search returns in-stock LCSC
hits (net tests green); pulled footprint loads in KiCad (load_check.ok True via fp export svg);
fp_verify flags a corrupted footprint (pad-count/pitch/pin1) exit 1 and passes correct ones exit 0
on BOTH legacy and modern formats; datasheet JSON validates (good exit 0, bad exit 1 with 5 precise
schema errors). `check.cmd` green: **188 passed** (155 prior + 33), check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. parts_search's primary source is the ANONYMOUS JLCPCB search, not the spec's "credentialed
   Parts API" (V5) - the credential is unnecessary for search and would gate the whole step on an
   access application. The credentialed api.jlcpcb.com is deferred to S12 ordering (payment path).
2. jlcparts SQLite fallback is implemented + unit-tested against a SYNTHETIC db (yaqwsx schema:
   components{lcsc,mfr,package,basic,description,stock,price-json}); no real jlcparts DB ships on
   this host, so real-DB behavior stays verify-at-first-use if one is dropped in. Column-tolerant.
3. datasheet_extract splits deterministic vs LLM work per SPEC 6.1: the SCRIPT owns the schema +
   PDF-text extraction + validation; the actual field extraction is the S13 datasheet-extractor
   agent's job (fed by the --pdf grounding payload). Image-only PDFs yield ~0 text -> agent reads
   the pages directly (noted in the payload).
4. Added two dependencies (pypdf, direct jsonschema pin) - the venv had no PDF lib and jsonschema
   was only transitive. Both pure-python, pinned, in check_env now.
5. fp_verify does courtyard-presence + pad geometry diff, not the LEARNINGS-suggested full "per-part
   DRC baseline" (that needs a scratch board + kicad-cli DRC per part - heavier; belongs to the
   librarian agent flow at S13, or a later fp_verify --drc-baseline). Warnings are non-blocking by
   design so a legit courtyard-less part doesn't hard-fail the gate.
6. `net`-marked live tests run in the default suite (like S3/S4 smoke tests) but SKIP when the
   JLCPCB endpoint is unreachable, so an offline check.cmd does not fail on a third-party API.

**Interface notes for later steps:**
- parts_search candidate shape (superset of SPEC P3 parts.json): {lcsc, mpn, brand, description,
  package, category, type, basic:bool, stock:int, price, price_breaks, min_qty, datasheet, url,
  attributes, rank}. part-sourcer (S13/P3) consumes this; datasheet URL feeds datasheet_extract.
- datasheet-extract JSON schema is the CONTRACT the schematic agents (S7/P4) wire against and
  fp_verify checks land patterns against. `datasheet_extract.py --schema` is the single source of
  truth (pin type enum, land_pattern fields). check_decoupling's decoupling.json (S4) is separate
  board metadata; this datasheet JSON is the per-part ground truth.
- fplib.parse_footprint(path) -> Footprint{name, pads[Pad{number,ptype,shape,at,size,layers,
  is_copper}], layers_present, copper_pads, has_courtyard, has_layer_kind(kind)}. Reusable by S9
  placement (courtyard/pad geometry) and S12 DFM. Handles legacy+modern, NPTH-excluded-from-copper.
- lib_pull registers ${KIPRJMOD}-relative lib-table URIs; board_init (S8) creates the project the
  tables live in. lib nickname default "aiee"; symbol/footprint names come from EasyEDA (e.g.
  C1525 -> footprint "C0402").
- fp_verify emits the S2 normalized violation schema (source "check.fp_verify"; kinds pad_count,
  pin1_missing, pad_pitch, pad_size, no_courtyard) so cluster_violations.py / verify_all.py (S5)
  merge it uniformly; error-severity => exit 1, warnings alone => exit 0/pass.

**Note (not S6 scope):** the working tree carries UNCOMMITTED files from other steps
(check_diffpair.py, check_silk.py, board_swig.py [S5]; board_init.py, rules_gen.py, impedance.py,
reference/{jlc_capabilities.yaml,jlc_rotations.csv,stackups.yaml} [S8]) - evidently WIP from a
parallel/prior session. NOT touched or committed here; the S6 commit stages only S6 paths. Those
steps are still "pending" on the status board.

**New verify-later items:** none. (V5 resolved above; jlcparts-real-DB and credentialed ordering
API remain future-verify but are covered by existing registers / S12.)

## S7 - Schematic generation (2026-07-22) - DONE

**Smoke tests first (V2 completion, live 10.0.3):** kicad-sch-api 0.5.6's hierarchical API
(add_sheet / add_sheet_pin / add_hierarchical_label) DOES serialize - unlike add_global_label
(still a silent no-op) - and a probe 2-sheet design came out ERC-clean with correct cross-sheet
netlist connectivity on the first try. Path chosen: kicad-sch-api native output, NO `sch upgrade`
step needed (files load as saved). Sheets are dicts; sheet-pin positions absolute (left-edge
`position_along_edge` measured from sheet bottom). LEARNINGS [python][erc][kicad-cli] x3.

**Built:**
- `scripts/schlib.py` - the P4 generation library over kicad-sch-api (S1 sch_build conventions
  lifted: grid snap+assert, outward stub+local-label wiring, rail clusters, pin-number fixups,
  minimal-pro authority). API: `Sheet` (add_component w/ `expect` pin-name insurance,
  wire_pin/wire_pins, power_flag / power_symbol_at_pin, hier_pin (pin-stub and free-cluster
  variants), place_ic_with_decoupling, save, emit_decoupling), `Project` (add_sheet stitching:
  sheet pins from the child's registered hier_pins, root-side label wiring; merged decoupling),
  `write_project`, `apply_pin_number_fixups`, `pin_table`. CLI: `--pins LIB_ID` prints a symbol
  pin table (grounding aid for P4 agents; JSON, exit 0/2, call-time ksa noise suppressed).
- `scripts/netlist_audit.py` - netlist-vs-constraints audit + netlist-vs-netlist identity.
  Audit: missing_net (error; all constraints net refs incl. high_speed reference layer maps),
  diffpair_naming/diffpair_unpaired (warnings; strong suffixes _P/_N, DP/DM, D+/D-),
  power_no_consumers / power_undeclared (warnings; pintype power_in scan, ground-name exempt),
  dangling_net (warning; single-pin non-unconnected-* = label-typo signature), decoupling
  metadata_mismatch (errors; value drift = warning). Warnings alone do NOT fail (fp_verify
  precedent). `--compare B.net`: strict identity (names + (ref,pin) memberships; renames
  classified, still failures). `--sch X.kicad_sch` exports via kc.py first. sexpdata parser
  (netlists are multiline).
- Generator-pattern fixtures (committed source AND build outputs):
  `tests/s7_regen/blinky2/kicad/gen/root.py` -> blinky2.kicad_sch/.kicad_pro + decoupling.json +
  blinky2.net; `tests/s7_regen/blinky2/golden.net` (reference export of the committed golden);
  `tests/s7_regen/hierdemo/kicad/gen/{root,power_sheet,load_sheet}.py` -> 3-sheet hierdemo
  (hier signal x2 variants, global rails, cross-child net, child-internal "/load/LED_K" net,
  per-sheet #PWR ranges via pwr_base) + constraints.json audit fixture.
- `tests/test_schgen.py` - 29 tests: 23 hermetic (committed artifacts + pure venv: golden netlist
  parse, comparator identity/diffs/rename classes, audit pass on regen + hierdemo, every audit
  violation kind + severity + exit codes, emitted decoupling == S4 golden fixture semantically,
  check_decoupling ON THE GOLDEN BOARD driven by the S7-EMITTED metadata, schlib pure helpers) +
  6 smoke (live rebuild -> ERC 0 -> re-export -> identical to golden AND to committed outputs
  [committed-artifact freshness guard], hierdemo full topology assert, --sch export path,
  --pins CLI, Sheet validation errors).

**Acceptance evidence (live 10.0.3):** blinky2 regenerated from the schlib generator: ERC
`--severity-all` = 0; netlist ELECTRICALLY IDENTICAL to the committed golden's export (43/43 nets,
same (ref,pin) memberships, incl. all 32 unconnected-(...) NC nets); audit passes (0 violations;
+3V3 5 power_in / 1 power_out driver). Emitted decoupling.json == the hand-written S4 fixture on
(cap,ic,pin,rail,value) x6, and S4's check_decoupling passes on the golden BOARD fed the emitted
file. hierdemo: ERC 0, netlist exactly the designed topology (global +3V3 across sheets, /VIN and
/CTL through both hier_pin variants), audit 0. `pytest` green: **301 passed** + check_env exit 0
(1 deselected - parallel-S9 WIP, below).

**Deviations from spec/plan (with reasons):**
1. Hier labels bind by wire geometry, not name-merge: hier_pin's free-cluster variant writes its
   own wire + local label + hier label so correctness never rests on same-sheet label-name-merge
   semantics.
2. Decoupling metadata records FINAL netlist names, which differ from sheet-local wiring labels
   for root-local ("/NAME") and hier-crossed nets: explicit `rail_net`/`gnd_net` entry overrides
   (inference would be fragile); netlist_audit --decoupling is the drift catcher - it CAUGHT this
   exact mismatch on hierdemo's first build (rail "VIN" vs net "/VIN").
3. Audit's "power-tree connectivity" is consumer/declaration-based (power_in scans), NOT
   driver-based: #PWR/#FLG symbols are excluded from netlists entirely, so driver presence is
   ERC's job (PWR_FLAG rules), not the netlist's. Ground-named nets (GND*/;*GND/VSS*/0V) exempt
   from power_undeclared.
4. `_P/_N` pairing warnings use only the strong suffix families (_P/_N, DP/DM, D+/D-), not
   check_diffpair's bare +/-, P/N tokens (every net ending in P would FP). Naming-convention
   violations are warnings, not errors (corpus itself uses DP/DM).
5. blinky2 regen is FLAT (root-sheet, like the golden) - hierarchy would change net names and
   break the identity acceptance; the hierdemo fixture proves the hierarchical machinery instead.
6. sch_build.py (S1 corpus generator) intentionally NOT refactored onto schlib - the corpus stays
   frozen; schlib lifted its proven code instead.

**Interface notes for later steps:**
- Generator pattern for P4 agents (S13): per-sheet `kicad/gen/<sheet>.py` exposing
  `build() -> schlib.Sheet`; root generator stitches via `schlib.Project.add_sheet(child, at,
  size, nets=[...])` and `Project.save(out_dir, decoupling=path)`. Sheet generators declare
  cross-sheet nets with `hier_pin`; rails ride power symbols (global, no sheet pin). Refs must be
  unique ACROSS sheets (allocate ranges per sheet, incl. pwr_base). tests/s7_regen/* is the
  working reference implementation.
- decoupling.json emission: place_ic_with_decoupling entries -> associations in EXACTLY the S4
  contract shape ({cap, ic, pin, rail, value, gnd?, class?, max_dist_mm?, max_loop_nh?});
  rail/gnd take rail_net/gnd_net overrides when the netlist name differs from the wiring label.
  S9 satellite locking reads the same associations (usbbuck4's placement.groups xtal workaround
  can retire once its design has S7 metadata).
- netlist_audit is the P4 gate companion: `--sch` (or `--netlist`) + `--constraints`
  [+ `--decoupling`]; exit 1 only on errors. `--compare` guards regenerations. Payload:
  checklib report shape + facts {nets, components, unconnected_pins, constraint_nets_checked,
  decoupling_associations, power[{net,nodes,power_in,power_out}]}; violation kinds:
  missing_net, diffpair_naming, diffpair_unpaired, power_no_consumers, power_undeclared,
  dangling_net, metadata_mismatch, netlist_diff.
- schlib CLI `--pins LIB_ID` = symbol pin-table grounding for P4 agents before wiring.
- Coordination note: this session ran in parallel with an in-flight S9 session (uncommitted
  place_* scripts, gates.yaml `place` gate, golden constraints placement blocks in the tree).
  S7 commits ONLY S7 paths (S6 precedent); test_kc_gate.py::test_gates_yaml_valid currently
  fails on S9's WIP gates.yaml (tool `place` unknown to the committed test) - that test is S9's
  to green when it lands. Everything else: 301 passed with that single test deselected.

**New verify-later items:** none. (V2 resolved above.)

## S8 - Board setup and reference data (2026-07-22) - DONE

**Smoke-tested the load-bearing claims first (all live 10.0.3), then built on them:**
1. kicad-cli AUTO-LOADS `<board>.kicad_dru` next to the board; a violated custom rule puts its
   NAME in the violation description (`rule 'NAME'`), which kc.py surfaces in `msg`. DRU condition
   net token is `A.NetName` (`A.Net` silently matches nothing); LATER rule wins for same-constraint
   collisions -> baseline first, per-net last. (LEARNINGS [kicad-cli][drc].)
2. No kicad-cli netlist->board path; SWIG place-from-netlist (FootprintLoad + pad-net from netmap,
   bbox shelf-pack) is schematic-parity-clean with only expected unconnected_items. Bundled python
   has no yaml -> venv driver + bundled-python worker via JSON. (LEARNINGS [swig].)
3. SWIG can't serialize a stackup on 10.0.3 -> board_init TEXT-injects the (stackup) block from
   stackups.yaml; geom reads it authoritative (assumed=False) and kicad-cli DRC still loads.
   (LEARNINGS [kicad][swig][geometry].)

**Built** (all under `.claude/skills/ai-ee/`):
- `reference/jlc_capabilities.yaml` - fab minimums per layer count / copper weight (2/4/6-layer,
  1oz/2oz) transcribed from jlcpcb.com capabilities + ayberkozgur cross-check, cited + dated.
  Consumed by rules_gen (baseline) and S12 dfm_check.
- `reference/stackups.yaml` - JLC physical stackups (JLC2313_1.6, JLC04161H-3313 with exact
  cited dielectric/copper thicknesses + epsilon_r/loss_tangent) + a `controlled_impedance` table
  (outer microstrip 50R SE, 90R/100R diff) COMPUTED by impedance.py (flagged, not JLC-transcribed).
  `defaults` maps layer count -> stackup; board_init emits the block, rules_gen reads impedance.
- `reference/jlc_rotations.csv` - CPL rotation corrections vendored from the community tables
  (bennymeg/JLC-Plugin, KiBot db), regex,rotation; first-match-wins; consumed by S12 bom_cpl.
- `reference/design_rules/{jlc_2layer_1oz,jlc_4layer_1oz}.kicad_dru` - baseline fab-floor templates
  = rules_gen `--baseline-only` output (drift-guarded by a test).
- `scripts/lib/impedance.py` - IPC-2141A microstrip + edge-coupled diff approximations
  (solve_width, diff_pair pins a tight-coupling gap + solves width, geometry_for).
- `scripts/lib/board_swig.py` - BUNDLED-python SWIG worker: netlist -> placed board, shelf-pack,
  outline (auto bbox+margin | fixed WxH), corner mounting holes marked board_only (parity ignores).
- `scripts/board_init.py` - venv driver: parse netlist (sexpdata), pick stackup, drive the worker,
  inject stackup, write minimal .kicad_pro, self-check (parity==0 AND setup-violations==0, excluding
  the unrouted board's unconnected_items). `--schematic` copies the sch next to the board for parity.
- `scripts/rules_gen.py` - constraints.json -> `<board>.kicad_dru` (baseline from capabilities +
  per-net power widths via check_current IPC-2152 + per-pair diff_pair_gap via impedance.py) and
  (optional --pro) net classes (Power, Diff<Z>) + board.design_settings.rules minimums. `--baseline-only`
  regenerates the templates.
- `tests/test_board_setup.py` - 25 tests (19 pure: reference-data validity, template drift guard,
  impedance reference/monotonic/round-trip, rules_gen baseline/power/diff-detect/ordering/net-classes,
  netlist parse + missing-fp, stackup-block, helpers; 6 smoke: board_init end-to-end, rules_gen clean
  golden, rules_gen ENFORCED, baseline templates FP-free x2 boards, --pro keeps board clean).

**Acceptance evidence (live 10.0.3):**
- board_init from golden board 2's netlist -> initialized 4-layer board: schematic parity 0,
  0 setup violations (no courtyard/short/mask/silk), 63 expected unconnected_items, ~54x68 mm outline,
  4 board_only mounting holes, stackup injected + geom reads assumed=False (F/In1/In2/B.Cu).
- rules_gen from usbbuck4 constraints: clean golden stays 0 violations (no false positives, all rules
  accepted); a +3V3 track narrowed 0.25->0.15 mm fails DRC with exactly `rule 'aiee_pwr_width_3V3'`
  (track_width, net +3V3) and the generic floor does NOT also fire (0.15 > 0.1016) - proves both
  enforcement and specific-overrides-floor ordering.
- `pytest` green: **213 passed** (188 prior + 25); check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. board_init builds the board via SWIG `CreateEmptyBoard` (no kicad-cli netlist import exists), not
   from a blank `templates/*.kicad_pcb` - full programmatic control of layer count / nets / outline.
   templates/ stays a spec artifact for later hand-use. Origin/grid left at KiCad defaults (0,0;
   grid is a UI setting, immaterial headless).
2. "passes DRC setup checks" interpreted as parity==0 AND zero non-unconnected DRC violations: an
   unrouted, unplaced-proper board necessarily has unconnected_items (routing is P7) - those are
   excluded from the setup pass criterion, everything else (courtyard/short/mask/setup) must be clean.
3. rules_gen power-width rule uses OUTER-copper (1oz) IPC-2152 ampacity as a single per-net
   track_width rule. A power net deliberately routed on a thin INNER layer would be under-constrained
   by the DRU (golden power is outer tracks + inner POURS, so no FP); the per-layer ampacity backstop
   is check_current (S4). Documented; layer-scoped rules are a possible refinement.
4. Controlled-impedance geometry is COMPUTED (impedance.py), not transcribed from JLC's calculator;
   outer microstrip only, no inner stripline. Physical stackups are cited-exact. -> V12.
5. rules_gen does NOT emit keepout (antenna/mounting) or courtyard rules: keepouts need mechanical
   geometry from P2/P6 (not available from constraints alone at board setup), and courtyard overlap
   is already a built-in KiCad DRC check (courtyards_overlap) - an explicit rule is redundant.
6. No new gates.yaml entry for P5: board setup's acceptance is board_init's internal self-check
   (parity + setup violations); the routed-board DRC gate (drc_routed, S2) is the phase gate at P7.
   The existing `drc` gate intentionally fails an unrouted board (unconnected errors), so it is not
   the P5 gate.

**Interface notes for later steps:**
- `board_init.py --netlist n.net --name B --out DIR --layers 2|4 [--stackup NAME] [--outline auto|WxH]
  [--mounting-holes N] [--schematic s] [--fp-lib DIR]` -> `DIR/B.kicad_pcb` + `B.kicad_pro`.
  Importable: `parse_netlist(path) -> ([{ref,value,fp}], {"REF.PAD":net})`, `build_stackup_block`,
  `inject_stackup`, `self_check`. S9 places into this board (parts pre-loaded, nets assigned, unrouted).
- `rules_gen.py --constraints c.json --layers N [--copper-oz X] [--stackup NAME] --out-dru B.kicad_dru
  [--pro B.kicad_pro] [--baseline-only]`. Rule names are `aiee_*` (floors `aiee_*_floor`,
  power `aiee_pwr_width_<net>`, diff `aiee_diff_gap_<base>`); violation msgs carry `rule 'NAME'`.
  constraints.json shape extension (optional, back-compat with S4): high_speed entries may add
  `impedance_ohm`; a top-level `diff_pairs: [{p,n,base?,impedance_ohm?}]` overrides name-suffix pairing.
- `reference/jlc_capabilities.yaml` design_rules[<layers>layer_<oz>oz] is the S12 dfm_check contract;
  `reference/stackups.yaml` stackups[NAME] (stack + controlled_impedance) is board_init + rules_gen's;
  `reference/jlc_rotations.csv` (regex,rotation, first match wins) is S12 bom_cpl's.
- `scripts/lib/impedance.py`: `solve_width(z0,h,t,er)`, `diff_pair(zdiff,h,t,er[,width|gap])`,
  `geometry_for(profile,h,er,cu_oz)`. First-order (V12); S5 check_diffpair can reuse for targets.
- board_swig.py is bundled-python ONLY (imports pcbnew); invoked via env.find_kicad_python. Mounting
  holes get FP_BOARD_ONLY|FP_EXCLUDE_FROM_POS_FILES|FP_EXCLUDE_FROM_BOM so parity/CPL ignore them.

**New verify-later items:** V12 (impedance approximation vs JLC calculator; outer microstrip only).

## S9 - Placement: seed, metrics, edit ops (2026-07-22) - DONE

**Edit-path decision first (V4/V8, plan-mandated):** SWIG bundled python, NOT kipy/IPC.
Evidence: (a) the S0-verified sandboxed-GUI IPC path REGRESSED on this host - smoke_ipc.py
(unchanged) now gets "ApiError: KiCad is not ready to reply" for the whole 45 s window, verdict
`unavailable`; a dedicated V8 probe (launch pcbnew on a golden copy, kipy connect, move+rotate via
FootprintInstance/update_items) never connected in 60 s; (b) library research
(headless-pcb-routing-2026): kipy on KiCad 9/10 REQUIRES a GUI instance, headless IPC lands in
KiCad 11 (~2027); (c) SWIG is headless, process-per-invocation, and already carries board_init
(S8). kipy's edit API surface EXISTS (position/orientation setters + update_items + save) - it is
the KiCad-11 migration target, recorded in V8. LEARNINGS [ipc], [swig].

**Built** (all under `.claude/skills/ai-ee/`, on the S2 normalized-violation schema + spec 6 CLI
contract):
- `scripts/lib/placelib.py` - the placement model geom.py deliberately lacks: parses footprint
  blocks into MOVABLE records {ref, fpid, pos, angle, side, attr flags, locked, pads with LOCAL
  offsets, courtyard polygon per side (fp_rect/fp_line/fp_circle/fp_poly/fp_arc + polygonize;
  pad-bbox+0.25 fallback flagged courtyard_missing)}; abs = fp_pos + R(-angle).local (S3
  transform; flip stays baked, parser never mirrors); center-based placement (place_center
  compensates origin-vs-body offset - prior-attempt 1x20-header trap); outline/rule_areas/copper
  come from geom.load_board. Cluster builder (decoupling.json associations -> cap satellites with
  target pins; constraints placement.groups -> explicit satellites; edge-declared satellites pin
  their whole cluster; missing refs warn, never crash). Legality -> normalized violations:
  courtyard_overlap (same-side pairs + THT vs both sides), outside_outline (movable only;
  declared-edge parts exempt down to ON_BOARD_MIN=0.25 on-board fraction - calibrated on the rf4
  edge-mount SMA's 35%), edge_violation (courtyard > EDGE_TOL=2.5 mm from declared edge),
  keepout_violation (constraints keepouts + board rule areas), courtyard_missing (warning).
  Metrics: HPWL (per-net bbox half-perimeter), MST flight-line crossings, congestion grid
  (cell rasterization of MST edges), all deterministic.
- `scripts/place_metrics.py` - the P6 gate tool: legality violations + decoupler DISTANCE
  violations (reuses S4 check_decoupling.check_association verbatim, filtered to
  kind=decoupler_distance - loop/via inductance stays P8's, it needs routing) + `metrics` facts
  {counts, hpwl, crossings, congestion, decoupling facts, utilization}. Sidecars default from the
  board's directory (gate.py convention). Exit 0/1/2.
- `scripts/place_edit.py` + `scripts/lib/place_swig.py` - the pipeline's ONLY placement writer
  (SPEC sec 4). ABSOLUTE ops {place|move|rotate|flip|lock} (idempotent by construction; flip takes
  a target side, never toggles). Driver: strict schema validation -> ref pre-flight -> stage copy
  in a scratch dir INSIDE the board's dir -> bundled-python worker (mmToIU rounding, not
  truncating FromMM; Flip(pos, True) - no FLIP_DIRECTION enum on 10.0.3; saves ONLY if every op
  applied) -> driver re-parses the staged file and verifies every op landed (pos 1e-3 mm, angle
  mod-360 0.05 deg - SetOrientationDegrees normalizes 270 to -90, side, locked) -> os.replace
  swaps just the .kicad_pcb back (same volume = atomic; real .kicad_pro/.kicad_prl never touched,
  test-guarded). ANY failure = original board byte-identical. Importable apply_ops() for seed/S10.
- `scripts/place_seed.py` - SPEC P6 stage 1: hard constraints -> satellite clusters -> block
  adjacency. Satellite slots in the anchor's LOCAL frame (rotate with the anchor): outside the
  courtyard facing their target pin, 2-pad parts rotated so the shared-net pad points at the pin,
  deterministic perimeter nudging. placement.edges pins connector clusters to edges (explicit rot
  or auto: body-overhang direction from pads-vs-courtyard centroid offset, snapped 90 deg;
  symmetric parts keep their angle; courtyard flush; explicit pos fraction or even distribution).
  Free clusters: connectivity-weighted (GND 0.2/power 0.5/signal 1.0) classic Fruchterman-Reingold
  (attraction d^2/k - the linear-in-d first cut scattered singletons and made seed HPWL WORSE than
  the shelf pack, LEARNINGS [placement]) with deterministic circle init, no RNG; then largest-first
  spiral grid legalization against courtyards/interior/keepouts. Emits ops for place_edit;
  `--apply` applies + re-checks legality on the saved file. Exit 0/1/2.
- `reference/gates.yaml` + `gate.py`: `place` gate (tool: place -> place_metrics on the board with
  its sidecar constraints/decoupling; fails on error severity). cluster_violations FIXER_HINTS +=
  the 6 placement kinds -> "placement" fixer domain.
- `tests/test_place.py` - 45 tests: 40 pure (parsing incl. S3 C10 transform probe pinned,
  courtyard rect/lines/rotation, center-based placement at 4 angles, clusters incl. double-claim/
  missing-ref/edge-satellite promotion, legality per kind incl. board_only exemptions, HPWL/
  crossings/congestion hand-computed, op schema accept + 8 reject cases, expected-state folding,
  rollback-on-missing-ref, facing rotation, auto edge rotation, synthetic seed legal+deterministic+
  HPWL-improves, too-small board exit 2, goldens x3 legality-clean, golden metrics clean,
  decoupler-moved mutant flagged via place_metrics, place gate wired) + 5 smoke (edit
  apply/idempotency/pro-preservation, worker-failure saves nothing, S9 acceptance: netlist ->
  board_init -> seed --apply on usbbuck4, seed determinism on corpus, <30 s timing).

**Acceptance evidence (live 10.0.3):**
- Golden board 2 from scratch: usbbuck4 netlist -> board_init (shelf pack, HPWL 832.6 mm) ->
  place_seed --apply -> 0 legality violations; J1/J2/J3 on their declared left/right/bottom edges;
  U1 centered with its 5 decouplers at their VDD pins (Manhattan 2.5-6.6 mm, all in class), crystal
  + load caps adjacent to the MCU, buck cluster + L1 together, C13 beside J1; HPWL 483.7 mm (42%
  under the shelf pack, within 7% of the hand-placed golden's 452.6); render eyeballed. Metrics
  JSON emitted (hpwl/crossings/congestion/decoupling/utilization).
- Op list: 4-op place/rotate/flip/lock applied + independently verified; re-application idempotent
  (parsed state identical); bad-ref op list -> exit 2, board BYTE-identical; worker-level failure
  saves nothing (exit 3); .kicad_pro byte-identical across edits.
- `gate.py --gate place` PASS on the golden; place_metrics catches the decoupler-moved mutant
  (C1, kind decoupler_distance) as its P6-level echo (P8's check_decoupling remains the owner).
- `check.cmd` green: **347 passed** (301 prior + 45 new + the gates.yaml test S7 left to S9),
  check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. Spec P6.3 says place_edit via "IPC headless; never raw file edits" - IPC headless does not
   exist at this pin (V4/V8 above); SWIG bundled python IS the headless path (still no raw file
   edits - pcbnew owns the file format). kipy/IPC recorded as the KiCad-11 migration target.
2. "Hierarchical-sheet groups arranged by block-diagram adjacency": the corpus goldens are flat,
   so block adjacency = connectivity-weighted cluster graph; sheet-derived grouping slots in when
   P4 designs carry S7 hierarchy (S7's decoupling.json is already consumed; usbbuck4's
   placement.groups xtal fixture stands in for satellite families S7 metadata will declare).
3. Ops are ABSOLUTE only (no relative move/rotate-by): relative ops break idempotent
   re-application, which the plan's acceptance demands; group moves are expanded to per-ref
   absolute ops by the generator (seed does exactly this).
4. place_metrics emits decoupler-distance violations by REUSING check_decoupling's association
   logic (filtered) rather than duplicating a distance path - P6 gate wants distance-only
   (pre-route); loop/via facts are reported as facts but not gated here.
5. The P6 gate's fast-route-completion term (spec ">=98%") requires S10/S11 route feedback -
   the `place` gate covers legality + decoupler distance until then (gates.yaml header documents).
6. Two corpus fixtures extended (usbbuck4 + rf4 constraints.json gained `placement` blocks) so the
   goldens are legality-clean under their own declarations (rf4's edge-mount SMA and usbbuck4's
   edge-overhang J1 are DECLARED, not special-cased). S4/S5 consumers ignore the extra key
   (verified: full suite green).

**Interface notes for later steps:**
- S10 annealer: placelib.PlaceModel IS the in-memory state - mutate fp.pos/fp.angle (or
  place_center) and re-read hpwl/crossings/congestion/legality_violations without file I/O;
  clusters from build_clusters are the move unit (apply_cluster in place_seed shows the transform
  math: satellite slots are anchor-local, abs angle = anchor angle + rel). Write results via
  place_edit.apply_ops (absolute ops, atomic, verified). Seed emits its ops via the same path.
  Metrics are deterministic; HPWL baselines: shelf 832.6 / seed 483.7 / golden hand 452.6 on
  usbbuck4 (the S10 accept bar ">=20% under seed" has real headroom - the spring embed is
  deliberately greedy-legalized, not optimal).
- S13 orchestrator: `gate.py --gate place <board>` = the P6 legality gate (sidecars from the
  board's dir); place_seed/place_metrics/place_edit all emit checklib payloads (status
  pass|violations|error, exit 0/1/2); violation kinds courtyard_overlap/outside_outline/
  edge_violation/keepout_violation/courtyard_missing/seed_unplaced cluster to the "placement"
  fixer domain. The placement agent's edit loop = generate ops JSON -> place_edit --ops (8-iter
  budget per spec P6 stage 3); ops schema documented in place_swig.py docstring.
- constraints.json["placement"] shape (P2/S13 generate): {edges: [{ref, edge:
  left|right|top|bottom, pos? 0..1, rot? deg}], groups: [{name?, anchor, members[]}], keepouts:
  [{rect:[x1,y1,x2,y2]|poly:[[x,y]..], side? front|back|both, reason?}], fixed: [refs]}. Edges are
  render-oriented (top = min y, file coords grow down). All keys optional; absent placement block
  -> pure legality (outline/overlap) only.
- place_edit rejects unknown refs BEFORE touching the board; staged-swap means concurrent readers
  never see a half-applied file. KiCad regenerates UUIDs on every save - never byte-compare
  boards across saves; compare parsed positions (placelib) instead.
- Mounting holes (board_only) and locked/placement.fixed refs are obstacles: never moved, exempt
  from outline containment, still collide.

**New verify-later items:** none. (V4 updated - GUI-IPC regressed on host; V8 resolved negative -
SWIG chosen, kipy = KiCad 11 target.)

## S10 - Placement: annealer with routability feedback (2026-07-23) - DONE

**Built:** `scripts/place_anneal.py` (single file, ~1100 lines) - SA refinement over the S9 rigid
clusters (placelib.build_clusters + place_seed satellite slots ARE the move unit; apply_cluster's
transform math reused for output so ops match seed semantics exactly):
- Engine: incremental cost evaluation over cluster (center, angle) states. Cluster-frame pad
  coordinates precomputed once (pad_abs = center + R(-angle) . q, q folds slot+rel rotation), so
  a move rebuilds only the moved cluster's nets. Raw term totals maintained per move, recombined
  with weights at accept time: weighted HPWL (gnd 0.25 / power 0.6 / signal 1.0), overlap mm^2
  (cluster pairs + fixed obstacles + keepouts + outside-outline, bbox-prefiltered shapely,
  ramped by sqrt(T0/T) so late epochs are effectively legal-only), congestion overflow (MST
  flight-line demand above --cong-cap per 2 mm cell), weighted MST crossings (orientation
  predicate, proper crossings only), rule terms (current_a x HPWL per constraints.power net;
  placement.separation pairs; constraints.thermal spreading). Gnd-class nets are excluded from
  the MST terms (planes carry them). full_sync() every epoch re-derives all totals (float-drift
  kill; incremental==full invariant pinned by test).
- Annealer: moves = translate (window-scaled, grid-snapped) / rotate +-90,180 / swap two free
  clusters / edge-slide + same-edge swap. Edge clusters slide ALONG their declared edge only
  (perpendicular seat preserved from the seed; explicit `pos` = frozen); side flips are not SA
  moves (agent domain, P6 stage 3). Adaptive schedule: T0 = 20x mean uphill delta from sampled
  moves; cooling 0.6/0.9/0.95/0.9/0.75 by epoch acceptance band; TimberWolf window
  W *= (0.56 + alpha); stall counts ONLY in the cold regime (alpha < 0.2) - see LEARNINGS. Ends
  with a zero-T quench from the best state. Deterministic per --seed (random.Random only;
  wall-clock reported, never steering).
- Top-N: distinct best states (>2 mm or >1 deg apart) -> applied to the in-memory model,
  greedy spiral repair if minor illegality remains, placelib legality check, absolute op list
  per candidate -> `<out-dir>/cand<k>.ops.json` + slim per-candidate report entries. --apply-best
  applies rank 1 via place_edit.apply_ops (atomic, verified).
- Routability feedback (SPEC P6.2): --route-feedback exits 2 with a clear message until S11
  (plan-sanctioned stub). The BLENDING IS BUILT and fake-probe-tested: anneal(...,
  route_probe=fn) probes the best state every --feedback-every epochs; completion c boosts
  cong/cross weights (fb_boost = 1 + 2*(1-c)) and candidates rank by cost*(1 + w_fb*(1-c)).
- `tests/test_place_anneal.py` - 23 tests: 21 pure (segment-crossing predicate, engine HPWL ==
  placelib on the applied state, incremental==full_sync invariant after 60 random moves,
  crossing/congestion counters react to moves, rule terms (current/separation/thermal),
  gnd MST exclusion, anneal improves + stays legal on a scattered synthetic board, board file
  untouched, same-seed determinism (ops + counts) / different-seed divergence, satellites ride
  their anchor (slot + rel angle preserved through rotation), edge cluster stays flush + never
  rotates, explicit-pos edge frozen, top-N distinct/sorted, forced-overlap repair, all-locked
  note, feedback stub exit 2, fake-probe blending + weight boost, CLI report/ops files schema,
  missing board exit 2) + 2 smoke (usbbuck4 acceptance at 60-epoch budget; corpus
  reproducibility - byte-identical ops per seed).

**Acceptance evidence (live 10.0.3, usbbuck4 from scratch):** netlist -> board_init (shelf
832.6 mm) -> place_seed --apply (483.7) -> place_anneal default budget (140 epochs, 141k moves,
123 s): best candidate HPWL **273.9 mm = 43.4% under the seed** (bar: >=20%; 50-epoch budget
already gives 26.0% in 41 s - the smoke test uses 60). 3 legal candidates, 0 violations,
overlap 0, congestion overflow 2 -> 0, weighted crossings 14.25 -> 3.0. Same seed twice ->
byte-identical cand1.ops.json. Applied via place_edit: `gate.py --gate place` PASS; place_metrics
hpwl matches the candidate; decoupler Manhattan 2.5-6.6 mm (satellites rigid). Render eyeballed:
connectors on their declared edges (J1 slid to bottom-left - HPWL-optimal, ergonomics is the P6
stage-3 agent's call), buck cluster between USB and MCU, xtal + decouplers at the MCU. Runtime
2 min << 30 min bar. Feedback-completion leg (>=98%) defers to S11 with the probe. `pytest` +
check_env green: **370 passed** (347 prior + 23).

**Deviations from spec/plan (with reasons):**
1. Route feedback stubbed behind --route-feedback exit 2 (the plan's own instruction when S10
   precedes S11); the blending/steering logic is implemented and fake-probe-tested so S11 only
   wires probe(model) -> completion.
2. Rule terms: "analog/digital separation" has no domain metadata until P2/S13 - implemented as
   generic constraints placement.separation [{a:[refs], b:[refs], min_mm}] (quadratic penalty);
   thermal spreading reads constraints.thermal (corpus has none; synthetic-tested); high-current
   path length = current_a x net HPWL.
3. Spec 6.2's "own test corpus of placement problems with known-achievable routability" needs
   route completion to label -> lands with S11 feedback; S10's corpus = synthetic scatter/cross/
   congestion problems + the usbbuck4 flow.
4. Gnd-class nets excluded from crossing/congestion terms (not in spec's list): their flight
   lines do not predict routing demand on plane-carrying boards; they still count toward HPWL.
5. Not a "~2 kLOC class": ~1100 lines, because clusters/slots/transforms/legality live in
   placelib/place_seed (S9) and are reused, not duplicated.

**Interface notes for later steps:**
- S11 (feedback wiring): pass route_probe=fn to place_anneal.anneal() (or replace the CheckError
  branch in run()); fn(model: PlaceModel with best state applied) -> completion fraction [0,1].
  Everything else (feedback_every, fb_boost steering, candidate blending, facts.last_completion)
  already works. The >=98% fast-route acceptance leg is S11's.
- S13 (P6 phase): stage 2 = `place_anneal.py --pcb B.kicad_pcb` (sidecars from the board dir;
  ~2 min default budget) -> report + `<board dir>/anneal/cand<k>.ops.json`; stage 3 agent reads
  the report's per-candidate {cost, score, hpwl_mm, terms, legal, n_violations, ops_file},
  renders the board per candidate if desired (apply ops to a COPY via place_edit), picks one,
  applies it; `--apply-best` short-circuits to rank 1. `gate.py --gate place` unchanged.
- Input contract: run on a seed-applied board. The engine re-seats satellites into their
  deterministic slots at init and only SLIDES edge clusters along their declared edge - the
  perpendicular flush seat must come from place_seed. Locked/fixed/board_only footprints are
  obstacles; explicit-pos edge clusters never move.
- Determinism: same --seed -> byte-identical ops files (smoke-pinned). Different seeds give
  independent candidates for the stage-3 agent.
- HPWL baselines (usbbuck4): shelf 832.6 / seed 483.7 / anneal 273.9 / golden hand 452.6. The
  anneal beats the hand placement on HPWL by packing tightly into the fixed outline - fine for
  wirelength, and the empty-board-half look is an outline-sizing (P5) artifact, not a placer bug.

**New verify-later items:** none. (Feedback-completion acceptance leg is explicitly S11's per
the plan; no register entry needed.)

## S11 - Routing pipeline (2026-07-23) - DONE

**Smoke tests first (plan-mandated; V1/V7/V3 all resolved live on 10.0.3):** DSN export +
SES import via SWIG two-arg calls work headless WITH the wx recipe (V1); the deterministic
Freerouting flag set verified on our own DSNs with the completion-parse priority pinned in
routelib (V7); post-SES fills are stale until the kicad-cli refill - 33 violations -> 0 (V3).
Bonus mechanics proven en route: zones export as "(plane NET)" and FR connects pads to planes
itself (26 vias with plane vs 7 without); the first autorouted pour split into 2 islands,
becoming plane_repair's live acceptance fixture.

**Decisions recorded per plan:** DSN/SES path = SWIG bundled python (spec P7.3 option (a)),
worker = lib/route_swig.py with results via FILES. KiCadRoutingTools v0.19.0 evaluated
("wrap or vendor") -> VENDORED under tools/krt (MIT, pinned zip + prebuilt abi3 pyd, sha256s
in PROVENANCE.txt, env.find_krt(), scipy==1.18.0 added to pins) and WRAPPED for diff pairs +
power (route_critical) and as route_auto's finish/fallback engine; RF fencing stays ours.

**Built** (S2 violation schema + spec 6 CLI contract throughout):
- lib/route_swig.py (worker verbs export_dsn/import_ses/apply_ops/add_zones; removals LAST
  before save) + lib/routelib.py (worker driver, FR ladder mp 20/60/100, log parser,
  marker-guarded fresh_work_dir, cross-volume-safe swap_in).
- route_edit.py - THE track/via op writer (place_edit pattern; idempotent adds/removals,
  atomic swap, rollback verified byte-identical).
- route_auto.py - refill -> DSN export (auto LT_POWER marking) -> FR ladder (per-rung process
  timeout, wedge short-circuit on timeout+zero-passes) -> best-SES import (next-best on
  corrupt SES) -> refill -> DRC -> KRT finish/fallback (rips DRC-error sliver vias by uuid,
  batched KRT route of unrouted nets, sub-0.05mm crumb sweep, kept only if DRC strictly
  improves) -> placement_adjust_request (the sanctioned P7->P6 backward edge) when unrouted.
  --probe = the S10 routability probe.
- planes_gen.py - constraints["planes"] schema + defaults (2L B.Cu GND; 4L In1 GND + In2
  dominant power; high_speed references guaranteed a plane); thermal-via grids under EPs;
  idempotency guard; distinct priorities for same-layer overlaps (zones_intersect fact).
- stitch_vias.py - pad stitching to planes (obstacles = WIRED copper only, fills re-flow;
  keepouts + 0.5 mm hole floor; corridor-checked connecting tracks; THT skipped; 2-layer
  bond rule vs via_dangling), area stitching at rise-time pitch, --fence-net RF fence.
- plane_repair.py - electrical-group split detection (per-layer fill components unioned by
  via/pad connectivity; naive component counting FPs on clean rf4), repair ladder (same-layer
  bridge -> other-layer bridge -> two-via jumper, 0.5->0.25 grid + thin-bridge escalation).
- route_cleanup.py - dangling/loop/chamfer hygiene with assert_fresh guard and a
  connectivity-regression self-check (exit 1 cleanup_regression, orchestrator restores).
- route_critical.py - KRT adapter: diff pairs (S5 pair-discovery reuse; stub-pad detach/
  restore around KRT's endpoint bug; impedance geometry from stackup; width ladder;
  check_diffpair post-verify), power (IPC-2152 x1.5; per-net neckdown policy vs DRU floors;
  post-KRT width normalization to the IPC floor; PLANE-CARRIED NETS SKIPPED - the plane is
  the trunk, outer trunks starve thermal spokes), RF (impedance width + fence handoff).
  DRC-delta rollback on new ERRORS only (warnings belong to cleanup).
- S10 wiring: place_anneal --route-feedback builds the real probe (place_edit snapshot ->
  route_auto.route_probe); kc.py violation items now carry uuid (fixer dispatch enabler).
- tests: test_route_auto (22) + test_planes_gen (23) + test_stitch_vias (24) +
  test_plane_repair (24) + test_route_cleanup (25) + test_route_critical (23) = 141 new.

**Freerouting 2.2.4 showstopper found + mitigated:** KRT guide-wire copper can wedge FR
DSN reading in infinite recursion (PolylineTrace.combine) before pass 1; the same board with
routed copper stripped routes in 2.8 s. route_auto detects the signature and falls back to
KRT for the remainder. Chain order is board-class dependent: 2L critical->auto->stitch;
4L critical->stitch->auto; plane-carried power nets are never outer-trunked. (LEARNINGS x5.)

**Adversarial review (ultracode: 5 lenses, 2 refuters/finding, 59 agents): 27 raw ->
19 CONFIRMED; all 4 majors fixed** (restore_stub_pads nested-detach order; stitch ring/fence
keepout gap; unguarded rmtree of user --work-dir x2) **+ 9 minors fixed** (foreign-fill
over-blocking + hole-distance in repair jumpers, pre-refill power-layer detection,
ses_items_added misreport, truncated-SES next-best fallback, cross-volume swap,
refill-failure board-modified error texts x3, cleanup assert_fresh). Documented-not-fixed:
plane_repair/route_cleanup mutate the real board in place by design (self-detected;
git/snapshot restore is the recovery - exercised live in acceptance).

**Acceptance evidence (live 10.0.3, both goldens netlist -> board_init -> rules_gen ->
place_seed -> planes_gen -> critical -> [stitch/auto per class] -> repair -> cleanup):**
- blinky2 (2L): route_auto completion 1.0 (FR converged at 34 left on the seeded board;
  KRT finished 9 nets), gate drc_routed PASS 0 total (err+warn included),
  verify_all PASS - all 8 checks clean.
- usbbuck4 (4L): stitch 35/40 pads pre-connected, route_auto completion 1.0 (KRT finish
  threaded the LQFP GND pins FR cannot fan out + ripped 1 hole-clearance sliver via),
  gate PASS 0 total, verify_all 0 errors + 1 warning (diffpair_via_asymmetry on the R3
  pull-up stub) - passes the error-gated verify gate. USB pair: coupled at computed 90-ohm
  geometry, skew 1.74 mm, uncoupled 0.0 at route_critical, check_diffpair pass there.
- plane repair: the live autorouted GND-pour split (2 islands, DRC 1 unconnected) detected
  and auto-repaired (two-via jumper, DRC -> 0); rf4 "plane-split" mutant truthfully NOT a
  split (keepout slot does not bisect In1; 1 component, area drop visible) - its catcher
  stays check_return_path per the manifest.
- S10 feedback leg: probe completion 1.0 >= 0.98 on seeded usbbuck4 (65 nets, 6-pass cap);
  --route-feedback wired end-to-end (fake-probe + factory tests).
- cleanup regression self-check fired on both boards; orchestrator-style rollback restored
  the routed state (the S13 fix-loop pattern, exercised).
- check.cmd equivalent green: **511 passed** (370 prior + 141 new) + check_env exit 0.

**Deviations from spec/plan (with reasons):**
1. Freerouting is not the sole remainder engine: a KRT finish/fallback pass was added (FR
   cannot fan out 0.5 mm LQFP pins; its reader wedges on KRT copper). FR stays primary; KRT
   output is always re-gated by kicad-cli DRC and kept only on strict improvement.
2. "plane-repair mutant fixed automatically": the rf4 mutant plane is NOT split (verified);
   plane_repair acceptance is the live routing-caused split it repairs automatically.
3. Plane-carried power nets are routed by NOT routing them (golden usbbuck4 pattern).
4. stitch_vias pitch: the plan lambda/20 literal is 10x its own pinned value; implemented
   c/(f_knee*200) = 4.28 mm at 1 ns.
5. gates.yaml unchanged - drc_routed (S2) is the P7 gate as designed; the P6 place gate
   fast-route term is now computable via route_auto --probe (S13 wires it if desired).
6. Acceptance chains run seed-only placement: the S10 anneal courtyard-only packing is
   silk-blind (refdes over neighbour pads -> 12 silk warnings failing the err+warn gate).
   Silk-aware refinement belongs to the P6 stage-3 agent / P8 silk fixer (S13).

**Interface notes for later steps:**
- S13/P7 playbook: 2L: route_critical -> route_auto -> stitch_vias -> plane_repair ->
  [route_cleanup, restore on exit 1] -> gate drc_routed. 4L: swap stitch before route_auto.
  All scripts take --pcb + sidecars from the board dir; route_auto artifacts live in
  <board dir>/route (marker-guarded). route_auto facts carry completion, rungs, krt_finish,
  and placement_adjust_request {request, nets, refs, region, reason, suggestions} - hand it
  to the placement agent (the only sanctioned backward edge).
- Violation kinds added for cluster_violations/fixers: critical_route_failed,
  critical_missing_net, zone_unfilled, stitch_impossible, plane_split,
  plane_split_unrepairable, cleanup_regression.
- route_probe(pcb, passes=, timeout_s=) -> facts with completion in [0,1]; place_anneal
  --route-feedback --probe-passes N --probe-timeout-s S uses it via make_route_probe.
- KRT invocations: always cwd=env.find_krt(), args as a list, --no-fix-drc-settings +
  explicit floors + fab-overrides file, fresh output path, parse the LAST JSON_SUMMARY line
  (route_critical.run_krt is the reference; "nothing to route" = no-op success).
- kc.py normalized violation items now include "uuid" - fixers can dispatch route_edit
  removals directly from DRC reports.

**New verify-later items:** V13 (route_cleanup loop-breaker can drop a plane-mediated
load-bearing segment - self-detected + rolled back; root-cause the union-find/fill edge at
S13/S14 or keep cleanup optional), V14 (the FR PolylineTrace.combine wedge deserves an
upstream freerouting issue report with a minimal DSN repro).

## S12 - Fab outputs, DFM, ordering (2026-07-24) - DONE

**Smoke test first (plan Convention 4, live 10.0.3):** exported gerbers/drill/pos from a golden and
confirmed gerbonara 1.6.3 turns them into usable geometry BEFORE building on it - F.Cu came back as
111 pad flashes + 76 trace lines (min aperture 0.25 mm via `aperture.equivalent_width('mm')`),
F.Mask as 86 openings, the drill as Flash objects with `.aperture.diameter`. That settled the
"independent second geometry path" premise (SPEC P9) as real rather than assumed.

**Built** (all under `.claude/skills/ai-ee/`, spec 6 CLI contract + S2 violation schema):
- `scripts/lib/gerblib.py` - gerbonara -> shapely, the second geometry stack. Classifies an exported
  fab dir by kicad-cli's layer tokens (board name irrelevant), returns copper/silk/mask per layer as
  buffered trace polylines + pad flashes + pour regions, drill holes, and the Edge.Cuts outline
  (polygonized from centerlines). Everything in BOARD space (gerber Y negated) and mm, so DFM
  violations carry the same coordinates as geom.py/kc.py/manifest.yaml. Copper layers re-sorted to
  PHYSICAL order (F, In1..InN, B).
- `scripts/fab_export.py` - the JLC package: curated layer set (copper x N + silk + mask + paste +
  Edge.Cuts) + Excellon drill + mm pos CSV, zipped, with sha256 per file and for the zip. Does NOT
  pass `--subtract-soldermask` (silk-over-pad must stay visible for dfm_check to see it).
- `scripts/bom_cpl.py` - JLC BOM.csv (grouped by value/footprint/LCSC, comma-joined designators) +
  CPL.csv (Mid X/Y, Layer, Rotation) with rotation corrections applied from
  `reference/jlc_rotations.csv` (regex on the footprint name, first match wins), plus a per-part
  `rotation_audit` trail (base -> correction -> final, matched pattern) and `missing_lcsc`.
- `scripts/dfm_check.py` - the P9 gate check. Copper: min trace width, min clearance (gaps between
  UNIONED copper islands - gerbers have no nets, so "touching = one conductor", which is what the
  fab's engine sees), copper-to-edge. Drill: hole size, hole-to-hole, hole-to-edge, annular ring.
  Mask/silk: silk-over-pad (silk ink inside a mask opening), mask dams, silk stroke width. Assembly:
  CPL polarity (below). Release: layer completeness, drill validity, BOM completeness.
- `scripts/order_quote.py` + `reference/jlc_pricing.yaml` - qty x finish x mask-colour x assembly
  matrix + lead times, computed from the board's REAL geometry (outline bbox, layer count, pad count
  for joints). Every figure carries `estimated: true` and the authoritative quote URL.
- `scripts/order_submit.py` - locates + hashes the package, snapshots the spec and chosen quote row,
  writes `fab/order.json`, and stops. Payment is never automated (SPEC P10).
- `reference/gates.yaml` + `gate.py`: the **dfm** gate (P9, tool `dfm`, fails on error severity;
  exports gerbers to scratch, takes the schematic beside the board as polarity oracle and parts.json
  for BOM completeness). `test_kc_gate.py`'s tool whitelist extended (S5/S9 precedent).
- `tests/test_fab.py` - 55 tests: 40 hermetic (rotation-table maths incl. the polarized packages,
  pos/BOM/CPL construction, parts.json shape tolerance, capability selection, tolerance semantics,
  gerblib layer/outline/hole/arc handling, seeded gerber defects written by hand - narrow trace,
  tight clearance, touching-copper non-violation, small drill, hole-to-hole, thin annular ring,
  at-the-limit acceptance, copper over edge, missing layer, BOM warning - polarity clean/caught/
  negative-controls, quote maths, order manifest) + 15 `smoke` (live export: layer sets, zip+hashes,
  4-layer stackup order, BOM/CPL on golden, goldens DFM-clean x3, both designated mutants caught at
  manifest coordinates, 4 negative-control mutants, gate pass/fail, full P9->P10 flow, runtime).

**Acceptance evidence (live 10.0.3):**
- **cpl-rotation CAUGHT** (V9 resolved, the step's crown jewel): `cpl_polarity`, ref **D1**,
  `rotation_delta_deg` **180.0** - exactly manifest's `expect`. Reported as "D1 pad nets are rotated
  180 deg from the schematic - the part would be assembled backwards (pad 1: board /LED_A vs
  schematic GND, pad 2: board GND vs schematic /LED_A)". `--schematic-parity` still reports 0 on
  this board, so this check is the only thing between a backwards LED and the fab.
- **silk-over-pad CAUGHT**: `dfm_silk_over_pad`, ref D1, pos [132.4375, 129.5] vs manifest
  [132.44, 129.5]; 0.344 mm2 of silk inside the mask opening (golden measures exactly 0.0).
- **Zero false positives**: all three goldens error-clean (`status: pass`, exit 0) - only the
  by-design silk-width warning (KiCad's stock 0.12 mm silk vs JLC's 0.15 mm floor). Four mutants
  owned by other checks (undersized-power-trace, decoupler-moved, diffpair-skew, missing-return-via)
  raise no DFM errors.
- Package: blinky2 -> 11 files (2L) / usbbuck4 -> 13 files (4L, In1/In2 present, physical order),
  zip + sha256 per artifact; BOM groups 17 parts correctly; D1's CPL rotation 180 -> +180 -> 0.
- P9->P10 flow on usbbuck4: 4-layer 60x45 mm, 23 parts / 111 joints -> quote matrix (qty 5 = $21.94
  incl. assembly, unit $4.39; qty 30 = $49.56) -> order.json `ready_for_human`, zip hash matching the
  export manifest, `--api` exits 2 without credentials.
- `gate.py --gate dfm`: PASS on all goldens, FAIL (exit 1) on cpl-rotation with `cpl_polarity` in
  `failing`. DFM runtime 3.6-4.5 s per golden (budget 30 s).

**Two bugs found and fixed while building (both would have failed good boards):**
1. **Arc curvature was being dropped.** gerbonara's `ArcPoly.outline` holds only segment endpoints,
   so round pads became coarse polygons - blinky2's vias (0.6 mm pad on 0.3 mm drill = exactly JLC's
   0.15 mm annular floor) read ~0.55 mm and ALL 25 failed. Fixed with `approximate_arcs(1e-3)` plus
   a 2 um comparison tolerance so an exactly-at-spec board passes.
2. **Annular ring measured against pours.** A zone fill is a keyhole ring threading past every via's
   antipad, so counting pours as "the pad around the hole" measured the antipad gap (phantom 0.1245
   mm ring). Restricted to pad flashes on outer layers.

**Deviations from spec/plan (with reasons):**
1. Plan's "package uploads clean to JLCPCB's web viewer (manual verification, once)" and "CPL
   rotations spot-checked against JLC's rendered preview for 3 polarized parts" are BROWSER steps
   with no API - **not done, registered as V15**, to be done once before the first real order (S14).
   The machine-checkable halves (package completeness/structure/hashes, rotation-correction maths for
   the polarized packages) are tested here. Stated plainly rather than claimed.
2. `order_submit.py` does NOT call api.jlcpcb.com: that programme requires an approved access
   application this environment lacks, so a live integration is unverifiable. `--api` exits 2 naming
   the exact prerequisite; the manifest it writes is already the payload for when credentials exist
   (V16). Shipping an untested "places your order" path would have been the dishonest option.
3. `reference/jlc_pricing.yaml` is new and NOT in the spec's reference list: order_quote needed
   SOME price basis for the P2/P10 matrices. Transcribed headline prices, cited + dated + flagged
   `estimated: true`, with the authoritative quote URL always emitted (V16).
4. Silk stroke width and mask dams are WARNINGS, not errors: KiCad's default 0.12 mm silk is below
   JLC's stated 0.15 mm minimum and prints fine, and all three goldens use it - gating on it would
   fail every legitimate board. Same for missing LCSC numbers. Follows the fp_verify/netlist_audit
   precedent (warnings do not fail the gate); dfm_check overrides checklib's status accordingly, so
   warnings-only = `pass` + exit 0.
5. `dfm_check` owns CPL polarity rather than `bom_cpl` generating-and-validating: generation and
   validation should not share a code path, or a rotation-table bug would validate itself. bom_cpl
   applies corrections and emits an audit trail; dfm_check independently compares pads to the
   schematic.
6. A `lib/gerblib.py` module was added (spec 6.4 lists only the five scripts): the gerbonara->shapely
   layer is reusable and keeps dfm_check's rules readable, mirroring the geom.py/checklib.py split.
7. No JLCDFM automation (V6): no public API exists, so it stays a human step, surfaced in
   order_submit's `human_steps` alongside the polarized-part preview check.

**Interface notes for later steps:**
- `fab_export.run(pcb, out_dir, name=, layers=, make_zip=) -> manifest` with `files[{name,sha256,
  bytes}]`, `gerber_zip`, `gerber_zip_sha256`, `copper_layers` (physical order), `pos_file`.
  `copper_layers(pcb)` is importable for anything needing the stackup order from the board text.
- `bom_cpl.run(pcb, out_dir, pos=, parts_json=, rotations=) -> {bom, cpl, bom_rows, cpl_rows,
  rotation_audit, missing_lcsc, bom_complete}`. `load_rotations`/`correct_rotation` are pure and
  reusable. parts.json accepts four shapes (`{"parts":[...]}`, list of `{refs,lcsc}`, `{ref: lcsc}`,
  `{ref: {lcsc}}`) - S6's parts_search output feeds it via the `lcsc` key.
- `dfm_check.run(pcb, fab_dir=, copper_oz=, schematic=|netlist=, polarity=, parts=, skip=)` ->
  checklib payload. New violation kinds for cluster_violations/S13 fixer dispatch: `dfm_trace_width`,
  `dfm_clearance`, `dfm_copper_to_edge`, `dfm_hole_size`, `dfm_hole_to_hole`, `dfm_hole_to_edge`,
  `dfm_annular_ring`, `dfm_silk_width`, `dfm_silk_over_pad`, `dfm_mask_dam`, `dfm_missing_layer`,
  `dfm_no_drill`, `dfm_bom_incomplete`, **`cpl_polarity`**, `pad_net_mismatch`.
- `gate.py --gate dfm <board>` is the P9 gate; sidecars (schematic, parts.json) resolve from the
  board's directory, gerbers export to scratch so gating never litters the design folder.
- S13/P9-P10 playbook: `fab_export.py` -> `bom_cpl.py` -> `gate.py --gate dfm` -> [fix loop] ->
  `order_quote.py` -> human checkpoint 5 -> `order_submit.py` (writes fab/order.json, stops before
  payment; its `human_steps` list is what checkpoint 5 presents).
- `gerblib.open_fab(dir)` is available to any later check wanting the as-shipped geometry;
  `ARC_MAX_ERROR_MM` and `dfm_check.GEOM_TOL_MM` are the two constants governing measurement
  fidelity - do not tighten GEOM_TOL_MM below the arc error or at-spec boards start failing.

**Coordination note (S6/S7 precedent):** the working tree carried UNTRACKED `scripts/bom_cpl.py` and
`scripts/fab_export.py` at session start - WIP from an earlier/parallel attempt at this step, never
committed and so not recoverable from git. This session's implementations now occupy those paths;
nothing else in the tree was touched. If that WIP mattered, it is in the prior session's context, not
here.

**New verify-later items:** V15 (JLC web-viewer upload + polarized-part CPL preview - human, before
first order), V16 (pricing-table staleness + unimplemented credentialed ordering API).
V6 and V9 resolved above. V11 (inner via-pad removal) unchanged: dfm_check reads the exported copper
so it sees whatever was actually emitted, and the annular check looks only at outer layers, where
JLC's inner-pad-removal option does not apply.

## S13 - Agents, orchestrator, SKILL.md (2026-07-27) - DONE

**Built** (the "soft top" + its machinery; spec sections 3/4/5/7, whole spec read per plan):
- `scripts/state.py` - state.json read/write helpers (SPEC 4 schema, version 1): phases P0-P10,
  per-gate {status, attempts, last, history}, human checkpoints 1-5, artifacts, open_issues with
  lifecycle (open|fixing|fixed|escalated|waived), budgets (fix_loops per gate = 3,
  freerouting_retries, place_edit_iterations), decisions, and an append-only `history` event log -
  the file is current state AND audit trail. Atomic writes (tmp + os.replace). Subcommands: init /
  show / resume (next-gate + pending-checkpoint summary from GATE_ORDER) / set-phase / record-gate /
  artifact / decision / human / issue / budget / log / snapshot / restore (sha256-verified workspace
  file snapshots - the fix-loop safety net). Importable State class + spec 6 CLI (exit 0/2).
- `scripts/fix_dispatch.py` - the violation->fixer wiring (SPEC 4 fix loop): reads a gate.py result
  (`failing`), a check report (`violations`), or a cluster payload; clusters via S5's
  cluster_violations; writes ONE work-order JSON per cluster (log/workorders/wo-<id>.json: domain,
  allowed_scripts, guidance, violations with coordinates/uuids, sidecar artifacts, scope rule) and
  registers open issues in state.json (`--state`). DOMAINS table: router/placement/plane/silk/
  schematic/library/fab/parts/review, each with script whitelist + load-bearing guidance lines.
  `parallel_groups` = order ids whose regions don't overlap (bbox + 1 mm). ERC clusters with unknown
  types fall back to the schematic domain; unknown non-ERC kinds stay "review" (human triage).
- `scripts/cluster_violations.py` EXTENDED (the S13 wiring the S11/S12 notes anticipated):
  FIXER_HINTS grew from 28 to ~90 kinds - S11 routing kinds, S12 DFM kinds, S6 fp_verify, S7
  netlist_audit, and the kicad-cli DRC/ERC type names; cluster() now keys on kind-or-check
  (`kind_of()`), so raw DRC gate reports dispatch correctly (they carry no `kind`).
- `agents/*.md` - 18 role prompts per SPEC 5 (one job first line; script whitelists in preference
  order; grounding rules incl. the never-from-memory pinout ban; uniform FILES/GATE/SUMMARY/OPEN
  output contract; adversarial framing + fresh-context note for the two reviewers; determinism-
  budget rule): requirements-analyst, research-{component-scout, reference-design, interface-spec,
  power-architect}, architect, part-sourcer, librarian, datasheet-extractor, schematic-block,
  schematic-reviewer, board-setup, placement, router, verify-reviewer, fixer, dfm, ordering.
  Every prompt embeds the REAL CLIs and the machine-verified gotchas from S6-S12 interface notes
  (chain orders 2L/4L, plane-carried-net skip, silk-blind packing, SES-duplicate ban, etc.).
- `reference/constraints_schema.md` - the single authoritative constraints.json shape doc
  (high_speed/power/diff_pairs/voltages/thermal/placement/planes + decoupling.json), compiled from
  the S4/S5/S8/S9/S10/S11 consumer contracts; P1 interface-spec and P2 architect write against it.
- `SKILL.md` - the orchestrator playbook (operational; frontmatter flags S14 hardening pending):
  6 non-negotiable rules (never open design files; files-are-the-interface spawn template;
  state.py everything; gate.py --commit on pass; venv python + exit contract; batch questions),
  phase machine + gate table (from gates.yaml), run-start/resume protocols, per-phase playbook with
  agent-selection guidance, the uniform fix loop (budget -> snapshot -> dispatch -> parallel-group
  fixers -> re-gate -> record EVERY attempt; regression restore; cleanup_regression continue-without;
  requires_pipeline_rewind escalation; the sanctioned P7->P6 backward edge), human checkpoint
  presentation format, known limits. `commands/ai-ee.md` - the real /ai-ee entry (new run + --resume).
- `tests/orchestrator/dryrun.py` - the ACCEPTANCE driver: enacts the playbook deterministically on a
  workspace copied from golden blinky2. Every step derives from state.json (any kill point resumes):
  erc gate -> place gate -> inject mutation A (a +3V3 segment narrowed 0.25->0.05 mm = track_width
  DRC ERROR) -> drc_routed FAILS -> budget -> fix_dispatch -> scripted router fixer (remove-by-uuid +
  re-add at the width of abutting same-net copper) via route_edit -> re-gate PASS -> inject mutation
  B (the canonical undersized-power-trace neck 0.8->0.16, DRC-quiet) -> verify FAILS
  (check_current undersized_track) -> fixer locates the uuid by the violation's segment coords ->
  re-gate PASS -> drc_routed REGATE (copper changed during P8) -> P9. The fixer's
  locate-by-uuid/coords + abutting-width repair is the reference implementation of fixer.md's router
  domain.
- `tests/test_orchestrator.py` - 20 tests: 19 hermetic (state lifecycle/attempts/history, budgets,
  snapshots with hash-verified restore, resume-summary progression incl. optional checkpoint 3,
  CLI contract; FIXER_HINTS covers all ~66 pipeline kinds (pinned list) + every domain has a
  DOMAINS table; kind-or-check clustering; dispatch work-order content incl. uuid pass-through,
  parallel groups, state issue registration, input-shape tolerance, erc fallback) + 1 smoke = the
  S13 acceptance (below).

**Acceptance evidence (live 10.0.3, the plan's S13 criteria):** dry-run P4->P8 on golden board 1
with mutations injected mid-pipeline, run as TWO processes: session 1 (`--stop-after drc_routed`)
= workspace + erc PASS + place PASS + mutation A + drc_routed FAIL->dispatch->fix->PASS (attempts
[fail, pass]), killed; session 2 = `resumed` event logged, earlier gates NOT redone (attempts
stay 1), mutation B, verify FAIL->dispatch->fix->PASS, drc_routed regate PASS (attempts=3),
phase P9, dryrun_complete. state.json history ordered init < resumed < complete; both issues
fixed with work orders + pre-fix snapshots on disk; budgets decremented once per gate. Fixes are
GOLDEN-IDENTICAL, not merely gate-quiet: +3V3 F.Cu copper area matches the committed golden within
1e-6 relative (geom). A third invocation on the complete run only logs a resume (gates/issues
unchanged). `check.cmd` green: **586 passed** (566 prior + 20), check_env exit 0, 7m46s.

**Deviations from spec/plan (with reasons):**
1. The acceptance "orchestrator dispatches fixers" runs as a SCRIPTED driver
   (tests/orchestrator/dryrun.py) enacting the SKILL.md protocol - not an LLM session inside
   pytest. The machinery the acceptance actually tests (gates, state, dispatch, fixer execution,
   resume) is fully exercised; the LLM layer (agent judgment) is by design not pytest-testable and
   lands with S14's real runs.
2. `scripts/state.py` + `scripts/fix_dispatch.py` are additions to the spec 6 inventory (the plan's
   own build list demands both: "state.json read/write helpers", "violation->fixer dispatch
   wiring"); gerblib/jlc_pricing precedent for in-spirit additions.
3. `reference/constraints_schema.md` added (not in spec's reference list): P1/P2 agents need ONE
   authoritative constraints.json shape source; previously the shapes lived only in per-script
   docstrings.
4. `agents/datasheet-extractor.md` added: spec section 2's tree omits it but spec P3's text names
   the agent role explicitly; S6's --pdf grounding payload is its input contract.
5. Dry-run mutations are the driver's own mutlib-style exact-match surgery (mutation B reuses the
   canonical undersized-power-trace strings) rather than invoking the S1 mutation scripts: those
   assert against committed-golden bytes at fixed repo paths, and the workspace board legitimately
   diverges after fixer A.
6. The S11/S12 "violation kinds added for cluster_violations/fixers" were documented in PROGRESS
   but never wired into FIXER_HINTS - raw DRC types and all S11/S12 kinds clustered to "review".
   S13 wired them (S13's build item, but recorded here as a found-and-fixed gap, pinned by the
   FIXER_HINTS-coverage test).
7. No silk text-move op was built (S11 notes hoped for a "P8 silk fixer" at S13): silk domain =
   footprint nudge via place_edit or human waiver, honestly documented -> V17.
8. gates.yaml unchanged: the P6 fast-route-completion term stays out of the `place` gate
   (route_auto --probe exists; the placement agent's prompt tells it when to use it; wiring it
   as a hard gate criterion is an S14 call once real-run timings are known).

**Interface notes for later steps (S14):**
- Orchestrator entry: `/ai-ee <description>` or `/ai-ee --resume <ws>` -> SKILL.md. Workspaces at
  `boards/<name>/` INSIDE this repo so `gate.py --commit` (repo-root `git add -A`) captures them -
  see the new LEARNINGS entry: a dirty tree from parallel work would be swept into gate commits;
  keep the tree clean during pipeline runs.
- state.py: `State.load/init` importable; GATE_ORDER = [(P4,erc),(P6,place),(P7,drc_routed),
  (P8,verify),(P9,dfm)]; `resume` returns {phase, gates_passed, next_gate, open_issues,
  pending_human, budgets, artifacts}. Checkpoint 3 is optional-but-on-by-default: it shows as
  pending until recorded approved|skipped.
- fix_dispatch work order: {id, gate, phase, board, fixer, role_prompt, allowed_scripts, guidance,
  cluster{net,kinds,checks,severity,count,region,violations}, artifacts, scope}; `parallel_groups`
  in its summary = safe concurrency sets (regions disjoint). Issues in state carry work_order path.
- The dry-run driver doubles as the protocol reference for S14 debugging: run it against a broken
  machine state to isolate "is it the machinery or the model" questions.
- DRC violations dispatch on `check` (type name) via kind_of(); check violations dispatch on
  `kind`. New DRC/ERC types default to "review" - extend FIXER_HINTS (and the pinned test list)
  when S14 meets new types.

**New verify-later items:** V17 (silk text-move op gap, registered above). V13 updated (cleanup
stays optional; restore pattern codified).

## S14 - End-to-end hardening (2026-07-27/28) - DONE - v1 FROZEN

**Ran (plan-mandated three full /ai-ee runs; exec plan user-tuned mid-session:
model-mix subagents [sonnet mechanical / opus judgment / fable for the two
adversarial reviewers], script phases inline, all checkpoints auto-approved
per user directive after H1 of run (a)):**

- **(a) `boards/stm32-blinky`** - 2L STM32 blinky-class. Brief -> order-ready
  (est $18.77/5 assembled), TWO design interactions (P0 batch + H1) <= the M5
  bar of 5. Highlights: schematic reviewer caught the AMS1117 ceramic-output
  instability (fixed pre-board: 22uF tantalum + VDDA/VDD3 per DS); P7->P6
  backward edge exercised for real (U1.8 boxed by neighbour escapes; 1mm
  cluster relief; attempt 2 = 0/0 + completion 1.0); V17 closed in-run.
- **(b) `boards/usb-buck`** - 4L STM32 USB-FS device + AP63203 buck, 3-sheet
  hierarchy. All 5 gates green; USB pair at computed 90R geometry; verify 8/8
  first try after a constraints correction (uncoupled 5->8mm, structural TVS
  flow-through span + pull-up stub, decomposition on record).
- **(c) `boards/pd-trigger`** - the user-chosen novel brief: USB-C PD sink
  trigger, 5A/100W, CH224K, 2L **2oz** (stackups.yaml entry added), DIP
  straps, zener-window fallback indication. The full research->architecture->
  extract->BOUNCE-BACK chain fired: datasheet extraction overturned the LDO
  topology (CH224K VDD is a shunt; datasheet dropper restored, LDO deleted
  with reasons); router falsified the placement's CC-displacement premise by
  measurement and shipped a pour-based 5A fan-in + 3.0mm trunk; final
  reviewer caught the checker-blind 5A RETURN choke at J1 (0.2mm necks ->
  rebuilt: 5.68/4.70A per pad, 16 vias) and the missing functional silk
  package (17 texts; the agent CORRECTED the orchestrator's inverted CFG
  table to switch-positions). Order-ready, est $19.65/10 assembled.

**Acceptance:** run (a) brief->order-ready with 2 human interactions (bar
<=5) - MET. All regression tests green: **610 passed** (586 baseline + 24
added with the fixes), check_env exit 0. PROGRESS closed out with the v1
known-issues list below. Every manual intervention became a script fix, a
prompt fix, or a documented human step (35-finding ledger).

**Pipeline defects found by the runs and FIXED (all test-pinned):**
1. board_swig never copied symbol fields -> LCSC-carrying schematics failed
   parity; fields now copied + hidden (were VISIBLE-ON-SILK by default).
2. board_init --schematic SameFileError on the standard P4 layout; samefile skip.
3. board_init self-check now partitions TRANSIENT silk (cross-part at shelf
   positions + silk_edge_clearance) from intra-footprint library defects.
4. kc.py refdes regex accepts suffixed refs (R2A) - unsuffixed under-counted
   violation refs and mis-classified cross-part silk.
5. parse_farads multi-token values ("10uF 25V X5R") - pdn_no_bulk FP'd on
   every real-world bulk cap value string.
6. check_pdn "pdn": false width-only power entries (pre-protection stubs).
7. dfm silk sliver warn band <0.05mm2 (EasyEDA body outlines kiss their own
   mask openings; golden mutant 0.344mm2 stays error).
8. gerblib FLAT trace caps vs KiCad's circular apertures: phantom island
   splits (2 FP clearance errors) AND w/2 copper-to-edge understatement
   (false-negative direction) - round caps.
9. dfm annular ring measures the UNION of containing flashes (stitch vias
   tangent to their pads FP'd at -0.095mm).
10. bom_cpl reads per-footprint LCSC fields from the board (primary
    ref->lcsc source; S6 parts.json shape has no refs).
11. route_auto dedups SES-echo copper post-import (FR echoes pre-session
    guide wires as EXACT same-net duplicates, invisible to DRC - run (a) had
    shipped 45; retrofit-cleaned + auto for all future runs).
12. stitch_vias: track-connected pads no longer count toward
    stitch_impossible (advisory FP).
13. placelib effective courtyard = union(courtyard, pad-bbox+0.25): EasyEDA
    courtyards smaller than pad fields let the place gate pass 9 SHORTING
    pad pairs (run (a) P6) - gate now pad-aware.
14. place_swig/place_edit add_text/move_text (V17) + TEXT_LAYERS validation
    + independent sexpdata verify.
15. place_anneal surfaces separation_unknown_refs (constraint refs absent
    from the board were silently dropped - a refdes rename lost a rule).
16. schlib --pins --lib (project symbol libs were invisible to the cache).
17. reference: stackups.yaml JLC2313_1.6_2oz; checklists/ authored (power,
    mcu, connector, interface-usb); constraints_schema pdn:false documented.
18. Prompt fixes: architect LCSC-code ban; board-setup/placement/verify-
    reviewer CLI forms; datasheet-extractor unique grounding names (parallel
    race); part-sourcer JLCPCB-placeholder rejection; router netclass-split
    + cleanup stance; fixer/dispatch silk domain rewritten for the text ops.

**v1 KNOWN-ISSUES (open by disposition; also in SKILL.md Known limits):**
1. route_cleanup union-find/fill loop-breaker unreliable on pour boards
   (V13 closed as dry-run/skip disposition; root cause unfixed).
2. Drill-spacing models incomplete: stitch hole floor is center-point (no
   slot extents) AND KiCad DRC never checks via-drill vs same-net THT
   pad-drill (live-proven) - recovery = DRC gate + route_edit removal.
3. check_current blind to viasless pour-channel widths (router discloses).
4. No outline-shrink step: P5 outline is final; caps bind at board_init.
5. placelib FpPad drops per-pad rotation (extents safe via bbox).
6. rules_gen one-Power-netclass-at-max-width (split in .kicad_pro, pattern
   in router.md).
7. order_quote undercounts Extended feeders; estimated:true everywhere.
8. route_critical diff pairs through flow-through parts peel to a never-run
   SE follow-up (FR covers; KRT route_diff limitation).
9. V11 (inner via-pad removal), V12 (impedance vs JLC calculator - run (b)
   deliberately ordered standard-stackup so still unexercised), V14 (FR
   wedge upstream report; NOTE: no wedge occurred in any S14 run), V15 (JLC
   web upload + CPL polarity preview - in every order.json human_steps),
   V16 (credentialed ordering API) remain open as registered.
10. EasyEDA library quality requires the S14 defenses (courtyard expansion,
    silk sanitize protocol, retype pass, EDITS.md convention) - they are
    load-bearing, not optional.

**Interface notes (post-v1 work):** resume any board via `/ai-ee --resume
boards/<name>`; the three workspaces are order-ready (fab/order.json
human_steps = the remaining human actions; NOTHING was purchased). SKILL.md
is the operational authority; SPEC.md section 9 carries the as-built addenda.
The S14 finding ledger (35 items) is summarized here; per-run digests in
each workspace's log/.

## Post-v1 amendment: report_gen design-document generator (2026-07-28)

**Built** (additive; recon x2 -> build -> validation + adversarial review, 5 agents):
- `scripts/report_gen.py` - assembles a per-run LaTeX design doc from the
  workspace (state.json spine + brief/requirements/architecture + digests +
  waivers + reviews + renders + verify/dfm/fab JSONs + order/quote) into
  `reports/design_doc/<board>-design-doc.{tex,pdf}`. Phase-aware ("as it's
  built": not-yet-due sections render pending stubs; due-but-absent core
  artifacts -> missing[] + exit 1). Compile: 2-pass pdflatex staged in system
  temp - ZERO .aux/.log residue in the tracked tree; `--tex-only` = full
  success without TeX; pdflatex absent = degrade + warning; bad AIEE_PDFLATEX
  pin = loud exit 2 (tex still written). Escaping is a per-char total map ->
  pure-ASCII .tex asserted (build fails otherwise).
- `env.find_pdflatex()` (AIEE_PDFLATEX -> PATH -> per-user MiKTeX default) +
  warn-level check_env check (23 checks now).
- `tests/test_report.py` - 31 tests (29 hermetic, 2 smoke incl. residue +
  rerun guards on real workspaces).
- SKILL.md: design-doc step wired before every human checkpoint + P10 close,
  explicitly NON-BLOCKING (never gates a run).

**Validation:** all three S14 workspaces compile end-to-end (pd-trigger 21 pp,
stm32-blinky 18 pp, usb-buck 23 pp with its two known artifact gaps rendered
honestly); schematic PDFs embedded page-exact; adversarial review (probe-
driven) found 1 real defect class - unescaped `[`/`*` are context-sensitive
after the \\ line-join and inside \item (fatal "Missing number" / silent
label swallow) - fixed by brace-wrapping in the escape map + regression
tests; 2 minor fixes (compile failures now self-explain in warnings; bad-pin
exit no longer discards the built .tex). LEARNINGS [latex] x2 (that, plus
pdfpages-2026 `artifact` keyval vs older graphics stacks - shimmed).
`check.cmd` green: **641 passed** (610 prior + 31), check_env exit 0.

**Known limits:** narrative markdown is converted by a deliberate md-lite
ceiling (headings/bullets/inline marks; tables + fences pass through as tt
blocks); doc prose quality = quality of the recorded digests/notes. The
hand-written pd-trigger prototype (reports/design_doc/pd-trigger-design.*)
stays untracked pending user disposition.

## Post-v1 amendment: JLCPCB Open API ordering + tracking (2026-07-28)

**Built** (research -> build -> 3-round adversarial loop; 1 research agent,
builder x3 rounds, validator, reviewer x3 rounds):
- `scripts/lib/jlcapi.py` - JOP HMAC client on stdlib urllib (injectable
  transport): signing pinned to the official doc vector, envelope
  normalization, error classifier (401 sig / 403 scope / code-1000 IP at
  any status / rate), endpoint wrappers (uploadGerber, audit, calculate,
  create, order/detail, wip, component), `--probe` CLI. LIVE-VERIFIED on
  the user's app (2026-07-28): signing accepted, 403 scope_pending (all
  five service permissions under JLC review), IP whitelist entry working.
  Balance endpoint stubbed (path not public - read the SDK jar when needed).
- `order_submit.py --api` quote-only leg (upload -> API DFM audit ->
  calculate -> fab/api_quote.json real price beside the estimate; V6
  partially compensated by the audit). `--api-create` = the ONLY create
  path: one-order-per-workspace latch (verdict-armed even for ids-less
  responses), gerber-sha256 binding, freight-attested grand-total confirm
  token, qty cross-check, ship-json key whitelist; board-specific
  human_steps survive every rewrite (the 2oz-guard evidence is permanent).
  NO sandbox exists: pcb/create is real spend, post-H5 only.
- `order_track.py` - order/wip poll -> fab/tracking.json (atomic write,
  content-diff change detection for notification cadence). PCB
  tracking-number surface is a live unknown (3DP exposes expressNo; PCB
  order/detail may not).
- Adversarial loop: 18 findings r1 (headliner: pcbParam key names from the
  wrong table - would have priced/ordered a default board), 5 r2 (latch
  --out bypass, copper-guard evidence self-destruct, freight outside the
  token), 2 r3 (S-1 cosmetic prefix note-loss documented; S-2 ids-less
  latch fixed at integration with regression, both latch AND sticky-verdict
  sites). Reviewer verdict: SHIP.
- ordering.md + SKILL.md P10 wired: API quote leg = agent; create =
  post-H5 orchestrator action with the human token; the agent NEVER
  creates. Env: AIEE_JLCPCB_APPID/KEY/SECRET user-level env vars (set
  2026-07-28; spawned-shell inheritance caveat in LEARNINGS [windows]).
- `tests/test_jlcapi.py` 77 tests (76 hermetic mock-transport + 1
  net-marked live probe that skips without creds). Full suite: **720
  passed** + 1 skipped (net probe), check_env exit 0. One net-marked live
  test (test_net_lib_pull_loads_in_kicad, EasyEDA pull) flaked during the
  full run and passes standalone - transient upstream, outside this diff.

**Live unknowns** (first scope-approved probe/order resolves): review
turnaround; copperWeight type strictness; balance auto-deduct vs
unpaid-order; PCB tracking-number field; upload empty-vs-meta signing;
rate limits. Day-one probe:
`.venv/Scripts/python.exe .claude/skills/ai-ee/scripts/lib/jlcapi.py
--probe` (exit 0, verdict flips "SIGNING VERIFIED - scope approval
pending" -> "live" on approval).

**2026-07-29 live update - scopes APPROVED, first real quote fetched:**
probe verdict "live"; pd-trigger quote-only flow succeeded end-to-end
(upload -> fileKey -> calculate): REAL price 40.00 USD for 10x 2L 2oz
48x30 HASL vs the 19.65 estimate (order_quote's 2oz/options undercount
confirmed large). Resolved live: signing/upload on this app; copperWeight
"2" STRING accepted; scope-review turnaround ~1 day. Corrected from live
evidence (LEARNINGS 2026-07-29): insideCuprumThickness is 4L+ only (2L =
code 2129); isAddCustomerCode/markOnPcb/autoConfirmProductionFile omitted
from calculate (code 2708; create-side options, decided at the first
gated create). Remaining before the first real order: pcb/audit is ASYNC
(code 2501 right after upload - add a re-poll); calculate returns no
shipList without a country input - plumb country so the freight-attested
grand-total token (N3 gate) carries real freight; then the human types
the token. Balance mechanics + tracking-number surface unknown until an
order exists.

## Post-v1 amendment: simulation legs - SPICE gate + layout IR-drop/PDN (2026-07-28)

**Built** (2 research agents [1 died on the monthly spend limit - model-licensing
leg replaced by a conservative design default] -> 2 parallel builders -> 1
combined adversarial reviewer -> fixes at integration):
- SPICE gate: `scripts/sim_run.py` + `lib/simlib.py` (kicadsexpr .net fragment
  synthesis with deterministic rename map; InSpice 1.7.0.5 [pinned] driving
  KiCad's bundled ngspice.dll v46 - no new binaries; per-bench killable
  subprocess w/ hard timeout; bounds sidecars -> checklib violations),
  `agents/sim-analyst.md` (P2/P4 role: generic model cards from datasheet
  params - NO vendored vendor models - + Tier-B pin stimulus), `sim` gate in
  gates.yaml/gate.py, 4 committed testbenches. Live-proven: pd-trigger zener
  window PASSES (vtrip 7.738 V in [7.2, 8.55]); the R7 47k wrong-value mutant
  FAILS the gate on vtrip 6.835 V - the defect class ERC/DRC/verify/DFM
  cannot see. PC13 sink 1.635 mA vs the 3 mA datasheet abs-max; NRST rise
  8.79 ms vs 8.8 analytic.
- Layout leg: `scripts/check_irdrop.py` (2.5D raster-FDM on geom.py copper:
  strip R within 0.43% of analytic, Trefethen corner +0.003 squares;
  undersized-power-trace mutant peak J at [118.4,107.4] ON the 0.16 mm neck
  at 1.74x golden - second catcher for that class; pd-trigger 5 A maps in
  0.1-1.6 s) + `scripts/check_pdn_z.py` (cavity model per the
  ai-library/pdn-irdrop-sim-2026 contract: 1/2/4 modal weights, cos*sinc
  ports, lossy k + delta_mod clip, Z_loaded decap loading; usbbuck4
  antiresonances 4.3-4.6 MHz). Both advisory-by-default.
- Adversarial verdicts: Track A SHIP, Track B FIX-FIRST (narrow) - all fixed
  at integration: pdn_target_mohm now gates antiresonance PEAKS only (band
  edges are model validity limits - no VRM/package model), empty bounds
  sidecars + non-finite bound limits rejected, zero-current entries skip
  instead of killing the run, unpaired rails surfaced in skipped_rails.
  Clean-hunt evidence: units audit (via barrel hand-recompute matched),
  zener knee 6.200 V at Izt, bounds robust at gmin x1000 + 60 C.
- SKILL.md: "Simulation legs" section (sim-analyst at P2/P4, sim gate at P8,
  layout legs advisory) + Known limits. LEARNINGS [spice] x2.
- Tests: test_sim.py 29 + test_layout_sim.py 18 (incl. adversarial
  regressions). Full suite: **769 passed** + 1 skipped (net probe),
  check: OK, check_env exit 0.

**Known limits:** SPICE = analog fragments only (digital pins as datasheet
stimulus; buck switching not simmed by policy); irdrop injection worst-case
unless source_ref/sinks declared; pdn_z bounding-rect geometry, no
VRM/package model. Sim-analyst calibration lesson: bounds are
engine-version-sensitive at leakage scales - the committed benches hold at
gmin x1000 and 60 C.
