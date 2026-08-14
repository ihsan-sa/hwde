# rf-de-20m - FAB PACKAGE (P9)

20 MHz Class E GaN RF power amplifier. 4-layer, 120.000 x 80.000 mm.
Built 2026-08-09 from `kicad/rf-de-20m.kicad_pcb`
(`sexpr_no_uuid:95c6b6e0943fdb0ea1148babff0a2b80917adbd9ac2666104ec1c9cc8df89e1d`).

Gates at the time of export: `erc` pass, `drc_routed` 55 (all owner-approved
waiver classes, `reports/route-notes.md` s13), `verify` **PASS** (0 failing /
189, 31 waived at checkpoint H4), `dfm` **PASS (0 errors, 0 warnings)**.

---

# 1. DO NOT ORDER YET

**EPC2019 (LCSC `C2836675`, Q201/Q202) is OUT OF STOCK at LCSC.** The order is
deliberately held. This package exists so that the moment stock returns the
order is a transcription, not a rebuild. Ordering is P10's job, not P9's.

Second hold, `reports/route-notes.md` s14: **`C5639707` is no longer on this
BOM** (R205/R206 reverted to 4R7 / `C160081` at H4), but `C160081` was the
thinnest stock line before that change - re-verify every line live at P10.

---

# 2. !!! THE NINE DNP SITES - READ THIS BEFORE UPLOADING ANYTHING !!!

## 2.1 The hazard (and what changed on 2026-08-14)

`kicad-sch-api`'s writer hard-codes `(dnp no)`, so this board marks
do-not-populate with a **visible `Variant=DNP` schematic field**, and until U3
**nothing in the ai-ee pipeline read it** - not `bom_cpl.py`, not
`netlist_audit`, not any `check_*`, not KiCad's own pos export. A raw
`bom_cpl.py` run emitted **68 CPL rows and all 9 DNP refs inside the BOM
designator lists**, and a board-local `fab/filter_dnp.py` post-step had to
strip them again.

If those unfiltered files ship, the assembler fits **C203, C308 and C309** -
and that **silently undoes the P8 ZVS fix**. The board comes back
hard-switching: `Vds` at turn-on ~15.6 V instead of ~1.4 V, `P_out` **~53 W
instead of ~113.8 W** (`reports/sim-notes.md`, `reports/route-notes.md` s17).
It will look assembled, it will power up, and it will be wrong.

**Since U3 (2026-08-14) the hazard is closed in the pipeline, not by hand.**
DNP is a first-class `assembly_class` in canonical parts data
(`parts/parts.json`: `refdes_dnp`, plus per-site `refdes_notes`), `bom_cpl.py`
decides BOM/CPL membership from those classes, and `dfm_check.py` FAILS a
package whose shipped BOM/CPL lists a site the classes exclude. `filter_dnp.py`
is **deleted** - do not reintroduce it. The regression that replaces it lives
in the repo (`tests/test_assembly.py::test_rf_de_regenerates_without_a_local_filter`),
so it runs on every `check.cmd`, not only when someone remembers the post-step.

## 2.2 The nine

    C203  C205  C206     C_shunt trim bank, 56 pF sites (C203 is the ZVS fix)
    C308  C309           C_s bank             <-- THE ZVS FIX
    C318                 C_m bank (P8 review E2)
    C321  C322  C323     27 pF bench-trim sites

Authoritative source: `refdes_dnp` on each line of `parts/parts.json`.

## 2.3 What the files in this directory already do

`BOM.csv` and `CPL.csv` carry the **populated set only** - they are generated
that way now, not filtered afterwards. `BOM-full.csv` is the BOM OF RECORD and
lists every intended part with its `Assembly Class` and an `Instructions`
column, so the nine DNP sites appear there **marked and explained** rather than
silently absent. Against the pre-U3 filtered files:

| | before | after |
|---|---|---|
| CPL.csv data rows | 68 | **59** |
| BOM.csv designators (total) | 68 | **59** |
| BOM.csv lines | 25 | 25 (no line went to zero) |
| `C113875` (56 pF 1206) designators | 21 | **15** |
| `C541492` (27 pF 1206) designators | 6 | **3** |
| occurrences of any of the 9 refs, either file | 9 each | **0** |

`BOM.csv` has no Quantity column - JLC derives quantity from the Designator
list - so removing the refdes IS the quantity correction. The two edited lines
now match `qty_per_board_populated` in `parts/parts.json` exactly (15 and 3).

