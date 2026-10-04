# Using hwde

How to run hwde, what it promises, and where each answer lives. The repository's [README](../README.md) shows what it has made.

An AI PCB engineer for KiCad + JLCPCB, packaged as a Claude Code skill
(`.claude/skills/hwde/`) and invoked as `/hwde <task>` or
`/hwde --resume <workspace>`. It takes a task in any project state - review
this board, fix these findings, move a part, re-route a net, make a footprint,
DFM, order, resume - and the full brief-to-order pipeline is one of those tasks.

Everything it produces lives in a per-board workspace under `~/dev/boards/<name>`
(brief, research, architecture, parts, lib, kicad, routing, reports, fab, log,
`state.json`), in the separate boards repo (set by `HWDE_BOARDS_ROOT`, default
`~/dev/boards`) - this repo holds no boards. Part numbers (`PCB-NNNN-R`) come
from `~/dev/boards/register.yaml`, read-only from here; a board not in it
carries no number. The design work is done by subagents; the deterministic
work is done by 57 scripts (plus 24 library modules) under
`.claude/skills/hwde/scripts/`, each with the same CLI contract (argparse,
JSON out, exit 0/1/2, no interactivity).

Pictures of the boards it has designed, and how it works, are on the
repository's [front page](../README.md).

## Maturity: supervised engineering assistant, not an unattended release system

Boards have been designed, fabricated and ordered with it, and the checker
corpus is real. It is still a system a human engineer drives and signs off:

- A green gate proves the checks that RAN, not the checks it lists. Coverage is
  being made explicit (v3 step U2); until then read the per-check report, not
  just the gate verdict.
- Workflow phase (`P9`, `P10`) is **not** a release certificate. Release
  attestation is v3 step U5; today the human decides what is releasable.
- Ordering is deliberately hard to do by accident. There is no public JLCPCB
  DFM API, so that review stays a human browser step. The credentialed API is
  wired but split: `order_submit --api` is quote-only, and `--api-create` - the
  only code path that spends money - refuses 4+ layer boards outright, refuses
  any board whose `fab/order.json` already records an order, refuses after an
  ambiguous create attempt until a human clears it, and requires a fresh quote,
  a matching normalized design hash, and a typed confirmation token.
- Known limits per stage are listed in the skill playbook and in `LEARNINGS.md`;
  the maturity of each piece of knowledge is tracked in
  `design/ladder-triage.md`.

## Authority map

One current authority per question. Where two documents disagree, the one named
here wins.

| Question | Authority |
|---|---|
| Environment, toolchain pins, host facts, session protocol | `CLAUDE.md` |
| How the skill operates (verbs, stages, gates, agent contracts) | `.claude/skills/hwde/SKILL.md` + `reference/tasks.yaml` |
| Task recipes and their exact commands | `.claude/skills/hwde/reference/recipes/` |
| Gate definitions and pass criteria | `.claude/skills/hwde/reference/gates.yaml` |
| What goes stale when something changes | `.claude/skills/hwde/reference/invalidation.yaml` |
| Per-board truth (phase, gates, decisions, holds, artifacts) | `~/dev/boards/<name>/state.json` |
| Fab capability, stackups, pricing assumptions | `.claude/skills/hwde/reference/jlc_capabilities.yaml`, `stackups.yaml`, `jlc_pricing.yaml` |
| Non-obvious gotchas, dated and tagged | `LEARNINGS.md` (index: `design/ladder-triage.md`) |
| Build state of the skill itself | `PROGRESS.md` |
| Original architecture and rationale | `SPEC.md` - **historical**, not normative |

`SPEC.md` is design evidence from the v1 build and is knowingly out of date on
platform, toolchain and API details (its kipy/api-server assumption never
materialised; see the verify-later register in `PROGRESS.md`). Read it for
intent; take facts from `CLAUDE.md` and `SKILL.md`.

Plans are historical once their steps are done: `ai-ee-implementation-plan.md`
(v1, frozen), `ai-ee-v2-plan.md` (v2), `hwde-v3-plan.md` (v3, in progress).

