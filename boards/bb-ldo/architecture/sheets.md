# bb-ldo - hierarchical sheet plan (P2)

## One flat sheet. There is no hierarchy on this board.

Six parts (one contingent), three nets, no signal net, no repeated block.
A hierarchical split would add sheet pins and a stitching root to a schematic
that fits in one screen. **P4 runs a SINGLE schematic agent on the root sheet;
there are no child sheets to parallelise.**

| sheet | file | blocks | parts |
|---|---|---|---|
| `main` (root) | `kicad/gen/main.py` -> `kicad/bb-ldo.kicad_sch` | B1 input interface, B2 linear regulator, B3 output interface | J1, C1, U1, C2, J2 |

## Refdes ranges

Refs must be unique across sheets; with one sheet the whole space is `main`'s,
but the ranges are stated so a later sheet (if this board ever grows) cannot
collide.

| class | range | assigned |
|---|---|---|
| U | U1-U9 | **U1** = the linear regulator |
| C | C1-C9 | **C1** = 10 uF tantalum Cin, **C2** = 22 uF solid tantalum Cout |
| R | R1-R9 | *(none fitted - the min-load bleed was RESOLVED OUT at P2; see below)* |
| J | J1-J9 | **J1** = DC input screw terminal, **J2** = 3V3 output screw terminal |
| #PWR | **pwr_base = 100** (#PWR100-#PWR199) | power symbols |

**These specific refdes are NOT free choices for P4.** `constraints.json`
already keys on them: `thermal[0].ref = U1`, `placement.edges` on J1/J2,
`placement.groups.reg` = U1 + C1 + C2, `placement.sides` on all five certain
parts. A different assignment silently unhooks the thermal and placement
constraints.

## Nets - canonical names, fixed here

| net | name in the netlist | notes |
|---|---|---|
| input rail | `+5V` | global power symbol, bare name (no leading `/`) |
| output rail | `+3V3` | global power symbol; this is ALSO the tab/heatsink net |
| return | `GND` | global power symbol |

All three are global power symbols, so **no hierarchical pins and no local
labels exist on this board** - nothing acquires a `/sheet/` prefix. These names
are what `constraints.json` (power, thermal, planes) already declares, and
`netlist_audit` compares the two: any rename breaks every gate at once.

ERC hint: the `+5V` and `GND` nets are driven only by J1's passive connector
pins, so both need a PWR_FLAG (schlib `power_flag`) or ERC reports an
undriven power net.

## What each block contributes to the sheet

- **B1** - J1: `+5V`, `GND`. Nothing else; no protection element sits behind it
  (scope tier).
- **B2** - U1 with C1 at its input pin and C2 at its output pin. **No R1**: the
  minimum-load bleed was resolved OUT at P2 on verified, page-cited research -
  the 1117 family's minimum-load spec belongs to the ADJUSTABLE variant, whose
  EXTERNAL divider draws it, while a fixed 3.3 V part's divider is internal and
  Kelvin-connected (AMS p1/p2/p6, LM1117 p6; second-reader verified). The board
  carries five parts. **Pin numbers come from the P3 datasheet
  extraction (`parts/<code>.json`), never from this document or from memory**;
  what P2 fixes is the topology: Cin between `+5V` and `GND` at the VIN pin,
  Cout between `+3V3` and `GND` at the VOUT pin, ground pin to `GND`, and the
  SOT-223 tab on `+3V3` (it is internally VOUT - the footprint's tab pad must
  be on the output net, not GND, and not left unconnected).
  There is **no enable pin and no feedback divider** on the fixed variant; if
  P3's final part turns out to have an EN pin, it is tied to its always-on
  state as a datasheet-required connection (still in scope at `block-only`),
  not brought out as a strap.
- **B3** - J2: `+3V3`, `GND`.

## decoupling.json (emitted by the generator)

C1 and C2 are associated with U1's input and output pins. **Do NOT tag either
with `"role": "reg_input"`** - that role exists for a SWITCHING regulator's VIN
and makes `check_decoupling` demand an HF ceramic within 7.5 mm. This block has
no switch node, and `blocks.md` s.3 records why no 0.1 uF ceramic is fitted.
Both rails carry a >= 1 uF bulk cap, so `check_pdn` has no bulk warning to
raise.

## Placement groups this plan implies (P6)

`reg` = U1 (anchor) + C1 + C2, already declared in
`constraints.json["placement"]["groups"]`. J1 and J2 are edge-pinned to
opposite edges. All five certain parts are side-pinned to `front`
(single-sided SMT assembly; the F.Cu pour is the heatsink).
