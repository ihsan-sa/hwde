# Design documents - filing and the P10 documents

`report_gen.py` assembles state.json + digests + reports + renders
into the design doc; without pdflatex it degrades to .tex-only (check_env
warns). Only the FINAL design doc is filed in the document register: run that
one with `--file`, or `DOC_PROJECT=Boards report_gen.py ... --file`. Never
export DOC_PROJECT for the session, or every run files. An unchanged rebuild
files nothing. At P10 close (or when the owner asks) every board also gets two
more documents, each filed as its own: `--kind highlight` (a few pages: what
it is, a picture, BOM, the decisions that changed it, checks) and `--kind full
--render-history` (the design doc plus a render of each routing snapshot,
every decision and why, the run's history and a diagram-maker figure of how it
went). Once the board's boards PR has squash-merged, pass `--history-ref <its
track branch>` so the history reads the run's own commits.