**Arithmetic check: 70 components in the netlist - 2 etched PCB spirals
(L301/L302, no part to place) - 9 DNP = 59 parts placed, of 68 purchased
lines.**

## 2.4 If you ever regenerate BOM/CPL

Just run `bom_cpl.py` (s11). It emits 59 CPL rows and 59 BOM designators
straight out, because membership comes from the assembly classes in
`parts/parts.json`. No post-step, no board-local script.

`bom_cpl.py` itself refuses to disagree with the declared populate: it derives
the populated count per line from the classes and **exits 1** if that count
differs from `qty_per_board_populated` (15 for `C113875`, 3 for `C541492`), if
a part classed `smt_placed` has no placement, or if a placed part has neither
an LCSC number nor a distributor line. `dfm_check.py --fab-dir fab/` then reads
the files in THIS directory and errors if any of the nine appears in them.

## 2.5 `rf-de-20m-pos.csv` IS NOT THE UPLOAD

It is `fab_export.py`'s raw KiCad pos export and `bom_cpl.py`'s input. It still
contains **all 68 placements including the nine DNP sites**, on purpose (it is
hashed in the export manifest). **Upload `CPL.csv`, never `rf-de-20m-pos.csv`.**

## 2.6 The stencil still has apertures at the nine sites

`F.Paste` carries 161 apertures, including both pads of every DNP site - a
paste gerber has no populate concept. JLC will print paste there and it will
reflow into bare bumps. That is normally cosmetic, but on **C203 and C205 it
is not**: each of those GND pads contains **4 vias that are open on the bottom
face inside the heatsink land** (s5.2). This is one of the reasons POFV is
ordered (s3.2).

---

# 3. WHAT TO ORDER

## 3.1 PCB

| field | value |
|---|---|
| Layers | **4** |
| Size | **120.000 x 80.000 mm** (measured off `Edge.Cuts`, one closed outline, 9600 mm2) |
| Quantity | **5** |
| Thickness | **1.6 mm** |
| Stackup | **`JLC04161H-1080B`** (JLC template code `202601040426384154`, live-verified 2026-08-06) |
| Outer copper | **1 oz** (0.035 mm, F.Cu and B.Cu) |
| Inner copper | **0.5 oz** (0.0152 mm, In1.Cu and In2.Cu) |
| Dielectrics | 0.2444 mm 1080x3 prepreg / 1.065 mm core / 0.2444 mm 1080x3 prepreg |
| Solder mask | any colour |
| Silkscreen | top only (`B.Silkscreen` is empty by design - the bottom is the heatsink face) |

The board's own stackup block is byte-for-byte this template. The L1-L2
dielectric of **0.2444 mm** is load-bearing: it is the return image the /SW
switching loop and both gate loops are designed against. **Do not accept a
substituted lamination.** `stackups.yaml`'s own warning applies - JLC retires
templates without notice, so **re-confirm the template exists at P10** and, if
it is gone, do not silently take the nearest one.

## 3.2 Order-time options - ALL THREE ARE MANDATORY, none is a BOM part

These are the D5 decisions (`architecture/decisions.md`, `architecture/stackup.md`
s5). None of them is expressible in a gerber, so **they exist only if a human
ticks them at order time.**

| option | why | consequence of skipping |
|---|---|---|
| **High-Tg FR4, TG155 or better** | The two etched air-core spirals (L301/L302) dissipate 2.57 W and 2.06 W into their own copper; that copper runs **100-140 C** (`reports/spiral-design.md` s4). JLC's standard FR4 is Tg 130-150. | Laminate near or past Tg under the highest-value components on the board. |
| **ENIG, not HASL** | EPC AN009 specifies ENIG for eGaN assembly. HASL's uneven finish is wrong under a 2.77 x 0.95 mm solder-bar LGA (EPC2019) and wrong under a 0.4 mm-pitch WCSP (U201, LMG1020). It is also wrong under a **flat bottom heatsink land**. | Unassemblable fine pitch, and a bumpy heatsink face. |
| **POFV - epoxy filled and capped vias** | Flatness of the B.Cu heatsink land, and s5.2's measured wick path. | Solder beads on the heatsink mating face; dimpled land. |

**Note on POFV, because the record contains a contradiction worth resolving.**
`stackup.md` s5 asked for POFV because of an LMG1020 via-in-pad, and
`reports/review-board.md` s2.2 correctly points out **that via was never
built** (the nearest GND via to U201 is 0.3 mm outside the ball array). POFV is
nevertheless still required, for two reasons that ARE built:

