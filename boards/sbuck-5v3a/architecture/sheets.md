# sbuck-5v3a - schematic sheet plan, net contract and refdes map

## 1. Sheet plan: ONE flat root sheet

| Sheet | Blocks (`blocks.md`) | Refdes block | `#PWR` base |
|---|---|---|---|
| **root** (no child sheets) | B1-B9, all of them | **1-99** | **100** |

**Decided: a single root sheet, no hierarchy.** 33 placed parts (2 of them DNP)
plus 7 test pads and 4 mounting holes. This is one function - a single-rail
converter - with one floorplan that runs straight through from the left edge to
the right edge, so there is no organising principle for a split to express. The
full-run recipe explicitly allows one schematic agent for a board this size.

The decisive argument is the **net-naming risk**, not the part count. KiCad
names a net from a hierarchical label as `/<sheet>/<LABEL>`, and every
`constraints.json` consumer at P5-P8 matches on the exact string; a mismatch is
silently no-op'd rather than failing. That trap cost the lumina-par run a P4
amendment and forced rf-de-20m into a binding root-label contract for a single
crossing net. A flat sheet removes the entire class: local labels come out as
`/NAME` and power symbols come out bare, with no sheet prefix anywhere.

Refdes are unique by construction on one sheet. The blocks below are a
*readability* convention for the BOM, not a uniqueness mechanism.

---

## 2. Net-naming contract - BINDING ON P4

These are the CANONICAL names. `constraints.json` matches them literally.

| Canonical net | Kind | Carries |
|---|---|---|
| `/VIN` | local label | J1.1 -> F1 -> Q1 drain. **2.44 A at 7 V**, raw and unprotected |
| `+VIN` | **power symbol / global label (bare)** | Q1 source -> C4-C9 -> U1 VIN. 2.6 A design, 1.5 A rms in the ceramics |
| `/SW` | local label | U1 SW -> L1. **3.53 A pk, hard-switched, 500 kHz** |
| `+5V` | **power symbol / global label (bare)** | L1 -> C10-C15 -> J2. 3.3 A design ceiling |
| `GND` | **power symbol (bare)** | F.Cu island + In1 + In2 + B.Cu. 3.3 A return |
| `/EN` | local label | R2/R3 junction -> U1 EN. TP5 |
| `/FB` | local label | R6/R7 junction -> U1 FB. High-Z, keep away from `/SW` and L1 |
| `/COMP` | local label | U1 COMP -> R5 -> C2 -> GND |
| `/BST` | local label | C1 -> U1 BST |
| `/RT` | local label | U1 RT -> R4 -> GND |
| `/QGATE` | local label | Q1 gate, R1 to GND, D2 anode |

**Rules P4 must not break:**

1. `+VIN`, `+5V` and `GND` must be **power symbols or global labels** so they
   come out bare. A local label would produce `/+VIN` and five
   `constraints.json` entries would stop matching in silence.
2. Every other net above must be a **local label on the root sheet**, producing
   the leading `/`. Do not "tidy" the slash away.
3. **Do not rename anything to end in `_P`, `_N`, `_H`, `_L`, `DP`, `DM`, `+` or
   `-`.** `rules_gen.detect_diff_pairs` auto-pairs `high_speed` nets with those
   suffixes; `/SW` is declared under `high_speed` and a suffix collision would
   silently emit differential-pair gap rules and an inner-layer track ban on the
   most current-carrying node on the board. Current names are safe.
4. `diff_pairs` is an **explicit empty list** in `constraints.json` - there is no
   differential net on this board and the empty list disables auto-discovery.

---

## 3. Refdes map

### B1 input entry + reverse polarity (`/VIN`, `/QGATE`)

