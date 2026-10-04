# Design evals: how hwde scores a PCB design against measured truth

This is the research and the design for hwde's design evals. It answers three
questions: how good evals are built, how much detail a design brief should give
the model, and which PCB quality signals can be measured and how. The last
section says what the build does and how much the full suite would cost.

The rule that runs through all of it: a score is only as good as the ground
truth it was checked against. Every grader here is deterministic code. Each one
is trusted to the degree it has been measured against something real: planted
faults it must catch, findings a person judged, a simulation against the
brief's numbers, or a board on the bench.

## 1. How good evals are built

### Task design

The benchmarks that held up share one shape. Each task is a real piece of work
with a hidden, executable check.

- **SWE-bench** takes 2,294 GitHub issues from 12 Python repos and grades a
  patch by running the repo's own tests that the human fix made pass
  ([Jimenez et al. 2023](https://arxiv.org/abs/2310.06770)). The grader is
  code, so it is cheap and repeatable.
- **SWE-bench Verified** exists because many of the original tasks were
  broken: the issue was too vague or the tests rejected correct fixes.
  93 developers screened samples, and 500 good tasks were kept
  ([OpenAI 2024](https://openai.com/index/introducing-swe-bench-verified/)).
  The lesson is that a task set needs an audit pass, and the scorer must be
  shown to accept a correct answer before it is trusted to reject a wrong one.
- **MLE-bench** grades 75 Kaggle competitions against each one's human
  leaderboard, so a score means "would have won a bronze medal", not an
  arbitrary number ([Chan et al. 2024](https://arxiv.org/abs/2410.07095)).
  Anchoring to human results is what hwde's human-board corpus is for.
- **VerilogEval** and **RTLLM** grade generated RTL by simulating it against a
  reference testbench ([Liu et al. 2023](https://arxiv.org/abs/2309.07544),
  [Lu et al. 2023](https://arxiv.org/abs/2308.05345)). VerilogEval v2 added
  in-context examples and failure classification, and reports how the prompt
  shape moves the score ([Pinckney et al. 2024](https://arxiv.org/abs/2408.11053)).
  NVIDIA's **CVDP** widens this to verification and agentic tasks
  ([2025](https://arxiv.org/abs/2506.14074)).
- **AnalogCoder** grades generated analog circuits by SPICE against
  functional specs ([Lai et al. 2024](https://arxiv.org/abs/2405.14918)).
- **EEBench** is the closest to hwde: held-out board-design tasks, SPICE at
  worst-case tolerance corners, and BOM cost as 35 % of the score
  ([methodology](https://eebench.org/methodology.html)). It stops before
  layout. hwde's E2E bench already copies its method and extends it to layout
  (`reference/e2e-scoring.md`). The other PCB benchmarks in
  `docs/competitive-research.md` (DesignSCH-Bench, NetlistBench, EEE-Bench,
  PCBSchemaGen) grade schematics or netlists. HWE-Bench grades board-level
  schematics by ERC and simulation on 300 tasks, and the best model passes
  8 % ([Qiu et al. 2026](https://arxiv.org/abs/2603.18102)). OmniLayout and
  OmniRouting score placement and routing on 1,681 industrial layouts
  ([2026](https://arxiv.org/abs/2607.03261),
  [2026](https://arxiv.org/abs/2608.04434)). None grades a routed board
  against measured hardware.

What this means for hwde: a task is a brief, the hidden check is a
`bounds.yaml` plus the deterministic checks, and the task set gets an audit
(a known-good board must score full marks before a brief is used).

### Held-out sets and contamination

A score on a task the system has seen measures memory, not skill. Three
defences are in use across the field:

1. **Keep the answers hidden from the system under test.** SWE-bench+ found
   that 33 % of SWE-bench "solves" had the fix written in the issue or its
   comments, and 31 % passed only because the tests were weak; filtering them
   cut one agent's resolve rate from 12.5 % to 4.0 %
   ([Aleithan et al. 2024](https://arxiv.org/abs/2410.06992)).
2. **Use tasks newer than the model.** LiveCodeBench dates every problem and
   scores a model only on problems after its training cutoff
   ([Jain et al. 2024](https://arxiv.org/abs/2403.07974)), and SWE-bench-Live
   adds fresh GitHub issues continuously for the same reason
   ([Zhang et al. 2025](https://arxiv.org/abs/2505.23419)).
3. **Detect copying.** MLE-bench runs a plagiarism detector over submissions.

hwde's risks are concrete. The hidden bounds sit in `tests/`, and near-twin
finished boards sit in `~/dev/boards`, both readable by a design session. The
pipeline architecture already answers this: design runs go in a sandbox that
cannot read `tests/`, `results/` or the boards repo, and held-out briefs, their
bounds and the human corpus are aggregate-only to any loop that edits hwde. The
calibration briefs (bb-ldo, bb-buck, bb-adc, bb-amp) are contaminated by
design: they check the scorer, never hwde.

### Who grades, and when each is trusted

| grader | trusted for | not trusted for |
|---|---|---|
| Programmatic (code) | anything with a computable answer: ERC/DRC counts, SPICE against a bound, clearance margins, cost | judgement calls with no computable answer |
| Model-graded (an LLM judge) | ranking prose, triage suggestions | a score. Judges show position, verbosity and self-preference bias ([Zheng et al. 2023, MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)), and a judge from the same family as the designer grades its own blind spots |
| Human expert | ground truth on a sample: is this finding real, did this board work | scale, and repeatability across days |

So every score in this design comes from code. People are used to measure the
code: the owner's verdicts on flagged findings set each check's precision, and
bench measurements set whether a high score predicts a working board. A model
may draft a triage verdict, but it only counts once a person confirms it.

Anthropic's agent-eval guide gives the same three grader types and advises
starting with 20 to 50 tasks
([2026](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).

### Variance: seeds, repeated runs, confidence intervals

Two kinds of noise matter and they need different treatment.

- **Scoring noise** is zero by contract here. Frozen board, pinned KiCad,
  same score every time (`bench.py`'s determinism contract). Any CI on frozen
  boards reflects which boards were sampled, not measurement noise.
- **Generation noise** is large. An agent run is not seedable, so "seed" means
  "repeat number". Published guidance is to run each task several times, report
  the mean with a standard error, cluster the error by task when tasks contain
  repeats, and compare two systems by paired differences on the same tasks
  rather than by two independent means
  ([Miller 2024, "Adding Error Bars to Evals"](https://arxiv.org/abs/2411.00640)).

The suite therefore reports the mean with a 95 % interval from a cluster
bootstrap: resample briefs (or boards), then repeats within each. With five
briefs the interval will be wide, and the report says so instead of hiding it.

### pass@k against mean score

pass@k is the chance that one of k tries succeeds, and its unbiased estimator
comes from the Codex paper ([Chen et al. 2021](https://arxiv.org/abs/2107.03374)).
It fits a setting where a verifier picks the winner. A board designer ships one
board, so the headline is the **mean score** per brief. hwde's gates do act as
a verifier, so pass@k on "gate-green board" is reported as a secondary number.
The reliability view is **pass^k**, the chance that all k tries succeed
([Yao et al. 2024, tau-bench](https://arxiv.org/abs/2406.12045)): an owner
cares whether every run gives a usable board, not whether one in three does.

### Cost per run

Every result records tokens, dollars and wall-clock beside its score
(`informational` in bench's contract, never in the composite). MLE-bench and
METR's long-task work both report compute beside capability
([Kwa et al. 2025](https://arxiv.org/abs/2503.14499)), because a score bought
with ten times the spend is a different result. For hwde a full design run is
the expensive unit: about $60 of API-equivalent spend and five hours on the
rp2040-mini track, so the suite size is set by that (section 4).

### Keeping a benchmark useful once it saturates

Benchmarks stop telling systems apart when everyone scores near the top.
The fixes in use are a verified hard subset, fresh tasks on a schedule, and
harder tiers. For hwde:

- The brief set is versioned and grows by tier (2-layer block, 4-layer mixed
  signal, power stage, RF). Scores are reported per tier and per suite version
  and are never compared across versions.
- A brief that every arm passes at full marks moves to a regression set. It
  stays as a guard and leaves the headline.
- Held-out briefs rotate in once a brief has been seen by a fix loop.

## 2. How much detail to give the model

This is a measured variable, not a choice. The experiment:

**Three detail levels per brief.**

| level | what it carries |
|---|---|
| terse | one or two lines: what the board does and every requirement, nothing else |
| typical | today's `brief.md`: the requirements in prose |
| full | typical plus an explicit spec: operating conditions, layer count, preferred parts, layout guidance, test points |

**Every level states the same requirements, and no level states a hidden
bound.** The requirements are the voltages, currents, tolerances and
connectors the board must meet. The hidden bounds (area, cost, decap
distance) are quality thresholds that, as in EEBench, the designer is judged
against without being told, and that is equally true at every level. So what
changes across levels is context and guidance, and the experiment doesn't
measure mind-reading. `tests/test_bench_scorecard.py` checks both halves for
every variant: each requirement number in `brief.md` appears in the variant,
and no bound's number does. A fourth, underspecified level, which leaves out
a requirement, measures whether the model asks or picks a sane default; it is
a later experiment, because it needs an "asked a question" grader.

**Design.** Same brief, same hidden bounds, same hwde commit, same model.
Levels × repeats, paired within brief. The analysis is the paired difference
(typical minus terse, full minus typical) per brief with a cluster bootstrap
interval. With per-run spread around 10 points, 5 briefs × 3 repeats gives 15
pairs per contrast, enough to see a difference of about 7 points; a pilot with
one brief and two levels can only check that the harness works and estimate
the spread.

**What is recorded beyond the score.** Cost and wall-clock per level, because
a longer brief may buy the same board for less spend. Also the number of
clarifying questions, assumptions written to the workspace, and which area
moved: guidance is expected to move layout and cost, and the spec to move
schematic correctness.

The brief variants live beside the brief as `brief.terse.md` and
`brief.full.md`, with `brief.md` the typical level, so `bounds.yaml` is shared
and a variant can't drift from its bounds. The pilot briefs are `ldo_3v3` and
`buck_3v3`. `ldo_3v3` is a calibration brief (the bb-ldo twin), so a run on
it checks the harness and the experiment's plumbing, not hwde; `buck_3v3` is
held out.

## 3. Which PCB quality signals are measurable

Five areas. The Normal proposal names layout, signal integrity and schematic;
power and manufacturing are split out because they are where fabbed boards
fail and they are measured by different code.

| signal | area | how it is measured | code |
|---|---|---|---|
| ERC errors | schematic | kicad-cli ERC, error count | gate-erc / bench E2E |
| connectivity and pin types | schematic | netlist audit findings | `netlist_audit.py` |
| part ratings | schematic | voltage, current and power derating per part | `check_ratings.py` |
| simulation against spec | schematic | SPICE at tolerance corners, fraction in bounds | `e2elib` (needs a brief) |
| requirements met | schematic | each requirement traced to evidence | `check_requirements.py` |
| DRC errors | layout | kicad-cli DRC error count | gate-drc_routed |
| routing completion | layout | unrouted connections | bench E2E live leg |
| area, crossings, decap distance | layout | outline area, ratsnest crossings, worst decap mm | `place_metrics`, `check_decoupling.py` |
| mechanical fit | layout | connector mating clearance | `check_mating.py` |
| return path | signal integrity | signals crossing plane splits or voids | `check_return_path.py` |
| diff pairs and impedance | signal integrity | Z0/Zdiff from the stackup, skew, coupling | `check_diffpair.py`, `lib/impedance.py` |
| route style | signal integrity | acute angles, stubs, needless arcs | `check_route_style.py` |
| PDN | power | decap count and placement, target impedance | `check_pdn.py`, `check_pdn_z.py` |
| IR drop and current | power | copper width against current, voltage drop | `check_irdrop.py`, `check_current.py` |
| thermal | power | dissipation against copper area | `check_thermal.py` |
| creepage | power | HV clearance | `check_creepage.py` |
| DFM margins | manufacturing | worst margin against JLC capability | gate-dfm report (read only) |
| silk | manufacturing | silk on pads, legibility | `check_silk.py` |
| BOM cost | manufacturing | USD per board at qty | `parts.json` price breaks |
| BOM risk | manufacturing | lines without stock, extended parts, single sources | `parts.json` |
| failure-mode coverage | all | which failure modes the board was checked for | `docs/failure-modes.yaml` (pcb-failure-research) |
| bring-up | ground truth | rails, currents, functions against npie limits | npie run records |

**How a check becomes a score.** A raw finding count is not empirical: some
checks are mostly noise. The check scorecard (`score_checks.py`) already
measures each check's precision from triaged findings and its recall from
planted faults. On 2026-09-29, check_current had precision 0.01 and
check_creepage 0.32. So a finding counts by its check's measured precision: an
area's expected real defects is the sum over its findings of severity weight
× precision, and the area score is `1 / (1 + expected real defects)`. The
precision is shrunk toward 0.5 by its sample size, `(tp + 1) / (tp + fp + 2)`,
so a check with two triaged findings is not taken as certain and a check
nobody has triaged counts at 0.5. A triaged finding counts 1 if real and 0 if
not. A waived finding still counts, because a waiver is the designer's call,
not a verdict. When the owner triages more findings, the score gets more
accurate without any code change.

**Failure modes.** pcb-failure-research owns the failure-mode taxonomy in
`docs/failure-modes.yaml`. This design does not copy it. Each finding carries a
`failure_mode` id, filled in from that file's check-to-mode map once it lands,
and the scorecard reports which modes a board was checked against and which
have no check.

**Bring-up and expert review: the empirical link.** These are the ground truth
the scores are checked against, and they never feed a fix loop.

1. *Predictive validity.* For every board that returns from fab, npie's run
   record gives a pass/fail per bring-up stage and measured values against
   limits. The test is whether area scores separate boards that worked from
   boards that didn't (rank correlation, and per area: did a low power score
   precede a rail failure?).
2. *Finding precision.* The owner reviews the top findings on each board, human
   boards included. Each verdict goes to `triage.yaml` and sets that check's
   precision, which feeds the scores above.
3. *Human anchor.* Professionally made boards from the human-board corpus
   should score high. A check that flags many real-looking problems on boards
   that are known to work is miscalibrated. This plays the part MLE-bench's
   human leaderboard plays.
4. *Sensitivity.* A planted fault must lower its area's score (the mutant
   corpus). A score that doesn't move under a known fault isn't measuring
   anything.

Composite weights stay provisional until (1) has enough boards to fit them.
Until then the scorecard leads with the area scores and the composite is
secondary.

## 4. What is built, and what it costs

### Built in this row

- **One results store.** JSONL under `results/`, one record per scored run,
  keyed by hwde commit, KiCad version, harness, model, fixture or board, seed
  and detail level. bench.py appends to it; the markdown tables are generated
  from it.
- **One finding shape.** `check, kind, refs, net, pos, severity,
  failure_mode, ladder`, plus `fix`: one sentence saying what to change. The
  first six match `triage.yaml` already. The list is ranked by expected real
  impact (severity × the check's precision), so a model mid-design reads the
  top items and knows what to do. A later row wires it into hwde's loop.
- **A board scorecard** (`bench.py --scorecard <workspace>...` or
  `--scorecard all`): the five areas for a finished board with no brief. It
  re-runs every offline verify check and reads the recorded ERC, DRC and DFM
  gate reports. A gate that never ran is a finding. `--record` appends to
  `results/scorecard.jsonl`, and `--scorecard-report docs/design-evals.md`
  regenerates the table below from it.
- **A suite score** with a cluster-bootstrap 95 % interval, overall and per
  area. The code is `scripts/lib/evalcard.py`.
- **Brief detail variants** for the pilot briefs.

The sandboxed e2e driver and the cost pilot belong to the eval-driver row, so
this row does not run design sessions of its own.

### The bare Claude Code against hwde experiment

The same brief goes to two arms: bare Claude Code with KiCad on PATH and no
skill, and `/hwde`. Both run in the eval-driver sandbox, and both finished
workspaces go through the same E2E bench and scorecard. A bare run may not
produce a board at all; that scores 0 on layout and is reported as "no board",
because a missing artefact is a result. The comparison is paired by brief, and
the findings lists show where each arm fails. In the pilot it would run on the
cheapest brief (`ldo_3v3`) once the eval-driver's sandbox exists.

### Cost of the full suite

A full hwde run of one board cost about $60 API-equivalent over five hours
(rp2040-mini, 16 loop iterations). A bare Claude Code run is likely a third of
that, but nobody has measured it.

| block | runs | estimate |
|---|---|---|
| 5 held-out briefs × 3 repeats × 2 arms (bare, hwde), typical detail | 30 | about $1,200 and 100 box-hours |
| detail levels: 5 briefs × terse and full × 3 repeats, hwde | 30 | about $1,800 and 150 box-hours |
| total | 60 | **about $3,000 and 250 box-hours, about 5 days at 2 runs at a time** |

These are on a subscription in practice, so the real limit is box time and the
usage cap, not dollars. That is over this row's budget, so the full run goes to
the owner through the planning seat.

### Pilot on the finished boards

Every board in the boards repo at phase P9 or later, scored at no design
cost: 19 boards in about 100 seconds. The composite is the plain mean of the
five areas until bring-up results can fit weights.

<!-- SCORECARD:BEGIN (bench.py --scorecard-report writes this) -->
Suite of 19 boards, recorded 2026-10-04T11:29:05Z at hwde cd6ca77f7e6f. Scores are 0-100 with a 95 % cluster-bootstrap interval.

| area | mean [95 % CI] |
|---|---|
| composite | 71.4 [63.0, 78.1] |
| schematic | 53.0 [46.0, 59.8] |
| layout | 93.2 [81.3, 100.0] |
| SI | 52.8 [40.2, 64.9] |
| power | 75.5 [59.9, 89.1] |
| mfg | 82.3 [73.2, 90.0] |

| board | composite | schematic | layout | SI | power | mfg | findings | top finding |
|---|---|---|---|---|---|---|---|---|
| PCB-0001-A_stm32-blinky | 83.8 | 67 | 100 | 86 | 100 | 67 | 9 | check_ratings/rating_unrated |
| PCB-0002-A_usb-buck | 80.3 | 60 | 100 | 58 | 100 | 83 | 11 | check_ratings/rating_unrated |
| PCB-0003-A_pd-trigger | 76.6 | 55 | 100 | 67 | 85 | 77 | 64 | check_ratings/rating_over_voltage |
| PCB-0004-A_lumina-carrier | 47.1 | 35 | 100 | 5 | 19 | 77 | 236 | check_decoupling/reg_input_no_hf |
| PCB-0007-A_rf-de-20m | 29.3 | 46 | 4 | 29 | 9 | 59 | 259 | check_current/undersized_track |
| PCB-0008-B_sbuck-5v3a | 71.9 | 67 | 100 | 67 | 49 | 77 | 20 | check_pdn/pdn_undecoupled |
| PCB-0009-A_rf-term-150w | 78.4 | 67 | 100 | 26 | 100 | 100 | 14 | check_return_path/corridor_void |
| PCB-0010-A_bb-buck | 77.1 | 75 | 100 | 45 | 94 | 71 | 34 | check_return_path/corridor_void |
| PCB-0011-A_bb-mcu | 84.0 | 60 | 100 | 60 | 100 | 100 | 8 | check_ratings/rating_unrated |
| PCB-0012-A_bb-ldo | 95.0 | 75 | 100 | 100 | 100 | 100 | 6 | check_ratings/rating_unrated |
| PCB-0013-A_bb-amp | 76.9 | 50 | 100 | 55 | 100 | 80 | 13 | check_silk/silk_misattributed |
| PCB-0014-A_bb-adc | 81.8 | 55 | 100 | 55 | 100 | 100 | 11 | check_ratings/rating_unrated |
| PCB-0015-A_g0-sense | 70.9 | 46 | 100 | 50 | 87 | 71 | 19 | check_ratings/rating_unrated |
| PCB-0016-B_pd-trigger-lite-dip | 84.5 | 60 | 100 | 75 | 97 | 91 | 17 | check_ratings/rating_unrated |
| PCB-0018-A_bldc-motor-driver | 33.2 | 23 | 100 | 8 | 7 | 28 | 514 | check_creepage/creepage |
| PCB-0019-A_rp2040-mini | 60.7 | 50 | 100 | 11 | 43 | 100 | 65 | check_decoupling/reg_input_no_hf |
| PCB-0021-A_lipo-boost | 64.3 | 60 | 67 | 67 | 45 | 83 | 20 | check_mating/mating_faces_inward |
| PCB-0022-A_nfc-card | 86.3 | 32 | 100 | 100 | 100 | 100 | 13 | check_ratings/rating_unrated |
| PCB-0022-B_nfc-card | 73.6 | 25 | 100 | 43 | 100 | 100 | 26 | check_ratings/rating_unrated |
<!-- SCORECARD:END -->

What the pilot shows. The spread is real: bb-ldo, a one-part block, scores
highest, and the 4-layer motor driver and the RF board score lowest, with
hundreds of power and signal-integrity findings each. Most findings are
untriaged, so most of every score rests on smoothed check precision rather
than on a verdict. That is the case for the owner's review: each verdict on a
top finding moves both that board's score and every board's score for that
check. Schematic scores are low across the board mainly from `check_ratings`
reporting parts with no voltage rating in `parts.json`. That is a gap in the
design record rather than a proven defect, and triage will say which.

## Against the Normal proposal

Where this follows it:

- Separate evals for layout, signal integrity and schematic, both to judge
  finished boards and to feed the model so it can judge its own work. The
  findings list, ranked and with a fix line, is the feed.
- Human-made boards go through the same evals, and the owner reviews and
  verifies the flagged feedback.
- The same brief goes to bare Claude Code and to hwde, and the evals say how
  the boards differ.

Where it departs, and why:

- **Two more areas.** Power and manufacturing are split out from layout,
  because they are measured by different code and are where fabbed boards fail.
- **The model never grades.** The proposal leaves the grader open; here every
  score is code, and the owner's review measures the code instead of scoring
  boards. That keeps scores repeatable and cheap to re-run.
- **Not everything is fed back.** Offline check findings go to the model mid-
  design. Held-out scores, the human corpus, bring-up and expert review do not,
  because a loop that sees its test learns the test.
- **Weights wait for hardware.** The composite is provisional until bring-up
  results can fit it.

## What I did not verify

The design-run cost is one track's loop log, not a measured average. The
precision figures come from the 2026-09-29 scorecard line. The citations were
checked for title, author and link, not re-read in full.
