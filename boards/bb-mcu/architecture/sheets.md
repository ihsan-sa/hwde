# sheets.md - bb-mcu sheet plan, refdes ranges, CANONICAL net names

## 1. Sheet plan: ONE FLAT ROOT SHEET

| Sheet | File | Blocks it carries | Interface nets at its boundary | Refdes ranges | `pwr_base` |
|---|---|---|---|---|---|
| root (only) | `kicad/bb-mcu.kicad_sch` | B1 MCU minimum system, B2 SWD debug port, J1 power in, J3 GPIO out, H1-H4 mounting | none - the board's only interfaces are the three physical connectors | `U1-U9`, `C1-C19`, `R1-R9`, `J1-J9`, `H1-H9` | **1** (`#PWR01..`, `#FLG01..`) |

**A hierarchy is REJECTED, explicitly and with the argument stated**, because
the role prompt invites disagreement and there is none to have here.

This board has **nine electrical parts and ten nets** on one A4 page.
Hierarchy exists to keep large schematics readable and to give each sheet its
own refdes and `#PWR` range; neither problem exists at this size. The cost of
splitting is concrete and this repo has already paid it: a label inside a child
sheet exports as `/<sheet>/<LABEL>`, which silently unhooks every
`constraints.json` entry that spells it `/<LABEL>` - the P4 amendment class
that cost `lumina-par`, and the reason `sbuck-5v3a` and `bb-buck` both went
flat. With one root sheet there are no sheet prefixes anywhere, by
construction.

Refdes ranges are therefore trivially unique. They are stated anyway because
the rule is "unique ACROSS sheets": **if a later amendment ever splits this
sheet, the child sheets take `pwr_base = 40` and `80` and keep the prefix
ranges above**, and every net name in s2 must be re-checked against the new
export.

Mounting holes are reserved `H1-H4`. **Whether four or two are fitted is a P6
call**, not a P2 one: `requirements.md` s5 asks for four M3 clearance holes
inset from the corners and sanctions two on opposite corners if the earned
outline cannot hold four. Under `canonical` binding the outline is not known
here, so the count is settled when it is known and the choice is recorded.

## 2. CANONICAL NET NAMES - binding from here

`research/interface-swd.json` proposed `SWDIO / SWCLK / NRST / +3V3 / GND` as
"proposals in the standard's conventional form" and handed reconciliation to
P2. **These are now the names the schematic MUST produce**, and they are the
names `constraints.json` uses.

| Canonical net | KiCad mechanism | Spans | In `constraints.json` |
|---|---|---|---|
| **`+3V3`** | power symbol (VALUE = net name) -> exports BARE | J1.1 -> C1 C2 C3 C4 -> U1 VDD(16) + VDDA(5) -> J2.3 | `power` 0.1 A |
| **`GND`** | power symbol -> exports BARE | everything; B.Cu pour | **not declared** - see `power_tree.md` s7 |
| **`/SWDIO`** | root-sheet LOCAL LABEL -> exports with ONE leading slash | U1 pin 19 (PA13) -> J2.4 | not declared (advisory only, `notes`) |
| **`/SWCLK`** | root-sheet local label | U1 pin 20 (PA14) -> J2.2 | not declared (advisory only, `notes`) |
| **`/NRST`** | root-sheet local label | U1 pin 4 -> J2.5 | not declared |
| **`/BOOT0`** | root-sheet local label | U1 pin 1 -> R1 | not declared |
| **`/IO1`** | root-sheet local label | U1 pin 6 (PA0) -> J3.1 | not declared |
| **`/IO2`** | root-sheet local label | U1 pin 7 (PA1) -> J3.2 | not declared |
| **`/IO3`** | root-sheet local label | U1 pin 8 (PA2) -> J3.4 | not declared |
| **`/IO4`** | root-sheet local label | U1 pin 9 (PA3) -> J3.5 | not declared |

Why `+3V3` and not `3V3`: it is a rail feeding supply pins and decoupled by
C1-C4, so it is drawn with a power symbol, and a power symbol's exported name
is bare. Why `/IO1` and not `IO1`: root-sheet local labels are prefixed with
one slash on export. **A power symbol WINS over a coincident label**, so P4
must not mix the two mechanisms on one node.

**Silk drops the slash.** The header silk reads `IO1 IO2 GND IO3 IO4` and
`GND SWCLK 3V3 SWDIO NRST` - the slash is a netlist artifact, not a label a
bench user should ever see. Naming note from the research: ST never calls the
sense pin "VTREF" on its own connectors (it is `T_VCC` or `VDD_TARGET`), so
the silk says `3V3`.