1. `kicad/constraints.json` (the Q201 `_note`): POFV caps the vias so the B.Cu
   heatsink land is a plane rather than a dimpled surface. Note the same entry's
   correction - **JLC does not sell copper-filled vias**; POFV is resin fill +
   copper cap and adds ~0.5 % to barrel conductance, so it is a **flatness**
   option, not a thermal one. Do not re-budget theta against it.
2. Measured on these gerbers (s5.2): **17 GND vias, 0.30 mm drill, are open at
   BOTH ends** - inside a top-side pad's mask opening and inside the bottom
   heatsink land aperture. Solder can wick from the top joint to the heatsink
   face.

## 3.3 Assembly (PCBA)

| field | value |
|---|---|
| Assembly side | **TOP ONLY** (`B.Paste` has **zero** apertures - verified in the gerber) |
| Parts placed | **59** |
| Unique BOM lines | **25** |
| THT | **1** - J101 (KF128-5.08-2P screw terminal), a pre-approved exception |
| Files | **UPLOAD** `BOM.csv` (Comment / Designator / Footprint / LCSC) + `CPL.csv` (Designator / Mid X / Mid Y / Layer / Rotation, mm). **DO NOT UPLOAD** `BOM-full.csv` - it is the BOM of record and deliberately includes the nine DNP sites and the board features |
| Rotation corrections applied | **1**: U101 `SOIC-8-EP_LM5017_TI-MRA08B`, matched `^SOIC-`, base 0 -> **+270 -> final 270 deg** (`reference/jlc_rotations.csv`) |
| Missing LCSC numbers | **none** |
| Polarity | **70 refs checked pad-by-pad against the schematic, 0 mismatches** - no part is mounted backwards |

The bottom face carries **no parts, no paste and no silk** - it is the heatsink
mating surface and nothing else.

---

# 4. VIA TENTING - DO NOT TURN IT OFF

**Requirement (HS-2, `kicad/constraints.json` placement keepout):** the bottom
heatsink land is a flat, solder-free, mask-opened GND face. Vias are permitted
inside it; **untented non-GND vias are not** - a mask-opened non-GND via there
shorts to the sink, and any mask-opened via there takes solder and breaks
flatness. Carried to P9 three times: `reports/route-notes.md` s10, s16.2, s17.

**Verified on this export, three independent ways:**

1. The board sets `(tenting (front yes) (back yes))` at board level
   (`rf-de-20m.kicad_pcb` line 99).
2. **Zero of the 230 vias carries a per-via `(tenting ...)` override**, so the
   board-level setting governs every one of them. Nothing can silently untent a
   subset.
3. The exported `B.Mask` gerber contains **exactly 11 openings**, every one
   accounted for and **not one of them a via**:

   | count | what | area |
   |---|---|---|
   | 3 | HS1 heatsink land (one aperture, 3 connected components) | 1430.150 mm2 |
   | 4 | H1-H4, M3 mounting holes | 8.041 mm2 each |
   | 2 | J101 THT pads | 4.523 mm2 each |
   | 2 | H5/H6, M2 heatsink clamp holes | 3.800 mm2 each |

**The six non-GND vias inside the heatsink land are tented on B.Cu** - measured
against the exported gerber, not against the board file:

| abs (mm) | board-local (mm) | net | drill / pad | B.Mask opening |
|---|---|---|---|---|
| 25.885, 69.568 | 19.250, 30.233 | `+5V` | 0.20 / 0.45 | **none** |
| 30.867, 74.550 | 24.232, 35.215 | `+5V` | 0.20 / 0.45 | **none** |
| 29.900, 62.400 | 23.265, 23.065 | `+5V_DRV` | 0.20 / 0.45 | **none** |
| 29.700, 61.100 | 23.065, 21.765 | `+5V_DRV` | 0.20 / 0.45 | **none** |
| 29.850, 63.200 | 23.215, 23.865 | `/stage/DRIVE` | 0.20 / 0.45 | **none** |
| 32.200, 60.800 | 25.565, 21.465 | `/stage/DRIVE` | 0.20 / 0.45 | **none** |

**No via-tenting-off option was passed to the plot and none must ever be.**
`kicad-cli pcb export gerbers` is invoked by `fab_export.py` with only
`-o` and `--layers`; there is no tenting flag in the call.

---

# 5. THE BOTTOM HEATSINK LAND (HS1)

## 5.1 It exported correctly

