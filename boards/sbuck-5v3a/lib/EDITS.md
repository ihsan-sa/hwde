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

## Edit 3. R9/C16 snubber upsize (0603->1206) - straight EasyEDA pulls, both accepted as-is

- **Context:** a fresh-context schematic reviewer found the DNP snubber's own resistor
  was overstressed by its paired cap: `P = C*V^2*fsw` = 162 mW at 18 V / 338 mW at the
  26 V hot-plug ring into an 0603 rated 100 mW - a DNP footprint that cooks itself the
  first time someone populates it. `parts.json` was updated by the orchestrator to
  1206/0.25 W R9 (`1206W4F220JT5E`, C17958) and 1206/470 pF C0G C16
  (`CC1206JKNPOCBN471`, C107177) before this librarian pass; see both parts' `role`
  fields for the full power-budget math.
- **Pull-vs-stock call:** EasyEDA pull, for both. Unlike F1, EasyEDA has clean CAD data
  for both LCSC ids (load-check ok, courtyards present) - no reason to prefer KiCad
  stock over a working, LCSC-linked pull, consistent with every other real-LCSC part on
  this board.
- **R9 -> `aiee:R1206` (NEW footprint, closes a real gap):** the project library had
  `R0603` but no 1206 resistor land at all before this pull. Pads `1.208 x 1.701 mm` @
  `2.96 mm` pitch (2.06 mm2 each). Courtyard present but (like ~10 of the board's other
  easyeda2kicad pulls) smaller than the pad field - the already-accepted systemic
  finding, no new action.
- **C16 -> `aiee:C1206` (REUSED, not a new file):** the pull resolved to the SAME
  footprint name already in the library from C29823 (4.7 uF/50 V X7R, C5-C8).
  **Confirmed NOT overwritten** - `(property "LCSC Part" "C29823")` in the file is
  unchanged after the pull. **Confirmed appropriate for C16 anyway:** 1206 is a fixed
  EIA body size: the external land pattern does not depend on dielectric (C0G vs X7R)
  or capacitance value, only on the package code, so the same land correctly serves
  both parts. Pads `1.485 x 1.728 mm` @ `3.18 mm` pitch (2.57 mm2 each). No separate
  land was built - would have been a needless duplicate of an already-verified file.
  (Side effect: this pull's autofix pass caught and fixed one leftover unprintable silk
  circle on `C1206.kicad_mod` that a mid-run process race earlier in this project had
  left un-sanitised - a benign cleanup, not a geometry change; `LCSC Part` and pad data
  untouched throughout.)
- **Pad sanity for bring-up current:** both pads are ordinary, adequately-sized 1206
  chip-component copper (>2 mm2 each) - no undersizing concern for the <=159 mW R9 will
  ever dissipate (worst case, 26 V transient) or for C16's own current.
- **Verification:** `kicad-cli fp export svg` loads clean (exit 0) on both. No formal
  `fp_verify.py` run for either - no `parts/C17958.json` or `parts/C107177.json`
  extraction exists (neither part got a dedicated datasheet-extractor pass), so there is
  no land_pattern JSON to diff against; both were instead sanity-checked directly
  (pad-count, pitch, area, courtyard) the same way L1 was.
- **Old symbols intentionally left in place:** `0603WAF220JT5E` (C23345, old R9) and
  `CL10B102KB8NNNC` (C1588, old C16) are still the live `lib_id`s for R9/C16 in
  `sbuck-5v3a.kicad_sch` - the schematic has not been rewired to the new parts yet
  (that is P4's job). Pruning them now would orphan a placed component. They become
  safe to prune once P4 completes the rewire.

## Edit 4. Four dead symbols pruned from `aiee.kicad_sym`

- **Authority:** explicit orchestrator request (P4, relayed by the coordinator) - these
  four went unreferenced after the FB-divider and compensation re-derivation:
  `ARG03BTC1153` (old R6, 115 k), `RT0603BRD0722K1L` (old R7, 22.1 k),
  `0603WAF1402T5E` (old R5/Rcomp, 14 k), `CL10C470JB8NNNC` (old C3, 47 pF).
- **Safety check performed before removing anything:** confirmed all four LCSC ids
  (C1509621, C723484, C22803, C1671) are absent from the current `parts.json` (already
  retired there). Then grepped `sbuck-5v3a.kicad_sch` directly for all four symbol names
  - **zero hits**, neither as a placed `lib_id` instance nor as a leftover cached
  `lib_symbols` entry. Their shared footprints (`R0603`, `C0603`) stay in active use by
  other still-live parts, so nothing is orphaned on the footprint side either.
- **Explicitly NOT extended to `0603WAF220JT5E`/`CL10B102KB8NNNC`** (the old R9/C16,
  also now retired in `parts.json`) even though they meet the same "retired in BOM"
  test - unlike the four above, THESE are still placed `lib_id` instances in the
  schematic (see Edit 3). Pruning them now would break the schematic; left for P4 to
  clean up as part of the R9/C16 rewire.
- **Method:** text-level surgery via `fpfix.top_level_nodes` (the same paren-scanner
  `lib_pull._dedupe_symbols` already uses for duplicate removal) - whole top-level
  `(symbol "NAME" ...)` blocks removed, nothing else in the file reformatted or touched.
- **Verification:** `kicad-cli sym export svg` on the whole library: exit 0, exactly
  **21** symbols plotted (23 original + 2 new R9/C16 pulls - 4 pruned = 21, matches).
  `lib_pin_types.py` re-run: 0 unexpected changes on the 19 untouched symbols (only the
  2 newly-pulled parts' pins changed) - confirms nothing else was disturbed.

## Verified state (post-edit)

| Check | Result |
|---|---|
| U1 EP size | **3.502 x 2.613 mm**, exact vendor match (was 3.200 x 2.500 mm) |
| U1 EP-to-signal-pad worst gap | **0.8935 mm** (was ~0.95 mm as pulled) |
| U1 `fp_verify.py` | exit 0 (pass); EP measured value now equals vendor X1/Y1 exactly |
| F1 footprint | `aiee:Fuse_1206_C1T_BelVendorLand`, pad 1.78x1.52mm @ 2.92mm pitch |
| F1 symbol | `Device:Fuse` (KiCad stock, not copied into project lib) |
| F1 pad-to-pad gap | 1.14 mm (vendor IR-reflow spec), courtyard margin 0.25 mm all sides |
| R9 footprint | `aiee:R1206` (new), pad 1.208x1.701mm @ 2.96mm pitch |
| C16 footprint | `aiee:C1206` (reused from C29823, confirmed unmodified + appropriate) |
| Symbols in `aiee.kicad_sym` | **21** (23 - 4 pruned + 2 new pulls), `kicad-cli sym export svg` exit 0 |
| Footprints in `aiee.pretty` | **14** (12 pulled/original + Fuse_1206_C1T_BelVendorLand + R1206; C1206 reused) |
| `lib_pin_types.py` | idempotent re-run clean, 0 unexpected changes |
