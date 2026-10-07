# learnings.d - one root lesson per file

`LEARNINGS.md` is a closed archive (entries 1-425, line numbers cited by the
remediation refs). Every newer non-obvious gotcha is its own file here, and the
file carries its own knowledge-ladder triage row, so two PRs that each add a
lesson touch different files and merge cleanly in either order.

## Adding a lesson

Name the file `<date>-<slug>.md`, where the slug is the first seven words of the
title, lower-case, joined by `-` (`learnlib.slug`; add `-2` on a clash). The
file is:

    ## 2026-10-06 [check_current][gates] The claim, in one line
    Body: what happened, what was measured, what to do instead.

    Triage: now L2 | target L2 | owner scripts/check_current.py | status done | note tests/test_t2_current.py pins it.

- Line 1 is the only `## ` heading: date, one or more `[tags]`, the title.
- The last non-blank line is the triage row: levels `L0`-`L3` (the rubric is
  `design/ladder-triage.md`), the owning artifact, a status of `done`, `open`,
  `n/a` or `planned-T<N>`/`planned-U<N>` (`done` means now == target), and an
  optional note.
- ASCII only.

`learnings.py resolve --kind root_learnings` writes such a file from a
workspace entry. Do not edit `LEARNINGS.md`, the Register table or any count by
hand: `learnings.py triage` prints the counts, and `tests/test_remediations.py`
fails on a lesson whose file or triage row is malformed.

## Recall

    grep -rn '\[check_current\]' LEARNINGS.md learnings.d/
