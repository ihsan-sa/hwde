# LUM-CAR-A - P2 decisions of record

For the orchestrator's decision log and for H1. Every entry is a decision the human can overturn;
none is a preference. `D-A*` = architecture decision. `TRAP-*` = a verified pipeline behaviour that
will bite a later phase. `OPEN-*` = something P2 could not settle.

---

## Headline decisions

| ID | Decision |
|---|---|
| **D-A0** | **Stackup `JLC04161H-3313`, 4 layers, 1 oz outer.** In1 = solid GND, In2 = +3V3. Forced by the 100 ohm MDI (a 2-layer solution is 1.081 mm per leg) and by reference-plane discipline; vendor guidance from TI and Skyworks agrees independently. Thermals are supporting, **not** decisive - `research/power.json`'s claim that the converter forces 4 layers treated the whole converter block as one refdes; split across U20/D20/L20 no single part is thermally decisive. |
| **D-A1** | **Reject the Skyworks Si3402-B/-C AND Si3404 family. Lead PD interface: TPS2378 class.** Si3402-B/-C and Si3404 are IEEE 802.3 **Type 1 only**; the Si3402-B datasheet's revision history explicitly *deleted* its former Class 4 claim. No resistor change reaches Type 2, so they make D-01's "resistor change, no respin" impossible. Skyworks' real PoE+ parts (Si3406/Si34061/Si34062) are effectively unstocked (0-37 units). |
| **D-A2** | **Magjack: integrated-bridge PoE type (HanRun HY931147C class). No external bridges on the board.** Second source HR861153C (same 10+4 footprint, same V+/V- positions). |
| **D-A3** | **Carrier overhead is 2.4 W (af) / 3.7 W (at), not the brief's 1.5 W.** And the "~10 W regulated" figure in requirements 3.2 is discarded outright. |
| **D-A4** | **Power topology: strategy (b) - separate PD interface + external 100 V buck.** Lead pair TPS2378 class + SCT2A25 class, plus a TPS563201-class synchronous buck for 12->3.3. |
| **D-A5** | **Non-isolated buck confirmed (Q5 default adopted), with the compliance consequences written into the ICD.** |
| **D-A6** | **48 V raw is three different numbers: connector pins 5.4 A, hardware limit 1.0 A latch-off, ICD sustained 0.25 A (af) / 0.50 A (at).** Plus a **+12V at-ceiling of 1.25 A** set by the converter's thermal budget. |
| **D-A7** | **Expansion connector: SPLIT - 2x7 power + 2x12 signal, 2.54 mm THT CONNFLY DS1021/DS1023.** Carrier male, daughter socket. Full ICD in `connector-icd.md`. |
| **D-A8** | **Common LUMINA footprint: 100.0 x 80.0 mm, 3 mm corner radius, 4x M3 at 5 mm inset + a 5th M3 at (46, 74). Stack height 11.0 mm.** |
| **D-A9** | **Q7 closes as MODULE: ESP32-S3-WROOM-1-N8, and the SKU is frozen** (GPIO35/36/37 and 47/48 are in use). |
| **D-A10** | **The daughter SPI is a separate bus (SPI3), not shared with the W5500's SPI2.** |
| **D-A11** | **Keep In1 GND continuous under the magjack.** WIZnet's blanket "no plane under the connector" rule loses to Pulse's integrated-connector-module exception plus the pipeline's own checker semantics. |
| **D-A12** | **PWM allocation: 4 channels on LEDC timer 0 + 4 on timer 1; timers 2 and 3 unallocated.** Works for either answer to D-04. |

---

## The conflicts, resolved explicitly

### D-A1 - the brief's named PD part is disqualified, and the power budget with it

**Conflict:** requirements 3.2 sources its whole power chain from Skyworks AN956, which describes the
Si3402-B. `research/refdesign-poe-pd` and `research/poe-power` independently established that the
Si3402-B/-C is "IEEE 802.3 Type 1 (Class 3 and below)" and that Si3404's datasheet says verbatim
"The Si3404 is a Type 1 PD" with "Removed Type 2 signaling from diagram" in its revision history.

