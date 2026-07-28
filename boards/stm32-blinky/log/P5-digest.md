# P5 digest (stm32-blinky)
board_init (inline, post-fix): 20 parts, 44 nets, 2L JLC2313_1.6, outline
FIXED 50x40 (requirements cap; margin 3), 0 mounting holes. Self-check PASS:
parity 0 (LCSC field-copy fix live), setup 0 (D2 lib silk repaired by
librarian; 11 cross-part refdes silk marked transient - placement's to fix),
46 unconnected expected. rules_gen: 2layer_1oz floors + 3 power width rules
(/VIN,+5V,+3V3 0.3A) + Power class; DRU beside board. Sidecars in place.
Script fixes this phase: parse_netlist fields + SetField/hide (parity bug),
samefile schematic skip, transient-silk partition. 28 tests green.