| Ref | Part class | Note |
|---|---|---|
| **J1** | 2-pin 5.08 mm THT screw terminal, DB128L-5.08-2P class | **LEFT short edge.** DNP for assembly, hand-soldered (Q25) |
| **F1** | 5 A slow-blow 1206 chip fuse, Bel Fuse C1T class | 63 V DC, 20 mOhm, 5.3 A^2s. >= 20 mm^2 copper per pad, kept off the U1/L1 zone |
| **Q1** | P-channel MOSFET SOIC-8, AO4407A class | **drain to input, source to load.** >= 50 mm^2 of drain+source copper |
| **R1** | 100k 0603 | gate to GND. Also the polarity-reversal turn-off path |
| **D2** | 15 V Zener SOD-123 | anode at gate, cathode at source. Clamps \|Vgs\| |

### B2 input capacitance (`+VIN`)

| Ref | Part class | Note |
|---|---|---|
| **C4** | 100 uF / 35 V hybrid-polymer alu SMD can, KNM2100UF35V149EC0055 class | **ESR 50-300 mOhm is a REQUIREMENT.** Place at the input edge (coolest corner). Not a low-ESR polymer, not a plain electrolytic |
| **C5-C8** | 4x 4.7 uF / 50 V X7R 1206, 1206B475K500NT class | 1.5 A rms shared four ways |
| **C9** | 100 nF / 50 V X7R 0603 | **AT the U1 VIN pin.** Innermost element of the hot loop |

### B3/B4 converter, compensation, UVLO (`+VIN`, `/SW`, `/EN`, `/FB`, `/COMP`, `/BST`, `/RT`)

| Ref | Part class | Note |
|---|---|---|
| **U1** | AP64350SP-13 class, SO-8-EP | Single GND pin + exposed pad on the same net. No VCC pin |
| **C1** | 100 nF / 50 V X7R 0603 | BST to SW. Required, not optional |
| **R4** | 200k 1% 0603 | RT -> 500 kHz (`RT[kOhm] = 100000/fsw[kHz]`) |
| **R5** | Rcomp, 0603 | vendor start 14k. **P4 RE-DERIVES against 5x22 uF** |
| **C2** | Ccomp, 0603 | vendor start 3.3 nF. **P4 re-derives** |
| **C3** | 47 pF C0G 0603 | optional feedforward across R6 |
| **R2** | **105k 1% 0603** | +VIN -> EN. UVLO top |
| **R3** | **24.0k 1% 0603** | EN -> GND. UVLO bottom. Target VON 6.2 V / VOFF 5.3 V |

### B5/B6 output filter and feedback (`/SW`, `+5V`, `/FB`)

| Ref | Part class | Note |
|---|---|---|
| **L1** | 6.8 uH molded alloy-composite, FAUL1050-6R8MT class | 11.5 x 10 mm, 4.1 mm. **>= 125 C rated, DCR <= 25 mOhm at 20 C** |
| **C10-C14** | 5x 22 uF / 25 V X7R 1210, TCC1210X7R226K250MT class | **4x is the authorised floor, 3x is not** (blocks.md B5) |
| **C15** | 4.7 uF / 16 V X7R 0805 | output HF bypass at the terminal / test point |
| **R6** | ~116k **0.1%** 0603 | FB top. 0.5% is the absolute floor |
| **R7** | ~22.1k **0.1%** 0603 | FB bottom. Ratio 6.249 -> 5.000 V from a 0.8 V ref |

### B7/B8/B9 indicator, output, snubber

| Ref | Part class | Note |
|---|---|---|
| **D1** | green 0805 LED, KT-0805G class | ~1 mA |
| **R8** | 2.2k 0603 | LED series |
| **J2** | same class as J1 | **RIGHT short edge.** DNP for assembly |
| **R9** | 0603, **DNP** | snubber R. 10-33 Ohm if ever fitted |
| **C16** | 0603, **DNP** | snubber C. 470 pF - 2.2 nF if ever fitted |
| **TP1-TP7** | 1.5 mm bare SMD round pads | `+VIN`, `/SW`, `+5V`, `/FB`, `/EN`, `GND`, and a scope-ground pad ~5 mm from TP3 |
| **H1-H4** | 3.2 mm NPTH | corners, inset 3.5 mm, 6.5 mm keepout, isolated from GND |

Total: 33 placed components (2 DNP), 7 test pads, 4 holes.

---

## 4. Floorplan for P6 - straight-through, left to right

