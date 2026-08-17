# power_tree.md - bb-mcu rails and budgets

**One rail. No conversion, no regulation, no sequencing, no switching, no
second rail, no energy storage.** This is the shortest power tree the pipeline
can produce, and saying so precisely is the point of the file.

`research/power.json` does not exist: the P1 roster SKIPPED
`research-power-architect` under its own "unless trivially powered" clause
(one external 3.3 V rail, no conversion, < 100 mA guessed). The numbers below
are therefore reconciled from `requirements.md` s3 + A1, the MCU datasheet
facts in `research/refdesign-mcu.md`, and the probe VTref figures in
`research/interface-swd.md` - not lifted from a power fragment.

---

## 1. The tree

```
EXTERNAL 3.3 V source  (bench PSU, or another board's 3.3 V pin)
  A1: NOT a battery. Indoors. Current-limited to roughly 0.5 A or less.
  Nothing charges and nothing stores energy on this board.
        |
        |  two bench lead wires
        v
  J1  2-pole 5.08 mm screw terminal   (silk + / -, the ONLY reverse-polarity defence)
        |
        +----------------------------------------> +3V3   (the board's only rail)
        |                                            |
        |                                            +--> U1 VDD  (pin 16)   + C1 100 nF, C2 4.7 uF
        |                                            +--> U1 VDDA (pin 5)    + C3 10 nF,  C4 1 uF
        |                                            |      (bare trace, NO filter - see below)
        |                                            +--> J2 pin 3  "3V3"    probe VTref SENSE only
        |
        +----------------------------------------> GND
                                                     |
                                                     +--> U1 VSS (pin 15) - also the VDDA return
                                                     |      (TSSOP-20 has NO VSSA pin)
                                                     +--> R1 -> BOOT0 (pin 1)
                                                     +--> J2 pin 1, J3 pin 3
                                                     +--> B.Cu pour: return AND reference
```

There is no node between J1 and the MCU. Nothing is switched, dropped,
filtered, ORed, fused, sequenced or monitored - all of that is excluded by the
`block-only` tier, and none of it is a reviewer finding on this board.

---

## 2. Rail spec

| Property | Value | Source |
|---|---|---|
| Nominal | **3.3 V** | brief (STATED) |
| Tolerance | **+/- 5 %** = 3.14 - 3.47 V | A1 (owner answer, now a stated requirement) |
| Part acceptance | **3.0 - 3.6 V** | A1 + `requirements.md` s2 point 1 |
| STM32F030 operating range | wider than 3.0-3.6 V on both sides (the F0 value line runs down to ~2.4 V) | NOT extracted by this run's research - the sourced fact is that the part clears the 3.0-3.6 V requirement (`research/mcu.md`); P3 pins the exact VDD range from the datasheet. Nothing on this board depends on the lower limit |
| Source current limit | ~0.5 A or less | A1 |
| Board budget | **< 100 mA (GUESS)** | `requirements.md` s3 - see s3 below |

The source can deliver several times what the board draws and there is no fuse
or current limit here by mode. At 3.3 V that is a bench fact, not a hazard to a
person - `requirements.md` s8 states it rather than hiding it.

---

## 3. Budget - and it is honestly a guess

| Consumer | Current | Basis |
|---|---|---|
| U1 STM32F030F4P6, running | **5 - 30 mA typical** | small Cortex-M0 on its internal RC at 3.3 V; `requirements.md` s3 |
| U1 worst case, everything on | still well under 100 mA | same |
| J2 probe VTref sense | **< 170 uA** (worst SOURCED case: J-Link EDU Mini; J-Link BASE/PLUS < 25 uA; ST publishes no ST-LINK figure) | `research/interface-swd.md` s7 - 0.17 % of budget, so it gets NO entry of its own |
| The four GPIO on J3 | a few mA each at most | A3: loaded no harder than the MCU's own per-pin limit; nothing inductive |
| **Declared board budget** | **100 mA = 0.33 W** | the SIZING CEILING, not a prediction |

**100 mA is the number `constraints.json` carries, and it is a marked guess.**
No firmware is delivered by this pipeline, so the real consumption depends on
code that does not exist yet; the ceiling is what copper and connectors get
sized against. Both are stated so nobody later mistakes the ceiling for a
measurement. The realistic figure is ~5-20x lower.

**Nothing about this rail is close to any limit.** IPC-2152 at 0.1 A and
dT 10 C on 1 oz outer copper asks for a width far below the fab's own minimum,
so `rules_gen` will bucket `+3V3` straight into the Default netclass (verified:
`rules_gen.net_classes` takes `max(min_width_mm, default_track)`). The screw
terminal, the 0.1 in headers and any routable trace are all oversized for
0.1 A by more than an order of magnitude at any geometry the placement earns.

---

## 4. Thermal: no entry, and why

`constraints.json` carries **no `thermal[]` section**, and the arithmetic is
written out here rather than waved at, because the margin at the GUESSED
ceiling is real but not infinite.

| | at the 100 mA budget CEILING | at the realistic 20-30 mA |
|---|---|---|
| Board dissipation | **0.33 W** | ~0.07-0.10 W |
| Junction rise, theta_JA 100-150 C/W | 33 - 50 C | 7 - 15 C |
| Tj at the 50 C ambient maximum | **83 - 100 C** | 57 - 65 C |

