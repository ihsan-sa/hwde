# P3 Parts + Library digest - g0-sense (2026-08-27)

- part-sourcer (sonnet/high) -> parts/parts.json: 20 distinct parts covering
  26 electrical refdes. 12 Basic / 8 Extended, of which 7 bear a JLC setup fee
  (the DNP header is Extended-priced but never machine-placed). ~$4.42/board,
  ~$22.10 for the 5-board run. All stock re-verified live; worst case (MCU
  C724040, 8351 pcs) is 334x the 5x-build-qty floor.
- Four sourcing corrections applied on review, three of them fee removals:
  R3 620R Extended -> 680R Basic (620R is a genuine E24 Basic-catalog gap);
  user LED KT-0603G Extended -> KT-0805G, which IS Basic; R12 220R -> 100R
  (electrical, not cost: green Vf 2.6-3.1 V against 3.3 V gave 0.9 mA at the
  worst bin - 100R gives 2-7 mA); whole resistor BOM normalised to 0603.
- 3 datasheet-extractors (parallel) -> parts/C724040.json, C2909890.json,
  C6186.json, all `datasheet_extract --validate` exit 0. Notable: TSSOP-20
  pin 19 is ONE bonded pad carrying PA15 and PA14-BOOT0/SWCLK - transcribed
  as the datasheet names it rather than picking a function; AMS1117 has NO
  recommended land pattern (outline only), so that field was omitted rather
  than faked; SHT40 die pad is present but explicitly NOT to be soldered.
- librarian (sonnet/medium): 20/20 pulled, 85 pins retyped (ERC prerequisite),
  lib tables registered. fp_verify found ONE real defect and it mattered:
  the pulled SHT40 DFN-4 soldered the die pad, which would have defeated the
  whole thermal-isolation design. Deleted (copper+paste+mask), courtyard
  closed. Three more fixes: broken symbol->footprint link (audited all 20 -
  the only one); C3 tantalum had NO polarity marking at all - pin 1 = anode
  established twice (manufacturer PDF + live EasyEDA CAD data), silk "+" and
  bar added; J2 Qwiic pin-1 confirmed against JST's own eSH.pdf ("viewed from
  the connector mounting surface", No. 1 circuit leftmost) - no flip needed.
- fp_verify final: 3 passed / 0 failed / 2 accepted pad_size warnings.
- P3 coverage exit: 7 slots, 0 gap, 3 part slots covered, 4 blocks
  provisional. No P3 research needed (2 of the 6 per-run tasks still unspent).
- 2 decisions recorded: AMS1117 SOT-223 tab = VOUT (pulled symbol confirms
  pin 4 = VOUT); SHT4x 20 V/ms slew item CLOSED, not escalated (the limit is
  specified for in-operation supply changes, not the cold-start ramp).
