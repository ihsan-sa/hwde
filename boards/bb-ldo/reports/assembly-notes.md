# bb-ldo - assembly notes

Build: JLCPCB PCBA, **single-sided SMT** (U1, C1, C2 on F.Cu), qty 5.

## Hand-install after PCBA

J1 and J2 (WJ500V-5.08-2P, C8465) are THROUGH-HOLE screw terminals. JLC
economy assembly is SMT-only, so both are hand-soldered after the board comes
back. They are classed `hand_install` in parts.json and therefore appear in
BOM-full.csv only - never in the assembler's BOM.csv/CPL.csv.

**J2 pin 1 (+3V3) needs preheat.** That pin is solid-connected to the ~1196
mm2 F.Cu +3V3 thermal pour, which is the regulator's heatsink and is
deliberately NOT thermally relieved (relief is correct for a hand-soldered pin
but the pipeline has no scripted way to set a per-pad zone connection - see
state.json, P8). Consequence at the bench:

- Preheat the board (100-120 C hotplate or preheater) before soldering J2.
- Use a high-thermal-mass tip and >= 60 W; a fine conical tip will not do it.
- Expect a longer dwell on J2.1 than on any other joint. Inspect it: a cold
  joint here is the most likely assembly defect on this board.
- J1's pins sit on +5V and GND, not on the pour, and solder normally.

## Polarity - check before power-up

- **C1 and C2 are solid tantalums.** Reversed, a tantalum fails SHORT and can
  burn. Both footprints print a `+` on pin 1; C2's own case marks are hidden
  under its body, so the silk `+` is the only visible cue.
- Board silk legends the terminals: J1 `+5V` / `GND` / `IN`, J2 `+3V3` /
  `GND` / `OUT`.

## Bench hazard

The board carries a **`HOT SURFACE`** legend for a reason: U1 dissipates 1.0 W
continuous with no heatsink but the board's own copper. At the design point
(5.25 V in, 500 mA out, 50 C ambient, still air) the tab copper runs near
95 C and the top pour 65-80 C - there is no cool place to hold it. There is
NO reverse-polarity or over-voltage protection by scope ruling: wiring 5 V
backwards into J1 destroys the board and reverse-biases C1.

## First-article checks

1. **Load-transient ring count on C2** (<= 4 rings) - this settles the one
   open electrical question. C2's ESR is inside the regulator's feedback loop
   and its 800 mohm figure came from an LCSC parametric field, not a page of
   Vishay's datasheet. See state.json, P3/P4.
2. **Tab temperature at full load** - the thermal margin (Tj ~110-115 C
   against a 125 C limit) rests on vendor copper-area tables, not on a
   measurement. A thermocouple on the tab at 500 mA settles it.
3. Inspect the three GND stitch vias near C1/C2/U1 for solder wicking; they
   were relocated clear of the pads at P8 precisely to prevent it.