**Enforcement, not hope:** at P4 run
`netlist_audit.py --net kicad/bb-mcu.net --constraints architecture/constraints.json`.
A net spelled differently in the schematic surfaces as `missing_net` (error).
Without that run a misspelling is silent - `check_current` finds no copper on a
net that does not exist and reports nothing.

## 3. Contents of the root sheet

### U1 - STM32F030F4P6TR, TSSOP-20 - complete pin map

| Pin | Name | Net | Note |
|---|---|---|---|
| 1 | BOOT0 | `/BOOT0` | -> R1 -> `GND`. Dedicated pin, NO internal pull, hardware-sampled on the 4th SYSCLK edge after reset |
| 2 | PF0-OSC_IN | - | unused, left floating (no crystal; tie-offs are RECOMMENDED only and mode-excluded) |
| 3 | PF1-OSC_OUT | - | unused, left floating |
| 4 | NRST | `/NRST` | -> J2.5. Permanent internal pull-up 25/40/55 k; NOTHING added |
| 5 | VDDA | `+3V3` | tied to VDD by a BARE TRACE; C3 10 nF + C4 1 uF to `GND` |
| 6 | PA0 | `/IO1` | -> J3.1 |
| 7 | PA1 | `/IO2` | -> J3.2 |
| 8 | PA2 | `/IO3` | -> J3.4 |
| 9 | PA3 | `/IO4` | -> J3.5 |
| 10 | PA4 | - | unused |
| 11 | PA5 | - | unused |
| 12 | PA6 | - | unused |
| 13 | PA7 | - | unused |
| 14 | PB1 | - | unused |
| 15 | VSS | `GND` | the only ground pin; also the VDDA return (no VSSA on this package) |
| 16 | VDD | `+3V3` | C1 100 nF + C2 4.7 uF |
| 17 | PA9 | - | unused |
| 18 | PA10 | - | unused |
| 19 | PA13 | `/SWDIO` | -> J2.4. Dedicated SWD after reset, internal PULL-UP active |
| 20 | PA14 | `/SWCLK` | -> J2.2. Dedicated SWD after reset, internal PULL-DOWN active |

Nine pins are deliberately unconnected. **PA13/PA14 must NOT also be routed to
J3** - they can be released to GPIO in software, but J2 needs them as SWD
permanently and routing them to both headers is a pin conflict.

### The rest of the board

| Refdes | Part | Net attachments |
|---|---|---|
| `C1` | 100 nF X7R ceramic | `+3V3` / `GND`, at U1 pins 16/15 |
| `C2` | 4.7 uF X7R ceramic | `+3V3` / `GND`, bulk on the VDD net |
| `C3` | 10 nF X7R ceramic | `+3V3` / `GND`, at U1 pin 5 |
| `C4` | 1 uF X7R ceramic | `+3V3` / `GND`, at U1 pin 5 |
| `R1` | 10 k (5 % is fine) | `/BOOT0` -> `GND` |
| `J1` | 2-pole 5.08 mm screw terminal, THT | 1 = `+3V3`, 2 = `GND`. Silk `+` / `-` |
| `J2` | 1x5 0.1 in header, single row, straight, THT | 1 `GND`, 2 `/SWCLK`, 3 `+3V3`, 4 `/SWDIO`, 5 `/NRST` |
| `J3` | 1x5 0.1 in header, single row, straight, THT | 1 `/IO1`, 2 `/IO2`, 3 `GND`, 4 `/IO3`, 5 `/IO4` |
| `H1`-`H4` | M3 clearance holes, 3.2 mm | mechanical, no net (count settled at P6) |

**Voltage ratings**: everything sits on a 3.3 V rail, so 16 V or 25 V X7R
ceramics are ample and DC-bias derating is a non-issue at 3.3 V on parts rated
5-8x that. P3 picks the exact parts; nothing here constrains them beyond value,
dielectric and a package the JLC PCBA line places on the top side.

### J2 pin order - RULED at P1, do not re-order

`GND / SWCLK / 3V3 / SWDIO / NRST`, positions 1..5. The reasoning is in
`blocks.md` s2 and in `state.json`; the one-line version is that on an unkeyed
5-way shell a 180-degree reversal maps position `i` to `6-i`, so **3V3 at the
centre is the unique arrangement in which a reversed probe lands its high-Z
VTref INPUT on the board's rail rather than a probe OUTPUT.** This is
deliberately NOT a vendor cable order - flying-lead probes present individually
labelled wires, so per-pin silk is what the user reads either way.

### J3 pin order - RULED HERE at P2

`IO1 / IO2 / GND / IO3 / IO4`, positions 1..5. The owner fixed the SET (four
GPIO plus a ground, because a signal with no return is not usable at the
bench); the ORDER was open. Ground goes in the CENTRE, for three reasons:

