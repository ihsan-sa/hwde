# P4 Schematic - digest

- One flat sheet, 5 parts, 3 nets, 12/12 pins connected. The generator is the
  source; the .kicad_sch rebuilds byte-identical from a clean delete.
- **Gate erc: 0 errors / 0 warnings** (commit 55d7875). netlist_audit exit 0,
  one expected `power_no_consumers` on +3V3 (only consumer is off-board).
- `U1 {1:GND, 2:+3V3, 3:+5V, 4:+3V3}` - the TAB (pin 4) is on +3V3, read back
  from the netlist rather than from source.
- **The catch of the run**: the readability redraw briefly left the tab run
  unnamed. Pins 2 and 4 are one node INSIDE the package but two on the sheet,
  so it exported as Net-(C2-Pad1) with +3V3 holding only pin 2 - the netless-
  tab thermal failure, arriving through a COSMETIC edit. ERC said 0/0 (an
  unnamed 3-pin net is legal). Only `netlist_audit --compare` saw it.
- Reviewer (fresh context): 1 error, 5 warnings. The circuit itself was clean.
  ERROR = no +/GND or IN/OUT legend on J1/J2 (same part, identical arrows) ->
  deferred to P6 as a silk requirement. Fixed here: min_vias 12 -> 0 (a +3V3
  pour cannot stitch to a GND plane), real wires, text collisions.
  Accepted: C2's ESR margin -> settled at bring-up by ring count (<= 4).
- 3 library defects repaired idempotently by `kicad/gen/lib_fixups.py` (C2 pin
  angles, C1 non-polarized graphic, numeral pin names). MUST be re-run after
  any lib_pull refresh or they silently return.
