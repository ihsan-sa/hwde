# P4 Schematic - digest (2026-08-16)

- ONE schematic agent, one flat root sheet (recorded). `kicad/gen/root.py` is
  the source; the .kicad_sch is build output.
- Gate **erc PASS** 0/0, attempt 2, commits 42f46c3 then 94d7a24.
  netlist_audit exit 0: 19 nets, 10 components, 44/44 pins, 4 decouplers.
- The generator caught its own defect by RENDERING: J1's two labels
  overprinted, exporting as +3VGNID - on the connector whose silk polarity is
  the only defence against a swapped supply. Fixed, proven netlist-neutral.
- Adversarial review, fresh context: **0 errors / 3 warnings**, and it CLOSED
  the run's biggest open item - BOOT0=0 selects Main Flash, R1 is correct.
- W1 actioned, REVERSING my P1 ruling: C5 100 nF added on NRST. My reason had
  misread AN4325; the datasheet's Fig 21 note 1 recommends it unconditionally
  for parasitic reset, and this board flies NRST on a lead.
- W3 actioned: J3 -> IO1/IO2/IO3/IO4/GND. J2 and J3 are the SAME unkeyed part,
  so the GPIO cable fits the debug header; centre-GND vs centre-3V3 shorted
  the rail. W2 held: rail-at-an-end is worse under a one-position slip.
- Then caught a P6 landmine: C5 had no placement.sides entry and is SMT, so
  the annealer could have flipped it to the back. Added (7 now) + into the
  mcu group; both constraints.json copies re-synced, lint 0.
