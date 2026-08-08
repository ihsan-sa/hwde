# requirements.md - rf-de-20m

20 MHz Class E GaN RF power stage, 200 W into 50 ohm.
Source: `brief/BRIEF.md` + `brief/RESEARCH-LEARNINGS.md`, owner-approved 2026-08-07.

**Frozen inputs - not open for re-derivation.** The topology, operating point and the two
core parts below were decided by the owner after a full costed trade study. They are recorded
here as settled requirements, not as proposals. Class DE was evaluated and REJECTED (no
LCSC-stocked gate driver can switch a 20 MHz half-bridge). Do not reopen.

---

## 1. Function

A bench RF power amplifier stage: a single-ended Class E inverter that converts a 40 V DC bus
into 200 W of 20 MHz RF power delivered to a 50 ohm load. An externally generated 20 MHz PWM
drive signal arrives on an SMA input, is buffered by a low-side GaN gate driver, and switches a
single ground-referenced eGaN FET. The FET's drain feeds a shunt capacitance plus a series
resonant tank and an L-match that transforms the 4.614 ohm Class E load line up to 50 ohm at the
output SMA. Scope is the POWER STAGE ONLY. There is no MCU, no on-board PWM generation, no
telemetry, and no protection logic on this board.

## 2. Interfaces

| # | Interface | Direction | Standard / detail | Connector |
|---|---|---|---|---|
| I1 | RF drive input | in | 20 MHz logic-level PWM from an external signal generator; 50 ohm terminated at the board. Feeds the LMG1020 input. Adjustable duty cycle expected (~50% nominal for Class E). | SMA (stated in brief) |
| I2 | RF power output | out | 20 MHz, 200 W CW into 50 ohm. Controlled-impedance 50 ohm trace from the L-match to the connector. | SMA (stated in brief) - see Q10 |
| I3 | DC bus input | in | 40 V DC, >=6 A. | NOT STATED - see Q5 |
| I4 | 5 V housekeeping | in or internal | 5 V rail for the LMG1020. Source not yet decided: onboard 40 V-input buck vs external 5 V feed. | see Q9 |

Notes carried from the brief that bind the interfaces:
- The 50 ohm output trace must be controlled-impedance all the way to the output connector.
- MUST-RESOLVE at design time: verify the LMG1020 input accepts a 50 ohm-terminated logic-level
  SMA signal directly; add bias or a fast buffer if it does not.
- No other external interfaces exist. No status LEDs, no buttons, no debug/telemetry header are
  required by the brief. ASSUMED: none wanted (scope is deliberately bare bones).

## 3. Power

**Main bus (frozen):**

| Param | Value | Status |
|---|---|---|
| Bus Vdd | 40 V DC | frozen |
| Bus current, DC average | ~5.8 A at 85% efficiency | frozen |
| Supply requirement | >=6 A capable at 40 V | frozen |
| Output power | 200 W into 50 ohm | frozen |
| Class E load line R_opt | 4.614 ohm | frozen |
| Vds peak | 142.5 V (3.562 x Vdd) -> 1.4x margin on the 200 V EPC2019 | frozen |
| Ids peak | ~16 A | frozen |
| Tank current | 6.6 A rms (equals load current - loaded Q sets VOLTAGE across L/C, not current) | frozen |
| Expected efficiency | 80-85% (NOT 86%) | frozen |
| Total dissipation | 35-50 W, most of it in the passives, not the semiconductor | frozen |

**Housekeeping rail:**

- 5 V for the LMG1020 gate driver. Must be a buck, NOT an LDO: gate-charge draw is Qg*f ~ 0.1 A,
  so a 40 V -> 5 V LDO would burn (40-5)*0.1 = 3.5 W.
- GUESS: 5 V rail budget 150-250 mA (0.1 A gate charge + driver quiescent + margin). To be
  confirmed against the actual EPC2019 Qg at the chosen drive voltage during design.
- If an onboard buck is used it must be LCSC-stocked and rated for a 40 V input (see Q9).

**Frozen part selections:**

- Switch: EPC2019 eGaN FET, 200 V / 36 mohm / Coss 110 pF / Qoss 18 nC @ 100 V. LCSC C2836675,
  ~$2.17. 1.35 mm chip-scale LGA, bottom-cooled through its solder balls.
