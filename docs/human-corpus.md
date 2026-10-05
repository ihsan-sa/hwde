# The human-made board corpus

The evals score hwde's boards against its own gates, which says nothing about
how those gates read a board a person designed. This corpus is that baseline:
open-hardware KiCad boards from GitHub, pinned by commit, each with its licence
and whatever is known about how it turned out, run through the same gates
(`verify_all`, `dfm_check`). The owner reviews what the gates flag on them, so
each board's findings are listed on their own, not only as a score.

- Manifest: `.claude/skills/hwde/reference/human_corpus.yaml`
- Script: `.claude/skills/hwde/scripts/human_corpus.py` (its docstring is the contract)
- Results: `docs/human-corpus-results.md` (written by `human_corpus.py table`)
- Checkouts and gate output: `~/.cache/hwde-human-corpus/` (never this repo or the boards repo)

## How boards were picked

Coverage and variety come first, not quality: a poor board is as useful a test
case as a good one. A board is taken only when:

- its repo carries a licence from the accepted set (MIT, Apache-2.0, BSD,
  0BSD, CERN-OHL-P/W/S, CC-BY, CC-BY-SA). The licence and where it was read
  are recorded; an unlicensed board is never taken. GitHub cannot read some
  hardware licences (it reports NOASSERTION), so those are set by hand with
  the file that grants them as `licence_source`;
- its `.kicad_pcb` is KiCad 6 or later (file version 20211014 or above);
  `fetch` checks the file and excludes an older one, and one saved by a
  KiCad nightly the pinned KiCad 10 cannot open (above 20260206);
- it fills a domain hwde designs: `power`, `mcu-usb`, `analog`, `motor`, `rf`
  or `4-layer`. The domain is the board's main job; `layers` comes from the
  file, so a 4-layer power board still counts as 4-layer in the table.

The first batch came from GitHub repo searches by topic (`kicad`, `pcb`) and
licence, kept to repos that look like one board or a family of boards, not
libraries or tools, plus a few well-known boards with a shipped history
(Glasgow, Bus Pirate 5, ThunderScope, OLIMEX ESP32-PoE).

The second batch leaned on the thin domains (motor, RF, analog) and on boards
with outcome evidence: GitHub topic searches pairing `kicad` with `bldc`,
`lora`, `rf`, `eurorack`, `audio` and the like, plus vendors who sell the
boards they publish (mjbots moteus, Winterbloom, Electronic Cats, OLIMEX,
tinyVision, Antmicro). A `product` label there cites the store page the
repo's own README links, and says when the revision on sale is not stated.
A KiCad 5 file is the commonest reason a candidate fails `fetch`; a
`.kicad_pro` beside the `.kicad_pcb` is a cheap first filter, though a
KiCad 6 project can still carry an unsaved KiCad 5 board.

## Outcome labels

The outcome is the empirical label the evals score against, so it is a
person's word with a source, never a guess:

| label | meaning |
|---|---|
| `product` | sold or shipped in quantity (a store page, a crowdfunding campaign) |
| `fabricated` | built at least once (photos, a build log, a fab order in the repo) |
| `errata` | a bug in this revision is on record (an issue, a note, a directory name) |
| `fixed-in-later-rev` | as `errata`, and a later revision in the corpus fixes it |
| empty | no evidence found; most boards are here, and that is fine |

When a later revision fixed a bug, both revisions are in the corpus as a pair:
each carries `pair: {with, role: before|after, note}`. A pair is where a gate
earns its keep: it should flag the bug on `before` and not on `after`.

`human_corpus.py label` collects evidence automatically (GitHub releases, and
issue titles that mention errata, rework, bodges, swapped or wrong parts) into
the `evidence` field. The evidence is per repo, so every board of a
monorepo carries the same lines, and the word match is loose ("short" also
matches "shortage"); it is a reading list, not a label. It never writes `outcome`: a person reads the evidence
and sets the label.

## Running a batch

From a checkout with the Linux toolchain (`CLAUDE.md`, "Linux host without the
container"):

    . ~/.local/kicad10/hwde-env.sh
    S=.claude/skills/hwde/scripts
    python $S/human_corpus.py pin      # new rows: commit, licence, pcb
    python $S/human_corpus.py fetch    # sparse checkouts by pinned commit
    python $S/human_corpus.py label    # outcome evidence
    python $S/human_corpus.py run      # gates, 2 boards at a time, own Xvfb
    python $S/human_corpus.py table    # docs/human-corpus-results.md

To add a batch, append rows with `id`, `url`, `domain` and, for a repo with
several projects, `pcb`; then run the same five steps on the new ids.

## Reading the results

The boards carry no hwde workspace (no constraints.json, decoupling.json or
parts dir), so `verify_all` runs in its default exploratory mode: the checks
that need those inputs are skipped and only the board-only checks run
(silkscreen, diff pairs, route style, connector mating and the rest that read
the `.kicad_pcb` alone). `dfm_check` runs against the JLCPCB capabilities with
the polarity oracle fed from the board's schematic when there is one. A
finding on a human board is therefore a question for the owner, not a verdict:
either the board has the problem, or the gate is wrong about a board it was
not tuned on. Both are what the evals want to know.
