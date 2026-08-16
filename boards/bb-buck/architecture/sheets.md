# sheets.md - bb-buck schematic sheet plan, refdes ranges, CANONICAL net names

## 1. Sheet plan: ONE FLAT ROOT SHEET

| Sheet | File | Blocks it carries | Interface nets at its boundary | Refdes ranges | `pwr_base` |
|---|---|---|---|---|---|
| root (only) | `kicad/bb-buck.kicad_sch` | B1 buck converter, J1 input, J2 output, TP1/TP2 probe, H1-H4 mounting | none - the board's only interfaces are the two physical terminals (`+VIN`/`GND` at J1, `+5V`/`GND` at J2) | `U1-U9`, `L1-L9`, `C1-C19`, `R1-R9`, `J1-J9`, `TP1-TP9`, `H1-H9` | **1** (`#PWR01..`, `#FLG01..`) |

**A hierarchical split is deliberately REJECTED on this board.** Hierarchy
exists to keep large schematics readable and to give each sheet its own
refdes/#PWR range; this board has 14 electrical parts and 6 nets on one A4
page. The cost of splitting is concrete and has been paid before: a label
inside a child sheet exports as `/<sheet>/<LABEL>`, which silently unhooks
every `constraints.json` entry that spells it `/<LABEL>` (the P4 amendment
class that cost `lumina-par`, and the reason `sbuck-5v3a` also went flat).
With one root sheet there are no sheet prefixes anywhere, by construction.

Refdes ranges are therefore trivially unique. They are stated anyway because
the rule is "unique ACROSS sheets": **if a later amendment ever splits this
sheet, the child sheets take `pwr_base = 40` and `80` and keep the prefix
ranges above**, and every net name in s2 must be re-checked against the new
export.

## 2. CANONICAL NET NAMES - these are now binding

`research/power.json` proposed `VIN / SW / +5V / GND`. **P2 makes them
canonical here, and two of the four change spelling.** These are the names
the schematic MUST produce and the names `constraints.json` uses.

| Canonical net | KiCad mechanism | Spans | Declared in constraints.json as |
|---|---|---|---|
| **`+VIN`** | power symbol (VALUE = net name) -> exports BARE | J1.1 -> C1/C2/C3 -> U1 VIN pin | `power` 1.1 A, `voltages` 30 V |
| **`GND`** | power symbol -> exports BARE | everything; B.Cu pour | `power` 2.6 A `plane_fed`, `planes` F.Cu + B.Cu, `thermal` heatsink net |
| **`+5V`** | power symbol -> exports BARE | L1 -> C4/C5 -> R1 -> J2.1 | `power` 2.6 A |
| **`/SW`** | root-sheet LOCAL LABEL -> exports with ONE leading slash | U1 SW pin -> L1 -> TP1 | `power` 2.6 A `pdn:false`, `high_speed`, `voltages` 30 V |
| **`/FB`** | root-sheet local label | R1/R2 midpoint -> U1 FB pin | **deliberately NOT declared** (see s4) |
| **`/BST`** | root-sheet local label | U1 BOOT pin -> C6 -> `/SW` | **deliberately NOT declared** (see s4) |

Why `+VIN` and not `VIN`: it is a rail feeding a power pin and decoupled by
the input bank, so it is a power symbol, and a power symbol's exported name
is bare. Why `/SW` and not `SW`: it is a root-sheet local label, and KiCad
prefixes those with a slash on export. **A power symbol WINS over a
coincident label**, so P4 must not mix the two mechanisms on one node.

**Enforcement, not hope:** at P4 run
`netlist_audit.py --net kicad/bb-buck.net --constraints architecture/constraints.json`.
A net spelled differently in the schematic surfaces as `missing_net` (error).
Without that run, a misspelling is silent: `check_current` finds no copper on
a net that does not exist and reports nothing.

## 3. Contents of the root sheet

