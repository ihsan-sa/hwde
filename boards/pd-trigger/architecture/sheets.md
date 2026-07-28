# pd-trigger - sheet plan

*Amended A1 after the P3 datasheet extracts: `+3V3` and U2 are gone, `/VIND` and
`/VDD` are new, PG is unconnected. See `decisions.md` section A1.*

## One flat root sheet - `pd-trigger.kicad_sch`

| Sheet | File | Blocks | Interface nets (sheet pins) | pwr_base |
|---|---|---|---|---|
| root `pd-trigger` | `kicad/pd-trigger.kicad_sch` | B1-B6, all of them | **none** - there are no child sheets | **1** |

Justification (the plan allows a flat sheet if argued):

- 28 components in one functional chain. The usb-buck precedent split at 28
  components across three genuinely separable domains; this board has one.
- **Every net that crosses a block boundary is a rail or a two-part stub**
  (`VBUS`, `GND`, `/VIND`, `/VDD`, `/VAUX`). Power symbols are global and need no
  sheet pin, so hierarchy would add sheet pins carrying nothing while introducing
  `/[sheet]/NAME` prefixes into net names that `constraints.json` would track.
- The only multi-block signal is `/HV_OK`, inside the indication block's own
  fan-out.
- P4 parallelism is not worth buying here: one generator script, one ERC run,
  one netlist audit.

Consequence for P4: **all local labels become `/NAME`** (root-local), which is
what `constraints.json` assumes for `/VAUX`, `/VIND` and `/VDD`.

## 1. Canonical net names

These are contractual. `check_current` raises `CheckError` (exit 2) on a `power`
net that is absent from the board, so `VBUS`, `/VAUX`, `/VIND` and `/VDD` must
appear verbatim in the final netlist.

### Global rails - power symbols, bare names

| Net | Symbol | Driven by | PWR_FLAG? |
|---|---|---|---|
| `VBUS` | `power:VBUS` | J1 VBUS pins (passive) | **yes** |
| `GND` | `power:GND` | passive everywhere | **yes** |

**`+3V3` NO LONGER EXISTS.** The 3.3 V LDO was removed at amendment A1: CH224K's
VDD is an internally shunt-regulated node (3.24/3.30/3.36 V, 0-30 mA sink) that
an external regulator would fight. There is no logic rail on this board.

**`VOUT` does not exist either.** The board is a pass-through: the receptacle
VBUS pins, the TVS, the bulk caps, every tap and the screw terminal are **one
copper object**, named `VBUS` end to end. The interface research's separate
`VOUT` entry (which assumed a series PPTC that no longer exists) is deduplicated
INTO `VBUS`; do not emit two power entries for one net.

### Root-local nets - `/NAME`

| Net | Members | Note |
|---|---|---|
| `/VAUX` | F1 pin 2, J3 pin 1 | own net so `check_current` sizes the aux stub at 1 A, not 5 A |
| `/VIND` | R14 pin 2, R1, R2, R6, R8, R10, R12, R13 | housekeeping stub behind the 0 ohm link; `pdn: false`, width-only |
| `/VDD` | R2 pin 2, U1 pin 1 (VDD), C5, R3/R4/R5 | the shunt node. Needs a **PWR_FLAG** - U1 pin 1 is a power-input pin fed through a passive |
| `/CFG1` `/CFG2` `/CFG3` | U1 pins 9/2/3, R3/R4/R5, SW1 | 100 k pull-ups to **`/VDD`**, switch shorts to `GND` |
| `/VSENSE` | R1, U1 pin 8 | 10 k series is mandatory (13.5 V abs max pin on a 21 V rail) |
| `/CC1` `/CC2` | J1 A5 -> U1 pin 7, J1 B5 -> U1 pin 6 | straight through, **no crossover, no series R, no external Rd** |
| `/BC12_DIS` | U1 pin 4 (DP) + pin 5 (DM) tied together | PD-only operation - **one net, deliberately shorted** (see V12) |
| `/ZBIAS` | D2 anode, R6 pin 1 | window detector bias chain from `/VIND` |
| `/HV_B` | R6 pin 2, Q1A base, R7 | R7 4k7 to GND kills zener knee leakage |
| `/HV_OK` | Q1A collector, R8, D6 cathode, R9 | high above ~6.7 V on the bus = profile achieved |
| `/FB_B` | R9 pin 2, Q1B base | inverter drive |
| `/FB_K` | Q1B collector, D5 cathode | red "5V ONLY" leg |

LED anode nets (R10/R12/R13 to D3/D5/D6) are two-part local nets; leave them
auto-named. **U1 pin 10 (PG) is a no-connect** - see s3.

**`/BC12_DIS` naming is load-bearing.** `constraints.json` sets an explicit
`"diff_pairs": []`, which disables `check_diffpair` outright - but the net name
also deliberately avoids any `DP`/`DM`/`_P`/`_N`/`D+`/`D-` token so that even
auto-discovery could not construct a "pair" out of a node that is a single
deliberate short.

## 2. Refdes allocation (one namespace, one sheet)