## Safety boundary

- The skill never spends money on its own. Exactly one code path can place an
  order (`order_submit --api-create`), it is 2-layer only, and it will not run
  without a human-typed confirmation naming the board, the quantity and the
  all-in total from the real quote. Everything else - including the 4-layer
  route - stops with the package and the checklist in hand.
- Anything irreversible (order submission, board file surgery on a fabricated
  design, credential use) is gated on an explicit human decision recorded in
  `state.json`.
- Fabricated boards are treated as frozen: a shipped design is reviewed and
  reworked, not silently re-edited.
- Electrical and thermal checks are engineering SCREENS with stated accuracy,
  not certification. Nothing here substitutes for a design review by the
  responsible engineer, and no output is safety-certified for mains, medical,
  automotive or aerospace use.

Board workspaces are not in this repo - they live in the separate boards repo,
`~/dev/boards/<name>` (`HWDE_BOARDS_ROOT`).

## Repo layout

    .claude/skills/hwde/  the skill: SKILL.md, agents/, scripts/, reference/, templates/
    tests/                pytest suite incl. the golden corpus + mutants
    design/               knowledge-ladder triage and stage evaluations
    docker/               Linux container image + the unattended run loop
    tools/                gitignored: portable JRE + Freerouting jar

Run the suite with `check.cmd` (the `make check` equivalent on this host).

Every push, and every pull request from a fork, runs the same suite on GitHub
Actions (the `checks` workflow, split into 8 `pytest` jobs inside the KiCad 10
image; the live-API `net` tests are left out). A run takes about 4 minutes of wall
time (about 27 runner-minutes across the 8 jobs). A red run names its failing job: open that job's `pytest` step for the failures,
or download its `junit-N` file. The image carries KiCad 10.0.6 (the version the box runs), so the tests
marked `kicad_recorded` (numbers recorded on 10.0.3) are skipped there, with
the reason in the skip line.

## Calling hwde from another agent (MCP)

`scripts/mcp_server.py` is a local MCP server over stdio. It opens no port;
anything that listens on one needs the owner first. It gives another agent
five tools and returns hwde's own JSON from each:

- `hwde_route` routes a task to a verb and returns the bound plan. It never runs it.
- `hwde_state` reads a workspace's state (`show`, `resume` or `freshness`).
- `hwde_gate` runs one named gate on a workspace. With no name, it lists the gates.
- `hwde_dfm_check` runs the JLCPCB dfm gate. The fab files go to scratch.
- `hwde_review` reviews an existing workspace: state, then the erc,
  drc_routed, verify and dfm gates. Importing a new board stays with `/hwde`.

Every call is read-only unless it passes `"write": true`. That records gate
results in `state.json`, and a gate's `"commit"` message is refused without
it. A read-only call leaves the workspace byte-identical, because it also
deletes the `.kicad_prl` file kicad-cli creates beside a board it loads.

To register it with Claude Code, add this to the project's `.mcp.json`, with
your own absolute paths. The server needs the same environment as any hwde
script, so on the Linux host without the container it sources
`hwde-env.sh` first (see `CLAUDE.md`); inside the container, `command` is
just `.venv/bin/python` with the script as its one argument.

```json
{
  "mcpServers": {
    "hwde": {
      "command": "bash",
      "args": ["-c", ". ~/.local/kicad10/hwde-env.sh && exec ~/.local/hwde-venv/bin/python ~/dev/ai-ee/.claude/skills/hwde/scripts/mcp_server.py"],
      "env": {"HWDE_BOARDS_ROOT": "/home/you/dev/boards"}
    }
  }
}
```

`mcp_server.py --tools` prints the tool table. `tests/test_mcp_server.py`
drives the server over stdio against a frozen fixture workspace.

## License

MIT - see [LICENSE](../LICENSE). Vendor datasheets, component 3D models and footprints
pulled from LCSC/EasyEDA are third-party material, not under MIT - see [NOTICE](../NOTICE).
