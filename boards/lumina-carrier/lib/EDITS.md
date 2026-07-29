# lib/EDITS.md - manual library edits, LUM-CAR-A

Every deviation from a straight `lib_pull.py` (easyeda2kicad) pull is recorded here.
Orchestrator-approved edits only. Verified state at the bottom.

## Context: an interrupted run

The P3 librarian was terminated mid-run twice by an API spend limit. The second
interruption left the library in a **torn state**: the symbol table had already been
repointed at two KiCad stock footprints that had **not yet been copied into
`aiee.pretty`**. Symbols therefore referenced footprints that did not exist.
That state was detected by direct measurement (not by trusting mtimes), and repaired.
Edits 1 and 4 were completed by the librarian; edits 2 and 3 were completed by the
orchestrator after verifying they were absent.

## Edits

### 1. J3 `HDR-TH_14P-P2.54-V-M-R2-C7-S2.54-1` - annulus 1.80 -> 1.70 mm
- **Why:** J3 is the ICD-01 **power** block, the connector carrying 48 V raw. As pulled
  it had a 1.80 mm annulus = 0.740 mm pad-to-pad copper gap = **1.17x** over the board's
  0.635 mm HV creepage requirement, while J4 (signals only) had 1.70 mm = 0.840 mm =
  **1.32x**. The two frozen ICD connectors were mutually inconsistent and the HV-carrying
  one had the *worse* margin.
- **Change:** all 14 pads resized 1.800 -> 1.700 mm. Drill left at 1.100 mm.
- **Effect:** gap 0.840 mm, **1.32x**, identical land pattern to J4. ICD-01 rev A2's
  published 0.84 mm / 1.32x therefore remains true and needed no re-issue.
- Note: pad-to-pad gap is `pitch - annulus` and is independent of drill. The ICD's
  original "1.02 mm drill" text was stale (real pull is 1.100 mm) and has been corrected;
  the gap conclusion is unaffected. Annular ring 0.300 mm/side, above JLC's PTH minimum.

### 2. U22 `TPS16630PWPR` - footprint swapped to KiCad 10 stock
- `HTSSOP-20_L6.5-W4.4-P0.65-LS6.4-TL-EP2.58` (EasyEDA pull) ->
  **`HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_Mask2.96x2.96mm_ThermalVias`**
- **Why:** the pulled footprint modelled a plain 2.585 x 2.585 mm NSMD thermal pad with
  4 vias. TI drawing 4224598/A specifies a **solder-mask-defined** pad: 2.96 x 2.96 mm
  exposed inside 3.4 x 6.5 mm masked copper, 9 vias. The pull had ~24 % less exposed
  metal, no 3.4 x 6.5 copper, signal pads 24 % narrow (0.343 vs 0.45 mm) and asymmetric
  rows (5.74 vs 5.80 mm c-c). This part is the 48 V hot-swap switch - its thermal pad
  *is* its dissipation path, so this is a reliability defect, not cosmetics.
- Copied **verbatim and unmodified** from KiCad 10.0 stock `Package_SO.pretty`.

### 3. U20 `SCT2A25STER` - footprint swapped to KiCad 10 stock
- `ESOP-8_L4.9-W3.9-P1.27-LS6.0-BL-EP` (EasyEDA pull) ->
  **`SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm`**
- **Why:** the pulled land had signal pads only 1.20 mm long at 5.82 mm c-c (inner edge
  2.31 mm) against KiCad's IPC SOIC-8 reference of 1.825 mm, leaving the worst-case heel
  fillet uncovered on a 100 V buck's power pins.
- **Coverage check performed before committing the swap:** EP 2.41 (X) x 3.3 (Y) fully
  covers the datasheet's 2.36 x 3.25 mm maximum die pad in both axes.
- Copied verbatim and unmodified from KiCad 10.0 stock.

### 4. J1 `RJ45-TH_HY931147C` - mounting holes made non-plated
- The two dia-3.25 mm mounting holes were `thru_hole` (plated) with pad size == drill,
  i.e. **zero annular ring**, which trips DRC at P7.
- **Change:** both converted to `np_thru_hole` (3.25 mm, at -2.40,-5.70 and -2.40,+5.70).
- The 4 LED holes were left at 1.10 mm drill (datasheet 1.02 mm); 0.08 mm oversize on a
  THT hole is harmless.

### 5. U1 `TPS2378DDAR` - footprint swapped to KiCad 10 stock (earlier, first librarian run)
- -> `SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.71x3.4mm`
- **Why:** the LCSC-hosted PDF carries the **superseded** package drawing 4208951-6/D
  (EP 3.10 x 2.40); TI's current 4214849/B (09/2025) has a larger EP (3.4 x 2.71 mask,
  2.95 x 4.9 copper). The KiCad stock footprint matches the current drawing exactly.

## Deliberately NOT changed

- **Untented vias-in-pad** under the ESP32-S3 thermal land (12 vias, drill 0.25 / pad 0.40
  = 0.075 mm ring, below JLC's usual 0.15 mm PTH minimum) and under the HTSSOP-20 pad.
  Left for the **P9 DFM gate** to adjudicate against real fab rules with its own fix loop,
  rather than being silently changed in the library.
- **Y10** footprint name `OSC-SMD_4P-L3.2-W2.5-BL_SIT8008BI` - cosmetically wrong (names a
  SiTime oscillator) but is the correct 4-pad 3225 crystal land. Renaming risks breaking
  symbol linkage for zero benefit.

## Verified state (post-edit)

| Check | Result |
|---|---|
| Footprints in `aiee.pretty` | **29** |
| KiCad 10 load check (`kicad-cli fp export svg`) | **29 / 29 rendered, exit 0** |
| Symbols whose `aiee:` footprint does not resolve | **none** |
| J3 / J4 annulus | both **1.700 mm** -> 0.840 mm gap -> **1.32x** over 0.635 mm |
| J1 non-plated mounting holes | 2 x `np_thru_hole` 3.25 mm confirmed |
| Courtyards | 27 / 27 on the original pulls; both stock swaps carry courtyards |
