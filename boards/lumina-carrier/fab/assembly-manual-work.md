# LUM-CAR-A - manual / non-standard assembly, in one place

Collected at H5 because it accumulated across P3-P10 in separate decisions and was
never totalled. **Quantities below are per board**, at the ordered quantity of 15.

## Correction to carry forward: the magjack is NOT hand-fitted

The "hand-fitted magjack" belongs to a **withdrawn** plan. Sequence of record:

| Candidate | Outcome |
|---|---|
| HY931147C (original) | publishes **no** tap current rating - rejected |
| Wurth 7499410213 | 600 mA/tap = exactly the 802.3at DC max and **below** the 0.686 A peak; **zero** LCSC stock, so **DNP + hand-solder 16 terminals x 14 boards**; +7.20 USD/board |
| **LINK-PP LPJG0926HENL (C22457393)** | **ADOPTED.** 720 mA @ 57 VDC continuous - covers the 0.686 A **peak**. 3109 in stock. **JLC Assembly Type = Wave Soldering, so JLC places it.** 80.57 USD cheaper than the Wurth plan for 14. |

So J1 is **machine-placed**. Eliminating that hand-solder operation was one of the
reasons the part was chosen (state.json decision, P3). Nothing about J1 is manual.

## What actually needs non-SMT handling: 6 THT parts, 72 THT joints

| Ref | Part | LCSC | Pins | Note |
|---|---|---|---|---|
| J1 | LPJG0926HENL RJ45 PoE+ magjack | C22457393 | 20 | **Wave soldering** per its JLC listing - machine, not hand |
| J3 | DS1021-2x7SF11-B male header | C7430403 | 14 | 2.54 mm THT. Carries 48 V / 12 V / 3.3 V + 7 GND to the daughter |
| J4 | DS1021-2x12SF11-B male header | C7430408 | 24 | 2.54 mm THT, signal |
| J2 | 1x6 2.54 mm header (recovery) | C7430362 | 6 | 2.54 mm THT. See OI note below - sits under the daughter |
| D2 | ABS210 2A 1000V bridge (Alt A) | C2892567 | 4 | THT bridge, PoE Mode A rectifier |
| D3 | ABS210 2A 1000V bridge (Alt B) | C2892567 | 4 | THT bridge, PoE Mode B rectifier |
| | **Total** | | **72** | of which **52** are on the five non-magjack parts |

**Why these are THT and not a choice we can undo:** CAR-REQ-17 requires a working
voltage above 57 V on the expansion connector. Every 0.4-1.0 mm mezzanine family JLC
stocks rates only 50-60 V (Panasonic AXK 60 V, Hirose FX10/BM22 50 V, Molex 50 V,
TE 50 V); the only compliant fine-pitch option, Samtec QTH/QSH at 175 V, costs
~15 USD per mated pair against a ~30 USD/carrier target. The 2.54 mm CONNFLY DS1021
line rates 250 V male / 600 V socket = **4.4x margin**. So the connector class is
forced, and with it the THT count. Recorded at P2.

**Confirm at the cart, do not assume:** the parts JSON files carry pad counts but no
JLC "Assembly Type" field, so which of D2/D3/J2/J3/J4 JLC treats as *wave* versus
*hand* soldering is **not verifiable from our data**. J1's wave-solder status is on
record from the P3 sourcing decision. Expect a hand-solder line item on the 2.54 mm
connectors - that was flagged as unavoidable at P2 - and read the real figure off the
JLC cart.

## Feeder / part-class exposure

- **47 of 111 placements are Extended parts** -> the estimate carries **141.00 USD**
  of feeder fees (47 x 3.00), which is **the single largest line in the assembly
  estimate** and larger than the bare PCB cost.
- **`order_quote` is known to UNDERCOUNT Extended feeder fees** (recorded skill
  limit). Treat 141.00 USD as a floor, not a figure.
- **C334927 (63.4 R) is deliberately NOT FITTED.** It is the 802.3at class-4 upgrade
  resistor and exists as a BOM line with zero placements so the "resistor change, no
  respin" promise of D-01 stays real. It must survive into any re-generated BOM - a
  BOM sync silently deleted it once already, which is why `bom_sync.py` now preserves
  `not_fitted` lines. **Do not let a vendor tool drop it.**

## Assembly-time cautions

- **Polarity preview is mandatory, not optional.** `bom_cpl.py` applied **5 rotation
  corrections**. Rotation is the classic JLC failure mode, so the rendered part
  preview must be eyeballed for every polarized part (LEDs D30/D31/D32/D40/D41/D42,
  diodes, the two THT bridges) before paying.
- **M3 hardware at the four corner holes must be small.** ICD rev A7 s7.1.1: at a
  3.0 mm inset against a 3.0 mm corner radius the hole wall is **1.3966 mm** from the
  board edge, so a standard 7.0 mm OD washer or a 5.5 mm A/F standoff flange
  **overhangs the rounded corner**. Use <= 5.0-5.5 mm OD hardware. The 5th hole at
  (46, 74) takes ordinary M3.
- **The recovery header J2 and the boot switch SW1 sit under the daughter board**
  (P8 reviewer finding, warning-severity, accepted). If a unit needs firmware
  recovery, the daughter has to come off first. Consider fitting J2 only on boards
  kept for bring-up, or plan a cable.