1. **Return distance.** With GND at an end, `IO4` is four positions from its
   return; at the centre no signal is more than two positions away. On a bench
   header the ground lead IS the return path, and SEGGER's own note is that
   "long ground leads can significantly worsen ringing and distortion". This is
   the real reason.
2. **The same reversal mechanism that decided J2.** Five positions, unkeyed,
   `i -> 6-i`; a centre GND maps to itself, so a reversed plug still lands
   ground on ground. Nothing destructive can happen on J3 either way (there is
   no rail on this header), but a user clipping a ground lead and getting a
   driven GPIO is a real bench annoyance that costs nothing to prevent.
3. **Consistency**: both headers on this board answer "where does ground go?"
   the same way, which is the kind of thing a study article should teach once
   rather than twice differently.

## 4. Constraint keys deliberately ABSENT - read before "fixing" them

| Key | Status | Why |
|---|---|---|
| `diff_pairs` | **OMITTED entirely** - NOT `[]` | P1 ruling. An explicit empty list DISABLES `check_diffpair` board-wide; omitting the key leaves auto-discovery ARMED. Both are no-ops on a board with no pair, so take the fail-safe one - disabling a check board-wide to say "we have none" is how a silent blind spot gets built in for the next edit. None of this board's net names matches the auto-discovery suffixes (`_P`/`_N`, `DP`/`DM`, `D+`/`D-`), so nothing is discovered by accident. This DIVERGES from `research/interface-swd.json`, which emitted `[]`, and from `stm32-blinky`, which shipped `[]`. |
| `high_speed` | absent | SWD binds nothing (`blocks.md` s3). Declaring these nets on 2 layers would only manufacture `corridor_void` findings that are unfixable by construction. The `<= 50 mm` / over-the-pour / keep-SWCLK-clear guidance lives in `notes` as ADVISORY. |
| `voltages` | absent | Nothing on the board exceeds 3.3 V. `check_creepage`'s derived check engages only ABOVE 30 V, so entries at 3.3 V would be dead weight, not forward-compatibility. `requirements.md` s8: the >30 V flag DOES NOT APPLY. |
| `voltage_pairs` | absent | No bridge, no AC tap, no net pair with a differential the node voltages cannot express. |
| `thermal` | absent | 0.33 W at the budget ceiling, no exposed pad, no via array (`power_tree.md` s4). |
| `planes` | absent | The 2-layer default (B.Cu GND pour) is exactly right, and a `planes[]` list REPLACES the defaults entirely (`stackup.md` s4). |
| `power` entry for `GND` | absent | Would manufacture a `check_pdn` `pdn_undecoupled` error requiring a waiver, and buy nothing at 0.1 A (`power_tree.md` s7). |
| `placement.keepouts` | absent | Keepouts are BOARD-LOCAL coordinates and this board has no outline yet by design. The mounting-hole washer keepouts get their rects at P6, once the outline is earned. |
| `placement.separation` | absent | Centre-to-centre, and SKIPPED when either ref is locked - it cannot express anything this board needs. Nothing here needs parts held apart. |
| `placement.fixed` | absent | Nothing has an earned position at P2. Locking refs is a P6 act, after explicit `place_edit`. |

## 5. Placement groups this sheet implies

One group, `mcu`: anchor `U1`, members `C1 C2 C3 C4 R1`.

- **C1 (100 nF) closest to pins 16/15**, then C2 (4.7 uF) as the reservoir
  behind it; **C3 (10 nF) closest to pin 5**, then C4 (1 uF). Each cap's ground
  drops straight to the B.Cu pour through its own via, with the supply via and
  the ground via straddling the cap right at the pin (AN4325 Fig 8). The
  datasheet's word is "must": "as close as possible to, or below, the
  appropriate pins".
- **R1 in the pin-1 window** - the BOOT0 node is hardware-sampled before any
  software runs and there is no reason for it to be long.
- **The one congestion point**: C3/C4 sit at VDDA (pin 5) on the same package
  face the four GPIO escape past. Place them toward the pin-1 end of pin 5's
  escape so the far half of that face stays clear (`blocks.md` s4).

Connector edges are in `constraints.json` `placement.edges`: J1 on its own
edge, J2 and J3 on two others, which is `requirements.md` s5's requirement that
power not share an edge with the two signal headers. **Every connector's
opening or mating face must point OFF-BOARD** - a requirement in words, because
no schema key expresses it, and `rot` is deliberately left unset since the
footprints' native entry directions do not exist yet (`bb-buck` recorded the
cost of guessing them).

Orientation guidance for P6, not a constraint: put U1's **pin-1 end toward
J2's edge**, so `/SWDIO`, `/SWCLK` and `/NRST` all escape from the same
package end, and the four GPIO escape from the diagonally opposite region
toward J3.
