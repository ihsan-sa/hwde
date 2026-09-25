# hwde - AI PCB design skill (staged build)

Building the `/hwde` Claude Code skill per `SPEC.md` + `ai-ee-implementation-plan.md`,
**one plan step per isolated session** to preserve context. `PROGRESS.md` tracks state.

## "run step N" protocol

When the user says `run step N` (or just `step N`):

1. Read `PROGRESS.md` (status board + interface notes of completed steps) and the step's
   plan entry: S<N> steps live in `ai-ee-implementation-plan.md` (v1, complete); T<N>
   steps live in `ai-ee-v2-plan.md` (v2 - same protocol, plus its own Conventions);
   **U<N> steps live in `hwde-v3-plan.md`** (v3 - same protocol, waves + owner-present
   steps marked there).
   Read ONLY the spec sections / files that entry lists (S13 alone reads the whole spec).
   Do not load prior steps' code beyond what the entry needs.
2. Check prerequisites on the status board against the plan's dependency graph. Unmet -> stop
   and tell the user which step is missing.
3. Grep `LEARNINGS.md` for the step's area tags BEFORE writing code; append new gotchas as hit
   (append-only, dated, tagged).
4. Honor the plan's Conventions: smoke-test any "verify-later" claim the step first touches
   before building on it; scripts follow the SPEC.md section 6 contract (argparse, JSON to
   stdout or --out, exit 0/1/2, no interactivity, ASCII-safe output).
5. Session end: all acceptance tests green via `check.cmd`; update `PROGRESS.md` (status board
   row + step entry: built / deviations with reasons / new verify-later items / interface
   changes affecting later steps); `git commit`. Do NOT start the next step.

## Boards live in their own repo

This repo is the skill only. Board workspaces live in the boards repo
(ihsan-sa/boards, cloned at `~/dev/boards`); every script finds them through
`env.boards_root()` = `HWDE_BOARDS_ROOT`, default `~/dev/boards`. A board's part
number (PCB-NNNN-R) comes from that repo's `register.yaml`, which hwde only
reads. Tests never need the boards repo: a test that needs a real board goes
through `tests/_boards.py` and skips, with the reason, when it is absent.

## Environment (S0-verified on this Windows 11 host)

- venv: `.venv\Scripts\python.exe` (Python 3.13.5). Pins: `requirements.txt` / `requirements.lock`.
- KiCad **pinned 10.0.3** through `.claude/skills/hwde/scripts/lib/env.py` - always resolve
  kicad-cli/bundled-python through it (kicad-cli is NOT on PATH; 9.0.5 installed as fallback;
  never mix versions - formats are not forward-compatible).
- `check.cmd` = the `make check` equivalent (host has no make). Tests: `.venv\Scripts\python -m pytest`.
- `tools/` (gitignored): portable Temurin 25 JRE + freerouting-2.2.4.jar (Freerouting needs
  Java 25; system Java 24 is insufficient). Re-fetch instructions: check_env remediation.
- Prior attempts live at `C:\dev\AI-EE` and `C:\dev\ai-ee2`: consult their LEARNINGS for
  machine-verified FACTS only (pointer entry in LEARNINGS.md) - never port their architecture.

## Environment - Linux container (2026-08-27, `docker/`)

The same toolchain runs on Linux inside the image built from `docker/Dockerfile`
(base `kicad/kicad:10.0.5`: kicad-cli 10.0.5 + python 3.13.5 with SWIG pcbnew +
symbol/footprint libs + libngspice; plus Node/Claude Code, the venv from
`requirements.lock` at `/opt/venv` linked to `.venv`, Temurin 25, Freerouting
2.2.4, KiCadRoutingTools 0.19.0, TeX Live). In the container:

- venv python is `.venv/bin/python` (read `.venv\Scripts\python.exe` in the docs as that).
- tool pins are env vars (`HWDE_KICAD_CLI`, `HWDE_JAVA`, `HWDE_FREEROUTING_JAR`,
  `HWDE_KRT_DIR`, `HWDE_NGSPICE_DLL`); `tools/` is unused there.
- `make check` = pytest + `check_env --quiet`; `make env` = `check_env --full`.
- Unattended board runs: `hwde-loop <board>` inside the container (rules:
  `docker/run-contract.md`); build/run commands in `docker/README.md`.

## Environment - Linux host without the container (2026-09-24)

When a session may not start containers, the same toolchain runs from user space
(no root): KiCad 10.0.6 debs from the `kicad/kicad-10.0-releases` PPA plus their
Ubuntu 26.04 library debs, unpacked with `apt-get download` + `dpkg-deb -x` into
`~/.local/kicad10`, with `bin/kicad-cli` and `bin/python3` wrappers that set
`LD_LIBRARY_PATH` (include the `sdl2-classic` and `pulseaudio` subdirs) and
`PYTHONPATH` (SWIG pcbnew for the host python 3.14). eeschema (ERC, netlist
export) also needs the `libwebkit2gtk-4.1-0` closure unpacked the same way;
chase `ldd usr/bin/_eeschema.kiface | grep "not found"` until it is empty. Before any hwde script:
`. ~/.local/kicad10/hwde-env.sh`. The venv is host python 3.14 with
`requirements.lock` minus `pywin32`; `tools/` holds Freerouting 2.2.4 and a
Temurin 25 JRE. SWIG Specctra paths need a display: `Xvfb :99 &` first.
