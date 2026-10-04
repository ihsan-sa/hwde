# hwde, evals, fwe and npie as one improving pipeline

Architect, 2026-10-04. Asked for by the owner. Built from a read-only map of today's code, a blind design by a second model, and a critic who checked the draft against the code. File:line references are from that check.

## The answer in short

The owner is right that the IP is in the tools. hwde has about 56k lines of Python against about 5.8k lines of prose, no script calls Claude, and gate order is already code. A "thin harness" works if it means **the plan is data and the gates are code**. It doesn't work if it means the model improvises the process. What the prose carries today and would lose (fresh-context reviewers, spawn tiers as a cost dial, web tools only for the researcher, the fix-loop re-order rule) moves into data that every harness binding reads.

The eval loop comes first in the schedule, not last. The five held-out e2e briefs have never run, and the full suite will take about 4-8 days of box time. So it has to start in week two to land in early November.

## Layers

1. **Tools.** The scripts stay as they are, under the SPEC §6 contract. The CLI is the front door, because the MCP server handles one request at a time with a 3600 s timeout (mcp_server.py:55, 312-327). The MCP server grows from 5 review tools to the core verbs plus `next`. A catalogue (name, purpose, inputs, outputs, side effects, cost class) is written by hand for the ~15 tools agents call directly, with flags captured from each script's `main(argv)`. The remaining ~70 come later, and only if someone needs them.
2. **Plan and state as data.** `state.py resume` already returns next_gate, gates_stale, pending_human and open_issues (state.py:834-870), and tasks.yaml already has a step grammar. Two things are still prose: the full-run body (one `note:` pointing at 68 lines) and the spawn rules (SKILL.md:218-249). They become `full-run` steps in tasks.yaml and a `roles.yaml` (role, model tier, tool scope, fresh context yes or no). `task_router.py --next --workspace W` is the plan cursor, built on resume and tested by the existing tests/orchestrator/dryrun.py. The spawn ledger becomes mandatory, because without it nobody can tell whether a harness dropped the fresh reviewer.
3. **Owner holds become real.** Today the agent records the owner's approval itself (`state.py human`, state.py:1112), and waivers carry a self-written `approved`. An H1-H5 verdict and an approved waiver must carry the owner's own mark (an approval file the owner writes, or a Slack-approval record from the box), and `set_phase` refuses without it. Until then, the evals count agent-written waivers as a penalty.
4. **Harness bindings.** Each one is generated from roles.yaml plus the entry text: the Claude Code skill, and for Codex an AGENTS.md and agent config (Codex CLI 0.153.4 is on the box). The test is gate parity: re-run the gates on one finished board under Codex, and they must match exactly. That's the first step of the box's any-harness plan (docs/any-harness), done by hand first. Generated adapters wait for that run and for the box's sandbox for other harnesses (iiks1 PR #751).

## The eval loop

- **One results store.** JSONL under `results/`, appended by bench.py, score_checks.py and the corpus run. Each run is identified by hwde commit, KiCad version, harness, model, fixture or board, and seed. The markdown tables are generated from it. A vendored hwde in the boards repo writes to ai-ee's store, never to its own copy.
- **One finding shape**: check, kind, refs, net, pos, severity, failure-mode id (the pcb-failure-research taxonomy), and ladder level. triage.yaml already matches on the first six.
- **What the loop may see.** Offline metrics are visible. Held-out briefs, their bounds and the human-board corpus are aggregate-only. Bring-up and expert review feed the writeup and the scorer's weights, never a fix row. A design run (any arm, bare Claude Code included) runs in a sandbox that can't read tests/, results/ or ~/dev/boards, because today the hidden bounds are readable and near-twin boards sit next door.
- **Findings become work, without gaming.** An `eval_dispatch.py` turns ranked findings into ai-ee rows, the way fix_dispatch.py turns gate failures into work orders on a board. At most 3 eval-loop rows are open at once. A fix row may not touch scorers, checks, bounds, fixtures or waivers. A row's done-check is the deterministic suites (per-stage bench, check scorecard, placement corpus) showing the target finding count drop with no regression.
- **The model-driven e2e suite is a periodic report, not a done-check.** It runs on a tagged, frozen hwde commit: 5 held-out briefs × 3 or more seeds × arms (bare Claude Code, hwde today, and later hwde + `--next` single agent), with spreads. It re-runs when hwde is re-tagged or the scorer changes, never nightly. A frozen board re-scores identically by contract. The brief set grows and rotates, so the held-out set doesn't get burned.
- **Hardware is the ground truth.** npie run records and the corpus's outcome labels land in the same store and check the scorer's weights once they exist.

## Contracts

There's one check-report location (today it's split between reports/checks and kicad/reports/checks), and the workspace schema version goes in state.json. CI moves to KiCad 10.0.6 to match the host, because env.py pins only the major version (env.py:41-50). A golden netlist test pins fwe's copied parser to hwde's output. fwe and npie get a `make check`, since they have no CI today. fwe's manifest carries every command's arguments.

## Schedule

The owner is away 10-10 to 10-19, so anything that needs him goes in week one.

**Week one (to 10-10):**
- Fold the results store and the finding shape into pcb-design-evals' brief, as a brief append, not a new row.
- Run one contracts row: report location, schema version, CI on 10.0.6, the golden netlist test, and make check for fwe and npie.
- Run one eval-driver row: the sandboxed e2e driver, the write-set rule for fix rows, and a cost pilot of one held-out brief × 5 seeds.
- Ask the owner for the eval budget, with the pilot's real per-run cost. The estimate is about 30-45 runs at about $750-1,100.

**Week two:**
- Tag the frozen hwde commit and start the suite, 2 runs at a time.
- Build roles.yaml, the full-run steps and `--next` (tested by dryrun.py), with the spawn ledger mandatory.
- Start eval_dispatch on the 8 open false-positive classes (check_current's precision is 0.01).
- Do the hand-run Codex gate-parity check.

**After the first suite report:**
- Make owner holds real.
- Write the catalogue for the core tools and grow MCP.
- Shrink SKILL.md, but only once the frozen runs are in the store, so the writeup compares like with like.
- Generate the Codex binding after PR #751.

## Measures

- Held-out composite with spreads, hwde against bare.
- Scorecard precision on the human corpus, plus the count of waivers agents wrote.
- Hops from a finding to a landed change (today #37 took 3 hand hops).
- Gate parity across harnesses on one board.
- Spawn-ledger coverage and how many reviews ran with fresh context.
- Cost per run, and how many placement runtimes are valid.

## Cut from the first draft

- Federating catalogues across hwde, fwe and npie.
- Remediation as JSON (25 files of judgement prose, already routed).
- A nightly re-score.
- All tools over MCP.
- The SQLite question.

## Not checked

- Whether Codex's agent config can express a fresh-context reviewer.
- Whether PR #63's held files (gate.py, dfm_check.py) collide with the `--next` work. If they do, `--next` waits for #63.
