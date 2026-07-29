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

### 6. D10 `TPD4E1U06DBVR_C19829453` - pin NAMES on pins 1 and 4 corrected
- **Why:** the easyeda2kicad pull captioned **pin 1 "D1+" and pin 4 "D2-"**, while
  `parts/C19829453.json` (datasheet pin-configuration drawing) gives **pin 1 = D2-,
  pin 4 = D1+**. The two channel labels were swapped.
- **Electrically a no-op:** every net is wired by pin NUMBER (`eth.py` maps
  4/6 -> TX and 1/3 -> RX straight from that JSON), and this is a uni-directional
  steering array whose four channels are identical and independent - there is no
  differential element inside, so the "pair" names are drawing convention only.
  The netlist was and is correct.
- **But it was a reading trap:** the schematic and the exported PDF showed
  `/ETH_TXP` arriving on a pin captioned "D2-", which invites a layout or DFM
  reviewer to "fix" a pairing that is already right.
- **Change:** `(name "D1+")` on pin 1 and `(name "D2-")` on pin 4 swapped, so all six
  names now read 1 = D2-, 2 = GND, 3 = D2+, 4 = D1+, 5 = NC, 6 = D1-. Pin numbers,
  positions, electrical types, footprint and every other field untouched.
- **Guard against regression:** `eth.py`'s `expect={}` for D10 previously asserted only
  the four names that agreed; it now asserts **all six**, so a lib re-pull that
  reintroduces the swap fails the generator instead of shipping.
- Verified after the edit: `lib_pin_types.py` re-run (idempotent, 0 changes - it keys
  on pin numbers), `root.py` rebuild, ERC 0 errors / 0 warnings, and the exported
  schematic PDF shows `D2- 1 / GND 2 / D2+ 3 / D1+ 4 / NC 5 / D1- 6`.

### 7. J1 `RJ45-TH_LPJG0926HENL_C22457393` - isolation barrier, NPTH holes, courtyard

New land, pulled 2026-07-29 for the C91754 -> C22457393 magjack swap. Three edits, all
applied by `work/mj_fp_edit.py`, which prints the full pad-pair gap table before and after.

**7a. Isolation barrier - the mandatory mitigation, and why it needed extending.**
- **Why:** this part has no internal bridge, so four RAW 48 V line-side taps (VC1..VC4,
  pads 11-14) land in a band that was empty on the HY931147C. `check_creepage` cannot see
  the problem - it sizes spacing from the 57 V working voltage (0.635 mm) and knows nothing
  about a magjack's chip-side/line-side barrier, which HALO's app note puts at
  **55 mil = 1.40 mm** at this pitch (LEARNINGS 2026-07-28 `[check_creepage][gates][magnetics]`).
- **As pulled** (all pads 1.524 mm), measured, not assumed:

  | barrier | min gap | pads |
  |---|---|---|
  | 48 V tap <-> **energised** chip net | **1.289 mm** | 11 (VC1) - 2 (TD1- = /ETH_TXN) |
  | 48 V tap <-> bare no-connect pad | 0.986 mm | 14 (VC4) - 10 (TD4-) |

  The plan of record assumed 1.50 mm pads and a 2.86 mm centre-to-centre and expected
  1.36-1.56 mm. The real pull is **1.524 mm pads on 2.8130 mm c-c**, so shrinking pads
  9/10 alone leaves the *energised* barrier at 1.289 mm - **still under guidance**, because
  the pad that sets it is pad 2, a live TX pin, not a spare-pair pad.
- **Change:** pads **9 and 10** (TD4+/TD4-, kept as BARE no-connects by `poe.py`) **and pads
  11 and 14** (VC1/VC4, the two taps that set every minimum) resized **1.524 -> 1.300 mm**.
  Drills untouched at 0.900 mm, so annular ring is 0.200 mm/side - above JLC's 0.15 mm PTH
  floor, and the VC pads carry only 0.6 A. **No live signal pad was resized.**
- **Effect, measured:**

  | barrier | before | after | requirement |
  |---|---|---|---|
  | 48 V tap <-> **energised** chip net | 1.289 mm | **1.401 mm** | 1.40 mm (HALO) - **met** |
  | 48 V tap <-> bare no-connect pad | 0.986 mm | **1.210 mm** | n/a, dead net |
  | 48 V tap <-> SHIELD board lock | 0.375 mm | **0.487 mm** | 0.635 mm - **NOT met, open** |

  1.401 mm is *at* guidance, not comfortably over it; shrinking VC1/VC4 further would take
  the annular ring to JLC's bare minimum, and the only other lever is pad 2 itself.