**Resolution.** The Si3402/Si3404 family loses, and so does every number derived from it:
- **the "~10 W regulated available" figure is deleted**, not adjusted. It is a Type-1 statement about
  an isolated flyback at ~77 % end-to-end, describing a part this board cannot use.
- The whole af/at budget is **re-derived from the selected parts** in `power_tree.md` s2, which lands
  at **8.61-9.28 W (af) / 18.70-20.00 W (at)** to the daughter - i.e. D-01's 8.5 W / 18.5 W
  allocation survives with margin rather than by assumption.
- **Watched consequence:** three components can silently pin this design to Type 1 and must be
  treated as carefully as the class resistor - (a) the PD controller (resolved by D-A1), (b) the
  magjack's tap rating (**unresolved**, OPEN-A), (c) the 48->12 converter and its copper, which must
  be laid out for the *at* dissipation even though build 1 never produces it.

### D-A2 - magjack topology: integrated bridge wins, and HR871150C is disqualified

**Conflict:** `research/mcu-net` framed this as stock-safety (HY931147C, 7693 pcs, integrated bridge,
no published bridge rating) versus electrical explicitness (HR871150C, 209 pcs, raw four centre taps,
**the only candidate publishing a rating**).

**Resolution: HY931147C class. HR871150C is rejected on the rating it publishes, not despite it.**
Its rating is *"57 VDC, 350 mA per centre tap - 17.5 W when using 2 centre taps, 35 W when using
4"*. **A PSE energises exactly one mode**, which uses two centre taps, so the real ceiling is
**17.5 W - below 802.3at's 25.5 W.** It is an af-only magjack and cannot serve D-01. Separately,
209 pcs is 14 boards with zero spares.

Consequences, all of them wins except the last:
- No external bridges, no `POE_TAP_*` nets. **48 V enters on two pins instead of four**, removing the
  hardest creepage region (48 V within millimetres of the MDI pads) and ~550 mm2 of board area.
- The bridge Vf (~1.4 V, 0.84 W at the at point) is no longer selectable and is dissipated **inside a
  plastic connector body with no heatsink path**, in air that reaches 56-69 C. Accepted; see OPEN-A.
- The internal bridge's incremental resistance sits in series with the detection path, so **RDEN may
  need trimming upward** from 24.9 k at P3/P4 rather than being ported blindly.

### D-A3 - carrier overhead: three numbers measuring three different things

| Source | Number | Measures |
|---|---|---|
| brief `00` s5.1 | 1.5 W | intended as the full overhead; omits the input bridge and double-counts the converter against AN956's already-net figure |
| `research/mcu-net` | 0.70-0.76 W | **+3V3 silicon only** - one term inside the overhead, not the overhead |
| `research/power` | 2.44 / 3.75 W | the real input-minus-delivered figure |

**Resolution: 2.4 W (af) / 3.7 W (at)**, independently reproduced as 2.39 / 3.70 W in
`power_tree.md` s2 from the selected parts. The +3V3 silicon term is **0.78 W** (mcu-net's measured
0.70-0.76 W of silicon plus 20 mA of LEDs and 5 mA of pull-ups - the two agree within 3 %). The
brief's 1.5 W is ~60 % low and **must not be carried into any daughter budget.** All figures remain
judgement figures until measured on the first prototype.

### D-A5 - non-isolated, and what it costs

**Adopted (Q5 default).** Two decisive facts, neither of them cost:
1. **There is no 12 V-secondary PoE PD flyback transformer in the JLCPCB catalogue.** The only
   stocked family has a 5 V / 2.2 A secondary; the 12 V variants are at 0-20 units. Isolation
   therefore breaks the section 7 single-order PCBA assumption and adds a qualification task with no
   in-catalog answer.
2. **Every Type-2 PD IC on JLC that integrates a converter is transformer-based.** So "integrated PD +
   converter" is simply **not available at Type 2 with a buck**, which is what forces D-A4's two-chip
   answer.
