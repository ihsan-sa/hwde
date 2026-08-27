# g0-sense - FAB PACKAGE (P9/P10)

USB-C powered temperature/humidity sensor node. 2-layer, **35.790 x 28.340 mm**,
1.6 mm FR-4, HASL, green. Built 2026-08-27 from `kicad/g0-sense.kicad_pcb`
(`sexpr_no_uuid:78f20b4b13f8390f7df0b95c041135505a1e527b5c683a8131bb2062c4ec2c35`).

Gates at export: `erc` PASS, `place` PASS, `drc_routed` **PASS 0/0**,
`verify` **PASS** (0 failing, 1 durable waiver, 5 warnings),
`dfm` **PASS** (0 errors, 1 advisory warning). Release attestation rev 1
verifies valid; disposition **order-ready**.

---

# 1. ORDER SETTINGS

| Field | Value |
|---|---|
| Layers | 2 |
| Size | 35.79 x 28.34 mm |
| Thickness | 1.6 mm |
| Surface finish | HASL (with lead) |
| Solder mask | Green |
| Copper weight | 1 oz outer |
| Quantity | 5 (prototype) |
| Assembly | JLC **Economy** PCBA, top side only, 24 of 26 parts |

**Estimated** cost at qty 5: **USD 42.68 total, 8.54/unit** (PCB 2.00 +
assembly 40.68: setup 8.00, feeders 24.00 for 8 Extended parts, stencil 8.00,
joints 0.68 over 80 joints). Source: `fab/quote.json`, `estimated: true` -
these are transcribed headline prices with no panelization and no promotions.
**The JLC cart is the only real quote.** Confirm before paying.

---

# 2. !!! SENSIRION ASSEMBLY RULES - THESE ARE NOT OPTIONAL !!!

U3 is a Sensirion SHT40. Sensirion **FORBIDS board wash**. Put these in the JLC
order remarks verbatim; a washed board is a scrapped board:

- **NO post-assembly board wash / no aqueous cleaning.**
- **No-clean solder paste only.**
- **No vapor-phase reflow.**
- **No hand rework on U3.**

# 3. !!! PANELIZATION - ONE REMARK THAT CANNOT BE FIXED LATER !!!

The right-hand edge (x = 54.75, y 38.05-44.95) is the free end of the **SHT40
thermal isolation tongue** - a cantilever formed by two 5.5 mm Edge.Cuts slots,
carrying the sensor. **Ask JLC NOT to land break-off tabs or mouse-bites on that
edge.** A tab there puts depanelization stress straight into the tongue root and
leaves a rough breakout beside the sensor aperture. Costs nothing to request;
unrecoverable if it happens.

---

# 4. POLARITY / ROTATION - WHAT WAS CHECKED AND WHAT YOU STILL CHECK

`dfm_check` ran with the schematic as the polarity oracle: **26 refs checked,
zero `cpl_polarity` findings, no `rotation_delta_deg` on any part.** The CPL
angles for the polarized parts:

| Ref | Part | CPL rotation |
|---|---|---|
| C3 | 22 uF tantalum, CASE-A | 0 |
| D1 | SMF5.0A TVS, SOD-123 | 0 |
| D2 | Red LED (power) | 180 |
| D10 | Green LED (user) | 180 |
| U3 | SHT40, DFN-4 | 0 |
| J1 | USB-C receptacle | 270 |
| U1 | AMS1117-3.3, SOT-223 | 0 |
| U2 | STM32G030F6P6, TSSOP-20 | 180 |

That proves the CPL agrees with the schematic for every part. It does **not**
replace your own check: at upload, **eyeball JLC's rendered part preview** for
C3, D1, D2, D10 and U3. A reversed tantalum or TVS is a dead board.

**Note on U3's silkscreen**: U3's footprint carries 4 silk strokes at 0.06-0.08 mm,
below JLC's 0.15 mm minimum, so its tiny outline and pin-1 marker may print faint
or drop out entirely. That is cosmetic and known - **do not read a faint U3
outline as a placement error.** U3's orientation is controlled by the CPL
rotation above, not by the silk.

---

# 5. HAND-INSTALL PARTS (not in BOM.csv / CPL.csv)

J3 and J4 are **DNP 0.1 in THT headers** - JLC does not fit them; they appear in
`BOM-full.csv` only, marked, with an `Instructions` column. Solder them yourself.

**The board silk could not fit all eight pin labels** (1.34 mm of available gap
against a 1.70 mm minimum label at this pitch), so only pin 1 and pin 4 are
marked on each header. **Here is the full pinout - pin 1 is the left-hand pad
looking at the top of the board with the USB-C connector on your left:**

| | Pin 1 | Pin 2 | Pin 3 | Pin 4 |
|---|---|---|---|---|
| **J3 (SWD)** | GND (marked "G") | +3V3 | SWDIO | SWCLK (marked "CLK") |
| **J4 (UART)** | GND (marked "G") | +3V3 | UART_TX | UART_RX (marked "RX") |

UART_TX is the **MCU's** transmit pin - cross it to your adapter's RX.

Also note: refdes text for **R1, R2, C10 and D1** sits closer to a neighbouring
part than to its own (and R1/R2/C10 end up under J1's shell and U2 after
assembly). The board is too dense to relocate them without ripping routing;
use this README and the schematic PDF rather than the silk for those four.

---

# 6. HUMAN STEPS (H5 - payment is never automated)

1. Upload `fab/g0-sense_gerbers.zip` to https://jlcdfm.com/ and read the DFM
   report (JLC's own 30+ checks; no public API, so this step is manual).
2. Upload the same zip at https://cart.jlcpcb.com/quote; confirm the real price
   against the estimate in section 1.
3. For assembly: upload `fab/BOM.csv` and `fab/CPL.csv`, then check the rendered
   part preview for every polarized part (section 4).
4. Paste the section 2 and section 3 remarks into the order notes.
5. Review, then pay.

---

# 7. KNOWN RESIDUALS (all recorded, none fab-blocking)

- **1 durable waiver**: `check_thermal` on U1. The checker's theta_JA model
  credits only same-net top copper and ignores the 810.9 mm2 B.Cu GND spreader
  under the regulator. Against the vendor tables for this package (AMS1117 p5
  Table 1: 80 C/W; TI LM1117 Table 9-2: 84 C/W) the rise is 40.8-42.8 C, inside
  the declared 45 C budget - Tj 82.8 C at the governing 0.51 W case, 109.7 C at
  the entitlement-abuse case, against a 125 C limit. Full evidence and the
  proof that no geometry on this outline can satisfy the model:
  `reports/verify-waivers.json`.
- **4 silk misattribution warnings** (R1, R2, C10, D1) - section 5.
- **1 `pdn_no_bulk` warning on VBUS** - correct by design: bulk ahead of the PTC
  is forbidden by the USB-C 10 uF attach limit, so the 10 uF sits one PTC
  downstream on +5V.
- **1 `dfm_silk_width` warning** - U3's footprint, section 4.
- **Bring-up check**: verify RH readings under sustained load. The LDO-to-sensor
  heat bias with a 300 mA Qwiic draw is not knowable from geometry.