`HS1` is a `board_only exclude_from_pos_files exclude_from_bom` footprint
(`aiee:HS2_HEATSINK_LAND`) with five `B.Cu` + `B.Mask` GND pads. In the
exported `B.Mask` gerber:

- **present, 1430.150 mm2**, as three connected components (616.275 + 608.970
  + 204.905 mm2) - the split is the deliberate notching around the six non-GND
  vias and the M2 clamp holes, not a dropped aperture;
- **100.00 % of it sits over B.Cu copper** (the 5999 mm2 GND island). The sink
  bolts onto bare GND metal, not onto solder mask;
- bounds x 12.23..42.63, y 49.33..109.33 (board-local x 5.6..36.0,
  y 10.0..70.0), inside the HS-2 keepout rect.

**Mechanical constraint that travels with it (HS-1 / SPIRAL-6):** the heatsink
must be **theta_HS <= 0.7 C/W MEASURED, in forced air**, and its body **must
not extend past board-local x = 40 mm** - a conductive plate under a PCB
air-core spiral is a shorted turn and no copper cutout prevents it. Grow it in
-x, +/-y or fin height, never in +x. Without the 0.7 C/W the FET pair does not
close thermally (waiver 6, `reports/verify-waivers.md` s2).

## 5.2 The one thing to be aware of about the land

87 of the 93 vias inside the land are GND (by design - they are the thermal
path, and notching the aperture around them would throw away contact area).
**17 of those are also inside a top-side pad's solder-mask opening**, i.e. they
are open at both ends:

| owning top pad | count | note |
|---|---|---|
| `C203.2` | 4 | **C203 is DNP** - bare paste over an open barrel |
| `C205.2` | 4 | **C205 is DNP** - same |
| `C102.2` | 3 | |
| `C211.2`, `R201.2`, `R202.2` | 1 each | |
| (pour-owned, no pad) | 3 | |

All are 0.30 mm drill, all GND, so there is no electrical hazard - the sink is
at land potential. The hazard is mechanical: solder can wick down a 0.30 mm
barrel and bead on the mating face. **POFV (s3.2) closes this**, which is why
it stays on the order even though its original LMG1020 rationale went away.
This is a *finding*, not a defect: no rule was violated and nothing was
weakened to pass. If POFV is ever dropped, inspect the bottom face for beads
before mounting the sink.

---

# 6. FIDUCIALS

Three global fiducials, all present in `F.Cu` and `F.Mask`, all correctly
absent from BOM/CPL (`smd board_only exclude_from_pos_files exclude_from_bom`)
and correctly **absent from `F.Paste`**:

| ref | position (mm) | copper | mask opening |
|---|---|---|---|
| FID1 | 24.635, 47.335 | 1.000 mm dia (0.7849 mm2) | 2.000 mm dia (3.1406 mm2) |
| FID2 | 118.635, 43.335 | 1.000 mm dia | 2.000 mm dia |
| FID3 | 31.635, 91.335 | 1.000 mm dia | 2.000 mm dia |

Not collinear, spread over three corners of the assembly area.

---

# 7. DFM RESULT

    gate.py --gate dfm  ->  PASS,  0 failing,  0 findings of any severity

Run twice, agreeing: once by `gate.py` on its own scratch re-export
(`reports/gate-dfm.json`), and once by `dfm_check.py --fab-dir fab/` **on the
exact files in this directory** (`reports/dfm_check-shipped.json`). Both are
gerbonara reading the shipped gerbers - a different geometry path from every
board-file check the pipeline runs.

| | measured | JLC `4layer_1oz` floor | margin |
|---|---|---|---|
| min trace width | 0.2000 mm | 0.1016 mm | 1.97x |
| min drill | 0.200 mm | 0.200 mm | **at the floor** |
| min silk stroke | 0.1500 mm | 0.150 mm | at the floor |
| copper to edge | no finding | 0.300 mm | - |
| hole to hole / hole to edge | no finding | 0.500 / 0.400 mm | - |
| annular ring | no finding | 0.100 mm | - |
| mask dam | no finding | 0.100 mm | - |
| silk over mask opening | none | - | - |
| paste aperture with no mask opening | none | - | - |
| CPL polarity vs schematic | 70 refs, 0 mismatches | - | - |
| BOM completeness | 0 missing LCSC | - | - |
| layer completeness | all 4 copper + 2 mask + 2 silk + closed Edge.Cuts | - | - |

**Zero warnings is unusual and is real** - this board's silk was already
regenerated at 0.15 mm, so KiCad's stock 0.12 mm advisory never fires.