Against the ~105 C junction limit of the -40 to +85 C ("6") temperature grade
that passes at every corner - by ~5 C in the worst combination of two
conservative guesses stacked on each other (a budget ceiling ~5x the part's
real draw, and the pessimistic end of the theta_JA class), and by ~45 C at the
figures the board will actually run at.

**Two caveats, stated rather than buried:** `theta_JA` for this exact
TSSOP-20 and the part's Tj limit were NOT extracted by this run's research -
both are part-class values, and P3 should replace them from the datasheet's
thermal table when it locks the part. And 0.33 W is the requirements.md s3
GUESS, not a measurement (`s3` above).

Even so this is not a design question: there is no exposed pad, no heat path to
engineer, no via array to specify, and no plausible reading of the numbers in
which the answer changes. `requirements.md` s3 puts it plainly - nothing on
this board is a thermal problem.

**The outline is therefore NOT a radiator here** - the explicit
contrast with `bb-buck`, where R_ba ran 39 -> 31 C/W with area and the outline
was an electrical decision. On bb-mcu the outline is set by connectors,
package escape and mounting holes only (`blocks.md` s6).

---

## 5. Decoupling inventory - what P4 must emit into `decoupling.json`

`decoupling.json` is a SEPARATE file, emitted by the schematic generators
(`schlib.place_ic_with_decoupling` + `Project.save(decoupling=...)`), not by
this package. The associations it must carry:

| cap | ic | pin | rail | value | gnd | class | intent |
|---|---|---|---|---|---|---|---|
| `C1` | `U1` | 16 (VDD) | `+3V3` | `100nF` | `GND` | `hf` | the per-pin-pair ceramic DS Fig 12 requires |
| `C2` | `U1` | 16 (VDD) | `+3V3` | `4.7uF` | `GND` | bulk | the net's bulk reservoir (AN4325 C6) |
| `C3` | `U1` | 5 (VDDA) | `+3V3` | `10nF` | `GND` | `hf` | AN4325 C3, "used for VDDA" |
| `C4` | `U1` | 5 (VDDA) | `+3V3` | `1uF` | `GND` | bulk | AN4325 C5, "used for VDDA" |

**`"role": "reg_input"` must NOT appear on any of them.** That role exists to
catch a missing HF ceramic at a SWITCHING REGULATOR's input pin; there is no
switching regulator anywhere on this board, and applying the role would
manufacture a `reg_input_no_hf` class of finding against a rail that has no
regulator to feed.

`max_dist_mm` should be tight (a few mm) on C1 and C3 - the datasheet's own
words are "as close as possible to, or below, the appropriate pins", and
AN4325 Fig 8 shows a supply via and a ground via straddling the cap right at
the pin. C2 and C4 are reservoirs and may sit one position further out.

With those four associations present, `check_pdn` sees `+3V3` carrying both HF
ceramics and >= 1 uF of bulk, which is exactly what it tests for.

---

## 6. Back-feed - a bench fact, restated because the board cannot enforce it

J2 carries `3V3`, so the board has two physical paths to its rail and no ORing,
no diode and no protection by mode. Two things make this a procedure note
rather than a defect:

1. **The J2 3V3 pin is a probe INPUT.** ST: `T_VCC`, "Input for STLINK-V3SET".
   SEGGER: VTref "is not intended to power the target system" and "must not
   have a series resistor".
2. **No probe in this class can back-power the board through a 5-position
   header.** Checked per probe in `research/interface-swd.md` s7: the only
   documented target-supply pin in any of them (ST-LINK/V2, ST-LINK/V2-1,
   STLINK-V3, J-Link, RPi Debug Probe, DAPLink) is **pin 19 of a 20-pin
   header**, and J2 has no such pin. STLINK-V3's manual states outright that
   it "does not provide power supply to the target application".

So: power the board from J1, never from the probe. That rule stands for
procedure hygiene and for the reversed-plug case - which the P1 pin-order
ruling already made non-destructive - not because a back-drive path was found.

---

## 7. What `constraints.json` declares, and what it deliberately does not

**Declares:** one `power[]` entry - `+3V3`, `current_a 0.1`, `dt_c 10`. That
entry is what sizes the netclass track width at P5 and what puts the rail into
`check_pdn`'s decoupling inventory and `check_irdrop` at P8.

**Does NOT declare `GND`.** This is a deliberate divergence from `bb-buck`,
which declared its return at 2.6 A on purpose. Here the declaration would buy
nothing and cost something concrete: at 0.1 A no width rule binds (the IPC
width is below the fab minimum), there is no IR-drop question, and no pour neck
can fail - while `check_pdn` iterates over `power[]` rails and errors
`pdn_undecoupled` on any entry with no caps associated to it. A return net
cannot have decoupling to itself, so declaring `GND` here would manufacture a
P8 error whose only resolution is a waiver. `bb-buck` paid exactly that price
and wrote the waiver. The return path on this board is verified by the checks
that can actually see it - `drc_routed`, `check_return_path`'s default
behaviour, and the unbroken B.Cu pour itself.
