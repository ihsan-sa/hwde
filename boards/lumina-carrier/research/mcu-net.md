# Component scout: `mcu-net` (ESP32-S3 + W5500 + PoE magjack + 25 MHz crystal) - LUM-CAR-A

Source requirements: `boards/lumina-carrier/architecture/requirements.md` (CAR-REQ-03/04/05/20,
section 2 interfaces, section 3.2 power budget, Q7/Q8/Q11/Q12/Q14/Q15).

Method: `parts_search.py` live JLCPCB endpoint (`source: "live"` on every query, no `--db`
fallback needed). Every datasheet claim below was pulled from the PDF and read - magjack
schematics via the `wmsc.lcsc.com` PDF mirror rendered as pages, W5500 and ESP32-S3-WROOM-1
datasheets parsed with pypdf. Nothing here is from memory. JLC assembly capability was
checked on the `jlcpcb.com/partdetail/<lcsc>` pages, not assumed.

Quantity basis: **14 boards** (Q15 default = 12 fixtures + 2 spares). Prices are USD, and the
"@14" column is the price break that actually applies at 14 pieces (usually the qty-10 tier;
crystals do not break until qty 50, so their @1 price applies).

---

## 0. Headline answer

| Sub-part | Pick | LCSC | @14 |
|---|---|---|---|
| MCU | **ESP32-S3-WROOM-1-N8** (module, 8 MB flash, no PSRAM) | C2913198 | $4.6428 |
| Ethernet controller | **W5500** | C32843 | $2.3804 |
| RJ45 PoE magjack | **HY931147C** (HanRun, THT, integrated bridge) | C91754 | $2.1480 |
| W5500 crystal | **X322525MRB4SI** 25 MHz / 18 pF | C70593 | $0.0951 |
| | **block subtotal** | | **$9.27/board** |

That is ~31 % of the Q15 default $30/board target consumed by four parts, before the PD front
end, the >= 60 V DC-DC, the expansion connector and all passives. Worth surfacing to the
architect now rather than at P3.

Two findings that change decisions rather than just informing them:

1. **The magjack everyone reaches for (HR911105A) cannot do PoE.** Verified from its own
   datasheet schematic, not from the parametric alone. Only **four** PoE-capable RJ45 magjacks
   exist on LCSC at all, and only one has real stock.
2. **The bare-chip route saves almost nothing at 14 units** - $0.16/unit against a module if you
   need external flash, $1.28/unit if you use the 8 MB-embedded ESP32-S3FN8 (which has 165 pcs
   in stock). Q7 should close as "module".

---

## 1. ESP32-S3 - module variants (CAR-REQ-03, Q7)

All ESP32-S3 modules and chips on LCSC are **Extended** (no JLC Basic option exists for any of
them), so the Basic-first tiebreak never fires in this sub-block; ranking is by fit, then
stock, then price.

