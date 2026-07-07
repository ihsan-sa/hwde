---
name: ai-ee
description: End-to-end AI PCB design pipeline (brief -> architecture -> schematic -> placed & routed board -> verified -> DFM-checked -> order-ready JLCPCB package). UNDER CONSTRUCTION - the orchestrator playbook lands at plan step S13. Do not invoke as a skill yet; see PROGRESS.md at the repo root for build state.
---

# ai-ee (skeleton - not yet operational)

This skill is being built per `SPEC.md` and `ai-ee-implementation-plan.md` at the repo root,
one plan step per session ("run step N" protocol in the repo CLAUDE.md).

Working today:

- `scripts/check_env.py` - toolchain validation. Run with the repo venv python;
  `--full` adds live probes (SWIG pcbnew roundtrip, IPC reachability). JSON to stdout,
  exit 0/1/2.
- `scripts/smoke_ipc.py` - how/whether the KiCad IPC API is reachable on this machine.
- `scripts/lib/env.py` - single source of truth for tool discovery (KiCad pin, Java,
  Freerouting jar). AIEE_* env vars override for tests.

Everything else arrives per the plan (S1-S14). PROGRESS.md is the source of truth.
