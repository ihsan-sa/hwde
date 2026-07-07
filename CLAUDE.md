# ai-ee3 - AI PCB design skill (staged build)

Building the `/ai-ee` Claude Code skill per `SPEC.md` + `ai-ee-implementation-plan.md`,
**one plan step per isolated session** to preserve context. `PROGRESS.md` tracks state.

## "run step N" protocol

When the user says `run step N` (or just `step N`):

1. Read `PROGRESS.md` (status board + interface notes of completed steps) and the S<N>
   entry in `ai-ee-implementation-plan.md`. Read ONLY the spec sections that entry lists
   (S13 alone reads the whole spec). Do not load prior steps' code beyond what the entry needs.
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

## Environment (S0-verified on this Windows 11 host)

- venv: `.venv\Scripts\python.exe` (Python 3.13.5). Pins: `requirements.txt` / `requirements.lock`.
- KiCad **pinned 10.0.3** through `.claude/skills/ai-ee/scripts/lib/env.py` - always resolve
  kicad-cli/bundled-python through it (kicad-cli is NOT on PATH; 9.0.5 installed as fallback;
  never mix versions - formats are not forward-compatible).
- `check.cmd` = the `make check` equivalent (host has no make). Tests: `.venv\Scripts\python -m pytest`.
- `tools/` (gitignored): portable Temurin 25 JRE + freerouting-2.2.4.jar (Freerouting needs
  Java 25; system Java 24 is insufficient). Re-fetch instructions: check_env remediation.
- Prior attempts live at `C:\dev\AI-EE` and `C:\dev\ai-ee2`: consult their LEARNINGS for
  machine-verified FACTS only (pointer entry in LEARNINGS.md) - never port their architecture.