Supporting: isolated costs ~10 points on the first stage, dropping af margin from 15 % to 4.6 %.

**What the whole system inherits, and it is load-bearing:** non-conductive enclosure, no chassis
earth, **Ethernet as the only external connection** - which kills Q9 option (a), USB-C on every
fixture - and everything downstream of the expansion connector floating at PoE potential, including
the daughter's LED wiring. Written into `connector-icd.md` s9.

### D-A6 - the 48 V current numbers

Q6's "2 A continuous / 3 A capability" reads as a rail spec. **2 A at 48 V is 96 W on a 12.95 W (af) /
25.5 W (at) supply.** Resolution, adopting `research/power`'s proposal and adding the +12V half:

| | Value | Basis |
|---|---|---|
| Connector pin capacity | **5.40 A** (3 pins x 1.80 A derated) | keep - cheap, thermally generous, clears CAR-REQ-13 by 80 % |
| Hardware fault ceiling | **1.0 A, latch off** | eFuse ILIM; the PD interface's own hot-swap handles 0.85 A continuous with a ~1.0 A limit |
| ICD sustained, `+48V_SW` | **0.25 A (af) / 0.50 A (at)** | the whole light-engine envelope taken on this one rail at the low-line corner |
| ICD sustained, `+12V` | **0.75 A (af) / 1.25 A (at)** | **the at figure is a thermal number**, not a connector number: above 1.25 A the 48->12 converter exceeds its `check_thermal` allowance in a sealed box. Excess must be taken on `+48V_SW`, which is where the free watts are |
| ICD sustained, `+3V3` | **0.25 A** | deliberate deviation from Q6's 0.5 A: 0.5 A of 3.3 V is 1.65 W = **19 % of the whole af light-engine budget spent on daughter logic**. The converter is still rated 1.0 A, so raising it later is a documentation change, not a hardware one |
| **Total, all rails** | **8.5 W (af) / 18.5 W (at)** | the binding number. The per-rail ceilings deliberately do not sum to it |

### D-A11 - the plane void under the magjack

**Conflict:** WIZnet says void all planes under the transformer and RJ45; TI scopes the same rule to
*discrete* magnetics; Pulse says the opposite for *integrated connector modules*.

**Resolution: keep In1 GND continuous under the magjack; void only In2 (+3V3).** WIZnet loses
because (a) our part is an integrated connector module - Pulse's stated exception; (b) with a
non-isolated PD there is no chassis ground to island, so the void would isolate nothing from nothing;
(c) with integrated magnetics there is no cable-side copper on the board, so the 1500 Vrms concern
has nothing to hold off; and decisively (d) **a void near the MDI pads is the most likely unwaivable
P8 failure on this board** - `check_return_path` raises an *error* on any corridor deficit,
`gate.py` has no waiver, and `planes_gen` supports only rectangular positive regions, so the void
would have to be built with zero tolerance against the pad row. This closes
`research/interface-ethernet`'s OPEN-2.

### Q7 / Q8 - close Q7 now, escalate Q8

- **Q7 (module vs bare chip) should be closed as "module".** The bare-chip saving is **$2 to $18
  across the entire 14-board build** and it buys 2.4 GHz RF layout, a pi-match, antenna tuning,
  80 MHz quad-SPI flash routing and modular-certification risk. Research produced better evidence
  than the provisional default; **recommend closing it.**
- **Q8 (must the radio work) is load-bearing on the permanent outline, not just on the enclosure.**
  "Keep it functional" costs a 10 x 22 mm no-copper board-edge keepout and a >= 0.5 A 3.3 V rail.
  "Permanently unused" swaps to WROOM-1U-N8 on the same land pattern and frees both. **Must be
  answered at H1, not after.**

---

## Rejected, with reasons