| Refdes | Part | Net attachments |
|---|---|---|
| `U1` | 36 V-class synchronous integrated-FET buck, 3 A-class, exposed pad, 400 kHz, internally compensated | VIN=`+VIN`, GND/PGND/EP=`GND`, SW=`/SW`, BOOT=`/BST`, FB=`/FB`, EN per datasheet (see below) |
| `C1` | 100 nF 50 V X7R - HF input bypass, **`role: reg_input`** | `+VIN` / `GND` |
| `C2` `C3` | 10 uF 1210 50 V X7R - input bank | `+VIN` / `GND` |
| `C6` | 100 nF - bootstrap (value/rating per datasheet) | `/BST` / `/SW` |
| `L1` | 15 uH shielded/composite, <= 40 mOhm, Isat >= ~6.6 A | `/SW` / `+5V` |
| `C4` `C5` | 22 uF 1206 25 V X7R - output bank | `+5V` / `GND` |
| `R1` `R2` | FB divider, 0.1 % / 25 ppm (`R1` = top, `+5V`->`/FB`; `R2` = bottom, `/FB`->`GND`) | as listed |
| `J1` | 2-pole 5.08 mm screw terminal, THT | 1=`+VIN`, 2=`GND` |
| `J2` | same part as J1 | 1=`+5V`, 2=`GND` |
| `TP1` | SW probe pad (A4) - INSIDE the SW copper, not on a spur | `/SW` |
| `TP2` | GND probe pad, adjacent to TP1 | `GND` |
| `H1`-`H4` | M3 clearance holes, 3.2 mm | mechanical (no net) |

**EN: read the part's own behaviour before adding anything.** Most parts in
this class auto-start from an internal pull-up, so EN ties to `+VIN` or
floats and NO parts are added. No UVLO divider - mode-excluded, and a bench
supply has no cable-droop motorboating case (0.62 A over 2 m of lead is
~0.1 V). No soft-start components: internal soft-start makes Cout inrush
`C x Vout/tss` ~ 65 mA, and A2 means the supply ramps from zero anyway.

If the FB pin has no divider because P3 found a FIXED 5 V part, `R1`/`R2` and
`/FB` disappear and the sense point ties straight to the output - **that is
the preferred outcome and it removes the whole s5 tolerance budget**, but do
not synthesise it from an adjustable part's datasheet figure.

## 4. Two nets deliberately left OUT of `constraints.json`

`/FB` and `/BST` are declared nowhere. This is intentional:

- `rules_gen` buckets every `power` entry into a netclass **at that net's own
  IPC-2152 width** (this used to flatten every power net to the widest width;
  the current script buckets per net - verified in `rules_gen.net_classes`).
  Even so, a `power` entry on `/FB` would give the feedback node a
  minimum-width rule and pull it into the `check_pdn` decoupling inventory,
  and `/FB` is a high-impedance sense node that wants to be SHORT and THIN
  and nowhere near `/SW`.
- `/BST` carries only gate charge. Nothing to size, nothing to decouple.

The two rules that DO apply to them are layout rules, carried in s5 below and
in `constraints.json` `placement.groups` / `separation`, not width rules.

## 5. Placement groups this sheet implies (they become P6 groups)

- **`hotloop`** (anchor `U1`; `C1`, `C2`, `C3`, `C6`): C1 nearest the VIN
  pin, then the bulk ceramics, then U1 VIN -> U1 PGND, on F.Cu, **smallest
  enclosed area achievable**. This is the loop that spends ~37 mV of the
  50 mV ripple budget. It must be placed by explicit `place_edit` and LOCKED
  before `place_anneal` runs - an annealer optimises a cost function and
  cannot discover a hot loop.
- **`output`** (anchor `L1`; `C4`, `C5`): Cout ground and Cin ground return
  to the GND pour at SEPARATE points near their own pins - never a shared
  narrow neck (`buck-cin-co-ground-separation`).
- **`feedback`** (anchor `R1`; `R2`): at the FB pin, sense point AFTER the
  output caps, >= 5 mm from L1 and off the `/SW` side of the package.
- **`probe`** (anchor `TP1`; `TP2`): TP1 inside the existing `/SW` pour;
  TP2's ground returns straight down to the B.Cu pour beneath it.

`/SW` itself: a short WIDE pour, 1.6-2.0 mm wide, <= 8 mm long, <= 40 mm^2
total, F.Cu only, never near a board edge or a screw terminal. IPC-2152
constrains the WIDTH (a floor); EMI constrains the AREA (a ceiling that
nothing in the toolchain enforces). TP1's pad counts against that 40 mm^2.
