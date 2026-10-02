# Design documents - filing and the P10 documents

`report_gen.py` assembles state.json + digests + reports + renders
into the design doc; without pdflatex it degrades to .tex-only (check_env
warns). Only the FINAL design doc is filed in the document register: run that
one with `--file`. It files into the board's own folder of the library, the
project `Boards/<PN> <name>` when the boards register gives the part number,
else `Boards/Unregistered`; `DOC_PROJECT=<project>` overrides that (never the
bare group `Boards`, which cc-docs refuses). Its title leads with the part
number (`PCB-0022-B nfc-card design doc`), so a new revision never files over
the last one's documents. Never export DOC_PROJECT for the
session, or every run files. An unchanged rebuild
files nothing. Every filed document also carries the board's fab set as
supporting files, each name led by the workspace directory's name:
`<ws>_gerbers.zip`, `<ws>_BOM.csv`, `<ws>_CPL.csv` and the distributor BOMs
when present; a fab set that changed under an unchanged PDF still goes up. At P10 close (or when the owner asks) every board also gets two
more documents, each filed as its own: `--kind highlight` (a few pages: what
it is, a picture, BOM, the decisions that changed it, checks) and `--kind full
--render-history` (the design doc plus a render of each routing snapshot,
every decision and why, the run's history and a diagram-maker figure of how it
went). Once the board's boards PR has squash-merged, pass `--history-ref <its
track branch>` so the history reads the run's own commits.