| Rejected | Reason |
|---|---|
| Si3402-B / Si3402-C / Si3404 | Type 1 only. Cannot satisfy D-01 (D-A1) |
| TPS2372 / TPS2373 | **Two** class resistors (CLSA + CLSB) turns D-01's single-part upgrade into a two-part change. Their auto-MPS feature is not worth that |
| HanRun HR871150C magjack | 17.5 W single-mode ceiling - af only (D-A2) |
| HanRun HR911105A + 7 other high-stock jacks | parametrically `Non-PoE`; no centre taps on package pins. Only **four** PoE magjacks exist on LCSC at all |
| LM5164 (48->12) | 1 A x 12 V = 12 W. Covers af, fails at, and D-01 forbids a respin at the upgrade |
| TPS54360 / TPS54560 / LM5160 / MP4560 / SCT2432 / LM2596 / LMR33630 | input rating 36-65 V against a 57 V worst case. LM2596 and LMR33630 are named exclusions in the brief |
| LM5017 | 0.6 A x 12 V = 7.2 W, below even the af budget |
| LDO for 12->3.3 | 6.1 W at 0.7 A - four times the entire carrier overhead, in a sealed box. Disqualified, not merely inefficient |
| Non-synchronous 12->3.3 (incl. the only Basic option, TPS5430) | ~0.3 W more than synchronous at D = 0.275. Rejected on that, not on price |
| Fuse or PPTC as the 48 V protection | no current limit, so a bolted short is a pure FET-SOA bet; the only stocked 2 A SMD fuses are **63 V** (6 V of margin), and the best 60 V PPTC holds 0.5 A. Keep a fuse only as a non-semiconductor backstop |
| TPS26600 eFuse | ILIM tops out at 2.23 A and it dissipates 0.6 W at 2 A - and it is a different pinout, so it is a redesign not a substitute |
| Every fine-pitch mezzanine family (Hirose FX10/BM22, Molex, Panasonic AXK, TE, HCTL SHD) | rated **50-60 V** against a 57 V worst case |
| Samtec QTH/QSH | passes on voltage (175 V), rejected on cost: $15.30 per mated pair, over half the $30/board target |
| PC/104 stackthrough (the only 15 mm route) | forces the single-connector scheme, gives up the free keying, and **publishes no working-voltage rating** - CAR-REQ-17 cannot accept that |
| Single 2x20 expansion connector | no intrinsic key, and a one-position mis-seat puts **48 V on an ESP32-S3 GPIO** |
| USB-C on every fixture (Q9 option a) | a second accessible non-isolated conductor. Incompatible with D-A5 |
| Sharing SPI2 between the W5500 and the daughter | saves 3 GPIOs on a board whose GPIO budget is exactly exhausted, but puts a 20 MHz Ethernet clock on a THT connector into an unknown board, where a hung daughter device takes down **the control path** |
| Ideal-diode input bridge (LT4321) | would recover ~0.7-1.5 W, but $7 + 8 external FETs + 126 pcs of stock. Not for 14 boards |

---

## TRAPs - verified pipeline behaviours that will bite later phases