- Driver: LMG1020YFFR, 5 V, 7 A source / 5 A sink, 3 ns prop delay, 1 ns min pulse, 60 MHz.
  LCSC C6423790, ~$0.36, 0.8 x 1.2 mm WCSP. NB: LCSC brands it "Tokmas", not TI - flag for an
  authenticity check on receipt.

**Frozen output network (Class E, Q_L = 5):**

    Drain --+-- C_shunt --GND        C_shunt 317 pF TOTAL (Coss 110 pF + ~200 pF external C0G)
            |
            +-- L_s -- C_s --+-- L_m --+-- SMA out (50 ohm)
                                       |
                                      C_m -- GND

    L_s 184 nH | C_s ~447 pF | L_m ~115 nH | C_m ~500 pF (match Q 3.14, 4.614 -> 50 ohm)

Binding design constraints on that network (from the brief's MUST-RESOLVE list):
- The output inductor is the hottest component on the board (~7 W at Q=150), hotter than the GaN.
  Size L and C by DISSIPATION and Q, not by current rating. If no LCSC RF inductor carries 6.6 A
  rms at high Q: parallel several (splits current AND ESR), or use a PCB air-core spiral
  (JLC-native, free in BOM, costs board area).
- Parallel several C0G caps for C_s and C_shunt to split ripple current. Tank L/C see ~215 V peak
  -> specify >=250 V, ideally 500 V C0G. No X7R anywhere in the tank.
- The drain-feed RF choke must be a real RF choke with self-resonance well above 20 MHz.
- Decoupling: multiple small-case (0402/0603) C0G right at drain/source. Bulk electrolytic is
  useless at 20 MHz and exists only to support the 5.8 A DC feed.

## 4. Environment

NOT STATED in the brief. What is known:

- Bench instrument, no enclosure (explicitly out of scope). Ingress protection: none required.
- Vibration: none - stationary bench use. ASSUMED.
- Ambient temperature: not stated - see Q7.
- Cooling: 35-50 W of dissipation must leave the board. The EPC2019 is bottom-cooled through its
  solder balls, so its thermal path is vias straight into plane copper. Whether that copper is
  then coupled to a heatsink and whether forced air is present is NOT STATED - see Q6.
- Duty cycle (continuous 200 W vs pulsed/keyed) is NOT STATED and materially changes the thermal
  design - see Q8.

## 5. Size & mounting

NOT STATED in the brief - no outline, no mounting holes, no height limit given. See Q3 and Q4.

Constraints that are already fixed and will bound whatever outline is chosen:
- 4-layer stackup is MANDATORY (non-negotiable at 20 MHz). L2 must be an unbroken GND plane
  directly under the power loop.
- Board area is a design variable, not just a cost item: the fallback for the output inductor is a
  PCB air-core spiral, which trades board area for BOM cost and sourcing risk. A tight HARD outline
  cap could remove that fallback.
- Copper pours for the tank and power loop must be wide (skin depth in Cu at 20 MHz is 14.6 um;
  1 oz = 35 um is only ~2.4 skin depths), so conductor area cannot be shrunk to DC-current sizing.

WARNING: any outline cap answered as HARD binds permanently at P5 board_init and cannot be
relaxed later without restarting layout. Answer HARD only if it is a real physical constraint.

## 6. Quantity & budget

NOT STATED in the brief - see Q1 and Q2.

The only budget guidance given is directional: "minimise spend by reducing SCOPE, never by
reducing quality." Known BOM anchors: EPC2019 ~$2.17, LMG1020YFFR ~$0.36.

## 7. Assembly

- **100% JLCPCB PCBA. Zero off-catalog parts.** Owner ruled on this explicitly and it is the
  reason the topology is Class E rather than the originally requested Class DE. Every part must be
  LCSC/JLC stocked. This is a HARD constraint.
- No hand-soldered parts, no wound magnetics, no THT-only parts. (This is what rejected the gate
  drive transformer, the push-pull output transformer, and Mini-Circuits/Coilcraft RF transformers.)
- 4-layer PCB.
- Assembly sides: NOT STATED. ASSUMED single-sided (top) assembly, because the EPC2019 is
  bottom-cooled into plane copper and a clear bottom side is useful for heatsinking - confirm
  via Q6.
- The two connectors (I1, I2) and the DC input (I3) must be JLC-assemblable parts, which
  constrains the connector choices in Q5 and Q10.

## 8. Compliance / safety flags

All three of the following APPLY to this board.

1. **>30 V present (40 V bus, 142.5 V peak switch node).** The DC bus is 40 V and the drain node
   swings to a designed 142.5 V peak, with real ringing on top of that - the 1.4x derate against
   the EPC2019's 200 V rating is the entire margin. Consequences: creepage/clearance on the
   drain net and tank must be sized for >=215 V peak (tank L/C see ~215 V pk); the 1.4x derate is
   protected by POWER LOOP AREA, not trace width, so layout is a safety item here, not just
   performance. Exposed high-voltage nodes on an unenclosed bench board are a shock/arc hazard.
2. **High current (>3 A): ~5.8 A DC input, ~16 A peak switch current, 6.6 A rms tank current.**
   Conductor sizing must account for skin effect at 20 MHz (14.6 um skin depth), not DC ampacity.
   The output inductor dissipates ~7 W and is the hottest component on the board - a burn hazard
   on an open bench board and a fire/derating risk if the chosen part is sized by current rating
   instead of dissipation.
3. **RF transmit: 200 W at 20 MHz.** This is a high-power HF RF source in a band adjacent to the
   13.56 MHz and 27.12 MHz ISM allocations; 20 MHz itself is NOT an ISM allocation. EMC
   implications: a Class E stage is a hard-switched square-wave source, so harmonics at 40, 60,
   80 MHz+ are strong and the only suppression is the output tank/match. Unenclosed, unshielded
   operation at 200 W will radiate. This board is for operation into a matched dummy load or a
   properly licensed/shielded setup only - it is not a certifiable transmitter and must not be
   connected to an antenna without an appropriate licence and additional filtering.
4. **Load-sensitivity hazard (consequence of the frozen topology).** Class E is narrowband and
   load-sensitive; it does not maintain ZVS across load pull. With protection logic explicitly out
   of scope, an open, shorted, or badly mismatched output at 200 W can drive Vds past the 1.4x
   margin and destroy the FET. This needs an explicit owner acknowledgement - see Q11.

Not applicable: no mains voltage anywhere on this board (external 40 V bench supply); no battery
of any chemistry; no motors.

## 9. Open questions

Answer these and the design can proceed. Defaults are offered where a sensible one exists - if a
default is fine, just say "default".

1. **How many boards do you want built?** (Default: 5 - JLCPCB's typical minimum-cost quantity for
   a 4-layer assembled board.)

2. **What is your target cost per board, assembled?** A rough ceiling is enough (e.g. "under $60
   each"). This mainly decides whether the output inductor is bought (several paralleled SMD
   parts) or etched as a free PCB spiral that costs board area. (Default: no explicit ceiling -
   optimise for quality within a sensible bench-instrument cost.)

3. **Is there a maximum board size?** If yes, give width x height in mm, and say whether that
   limit is **HARD** (a real physical constraint, e.g. it must fit an existing fixture - this
   binds permanently and cannot be changed later) or **soft** (a preference). (Default: soft
   guidance of about 100 x 80 mm, no hard cap.)

4. **Do you want mounting holes?** If yes: how many, what screw size, and are their positions
   fixed by something existing? (Default: 4x M3 holes, one near each corner, positions chosen by
   the layout.)

5. **How should the 40 V DC bus connect to the board?** It must carry ~6 A continuously. Options:
   (a) a screw terminal block, (b) a high-current 2-pin header, (c) solder lugs/pads for
   ring-terminal wires, (d) a banana-jack pair. Also: do you already have a 40 V supply that can
   deliver 6 A, and what does its output cable terminate in?
   (Default: (a) a 2-position screw terminal rated >=10 A.)

6. **How will the board be cooled?** It dissipates 35-50 W. Options: (a) bare board on the bench
   with no heatsink (this will get very hot and may not be survivable at continuous 200 W), (b) a
   heatsink bolted to the bottom of the board under the GaN FET, (c) a fan blowing across the top
   of the board, (d) both (b) and (c). Your answer decides whether the bottom copper must be left
   clear and flat, so it also fixes whether assembly is single- or double-sided.
   (Default: (d) - design for a bottom-side heatsink plus forced air, since that is the only
   answer that makes continuous 200 W comfortable.)

7. **What ambient (room) temperature should the board be designed to survive?**
   (Default: 25 C typical bench, designed with margin to 40 C.)

8. **Will this run at 200 W continuously, or in short bursts?** If bursts: roughly how long is a
   burst and how often (e.g. "10 seconds on, a minute off")? This changes the thermal design
   substantially - a pulsed duty cycle can make the hot output inductor a non-issue.
   (Default: continuous 200 W - the worst case, and the safe assumption.)

9. **Where should the 5 V driver supply come from?** Options: (a) an onboard step-down converter
   running off the 40 V bus, so the board needs only one power connection; (b) a separate 5 V
   input you feed from a bench supply or USB brick, which is one more cable but removes a part and
   removes 40 V switching noise near the gate drive. (Default: (a) onboard buck - one cable is
   worth more on a bench instrument.)

10. **Confirm SMA for the 200 W RF output.** The brief says SMA and SMA is electrically fine at
    20 MHz, but SMA is a small connector for 200 W and repeated mating at that power is a known
    wear point; a BNC or N-type is more robust. (Default: keep SMA as briefed.)

11. **SAFETY - please confirm explicitly:** this board has NO protection of any kind (no VSWR
    detection, no overcurrent, no overvoltage, no thermal shutdown - all were placed out of scope).
    Class E is load-sensitive, so running it into an open, a short, or a badly mismatched load at
    200 W can push the switch node past its voltage margin and destroy the FET, and the RF output
    is a burn/RF-exposure hazard at 200 W. Do you confirm this will only ever be operated into a
    proper 50 ohm dummy load or matched load, on a bench, by you? (No default - this must be
    answered.)

12. **What does your signal generator actually put out on the drive SMA?** Specifically: peak-to-
    peak amplitude, whether it can drive a 50 ohm load, and whether its duty cycle is adjustable at
    20 MHz. This decides whether the LMG1020 can be driven directly or needs a bias network or a
    fast buffer in front of it. (Default: assume a 50 ohm-capable generator putting out ~5 Vpp
    into 50 ohm with adjustable duty cycle, and design the input to tolerate 3.3-5 Vpp.)

---

## 10. ANSWERS - all 12 questions closed by the owner 2026-08-07 (P0 batch)

**These are settled. Downstream phases treat them as requirements, not proposals.**

| # | Answer |
|---|---|
| 1 | Build quantity **5** (default taken) |
| 2 | **No hard cost ceiling**; minimise spend by reducing scope, never quality (default taken) |
| 3 | Outline **~100 x 80 mm, SOFT - no hard cap** (default taken). Deliberately NOT hard-capped so the PCB air-core spiral inductor fallback stays reachable |
| 4 | **4x M3** mounting holes at corners (default taken) |
| 5 | 40 V bus via **2-position screw terminal, >=10 A** (default taken) |
| 6 | **OWNER: continuous 200 W + bottom-side heatsink + forced air.** Bottom copper stays clear and flat as a heatsink face -> **single-sided (top) assembly** |
| 7 | Ambient **25 C bench, margin to 40 C** (default taken) |
| 8 | **OWNER: continuous 200 W.** Worst case; thermal drives the layout |
| 9 | **5 V from an onboard buck** off the 40 V bus - one cable (default taken) |
| 10 | **OWNER: keep SMA.** 100 Vrms / 2 Arms at 20 MHz is within SMA HF limits; N-type would break the 100% JLC PCBA rule |
| 11 | **OWNER SAFETY ACK: confirmed.** No VSWR / OCP / OVP / thermal protection of any kind. Operated into a proper 50 ohm matched or dummy load ONLY. Owner accepts that an open, short or bad mismatch at 200 W will likely destroy the FET |
| 12 | **OWNER: ~5 Vpp into 50 ohm, duty adjustable.** -> 50 ohm termination direct into the LMG1020 input, **NO buffer stage**. Closes brief MUST-RESOLVE #4 |

### Consequences that bind later phases

- **Single-sided top assembly.** Bottom layer is reserved as a flat heatsink mounting face; no
  bottom-side components. Thermal via array under the EPC2019 down to bottom copper.
- **Thermal is a first-class layout driver**, not an afterthought: 35-50 W continuous, and the
  output tank inductor (~7 W) runs hotter than the GaN.
- **No protection parts** are to be added by any later phase. If a reviewer flags the missing
  protection, the response is "waived, owner-acknowledged at P0" - not a new part.
- **Outline stays soft** through P5 `board_init`; do not pass a hard `--outline` cap that would
  foreclose a PCB spiral inductor.
