# AI PCB design: the field in September 2026, and what hwde should build next

Written 2026-09-27 from web sources (linked inline) and hwde's own record
(`SKILL.md`, `PROGRESS.md` status boards, `LEARNINGS.md` headings, `SPEC.md` section 1.1,
the boards register). Vendor numbers are vendor claims unless a line says otherwise.

**The headline correction:** the brief's "GPT-6 Astra scores 69.3% on EEBench" has no
primary source. EEBench's own post of 2026-09-04 lists no Astra score and says the team
"would really like to find out how it handles these circuit-design tasks"
([eebench.org blog](https://eebench.org/blog/can-ai-design-circuit-boards-yet/)). The
figure circulates only on aggregator sites. The published top score is Claude Opus 5 at
61.6%.

## Landscape

| Tool | What it automates | How | How output is verified | Published results |
|---|---|---|---|---|
| [GPT-6 Astra](https://openai.com/index/gpt-6-astra/) (OpenAI) | Placement and routing from a schematic | General model driving the KiCad GUI | Not shown: the demo claims net completion only, no DRC, fab or bring-up ([Quilter's read](https://www.quilter.ai/blog/llm-pcb-layout-gpt-6-astra)) | No EEBench score yet (above) |
| [atopile](https://github.com/atopile/atopile) | Schematic capture as code, parametric part picking, reusable modules with attached layouts | Declarative `.ato` language + compiler | Compiler checks, parameter solving | None of its own; it is EEBench's substrate |
| [EEBench](https://eebench.org/) (atopile team) | Benchmark: analog + digital design loops | Held-out tasks, answer is an atopile bundle | SPICE at worst-case tolerance corners; score = 0.65 technical + 0.35 BOM cost ([methodology](https://eebench.org/methodology.html)) | Opus 5 61.6%, Grok 4.6 57.1%, Fable 5.1 56.4%, Fable 5 54.3%, Opus 4.8 Max 51.4% (2026-09-01) |
| [Quilter](https://www.quilter.ai/blog/the-next-generation-of-eda-a-2026-guide-to-ai-powered-pcb-design-tools) | Placement, routing, BGA fanout, beside Altium/KiCad | Physics-driven optimisation, many candidates | Its own physics validation, then DRC in the customer's CAD | "Project Speedrun": 27 h placement+routing, 98% routed ([guide](https://www.quilter.ai/blog/the-2026-guide-to-autonomous-pcb-design-quilter-vs-deeppcb-vs-flux-ai)); 99.4% routability on a 161-net board vs 93.8% for naive SA (`SPEC.md` 1, Apr 2026) |
| [Flux Copilot](https://www.flux.ai/p/blog/flux-copilot-under-the-hood) | Schematic, layout help, BOM, part research in a browser EDA | Tuned LLM + live part pricing; spring 2026 "self-correcting agent" | Engineer review in the tool | None found |
| [JITX](https://www.jitx.com/) | Schematic + board structure from code, SI sim dispatch | Code-first HDL; LLM edits the code, compiler is deterministic | Constraint-driven routing, HFSS EM runs, rule checks | None public |
| [DeepPCB](https://deeppcb.ai/reinforcement-learning-pcb-routing-explained/) (InstaDeep) | Placement and routing | Reinforcement learning, DRC in the reward | DRC | Public tier capped at 1,000 parts / 8 layers; no quality figures found |
| [CherryBlossom](https://www.trycherryblossom.com/) | Prompt to schematic, layout, Gerbers | LLM over plain-text TSX design files | Automatic DRC and connectivity after every AI edit | None found |
| [Circuit Mind](https://www.circuitmind.io/product) | Block diagram to schematic + BOM with part selection | Search/optimisation over a parts database | Rule-driven validation | "Schematic + BOM in 60 s" (vendor, [EE Journal](https://www.eejournal.com/article/from-architecture-to-pcb-schematic-in-60-seconds/)) |
| [Celus](https://www.celus.io/) | Requirements to block diagram, parts, schematic draft | LLM assistant + CUBO part knowledge base | Internal rules | "Up to 75% less schematic time" (vendor) |
| [Cadstrom](https://www.cadstrom.io/) | Verification only: finds design errors before fab | Reads component datasheets to infer expected behaviour, checks the design against it | It is the checker | "Up to 66% fewer design errors" (vendor) |
| KiCad MCP servers ([kicad-mcp](https://github.com/nmlsports/kicad-mcp), [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)) | Let any coding agent read a project, edit the PCB live, run DRC, export | MCP over KiCad IPC (PCB editor only until KiCad 11) + kicad-cli | Whatever the agent runs; one ships a "production-readiness gate" | None |
| Academic | RL placement ([RL_PCB](https://github.com/LukeVassallo/RL_PCB), DATE 2024); LLM netlist synthesis ([PCBSchemaGen](https://arxiv.org/pdf/2602.00510)); schematic benchmarks (ChatSCH / DesignSCH-Bench, 232 tasks; [NetlistBench](https://arxiv.org/pdf/2608.12197); [EEE-Bench](https://arxiv.org/pdf/2411.01492)) | RL with local rewards; reward-guided code synthesis | Post-route wirelength; netlist checks; graded tasks | RL_PCB beats stochastic placers on wirelength (figures not retrieved) |

Two things stand out. Every generator is either code-first (atopile, JITX, CherryBlossom)
or a GUI agent (Astra), and the only one that grades itself by physics end to end is
Quilter. And nobody but Quilter's Speedrun publishes a fabricated, working board.

## Where hwde leads

- **It goes all the way to an order.** Brief to JLC order with release attestation,
  durable waivers and real orders placed (18 boards in the register, two ordered and shipped).
  Astra stops at net completion and EEBench stops before layout.
- **It keeps a real KiCad schematic** for human review, which atopile, JITX and
  CherryBlossom give up (`SPEC.md` 1.1 rejected atopile for exactly this).
- **Gates are deterministic scripts, not model judgement:** ERC, DRC with parity, an
  8-check verify suite (creepage, current, return path, diff pairs, PDN, thermal, IR drop,
  decoupling), sim benches with bounds, gerber-level DFM, each with a clustered fix loop
  and a freshness-aware invalidation map. CherryBlossom's "DRC after every edit" is a
  subset of this.
- **It works on a board in any state** (review, fix, move, swap, reroute, intake of an
  outside project), where most tools are generate-only.
- **Research is audited:** acquisitions are allowlisted and a second reader verifies them,
  and design agents never get web tools.

## Where hwde is behind

- **No external score.** It has a stage bench on frozen fixtures (T5) but no brief-to-board
  task set and no number anyone outside can compare. EEBench shows "harness fit" moves
  scores more than model version, and hwde is exactly a harness.
- **No bring-up evidence.** Both T11 orders show Shipped and nobody has powered a board,
  so hwde's boards are DRC-clean, not proven.
- **Placement quality is unmeasured against the commercial bar.** `SPEC.md` set >=98%
  Freerouting completion and cites Quilter's 99.4%; the annealer has completion feedback,
  but no corpus-wide completion figure is recorded.
- **No field solver.** Impedance comes from tables and assumed epsilon_r (V12, V18 open);
  JITX dispatches HFSS runs.
- **No verified reusable blocks.** Every board re-derives its buck or USB front end;
  atopile ships modules with their layouts attached.
- **No datasheet-limit check.** Nothing compares a net's voltage or current against the
  absolute-maximum ratings of the pins on it, which is Cadstrom's whole product.
- **Only reachable as a Claude Code skill.** Other agents reach KiCad through MCP servers.

## Should hwde be scored on EEBench?

Yes, but not first, and not as it stands. EEBench grades atopile design bundles by
simulation and does not test layout, so it would score hwde's P2-P4 half (architecture,
parts, schematic) and none of what hwde leads on. Entering takes three things. First, an
exporter from hwde's schematic and `parts.json` to an atopile bundle, or EEBench agreeing
to accept a KiCad netlist plus SPICE deck. Second, a run mode that stops at P4 and emits
that bundle. Third, contacting the EEBench team, because submissions are not self-serve
yet ([methodology](https://eebench.org/methodology.html)). The contact goes out in the
owner's name, so it is the owner's call. The cheaper and more useful step is to copy EEBench's
method in-house first (item 1 below): hidden tasks, SPICE grading at tolerance corners,
BOM cost in the score, and then extend it to layout, which EEBench says it cannot do.

## Ranked backlog

None of these duplicates the tracks in flight (cross-stage rails U9, harvest prep U22,
SWIG writer lock). Sizes: *small* is a subagent or one sitting, *worker* is one track
with its own tests.

1. **An end-to-end task bench, scored like EEBench and extended to layout.**
   Evidence: EEBench's design (held-out tasks, SPICE at corners, 0.65/0.35 technical/cost)
   and its finding that the harness moves scores more than the model. hwde's T5 bench
   scores stages on frozen fixtures, never a brief. Gain: one number per hwde change,
   so every item below can prove itself; also the prerequisite for item 4. Size: worker.
   Files: `scripts/bench.py` (a new `e2e` stage), `tests/fixtures/stages/` (5-10 briefs
   with hidden bounds), `reference/` (scoring doc). Owner: no, though an owner-written
   brief or two would make the set harder to overfit.

2. **Power up the shipped boards (T11) and record the result.** Evidence: only Quilter
   publishes a working fabricated board; hwde has boards in the post. Gain: turns
   "DRC-clean" into "works", and a failure is the most valuable learning the skill can
   get. Size: small per board, already planned as T11. Files: board workspaces,
   `PROGRESS.md`, `LEARNINGS.md`. Owner: **yes**, the owner has to confirm arrival and do or
   watch the bring-up.

3. **Measure placement against the Quilter bar across the whole register.** Evidence:
   `SPEC.md` 1 (>=98% target, Quilter 99.4%, naive SA 93.8%); Quilter's Speedrun 98%.
   Gain: tells us whether the annealer, the largest custom investment, meets its own spec;
   if not, that becomes the next placement track with a measured baseline. Size: small
   (a batch run of `place_seed` + `place_anneal` + `route_auto` on copies of the 18 boards,
   reported in a doc), worker only if the answer is bad. Files: a report under `docs/`,
   possibly a `bench.py` P6 corpus mode; must not touch `lib/place_swig.py` while the
   writer-lock track holds it. Owner: no.

4. **Enter EEBench.** Evidence and needs: the section above. Gain: an outside number on
   the harness, which is currently the thing that separates top models. Size: worker
   (the atopile bundle exporter plus a stop-at-P4 run mode), after item 1. Files: a new
   `scripts/ato_export.py`, `reference/recipes/` (a `bench-export` recipe),
   `scripts/task_router.py` verb list. Owner: **yes**, the outreach goes in the owner's name.

5. **A datasheet absolute-maximum check.** Evidence: Cadstrom's approach
   ([cadstrom.io](https://www.cadstrom.io/)); hwde's verify suite checks copper and
   geometry but never a pin rating against the net it sits on. Gain: catches the
   respin-class error no DRC sees (an over-voltage input, a reversed rail), at P4 before
   any layout. Size: worker. Files: a new `scripts/check_ratings.py`, `reference/gates.yaml`
   (add it to `verify`), `reference/remediations/`. It reads the per-part JSON that
   `datasheet_extract.py` writes, so start after U9 releases that file. Owner: no.

6. **Verified reusable blocks.** Evidence: atopile's module registry with attached
   layouts; hwde already has a buck, USB-C PD and STM32 core that passed every gate on
   ordered boards. Gain: a known-good block is placed and routed once, and later boards
   re-use its sub-sheet, placement group and copper, which cuts P4-P7 time and risk.
   Size: worker. Files: a new `reference/blocks/` store, `scripts/board_update.py`
   (insert a block), `reference/recipes/add-part.md`, `scripts/knowledge.py` (offer a
   block at P2). Owner: no, but promoting a block to "verified" should wait for its board
   to pass bring-up (item 2).

7. **A 2D field solver for controlled impedance.** Evidence: JITX's HFSS dispatch;
   hwde's V12 and V18 (tables and assumed epsilon_r) are still open. Gain: USB, Ethernet
   and RF traces get a solved width instead of a table lookup, and the solver can be
   checked against JLC's calculator once. Size: worker. Files: `scripts/lib/impedance.py`,
   `reference/stackups.yaml`, `scripts/check_diffpair.py`, `check_env.py` (a user-space
   solver such as openEMS). Owner: no, unless the solver needs a system package.

8. **An MCP front door to hwde's verbs.** Evidence: at least two competing KiCad MCP
   servers exist and none has gates. Gain: other agents (and the other skills on this box)
   can call `review`, `dfm-check` or a gate as tools and get hwde's deterministic answers.
   Size: small to worker. Files: a new `scripts/mcp_server.py` wrapping `task_router.py`
   and `gate.py`. Owner: no for a local stdio server; **yes** before anything listens on
   a port.

9. **Render-and-compare review of placement and routing style.** Evidence: Astra works
   from what it sees on screen; hwde already renders boards but judges style only when
   the owner looks (the "straight and 45-degree routing, no needless arcs" preference is
   a memory, not a check). Gain: owner style becomes a scored review term instead of a
   correction after the fact. Size: small. Files: `agents/verify-reviewer.md`,
   `scripts/render.py` (a fixed view set), `reference/remediations/`. Owner: no, though
   the U11 routing teaching cycle is where the owner's style rules are meant to come from.

## What I did not verify

- RL_PCB's wirelength figures and DeepPCB's quality results: no numbers surfaced.
- Every Flux, Circuit Mind, Celus, Cadstrom and CherryBlossom performance claim is the
  vendor's own.
- The OpenAI Astra launch page was seen in search results, not read in full.
