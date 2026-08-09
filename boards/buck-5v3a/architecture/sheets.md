# buck-5v3a - schematic sheet plan

## 1. ONE FLAT SHEET - and why that is the right answer, not laziness

**No hierarchy. One root sheet, `buck-5v3a.kicad_sch`, containing all 25 placed
parts.** This is a deliberate deviation from the pipeline's usual hierarchical
default, recorded here so it is not mistaken for an omission:

- The board has **one function** (7-18 V -> 5 V/3 A) and **one rail**. There is no
  second function to isolate, no repeated block to instance, no MCU/peripheral split.
- Hierarchy costs a real thing here: KiCad names a net from a hierarchical label as
  **`/<sheet>/<LABEL>`**, so every net in `constraints.json` would acquire a sheet
  prefix, and **a net name that does not match is silently no-op'd by every P5-P8
  consumer** - the trap that cost the lumina-par run a P4 amendment. A flat sheet
  makes local labels come out as plain `/SW`, `/FB`, and removes that failure mode
  entirely.
- 25 parts fit on one A4 sheet with room to lay it out in signal-flow order
  (left to right: J1 -> F1 -> Q1 -> Cin/U1 -> L1 -> Cout -> J2), which is also the
  board floorplan. One sheet, one floorplan, one reading order.

The threshold for revisiting this: if P3/P4 adds an input filter stage or a second
rail, split at that point - not before.

| Sheet | Blocks (`blocks.md`) | Refdes block | `#PWR` base |
|---|---|---|---|
| **root** (flat) | B1-B6, all of them | **1-99** per prefix | **100** (`#PWR0100`+) |

Refdes uniqueness is structural on a single sheet. `pwr_base = 100` is still declared
explicitly so that a later hierarchy split (see threshold above) starts from a
convention rather than colliding with `#PWR01`.

## 2. Refdes assignment - BINDING ON P4

`constraints.json` (`placement.groups`, `placement.separation`, `thermal.ref`)
references these refdes **by name**. A rename silently drops the constraint that
mentions it - `place_anneal` collects unknown separation refs but a dropped grouping
just produces a worse placement (S14 lesson). If P4 must rename, update
`constraints.json` in the same commit.

| Ref | Part / class | Block | Notes |
|---|---|---|---|
| **J1** | 5.08 mm 2P THT screw terminal, WJ500V-5.08-2P class | B1 | left edge, wire entry outward, silk `VIN 7-18V` |
| **F1** | 4 A 1206 one-shot fuse, 1206T4A63V class | B1 | coolest corner, next to J1 |
| **Q1** | P-FET, AO4407A class SO-8 (AOD403 DPAK alt) | B2 | source `/VIN_FUSED`, drain `+VIN` |
| **R6** | 10 kohm gate pull-down | B2 | NOT 100-330 ohm - `decisions.md` D6 |
| **D3** | zener 12-15 V, Vgs clamp | B2 | Vz <= Vgs(max) - 5 V of the chosen Q1 |
| **D2** | TVS, SMBJ20A class (20 V standoff / 32.4 V clamp) | B3 | on `+VIN`, AFTER Q1 |
| **C1, C2** | 10 uF 50 V X7R 1210 | B3 | >= 1.5 A RMS at 450 kHz; X5R DISQUALIFIED |
| **C3** | 100 nF 50 V 0603 | B3 | at the VIN pin, same layer, shortest loop |
| **U1** | **AP63356QZV-7**, VDFN-13 3x2 | B4 | PWM-only sibling - `decisions.md` D3 |
| **C4** | 100 nF bootstrap (BST-SW) | B4 | required, not optional |
| **R1, R2** | FB divider 158k / 30.1k, **0.5 % or better** | B4 | Vout = 0.8 x (1 + R1/R2) = 5.00 V |
| **R3, R4** | EN/UVLO divider 86.6k / 20k, 1 % | B4 | ~6.2 V rising / ~5.3 V falling |
| **L1** | 6.8 uH, Isat >= 6 A, DCR <= 30 mohm, shielded, 125 C | B5 | **P3 must sweep 6.8 uH - the P1 shortlist has none** |
| **C5, C6** | 22 uF 25 V X7R 1210 | B5 | ~30 uF effective after 5 V DC bias |
| **C7** | 100 uF polymer | B6 | **RESERVED refdes, NOT FITTED** (H1 open 1) |
| **J2** | same terminal family as J1 | B6 | right edge, silk `5V 3A` |
| **D1, R5** | green LED + 1 kohm | B6 | 1.9 mA |
| **TP1, TP2, TP3** | test points | B6 | `+VIN`, `+5V`, `GND` |
| **H1-H4** | M3 mounting holes | - | created by `board_init --mounting-holes 4`, board-only (not in the schematic, excluded from BOM/CPL/parity) |

