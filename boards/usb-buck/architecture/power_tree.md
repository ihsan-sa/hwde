# usb-buck - power tree

One source (USB VBUS), one regulated rail (+3V3), one regulator. Numbers are
lifted from `research/power.json` / `power.md` and RECONCILED against the
final architecture choices - the only delta is the LED resistor (1 k instead
of the research's assumed 330 R, see decisions.md item 2), which drops the
+3V3 peak from 57.1 mA to 54.0 mA.

```
USB micro-B J1 . VBUS 4.40-5.25 V, 48 mA pk
   |
   +-- C1 10uF + C2 100nF ....... the ONLY capacitance allowed on VBUS
   |
   +-- U2 AP63203WU-7 buck ...... 1.1 MHz, fixed 3.3 V, EN tied to VBUS
          |
          +-- L1 4.7uH + C4,C5 2x22uF
                 |
                 +-- +3V3, 54 mA pk --> U1 STM32F103C8T6 (VDD x3, VDDA, VBAT)
                                    --> R4 1.5k USB D+ pull-up
                                    --> R1/D1 status LED
                                    --> R2 button pull-up
                                    --> J2 pin 1 (3V3 reference, 0 mA)
```

## 1. +3V3 - the only regulated rail

| Consumer | Typ | Peak | Basis |
|---|---|---|---|
| U1 STM32F103C8T6, 72 MHz from Flash, all peripherals enabled | 36.0 mA | 50.0 mA | DS5319 Table 17 (typ, 25 C, 3.3 V) / Table 13 (max, 85 C) |
| D1 + R1 status LED, red Vf ~1.9 V, **1 k** | 1.4 mA | 1.5 mA | (3.30-1.9)/1k typ; (3.33-1.8)/1k at rail max + Vf min |
| R4 USB D+ pull-up 1.5 k | 0.2 mA | 2.2 mA | typ = idle J into the host 15 k pull-down; peak = host drives D+ low |
| R2 button pull-up 10 k (only while pressed) | 0 mA | 0.33 mA | 3.3/10k |
| BOOT0 pull-down, NRST RC, crystal caps, decoupling, J2 pin 1 | 0 mA | 0 mA | returns to GND or AC-only; the SWD 3V3 pin sources nothing |
| **Sum** | **37.6 mA** | **54.0 mA** | |
| +30% headroom on peak | | 70 mA | |
| **Declared `current_a`** | | **0.10 A** | rounded to the one-unit-load ceiling |

72 MHz is not optional: USB FS needs a 48 MHz clock off the PLL, so there is
no lower-power operating point that keeps USB alive. The "all peripherals
enabled" column is deliberately over-conservative (this firmware would sit
nearer 27 mA typ / 32.8 mA max).

Rail voltage: the AP63203's fixed output is 3.27-3.33 V, comfortably inside
the F103 USB transceiver's 3.0-3.6 V window. Below 3.0 V the USB electricals
degrade - the 2 x 22 uF output stack plus the MCU-local 4.7 uF bulk keep
transient droop far from that floor at 54 mA.

## 2. VBUS - input rail (pass-through, no series element)

| Consumer | Typ | Peak | Basis |
|---|---|---|---|
| U2 input current | 29.2 mA | 41.9 mA @ 5.00 V / **47.6 mA @ 4.40 V** | P_out = 3.3 V x I_3V3; P_in = P_out / 0.85 est.; I = P_in / V_bus |
| U2 quiescent (no-load, non-switching) | 22 uA | 22 uA | DS41326 IQ |
| Anything else on VBUS | 0 | 0 | nothing else is fed from VBUS |
| **Sum (worst case 4.40 V in)** | **29 mA** | **48 mA** | |
| +30% headroom on peak | | 62 mA | |
| **Declared `current_a`** | | **0.10 A** | same ceiling |

Efficiency 85% is an ESTIMATE (DS41326 publishes curves only for VIN 12/24 V,
VOUT 5 V). Sensitivity at the 5 V operating point: 80% -> 44.6 mA, 90% ->
39.6 mA. No conclusion here moves across that range.

**USB power class: LOW-POWER bus-powered function.** Peak draw at the
connector is 48 mA - under half of one 100 mA unit load - so the board is
legal before enumeration, on the most pessimistic port, with no firmware-timed
load switching. Declare `bMaxPower` <= 50 (100 mA) in the configuration
descriptor; 0x19 (50 mA) is the honest value. The brief's "500 mA budget" is
the port's capability, not this board's entitlement.

Worst-case input 4.40 V (the floor a low-power function must operate at) is
far above the AP63203's 3.8 V minimum VIN and 3.50 V typ rising UVLO; at
D = 0.75 the on-time is 682 ns against an 80 ns minimum - no dropout, no
pulse-skipping risk.

## 3. Input capacitance: USB 10 uF ceiling vs the AP63203 C_IN - RECONCILED