| ID | Trap | Where it bites | What to do |
|---|---|---|---|
| **TRAP-1** | **`rules_gen.py` never reads `constraints.json.voltages`** (grep-verified), and the net class it emits for power nets gets `max(fab_min, 0.2) mm` clearance. **Nothing makes the P7 router honour the 0.60 mm 48 V clearance** - the violation only surfaces at P8 `check_creepage`, after routing | P5 -> P7 -> P8 | Add a named `.kicad_dru` clearance rule at P5 keyed on **`A.NetName`** (`A.Net` silently matches nothing - LEARNINGS 2026-07-22), covering `V48_RAW`, `V48_RTN`, `+48V_SW`, and remember that a **later** rule wins |
| **TRAP-2** | **`rules_gen.net_classes()` puts EVERY power net in one `Power` class at the WIDEST width.** `+12V`'s 1.10 mm would be applied to `V48_RTN` (0.6 A) and exported into the Freerouting DSN | before `route_auto` | Split `netclass_patterns` so the wide class holds only `+12V`, and the thin nets get their own class or Default. The DRU rules are per-net and are already correct - only the `.kicad_pro` netclass is wrong |
| **TRAP-3** | **`board_init` does NOT place the outline at (0,0)** - the origin comes from the packed component bbox. So `placement.keepouts` and `planes[].region` cannot be authored at P2 | P5 | `architecture/constraints.json` ships `planes` **without** regions and **no** `keepouts`. **Mandatory P5 step** with the exact recipe in `stackup.md` s7.1: read `reports/board_init.json.outline_bbox` and patch `kicad/constraints.json` with the antenna keepout and the six plane regions. **Skipping it leaves the ESP32-S3 antenna over a solid GND plane** |
| **TRAP-4** | `board_init` **clamps `--corner-radius` to the mounting-hole inset**, and the inset is `--margin / 2` | P5 | Pass `--margin 10` (inset 5 mm, radius up to 5 mm). A 3 mm radius then does not clamp. Do not lower `--margin` |
| **TRAP-5** | `place_anneal` **silently drops `separation` refs that are not on the board** | P4 -> P6 | Any P4 refdes edit must be mirrored into `constraints.json`. The refs at risk: U20, L20, D20, U21, L21, U10, Y10, J1, U30, U1, D1, and all five group anchors |
| **TRAP-6** | `check_return_path` raises `CheckError` -> **exit 2** for a `high_speed` net that is not on the board; `netlist_audit` raises `missing_net` at **error** severity for a `voltages[].net` that is absent | P4 | The five `high_speed` names and the six `voltages` names in `constraints.json` are **contractual on the sheet plan**. `V48_RTN` in particular must be a power symbol on `poe`, not a local label, or it becomes `/poe/V48_RTN` |
| **TRAP-7** | `check_thermal` exits 2 on a refdes with no pads, and `min_vias` demands vias on the declared `net` | P8 | Only **one** thermal entry is declared (U20, net GND - the ESOP-8 pad genuinely is GND). D20's tab is the SW node and U10 has no exposed pad; both are carried as **layout requirements** in `blocks.md` s5 instead |

---

## OPEN - decisions P2 could not settle

| ID | Item | Why it matters | Recommendation |
|---|---|---|---|
| **OPEN-A** | **No LCSC PoE magjack publishes an 802.3at (600 mA) tap rating.** All three HanRun candidates state af compliance (350 uH OCL at 8 mA bias, "meets or exceeds IEEE802.3af") | **This is the single largest technical risk to D-01's at upgrade.** Build 1 (af) is fully covered | Record the at upgrade as carrying **two documented non-board dependencies**: magjack qualification, and enclosure ventilation (`power_tree.md` s7.2). At P3, either obtain HanRun's at data or qualify a Bel/Pulse PoE+ ICM in the same 10+4 THT footprint. Removing the risk at H1 means sourcing a raw-tap jack off-LCSC, which breaks the Q14 single-order assumption |
| **OPEN-B** | **Does the selected magjack's internal rectifier take BOTH the data-pair centre taps and the spare pairs?** | Mode A + Mode B + either polarity is **mandatory** for an 802.3-compliant PD, not a choice. A Mode-A-only or Mode-B-only jack is non-compliant | Hard P3 gate: read the datasheet schematic, do not infer from the parametric |
| **OPEN-C** | **Q4a's LED module on a separate heatsink is at PoE potential.** In a non-isolated PD, IEEE 802.3 requires isolation between the MDI and *all accessible external conductors including frame ground* | If the LED module is touchable, metal, or shares a mount with anything earthed, **the non-isolated topology is non-conformant** | Needs an explicit human answer. Carried into `connector-icd.md` s9 as a daughter obligation in the meantime |
| **OPEN-D** | **The at upgrade needs enclosure vents or a confirmed ambient below ~30 C.** In Q13's sealed box at 40 C ambient, internal air reaches ~69 C at the at operating point | D-01 survives (it is still a board-level resistor change) but acquires an enclosure dependency | Either specify vents as a documented dependency of the at upgrade, or confirm the real basement ambient is 0-30 C, in which case the sealed box closes |
| **OPEN-E** | **The ESP32-S3-WROOM-1 GPIO budget is exhausted: 28 of 28 legal pins assigned**, with only GPIO3 left and only for a permanently-driven output | Any new carrier function - a second status LED, a fan tach, a temperature sensor - has nowhere to go | Accept, and note that the escape hatch is an I2C GPIO expander (the bus is already routed). Not a board risk today; a design-headroom finding for H1 |
| **OPEN-F** | **The carrier lands at $26-32 per assembled board against Q15's provisional <= $30**, and 12 carriers is ~$360 of a $500-1000 programme budget that also has to cover daughters, enclosures and the managed PoE switch | Programme-level, not board-level | Confirm the budget or the fixture count before P3 commits. $9.27 of the BOM is four parts with no cheaper credible substitute |
| **OPEN-G** | **J3/J4 board coordinates are provisional until the end of P6.** Everything else in the ICD freezes at H1 | Two daughters are blocked on the coordinates | After P6, compare the placed positions against `connector-icd.md` s7.2, correct with `place_edit`, and **re-issue the ICD before any daughter run starts** |

