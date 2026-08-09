# lib/EDITS.md - manual library edits, sbuck-5v3a

Every deviation from a straight `lib_pull.py` (easyeda2kicad) pull is recorded here.
Orchestrator-approved edits only.

## Edit 1. U1 `AP64350SP-13` (SO-8_L4.9-W3.9-P1.27-LS6.0-BL-EP) - exposed pad enlarged to vendor spec

- **Authority:** explicit orchestrator approval (coordinator message, this P3 run) -
  "You are explicitly authorised to edit this footprint... Enlarge the EP to
  3.502 x 2.613 mm."
- **Why:** as pulled, pad 9 (the exposed pad, GND/thermal path) measured
  **3.200 x 2.500 mm** against the vendor's own Suggested Pad Layout (DS41976 Rev.5-2,
  p.24, dimensions X1=3.502/Y1=2.613) - undersized 8.6% in X, 4.3% in Y, 12.6% less
  area (8.00 vs 9.15 mm2). U1's own datasheet-confirmed theta_JC (5 C/W) already closes
  the board's thermal budget with ZERO margin, so the EP *is* the thermal design, not
  cosmetic.
- **Change:** pad 9 `(size 3.200 2.500)` -> `(size 3.502 2.613)`. Pad type/shape
  unchanged (`smd rect`), still on `F.Cu F.Paste F.Mask` (single un-windowed 100%
  aperture - see paste note below), still centred at the footprint origin. No other
  pad, silk, courtyard or 3D-model geometry touched.
- **Clearance check performed before committing:** the enlarged EP does not overlap
  any of the 8 signal pads in Y (the axis it grows toward); worst-case EP-to-signal-pad
  gap measured **0.8935 mm** (pin 8), essentially unchanged from the as-pulled 0.95 mm
  (only 0.057 mm consumed) and vastly above JLC's clearance floor. Full vendor spec was
  achievable with no compromise - did not need to stop short.
- **Solder paste/mask guidance check:** re-read the datasheet's own Suggested Pad
  Layout and Mechanical Data sections (DS41976 Rev.5-2 pp.23-25, the whole remainder of
  the document) directly from the PDF (not just the JSON extraction) looking for a
  stencil/paste-segmentation note for the exposed pad. **None exists** - the datasheet
  gives pad geometry only, no paste windowing guidance. Per instruction, none was
  invented: the EP keeps the single 100%-aperture paste layer it was pulled with. This
  is worth a second look at P8/DFM time as ordinary large-thermal-pad practice, but it
  is not a vendor requirement being skipped.
- **Verification:** `kicad-cli fp export svg` loads clean (exit 0). `fp_verify.py`
  re-run against `parts/C2071691.json`: exit 0 (pass), measured EP size now reads
  `(2.613, 3.502)` mm - an **exact** match to the vendor's X1/Y1 (0.000 mm delta). The
  one remaining "warning" fp_verify reports is a schema artifact (it diffs ALL pads,
  signal + EP, against the single `pad_size_mm` field, which only describes the signal
  pads) - not a new finding.

## Edit 2. F1 `0685T5000-01` (Bel Fuse C1T, C3163312) - KiCad-stock symbol + hand-built vendor-land footprint, NOT an EasyEDA pull

- **Authority:** explicit orchestrator decision (coordinator message, this P3 run) -
  EasyEDA has no CAD data for this LCSC id (confirmed 404, "Component not found", not a
  rate-limit - see report). C3163312 is the only LCSC listing for this exact MPN, and
  the orchestrator decided against re-sourcing to a different, unverified fuse part.
  Use KiCad stock assets instead, vendor-land-checked.
- **Symbol:** `Device:Fuse` (KiCad 10.0.3 stock `Device.kicad_sym`, reachable via the
  global sym-lib-table with no project-table change - same mechanism already used for
  the project's TestPoint/MountingHole reach). Not copied into `aiee.kicad_sym`: BOM/CPL
  provenance for F1 comes from `parts.json`'s own ref->lcsc map (`bom_cpl.py`
  `load_parts_map`, which overrides any board/symbol-embedded LCSC field), so a plain
  stock symbol with no LCSC property does not break BOM generation.
- **Footprint:** KiCad stock `Fuse:Fuse_1206_3216Metric` (IPC-7351 nominal 1206 land,
  pad 1.25 x 1.75 mm @ 2.80 mm pitch) was checked against the Bel Fuse C1T datasheet's
  own Recommended Pad Layout (Type C1T, Rev.C1T May2023, p.4/4, IR-REFLOW variant: pad
  1.78 x 1.52 mm, 1.14 mm gap -> 2.92 mm pitch) and found **materially different**: the
  stock pad is 30% narrower than the vendor's in the pitch axis (1.25 vs 1.78 mm) and
  the stock gap is 36% wider (1.55 vs 1.14 mm measured gap). F1 carries 2.44 A
  continuous, so termination copper area is not cosmetic.
- **Change:** copied the stock footprint's structure (silk, F.Fab outline, 0.25 mm
  courtyard-margin convention) into a new project-library footprint,
  `aiee:Fuse_1206_C1T_BelVendorLand`, with the two pads resized/repositioned to the
  vendor's IR-reflow numbers: `(size 1.78 1.52)` at `(at -1.46 0)` / `(at 1.46 0)`
  (pitch 2.92 mm). Courtyard grown to match (+-2.60 x +-1.01, same 0.25 mm margin
  convention measured on the stock part). `(property "LCSC Part" "C3163312")` added for
  traceability even though the BOM pipeline does not depend on it (see symbol note).
- **Paste guidance:** the datasheet states "RECOMMENDED SOLDER PASTE THICKNESS: 0.15 mm
  minimum" - a stencil-thickness spec, not an aperture-segmentation spec. No windowing
  called for on a plain 2-terminal chip part this size; single 100% aperture per pad
  (F.Paste = F.Cu), same as the stock footprint's own convention.
- **Fab-clearance check:** pad-to-pad gap = 1.14 mm, far above JLC's clearance floor -
  no constraint issue.
- **Verification:** `kicad-cli fp export svg` loads clean (exit 0). No formal
  `fp_verify.py` run (no `parts/C3163312.json` extraction exists to diff against - the
  numbers above were read directly off the vendor PDF page 4, same method as the
  J1/J2 THT-drill check). Courtyard-vs-pad-bbox margin confirmed adequate (0.25 mm all
  four sides) - unlike most of this board's easyeda2kicad pulls, this hand-built land
  does not have the systemic courtyard-smaller-than-pads issue.

## Verified state (post-edit)

| Check | Result |
|---|---|
| U1 EP size | **3.502 x 2.613 mm**, exact vendor match (was 3.200 x 2.500 mm) |
| U1 EP-to-signal-pad worst gap | **0.8935 mm** (was ~0.95 mm as pulled) |
| U1 `fp_verify.py` | exit 0 (pass); EP measured value now equals vendor X1/Y1 exactly |
| F1 footprint | new `aiee:Fuse_1206_C1T_BelVendorLand`, pad 1.78x1.52mm @ 2.92mm pitch |
| F1 symbol | `Device:Fuse` (KiCad stock, not copied into project lib) |
| F1 pad-to-pad gap | 1.14 mm (vendor IR-reflow spec), courtyard margin 0.25 mm all sides |
| Footprints in `aiee.pretty` | 12 (11 pulled + the new Fuse land) |