| Block | Refs | Parts |
|---|---|---|
| B1 input + protection | J1, D1, C1, C2 | receptacle, TVS, 22 uF bulk, 100 nF |
| B2 controller + supply | U1, R1, **R2**, C5 | CH224K, 10 k sense, **1 k / 2512 dropper**, 1 uF on /VDD |
| B3 profile selector | SW1, R3, R4, R5 | DIP-3, 3 x **100 k** pull-up to /VDD |
| B4 housekeeping stub | **R14** | 0 ohm 0603 link, VBUS -> /VIND |
| B5 indication | D2, Q1, R6, R7, R8, R9, D3, D5, D6, R10, R12, R13 | zener, dual NPN, window network, 3 LEDs + legs |
| B6 output + aux | J2, F1, J3 | screw terminal, 1 A PPTC, aux header |
| power symbols | `#PWR01`+ / `#FLG01`+ | pwr_base = 1 |

**Refdes gaps are intentional: there is no U2, C3, C4, D4 or R11.** Those were
the LDO, its two capacitors, the PG LED and the PG LED's resistor, all removed at
amendment A1. Surviving parts keep their original designators so that P3's
in-flight sourcing does not have to be re-keyed - do **not** renumber to close
the gaps.

Assignments are reflected in `constraints.json` (`thermal` names J1;
`placement.edges` names J1, J2, J3, SW1; `groups` name Q1 and D3; `separation`
names R2 and U1). **`check_thermal` hard-errors (exit 2) on a refdes with no
pads**, so if P4 renumbers, `constraints.json` must be renumbered with it.

## 3. Wiring facts P4 must not re-derive from memory

All from `parts/C970725.json` (CH224 manual V2.1) unless noted:

1. **Pin 0 is the exposed baseplate AND the ground terminal**, and
   **KiCad/EasyEDA footprints usually number that pad 11**. Run
   `schlib.py --pins` against the actual symbol and check the footprint's pad
   numbering before wiring; a mis-numbered thermal pad leaves GND unconnected on
   a part whose only ground is that pad.
2. **No external 5.1 k Rd on CC1/CC2.** The CH224K reference schematic wires CC
   straight to the connector; the CH224D and CH221K schematics in the same manual
   *do* show 5.1 k. Rd is integrated on this part - fitting external pull-downs
   would put ~2.55 k on CC and shift the source's Rd/Ra detection.
3. **CC1 = A5 -> pin 7, CC2 = B5 -> pin 6, no crossover, no series elements** (a
   series R adds directly to Rd, whose budget is only +/-20 %).
4. **No caps on CC** without knowing U1's own pin capacitance (the PD spec's CC
   receiver window is 200-600 pF total, and 200 pF is a *minimum*).
5. **R2 (1 k) into pin 1 and R1 (10 k) into pin 8 are mandatory.** Pin 1 is a
   3.0-3.6 V shunt node; pin 8 is a 13.5 V-max detect input on a 21 V rail.
   Neither may be shorted to the bus, and neither may be "optimised" away.
6. **CFG straps: 100 k to `/VDD`, switch to GND.** CFG2/CFG3 have **no internal
   pull-ups** and are absolute-max VDD + 0.5 V - they must never see VBUS. 10 k
   would eat 58 % of the VDD budget at the 5 V profile.
7. **PG (pin 10) is left unconnected**, matching the datasheet's reference
   schematic. It needs an explicit **no-connect flag** with the justification
   comment: *"open-drain, no absolute-maximum rating published for CH224K - may
   not be pulled to VBUS/VIND; a VDD-referenced pull-up would spend the 1.7 mA
   VDD budget. Indication is handled by the D5/D6 window (blocks.md B5)."*
8. **DP (pin 4) and DM (pin 5) shorted together at the chip, off the connector**
   (`/BC12_DIS`); the receptacle's A6/A7/B6/B7 stay unconnected. See **V12** -
   the extract reads the reference schematic as wiring DP/DM to the connector,
   while the interface research cites a PD-only-mode instruction to short them.
   Resolve before wiring; do not leave them floating either way.
9. **J1 shell tied directly to GND** (bench tool, no chassis - no 1 M / 4.7 nF
   hybrid tie).
10. **All four VBUS pins and all four GND pins of J1 in the netlist** - the 5 A
    rating is collective across them, and `netlist_audit` is the check that they
    were not partially wired.
11. Every unconnected receptacle pin (SBU1/2, DP/DM, any SuperSpeed pads) gets an
    explicit no-connect flag with a one-line justification.

## 4. Decoupling metadata P8 depends on

`check_pdn` reads `decoupling.json` associations and errors on a **declared power
rail with no associated cap at all**. Two declared nets carry `pdn` true:

| Net | Cap that must be associated | Value |
|---|---|---|
| `VBUS` | C1 (bulk) and C2 | 22 uF, 100 nF |
| `/VDD` | **C5**, associated to **U1 pin 1** | 1 uF |

C5 is the datasheet's only specified capacitor for this part ("VDD: external
1 uF capacitor to GND, series resistor to VBUS"), and declaring `/VDD` in
`power[]` is what makes `check_pdn` enforce it. Pass `rail_net="/VDD"` to
`place_ic_with_decoupling` so the metadata records the final net name rather than
a wiring label.

`/VAUX` and `/VIND` both carry `"pdn": false` and are skipped by the inventory:
nothing decouples a fused stub to a header, or a resistor-fed indicator stub, by
design.
