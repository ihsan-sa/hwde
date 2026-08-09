# rf-term-150w - 50 ohm / 150 W single-port RF termination, DC-25 MHz

A bolt-down RF dummy load head. The PCB carries the SMA launch, the reactance
trimmer and the mechanical interface only. The 250 W termination element bolts
directly to a heatsink or coldplate you supply; the PCB is deliberately NOT in
the thermal path.

    SMA jack J1 --+-- launch --> R1 tab (element bolts to YOUR heatsink)
                  |
                 C1  trimmer, shunt to ground, tunes out residual reactance

Board: 26.0 x 20.0 mm, 2 layers, 1.6 mm FR4, 1 oz HASL, JLCPCB standard
process (no upcharge options, no controlled impedance).

**Status:** ERC 0/0, DRC 0/0 (routed, parity + all-track-errors + fresh fills),
placement 0/0, DFM pass, simulation pass (4 benches / 295 bounds / 553 measures,
48 build corners). Verification passes with 3 documented waivers - see section 7.
Nothing has been ordered.

---

## 1. Assumptions taken

The brief left two fields blank and told me not to ask. These are the calls I
made; everything downstream depends on them.

| # | Assumption | Why it matters |
|---|---|---|
| A1 | **Fc = 25 MHz**, band DC-25 MHz, spec band 22.5-27.5 MHz | You said "up to 25 MHz". Top of band is worst case for residual reactance. |
| A2 | **Duty = CW, 100 %, continuous** | Duty was blank. CW is the thermally bounding case. **This assumption alone drives the trimmer choice and 72 % of the BOM cost** - see 6. |
| A3 | 25 C ambient, natural convection for the air-cooled figure | Brief specified 25 C ambient. |
| A4 | Element bolts to your heatsink; PCB rides beside it on shims | Brief scoped the thermal path out of the design. |
| A5 | Hand-built, 5 off. Not JLC PCBA | All three parts are through-hole / mechanical; PCBA of a bolt-down power part at qty 5 is not sensible. |
| A6 | Shunt trimmer is the reactance null, top-adjustable | Brief required adjustment without desoldering or unbolting. |
| A7 | 50 ohm +/-2 % met by **select-on-test**, not by part tolerance | No >= 250 W flanged RF termination is stocked anywhere at <= 2 %. See 5. |
| A8 | Cost cap reported honestly, not engineered around | The gap is a materials floor, not a sourcing failure. See 6. |
| A9 | Deliverables stop at fab artifacts; nothing ordered | No money spent. |

**The port carries 86.6 Vrms / 122.5 Vpeak / 1.732 Arms.** Every clearance on
this board is set to 0.80 mm from that (IPC-2221, 101-150 V band, row A6 for
exposed lands), not to a default.

---

## 2. Tuning procedure

**Tune at reduced drive or with a VNA. Never at 150 W.** Matching for minimum
reflection is a small-signal measurement and is *more* accurate at low drive.
This keeps you away from a 122.5 Vpeak port entirely. C1's threaded case is
grounded by design, so the metal you touch is at ground potential - that is
defence in depth, not the primary protection.

1. Assemble and bolt down per section 4. Let it reach thermal equilibrium
   **cold** - do not tune a hot load, the tune shifts.
2. Connect a VNA (or a signal source + return-loss bridge / directional
   coupler) to J1 at **<= +10 dBm**. Sweep 20-30 MHz.
3. Insert a **Johanson 8764** tuning tool (0.130 in / 3.30 mm shank,
   non-metallic tip preferred) into C1's top slot. A metal blade detunes the
   reading while inserted - back it out before reading, or use the plastic tool.
4. Turn for **minimum reflection at 25.0 MHz**. It is a genuine interior
   minimum - simulation confirms equal degradation either side of the setting -
   so you will feel it bottom out in both directions rather than run to a stop.
5. Confirm >= 20 dB across 22.5-27.5 MHz **without re-tuning**. Set once at Fc;
   re-optimising per frequency is not what the spec means.
6. Remove the tool, re-read, then apply full power.

### Tuning range

C1 is a Johanson 5602, **1-30 pF**. It is *not* the only capacitance at the
port: the launch (42.5 mm of 0.94 mm trace plus the 5.0 x 7.0 mm lap pad)
contributes **~5.4 pF** of its own. Total in circuit is **6.4-35.4 pF**.

Solved from the true null condition `wC = X/(R^2 + X^2)` (not the `C = L/R^2`
approximation, which is 7 % optimistic at the top of the range) and confirmed
by ngspice:

| C1 setting | Total shunt C | Cancels series X at 25 MHz | Equivalent series L |
|---|---|---|---|
| full CCW (1 pF) | 6.4 pF | 2.520 ohm | **16.04 nH** |
| full CW (30 pF) | 35.4 pF | 15.183 ohm | **96.66 nH** |

> ### Achievable adjustment range: residual series inductance **16.0 nH to 96.7 nH**
> (envelope **14.3-100.3 nH** across the 4.7-6.5 pF parasitic uncertainty band).

**The board sits inside that window on purpose.** Its residual is **19.5 nH**
(band 18.5-23.3), so C1 lands at about **2.4 pF** at 50 ohm - roughly
**0.3-3.3 pF of downward authority and ~26-29 pF upward**. Turning the trimmer
either way makes the match worse, which is what a real null feels like. All 12
resistance x inductance corners were simulated and every one has positive
downward authority at the nominal parasitic; the null was verified as a genuine
interior minimum (Im{Zin} = 3e-7 ohm at the setting, and +/-0.29 pF either side
costs an equal 0.0089 dB).

**This cost nothing.** The RF trace is deliberately *not* routed for minimum
inductance - it is a 33 mm meander at the current-limited minimum width. A true
null beats an over-corrected trimmer stop, so making the launch more inductive
actually *improved* the worst-case return loss by **+1.06 dB**.

**The honest edge.** Under the most conservative convention (all the added
distributed capacitance lumped at the port, 6.1 pF) at 51 ohm or above with the
residual at the low end of its band, C1 bottoms out again. It costs **at most
0.07 dB** and every such build still reads **>= 31.66 dB**. Nothing about the
spec depends on it.

### What the trimmer cannot do

A shunt susceptance only cancels the *imaginary* part. A series residual X
transforms the port resistance to **R_eff = R + X^2/R**, which no amount of
trimming undoes. The 26 dB limit is R_eff <= 55.276 ohm, i.e. X <= 16.24 ohm at
R = 50, or **X <= 12.07 ohm (76.9 nH)** at the +5 % resistance corner. At the
as-routed 19.5 nH (X = 3.06 ohm) the board spends only **30 %** of that budget.

Simulated across 48 builds (4 resistances x 4 parasitics x 3 inductances),
C1 tuned once at 25.0 MHz then frozen across the band:

| Element resistance | RL at 25 MHz | Worst in 22.5-27.5 MHz |
|---|---|---|
| 50.0 ohm (nominal) | 54.6 dB | 52.9 dB |
| 49.0 ohm | 41.6-42.7 dB | 41.2-42.1 dB |
| 51.0 ohm (select-on-test limit) | **38.1-38.8 dB** | 37.7-38.5 dB |
| 52.5 ohm (+5 % catalogue corner) | **31.4-31.7 dB** | **31.3-31.6 dB** |

**Worst point anywhere: 31.43 dB at Fc, 31.27 dB in band**, against specs of
26 dB and 20 dB - margins of **+5.4 dB** and **+11.3 dB**. All 48 builds pass.

Note what holds that margin: at the worst corner the reactance is fully
nulled and what remains is *pure resistance error*. A de-selected +10 % part
reads **26.05 dB**, right on the spec line. **Select-on-test, not tuning, is
what keeps this board in spec.**


This is also why an ordinary "non-inductive" bolt-down power resistor cannot
substitute: at the typical 0.1 uH spec limit, X = 15.71 ohm gives **26.55 dB**
at best and **23.46 dB** with a +5 % part - a spec failure the trimmer cannot
rescue, because it is a *resistive* error by the time it reaches the port.

---

## 3. Thermal - the required heatsink

