# key decisions - g0-sense P2 (for the orchestrator to log)

Orchestrator inputs (already-taken decisions 1-11) were designed to, not
re-litigated; none was found technically wrong. Decisions below are the
architecture calls this phase made, each with a one-line why, plus
rejections.

## Taken

1. Stackup `JLC2313_1.6`, 2 layers, 1 oz, HASL - no impedance control, no
   planes beyond one GND pour, low density; fewest layers the blocks
   honestly need; 2 oz buys nothing at a 1.5 A fault sizing.
2. Board size stays an OUTPUT: layout needs ~800-1000 mm^2 (USB-C swath,
   sensor island + slot + 8 mm separation, ~600-1000 mm^2 LDO pour, edge
   access); the soft 35 x 25 target is plausibly earned, ~40 x 28 is the
   honest ceiling if M2 corners + slot refuse to coexist - P6 decides,
   relaxation recorded then, not now.
3. LDO = AMS1117-3.3 SOT-223 (orchestrator input) with C3 = 22 uF
   TANTALUM-CLASS output cap and a 600-1000 mm^2 TOP +3V3 tab pour;
   governing point 0.51 W rated case - only candidate with thermal margin
   there, degrades gracefully at Qwiic-abuse 0.83 W.
4. TVS lead = SMF5.0A (SOD-123) over research rank-1 SMAJ5.0A: identical
   5V/6.4V/9.2V electricals, 200 W is ample for an indoor USB port, and the
   smaller footprint serves the tight power corridor; SMA is the drop-in
   alternate if area allows.
5. PTC lead = BSMD0805-075-16V class over research rank-1 1206 twin: same
   750 mA/16 V, lower Ri (70 vs 90 mOhm) preserves LDO dropout margin,
   smaller, deeper stock.
6. Cap topology vs the Type-C 10 uF attach limit (from research/power.md,
   now binding): 100 nF ONLY ahead of the PTC at the connector; 10 uF X5R
   after the PTC at U1 VIN; 22 uF tantalum behind the LDO on +3V3.
7. I2C pull-ups 2.2 kOhm x2, once, at the MCU (host) end: sized for the
   ~0.5 m Qwiic leg + one downstream device; the SHT4x datasheet's 10 k
   typical LOSES (no cable budget - fails Fast-mode rise time loaded).
8. Pin map made canonical, unchanged from research/refdesign-stm32g030:
   SWD PA13/PA14 (18/19), USART2 PA2/PA3 (9/10), I2C1 PA9/PA10 (16/17),
   user LED PA5 (12) - re-checked against the fragment's DS12991 Table 12
   transcription, zero conflicts; PA9/PA10 are FT_f (5 V-tolerant, Fm+).
9. BOOT0: NO strap - factory option bytes boot main flash and ignore the
   pin, which shares pin 19 with SWCLK; UART-bootloader entry stays a pure
   option-byte rewrite over SWD (headers already on the bootloader's own
   USART2 pins).
10. NRST button = 5.1 x 5.1 mm JLC Basic class (orchestrator preference
    CONFIRMED on placement grounds: it sits mid-board by the MCU where
    5.1 mm costs nothing) - not overruled.
11. Power LED red on +3V3 (not VBUS): indicates the rail the logic runs
    on; red Vf 1.8-2.4 V leaves real resistor headroom at 3.3 V (R3 620R,
    1.5-2.4 mA). User LED green (input) R12 220R -> 0.9-3.2 mA over the
    Vf bin spread; accepted for an indicator, flagged to P3.
12. Qwiic connector lead = genuine JST SM04B-SRSS-TB class over 5x-cheaper
    clones: exact KiCad footprint ships in the library and the delta is
    ~$0.85 across the whole 5-board run; P3 may swap with a dimension check.
13. Header pinouts canonical: J3 SWD 1:GND 2:3V3 3:SWDIO 4:SWCLK; J4 UART
    1:GND 2:3V3 3:TX(MCU) 4:RX(MCU); GND-at-pin-1 on both, silk-labeled -
    no vendor standard exists, so silk is the contract.
14. Two-sheet hierarchy (power / main) with disjoint refdes + #PWR ranges
    (100/200): gives P6 its placement groups for free on a board this size.
