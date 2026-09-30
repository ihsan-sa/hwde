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
<!-- SCORECARD:END -->

## Open findings

None recorded yet.
