# The hwde showcase: how it is made

The showcase itself is the repository's [README](../../README.md), and the
same text is set as a PDF in [hwde-showcase.pdf](hwde-showcase.pdf) (library
document 003-0001, the hwde showcase). The two copies of the prose are kept by
hand: `hwde-showcase.tex` and the top-level `README.md` say the same things,
so an edit to one is made to the other.

## Remaking any of this

- `./build_docs.sh` exports the figures and builds the PDF.
  - The figures are diagram-maker specs in `diagrams/*.json`. The skill's
    `scripts/export.sh` turns each into the PDF the document places and the
    PNG the README shows.
  - The PDF is set in the house style of the pdf-material-builder skill and
    needs `lualatex` and that skill.
- `./render_boards.sh` made the 3D renders of the first fourteen boards. It
  runs KiCad in Docker and expects the board folders as they were named before
  the `PCB-NNNN-R_name` scheme, so it needs updating before it is run again.
- The four boards added in revision B use the renders in their own `reports/`
  folders, finished for the page with `_finish.py`:

  ```
  B=~/dev/boards
  ./_finish.py $B/PCB-0017-A_stereo-class-d-amp/reports/layers/PCB-0017-A_stereo-class-d-amp_iso.png renders/stereo-class-d-amp.png
  ./_finish.py --opaque-only $B/PCB-0018-A_bldc-motor-driver/reports/PCB-0018-A_bldc-motor-driver_top.png renders/bldc-motor-driver.png
  ./_finish.py --opaque-only $B/PCB-0016-A_pd-trigger-lite/reports/render_final/pd-trigger-lite_top.png renders/pd-trigger-lite.png
  ./_finish.py --opaque-only $B/PCB-0016-B_pd-trigger-lite-dip/reports/pd-trigger-lite-dip_top.png renders/pd-trigger-lite-dip.png
  ```

- The two copper views are KiCad plots of the top copper layer with net names,
  made by hwde's `layer_views.py` (the amplifier's is already in its
  `reports/layers/`; the motor driver's was made with
  `layer_views.py <board>.kicad_pcb --out-dir <dir> --no-3d`). Each
  `*_F_Cu.pdf` was rasterised with `pdftoppm` and scaled to 1600 px or less on
  the long side.

The dimensions, layer counts and footprint counts are read from each board's
`.kicad_pcb`, and the stage each board reached from its `state.json`.