- **NEW DEFECT FOUND, not fixed here.** The d1.70 board-lock pads 19/20 - which are the
  only path from the shield shell to the board - sit **2.287 / 2.297 mm c-c** from VC1 / VC4.
  Even after 7a that is **0.487 mm of copper between a 57 V tap and SHIELD, against the
  board's own 0.635 mm rule**. Unlike the isolation barrier this one IS inside
  `check_creepage`'s model, so P8 will raise it. Left for P7 to adjudicate: reaching
  0.635 mm needs pads 19/20 at 2.00 mm and VC at 1.20 mm, i.e. 0.15 mm/side annular on
  both, which is JLC's floor on a connector that takes mechanical stress. Not a silent
  half-fix.

**7b. Mounting holes -> non-plated.** The two dia-3.20 mm holes were pulled as `thru_hole`
with pad size == drill (zero annular ring), the identical defect fixed on the HY931147C land
in edit 4. Both converted to `np_thru_hole` (3.20 mm, at -5.72,+2.42 and +5.71,+2.42).
Consequence for `poe.py`: the shield reaches the board **only** through pads 19/20.

**7c. Courtyard added.** The pull emitted no `F.CrtYd` and `lib_pull` warned about it; 29 of
the library's other 30 footprints carry one. Drawn on the silk body outline + 0.25 mm:
X +/-8.21, Y -8.28 .. +13.46 (body is 15.93 x 21.25 mm per the datasheet).

**Verified after the edits:** land re-measured against the vendor's p2 "Suggested PCB Layout"
(every dimension within 0.05 mm; the drawing's 2.56 mm row-B-to-row-C becomes 2.51 mm in the
pull, inside its own +/-0.25 mm tolerance), `fp_verify.py` against `parts/C22457393.json`
exit 0, KiCad 10 load check 31/31 footprints, ERC 0 errors / 0 warnings.

### 8. D2/D3 `ABF_L5.1-W4.4-P4.00-LS6.2-BL` - pulled unmodified

The two PoE input bridges (ABS210, C2892567). Pulled clean: 4 pads, courtyard and silk
present, `fp_verify.py` against `parts/C2892567.json` exit 0. Body length 5.1, width 4.4,
lead pitch 4.00 and lead span 6.2 all match the datasheet's ABS/LBF mechanical table
(D 4.9-5.2, E 4.2-4.5, d 3.8-4.2, HE 6.0-6.4). Its pads run 1.97-3.67 mm from centre and so
cover the 0.6 mm foot with ~0.5 mm of heel and ~0.5 mm of toe, which is *more* generous than
the vendor's own 2.0 x 1.0 mm recommendation - whose toe is 0.1 mm short at maximum lead
span. **No edit made. But a LAYOUT REQUIREMENT rides on it:** the datasheet's RthJA = 65 C/W
is quoted "mounted on glass epoxy PC board with 4 x (5 x 5 mm) copper pad". The junction
temperature that justified this part (118-133 C against a 150 C limit) is void unless P7
gives each of the 8 pads its ~5 x 5 mm pour.

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
| Footprints in `aiee.pretty` | **31** (29 + the new J1 land + the bridge land) |
| KiCad 10 load check (`kicad-cli fp export svg`) | **31 / 31 rendered, exit 0** |
| Symbols whose `aiee:` footprint does not resolve | **none** |
| J3 / J4 annulus | both **1.700 mm** -> 0.840 mm gap -> **1.32x** over 0.635 mm |
| J1 non-plated mounting holes | 2 x `np_thru_hole` **3.20 mm** confirmed (new land, edit 7b) |
| J1 isolation barrier to any energised net | **1.401 mm** (pad 11 - pad 2), at the 1.40 mm guidance |
| J1 48 V tap to SHIELD board lock | **0.487 mm** vs 0.635 mm required - **OPEN, see edit 7a** |
| Courtyards | 31 / 31 (edit 7c added the only missing one) |
| `fp_verify.py` on the two new lands | exit 0 on both |
