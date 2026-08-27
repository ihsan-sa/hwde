# mcu-sensor - research (P1 component scout)

Block assignment: the two brief-NAMED parts (STM32G030F6P6, Sensirion SHT4x)
plus their pin-compatible/family fallbacks. Both are brief-permitted Extended
parts. All data verified live via `parts_search.py` (JLCPCB/LCSC, today's
stock/price) + the manufacturer datasheets (downloaded and magic-byte
checked, `%PDF`). Full sweeps: `research/raw/mcu-sensor-sweep.json`.

## 1. MCU: STM32G030x6/G031x6/x8/G041x8, TSSOP-20

All TSSOP-20, all pin-compatible (same STM32G0 value-line pinout), all
**Extended** on JLC (no Basic part exists in this family) - each unique MPN
used on the BOM adds one JLC setup fee.

| rank | MPN | LCSC | flash/RAM | stock | price@qty5 | 16MHz HSI current (typ, 25C) | notes |
|---|---|---|---|---|---|---|---|
| 1 | **STM32G030F6P6** (brief-named) | C724040 | 32KB/8KB | 8398 | $1.369 | 1.6 mA (Range1, VDD=3.0V, flash) | no AES/RNG, cheapest ecosystem |
| 2 | STM32G031F8P6 | C529334 | 64KB/8KB | 11970 | $1.3414 | 1.5 mA (Range1, VDD=3.0V, flash) | adds LPUART + 32-bit GP timer; deeper stock AND cheaper than the named part |
| 3 | STM32G031F6P6 | C529333 | 32KB/8KB | 358 | $2.8321 | ~1.5 mA (same silicon as #2) | same flash size as named part; thin stock, pricier than #2 |
| 4 | STM32G041F8P6 | C724065 | 64KB/8KB | 27 | $3.0254 | 1.5 mA (Range1, VDD=3.0V, flash) | adds AES-128 + true RNG; stock is thin (27 units) - last resort |

STM32G041F6P6 (32KB G041 variant) is **0 stock today** on JLC - not
orderable, excluded from the candidate table (checked live, not stale cache).

**Current consumption citation** (the number needed for the power budget):
Table 25 "Current consumption in Run and Low-power run modes", Range 1
(default reset state), PLL disabled, fHCLK = fHSI16 bypass = 16 MHz, fetch
from Flash, VDD = 3.0 V (Typ column), 25C:
- STM32G030F6P6: **1.6 mA typ** - DS12991 Rev 3 ("STM32G030x6/x8" datasheet),
  Table 25, p.44/93.
- STM32G031F6P6/F8P6: **1.5 mA typ** - DS12992 Rev 3
  ("STM32G031x4/x6/x8" datasheet), Table 25, p.50-51/120.
- STM32G041F6P6/F8P6: **1.5 mA typ** - DS12993 Rev 2
  ("STM32G041x6/x8" datasheet), Table 25, p.51/118 (numbers are byte-identical
  to the G031 table - same silicon platform, AES/RNG add negligible static
  current when unused).

All four candidates land well inside the brief's guessed 5-15 mA MCU budget
line - the guess was conservative; actual HSI16 Range-1 run current is
1.5-1.6 mA typ (max column at 85C is 2.1-2.5 mA, still inside budget).

**Family differentiation** (Table 2, family feature-count tables, all three
datasheets): G030 has NO AES/RNG, narrower voltage range (2.0-3.6V), no
LPUART, no internal VREF buffer, temp range -40..85C only. G031 adds LPUART,
one 32-bit general-purpose timer, internal VREF buffer, wider voltage range
(1.7-3.6V) and optional -40..125C grades, but still NO AES/RNG. G041 = G031
plus AES-128 + hardware RNG. SRAM is 8KB across the whole family regardless
of flash size; flash choices in TSSOP-20 are 32KB (x6) or 64KB (x8).

**Risk**: none of the four is single-sourced - the family gives 3 orderable
pin-compatible fallbacks today. The thinnest stock (G041F8P6, 27 units) is
still the AES/RNG upsell, not the default pick.

## 2. Sensor: Sensirion SHT4x, DFN-4 1.5x1.5mm

All JLC-stocked SHT4x variants are **Extended** (no Basic SHT4x exists), and
share one manufacturer datasheet ("SHT4x", Sensirion D1 Version 2, July
2021) that explicitly documents all three accuracy tiers and both I2C
addresses - it was downloaded and page-checked (17 pages, `%PDF-1.7` magic
bytes verified) rather than typed from memory.

| rank | MPN | LCSC | I2C addr | package | stock | price@qty5 | notes |
|---|---|---|---|---|---|---|---|
| 1 | **SHT40-AD1B-R2** (brief-preferred) | C2909890 | 0x44 | DFN-4-EP 1.5x1.5mm | 23700 | $1.9016 | highest stock in family |
| 2 | SHT40-AD1B-R3 | C2848306 | 0x44 | DFN-4 1.5x1.5mm | 13981 | $1.7425 | same die as #1, bigger tape reel (10k vs 2.5k/reel) - packaging code only, cheaper |
| 3 | SHT40-BD1B-R2 | C7461849 | **0x45** | DFN-4 1.5x1.5mm | 2184 | $1.939 | same SHT40 die, alternate address |
| 4 | SHT41-AD1B-R2 | C7461861 | 0x44 | DFN-4 1.5x1.5mm | 927 | $3.0903 | intermediate accuracy tier |
| 5 | SHT45-AD1B-R2 | C5221601 | 0x44 | DFN-4 1.5x1.5mm | 9278 | $6.1254 | best accuracy tier, 3.2x SHT40 price |

**I2C address is load-bearing and differs by suffix letter** (datasheet p.1
"Products Details" + p.15 Table 9 nomenclature, position 7): suffix **A**
= I2C address **0x44**; suffix **B** = I2C address **0x45**. So:
- SHT40-**A**D1B, SHT41-**A**D1B, SHT45-**A**D1B -> **0x44**
- SHT40-**B**D1B -> **0x45**

(Note the nomenclature's own position-7 letter, not the whole "AD1B/BD1B"
string, carries the address - position 8 "D" = DFN package and position 10
"B" = blank/no-membrane variant are constant across the family and are NOT
address indicators. Only the SHT40 line ships a stocked "B..." SKU on JLC
today; SHT41/SHT45 B-address variants exist in the datasheet's naming scheme
but were not found in stock via parts_search.)

**Supply range / current** (datasheet Table 3, Electrical Characteristics,
p.7, valid across the whole SHT4x family): VDD = **1.08 V to 3.6 V**
(typical values quoted at VDD=3.3V, 25C). Supply current (no heater):
idle **0.1 uA typ / 1.0 uA max** (25C, up to 3.4 uA at 125C); during a
measurement **350-500 uA**; average continuous current at 1 measurement/sec,
high repeatability, **2.4 uA typ**. This is far under the brief's guessed
"<1 mA average, single-digit mA peaks" - actual peak is under 0.5 mA and
average is single-digit microamps.

**Recommended decoupling and I2C bus requirements** (datasheet Figure 1,
"Typical application circuit", p.3/17 - read as a rendered page image since
the values are in the schematic graphic, not the extracted text layer):
- **100 nF** ceramic decoupling capacitor directly across VDD-GND at the
  sensor.
- **10 kOhm** pull-ups on both SDA and SCL to VDD in the reference circuit
  (this is Sensirion's own typical value, not the datasheet's minimum-Rp
  spec below - use 10k as the default, matching the design already sharing
  the bus with the Qwiic connector).
- I2C interface: standard/fast-mode/fast-mode-plus capable per NXP
  UM10204 Rev.6; **no clock stretching support** - the master must not rely
  on it. Minimum pull-up resistance (Table 3, p.7) is 820 Ohm for VDD<1.62V
  or 390 Ohm for VDD>=1.62V (drive-strength floor, not a design target);
  max bus capacitance ~400 pF at Rp=820 Ohm (fast mode) or ~340 pF at
  Rp=390 Ohm (fast mode plus) - the 10k default is comfortably inside both
  limits for a short on-board + Qwiic-cable bus.

**Land pattern note**: die pad (thermal pad) soldering is *optional* and
Sensirion recommends **not** soldering it, since the sensor can reach
higher temperatures during heater operation - relevant to the SHT4x thermal
isolation slot/cutout already called out in requirements.md section 4.

## 3. Extended-part cost flag (both blocks)

Every candidate in both tables is **Extended**, confirming neither
MCU-family nor SHT4x-family has a JLC Basic option. The brief explicitly
permits Extended for parts it names (MCU, sensor), so this is not a
deviation - but each *unique* Extended MPN placed on the BOM (MCU + sensor +
any other Extended part elsewhere on the board) draws its own JLC
one-time setup fee (JLC's per-part extended-component fee, independent of
board quantity). Cost ballpark for P3: 2 Extended MPNs (one MCU + one
sensor) is the minimum for this design; picking a fallback instead of the
named part does not remove this fee since the fallback is also Extended.

## Risks

- STM32G041F6P6 is 0 stock today (checked live) - not usable without a
  re-check closer to order time.
- STM32G041F8P6 fallback has only 27 units in stock - workable for a 5-unit
  prototype run but leaves no rework margin; treat as last-resort, not a
  primary fallback.
- SHT41/SHT45 "B-address" (0x45) SKUs were not found in stock on JLC today;
  only the SHT40 line has a stocked 0x45 alternate (SHT40-BD1B-R2). If a
  0x45 SHT41/45 part is ever needed, it will need a fresh live check.
- The Sensirion SHT4x datasheet on file (D1 Version 2, July 2021) is the
  version LCSC serves for the AD1B-R2 SKU; the manufacturer's own hosted
  URL for SHT41-AD1B-R2 (returned by parts_search) 404s server-side
  (S3 "NoSuchKey") - the LCSC-mirrored copy of the same document was used
  instead for all sensor citations, and its `%PDF` bytes were verified.