**Two things at the floor, both deliberate, both fine but worth knowing:**

- **0.200 mm drill x 9 vias.** Exactly JLC's 4-layer minimum via drill (pad
  0.45 mm = exactly the minimum via diameter). These are the nine 0.2/0.45
  signal vias, six of which are the tented land vias in s4. Zero process
  margin; if JLC's minimum ever moves, these are what breaks. The other 317
  holes are 0.30 mm or larger.
- **0.150 mm silk stroke.** Exactly the minimum. Legible, but do not expect
  crisp small text.

**The known waiver classes did NOT resurface in gerber form**, and that is
expected rather than lucky - all three are rules this board sets on ITSELF,
tighter than JLC's:

| class | board rule | JLC floor | gerber verdict |
|---|---|---|---|
| EPC2019 die-pitch spacing (31 + 13 + 4 `clearance`) | `aiee_hv_143v_SW` 0.8 mm | 0.1016 mm | 0.350 mm passes JLC with 3.4x |
| Spiral inner-layer bridge pads (2 `padstack`) | "SMD pad has no outer layers" | n/a | inner-only pads are legal copper; nothing to report |
| Pour fan-in track widths (4 `track_width`) | `aiee_pwr_width_*` 8.4-11.9 mm | 0.1016 mm | 0.25-7.65 mm all pass JLC |

Those waivers remain owner-approved at H4 in `reports/verify-waivers.json`;
this gate simply had no reason to raise them.

**No rule and no check was weakened anywhere in P9.** `jlc_capabilities.yaml`,
the `.kicad_dru`, the netclasses and `constraints.json` are untouched.

---

# 8. HUMAN STEPS BEFORE ORDERING (checkpoint 5)

The local engine covers the big classes so that this step finds nothing new -
**not so it can be skipped.** JLCDFM has no public API.

1. Upload `rf-de-20m_gerbers.zip` to **jlcdfm.com** and to the JLC order
   viewer. Eyeball: rendering sane, 4 copper layers present and in order, board
   reads 120 x 80 mm.
2. **Confirm the bottom side shows one large bare-copper land, not mask.** If
   the B.Mask renders as a solid sheet with no window, the package is wrong -
   stop.
3. **Confirm the M3 (H1-H4, 3.2 mm) and M2 (H5/H6, 2.2 mm) holes read as
   NON-PLATED.** The drill file is a single mixed-plating Excellon
   (`TF.FileFunction,MixedPlating,1,4`) and marks T5/T6 `NonPlated,NPTH` as X2
   attributes. JLC reads those - but this is the one place a merged drill file
   can be misread, so look.
4. Upload `BOM.csv` + `CPL.csv` and step through JLC's placement preview.
   **Count the parts: it must say 59.** Check the polarized/oriented parts
   visually: C101/C102 (electrolytic, "+" on the chamfered end - see
   workspace LEARNINGS 2026-08-08), U101 (270 deg after correction), U201,
   Q201/Q202, J201/J301.
5. **Confirm C203, C205, C206, C308, C309, C318, C321, C322, C323 are NOT in
   the preview.**
6. Tick **TG155+ base material**, **ENIG**, **POFV**. None of them is in a file.
7. Only then check EPC2019 stock.

---

# 9. BENCH NOTE - HOW THIS BOARD IS MEANT TO BE RUN

**25-30 V bus, 100-150 W out, with fans.** The populate in these files is tuned
for that operating point.

