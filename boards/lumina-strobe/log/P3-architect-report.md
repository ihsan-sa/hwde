# P2 architect - report to the coordinator, ICD rev A6 reconciliation

**Date:** 2026-07-28. **Board:** LUM-DTR-STROBE-A. **Written to disk because `SendMessage` bounces.**

Files changed: `architecture/blocks.md`, `architecture/power_tree.md`, `architecture/sheets.md`.
`constraints.json`, `stackup.md` and `light-engine-spec.md` untouched - nothing in rev A6 reaches
them. All ASCII-clean, JSON still valid.

---

## 1. Channel -> timer -> frequency map (ICD rev A6 s3.5 artifact)

Written as a **normative declaration** in `blocks.md` s4.2.

| Pin | Colour | Function | Peripheral | LEDC timer | Freq / resolution |
|---|---|---|---|---|---|
| PWM0 | W | `FLASH_GATE_W` | **GPIO / RMT one-shot** | **none** | n/a |
| PWM1 | R | `FLASH_GATE_R` | **GPIO / RMT one-shot** | **none** | n/a |
| PWM2 | G | `FLASH_GATE_G` | **GPIO / RMT one-shot** | **none** | n/a |
| PWM3 | B | `FLASH_GATE_B` | **GPIO / RMT one-shot** | **none** | n/a |
| PWM4 | W | `AMP_SET_W` | LEDC | **timer A** | 13-bit / 9.766 kHz |
| PWM5 | R | `AMP_SET_R` | LEDC | **timer A** | 13-bit / 9.766 kHz |
| PWM6 | G | `AMP_SET_G` | LEDC | **timer A** | 13-bit / 9.766 kHz |
| PWM7 | B | `AMP_SET_B` | LEDC | **timer A** | 13-bit / 9.766 kHz |

**1 LEDC timer consumed, 3 free.** Rev B budgeted two timers and left none; the withdrawal of the
two-timer partition halves what this board needs. Rev B s4.3 is retained only as the rationale for
choosing RMT, explicitly flagged as no longer describing a constraint. Route 3 (requesting timers
2/3) is now moot in both directions.

**CR-4 stagger applies** (four channels on one timer) and is **harmless**: a phase offset does not
change a filtered DC mean. Two small free benefits - the four RC filters stop drawing charging
current simultaneously, and the residual ripple across the four colours is decorrelated so it
cannot sum coherently.

## 2. The 14-bit / 4.883 kHz option - DECLINED

1. **Resolution is not the limiting error, by 47x.** 13-bit LSB = `2.6 A / 8192` = 0.317 mA =
   **0.12 %** at the 10 % dim point. The LM2904B's 3 mV offset on the 52 mV setpoint there is
   **5.8 %**. Doubling a resolution already 47x finer than the dominant error buys nothing.
2. **It doubles setpoint ripple**, 2.6 % -> **5.2 %** of full scale (RC ripple scales `1/f`). That
   is real current modulation on the LED.
3. **Restoring the ripple breaks the amplitude contract.** Back to 2.6 % needs `tau` 2 ms, taking
   1 % settling from 4.6 ms to **9.2 ms**, against a **shortest normal pulse of 2.67 ms**.

Plus judgement: 4.883 kHz spends camera-flicker margin on **the one fixture in the rig most likely
to be filmed.** Stay at 13-bit / 9.766 kHz.

## 3. ICD s7.7 reconciliation - the 85-90 C failing rows DO NOT survive

**Design-of-record ambient raised 56 C -> 70 C**, the ICD's published ceiling. Deliberately not
this fixture's computed 32-48 C: 70 C is the most conservative number that is actually *normative*,
so the board is correct anywhere inside the ICD's envelope rather than only at its expected point.

