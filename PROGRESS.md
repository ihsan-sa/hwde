# PROGRESS

Build state for the ai-ee skill. One entry per plan step (`ai-ee-implementation-plan.md`).
Session protocol: repo `CLAUDE.md` ("run step N"). Update this file + commit at every session end.

## Status board

| Step | Title | Status | Date |
|---|---|---|---|
| S0 | Repo bootstrap and environment | **done** | 2026-07-06 |
| S1 | Golden board corpus | pending | |
| S2 | kicad-cli wrappers and gate infrastructure | pending | |
| S3 | Geometry library | pending | |
| S4 | Verification suite part 1 (crown jewels) | pending | |
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
| V2 | kicad-sch-api output opens in KiCad 10 | spec sec 9, S7 | Untested. 0.5.6 installed; smoke first thing in S7 (`sch upgrade` available on the 10.0.3 pin). |
| V3 | `drc --refill-zones` availability | spec sec 1 | RESOLVED S0: absent on 9.0.5, present on 10.0.3 (a pin-decision driver). Behavior on a real zoned board: verify at S3 (zone freshness) / S11 (post-SES refill). |
| V4 | kipy `headless=True` starts `kicad-cli api-server` | spec sec 1 | RESOLVED S0: NO api-server subcommand in 9.0.5/10.0.3; kipy 0.7.1's server helper targets newer KiCad. Working IPC: sandboxed-GUI launch (smoke_ipc.py, verdict `gui-sandboxed-ok`). Headless alternative: SWIG bundled python. Decide edit path at S9. |
| V5 | JLCPCB Parts API (credentialed) | spec sec 1, S6 | Needs access application; jlcparts SQLite fallback path untested. S6. |
| V6 | JLCDFM upload (no public API) | spec P9 | Semi-manual by design; S12. |
| V7 | Freerouting batch flags + result parsing | LEARNINGS [freerouting] | Prior-attempt facts; re-verify on our own DSN at S11. |
| V8 | IPC API feature coverage for placement edits (move/rotate via kipy 0.7.1 on KiCad 10) | spec P6 | Connection verified S0; edit-op coverage untested until S9. |

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