**A 40 V bus is not a free upgrade, and the simulation says so.** The `sim`
gate's one failing item is exactly this (`reports/gate-sim.json`,
`sims/bus_derating.cir`):

    vds_pk_40v_v = 172.547 V  against SIM-1's <= 155 V
    (1.29x derate on the EPC2019's 200 V BVDSS)

The ZVS populate in these files (C203 DNP, C308/C309 DNP, C320 fitted) was
solved at the 30 V bench point. At 40 V it is **under-shunted** - nonlinear
Coss supplies less charge-equivalent capacitance over a larger swing - so the
drain peak rises past the derate. **One populate cannot serve both bus points:
running 40 V needs its own C_shunt bank setting, re-solved against the
simulation, not guessed.** (Workspace LEARNINGS 2026-08-08
`[sim][classE][gan]`.) This is a bench constraint on a board that is otherwise
fab-ready; it does not affect what is ordered.

Forced air is not optional at any bus voltage: **theta_HS <= 0.7 C/W measured**
is a hard requirement (HS-1 / OPEN-9), and the `check_thermal` waiver rests on
it.

---

# 10. CONTENTS

| file | sha256 | bytes |
|---|---|---|
| `rf-de-20m_gerbers.zip` | `7c6adf4e697c1d0b6a5d09b0ea4f3a0b24030817df35aa35fc5f18a16ae677cd` | 165232 |
| `BOM.csv` (upload; 59 designators) | `7fbf8861602c5b8354cc342416e35b0204864567c1607836f1c4f75e5de448df` | 1438 |
| `BOM-full.csv` (BOM of record; **not** an upload) | `6f0ff0867bd46214b3ecd32dae2dc39d53f78ca96281fbf0408af4c2901ef740` | 3536 |
| `CPL.csv` (59 rows) | `4ce10f04dbdab7f954c55252265d121bceb0dab22f5f1696d8318a095cf54d93` | 2074 |
| `rf-de-20m-pos.csv` (**raw, all 68 placements, NOT an upload**) | `9e8a2b6a47d5ad86dcac283b83931bc03dade3c91008bcb411291497b19b729c` | 5201 |

`CPL.csv` is byte-for-byte the file the retired filter produced. `BOM.csv` has
the identical 25 rows; only the ordering of the `C113875` line moved, because
the generator now sorts by the line's first POPULATED designator (C301) instead
of by a designator it had just deleted (C203).

Inside `rf-de-20m_gerbers.zip` / `gerbers/` (13 files, per-file sha256 in
`reports/fab_export.json`):

| file | layer |
|---|---|
| `rf-de-20m-F_Cu.gtl` | F.Cu (1 oz) |
| `rf-de-20m-In1_Cu.g1` | In1.Cu (0.5 oz) - GND |
| `rf-de-20m-In2_Cu.g2` | In2.Cu (0.5 oz) - GND |
| `rf-de-20m-B_Cu.gbl` | B.Cu (1 oz) - GND + heatsink land |
| `rf-de-20m-F_Silkscreen.gto` | F.Silkscreen |
| `rf-de-20m-B_Silkscreen.gbo` | B.Silkscreen (empty by design) |
| `rf-de-20m-F_Mask.gts` | F.Mask (172 openings) |
| `rf-de-20m-B_Mask.gbs` | B.Mask (11 openings - see s4) |
| `rf-de-20m-F_Paste.gtp` | F.Paste (161 apertures) |
| `rf-de-20m-B_Paste.gbp` | B.Paste (**0 apertures**) |
| `rf-de-20m-Edge_Cuts.gm1` | Edge.Cuts (closed, 120 x 80 mm) |
| `rf-de-20m.drl` | Excellon, metric, mixed plating, 326 holes |
| `rf-de-20m-job.gbrjob` | Gerber job file |

Layer order in the export is **physical stackup order** (F.Cu, In1.Cu, In2.Cu,
B.Cu), not KiCad's raw layer ids.

---

# 11. REPRODUCE

    .venv/Scripts/python .claude/skills/ai-ee/scripts/fab_export.py \
        --pcb boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb \
        --out-dir boards/rf-de-20m/fab \
        --out boards/rf-de-20m/reports/fab_export.json

    # --pos pins the raw export already in this directory so a rerun cannot
    # perturb the hashed pos file; drop it to re-export from the board.
    .venv/Scripts/python .claude/skills/ai-ee/scripts/bom_cpl.py \
        --pcb boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb \
        --out-dir boards/rf-de-20m/fab \
        --pos boards/rf-de-20m/fab/rf-de-20m-pos.csv \
        --parts boards/rf-de-20m/parts/parts.json \
        --out boards/rf-de-20m/reports/bom_cpl.json

    .venv/Scripts/python .claude/skills/ai-ee/scripts/gate.py --gate dfm \
        boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb \
        --out boards/rf-de-20m/reports/gate-dfm.json

    # the shipped-package audit + the BOM-completeness leg the gate cannot run
    # (gate.py looks for parts.json BESIDE the board; this workspace keeps it
    #  at parts/parts.json - workspace LEARNINGS 2026-08-09)
    .venv/Scripts/python .claude/skills/ai-ee/scripts/dfm_check.py \
        --pcb boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb \
        --fab-dir boards/rf-de-20m/fab \
        --parts boards/rf-de-20m/parts/parts.json \
        --schematic boards/rf-de-20m/kicad/rf-de-20m.kicad_sch \
        --out boards/rf-de-20m/reports/dfm_check-shipped.json
