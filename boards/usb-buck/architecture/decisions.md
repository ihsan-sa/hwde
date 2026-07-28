# usb-buck - P2 architect decisions (for the orchestrator log)

Each entry: what was decided, why, and what was REJECTED with the reason.
Items 1-7 settle the OPEN questions handed over by P1 research.

1. **Buck stands: AP63203WU-7 (TSOT-26), VBUS -> +3V3.** The brief names it and
   the power research endorses it: 31 mW self-heating vs ~97-111 mW for an
   LDO, and 42 mA of VBUS draw at peak vs 54 mA (13% of the input budget
   saved). REJECTED: the LDO override (3 fewer parts, no switch node) - the
   part is brief-specified and the research's own comparison ends "the buck
   stands". Residual cost: a 1.1 MHz switch node and ripple on the rail that
   also feeds VDDA, mitigated by the VDDA 1 uF + 100 nF pair (item 9).

2. **Status LED: red, on PC13, active-low sink, R1 = 1 k (1.4 mA).** The
   resistor is set by the PIN, not by brightness: PC13/14/15 are backup-domain
   pins ST limits to 3 mA, so the research's 330 R (4.2 mA) would violate the
   datasheet. PC13 is chosen because it keeps every fast GPIO free and matches
   the universal F103 firmware convention. Red, not green/blue: a 3.3 V rail
   leaves too little headroom over a 2.9-3.2 V green Vf for a predictable
   current. REJECTED: 330 R on a general-purpose GPIO (brighter, but spends a
   fast pin and breaks the ecosystem convention for a cosmetic gain).
   Effect: +3V3 peak drops 57.1 -> 54.0 mA. No constraint changes.

3. **USB D+ pull-up: R4 = 1.5 k 1%, HARD-WIRED to +3V3.** The board is
   bus-powered, so +3V3 is derived from VBUS and USB 2.0 7.1.5.1 is satisfied
   without a soft-connect; AN4879 requires the switched pull-up only for
   SELF-powered designs. REJECTED: GPIO-driven pull-up - it buys firmware
   re-enumeration for the cost of a net AND makes enumeration itself depend on
   firmware correctly driving a pin (a first-bring-up trap on a bench board,
   where unplugging the cable achieves the same thing). Value is 1.5 k, NOT
   the 10 k many Blue Pill clones fit - that value fails enumeration.

4. **VBUS sense divider: OMITTED.** Not mandatory for a bus-powered device
   (USB is always present when the board is powered) and the F103 has no OTG
   VBUS-sense block, so it would be a plain GPIO read. Saves 2 parts and
   43 uA of the 500 uA USB suspend budget. REJECTED: fitting the AN4879
   33 k / 82 k divider "just in case" - speculative parts. If firmware ever
   wants it, that divider into any 5 V-tolerant pin is the drop-in.

5. **Shield bond: micro-B shell -> GND DIRECTLY at the connector.** One ground
   system, no chassis, bare bench board: the direct bond is the accepted
   industry practice USB 2.0 6.8 defers to, and it gives ESD the shortest
   path. REJECTED: the ferrite / 1 Mohm || 4.7 nF shell island - it needs the
   shield pads on their own copper island, which would carve a hole in the
   In1 GND plane right where the USB pair breaks out, for a benefit that only
   materialises when a separate chassis ground exists. Decided PRE-layout as
   the research demanded.

