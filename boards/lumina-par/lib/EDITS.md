# lib/EDITS.md - manual library edits, LUM-PAR-A

Every deviation from a straight `lib_pull.py` (easyeda2kicad) pull is recorded here.
Orchestrator-approved edits only. Verified state at the bottom.

## Edits

### 1. J3 `HDR-TH_14P-P2.54-V-F-R2-C7-S2.54-1` (C113344) - annulus 1.80 -> 1.70 mm

- **Why: ICD-01 conformance, NOT a clearance rescue.** As pulled, J3 gave a 0.740 mm
  pad-to-pad copper gap = **1.17x** the board's 0.635 mm HV creepage requirement, so it
  *passed* creepage on its own. The defect is that ICD-01 rev A3 s5.2 is a **frozen
  interface that two boards mate through**, and it mandates a 1.70 mm annulus on a
  1.10 mm drill (0.300 mm ring/side, 0.84 mm gap, 1.32x). A daughter that quietly ships
  a different land pattern is exactly the silent divergence the ICD preamble forbids.
- **Change:** all 14 pads resized 1.800 -> 1.700 mm. Drill left at 1.100024 mm (already
  correct - it matched the ICD as pulled).
- **Effect:** annular ring 0.300 mm/side, pad-to-pad gap 0.840 mm, **1.32x**. Identical
  land pattern to J4 and to the carrier's mating DS1021 pair.
- Note: pad-to-pad gap is `pitch - annulus` and is independent of drill.
- Same edit, same numbers, as carrier `boards/lumina-carrier/lib/EDITS.md` edit 1.

### 2. J4 `HDR-TH_24P-P2.54-V-F-R2-C12-S2.54` (C92265) - annulus 1.60 -> 1.70 mm, drill 1.050 -> 1.100 mm

- **Why: ICD-01 conformance.** As pulled, J4 had a 1.600 mm annulus on a **1.049986 mm**
  drill = 0.275 mm ring/side and a 0.940 mm gap (1.48x). No 48 V exists anywhere on this
  connector (ICD s3.2) so creepage never bound here either - but the ICD requires both
  frozen connectors to share ONE land pattern, and this one matched neither the ICD nor J3.
  The drill was also the only one of the four ICD connector footprints (2 carrier + 2
  daughter) that was not 1.100 mm.
- **Change:** all 24 pads resized 1.600 -> 1.700 mm AND drill 1.049986 -> 1.100024 mm.
- **Effect:** annular ring 0.300 mm/side, gap 0.840 mm, 1.32x. J3 == J4 == carrier pair.
- The socket tail is 0.60 x 0.40 mm (C113344 datasheet), so a 1.100 mm hole clears it
  comfortably; CONNFLY's own recommendation is 1.02 mm and the ICD's 1.10 mm is 0.08 mm
  looser, which is the deviation ICD-01 rev A2 already recorded and accepted.

### 3. L301 / L321 / L341 / L361 `CKCS4030-47uH/M` (C354593) - footprint swapped to KiCad 10 stock

- `IND-SMD_L4.0-W4.0` (EasyEDA pull) -> **`L_Cenker_CKCS4030`** (KiCad 10.0
  `Inductor_SMD.pretty`), copied **verbatim and unmodified**.
- **Why:** the pulled land placed its two pads on **3.20 mm** centres (1.60 x 3.50 mm pads)
  against the datasheet's "Recommended patterns" figure of **2.60 mm** centres
  (F = 1.2 gap, G = 1.40 pad width, H = 3.7 pad length). That is a 0.60 mm pitch error -
  12x `fp_verify`'s 0.05 mm tolerance, and a real one: the CKCS4030's bottom electrodes
  span 0.65 to 2.00 mm from the body centre, so the pulled pads (0.80 to 2.40 mm) cover
  only 1.20 mm of the 1.35 mm electrode and hang **0.40 mm past the 4.0 mm body edge**.
  Overall land span 4.80 mm against a 4.00 mm body.
