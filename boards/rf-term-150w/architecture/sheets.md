# rf-term-150w - hierarchical sheet plan

## ONE SHEET. P4 SPAWNS A SINGLE SCHEMATIC AGENT.

There is no hierarchy. The whole design is 3 electrical parts, 3 mechanical footprints and
2 nets. **Everything lives on the root sheet; there are no child sheets and no hierarchical
labels.** Decomposing this would add sheet-prefix net names and a sheet-symbol layer of
indirection to a circuit that fits on one line of text.

| Sheet | Blocks (`blocks.md`) | Refdes block | `#PWR` base |
|---|---|---|---|
| **root** (`rf-term-150w.kicad_sch`) | B1 RF port, B2 adjustment, B3 termination element, B4 mechanical | **1-99** (all prefixes) | **1** |

Refdes uniqueness is trivial - one sheet, six refdes.

---

## 1. Net-naming contract - BINDING ON P4

Only two nets exist. Getting their spelling wrong silently no-ops every P5-P8 consumer that
reads `constraints.json`, so it is written here as a contract rather than left to chance.

| Canonical net | How P4 must create it | Carries |
|---|---|---|
| **`/RF`** | a **local label spelled `RF`** placed on the root-sheet wire between J1.1, C1's stator pin and R1.1 | 86.6 Vrms / 122.5 Vpeak / 1.732 Arms, DC-25 MHz |
| **`GND`** | the **global power symbol `GND`** on J1.2, C1's rotor pin and R1.2 | RF return + the flange bond |

Two rules behind that table:

1. **A root-sheet local label comes out as `/<LABEL>`, so `RF` becomes `/RF`.** Every
   `constraints.json` entry below spells it `/RF`. If P4 uses a hierarchical label, a global
   label or a different spelling, `check_current`, `check_creepage`, `check_return_path`,
   `rules_gen`'s HV and width rules and `planes_gen`'s reference guarantee all silently stop
   matching. There is no error - the checks just pass on an empty set.
2. **Power symbols are global and bare: `GND`, never `/GND`.**

## 2. Symbols, pins and the two pin-mapping calls P4 must get right

| Ref | Part class | Symbol | Footprint | Pins -> nets |
|---|---|---|---|---|
| **J1** | SMA female jack, right-angle THT (SMA-KWE class) | `Connector:Conn_Coaxial` | `Connector_Coaxial:SMA_BAT_Wireless_BWSMA-KWE-Z001` | 1 (centre) -> `/RF`, 2 (shield, 4 legs, one net) -> `GND` |
| **R1** | 50 ohm 250 W flanged RF termination (T50R0-250-12X class) | `Device:R` (2-pin passive) | **custom, P3 builds** - see `blocks.md` s2.3 | 1 (RF tab) -> `/RF`, 2 (flange, 2 lands) -> `GND` |
| **C1** | 3-33 pF 250 V film trimmer, top-adjust (BFC2808 class) | `Device:C_Variable` | **custom, P3 builds** - dia 7.5 mm THT radial, 2.5 mm pin grid | **stator -> `/RF`, ROTOR -> `GND`** |
| **H1-H3** | M3 mounting hole | `Mechanical:MountingHole` | `MountingHole:MountingHole_3.2mm_M3` | none - **`board_only`** |

**Call 1 - C1 rotor to GND, not to RF.** The rotor is the terminal mechanically continuous
with the adjustment screw the operator touches with a tuning tool, at 122.5 Vpeak, while
transmitting (the intended use case per A6). Grounding it puts the touched metal at ground
potential. This is a requirements-s8-F1 safety consequence, not a preference. If the chosen
part does not distinguish rotor from stator, say so and fall back to an insulated tuning tool
plus a "tune at reduced drive" README instruction - **do not silently pick a pin.**

**Call 2 - H1-H3 must be `board_only`.** A mounting hole that carries a symbol becomes a BOM
line and a CPL line (LEARNINGS 2026-07-29 - fix it at the symbol, not downstream). The
budget is <= 4 BOM lines and <= 6 placements; `board_only` holes keep the BOM at 3 lines,
the CPL at 3 placements and the total footprint count at exactly 6.

## 3. Interface nets and placement groups

There are no inter-sheet interfaces. For P6, the two groupings that matter are:

| Group | Members | Rule |
|---|---|---|
| `port` | anchor **J1**, member **C1** | C1's shunt must tap the RF node at the port end. The tap point, not C1's body, is what matters - the stub between them is in series with C and shifts C_eff by <0.3% at 25 MHz (`blocks.md` s4.3). Keep the stub as short as C1's dia 7.5 mm body allows. |
| - | **C1** vs **R1** | `separation >= 10 mm`. Two independent reasons: the tuning-tool access cone must clear the flange (I2/A6), and C1 is a -40..+70 C part sitting near a 120 C flange (`blocks.md` s8 OPEN-1). |

Edge constraints (also in `constraints.json.placement.edges`):

| Ref | Edge | pos | rot | Why |
|---|---|---|---|---|
| J1 | `top` | 0.375 | 0 | at rot 0 this footprint's barrel and courtyard run to -12 mm in Y, so rot 0 on the top edge puts the 8.6 mm barrel off-board where a cable can mate. pos 0.375 = x 9.0 mm on a 24 mm board. |
| R1 | `bottom` | 0.375 | 180 | tab enters from off-board; flange, element and both mounting holes are outside the outline. |

## 4. ERC expectations

- **Two nets, six footprints, zero power rails.** No `#PWR` flag beyond `GND`.
- `Device:R` and `Device:C_Variable` are passive on both pins; `Conn_Coaxial` is passive.
  No driver anywhere - the board has no active part, so P4 should expect ERC to want a
  `PWR_FLAG` on `GND` (and only on `GND`).
- No unconnected pins. No no-connects. No power-input pins.
- `decoupling.json` is legitimately **empty/absent** - there is no IC to decouple
  (`power_tree.md` s1).