The two requirements collide at exactly the same number, so both are met with
one part and no compromise:

- USB 2.0 s7.2.4.1 caps the load at the far end of the cable at **10 uF in
  parallel with 44 ohm**, counting bypass capacitance directly across VBUS
  plus any capacitance visible through the regulator. Above that the device
  must add VBUS inrush limiting. USB-IF turns this into a charge test:
  current above 100 mA integrated over 100 ms after attach, 50 uC pass limit
  (= 5 V x 10 uF).
- DS41326 Table 2 asks for **C1 = 10 uF** at VIN.

**Decision: C1 = one 10 uF X5R/X7R (>=16 V, 0805) + C2 = 100 nF HF bypass at
the VIN pin. Nothing else on VBUS - ever.** 10 uF nominal x 5 V = 50 uC, i.e.
exactly the pass limit even crediting zero DC-bias derating; a real 10 uF
0805 at 5 V bias measures ~6-8 uF, so actual inrush charge is ~30-40 uC.
There is **no room left for a second bulk cap on VBUS**. The USBLC6 TVS array
is fine (a shunt with pF-scale capacitance); an electrolytic or a second MLCC
is not. If a later spin must add VBUS capacitance, drop C1 to 4.7 uF - the
input RMS ripple current at 54 mA load is only ~28 mA, so 4.7 uF is
electrically sufficient and the 10 uF is datasheet-conformance margin.

**The output-side capacitance does not count.** Total on +3V3 is ~50 uF
(2 x 22 uF + 4.7 uF MCU bulk + 1 uF VDDA + 6 x 100 nF). The AP63203's
internal 4 ms soft-start charges it at 3.3 V x 50 uF / 4 ms = 42 mA average
on the output side, ~32 mA reflected to VBUS - and the MCU is still in POR
while that happens. Attach current never reaches the 100 mA threshold at
which the compliance test starts integrating, so the only charge the test
sees is C1 itself. **No inrush-limiting FET, PTC or NTC is needed.**

## 4. Dissipation

| Part | P_d peak | Basis | Constraint? |
|---|---|---|---|
| U2 AP63203 | 0.031 W | P_in - P_out = 0.2096 - 0.1782 W | No. dT_j = 0.031 x 89 C/W = **2.8 C** |
| U1 STM32F103C8T6 | 0.165 W | 3.3 V x 50.0 mA max | No - 3x under the 0.5 W flag |
| R1 LED resistor | 0.002 W | (3.3-1.9)^2 / 1k | No |
| L1 4.7 uH, DCR < 100 mohm | < 0.001 W | I^2 R at 54 mA | No |

Nothing exceeds 0.5 W, so `constraints.json` carries **no `thermal` key** -
check_thermal and the annealer's spreading term correctly no-op. The
datasheet's "2 oz copper" layout advice targets 2 A designs; at 31 mW a 1 oz
JLC stack with the In1 GND plane under the part is ample. Keep the standard
practice anyway (tight input loop, small SW copper, GND vias under the IC) -
it is free and it is what keeps 1.1 MHz noise local.

## 5. Sequencing, startup, noise

- **No sequencing.** One rail, one consumer group. EN ties to VBUS (an
  internal 1.5 uA pull-up would auto-start it even floating). 4 ms soft-start
  plus the F103's POR/PDR means VDD is valid long before code runs.
- **USB pull-up is hard-wired** (decision 3): the host sees the connect a few
  ms before firmware is ready, which is fine - hosts debounce >=100 ms before
  reset.
- **VDDA sits on +3V3** with the buck's 1.1 MHz ripple. Mitigation is the
  dedicated 1 uF + 100 nF VDDA pair plus 44 uF of output capacitance, NOT a
  ferrite: a ferrite would create a stub node needing its own width-only
  `"pdn": false` constraint entry for no measurable gain on a board with no
  ADC use. Revisit only if a spin uses the ADC.
- **The SWD header's 3V3 pin is an output/reference.** Powering the board
  from the debugger back-drives the buck output. Silkscreen it; no diode.
- **VBUS is a single net** J1 -> C1/C2 -> U2.VIN with no series element, so no
  `"pdn": false` stub entry is needed. A future series ferrite for conducted
  EMI would create exactly such a stub and would need one.

## 6. Constraints emitted (mirrors constraints.json)

```json
"power": [
  {"net": "VBUS", "current_a": 0.1, "dt_c": 10, "via_amps": 0.5},
  {"net": "+3V3", "current_a": 0.1, "dt_c": 10, "via_amps": 0.5}
]
```

Both are real decoupled rails, so neither takes `"pdn": false`. GND is
deliberately absent: it is a plane (In1.Cu), not a width-ruled trace. 0.10 A
is a rounded-up design ceiling - the real numbers are the 54 mA and 48 mA
peaks derived above.
