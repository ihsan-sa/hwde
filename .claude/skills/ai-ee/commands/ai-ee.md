# /ai-ee - AI PCB design pipeline

Usage:
- `/ai-ee <board description>` - start a new design run (attach docs freely:
  requirements, datasheets, mechanical constraints - they land in `brief/`).
- `/ai-ee --resume <workspace>` - continue a run from its `state.json`
  (e.g. `/ai-ee --resume boards/rf-amp-ctrl`).

On invocation:
1. Read `.claude/skills/ai-ee/SKILL.md` (the orchestrator playbook) and
   follow it exactly - it defines the phase machine, gates, fix loops,
   state recording, and human checkpoints.
2. New run: derive a short kebab-case board name from the description,
   create `boards/<name>/`, run `scripts/check_env.py`, `state.py init`,
   and enter P0 (requirements intake).
3. Resume: `state.py resume --workspace <ws>`, log the resume event, and
   re-enter at the next unmet gate or checkpoint.

The orchestrator never opens design files; all design work happens in
spawned subagents using the role prompts in `.claude/skills/ai-ee/agents/`.
