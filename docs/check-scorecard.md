# Check scorecard

`score_checks.py` scores each deterministic verify check on its own, so a
change to a check shows up as a number that moved. It runs every check in
`verify_all.CHECKS` over three corpora:

- **golden**: the three golden boards. Every finding is a false positive
  unless `tests/golden/scorecard/triage.yaml` records it as a true one.
- **mutants**: the planted faults in `tests/golden/manifest.yaml`. The owning
  check catches a fault when one finding matches every key of its `expect`;
  otherwise it is a miss. `dfm_check`'s mutant is scored by `test_fab.py`,
  because dfm_check is a fab check outside the verify suite.
- **boards**: finished boards (phase P9 or later) in the boards repo. A
  finding takes its verdict from a triage entry. Findings only a waiver
  covers are `waived_untriaged`, and the rest are `untriaged`: counted, not
  scored, because nobody has judged them yet.

Precision is tp/(tp+fp) and recall is caught/(caught+misses); a dash means
the check has nothing to score there yet.

Record a run with `score_checks.py --record` after a check changes. The gate
test `tests/test_check_scorecard.py` fails when a check's false positives or
misses on the golden or mutant corpus rise above the last recorded line.

<!-- SCORECARD:BEGIN (score_checks.py --record writes this) -->
Last run 2026-10-07, compared with 2026-09-29.
Corpora: boards scored, golden scored, mutants scored.

| check | fp | misses | caught | precision | recall | change |
|---|---|---|---|---|---|---|
| check_bom_sync | 0 | 0 | 1 | 1.00 | 1.00 | new |
| check_creepage | 25 | 0 | 1 | 0.36 | 1.00 | fp 36->25 |
| check_current | 114 | 0 | 1 | 0.03 | 1.00 | fp 362->114 |
| check_decoupling | 0 | 0 | 1 | 1.00 | 1.00 | same |
| check_diffpair | 7 | 0 | 1 | 0.12 | 1.00 | same |
| check_mate_pins | 0 | 0 | 2 | 1.00 | 1.00 | new |
| check_mating | 0 | 0 | 1 | 1.00 | 1.00 | new |
| check_pdn | 1 | 0 | 1 | 0.67 | 1.00 | same |
| check_ratings | 0 | 0 | 1 | 1.00 | 1.00 | same |
| check_return_path | 1 | 0 | 2 | 0.89 | 1.00 | same |
| check_route_style | 0 | 0 | 1 | 1.00 | 1.00 | same |
| check_silk | 5 | 0 | 1 | 0.38 | 1.00 | same |
| check_thermal | 6 | 0 | 1 | 0.14 | 1.00 | same |
<!-- SCORECARD:END -->

## Open findings

These are the false positives the boards corpus holds after this PR. Each
comes from a waiver whose reason says the check, not the board, is wrong, and
each is recorded in `triage.yaml` with that reason. None is fixed yet, so each
stays counted until a check change makes it disappear from the next record.

- **check_current, transition vias (bldc-motor-driver, bb-ldo, 283).** The
  check charges every via with the whole net's current, so a net fed through
  many vias in parallel reads as short of vias.
- **check_current, undersized tracks and pour necks (bldc-motor-driver,
  rf-de-20m, 79).** Kelvin sense taps carry signal current but inherit the
  net's power budget; necks between stitching vias read as necks in the
  pour; the DC width floor is applied to a 20 MHz tank net.
- **check_creepage (rf-de-20m, bldc-motor-driver, 36).** The board rule is
  applied inside a part's own land pattern (the EPC2019 die pitch), and nets
  on one half-bridge leg take the wrong voltage class.
- **check_thermal, thermal_area (rf-de-20m, bb-ldo, g0-sense, 6).** The model
  ignores heatsinks, credits only same-net top copper and clamps area at
  645 mm2.
- **check_diffpair (bldc-motor-driver, bb-amp, 7).** Low-frequency sense and
  DC precision pairs are held to high-speed skew, coupling and impedance
  rules.
- **check_silk, silk_over_pad (rf-term-150w, 5).** An outline drawn with
  `(fill no)` is still treated as covering the pad.
- **check_return_path (bb-adc, 1).** A 2-layer coplanar return is outside the
  model.
- **check_pdn (bb-buck +5V, 1).** The check reads only decoupling.json, so a
  real output bank that sits on no IC power pin counts as no decoupling.

Fixed in this PR: check_pdn no longer flags a ground net listed under `power`
for its return current (bb-buck, sbuck-5v3a and bldc-motor-driver had each
waived it). The regression test is in `tests/test_check_scorecard.py`.

lumina-carrier's 101 unwaived errors are not triaged: the board never passed
its verify gate, and its `open-items.md` accepts them as open design items.