- **KiCad stock is a strict superset of the datasheet land:** pads 1.9 x 3.7 mm on 2.70 mm
  centres span 0.40 to 2.30 mm, covering the full 1.35 mm electrode with fillet relief on
  both sides. It is named for this exact part family (Cenker CKCS4030) so the intent
  survives a later reader.
- **Residual, accepted:** `fp_verify` still reports `pad_pitch` 2.70 vs 2.60 mm (0.10 mm,
  above the 0.05 mm tolerance). This is expected and correct - IPC-derived stock lands are
  routinely a little wider than a vendor's minimum pattern. 2.70 is 0.10 mm off; the pull
  was 0.60 mm off.
- The superseded `IND-SMD_L4.0-W4.0.kicad_mod` is left in `aiee.pretty` (nothing
  references it; the `CKCS4030-47UH_M` symbol's `Footprint` property now reads
  `aiee:L_Cenker_CKCS4030`).

### 4. D501-D504 `SMF15A` (C435484) - CONSIDERED AND ACCEPTED AS PULLED. No change.

Recorded so a later reviewer does not reopen it.

- `fp_verify` reports a `pad_pitch` **error**: pulled `SOD-123_L2.7-W1.8-LS3.7-RD` places
  its pads on **3.26 mm** centres against the datasheet's 3.00 mm.
- **Accepted** because the discrepancy is a 0.13 mm outboard shift per pad, and the pad
  **size matches the datasheet exactly** - 1.00 x 1.10 mm, i.e. the datasheet's B x A
  (there is no `pad_size` warning at all on this part). The pads still fully cover the
  SOD-123 terminal, and the shift is in the safe direction (more toe fillet, more
  inspectable joint).
- For contrast, the alternative KiCad stock `Diode_SMD:D_SOD-123` is *worse* on both
  counts: 3.30 mm centres (0.30 off, vs 0.26) and 0.9 x 1.2 mm pads (does not match the
  datasheet). The pull is the better of the two available options.
- Polarity confirmed correct: pin 1 = cathode, and the silkscreen cathode band
  (`fp_line` at x = -0.95, width 0.15 mm, printable) sits on the pad-1 side.

## Not edited - flagged instead

- **Q102 `SOT-23-3_L2.9-W1.5-P1.90-LS2.6-BR` (C427379 BSS123).** All three pads carry
  `(at x y 90)`. `placelib._pad_box_local()` reads `(size 0.700 1.250)` verbatim and never
  applies the rotation, so P6 sees a 0.70 mm-wide pad box where the truth is 1.25 mm -
  0.275 mm under-estimated per side. This is a `placelib` limitation, **not** a footprint
  defect, so the footprint is untouched. Handed to P6.
- **Emitters C22434861 / C48586656.** `fp_verify` reports `pad_count` 7 != 6 and 3 != 2.
  Both are **false positives**: the extra pad is the central circular thermal land
  (dia 6.0 / 5.0 mm) that the datasheet extraction did not count. Off-board module parts,
  excluded from the gate. Untouched.

## Verified state after the edits

Measured from the files, not assumed:

| | drill | annulus | ring/side | pad-to-pad gap | vs 0.635 mm |
|---|---|---|---|---|---|
| ICD-01 s5.2 requirement | 1.100 | 1.700 | 0.300 | 0.840 | 1.32x |
| **J3** C113344, 14 pads | **1.100024** | **1.700** | **0.300** | **0.840** | **1.32x** |
| **J4** C92265, 24 pads | **1.100024** | **1.700** | **0.300** | **0.840** | **1.32x** |
| carrier DS1021 2x7 / 2x12 | 1.100024 | 1.700 | 0.300 | 0.840 | 1.32x |

- `L_Cenker_CKCS4030` present in `aiee.pretty`, pads `1`/`2` at +/-1.35, size 1.9 x 3.7.
- `CKCS4030-47UH_M` symbol `Footprint` = `aiee:L_Cenker_CKCS4030`.
- All 23 footprints load under `kicad-cli` 10.0.3 (`fp export svg`).
- `boards/lumina-par/lib` populated; `kicad/fp-lib-table` and `kicad/sym-lib-table` both
  resolve `${KIPRJMOD}/../lib/...` with a single `..`.