15. M2 holes conditional with a CONCRETE hurting test for P6: drop
    right-side pair first, then to 2 diagonal, if holes would (a) grow the
    outline > 2 mm beyond electronic need, (b) shrink the sensor slot /
    break the 8 mm separation, or (c) cut the LDO pour below ~600 mm^2.
16. SHT4x isolation expressed checker-testably as placement.separation
    (U3 >= 8 mm from U1, U2) + edge pin; deliberately NOT a thermal[]
    entry (that would demand spreading copper - the opposite of isolation).
17. Sensirion assembly rule routed to P9/P10 verbatim: no-clean paste, NO
    board wash, no vapor-phase, no hand rework of U3 - must appear in the
    JLC order remarks.
18. sim gate: NONE - no analog block with a numeric pass window exists (the
    only analog question, AMS1117 stability, is a datasheet cap-type
    compliance item, not simulable without a vendor model).

## Rejected

- AP2112K / RT9013 / TLV70233 (LDO): all fail the governing 0.51 W point on
  their own datasheets' thermal numbers (134 C / 300 mW rating / ~425 mW
  allowable) - fine at 0.26 W realistic, wrong for a product-scope
  nameplate.
- Series reverse-polarity element (Schottky or P-FET): orchestrator input
  7, and the dropout arithmetic independently forecloses it (125-190 mV
  would erase the 110 mV worst-corner margin).
- 2 oz copper stackup: nothing needs it; costs money.
- Explicit diff_pairs/high_speed keys: omitted, none exist (an explicit []
  would disable checks board-wide instead of letting auto-discovery no-op).
- planes override for the LDO pour: a declared F.Cu +3V3 plane would pour
  the whole top; the pour is P7 geometry driven by the thermal[] entry.
- Smaller Extended NRST buttons (4x3 mm class): Basic 5.1 mm fits; one
  candidate (TS263065A) also carries a documented lib_pull symbol-name trap.
- 1 A-hold PTC (nSMD100): partial faults in the 350 mA-1 A band would
  never trip; sensitivity chosen over its lower Ri.

## Open / carried verify items

- P3: confirm C6186 (Basic AMS1117) vs its cheaper Extended twin against
  the live fee schedule; confirm C165948 pinout carries shield on SMD GND
  pads (cold THT legs acceptable); verify SHT4x VDD slew <= 20 V/ms vs
  AMS1117 startup ramp (expected fine; add +3V3 bulk if thin).
- P6/P8: USB-C CPL rotation check against datasheet pin-1 (known JLC
  rotation-error class); final outline vs 35 x 25 recorded as
  earned-or-relaxed at H1.

## Cost ballpark for H1 (order_quote at P10 does real numbers)

Parts ~= $4.40/board at qty-5 research prices (MCU $1.37 + SHT40 $1.90 +
connectors ~$0.40 + LDO $0.20 + protection ~$0.08 + jellybeans ~$0.15 +
DNP headers ~$0.07). Fab: 2L ~35x25 mm, 5 pcs ~= $2-4. Economy PCBA setup
+ ~7 unique Extended MPN fees (MCU, sensor, USB-C, JST, TVS, PTC, green
LED at ~$3 each) ~= $25-30. Total run ~= $55-75 for 5 assembled boards
(~$11-15/board); Basic parts (LDO, button, red LED, R/C) carry no fees.

## Revisions at the P2 coverage exit (orchestrator, after research + second reads)

19. I2C pull-ups 2.2 kOhm -> **1.5 kOhm** (decision 8 above superseded). The
    draft record backing 2.2 k was refuted against its own bus budget:
    UM10204 Eq 1 at tr = 300 ns gives Rp(max) = 354/Cb[pF] kOhm, i.e. 1.77 k
    at 200 pF, so 2.2 k needs Cb <= 161 pF. 1.5 k holds the ceiling to 236 pF
    and clears both floors (967 Ohm bus, 390 Ohm sensor). Independently
    recomputed by a second reader.
20. BOOT0 "no strap" -> **R13 = 10 kOhm pull-down on PA14/pin 19**
    (decision 9 above superseded). The no-strap reasoning rested on a record
    whose only source was a community.st.com forum page; a fresh second reader
    refuted it and RM0454/AN2606 are unobtainable (st.com times out from this
    container). The pull-down makes the board boot main flash under EITHER
    option-byte state, so the design no longer depends on unverified
    knowledge. Cost: one 0402, 330 uA on SWCLK.
