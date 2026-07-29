# P4 waivers and triage - LUMINA carrier (LUM-CAR-A)

Source: fresh-context `schematic-reviewer`, 19 findings against the ERC-passing schematic.
ERC gate: **0 errors / 0 warnings** (first attempt). `netlist_audit`: **exit 0**.

Triage key: **FIXED** = changed in copper this phase | **WAIVED** = accepted, reasoning below |
**AMENDED** = fixed by changing the ICD rather than the board | **OWNER** = raised at H2.

---

## 1. The most important caveat: what the ERC pass does and does not prove

**Finding 7, WAIVED with a narrative correction that must survive into the design document.**

`gen/lib_pin_types.py` retypes every pin in `lib/aiee.kicad_sym` to either `power_in` (where the
datasheet extract says ground/power_in) or `passive` (everything else). Confirmed against the exported
netlist: across all 102 components the only two pin electrical types present are `passive` and
`power_in`. There is no `output`, `input`, `bidirectional`, `tri_state` or `open_collector` anywhere.

**Consequence:** KiCad's output-vs-output conflict, input-not-driven, and driver-conflict checks are
**structurally inert** on this design. The 0-error/0-warning result proves only that

- no `power_in` pin lacks a driver, and
- no wire or label dangles.

It does **not** prove pin-level electrical correctness. That coverage came from the reviewer's
independent per-IC audit against the datasheet extracts, not from ERC.

Why it is waived rather than fixed: the retype is the documented workaround for easyeda2kicad symbols
carrying `unspecified` on nearly every pin, which otherwise floods ERC with false `pin_to_pin`
warnings and false `pin_not_driven` errors and makes the gate unpassable (LEARNINGS 2026-07-27
`[easyeda2kicad][erc]`). A richer retype is possible but would need per-pin direction data the
extracts do not carry for every part.

**Required of the design document: do not present ERC 0/0 as pin-conflict coverage.**

---

## 2. Fixed in copper this phase

| # | Severity | Item | Fix |
|---|---|---|---|
| 2 | warning | U22 `+48V_SW` had no negative-transient Schottky, against TPS16630 sec 9.4.1, while driving an off-board ~2800 uF inductive load. V(OUT) abs max is -0.3 V | SS510 added, cathode to `+48V_SW`, anode to `GND`, adjacent to U22 pins 18-20 |
| 8 | warning | R71 = 1 k did double duty as PGOOD pull-up (vendor range 10 k-100 k) and D21 ballast, giving 0.20-0.70 mA of LED current depending only on the green bin's 2.6-3.1 V Vf | PGOOD pull-up moved to 10 k; LED given its own ballast |
| 10 | note | `ENABLE` / `FAULT` ran from the user-mateable J4 straight to the MCU and to U22 SHDN (abs max 5.5 V) with no series protection, while all three analogue connector signals had 1 k + clamp | 1 k series added on both, mirroring the analogue pattern, without defeating R69 |
| 11 | note | `/IMON` can exceed the ESP32-S3's 3.6 V pin abs max for ~1 us between fast-trip and the 45 A SCP threshold | 1 k series added to IO8 |
| 12 | note | W5500 AVDD pin 21 had only the shared 4.7 uF bulk while every sibling supply pin had a local 100 nF | 100 nF added at pin 21 |
| 17 | note | IO3 left floating, but the module datasheet states its strapping value "must be controlled by the external circuit that cannot be in a high impedance state" and it has no internal pull | 10 k pull-down added |
| 13 | note | `TPD4E1U06DBVR` symbol labels pin 1 "D1+" / pin 4 "D2-"; the datasheet says pin 1 = D2-, pin 4 = D1+. Netlist was already electrically correct (wired by number) but the PDF would mislead layout and DFM | Symbol pin **names** corrected; recorded in `lib/EDITS.md` |

---

## 3. Fixed by amending the ICD instead of the board

| # | Item | Amendment |
|---|---|---|
| 6 | `/FAULT` also carries the carrier's own indicator LED, so a daughter asserting it sinks **~4.3 mA**, not the ~0.33 mA the ICD implied - 13x what two other boards were designing against | **ICD rev A6** s3.3 now states "**a daughter asserting FAULT must sink >= 5 mA**". Chosen over moving the LED because 4.3 mA is trivially met by any open-drain FET, and publishing the real number is cheaper for the daughters than a carrier respin plus a GPIO |
| 3 | The ICD described the average-energy governor as closed-loop on IMON, but IMON's specified accuracy starts at **0.6 A** and the rail's sustained limits are **0.25 A (af) / 0.50 A (at)** - both below the floor | **ICD rev A6** adds s6.2.1: IMON is monotonic and useful as a guard, but is **not** a calibrated meter below 0.6 A. Daughters must not depend on better than ~+/-20 % there without per-unit characterisation (the ID EEPROM already provides storage), a shunt+amp on a future revision, or a conservative governor |

---

## 4. Waived - accepted, with reasoning

**Finding 5, U22 OVP set point sits above the part's own rating.** OVP rising is 64.20 V typ and up to
66.78 V worst-case-high, against V(IN) recommended max 60 V and abs max 67 V. Between 60 V and
~66.8 V the eFuse runs outside its recommended range with neither OVP nor the TVS acting (SMBJ58A
V_BR min is 64.4 V).
**Waived because it is inherent, not a design error:** the OVP protects the **daughter**, not the
eFuse. The TVS is the only real clamp on U22 itself. Recorded here and in the design document so
nobody later reads "OVP" as protecting U22.