Prefix blocks for anything P3/P4 adds: **C8+, R7+, D4+, TP4+**. Do not renumber
existing refdes to close gaps.

## 3. Net-naming contract - BINDING ON P4

These are the **canonical names**. `constraints.json` is written against them, and a
mismatch is a silent no-op in `check_current`, `check_thermal`, `rules_gen`,
`planes_gen` and `route_critical`.

| Net | Type | From -> to | Declared in `constraints.json` |
|---|---|---|---|
| `/VIN_RAW` | local label | J1.1 -> F1 | `power` 3.0 A, `pdn: false` |
| `/VIN_FUSED` | local label | F1 -> Q1 source | `power` 3.0 A, `pdn: false` |
| `+VIN` | **power symbol** | Q1 drain -> D2, C1-C3, U1.VIN, R3 | `power` 3.0 A |
| `/VIN_GATE` | local label | Q1 gate -> R6 -> D3 | not declared (uA) |
| `/EN` | local label | R3/R4 midpoint -> U1.EN | not declared (uA) |
| `/BST` | local label | C4 -> U1.BST | not declared |
| `/SW` | local label | U1.SW -> L1, C4 low side | `power` 3.6 A dT 20, `pdn: false` |
| `+5V` | **power symbol** | L1 -> C5, C6, J2, R5, R1 top | `power` 3.6 A |
| `/FB` | local label | R1/R2 midpoint -> U1.FB | not declared |
| `/LED_A` | local label | R5 -> D1 anode | not declared |
| `GND` | **power symbol** | everything | `power` 3.6 A, `plane_fed`, `pdn: false` |

Rules P4 must honour:

- **Power nets are bare global power symbols** (`+VIN`, `+5V`, `GND`); everything
  else is a **root-sheet local label**, which on a flat sheet yields `/NAME` with no
  prefix. Do not use hierarchical labels - there is no hierarchy.
- **A power symbol's net name comes from its VALUE field, not its library pin name**
  (LEARNINGS 2026-07-28). A `+VIN` symbol cloned from `+12V` and not re-valued will
  produce the net `+12V` and silently orphan every `+VIN` constraint.
- `/FB` senses at the **Cout node**, not at the inductor, and is routed away from
  `/SW` and L1 (DS41948 Figure 47, buck.md s4).
- U1's `COMP` pin is **tied to GND** (internal compensation). `PG` is left
  unconnected; mark it with a no-connect flag so ERC stays clean. Pin 7 is `NC` -
  leave it floating, do not tie it to anything.
- `TP1` is on **`+VIN`** (post-protection), not on `/VIN_RAW`.

## 4. Placement groups the sheet plan implies

These become `placement.groups` in `constraints.json` and drive P6 clustering. They
are listed here because the sheet layout should mirror them - a schematic drawn in
this order makes the placement obvious.

1. **`hotloop`** - anchor **U1**, members **C1, C2, C3, C4**. The Cin -> VIN -> GND
   loop is the shortest loop on the board and outranks every other placement
   preference (buck.md s3, DS41948 rule 2). C4 (BST) sits directly against the
   BST/SW pins.
2. **`fb`** - anchor **U1**, members **R1, R2** plus **R3, R4**. FB network as close
   to the FB pin as possible (DS41948 rule 5); the EN divider rides along because it
   is the same small-signal corner of the part.
3. **`output`** - anchor **L1**, members **C5, C6**. Inductor as close to SW as
   possible (rule 3), output caps' GND return short (rule 4).
4. **`rpp`** - anchor **Q1**, members **R6, D3, D2**. The gate network must be at the
   FET; the TVS lands on the same `+VIN` node.

Separations (centroid-to-centroid, `place_anneal` cost terms):
**U1 <-> L1 >= 8 mm** (~2.5 mm body gap for 3x2 and 8x8 bodies) and
**U1 <-> F1 >= 15 mm** (F1 in the cool corner by J1).

## 5. Area P6 must leave clear (no footprint, no constraint - a placement instruction)

- **~40 mm^2 beside J2 for C7**, the reserved 100 uF polymer (D6.3 x 5.8 mm class),
  so that a "yes" to H1 open question 1 is a BOM change and not a re-layout.
- **~60 mm^2 between J1 and F1** for the optional input filter A7 asks room for. No
  unpopulated footprints are added: a DNF part on a JLC PCBA BOM buys confusion, and
  the requirement is for *room*, not for parts.
