# Component scout: USB-PD SINK controller ("PD trigger" class) - boards/pd-trigger

Source requirements: `boards/pd-trigger/requirements.md`. Need: negotiate 5/9/12/15/20V
as a SINK, user-selectable (DIP switch/jumper/button, no MCU on this board), 100W path
(controller itself low-current - power path is straight copper, not through the chip),
visible 5V-fallback indication capability, JLC Basic preferred (soft - no PD sink
controller of any kind is in JLC Basic; all real candidates below are Extended),
economy PCBA, avoid leadless if possible (QFN acceptable only if nothing else works).

Method: `parts_search.py --query <MPN>` (live JLCPCB endpoint, verified reachable) for
stock/price/package truth; datasheets pulled via the wmsc.lcsc.com PDF transform
(LEARNINGS 2026-07-28 [datasheet][parts]) and read with pypdf to confirm the actual
profile-selection pin table, PG/FAULT behavior, and max voltage per part - not taken
from memory.

## Comparison table (top candidates)

| MPN | LCSC | Package | Leadless? | Basic | Stock | Price @1 / @10 | Max V / W | Selection mechanism | PG / fallback signal |
|---|---|---|---|---|---|---|---|---|---|
| **CH224K** | C970725 | ESSOP-10-150mil-1mm | No (gull-wing SOP) | Extended | 12,404 | $0.4858 / $0.389 | 20V / 100W | CFG1/CFG2/CFG3 3-pin digital strap: `1XX=5V, 000=9V, 001=12V, 011=15V, 010=20V` (also single-resistor-on-CFG1 or I2C alternates) | PG pin (10), open-drain active-low "Power Good" - power-present only, does NOT distinguish selected-vs-fallback natively |
| **HUSB238A-BB001-QN16R** | C24833806 | QFN-16L-EP(3x3) | **Yes (QFN)** | Extended | 4,994 | $0.6472 / $0.5278 | 28V/3.25A in GPIO mode (48V/5A only in I2C mode, unused) | ADDR/ORIENT pin float=GPIO mode; SNK_VSET+SNK_ISET are analog resistor-divider inputs (not a clean digital truth table - needs switched resistor taps per DIP position) | FAULT/OUT2 pin (13) pulls HIGH if "the power adapter cannot supply the required voltage or current" - closer native match to the fallback-indication ask |
| CH224Q | C46061833 (real WCH listing) | DFN-10-EP(2x2) | Yes (DFN) | Extended | **0** (real listing; two other "hits" are JLCPCB-Assembly generic placeholder SMT footprints, $0.0393, no datasheet - not real parts, ignored) | $0.4454 / $0.3535 | 28V / 140W (EPR) - more than needed | Same CFG1/2/3 family mechanism as CH224K, extended with AVS/PPS | PG pin, same as CH224K |
| CH224D | C3975094 | QFN-20 | Yes (QFN) | Extended | 1,068 | $0.3777 / n/a (breaks at qty50) | 30V (family max) | CFG1/2/3 + integrates NMOS gate-driver (DRV) and current-sense (ISP/ISN) pins for an internal power-switch role - unneeded here since VBUS passes straight through per requirements | PG-equivalent, unconfirmed pin (datasheet URL not returned by search; covered by same CH224 family manual) |
| IP2721 | C603176 | TSSOP-16 | No (TSSOP) | Extended | 0 | $0.7569 / $0.6246 | 20V max, and only 3 levels | **SEL pin is a 3-level (High/Float/GND) selector giving only 3 max-voltage ceilings**: High=20V, Float=15V, GND=5V on IP2721; a separate IP2721_MAX12 part gives 12V/9V/5V instead. No single populated part covers the required 5/9/12/15/20V set. | none dedicated; also requires an external NMOS in the VBUS path (VBUSG pin) - extra BOM the others don't need |
| CYPD3177-24LQXQ | C2959321 | QFN-24 | Yes (QFN) | Extended | 1,565 | $1.2023 / $1.0974 | 24.5V | **"Highly-integrated pre-programmed" EZ-PD BCR** - fixed single-voltage output set once via Cypress's EZ-PD Configuration Utility (I2C/OTP). No hardware pin-strap for live multi-profile selection found anywhere in the datasheet (grepped for VSEL/pin-strap/preset - no hits). | n/a for this use |
| FUSB302BMPX | C132291 | WFQFN-14(2.5x2.5) | Yes (QFN) | Extended | 7,723 | $0.9441 / $0.8231 | n/a | **Not a candidate**: FUSB302 is a Type-C CC/PHY transceiver only - all PD sink policy (PDO parsing, profile request, GoodCRC, state machine) must run in external MCU firmware. This board has no MCU (selector is DIP switch/jumper/button per the brief). Hard disqualifier, not a package/stock issue. | n/a |