**Finding 9, D30 status LED current is bin-dependent** (2.12 mA down to 0.61 mA across the green
Vf 2.6-3.1 V spread from a 3.3 V GPIO through 330R). Works; the current is set by the LED bin rather
than the resistor. A red or a 2.0 V-class green would be predictable. Not worth a respin.

**Finding 14, J1 pin 3 (RX centre tap) floating.** Neither the W5500 nor the HY931147C datasheet
publishes a centre-tap network, so this could not be grounded from either extract; the W5500 biases
RXP/RXN internally. Raised at H2 as a cheap optional lever (a 0.1 uF DNF footprint to GND) since P5
freezes the layout.

**Finding 15, no crystal drive-level damping.** R36 = 0R gives the oscillator no series damping
against the W5500's specified 59.12 uW drive level. R36 **is** the intended trim lever and is fitted;
measure on the first prototype. Crystal loading is otherwise correct (27 pF back-solves to ~4.5 pF
stray for an 18 pF part).

**Finding 18, MPS depends on the W5500 staying awake.** Resistive + bias load alone is ~4.6 mA;
normal operation adds ~5.3-10.8 mA (W5500) and ~3.3-8.2 mA (ESP32), so MPS is comfortably over the
10 mA DC floor. But PHY power-down **plus** ESP32 deep sleep would fall to ~6 mA and the PSE would
drop the port. Already captured as firmware requirement **FW-05** in ICD s7.8.

**Finding 19, documentation drift.** (a) ICD header rev label - fixed, now carries the full A2-A6
history. (b) `power_tree.md` says CBULK 44 uF (2 x 22 uF); the build fits 4 x 10 uF = 40 uF nominal
because no 22 uF/100 V MLCC exists on LCSC. Electrically fine (>= 5 uF AC-MPS floor, far under the
~180 uF port ceiling); the doc will be reconciled in the design document.

**netlist_audit `diffpair_naming` x3.** `/ETH_TXP`+`/ETH_TXN` and `/ETH_RXP`+`/ETH_RXN` do not use the
`_P/_N` suffix convention the auto-discovery heuristic looks for. Cosmetic only: `constraints.json`
declares `diff_pairs` **explicitly**, so the heuristic is never consulted and the 100 ohm targets bind
correctly.

---

## 5. Raised at H2 for the owner

**Findings 4 + 5 are coupled and cannot both be comfortably satisfied with this part.**
Re-derived independently from the TPS16630's asymmetric limits with 1 % resistors:

| Threshold | worst-low | typ | worst-high | Requirement | Result |
|---|---|---|---|---|---|
| UVLO rising | 33.66 V | 35.02 V | **36.42 V** | < 37 V | **PASS**, 1.6 % margin |
| OVP rising | 61.69 V | 64.20 V | **66.78 V** | < 67 V abs max | pass, but above the 60 V rec. max |
| OVP falling | **57.18 V** | 60.03 V | - | > 57 V | **PASS**, but only **0.18 V** |

The 0.18 V OVP-falling margin does not survive thick-film tempco: at +/-100 ppm/degC over a 60 degC
excursion the uncorrelated worst case is ~1.2 % on the ratio, i.e. ~56.5 V - below the 57 V PSE
maximum. The consequence is bounded (the rail fails to re-enable only after a genuine >61.7 V event
while the PSE then sits at exactly 57 V), but it is not a margin.

The constraint is close to unsatisfiable with this part: the OVP hysteresis plus +/-2 % forces
`V_OV_fall_min <= V_OV_rise_min / 1.078`, so "never false-trip below 57 V" and "guaranteed re-enable
at 57 V" cannot both be held with comfort. **Owner choice: (a) accept and document the corner,
(b) specify 0.1 % resistors on R66/R67/R73, or (c) re-centre toward protecting U22 and accept that
the rail may not re-enable at exactly 57 V.** Recommendation: **(b)** - it is a BOM tolerance change,
not a respin, and it buys the margin outright.

**Finding 16, the class-4 upgrade resistor has zero thermal margin.** The fitted R3 = 90.9R (class 3,
af) dissipates 73 mW on a 0603 - fine. The documented class-4 alternate (63.4R) dissipates **105 mW
against a 100 mW 0603 rating**. Classification is a sub-second transient so it will survive, but D-01
promises the at upgrade is "a resistor change only - no respin". **Specify the alternate as 0805** to
keep that promise clean. Related: with class 3 programmed, a Type-2 PSE never runs 2-event
classification, so `/T2P` reads "no Type-2" permanently on build 1 - expected, and firmware must not
treat it as a fault.

**Finding 1 (the only ERROR) is being fixed, not waived:** `parts.json` had drifted badly from the
schematic - 9 refdes with no BOM line, 2 with the wrong part, 2 phantom lines (the U40 EEPROM
superseded by the ID_ADC scheme, and a phantom C120), and 7 wrong quantities. Being resynced from the
exported netlist so the BOM/CPL that P9/P10 emit is correct.