The board is 50 mm wide (x) by 40 mm tall (y); the **short edges are left and
right**, which is where the two connectors go (Q10).

| Zone | x | Contents |
|---|---|---|
| **input** | 0 - 13 | J1, F1, Q1, D2, R1, C4. The coolest corner - C4's life is set by local board temperature |
| **converter** | 13 - 32 | C5-C9, U1 (thermal island, centred near x=21 y=20), C1, R2-R5, C2, C3, /SW pour, R9/C16, L1 |
| **output** | 32 - 50 | C10-C15, R6/R7, D1/R8, TP1-TP7, J2 |

Non-negotiables that no annealer can discover:

1. **Hot loop first.** `C5-C9 -> U1 VIN -> U1 PGND -> C5-C9` is the shortest
   loop on the board, all on F.Cu, with C9 physically closest to the pin and
   In1 solid GND directly beneath as the image plane.
2. **`/SW` is a short wide pour**: >= 2.5 mm wide, <= 8 mm long, <= 40 mm^2,
   F.Cu only, never inner, never near a board edge or connector. The TP2 tap is
   a stub that counts against the 40 mm^2.
3. **R6/R7 and the `/FB` trace hug the FB pin and stay away from `/SW` and L1** -
   an explicit rule in all three candidate vendor layouts.
4. **R9/C16 sit directly across the SW pour to PGND** with a low-inductance path
   even while unpopulated. Place by explicit `place_edit`.
5. **C4 and F1 stay >= 10-12 mm from U1 and L1** (declared as `separation`
   entries): C4 because its life halves every 10 C, F1 because it is a
   deliberate 0.15 W heat source.
6. **16 thermal vias in U1's pad** at 0.3 mm / 1.0 mm pitch, plus 8-12 stitching
   vias in the surrounding F.Cu island. `check_thermal` will not catch their
   absence (see `power_tree.md` s4.3) - this is a review gate.
7. **No layer transitions on `/VIN`, `+VIN`, `/SW` or `+5V`.** A transition needs
   6-8 vias at 0.5 A/via. GND is plane-fed through the stitching field.

Parts to place by explicit `place_edit` and **lock** before the annealer runs:
`U1`, `L1`, `C5-C9`, `C1`, `R9`, `C16`, `J1`, `J2`, `H1-H4`.

---

## 5. P4 notes (schematic phase)

1. **Re-derive the compensation.** The vendor's Rcomp/Ccomp are quoted for
   2x 22 uF; the bank is 5x 22 uF. Target fc 25-50 kHz, phase margin >= 45 deg,
   using the AP64350 datasheet's Eqs 12-20. Record the numbers on the schematic.
   If the loop cannot close there, drop to 4x 22 uF and record it.
2. **R6/R7 must be 0.1% parts in the BOM**, not 1% with a 0.1% note. The
   reference tolerance alone spends 60% of the +/-2% window.
3. **UVLO is 6.2 V / 5.3 V, not the delegate's 6.5 / 6.0.** Use the AP64350
   divider equations (they include the 4.114 uA and 5.5 uA internal pull-ups -
   a naive divider calculation is wrong) and verify against the P8 sim bench.
4. **No gate RC on Q1 and no gate capacitor.** The body diode already bypasses
   the channel during inrush. This is a decision, not an omission - do not let
   ERC or a reviewer add one.
5. **The snubber R9/C16 must exist in the netlist** as DNP so their pads,
   clearance and routing are accounted for at P6/P7. Populating later is then a
   BOM change, not a respin.
6. **Test pads are real nets.** TP7 is a second GND pad placed for a scope
   spring ground, ~5 mm from TP3, not a duplicate of TP6.
7. **Silkscreen** (Q33): board name + rev A + date; "VIN 7-18V" and "VOUT 5V 3A"
   with polarity marks at both terminals - this is the *only* mitigation for a
   swapped-connector event, which is not survivable by design; pin-1 marks on
   every polarised part; every test point labelled; no logo.
8. **J1 and J2 are DNP for assembly** and must appear as such in the BOM/CPL.