| ambient | allowance | pass FET 0.807 W | charge FET 0.215 W |
|---|---|---|---|
| 32-48 C (wall path works) | 1.51-1.82 W | 1.9-2.2x | 7.0-8.5x |
| **70 C - design of record** | **1.076 W** | **1.33x PASS** | **5.0x** |
| 77 C (wall path FAILS, 40 C room) | 0.939 W | 1.16x PASS | 4.4x |
| **83.8 C** | 0.807 W | **break-even** | 3.7x |
| 85-90 C (par's bound) | 0.685-0.783 W | 0.85-0.97x fail | 3.2-3.6x |

- **The worst package fails at 83.8 C. The ICD holds air to 70 C. That is 13.8 K of margin against
  a normative ceiling.**
- **Even the wall-path-FAILS case passes** (71-77 C at a 40 C room -> 1.16x). The design tolerates
  the failure of its own load-bearing dependency.
- **The `P_rail` governor caps (7.99 W / 6.99 W) are WITHDRAWN as operating constraints** and
  retained as contingency documentation only. **Do not implement them in firmware.** They cost
  3-15 % of the light and are needed at no ambient the ICD permits.
- **Still standing:** `BANK_ARM` remains momentary-only - armed-25 Hz is 1.408 W against a 1.076 W
  allowance, a *worse* ratio at 70 C than at 56 C. It is now the board's only thermal constraint.
- **Bank life at 70 C = ~113,000 h** (vs 298,000 at 56 C, 28,000 at 90 C) - a 2.6x reduction, not
  the 10x s10.5 warned about. No longer a headline finding.

## 4. Corrected s10.3 cold-start bracket - Tjmax 150 C, not 175 C

BLOCKING-04 made `Q100` a P-channel; IR P-channels in this class are -55..+150 C. 2.56 J / 590 ms,
mean 4.34 W, `Zth_JA(0.6 s)` 5-9 C/W -> 22-39 C rise:

| | Tj | vs 125 C design | vs **150 C** abs max |
|---|---|---|---|
| **70 C air (design of record)** | **92-109 C** | **inside, 16-33 K spare** | 41-58 K spare |
| 90 C air (par's bound) | 112-129 C | brackets, +4 K worst | 21-38 K spare |

**At the design-of-record ambient the cold start is no longer marginal at all.** It was only ever
marginal against the par's bound, which s10.8 moved out of the envelope.

## 5. Floating-rail bias budget - resolved with both levers

```
  24 k, one 0805 (rev C):
    bias at 48 V = 1.50 mA ; LM2904B Iq up to 1.2 mA -> only 0.30 mA for the zener   TOO LITTLE
    dissipation at 57 V = 84.4 mW / 125 mW 0805 = 67 %                                TOO HOT
  and the two pull in opposite directions.

  REQUIREMENT: zener bias >= 1.0 mA at the 48 V minimum with worst-case Iq
               (48-12)/R - 1.2 mA >= 1.0 mA  ->  R <= 16.4 k

  ADOPTED: 2 x 8.2 k 0805 IN SERIES = 16.4 k   (lower it AND split it)
    48 V -> 2.20 mA, zener gets 1.00 mA (worst case)
    57 V -> 2.74 mA, zener gets 1.54 mA ; 123.5 mW total = 61.7 mW/part = 49 % of 0805
    zener 18.5 mW in a 500 mW SOD-123 = 4 %
```

An 0805 holds full 125 mW to 70 C, which is now the design-of-record ambient, so **no derating
applies at the operating point.** Every part of the charge loop now has comfortable margin.

**Cost recorded:** `+48V_SW` housekeeping 3.02 -> **4.22 mA**, total housekeeping **342 mW**,
`P_avail` 8.215 -> **8.158 W (-0.7 %)**. `I_avg` 0.170 A puts `V_mean` at **44.5 V** with the
20.5 ohm path - **still exactly at the ceiling, so the ballast sizing is unchanged.**

## 6. Charge-FET SOA verdict - the method does NOT extend

**`IRF5210STRLPBF`. The `P x Zth = 150 C` method that closed the `IRF640NS` does not transfer.**

The `IRF640NS` case worked because **there was a DC line to extrapolate toward** - it was
interpolation *between* the 10 ms curve and the published DC asymptote, verified against four
plotted lines. The `IRF5210S` publishes **100 us / 1 ms / 10 ms only, Tc-referenced, no DC line**.
590 ms is **59x beyond the longest curve with nothing beyond it** - extrapolation past the end of
the data, on the one device whose failure mode is a linear-mode short across 48 V.

**Context so the escalation is decidable:**

```
  peak stress = 0.20 A x 43.9 V = 8.78 W falling to 0 over 590 ms
  as a fraction of the part's ~200 W Pd rating              = 4.4 %
  junction-to-CASE rise, Zth_JC ~1.2 C/W at 0.6 s           = ~10.5 C
```

**In bulk-thermal terms this is mild.** What no number covers is **Spirito hot-spotting, a local
instability not predicted by average power** - and at 0.20 A the part sits far below any ZTC
crossover, in the positive-tempco region.

**Mitigations considered and rejected**, so the escalation does not re-tread them: a bigger ballast
is barred by the route-(a) window arithmetic; a lower current limit is barred because sustained
draw is **0.170 A**; a soft-start ramp on the reference **does not help** - it delays the peak
without reducing it, since peak power occurs once current has reached the limit and the bank is
still low.

**Options for the owner:** **(a)** accept and validate on the bench - 1000+ ENABLE cycles with
`Rds(on)` thermometry on the first prototype, defensible given the 10 s re-arm contract and the
event's rarity; **(b)** source a P-channel with a plotted DC SOA line from outside the JLC
catalogue as a hand-fitted part, alongside the bank and connectors which already are not a standard
SMD line (P3-OPEN-6); **(c)** revisit the deleted hot-swap controller with TIMER held low, trading a
documented undocumented-mode hack for a documented SOA. **Recommendation: (a), with (b) as fallback
if the bench run shows drift.**

## 7. IMON (ICD rev A6 s6.2.1) - read, and it does not constrain this board

`IMON` has **no datasheet-guaranteed accuracy below 0.6 A**; this rail runs at 0.25 A (af), so the
governor's feedback is good to roughly **+/-20 %** at the current it actually regulates.

**This board does not depend on it, for two independent reasons:**
1. **The flash schedule is commanded, not measured.** Rail power is known feed-forward from
   energy x rate; the governor does not need to meter it.
2. **The charge path is hard-limited at 0.20 A in hardware**, so `P_rail` can never exceed 9.6 W
   however badly firmware mis-meters.

And the protection that matters - the NTC over-temperature trip - is **firmware-independent by
construction** (STR-REQ-20). Recorded in `blocks.md` s4.6 as: treat `IMON` as the ICD suggests, **a
guard, not a meter.**

## 8. `FAULT` sink current

Recorded in `blocks.md` s2.4.4 as the requirement `Q404` is sized against: ICD rev A6 s2 requires
**>= 5 mA** because the carrier hangs its **red fault LED** on that net as well as the 10 k pull-up
(real load ~4.3 mA, not the 0.33 mA a 10 k to 3.3 V alone implies). `Q404` (2N7002, 115 mA,
`Rds(on)` ~1.2-2 ohm) gives **`VOL` ~10 mV at 5 mA**. **A comparator output driving `FAULT`
directly would have been sized against the wrong load** - the translation stage was added for a
level-shift reason and happens to be the only thing on the board that could have met this anyway.

## 9. `ID_ADC` - the placeholder was wrong and it was the PAR's code

**`R_ID` = 2.7 kohm 1 % (ICD rev A6 s3.4 code 1, LUM-STR-A, `V_ID` 0.702 V).** The 4.7 kohm carried
since rev A is **code 2 = LUM-PAR-A**. Left alone, this board would have announced itself to carrier
firmware as the RGBW par and been handed the wrong daughter profile - including, under the new
s3.5 regime, **the wrong channel -> timer map**. Fixed in `blocks.md` s2.1 and `sheets.md` (R2 and
the net table); all "placeholder pending allocation" language removed.

---

# parts.json deltas

| action | part | why |
|---|---|---|
| **CHANGE** | `R2`: 4.7 kohm -> **2.7 kohm 0603 1 %** | ID_ADC code 1. **The old value is the par's code** - functional mis-identification, not cosmetic |
| **CHANGE** | floating-rail dropper: 1 x 24 k 0805 -> **2 x 8.2 k 0805** | Bias budget + dissipation, s3.3.1. Both 0805, likely Basic - **no new feeder expected, +1 placement** |
| no change | `IRF5210STRLPBF` | SOA is escalated, not re-sourced. Do not substitute pending the owner's decision |

Nothing else moves. The rev D additions (100 ohm gate resistors, 1 nF compensation, hysteresis
resistors, SMAJ12CA-class TVS, `Q404` 2N7002 placement) are unchanged and still stand.