Notes on stock/price: JLC live search, verified reachable this run (`source: "live"` on every
query, no `--db` fallback needed). Price columns are unit price at qty 1 and the qty-10
price break (matches this board's prototype qty).

## Why CH224K and CH224Q/CH224D/IP2721/CYPD3177/FUSB302 were passed over

- **CH224Q**: real WCH-brand listing is currently at 0 stock; also EPR-capable to 28V/140W,
  more part than the 20V/100W ceiling in the brief needs, and DFN-EP is leadless. Two other
  "CH224Q" search hits are JLCPCB-Assembly generic SMT-footprint placeholder entries (no
  datasheet, $0.0393 nominal price, category "SMT") - not real orderable ICs, noted so they
  aren't mistaken for stock elsewhere in the pipeline.
- **CH224D**: QFN-20 (leadless, more pins than CH224K's ESSOP-10) and integrates an NMOS
  gate-driver + current-sense pair aimed at CH224D acting as its own power switch - a role
  this board doesn't need since the 5A path is bare copper from the USB-C connector to the
  output terminal (requirements section 1: "no regulation/conversion circuitry... pass-through
  trigger board"). No upside over CH224K for this design.
- **IP2721**: confirmed via datasheet (section "SEL pin") that it only ever offers 3
  selectable ceilings, not 5, and no single part number covers 5/9/12/15/20V - a hard
  functional gap against the requirement, not a preference call. Also currently 0 stock.
- **CYPD3177**: confirmed via datasheet as a pre-programmed fixed-voltage part (Cypress's
  own description: "highly-integrated pre-programmed... targeting electronic devices that
  have legacy [barrel-connector] power inputs"). Runtime multi-profile selection would need
  an external I2C host to reprogram it - this board has no MCU, so it's out for the same
  underlying reason FUSB302 is out.
- **FUSB302**: PHY-only, needs a host MCU to run the PD stack. No MCU on this board by
  design (selector is DIP switch/jumper/button, not firmware). Hard disqualifier.

## Recommendation

**Lead: CH224K** (C970725, ESSOP-10, WCH). Its CFG1/CFG2/CFG3 pins give a clean 3-bit
digital truth table landing on exactly the five profiles the brief asks for (5/9/12/15/20V,
`1XX/000/001/011/010`) with zero MCU - a direct DIP-switch or jumper wiring, no resistor-divider
tuning needed. Non-leadless package (SOP-style gull-wing), cheapest of the real candidates,
best stock by a wide margin (12,404), and its VBUS pin is confirmed sense-only (tied to VHV)
so the 5A path never runs through the chip. This is also literally the part family the brief
names ("CH224-class"). Gap: its PG pin is a plain power-good signal, not a selected-vs-fallback
discriminator - satisfying requirements-answer #6 (visible fallback indication) will need a
small added voltage-comparison circuit at the architecture stage, not something CH224K gives
for free. Flagging that forward rather than guessing a solution here.

**Alternate: HUSB238A-BB001-QN16R** (C24833806, QFN-16L-EP, Hynetek). Same profile coverage
(GPIO mode reaches 28V/3.25A, well past the 20V/100W needed) and its FAULT/OUT2 pin is a
closer native match for the fallback-indication ask (asserts specifically when "the power
adapter cannot supply the required voltage or current"). Traded off against CH224K on two
fronts: QFN package (leadless - flagged per the requirement to avoid leadless where possible)
and an analog resistor-divider selection interface (SNK_VSET/SNK_ISET) that's less DIP-switch-
natural than CH224K's clean 3-bit digital table. Use if CH224K's real stock or CFG behavior
doesn't pan out once the schematic stage wires it up.