Element: **Vishay/Barry T50R0-250-12X**, 250 W, thick film on BeO.
Derating curve (datasheet p.1, digitised from the plot's vector path):

    250 W flat from 25 C to 100 C flange, then -5.0 W/C, reaching 0 W at 150 C
    Footnote: "Rating based on <=100 C constant flange temperature"

The curve is defined on **flange** temperature, so the element-to-flange Rth -
which the datasheet does not publish - is not needed to close the requirement.

**150 W is permitted at a flange temperature of 120 C.** Therefore:

> ### Required thermal resistance, flange to ambient, at 150 W and 25 C:
> ## **Rth <= 0.633 C/W**
> (0.500 C/W if you want the part at its 100 %-rated 100 C knee, which leaves
> 100 W of headroom instead of zero.)

**The interface is a third of that budget.** The flange is only 24.77 x 9.525 mm
= 2.359 cm^2. A normal 0.5 C.cm^2/W grease joint is **0.212 C/W**, so:

> ### The heatsink *itself* must be <= 0.421 C/W in free air.
> Quoting 0.633 without this is misleading - mount it dry or sloppy and you
> lose the requirement to the joint alone.

### Derated air-cooled power

Solving the derating curve against a given total Rth:

    P = 250 W                for Rth_total <= 0.30 C/W
    P = 625 / (1 + 5*Rth)    otherwise

With real, currently-purchasable heatsinks (published **natural-convection**
figures, interface included):

| Heatsink | Rth_hs | + grease | **CW power** | Flange |
|---|---|---|---|---|
| Wakefield 392-300AB, 300x125x136 mm | 0.33 C/W | 0.542 | **168.5 W** | 116 C |
| Fischer SK 88 100 SA, 100x100x50 mm | 1.05 C/W | 1.262 | **85.5 W** | 133 C |
| No heatsink (bare element in air) | - | - | **~0.8-1.2 W** | - |

> ### Derated air-cooled power: **~85 W** on a sane 100 mm extrusion.
> Hitting the full **150 W in still air needs the 300 mm-class sink** - which
> costs more than every other part on this board combined ($193). Forced air
> reaches 0.42 C/W on a far smaller sink and is the sensible answer if you
> actually need 150 W CW.

---

## 4. Assembly - read before building

The PCB is **not** the thermal path and **not** the ground return by bolting.
Both facts are load-bearing.

1. **Bolt R1 to the heatsink** through its two 3.302 mm flange holes, 18.42 mm
   apart, with a thin, even grease joint. Torque evenly. The board's bottom-edge
   `BOLT CL` and `FLANGE/TAB CL` silk marks give the alignment datum.
2. **Mount the PCB on three 1.0 mm shims** (M3). This lifts top copper to
   2.635 mm, meeting R1's tab underside at 2.667 mm - a 0.032 mm gap, i.e. an
   ideal flat lap solder joint with essentially no added inductance.
   - **Prefer insulating shims** (PEEK / nylon / fibre). They are not needed
     electrically - see 3 below - and they keep the trimmer cooler.
3. **Solder two copper straps from R1's flange to the two GND lands.**
   *This is the only RF return path.* Do not rely on the bolted flange-to-
   heatsink joint: on an anodised sink that joint is a ~418 pF capacitor,
   15.2 ohm at 25 MHz, and the board will not work. Keep the straps short,
   wide and symmetric.
4. **Solder R1's tab to the lap pad.** Guaranteed protrusion is only 3.18 mm
   (the datasheet gives no maximum), so the guaranteed lap is ~2.18 mm -
   measure the actual lead at incoming inspection and trim to suit.
5. **Your heatsink needs a clearance hole under C1**: >= 7 mm diameter,
   >= 5 mm deep or through. C1's threaded case protrudes 4.75 mm below the PCB
   against only 1.0 mm of shim clearance. *Alternative:* let the J1/C1 end of
   the board overhang the heatsink edge - no machining, and it runs cooler.
6. Fit J1 and C1. C1 is top-adjust and must stay reachable with a cable mated.

### Select-on-test (required to meet the DC spec)

The specified element is **+/-5 % catalogue** - no >= 250 W flanged RF
termination is stocked anywhere at <= 2 %, and this part number has no
tolerance suffix at all. So the 50 ohm +/-2 % requirement is met by
**measuring and selecting**:

> 4-wire measure each element. **Accept 49.00-51.00 ohm.** Order spares -
> the datasheet only guarantees +/-5 %, so some parts will fall outside.

This is doing real work: resistance tolerance, not layout inductance, is the
entire error budget. A 3x change in inductance moves return loss by <1 dB; the
+5 % resistance step costs 40 dB.

---

## 5. Safety

- **BeO (beryllium oxide) substrate on R1.** Toxic if inhaled as dust.
  **Do not machine, grind, drill, sand or break the part.** Intact and bolted
  down it is safe. An AlN-substrate drop-in (Barry TA50R0-300-2X, dimensionally
  identical) is documented but was out of stock at both distributors.
- **Hot surface in normal operation.** The flange runs 100-133 C at rated
  power - this is the design condition, not a fault. Do not touch. Allow
  cool-down before handling.
- **>30 V.** 122.5 Vpeak at the port. Never tune at full power; see 2.
- **Never key the transmitter with the port unmated.**
- **No protection of any kind.** This is a bare passive load: no fusing, no
  over-temperature cutout, no interlock, no VSWR trip, no enclosure. If it is
  driven beyond the derated power for its heatsink, nothing intervenes -
  the element runs up its derating curve until it fails. Provide external
  protection if the driving source can exceed the rating.
- **R1's datasheet publishes no maximum voltage or current rating at all.**
  The 86.6 Vrms / 1.732 Arms operating point is inferred from the 250 W power
  rating into 50 ohm, not read off a limit line. Do not assume headroom.
- **SMA is a low-mating-cycle connector** (typically a few hundred cycles, not
  published for this part). For a load that gets moved between rigs often,
  expect the jack to wear out before anything else does.

---

## 6. BOM and cost - the brief's $40 cap is not achievable

Qty-5 pricing, distributor-verified.

| Ref | Part | Source | Qty 5 | Ea. | Ext. |
|---|---|---|---|---|---|
| R1 | Vishay/Barry **T50R0-250-12X**, 50 ohm 250 W BeO flanged | DigiKey 4353-T50R0-250-12X-ND | 5 | $24.40 | $122.00 |
| C1 | Johanson **5602**, 1-30 pF 250 V air trimmer, -65/+125 C | DigiKey 1956-1000-ND | 5 | $63.37 | $316.85 |
| J1 | Lian Xin **SMA-KWE**, SMA jack, 335 Vrms | LCSC C7498154 | 5 | $0.561 | $2.81 |
| | PCB, 2L 26x20 mm | JLCPCB | 5 | - | ~$2-6 |
| | | | | **Total** | **~$444** |

> **~$444 against a $40 cap - about 11x.** Reported, not engineered away, per
> the brief's own instruction to keep the design honest.

**Why, and the one lever you have.** Two irreducible costs:

- **R1 ($122)** is a materials floor. 150 W *rated* is not enough: a part rated
  150 W at 25 C flange needs Rth = 0 C/W to pass 150 W at 25 C ambient, which
  is unsatisfiable with any finite heatsink. The element must be >= 250 W class,
  and that means BeO/AlN RF ceramic. Cheaper wirewound "non-inductive" parts
  blow the reactance budget outright.
- **C1 ($317, 72 % of the BOM)** is bought entirely by **assumption A2 (CW)**.

> ### If your duty cycle is not CW, you save $272 per build of 5.
> The cheap alternative is **Vishay BFC280811339**, 3-33 pF, 250 V, ~$8.88 ea
> (LCSC C3273212), which drops total cost to **~$172**. It is rated only
> **-40 to +70 C**, and this board sits at 74-88 C at full 150 W CW - hence the
> expensive part. At reduced duty or reduced CW power it is entirely adequate.
> It needs a different footprint (3-lead vs threaded case), so it is a board
> change, not a drop-in - tell me the real duty and I will respin it.

Counts against the brief's caps: **3 unique BOM lines** (cap 4), **3 placements
/ 6 footprints** (cap 6), **26 x 20 mm** (cap 30 x 30).

---

## 7. Known limits

- **CPL contains 2 rows (C1, J1), not 3.** R1's body is off-board on your
  heatsink; a pick-and-place "position" for it would mislead an assembler. It
  is in the BOM. The board is hand-built anyway.
- **No field solver.** The 19.5 nH residual is a term-by-term geometric budget
  (grounded-CPW model, 0.4281 nH/mm), not a solved EM result. It is swept
  18.5-23.3 nH and the ~5.4 pF launch parasitic is swept 4.7-6.5 pF; every
  simulated bound holds across both bands. The parasitic is an estimate to
  about +/-25 %, not an extraction.
- **The `verify` gate passes only with 3 waivers** (`reports/verify-waivers.json`),
  covering 7 findings. Five are a checker bug - `check_silk.py` treats an
  unfilled rectangle as solid ink, so it reports J1's `(fill no)` body outline
  as covering its own pads; KiCad's own DRC reports zero silk findings on the
  same board. Two are the unavoidable antipads of the /RF through-hole pads in
  the B.Cu pour (0.45 mm of crossing on a 15.065 mm trace). **These were
  approved by the automated run under your no-questions instruction, not by a
  human engineer.**
- **6 silk strokes are 0.12 mm against JLCPCB's 0.15 mm minimum**, inherited
  from the stock KiCad SMA footprint. The DFM gate passes (warning severity);
  JLC may thin or drop those lines. Cosmetic only - the connector's orientation
  is unambiguous from its four symmetric ground legs.
- **J1's 3D model is absent from KiCad**, so mating direction was proven from
  footprint geometry against the vendor drawing rather than from a render.
  **Worth an eyeball before you order.**
- **C1's 6.3 mm plated hole is exactly at JLCPCB's standard limit** (max
  6.3 mm). Compliant, but with zero margin.
- **Rth element-to-flange is absent** from the datasheet, so no element
  temperature is quoted - only flange, which is what the curve is defined on.
- Return loss is verified by simulation and by geometry, **not by measurement**.
  Build one and sweep it.
</content>