---

## Provisional dependencies - what flips if the human answers differently

Every P0 question is still unanswered; P2 worked to the section 9 defaults. Marked here so H1 can
see the blast radius of each answer.

| Q | Default taken | If it flips |
|---|---|---|
| Q1/Q2 | board size leads; **100 x 80 mm** | 80 x 60 is impossible (92 % utilisation needed); 100 x 100 works but is a 25 % bigger enclosure for headroom nobody asked for. **Permanent at P5** |
| Q3 | 3 mm radius, 4x M3 at 5 mm inset | plus a 5th M3 at (46,74) added by this architecture for CAR-REQ-15. Permanent |
| Q4 | stacked mezzanine, daughter above | **standoff moves 15 -> 11.0 mm** (D-A8); daughters need a top-edge notch over the RJ45. Alternative: panel-mount RJ45, which changes the outline and must land **before P5** |
| Q4a | LED module external on its own heatsink | OPEN-C |
| **Q5** | **non-isolated buck, plastic enclosure, Ethernet-only** | isolated drops af margin to 4.6 %, has no in-catalog transformer, and adds a 2.0 mm barrier spacing requirement. **Load-bearing for the whole compliance argument** |
| **Q6** | 48 V 2 A cont / 3 A cap, 12 V 2 A, 3.3 V 0.5 A | **corrected**, D-A6. A 48 V peak above 3 A pushes the power block to 2x8 (socket stock 47 pcs) or 2x9. **Get this answered before H1** - the ICD freezes there and two daughters are blocked |
| **Q7** | pre-certified WROOM-1, 8 MB, no PSRAM | **recommend closing now** as "module" - research produced better evidence than the default |
| **Q8** | radio unused but functional | "permanently dead" -> WROOM-1U-N8 on the same land pattern, keepout gone, 220 mm2 and a board edge back, +3V3 peak drops from 500 mA to ~230 mA. **Load-bearing on the permanent outline** |
| Q9 | Ethernet OTA + an internal UART/BOOT header | option (a) USB-C is **unavailable** under D-A5. The header must be used with PoE unplugged or with an isolated adapter |
| Q10 | both divider and I2C EEPROM | implemented as **1** ID pin + the shared I2C bus; the freed position became a fifth signal GND |
| Q11 | RJ45 LEDs + one status LED | satisfied: 2 magjack LEDs from the W5500, 1 MCU status LED, plus **2 hardware-driven LEDs** off the eFuse PGOOD/FLT that cost no GPIO |
| Q12 | board-edge THT magjack | panel-mount frees zone A and removes the daughter relief, but changes the outline |
| Q13 | 0-40 C, sealed, natural convection | **binding for the thermal argument.** OPEN-D |
| Q14 | JLCPCB PCBA, top-side SMT | **no JLC Basic part exists** for the module, W5500, magjack, PD interface, either converter, the eFuse or the connectors. "Prefer Basic" is unachievable here |
| Q15 | build 14, <= $30/carrier | OPEN-F |
| Q16 | ICD serves strobe + RGBW par only | honoured. LEDC timers 2 and 3 and the shared SPI/I2C are the only reservation, and they cost nothing |