6. **ESD: one USBLC6-2SC6 (SOT-23-6) at the receptacle, in-line, no separate
   VBUS TVS.** A matched 2-channel array is required (USB 2.0 7.1.6.1: D+/D-
   capacitance must match within 10%); FS capacitance headroom is generous
   (<=50 pF/line recommended, 100 pF/line limit) so no ultra-low-Cj HS part is
   needed. The array's VBUS/supply pin gives VBUS its clamp. REJECTED: adding
   ESDA7P60-1U1M on VBUS as well (AN4879 Table 11's full pairing) - one more
   part and feeder for a bench board whose VBUS already faces a 35 V-rated
   buck input. If the P3-selected array turns out to have no VBUS clamp pin,
   re-open this. NOT fitted: series resistors, ferrite beads, or edge-rate
   caps on the pair - all three are explicitly discouraged for FS.

7. **VBUS capacitance: C1 = 10 uF + C2 = 100 nF, and NOTHING else on VBUS.**
   The USB inrush ceiling (10 uF || 44 ohm, USB-IF 50 uC test) and DS41326
   Table 2's C_IN land on the same number, so both are met exactly with one
   part; DC-bias derating makes the real charge ~30-40 uC against the 50 uC
   limit. The 2 x 22 uF output stack does not count - the AP63203's 4 ms
   internal soft-start keeps attach current under the 100 mA threshold where
   the compliance test starts integrating. Hard rule for P3/P4: any added
   VBUS capacitance forces C1 down to 4.7 uF (electrically sufficient - input
   RMS ripple is only ~28 mA) or an inrush limiter. Full derivation in
   power_tree.md s3.

8. **Hierarchy: 3 child sheets (`usb`, `power`, `mcu`) under a thin root, with
   exactly TWO cross-sheet nets.** The brief asked for hierarchy and the
   pipeline's P4 generates one sheet per subagent. Net naming is planned, not
   inherited: rails are power SYMBOLS (global, bare `VBUS` / `+3V3` / `GND`,
   no sheet pins), the USB pair crosses via sheet pins with root labels
   `USB_DP` / `USB_DM` -> final `/USB_DP` / `/USB_DM` (usbbuck4 golden
   precedent), everything else stays sheet-internal as `/<sheet>/NAME`.
   Sheet names are therefore CONTRACTUAL - `constraints.json` names
   `/mcu/OSC_IN` and `/mcu/OSC_OUT`. Crystal nets are declared `high_speed`
   with a GND reference deliberately: on this stackup a B.Cu run would
   reference the In2 +3V3 plane instead, and check_return_path catching that
   is worth the coupling to the sheet name. Refdes ranges: power 100s
   (U2, L1, C1-C5), mcu 200s (U1, Y1, J2, D1, SW1, R1-R4, C10-C19), usb 300s
   (J1, U3) - full table in sheets.md.

9. **MCU decoupling: ST's F1 scheme in full** - 100 nF per VDD/VSS pair (x3),
   one 4.7 uF bulk, plus a dedicated 1 uF + 100 nF pair on VDDA, 100 nF on
   VBAT, 100 nF on NRST. This does NOT copy stm32-blinky's waiver of the VDDA
   bulk: there the rail came from an LDO, here VDDA sits directly on a
   1.1 MHz switching rail and the USB transceiver needs a clean 3.0-3.6 V.
   REJECTED: a ferrite-isolated +3V3A node - it would create a stub needing
   its own `"pdn": false` constraint entry, for no measurable gain on a board
   that uses no ADC.

10. **Stackup `JLC04161H-3313`** (JLC standard 4-layer, 1.6 mm, 1 oz outer /
    0.5 oz inner, HASL). In1.Cu = solid GND (the USB pair's reference),
    In2.Cu = **+3V3** (the dominant power net by pad count, ~20 vs VBUS's ~5),
    which is exactly what planes_gen's 4-layer default produces - so no
    `planes` key is written. Target outline 40 x 30 mm inside the 55 x 45 mm
    limit; single-sided top SMT, THT SWD header hand-soldered.
    DECIDED: adopt the `diff_90` geometry (w 0.314 / gap 0.210 mm) but order a
    STANDARD 4-layer board, not JLC's impedance-controlled service - FS USB
    does not need controlled impedance and nothing downstream measures it.

11. **Button: SW1 to GND on PB0 with an external 10 k pull-up (R2).** The F103
    resets its GPIOs to floating inputs, so an external pull-up gives a
    defined level with zero firmware and survives reset/debug halts.
    REJECTED: relying on the MCU's internal 30-50 k pull-up (saves one 0603
    and 0.33 mA, but the level then depends on firmware having run). PA0/WKUP
    is deliberately left free: standby wake-up needs an active-HIGH edge,
    which this active-low button would fight.

12. **SWD header J2 = 1x4 2.54 mm THT: 1 +3V3, 2 SWCLK, 3 GND, 4 SWDIO** - the
    ST Nucleo CN4 debug-row order minus NRST/SWO, so an ST-Link ribbon maps
    1:1. No NRST pin (requirements say 4-pin) and no BOOT0 jumper (the user
    button is explicitly not a boot selector), so SWD is the only programming
    path - accepted for a bench board. The 3V3 pin is a reference OUTPUT;
    silkscreen it and do not add a diode.

13. **Lead parts (part classes / MPNs only - LCSC codes are P3's job, never
    from memory):** STM32F103C8T6 LQFP-48; AP63203WU-7 TSOT-26; USB micro-B
    receptacle SMD (KiCad `Connector:USB_B_Micro`); USBLC6-2SC6 SOT-23-6;
    8 MHz crystal, CL 20 pF class, +/-30..50 ppm; 4.7 uH shielded inductor,
    Isat >= 1 A; red 0603 LED; SMD tactile switch; 1x4 2.54 mm THT header;
    JLC Basic 0603/0805 passives everywhere else. The brief's "prefer JLC
    Basic" applies to every part except the brief-named AP63203.

14. **Cost ballpark (ESTIMATE, real numbers at P10):** 4-layer PCB $9.90 for
    10, assembly setup + stencil $16, ~3-4 Extended feeders $9-12, ~120
    joints/board $2, BOM $25-35 -> **~$62-75 for qty 10, ~$6-8 per board**,
    dominated by one-time fees and the STM32.
