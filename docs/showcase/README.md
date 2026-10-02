# The PCB flow (hwde) showcase: how it is made

The showcase itself is the repository's [README](../../README.md), and the
same text is set as a PDF in [hwde-showcase.pdf](hwde-showcase.pdf) (library
document 003-0001, the PCB flow (hwde) showcase). The two copies are made two ways:

- **The board gallery is generated.** `gallery.py` reads
  [gallery.yaml](gallery.yaml) and the boards repo (`register.yaml`, and each
  board's `.kicad_pcb`, `state.json` and `fab/`), and writes `gallery.tex`,
  which the PDF inputs, and the README's part between the `gallery:start` and
  `gallery:end` markers. Never edit either copy; edit `gallery.yaml`.
  - Layers, size and footprint count come from the `.kicad_pcb`. Where a
    board stopped comes from its files: "ordered and made" when `fab/` has a
    `tracking.json`, "<stage>, findings open" when a gate in `state.json`
    failed, "package ready" when `fab/` has the Gerbers zip and a placement
    file, and otherwise the phase it reached.
  - A board the register lists and `gallery.yaml` does not is shown anyway,
    in a "New boards" section, with the first sentences of its
    `requirements.md` "## 1. Function", or its register title when it has
    none. Giving it an entry in `gallery.yaml` (a blurb, a section) moves it
    out of there.
  - A board that never reached a routed layout is named in one line at the
    end, not pictured.
- **The opening, the pipeline and the closing sections are written by hand**,
  in `hwde-showcase.tex` and the top-level `README.md` alike, so an edit to one
  is made to the other.

## Bringing it up to date

`./sync.py` does all of it: it makes the picture of any new board, regenerates
both copies of the gallery, and, when anything the PDF is built from changed
since the last filing, builds the PDF and files it in the library as the next
revision of 003-0001. It commits nothing; the README, `gallery.tex`, the PDF,
any new picture and `filed.json` (the hash of what was last filed) are left
ready to commit. Run it after a boards-repo change that adds or changes a
board. `tests/test_showcase_gallery.py` fails when the register lists a board
with a routed layout that the committed showcase does not show.

## Remaking any of this

- `./build_docs.sh` exports the figures and builds the PDF.
  - The figures are diagram-maker specs in `diagrams/*.json`. The skill's
    `scripts/export.sh` turns each into the PDF the document places and the
    PNG the README shows.
  - The PDF is set in the house style of the pdf-material-builder skill and
    needs `lualatex` and that skill.
- A board's picture is `renders/<name>.png`. For a new board `sync.py` takes
  the board's own render from its workspace (an angled `*_iso.png` first, then
  a `*_top.png`) and finishes it for the page with `_finish.py`. The older
  pictures were made the same way or by `render_boards.sh`.
- `./render_boards.sh [name ...]` renders a board with kicad-cli on the host,
  for a board that has no render of its own. The user-space KiCad under
  `~/.local/kicad10` cannot find its 3D model plugins, so there it draws the
  bare board without its parts; a system KiCad draws them.
- The two copper views are KiCad plots of the top copper layer with net names,
  made by hwde's `layer_views.py` (`layer_views.py <board>.kicad_pcb --out-dir
  <dir> --no-3d`). Each `*_F_Cu.pdf` was rasterised with `pdftoppm` and scaled
  to 1600 px or less on the long side.
