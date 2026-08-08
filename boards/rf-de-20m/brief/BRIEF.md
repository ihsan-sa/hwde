# BRIEF - rf-de-20m: 20 MHz Class E GaN RF power stage, 200 W

Owner-approved 2026-08-07. Full derivation + rejected alternatives: `LEARNINGS.md` (this dir).
**Read that file before changing any number here** - the operating point is frozen and the
Class DE / gate-drive-transformer alternatives are already closed.

## Scope (deliberately narrow - owner asked for power stage ONLY)

IN scope: gate driver, GaN power stage, output filter + impedance match, 5 V housekeeping.
OUT of scope: no MCU, no PWM generation, no telemetry, no protection logic, no enclosure.
PWM arrives from an external signal generator via SMA. This is a bench power stage.

## Hard constraints

- **100% JLCPCB PCBA - zero off-catalog parts.** Owner ruled on this explicitly; it is the reason
  the topology is Class E and not the originally requested Class DE (no LCSC-stocked driver can
  switch a 20 MHz half-bridge; see LEARNINGS). Every part must be LCSC/JLC stocked.
- 4-layer PCB. L2 = unbroken GND directly under the power loop. Non-negotiable at 20 MHz.
- Minimise spend by reducing SCOPE, never by reducing quality.

## Operating point (frozen - do not re-derive)

| Param | Value |
|---|---|
| Frequency | 20 MHz |
| Output power | 200 W into 50 ohm |
| Bus Vdd | 40 V DC (needs >=6 A supply) |
| R_opt (Class E) | 4.614 ohm |
| Vds peak | 142.5 V (3.562 x Vdd), 1.4x margin on 200 V part |
| Ids peak | ~16 A |
| I_dc | ~5.8 A |
| Expected efficiency | **80-85%** (NOT 86% - see thermal note) |

## Core parts (both LCSC-verified in stock)

- **Switch:** EPC2019 eGaN FET - 200 V, 36 mohm, Coss 110 pF, Qoss 18 nC@100 V. **LCSC C2836675**,
  ~$2.17. 1.35 mm chip-scale LGA, bottom-cooled through its solder balls.
- **Driver:** LMG1020YFFR - 5 V, 7 A source / 5 A sink, 3 ns prop delay, 1 ns min pulse, 60 MHz.
  **LCSC C6423790**, ~$0.36, 0.8x1.2 mm WCSP. NB: LCSC brands it "Tokmas", not TI - flag for
  authenticity check on receipt.
- **5 V rail:** small 40 V-input buck. NOT an LDO - gate charge draw is Qg*f ~ 0.1 A, so an LDO
  would burn (40-5)*0.1 = 3.5 W. Pick an LCSC-stocked 40 V-capable buck.

## Output network (Class E, Q_L = 5)

    Drain --+-- C_shunt --GND        C_shunt 317 pF TOTAL (Coss 110 pF + ~200 pF ext C0G)
            |
            +-- L_s -- C_s --+-- L_m --+-- SMA out (50 ohm)
                             |         |
                            (--)      C_m -- GND

    L_s 184 nH | C_s ~447 pF | L_m ~115 nH | C_m ~500 pF (match Q 3.14, 4.614 -> 50 ohm)

## MUST-RESOLVE during build (do not silently skip)

1. **Tank current is 6.6 A rms.** In a series-resonant tank the circulating current equals the load
   current - loaded Q sets VOLTAGE across L/C, not current. Size L and C by *dissipation*, not
   current rating.
2. **The output inductor is the hottest component on the board** (~7 W at Q=150), hotter than the
   GaN. If no LCSC RF inductor carries 6.6 A rms at high Q: parallel several (splits current AND
   ESR), or use a PCB air-core spiral (free, JLC-native, costs area).
3. **Parallel several C0G caps** for C_s / C_shunt to split ripple current. L/C see ~215 V peak ->
   specify >=250 V, ideally 500 V C0G. No X7R anywhere in the tank (voltage/temp coefficient).
4. **Verify LMG1020 input** accepts a 50 ohm-terminated logic-level SMA signal directly; add bias /
   a fast buffer if not.
5. Total dissipation 35-50 W. Thermal path for the EPC2019 is vias straight into plane copper.

## Layout rules

- Gate loop (LMG1020 -> EPC2019 gate -> source) must be the tightest loop on the board. The WCSP
  driver exists to be placed millimetres from the FET; do not waste that.
- Power loop area, not trace width, sets the ringing that the 1.4x Vds derate protects.
- Skin depth in Cu at 20 MHz is 14.6 um; 1 oz = 35 um is only ~2.4 skin depths. Pour tank and
  power-loop conductors wide - do NOT size by DC current.
- Decoupling: multiple small-case C0G right at the drain/source. Bulk electrolytic is useless at
  20 MHz - it is there only for the 5.8 A DC feed.
- RF choke feeding the drain must be a real RF choke, self-resonance well above 20 MHz.
- Keep the 50 ohm output trace controlled-impedance to the SMA.