| Rank | MPN | LCSC | Package | Basic | Stock | @1 / @14 | Rationale |
|---|---|---|---|---|---|---|---|
| **1** | **ESP32-S3-WROOM-1-N8** | C2913198 | SMD 25.5 x 18 x 3.1 mm | Extended | 6,895 | 5.3271 / **4.6428** | Exactly the Q7 default. 8 MB quad flash, **no PSRAM** -> IO35/36/37 stay free for the expansion connector, and ambient rating is **-40~+85 degC** instead of the R8 parts' +65 degC ceiling. Stock is 490x the build quantity. |
| 2 | ESP32-S3-WROOM-1-N16R8 | C2913202 | same | Extended | 50,238 | 5.4965 / 4.8785 | Deepest stock by far and only +$0.24/unit, but **-40~+65 degC ambient** (bad fit for a sealed enclosure sharing volume with a DC-DC - CAR-REQ-18 / Q13 default) and the octal PSRAM eats IO35/36/37. Take only if 8 MB flash is ruled too small. |
| 3 | ESP32-S3-WROOM-1-N4 | C2913197 | same | Extended | 5,951 | 4.6412 / 4.1571 | Cheapest WROOM-1, -40~+85 degC. But 4 MB flash is tight against the Q9 default (Ethernet OTA -> two app partitions + NVS). Saves $0.49/unit = ~$7 across the build. Not worth the OTA headroom. |
| 4 | ESP32-S3-MINI-1-N8 | C2913206 | SMD 15.4 x 15.4 x 2.4 mm | Extended | 4,086 | 5.0366 / 4.4605 | 40 % smaller footprint, $0.18/unit cheaper. **Not** footprint-compatible with WROOM-1, exposes a **subset** of the GPIOs (must be checked against this board's ~26-30 pin budget), and its LGA pads sit under the body (no visual joint inspection). Fallback if the floorplan gets tight. |
| 5 | ESP32-S3-WROOM-1U-N8 | C2980297 | SMD 19.2 x 18 x 3.2 mm | Extended | 1,352 | 5.1318 / 4.5960 | u.FL/MHF-I connector, **no PCB antenna, no keep-out**. Shares the WROOM-1 land pattern (the 1U is the same 18 mm-wide 40-pad pattern, just 6.3 mm shorter) so one footprint takes both. Only relevant if Q8 flips - see section 5. |

Other WROOM-1 variants with usable stock, not ranked because they are the same module with a
different memory mix: N8R2 (C2913204, 19,071, $4.8462), N16R2 (C2913205, 6,783, $4.1829),
N8R8 (C2913201, 9,012, $4.3282), plus the whole WROOM-1U family. Every `C99xxxxxxx` /
`C520xxxxx` "ESP32-S3-WROOM" hit is a JLCPCB-Assembly placeholder footprint entry at
$0.0393 with 0 stock - not real orderable parts, ignore them.

### 1a. Module vs bare chip - the actual number the architect asked for

| Route | Core parts @14 | Extra required parts | Unit total | Delta vs WROOM-1-N8 | Delta over 14 boards |
|---|---|---|---|---|---|
| **Module** ESP32-S3-WROOM-1-N8 | 4.6428 | none (flash, crystal, RF match, antenna all inside) | **$4.64** | - | - |
| Bare **ESP32-S3FN8** (C2913196, 8 MB embedded flash, QFN-56-EP) | 3.2615 | 40 MHz xtal C284179 $0.0756 + 2 load caps + RF pi-match (3 x 0402) ~$0.02 | ~**$3.36** | **-$1.28** | **-$18** |
| Bare **ESP32-S3** (C2913192, no flash) + external flash | 2.5482 | W25Q64JVSSIQ C179171 $1.8381 + 40 MHz xtal $0.0756 + match ~$0.02 | ~**$4.49** | **-$0.16** | **-$2** |

What the ~$2-18 module premium buys, all of which is otherwise added to a *first spin*:

- Pre-certified radio (FCC/IC/CE modular approval). Without it, section 8's "RF transmit -
  CONDITIONAL" flag becomes a certification work item, not a layout note.
- No 2.4 GHz impedance-controlled RF trace, no pi-match tuning, no antenna design/tuning.
- No 40 MHz crystal placement/ground-island work (Espressif's guidelines require a complete
  ground plane under RF and the crystal).
- No quad-SPI flash routing/length matching at 80 MHz.
- A part JLCPCB assembles routinely, versus a QFN-56-EP with a thermal pad.

Stock also argues for the module: the only 8 MB-embedded-flash bare chip (ESP32-S3FN8) has
**165 pcs**, which is a re-order hazard for a design meant to be built repeatedly. There is no
JLC Basic 64 Mbit SOIC-8 flash either (a `--basic-only` search returns empty), so the external
flash on the cheap route is also an Extended part at $1.84.

**Recommendation: close Q7 as "pre-certified module, WROOM-1-N8".** The saving does not exist.

---

## 2. W5500 (CAR-REQ-04)

| MPN | LCSC | Package | Basic | Stock | @1 / @14 / @30 | Verdict |
|---|---|---|---|---|---|---|
| **W5500** (WIZnet) | **C32843** | LQFP-48 (7x7, 0.5 mm) | **Extended** | **34,016** | 2.7354 / **2.3804** / 2.1286 | The only orderable W5500 on LCSC. In stock, deep. |
| W5100S-L | C194673 | LQFP-48 (7x7) | Extended | 4,816 | 2.4417 / 2.0899 | **Not a drop-in.** Different pinout and different register map / SPI framing. Swapping = schematic + firmware respin. |
| W6100 | C911393 | LQFP-48 (7x7) | Extended | 1,668 | 4.4137 / 3.8085 | **Not a drop-in.** WIZnet documents the W6100 as PIN-2-PIN compatible with the **W5100S**, not the W5500 (confirmed on WIZnet's own store listing and developer forum). |
| ENC28J60 (all packages) | C47351 / C411626 / C57281 ... | SOIC-28 / SSOP-28 / QFN-28 | Extended | 62-189 each | 3.25-5.21 | 10 Mbit only, different package and different driver. Stock under 200 on every variant. Not a candidate. |

Every other "W5500" search hit is a 0-stock placeholder or a breakout module (`W5500_Module`,
`W5500io-M`, `W5500Lite`), not the IC.

**Is it Basic? No - Extended**, so it carries a feeder fee. There is no Basic Ethernet
controller of any kind.

Design facts pulled from the W5500 datasheet v1.1.0 that P2/P3 will need:

- 3.3 V on VDD and AVDD; internal 1.2 V regulator with a `1V2O` output pin and a `TOCAP`
  decoupling pin - both need caps, they are not no-connects.
- **12.4 k 1 %** from `EXRES1` (pin 10) to AGND. Mandatory, it sets the PHY bias current.
- SPI mode 0 and 3, **rated to 80 MHz** by the feature list. Gate 5's "SPI clock inside the
  W5500 maximum" check is therefore trivially satisfiable at any ESP32-S3 SPI rate; the real
  constraint will be the shared-bus routing, not the chip. Note: the **Variable Length Data
  Mode** (host-controlled SCSn) is the mode that permits sharing the SPI bus with other
  devices - Fixed Length Data Mode dedicates the bus. The expansion connector shares SPI
  (section 2.1), so **VDM is mandatory**; worth writing into the schematic notes.
- 5 V-tolerant inputs (VIH max 5.5 V).
- Four dedicated active-low LED outputs: SPDLED, LINKLED, DUPLED, ACTLED. Relevant to Q11 -
  see section 3.
- `RSVD` pins 23 and 38-42 must be tied to GND / left per datasheet, not floated.

**Single-source risk: HIGH, and it is the highest in this block.** One orderable part number,
one manufacturer, no pin-compatible alternate anywhere on LCSC. Mitigation is procurement, not
design: 34 k in stock is deep, but buy the W5500s with the board order rather than assuming
availability at re-order time. If the architect wants a real second source, that means
committing to a *different* controller family up front (W5100S) with different firmware - a P2
decision, not a P3 substitution.

---

## 3. RJ45 magjack, data + PoE (CAR-REQ-05, CAR-REQ-20, Q11, Q12)

### 3a. The rejection that matters

**HR911105A (C12074) is not PoE-capable.** It is the highest-stock (48,280), cheapest
($1.5509 @14) magjack on LCSC and the default in most ESP32/W5500 hobby designs, so this needs
to be explicit. Its datasheet schematic has **no power pins at all**: chip-side P4/P5 are
winding centre taps intended for bypassing only, P7 is NC, P8 is chassis GND, and the spare
pairs J4/J5/J7/J8 terminate into the internal 4 x 75 ohm + 1000 pF/2 kV Bob Smith network.
There is nowhere to take PD power from. LCSC's own parametric agrees: `PoE = "Non-PoE"`.

The same rejection applies to every other high-stock HanRun jack, all parametrically
"Non-PoE" and all confirmed as ordinary NIC magjacks: HR911130A (C54408, 9,942),
HY951180A (C34677, 8,823), HR911130C (C50933, 4,226), HR961160C (C55683, 2,672),
HR871181A (C49312, 1,804), HY911130A (C55679, 1,539), HY911102A (C21842, 489).

Scanning ~225 distinct RJ45 listings, **exactly four** carry `PoE = "With PoE"`.

### 3b. The four real candidates

| Rank | MPN | LCSC | Basic | Stock | @1 / @14 | Power take-off topology | Isolation | LEDs | JLC assembly |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **HY931147C** (HanRun) | **C91754** | Extended | **7,693** | 2.5643 / **2.1480** | **Integrated rectifier**, out to **V+ (P9) / V- (P10)** | 1500 Vrms | Yellow left (585 nm) + Green right (568 nm), 20 mA, Vf 1.8-2.8 V | **Yes - Wave Soldering** |
| 2 | HR871150C (HanRun) | C19724786 | Extended | **209** | 2.0544 / 1.7397 | **Four raw centre taps**: VC1+ (P7), VC1- (P8), VC2+ (P9), VC2- (P10). External bridges required. | **2250 VDC** | same | **Yes - Wave Soldering** |
| 3 | HR861153C (HanRun) | C19724782 | Extended | 471 | 2.6870 / 2.2738 | Integrated "TBBS" bridge, out to V+ (P9) / V- (P10); GND on P7, P8 NC | **2250 VDC** | same | **Yes - Wave Soldering** |
| 4 | LPJG0926HENL (Link-PP) | C22457393 | Extended | 3,111 | 4.4056 / 3.7892 | **UNVERIFIED** - LCSC carries no datasheet | unknown | "With LED", colours unknown | not checked |

Common to all three HanRun parts, from their datasheets:

- **350 uH minimum OCL @ 100 kHz / 100 mV with 8 mA DC bias** - this is the IEEE 802.3
  magnetics requirement under PoE DC bias, and it is what separates these from the "Non-PoE"
  jacks. All three state "Meets or exceeds IEEE802.3af standards including 350uH Min OCL with
  8mADC".
- THT, right-angle, tab-down, shielded, UL recognised (file E330599 on the HR parts).
- Body: 16.00 mm wide x 21.2-21.6 mm max deep x ~15 mm high; footprint is 10 signal holes
  (0.89 mm) + 4 LED pins (1.02 mm) + 2 x 3.25 mm + 2 x 1.63 mm posts on a ~15.5 x 10.9 mm
  pattern. Suggested panel cutout for this HanRun body style is **16.54 x 14.00 mm**.
- LEDs are **yellow (left) and green (right)**, 20 mA, Vf 1.8-2.8 V - so Q11's default (b)
  "the RJ45's own LEDs plus one status LED" is satisfiable with exactly two colours. The W5500
  gives four active-low LED outputs (LINK, SPD, DUP, ACT), so the two jack LEDs are a
  free choice of any two of those, or one from the W5500 and one firmware-driven from the
  ESP32-S3.

### 3c. THT and JLC assembly - the explicit answer

**JLCPCB can place all three HanRun candidates.** Each part page reports
`Assembly Type: Wave Soldering`, `PCBA Type: Economic and Standard`. They are **not**
hand-solder-only parts. The cost is JLCPCB's through-hole surcharge -
**$3.50 hand-soldering labour + $0.0173 per joint** - i.e. ~18 joints on this connector is
about **$0.31/board plus a one-off $3.50**, and one extra build day. Negligible against the
build. So Q12's default (board-edge THT magjack) survives the assembly question.

Caveat worth carrying: mixing THT with SMT means the board sees both processes; if any other
THT part is added later on the **bottom** side, that combination is what actually breaks
JLC's flow, not the magjack alone.

### 3d. Recommendation and the decision it forces on P2

**HY931147C (C91754) is the stock-safe pick** and the only PoE magjack with real depth. But
the choice is not purely commercial - the two topologies are electrically different and the
architect has to pick one:

- **Integrated bridge (HY931147C, HR861153C):** V+/V- arrive pre-rectified. Fewer parts,
  simpler PD front end, polarity and Mode A/B handled inside the jack. **But neither datasheet
  states a current or thermal rating for the internal bridge**, and you cannot choose the
  diodes (no low-Vf or ideal-diode option, no control over the ~1.4 V bridge drop at 25 W).
- **Raw four centre taps (HR871150C):** the textbook PD arrangement - the PD front end owns its
  own Mode A and Mode B bridges, so every rating is explicit. It is the **only** candidate that
  publishes a power rating: *"Designed To Support 57VDC, 350mA per centre taps (17.5W when
  using 2 centre taps; 35W when using 4 centre taps)"*. Note what that says about **D-01**: a
  2-centre-tap (single-mode) design caps at 17.5 W, which is **below** the 802.3at 25.5 W the
  Type 2 power stage is meant to reach. Only the 4-centre-tap arrangement (35 W) gets there -
  and 4 centre taps is what 802.3 compliance requires anyway (Mode A + Mode B, either
  polarity, per the `ASSUMED:` in requirements section 2.2).

So: if the PD controller's reference design wants raw centre taps into its own bridges - which
the Si3402-B class of parts does - **HR871150C is the electrically correct part, and its 209
pcs of stock is a procurement emergency, not a preference.** 209 pcs covers ~14 boards with
zero spares and no re-order headroom.

Mechanically the three HanRun parts share the same 10+4-pin footprint, so **one footprint can
accept either topology** - but P7/P8 change meaning (VC1+/VC1- on HR871150C vs GND/NC on
HR861153C), so the *netlist* differs. If P2 wants insurance, design the PD front end so both
stuffings are possible (external bridges fitted, bypassed when an integrated-bridge jack is
used). That is a cheap hedge against the single-source problem below.

**Single-source risk: HIGH.** Four PoE magjacks exist on LCSC; three are from one manufacturer
(HanRun) and the fourth is undocumented. Within a chosen topology there is effectively one
part with stock. This is the second-riskiest line in the block after the W5500.

---

## 4. 25 MHz crystal for the W5500

The requirement, quoted from **W5500 datasheet v1.1.0, section 5.5.3 Crystal Characteristics**
(read from the PDF, not memory):

| Parameter | Range |
|---|---|
| Frequency | 25 MHz |
| Frequency tolerance (at 25 degC) | **+/-30 ppm** |
| Shunt capacitance | 7 pF max |
| Drive level | 59.12 uW |
| **Load capacitance** | **18 pF** |
| Aging (at 25 degC) | +/-3 ppm/year max |

| Rank | MPN | LCSC | Package | Basic | Stock | @1 / @50 | CL | Tol @25 degC / stability | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **X322525MRB4SI** (YXC) | **C70593** | SMD3225-4P | Extended | 34,358 | 0.0951 / 0.0753 | **18 pF** | +/-10 ppm / +/-20 ppm (-40~+85 degC), ESR 50 ohm | Exactly the datasheet CL, 3x margin on tolerance. |
| 2 | XL2EL89CRI-111YLC-25M (YXC) | C19078191 | SMD3225-4P | Extended | 14,107 | 0.0856 / 0.0688 | 18 pF | +/-10 ppm / +/-20 ppm, ESR 50 ohm | Identical parametrics, cheaper, same footprint -> **true drop-in second source**. |
| 3 | X322525MOB4SI (YXC) | C9006 | SMD3225-4P | **BASIC** | 231,198 | 0.0956 / 0.0764 | **12 pF** | +/-10 ppm / +/-20 ppm, ESR 50 ohm | The only **JLC Basic** 25 MHz crystal. See tradeoff below. |
| 4 | 7M25000014 (TXC) | C90912 | SMD3225-4P | Extended | 5,016 | 0.1773 / 0.1406 | 18 pF | +/-10 ppm / **+/-10 ppm** | Tightest stability, but only **-10~+70 degC** and 1.9x the price. No benefit - W5500 only asks +/-30 ppm. |

**The Basic tradeoff (C9006):** it is the same manufacturer, same SMD3225-4P footprint, same
ppm grade, 231 k in stock, and it is the *only* way to avoid an Extended feeder fee on this
line - but its CL is **12 pF, not the 18 pF the W5500 datasheet specifies**. It is usable if
the external load caps are re-computed (roughly 2 x (12 - Cstray) ~ 18 pF each instead of
2 x (18 - Cstray) ~ 30 pF each), but it moves the oscillator's gain margin away from the value
WIZnet characterised. Given the crystal is $0.095 either way, the feeder fee is the only
argument, and a mis-tuned 25 MHz reference on the PHY is a nasty class of intermittent
Ethernet fault. **Recommend C70593 (18 pF); if P3 takes C9006 for the Basic status, it must be
raised explicitly at schematic sign-off.**

Note the 3.2 x 2.5 mm 4-pad package is shared by ranks 1-4, so one footprint covers all
sources. **Single-source risk: LOW** - two 18 pF parts plus a Basic 12 pF part, all drop-in
mechanically.

---

## 5. Antenna keep-out - does the module choice constrain the floorplan? (yes)

**Yes, and it is a permanent constraint because of MECH-02.**

From the ESP32-S3-WROOM-1/1U datasheet v1.8:

- WROOM-1: **25.5 x 18.0 x 3.1 mm**. WROOM-1U: **19.2 x 18.0 x 3.2 mm**. The **6.3 mm**
  difference is exactly the PCB-antenna section. The pin-layout figure labels that end
  "**Keepout Zone**" and notes it is present on WROOM-1 and absent on WROOM-1U; the recommended
  land pattern labels it "**Antenna Area**". So the keep-out is approximately
  **6 x 18 mm at the module's antenna end** - no copper, no plane, no traces, any layer.
- The datasheet defers the placement rule to *ESP32-S3 Hardware Design Guidelines > General
  Principles of PCB Layout for Modules*, which requires: place the module **as close to the
  base-board edge as possible**; the PCB antenna should **extend beyond the base board**
  wherever possible, feed point closest to the board; if it cannot overhang, **cut the base
  board away on both sides of and below the antenna**; **never** place the module in the board
  centre with a four-sided hollow; and put solid ground copper with dense ground vias on the
  base board *near* (not under) the antenna.

Consequences that land on P2 and P5:

1. **P2 floorplan** must reserve one board edge, ~18 mm wide, for the module, with the antenna
   end overhanging or relieved.
2. **P5 outline is permanent** (`board_init.py --outline WxH`, no shrink step, MECH-02). If the
   antenna needs an overhang or a cut-out, that geometry has to be in the outline from the
   first `board_init` call. This is the single most expensive thing to get wrong here.
3. **Conflict with the RJ45.** The magjack is also an edge part (Q12 default: board-edge THT
   through a cutout, CAR-REQ-20), it is 16 mm wide, and it has a **shielded metal shell plus a
   metre of shielded cable hanging off it**. It must not share an edge with the antenna. Put
   them on different edges - ideally opposite.
4. **Conflict with the mounting holes.** Q3's default is 4x M3 inset 5 mm from each edge. A
   corner hole plus its annulus and keep-out competes with the antenna relief for the same
   corner. Check at P2, not at P5.
5. **Enclosure.** Q8's default ("radio unused but keep it functional") only holds if the
   enclosure is non-metallic, which is consistent with Q5's default. If either flips, the
   antenna is decorative.

**If Q8 closes as "radio permanently unused", switch to ESP32-S3-WROOM-1U-N8 (C2980297) and fit
no antenna.** That removes 6.3 mm of module length *and* the entire keep-out, frees a board
edge for the connector or the DC-DC, and costs $0.05/unit less than the WROOM-1-N8. Because the
WROOM-1 and WROOM-1U land patterns are the same 18 mm-wide 40-pad pattern (1U just ends
sooner), a WROOM-1 footprint physically accepts a 1U - so **leaving Q8 open is survivable, but
the outline decision is not reversible.** Raise Q8 before H1, not after.

---

## 6. Current draw (for the power architect)

All at 3.3 V. ESP32-S3 figures from the WROOM-1/1U datasheet v1.8 sections 6.2/6.4; W5500
figures from datasheet v1.1.0 sections 5.3/5.4. **TX currents are rated at 100 % duty cycle;
RX currents with peripherals disabled and CPU idle.**

| Part | Condition | Typ/Peak | Power |
|---|---|---|---|
| ESP32-S3-WROOM-1 | **Wi-Fi TX 802.11b, 1 Mbps @20.5 dBm** | **355 mA peak** | 1.17 W |
| | Wi-Fi TX 802.11g, 54 Mbps @18 dBm | 297 mA | 0.98 W |
| | Wi-Fi TX 802.11n HT20 MCS7 @17.5 dBm | 286 mA | 0.94 W |
| | Wi-Fi RX 802.11b/g/n HT20 | 95 mA | 0.31 W |
| | BLE TX @20 dBm / RX | 344 mA / 93 mA | 1.14 / 0.31 W |
| | Modem-sleep 240 MHz, dual core 32-bit, periph clocks **on** | 81.3 mA | 0.27 W |
| | Modem-sleep 160 MHz, dual core 32-bit, periph clocks **on** | 64.1 mA | 0.21 W |
| | Modem-sleep 160 MHz, WAITI, periph clocks off | 27.6 mA | 0.09 W |
| | Light-sleep | 240 uA | - |
| | Deep-sleep (RTC memory up) | 7-8 uA | - |
| | **Datasheet requirement: external supply must deliver >= 0.5 A** | - | - |
| W5500 | **100M transmitting** | **132 mA** | 0.44 W |
| | 100M link | 128 mA | 0.42 W |
| | 10M link / 10M transmitting | 75 / 79 mA | 0.25 / 0.26 W |
| | Un-link (auto-negotiation) | 65 mA | 0.21 W |
| | Power-down mode | 13 mA | 0.04 W |
| Magjack LEDs | 2 LEDs, Vf 1.8-2.8 V, 20 mA max each | 2 x ~5-10 mA driven | ~0.05 W |
| Crystal + 12.4 k bias | - | negligible | - |

Two numbers the power architect should carry forward:

- **Normal operation (radio off, Ethernet at 100M, CPU at 160-240 MHz driving 8 PWM
  channels):** ESP32-S3 ~64-81 mA + W5500 ~128-132 mA + LEDs ~15 mA = **~210-230 mA at 3.3 V =
  0.70-0.76 W**. That fits inside the 1.5 W carrier-overhead allocation (requirements section
  3.2) - but it leaves only ~0.75 W for **both** conversion stages' losses on the 48 -> 12 ->
  3.3 chain. The 1.5 W allocation is already flagged as judgement in `00`; this block alone
  eats half of it, and that is before the PD front end's own quiescent draw. **Flag to the
  power architect: the 1.5 W budget is tighter than it looks.**
- **Peak sizing for the 3.3 V rail:** if Q8 keeps the radio functional, the rail must survive
  **355 mA Wi-Fi TX + 132 mA W5500 = ~490 mA, ~1.6 W burst**, and Espressif independently
  requires the supply to be capable of **>= 0.5 A**. So the 3.3 V regulator is a >= 0.5 A part
  regardless of average draw. If Q8 closes as "radio permanently dead in firmware", the peak
  drops to ~230 mA and a smaller 3.3 V stage becomes legitimate - **another reason Q8 is not a
  cosmetic question.**

---

## 7. Single-source risk summary

| Sub-part | Risk | Detail |
|---|---|---|
| ESP32-S3 module | **LOW** | Four WROOM-1 flash/PSRAM variants with >5,000 stock each, plus MINI-1 and the WROOM-1U family. WROOM-1 and WROOM-1U share a land pattern (1U is 6.3 mm shorter on the same 18 mm-wide 40-pad footprint), so one footprint covers both. MINI-1 does **not** share it. |
| **W5500** | **HIGH - hard single source** | Exactly one orderable part (C32843). **No pin-compatible alternate exists on LCSC**: W6100 is pin-compatible with the W5100S (confirmed with WIZnet), W5100S-L has a different pinout and register map, ENC28J60 is 10 Mbit with <200 stock. A second source means a different chip and different firmware - a P2 architecture decision, not a P3 substitution. Mitigation: 34 k stock is deep; buy with the board order. |
| **PoE magjack** | **HIGH** | Only 4 PoE-capable jacks exist on LCSC; 3 are HanRun and the 4th (LPJG0926HENL) has no datasheet. Within a chosen topology there is effectively one stocked part. The integrated-bridge and raw-centre-tap variants share a footprint but not a netlist - design the PD front end to accept both if insurance is wanted. |
| 25 MHz crystal | **LOW** | Two identical 18 pF parts (C70593, C19078191) plus a Basic 12 pF part (C9006), all SMD3225-4P, all drop-in mechanically. |

---

## 8. Open questions for the architect

1. **Q7 - close it as "module".** The bare-chip saving is $2-18 across the entire build and buys
   RF layout plus certification risk. Recommend ESP32-S3-WROOM-1-N8 (C2913198).
2. **Q8 is load-bearing on the outline, not just on the enclosure.** "Keep the radio functional"
   costs a ~6 x 18 mm edge keep-out that must be baked into the permanent P5 outline, plus a
   >= 0.5 A 3.3 V rail. "Radio permanently unused" swaps to WROOM-1U-N8 and frees both. Needs
   answering before H1.
3. **Which PoE magjack topology?** Integrated bridge (HY931147C, 7,693 pcs, stock-safe) or raw
   four centre taps (HR871150C, **209 pcs**, the only one with a published 35 W rating and the
   only one that clearly supports D-01's 802.3at upgrade path). This depends on the PD
   controller's reference design and should be decided together with it - and if it is
   HR871150C, the parts must be bought now.
4. **Does the two-LED colour set (yellow + green) satisfy Q11?** The jack gives exactly two, and
   the W5500 offers four LED outputs (LINK/SPD/DUP/ACT). Q11's default adds one more status LED
   beside the cutout for power-good/fault. Confirm the mapping so P2 can allocate the pins.
5. **This block is $9.27/board of a $30 target.** Confirm the Q15 cost target is real before P3
   commits, because the PD front end plus a >= 60 V DC-DC will not be cheap.
