# hwde

An AI PCB engineer for KiCad + JLCPCB, packaged as a Claude Code skill
(`.claude/skills/hwde/`) and invoked as `/hwde <task>` or
`/hwde --resume <workspace>`. It takes a task in any project state - review
this board, fix these findings, move a part, re-route a net, make a footprint,
DFM, order, resume - and the full brief-to-order pipeline is one of those tasks.

Everything it produces lives in a per-board workspace under `boards/<name>/`
(brief, research, architecture, parts, lib, kicad, routing, reports, fab, log,
`state.json`). The design work is done by subagents; the deterministic work is
done by 57 scripts (plus 24 library modules) under
`.claude/skills/hwde/scripts/`, each with the same CLI contract (argparse,
JSON out, exit 0/1/2, no interactivity).

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
| Per-board truth (phase, gates, decisions, holds, artifacts) | `boards/<name>/state.json` |
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

## Repo layout

    .claude/skills/hwde/  the skill: SKILL.md, agents/, scripts/, reference/, templates/
    boards/               board workspaces (see boards/README.md)
    tests/                pytest suite incl. the golden corpus + mutants
    design/               knowledge-ladder triage and stage evaluations
    tools/                gitignored: portable JRE + Freerouting jar

Run the suite with `check.cmd` (the `make check` equivalent on this host).

## License

MIT - see [LICENSE](LICENSE). Vendor datasheets, component 3D models and footprints
pulled from LCSC/EasyEDA are third-party material, not under MIT - see [NOTICE](NOTICE).
