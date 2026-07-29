import json, sys, os
sys.stdout.reconfigure(encoding='ascii', errors='replace')
V = json.load(open(r"boards\lumina-carrier\work\ps\verified.json"))
BUILD_QTY = 14

T = [
# ---------------- poe sheet ----------------
("C91754","J","poe","HY931147C PoE RJ45 magjack",1,["J1"],
  [{"mpn":"HR861153C","lcsc":"C19724782","note":"HanRun, same 10+4 THT land pattern, same integrated-bridge V+ (P9) / V- (P10) topology, 2250 VDC isolation, 471 pcs. P7/P8 differ (GND/NC) so the netlist changes; the footprint does not."}],
  "THT right-angle shielded RJ45 with integrated magnetics AND integrated PoE rectifier. Datasheet schematic READ this session (2 pages, wmsc mirror): TWO full diode bridges - one fed from both transformer centre taps (Mode A, data pairs), one fed from the tied spare pairs (Mode B, J4+J5 and J7+J8) - both rectifying into a common V+ (P9) / V- (P10). MODE A + MODE B + EITHER POLARITY CONFIRMED: open item B is closed, not a blocking escalation. P7/P8 do not appear on the schematic = no-connect. LEDs: pin 11 anode / 12 cathode yellow 585 nm, pin 13 anode / 14 cathode green 568 nm, 20 mA, Vf 1.8-2.8 V, so drive the anode from +3V3 through a series R and take the cathode to the W5500 active-low LED output. Isolation 1500 Vrms (P2+P5 to J2+J3); OCL 350 uH min at 100 kHz / 100 mV with 8 mA DC bias. RATING LIMIT (open item A): the datasheet publishes NO current, power or thermal rating for the internal bridge or the taps; its only PoE claim is 'Meets or Exceeds IEEE802.3af standards including 350uH Min OCL with 8mADC'. QUALIFIED FOR THE af BUILD ONLY - the 802.3at (600 mA) upgrade is not covered by any published number. THT: JLC wave-solders it (Assembly Type: Wave Soldering), ~18 joints."),
("C21189","R","poe","0R jumper 0603",1,["R9"],[],
  "APD-to-RTN link on U1 pin 8. CORRECTED after datasheet extraction: parts\\C337500.json quotes the explicit instruction 'If not used, connect APD to RTN' - APD is an INPUT (>1.5 V above RTN turns the pass MOSFET off and forces T2P active, giving an external adapter priority over PoE), and its sink current is only 1-3 uA, so a floating APD can drift up and shut the hot-swap FET off. My earlier 'leave pin 8 unconnected' role text was wrong. Fitting the tie as a 0 ohm link rather than a hard copper short preserves the TPS2379 second source, whose pin 8 is GATE and must NOT be tied to RTN - depopulate R9 if a TPS2379 is ever stuffed. JLC Basic, $0.0027."),
("C337500","U","poe","TPS2378DDAR",1,["U1"],
  [{"mpn":"TPS2379DDAR","lcsc":"C140293","note":"True second source. Pins 1-7 identical (VDD/DEN/CLS/VSS/RTN/CDB/T2P); only pin 8 differs (TPS2378 = APD, TPS2379 = GATE). The board is PoE-only so pin 8 stays unconnected and either part builds on one footprint. 1755 pcs, $1.7058@10."}],
  "802.3at Type 2 PD interface, SO-8 PowerPAD. 100 V / 0.5 ohm integrated hot-swap FET, 0.85 A continuous, 140 mA inrush limit, single-resistor classification (the D-01 lever), CDB converter-disable straight to U20 EN, T2P Type-2-detected flag. Si3402-B / Si3402-C / Si3404 are DISQUALIFIED (Type 1 only) and are not proposed. PIN 8 (APD): the datasheet says 'If not used, connect APD to RTN' - do NOT float it. Tied through R9 (0 ohm) so the TPS2379 second source, whose pin 8 is GATE, stays buildable by depopulating one link. Do not wire any sleep or power-save function to DEN or APD: that kills DC MPS and the PSE drops the port."),
("C2891331","D","poe","SMBJ58A 58V 600W TVS",1,["D1"],
  [{"mpn":"SMBJ58A","lcsc":"C707476","note":"Same part number, different vendor lot, 6804 pcs, $0.047. Drop-in."}],
  "Unidirectional TVS across V48_RAW / V48_RTN, physically first after the jack. 58 V standoff clears the 57 V worst case; 64.4 V Vbr min and 93.6 V Vclamp stay under U1's 100 V abs max. 600 W not 400 W: an SMAJ58A's 4.3 A I_PP is below the 4.65 A a 1 kV class-2 surge delivers into one shorted line."),
("C5156756","C","poe","10uF 100V X7R 1210",4,["C2","C4","C5","C6"],
  [{"mpn":"TCC1210X5R106K101MT","lcsc":"C51892808","note":"X5R instead of X7R, $0.4658@10, 23569 pcs. Cheaper but a weaker dielectric for a 48 V bulk cap sitting in 56-69 C internal air."}],
  "CBULK on V48_RAW. SUBSTITUTION vs the architecture: blocks.md s2.2 specifies 2 x 22 uF / 100 V ceramic = 44 uF, but NO 22 uF / 100 V MLCC EXISTS ON LCSC in any package (--package 1210 and 1812 both return zero rows; the only 22 uF / 100 V hits are aluminium electrolytics, which this board bans). 4 x 10 uF = 40 uF nominal is the closest stocked equivalent; after ceramic DC-bias derating at 48 V expect ~20-24 uF effective, still 4x the >= 5 uF AC-MPS floor (TPS2378 DS 7.4.7) and far under both the ~180 uF 802.3 port ceiling and the part's own 240 uF limit. This is the single most expensive passive line on the board at ~$2.25/assembly."),
("C153036","C","poe","2.2uF 100V X7R 1210",2,["C50","C51"],[],
  "U20 buck input capacitance on V48_RAW. 100 V rated per the >= 100 V discipline on the 48 V domain - never a 50 V or 63 V part here."),
("C28233","C","poe","100nF 100V X7R 0805",1,["C1"],
  [{"mpn":"CC0805KKX7R0BB104","lcsc":"C106243","note":"Yageo, same 100 V / 0805 / X7R rating, 715239 pcs, $0.0381 - cheaper per piece but Extended, so it costs a feeder fee to save $0.40 across the build."}],
  "U1 VDD-VSS bypass, inside the IEEE 802.3 50-120 nF detection-signature window. 100 V part on the 48 V domain. Note its ground reference is V48_RTN, not GND - P4 needs an explicit gnd_net override on this decoupling entry. JLC Basic."),
("C9196","C","poe","1nF 2kV X7R 1206",1,["C3"],[],
  "Shield hybrid: 1 nF / 2 kV in parallel with R6 (1 M) between the magjack shield tabs and board GND. JLC Basic."),
("C30908","R","poe","12.4k 1% 0805",4,["R1","R2","R30","R67"],[],
  "R67 ADDED after datasheet extraction as the UVLO-to-OVP middle leg of U22's three-resistor divider (see R66). R1+R2 form the split 24.9 k detection signature with the tap brought out at /poe/DEN_TAP - grounding the tap disables the PD and spoils the signature, which is the clean hardware PD-disable. 0805 per the 48 V-domain resistor rule, 150 V working. R30 re-uses this line as the W5500 EXRES1 bias resistor (12.4 k 1 % to AGND, sets MDI drive amplitude). NOTE from decisions.md D-A2: the magjack's internal rectifier sits in series with the detection path, so RDEN may need trimming UPWARD at P4 - do not port 24.9 k blindly."),
("C23130","R","poe","90.9R 1% 0603",1,["R3"],[],
  "R3 = THE D-01 LEVER, fitted value for build 1: 90.9 ohm = Class 3 (802.3af, 12.95 W). Standalone silkscreened pad pair, silk marked 'af=90R9 / at=63R4'."),
("C23223","R","poe","63.4R 1% 0603",0,["R3-at"],[],
  "NOT FITTED - the 802.3at upgrade option for R3. 63.4 ohm = Class 4 (25.5 W). Sourced now so the D-01 upgrade is a stocked-part swap and never a sourcing task; order 14 pcs with the build and keep them with the spares. qty_per_board is 0 because the board ships with 90.9 ohm."),
("C17414","R","poe","10k 1% 0805",2,["R4","R5"],[],
  "T2P level-shift network. T2P is an open-drain output referenced to VSS (the raw PoE negative), not to board GND, and can sit tens of volts away from it - it is never a bare GPIO connection. 0805 / 150 V per the 48 V-domain resistor rule. Exact divider values are set at P4 from the TPS2378 datasheet; the orderable part is the same 0805 1% thick-film series either way. JLC Basic."),
("C22935","R","poe","1M 1% 0603",1,["R6"],[],
  "Shield hybrid bleed in parallel with C3, magjack shell to board GND. JLC Basic."),
("C23138","R","poe","330R 1% 0603",5,["R7","R8","R71","R72","R102"],[],
  "LED series resistors: R7/R8 for the magjack's yellow and green LEDs driven from the W5500's active-low LINK/ACT outputs (anode side to +3V3 - jack pins 11 and 13 are the anodes, confirmed from the datasheet), R71/R72 for the power-good and fault LEDs, R102 for the ESP32-S3 status LED. ~4 mA per LED at 3.3 V. JLC Basic."),
# ---------------- eth sheet ----------------
("C32843","U","eth","W5500",1,["U10"],[],
  "SINGLE SOURCE, NO ALTERNATE EXISTS - the empty alternates list is deliberate. One orderable part number, one manufacturer, no pin-compatible part anywhere: W6100 is pin-2-pin with the W5100S, NOT the W5500, and W5100S-L has a different pinout AND a different register map, so a swap is a schematic plus firmware respin. RISK: HIGH and unmitigable by design. Mitigation is procurement - 33998 pcs today, but buy the W5500s with the board order rather than assuming availability at re-order time. LQFP-48 (7x7, 0.5 mm), no exposed pad, so no min_vias thermal demand is satisfiable - a copper pour under it is a layout note instead. Variable Length Data Mode is mandatory (the host drives SCSn) because the SPI bus is shared with the expansion connector. Guaranteed SPI clock is 33.3 MHz, not the feature list's theoretical 80 MHz; the design runs 20 MHz."),
("C70593","Y","eth","25MHz 18pF CL crystal",1,["Y10"],
  [{"mpn":"XL2EL89CRI-111YLC-25M","lcsc":"C19078191","note":"YXC, identical parametrics (18 pF CL, +-10 ppm / +-20 ppm, ESR 50 ohm), same SMD3225-4P footprint, 14107 pcs, $0.0856 - a true drop-in second source."}],
  "W5500 reference. CL AND ppm VERIFIED AGAINST W5500 DS v1.1.0 s5.5.3, which requires 25 MHz, CL 18 pF, tolerance +-30 ppm at 25 C, shunt capacitance <= 7 pF and 59.12 uW drive: this part is CL 18 pF exactly, +-10 ppm initial and +-20 ppm over -40..+85 C, so initial + temperature = +-30 ppm total, meeting the datasheet's +-30 ppm and leaving 1.7x margin against IEEE 802.3 clause 25's +-50 ppm transmit-clock budget with ageing (+-3 ppm/yr) still to spend. The JLC Basic 25 MHz part (X322525MOB4SI, C9006) is CL 12 pF and is deliberately NOT taken: at $0.095 either way the only gain is one feeder fee, against moving the oscillator off the load capacitance WIZnet characterised."),
("C107045","C","eth","27pF 50V NP0 0603",2,["C30","C31"],[],
  "Crystal load caps: C = 2 x (CL - Cstray) with CL 18 pF and Cstray ~4 pF. NP0/C0G is mandatory. Expect to trim on the first prototype - most W5500 module schematics use 22 pF, which back-solves to CL 15 pF and is wrong for an 18 pF part."),
("C19829453","D","eth","TPD4E1U06 4ch 0.55pF ESD array",1,["D10"],
  [{"mpn":"SP3012-04UTG","lcsc":"C2987148","note":"4-channel MDI array at 0.3 pF/line, DFN2510-10 (leadless - fine on JLC PCBA, not for hand assembly), 4221 pcs, $0.0702."}],
  "MDI ESD array on the PHY side of the magnetics, across TXP/TXN and RXP/RXN at the J1 end of the pairs. 0.55 pF per line meets the binding <= 1 pF/line spec - a general-purpose 20-50 pF array visibly degrades the 10 dB return-loss floor. FITTED, not DNP. SOT-23-6, leaded."),
("C23345","R","eth","22R 1% 0603",2,["R31","R32"],[],
  "Series termination on /ETH_SCLK and /ETH_MOSI, placed at the ESP32-S3 driver pin. Fitted so the value can be tuned if EMC bites. JLC Basic."),
("C1779","C","eth","4.7uF 25V X5R 0805",2,["C32","C36"],[],
  "C32 = W5500 TOCAP (a required decoupling pin, not a no-connect). C36 = local +3V3 bulk at the W5500. JLC Basic."),
("C57112","C","eth","10nF 50V X7R 0603",2,["C33","C59"],[],
  "TWO uses. C33 = W5500 1V2O internal-regulator output cap, a pin that is not a no-connect. C59 = U22's dV/dT inrush-ramp cap, CORRECTED after datasheet extraction: parts\\C1849461.json gives C(dVdT) MINIMUM 10 nF, and the UVLO/OVP turn-on timing specs are only defined for C(dVdT) >= 10 nF, so my original 1 nF was out of spec. 10 nF is the datasheet minimum and therefore still the FASTEST compliant ramp, which is what the architecture wants - the daughter owns the inrush ramp because it holds the ~2800 uF, and U22's limit sits above the daughter's inrush level so the two soft-starts do not fight. t(dVdT) = 20.8e3 x 48 V x 10 nF = ~10 ms. The dVdT pin is 0-4 V rec / 5.5 V abs max, so the 50 V rating is ample. JLC Basic."),
# ---------------- pwr sheet ----------------
("C5124114","U","pwr","SCT2A25STER",1,["U20"],[],
  "48 V -> 12 V asynchronous buck, ESOP-8. 5.5-100 V in / 110 V abs max = 1.9x margin on the 57 V worst case, against the 5% a 60 V TPS54360 would have; 2 A continuous / 4 A peak, COT 300 kHz, integrated 500 mohm HS FET, RthetaJA 42 C/W, and the datasheet ships the literal 48 V -> 12 V / 2 A design. NO PIN-COMPATIBLE ALTERNATE - the empty list is deliberate: LM5164 (1 A = 12 W, covers af and fails at), MP9486A, LM5146 (controller + 2 FETs) and TPS54360B (60 V) are all different pinouts and different designs, so a swap is a respin, which D-01 forbids. Stock 3160 = 226x the build, so this is a re-order risk, not a build risk. Exposed pad to the In1 GND plane with >= 9 vias. EN is driven from U1's CDB pin for correct PoE start-up sequencing with no glue. POST-EXTRACTION CORRECTIONS (parts\\C5124114.json): the feedback reference is 1.2 V +/-1%, NOT 0.8 V - the FB divider is 270k/30k (R60/R61) plus a 150 pF feedforward cap (C60) that the datasheet calls necessary for loop stability. Switching frequency is FIXED at 300 kHz with no RT pin. The 68 uH inductor and 2 x 22 uF output caps already in this BOM match the datasheet's own 48 V -> 12 V / 2 A example exactly."),
("C526032","L","pwr","68uH 3A 140mohm inductor",1,["L20"],
  [{"mpn":"FXL1040-680-M","lcsc":"C475920","note":"Same family, 11.5x10 mm instead of 13.5x12.6 mm, 15713 pcs, $0.2687 - but 195 mohm DCR puts the 48->12 block at ~1.31 W, OVER the 1.25 W budget blocks.md s2.3 places on P3. Take it only if the +12V ICD ceiling is lowered."}],
  "U20 output inductor, selected on DCR rather than on price or size. blocks.md s2.3 places a HARD <= 1.25 W budget on the whole 48->12 block at the at operating point (I_out = 1.324 A at the ICD's 1.25 A +12V ceiling). At 140 mohm this inductor burns 0.245 W, so U20 (0.43 W) + D20 (0.54 W) + L20 (0.245 W) = 1.22 W and the budget CLOSES; every other stocked 68 uH part is 190-260 mohm and breaks it. 3 A rated / 4.5 A saturation. Body 13.5 x 12.6 mm, larger than blocks.md's '~7 x 7 mm' estimate - a 68 uH / 3 A part simply is not 7 x 7."),
("C19229","D","pwr","SS510C 100V 5A Schottky SMC",1,["D20"],
  [{"mpn":"SS510B","lcsc":"C65011","note":"Same die in SMB (DO-214AA), 98190 pcs, $0.0748. Smaller body, worse thermal path - only if board area forces it."}],
  "U20 catch diode, the part the SCT2A25 datasheet names. SMC (DO-214AB) taken over SMA/SMB for the thermal path: it DISSIPATES MORE THAN THE BUCK IC (~0.54 W vs ~0.43 W at the at operating point), and its layout requirement is >= 100 mm2 of F.Cu on the cathode - a via field is not an option because the tab is the switch node. Placement must not treat U20 as 'the hot part' and starve D20 of copper."),
("C116592","U","pwr","TPS563201DDCR",1,["U21"],[],
  "12 V -> 3.3 V synchronous buck, SOT-23-THIN-6, 4.5-17 V in, 3 A, 580 kHz, EN pin. An LDO here is DISQUALIFIED, not merely inefficient: (12 - 3.3) x 0.7 A = 6.1 W, four times the entire carrier-overhead allocation, in a sealed box. The one JLC Basic candidate (TPS5430) is non-synchronous and costs ~0.3 W more at this duty, which is what rejects it - not price. No clean pin-compatible alternate is recorded: SY8113BADC has a different pinout, and the MSTPS563201DDCR clone (C49208507) carries no fetchable datasheet, so it is not a verified candidate. Mitigated by 105187 pcs = 751x the build. 12 V sits at 71% of the 17 V ceiling - check against +12V transients at P4."),
("C325964","L","pwr","4.7uH 4A 46mohm inductor",1,["L21"],[],
  "U21 output inductor. 4 A rated / 4.5 A saturation and 46 mohm against a 1.0 A design rail with a 1.21 A ms-scale peak (Wi-Fi TX + W5500 TX + daughter). 5.4 x 5.2 mm."),
("C1849461","U","pwr","TPS16630PWPR",1,["U22"],[],
  "60 V eFuse / load switch gating +48V_SW to the expansion connector, HTSSOP-20 PowerPAD. 4.5-60 V op / 67 V abs, ILIM adjustable 0.6-6 A +-7%, adjustable UVLO and OVP, dV/dT inrush ramp, latch-or-retry MODE, PGOOD, open-drain FLT, and an analogue IMON current monitor that closes the firmware energy governor's loop for zero extra parts. CONFIGURATION THAT IS NOT OPTIONAL, now set from the extracted datasheet (parts\\C1849461.json, SLVSET9G Rev G): R65 = 18 kohm for the 1.0 A limit (R(ILIM) = 18 / I(OL), TI's own 1 A example), C59 = 10 nF minimum on dVdT, R68 = 30 kohm on IMON, and the UVLO/OVP function is a THREE-resistor string R66/R67/R73 = 1 M / 12.4 k / 20 k giving UVLO 38.2 V and OVP cutoff 61.9 V. MODE open = LATCH OFF (auto-retry into a browning-out daughter produces restart oscillation), and a 10 k pull-down on SHDN (R69) because the datasheet's SHDN open-circuit voltage is 2.48-3.3 V with a 10 uA source - AN UNCONNECTED SHDN FLOATS HIGH AND THE DEVICE POWERS UP ON. That pull-down IS the CAR-REQ-08 fail-safe (must default OFF with no MCU present). NO PIN-COMPATIBLE ALTERNATE - deliberate empty list: TPS26600 is a different pinout and cannot pass 3 A, and the LM5069 fallback is a controller + external FET + shunt, i.e. a redesign. Stock 2055 = 146x the build but thin for a re-order; buy with the board order. RESIDUAL RISK carried from research: the SMBJ58A clamps at up to 93.6 V against this part's 67 V abs max, which is only defensible because U22 sits DOWNSTREAM of U1's hot-swap FET and CBULK, not on the rectified input. If placement ever moves it upstream, the part must change to LM5069 + a 100 V FET."),
("C25810","R","pwr","18k 1% 0603",1,["R65"],[],
  "U22 ILIM, CORRECTED after datasheet extraction. parts\\C1849461.json: R(ILIM) = 18 / I(OL) with R in kohm and I in A (Eq 6/10), so a 1.0 A overload limit needs 18 kohm - and 18 kohm is TI's own worked 1 A example (sec 9.2.2.1, and Figures 8-6/8-7/8-8 are captured at that value). My original 49.9 k would have limited at 18/49.9 = 0.36 A, which is BELOW the ICD's 0.50 A at-case sustained rating on +48V_SW - the daughter would have tripped the eFuse in normal operation. ILIM is a GND-referenced programming pin, never on the 48 V domain, so 0603 is correct here. Recommended R(ILIM) range is 3-30 kohm and UL 2367 recognition requires >= 3 kohm; 18 k sits mid-range. JLC Basic."),
("C4328","R","pwr","20k 1% 0805",1,["R73"],[],
  "U22 OVP-to-GND bottom leg, the third resistor of the UVLO/OVP string (see R66). NEW REFDES: the sheets.md allocation gave R65-R68 for ILIM + divider + IMON + dV/dT, which is one resistor short - the extraction shows UVLO and OVP share a THREE-resistor string (R1 IN-UVLO, R2 UVLO-OVP, R3 OVP-GND, Figure 8-3), not a two-resistor divider. R73 is free in the pwr sheet's R60-R99 block. 0805 per the 48 V-domain rule even though the node itself only reaches ~1.1 V, because an open top leg would expose it to the rail. JLC Basic."),
("C17514","R","pwr","1M 1% 0805",1,["R66"],[],
  "U22 UVLO/OVP divider TOP leg (IN to UVLO) - the only resistor on the board that sees the full 57 V continuously. Sized after datasheet extraction: with R66 = 1 M, R67 = 12.4 k and R73 = 20 k the string gives UVLO rising 38.2 V / falling 35.8 V (inside power_tree.md s6's 36-40 V turn-on window) and OVP cutoff rising 61.9 V / falling 57.9 V, which sits above the 57 V PSE maximum and below the part's 67 V abs max. Divider current is 46.5 uA at 48 V, comfortably over the >= 20x pin-leakage rule (3 uA) the datasheet gives in sec 9.2.2.2. 3.2 mW at 57 V. P4 REVIEW ITEM: the OVP FALLING threshold is only ~0.9 V above the 57 V worst case, so after an overvoltage event the rail must drop below 57.9 V to re-enable - re-tunable within these same stocked values if that margin is judged too thin. NOTE UVLO must never be left floating (sec 8.3.2) and OVP is a LOW-VOLTAGE pin (0-4 V rec, 5.5 V abs max) that must never see the raw rail. JLC Basic."),
("C22984","R","pwr","30k 1% 0603",2,["R61","R68"],[],
  "TWO uses, both set by datasheet extraction. R61 = the SCT2A25 +12V feedback divider BOTTOM leg (with R60 = 270 k). R68 = U22 IMON scaling: V(IMON) = I(OUT) x 27.9 uA/A x R(IMON), so 30 k gives 0.837 V at the 1.0 A eFuse limit and 0.209 V at the af sustained 0.25 A - this is TI's own 1 A example value, and it maps the full eFuse range onto the ESP32-S3 ADC1 0 dB attenuation window (~0-950 mV) where linearity is best. My original 49.9 k would have read 1.39 V at 1.0 A - legal (the IMON ceiling is 4 V) but a worse ADC fit. DATASHEET RULE for P4: IMON must have NO bypass capacitor, or the current reading is delayed. JLC Basic."),
("C22965","R","pwr","270k 1% 0603",1,["R60"],[],
  "U20 +12V feedback divider TOP leg. CORRECTED after datasheet extraction, and this was the most serious error in the P3 BOM: parts\\C5124114.json states the SCT2A25 feedback reference is 1.2 V +/-1% (1.188/1.2/1.212), explicitly 'NOT 0.8 V'. My original 140k/10k on an assumed 0.8 V reference would have produced 1.2 x 15 = 18.0 V on the +12V rail, over the rating of the TPS563201 (17 V max) and of every 25 V output capacitor after derating. USING 270k/30k RATHER THAN THE DATASHEET'S 271k/30k: 271 k is a real E96 value but is ZERO STOCK on LCSC in both 0603 and 0805 (all six listings are 0 pcs), whereas 270 k gives a ratio of exactly 9.000 and therefore 1.2 x 10 = 12.000 V - marginally closer to nominal than the datasheet pair's 12.04 V. 161541 pcs."),
("C107038","C","pwr","150pF 50V NP0 0603",1,["C60"],[],
  "Feedforward capacitor across R60, the +12V feedback divider top leg. NEW PART, added after datasheet extraction: the SCT2A25's 48 V -> 12 V / 2 A design example ships this cap and the datasheet calls it NECESSARY for loop stability, not optional - a COT converter with a 300 kohm feedback string needs the zero it provides. NP0/C0G, 5 % tolerance."),
("C149504","R","pwr","100k 1% 0805",1,["R70"],[],
  "R70 = the carrier-side bleed on +48V_SW. De-energises the connector's 48 V pins whenever ENABLE is low; 0.5 mA / 23 mW. 0805 per the 48 V-domain rule - 0603 parts are 75 V working and must not be used here. JLC Basic."),
("C4216","R","pwr","33k 1% 0603",1,["R63"],
  [{"mpn":"RC0603FR-0733K2L","lcsc":"C185338","note":"33.2 k, the datasheet Table 2 value (33.2k/10.0k = 3.318 V). Extended, 100723 pcs, $0.0075 vs Basic 33 k at $0.0021 - swap only if a P4 review wants the datasheet pair verbatim."}],
  "U21 +3V3 feedback divider, top leg. VERIFIED, not corrected: parts\\C116592.json confirms the TPS563201 reference is 768 mV typ (749/787 min/max) and Equation 2 is VOUT = 0.768 x (1 + R1/R2), so my assumed value was right. 33k/10k gives 3.302 V; the datasheet's own table pair is 33.2k/10.0k = 3.318 V. KEEPING 33 k: it is JLC Basic at a third of the price, and 3.302 V is if anything closer to nominal 3.3 V than the datasheet pair. Both are inside the ESP32-S3 and W5500 supply windows. JLC Basic."),
("C380359","C","pwr","22uF 25V X5R 1206",6,["C52","C53","C55","C56","C57","C80"],
  [{"mpn":"CL31A226KAHNNNE","lcsc":"C12891","note":"Samsung, JLC Basic, 1046995 pcs - but $0.4138 vs $0.1062, i.e. ~$1.85/board more to save one feeder fee. Not worth it at 14 boards."}],
  "Bulk on the low-voltage rails: C52/C53 = +12V output, C55 = U21 input, C56/C57 = +3V3 output, C80 = the ESP32-S3 module's local bulk (the module datasheet independently requires a supply able to deliver >= 500 mA, and the 355 mA Wi-Fi TX burst is served by local bulk, not by the converter). 1206 rather than 0805 to limit DC-bias derating on the 12 V rail."),
("C2297","D","pwr","Green LED 0805",2,["D21","D30"],[],
  "D21 = power-good, driven straight from U22's PGOOD pin with NO GPIO. D30 = the ESP32-S3 firmware heartbeat / commissioning LED on GPIO48. The only JLC Basic green LED is 0805, which is why the board deliberately mixes 0603 red with 0805 green. Visible through the RJ45 cutout per Q11's default."),
("C2286","D","pwr","Red LED 0603",1,["D22"],[],
  "D22 = fault, driven straight from U22's open-drain FLT output with NO GPIO. JLC Basic, 0.7 cents."),
# ---------------- mcu sheet ----------------
("C2913198","U","mcu","ESP32-S3-WROOM-1-N8",1,["U30"],
  [{"mpn":"ESP32-S3-WROOM-1-N8R2","lcsc":"C2913204","note":"Same land pattern, same -40..+85 C ambient. QUAD PSRAM uses the flash lines, NOT IO35/36/37, so it is genuinely pin-compatible with this design. 19068 pcs, $4.8462@10."},
   {"mpn":"ESP32-S3-WROOM-1-N16R2","lcsc":"C2913205","note":"Same land pattern, 16 MB flash + quad PSRAM, IO35/36/37 free, 6783 pcs, $4.6945@1. Second choice only because the OTA partition plan is sized against 8 MB."},
   {"mpn":"ESP32-S3-WROOM-1-N4","lcsc":"C2913197","note":"Same land pattern, -40..+85 C, 5951 pcs, $4.1571@10. 4 MB flash is tight against Ethernet OTA's two app partitions plus NVS - fallback only."}],
  "MCU, pre-certified module WITH THE PCB ANTENNA. The -1U (u.FL, C2980297) is explicitly NOT taken: H1 closed Q8 as 'Wi-Fi functional, a supported control path', so the on-module PCB antenna is required and its ~6 x 18 mm keepout is a permanent outline constraint. The -N8 SKU is frozen by the architecture, not merely preferred: GPIO35/36/37 are in use and they are wired to the OCTAL PSRAM on -N8R8 / -N16R8V, and -N16R8V additionally puts GPIO47/48 at 1.8 V (both in use). Ambient is the second reason: -40..+85 C on -N8 versus -40..+65 C on the R8 parts, against a computed internal air of 56 C (af) / 69 C (at) - 16 C of margin at the at point. Module vs bare chip: the bare-chip saving is $0.16-$1.28/unit = $2-$18 across the whole build, against RF layout, a pi-match, 80 MHz quad-SPI flash routing, modular certification and a QFN-56-EP. The saving does not exist."),
("C7430362","J","mcu","DS1021-1x6SF11-B 1x6 2.54mm header",1,["J2"],[],
  "Recovery header (Q9 default b): GND, +3V3, TXD0, RXD0, EN, BOOT. Same CONNFLY DS1021 family as J3/J4 so the whole board uses one header vendor and one land-pattern family. 2.54 mm THT male, gold, 250 V / 3 A, 4272 pcs. THT - JLC wave-solders it, 6 joints. Inside the enclosure, no panel cutout. Silkscreen must carry 'PoE OFF or ISOLATED ADAPTER ONLY': an earthed USB-UART adapter ties the floating PoE return to earth and breaks PD signature detection outright."),
("C720477","SW","mcu","Tactile switch SMD 4x3mm",1,["SW1"],[],
  "Optional BOOT button on GPIO0 alongside the J2 header pin. JLC Basic, 857198 pcs, SMD so it adds nothing to the THT joint count."),
("C15849","C","mcu","1uF 50V X5R 0603",2,["C84","C85"],
  [{"mpn":"CL10B105KA8NNNC","lcsc":"C29936","note":"Samsung X7R 25 V, 2050769 pcs, $0.0226 - cheaper per piece but Extended, so it costs a feeder fee to save ~$0.93 across the build."}],
  "C85 = the EN-pin RC with R100 (10 k), which sets the ESP32-S3 power-on reset delay. C84 = module supply decoupling. JLC Basic, 50 V."),
# ---------------- expansion sheet ----------------
("C7430403","J","expansion","DS1021-2x7SF11-B 2x7 male header",1,["J3"],[],
  "EXPANSION POWER connector, CARRIER SIDE ONLY - frozen by ICD-01 and not re-openable. 14 position, 2.54 mm, THT male, gold over copper alloy, 250 V rated working voltage (4.4x the 57 V worst case), 3 A/contact (1.80 A/pin after the 60% adjacent-pin derate the ICD uses throughout), -40..+105 C. Orderable variant verified: 2x7P, MALE, straight/vertical through-hole, 5575 pcs. THE MATING DS1023-2*7SF11 SOCKET IS THE DAUGHTER BOARDS' PART AND IS DELIBERATELY ABSENT FROM THIS BOM. THT - 14 joints. Pin map: connector-icd.md s3.1. At 2.54 mm with a 1.70 mm annulus the pad-to-pad copper gap is 0.84 mm against the 0.60 mm IPC-2221B B2 requirement (1.4x); every fine-pitch mezzanine family JLC stocks is rated 50-60 V and fails or grazes the 57 V case, which is what closed the fine-pitch route."),
("C7430408","J","expansion","DS1021-2x12SF11-B 2x12 male header",1,["J4"],[],
  "EXPANSION SIGNAL connector, CARRIER SIDE ONLY. 24 position, 2.54 mm, THT male, gold, 250 V / 3 A, 3652 pcs. The mating DS1023-2*12SF11 socket is the daughter's part and is NOT in this BOM. No 48 V exists anywhere on this connector. THT - 24 joints. Pin map: connector-icd.md s3.2."),
("C25804","R","expansion","10k 1% 0603",8,["R33","R34","R64","R69","R100","R101","R132","R134"],[],
  "The board's general-purpose pull-up / pull-down / divider value. R69 is THE CAR-REQ-08 FAIL-SAFE (10 k pull-down on /ENABLE, which reaches both U22 SHDN and J4-23 as one net) - passive, so it cannot be defeated by firmware, a reset, a brownout or a reboot, and it must be called out on the schematic. VALUE CONFIRMED against parts\\C1849461.json sec 8.3.11: the TPS16630 has NO active-high EN pin, only active-low SHDN with an internal pull-up whose open-circuit voltage is 2.48/2.7/3.3 V against a 2.0 V rising enable threshold, so it DEFAULTS ON; the datasheet requires a pull-down that sinks >= 10 uA while holding the pin below the 0.8 V V(SHUTF) threshold. 10 k against the 10 uA max internal source holds SHDN at 0.10 V - 8x inside the threshold - and sinks the required current, so R69 is correct as sourced and is already in this line's quantity. R61 has MOVED OFF this line to the new 30 k part (the SCT2A25 reference is 1.2 V, not 0.8 V). R33 is MANDATORY, not belt-and-braces: GPIO10 has a documented 60 us LOW glitch at power-up and low = W5500 selected, and the W5500's own 50-112 k SCSn pull-up cannot fight an actively driven glitch. R34 = /ETH_RSTn pull-up; R100/R101 = EN and BOOT; R132 = /FAULT pull-up on the wire-OR shared with U22's FLT; R134 = the ID divider top leg (the daughter fits the bottom leg); R61/R64 = the two feedback-divider lower legs. JLC Basic."),
("C23162","R","expansion","4.7k 1% 0603",2,["R130","R131"],[],
  "I2C pull-ups, CARRIER SIDE per ICD-01 s3.3 - daughters must not fit their own. 400 kHz. JLC Basic."),
("C21190","R","expansion","1k 1% 0603",3,["R135","R136","R137"],[],
  "Series protection on /ID_ADC, /ADC0 and /ADC1. Part of the CAR-REQ-14 survivability story, not just ESD hygiene: a mis-seated daughter can bridge a neighbouring connector pin onto these lines. Small enough to keep the ICD's <= 10 kohm source-impedance rule intact. JLC Basic."),
("C2687129","D","expansion","PESD3V3L1BA 3.3V ESD clamp SOD-323",3,["D40","D41","D42"],[],
  "3.3 V bidirectional clamps on /ID_ADC, /ADC0 and /ADC1, downstream of R135-R137. These lines are DC / low-speed so the ~100 pF junction capacitance is irrelevant here, unlike the MDI where D10 must be <= 1 pF/line. 374413 pcs."),
("C83836","U","expansion","M24C02 2Kbit I2C EEPROM",1,["U40"],
  [{"mpn":"BL24C02F-PARC","lcsc":"C176653","note":"Belling, 1.7-5.5 V, 1 MHz, SOP-8, 39939 pcs, $0.0743 - about half the price and functionally equivalent for an ID/calibration store."},
   {"mpn":"AT24C02","lcsc":"C688857","note":"IDCHIP, SOP-8, 132189 pcs, $0.0659. Commodity second source; it is a clone, so verify address-pin behaviour before shipping."}],
  "Carrier board-ID / calibration EEPROM on the shared I2C bus. 2 Kbit, 1.8-5.5 V so 3.3 V is comfortably inside, 400 kHz, SOIC-8. INCLUDED PER ASSIGNMENT AMENDMENT 4, and flagging a genuine conflict with the architecture: blocks.md, sheets.md s2.5 and connector-icd.md s2 all place the ID EEPROM on the DAUGHTER ('the EEPROM rides the shared I2C bus', which is exactly why ID is one pin and not two), and no U40 exists in the refdes allocation. It is sourced here at $0.13 as a carrier-side board-ID store; if P4 rules the architecture wins, drop this one line and nothing else in the BOM moves."),
("C14663","C","expansion","100nF 50V X7R 0603",12,["C34","C35","C37","C38","C39","C40","C54","C58","C81","C82","C83","C120"],[],
  "General decoupling: six on the W5500's VDD/AVDD pins, C54 = the SCT2A25 bootstrap cap, C58 = U21 output HF bypass, three on the ESP32-S3 module supply, one on the EEPROM. JLC Basic, 104 M in stock."),
]

parts = []
tot_cost = 0.0
tot_pcs = 0
basic_n = ext_n = 0
tht_n = 0
lines = []
fails = []
for lcsc, pref, block, value, q, refs, alts, role in T:
    r = V[lcsc]
    order_qty = q * BUILD_QTY
    pb = sorted(r.get("price_breaks") or [], key=lambda b: b["qty"])
    price = r.get("price")
    for b in pb:
        if b["qty"] <= max(order_qty, 1):
            price = b["price"]
    line_cost = price * q
    tot_cost += line_cost
    tot_pcs += q
    if r.get("basic"):
        basic_n += 1
    else:
        ext_n += 1
    need = 5 * order_qty
    if order_qty > 0 and r["stock"] < need:
        fails.append((lcsc, r["stock"], need))
    e = {
        "ref_prefix_hint": pref, "block": block, "mpn": r["mpn"], "lcsc": lcsc,
        "value": value, "qty_per_board": q, "refs": refs,
        "package": r.get("package"), "basic": bool(r.get("basic")),
        "stock": r["stock"], "price": round(price, 4),
        "price_breaks": pb, "min_qty": r.get("min_qty"),
        "datasheet": r.get("datasheet"), "url": r.get("url"),
        "brand": r.get("brand"), "attributes": r.get("attributes"),
        "alternates": alts, "role": role,
    }
    parts.append(e)
    lines.append((lcsc, r["mpn"][:30], q, price, line_cost, r.get("basic"), r["stock"]))

os.makedirs(r"boards\lumina-carrier\parts", exist_ok=True)
json.dump({"parts": parts}, open(r"boards\lumina-carrier\parts\parts.json", "w"), indent=1)
for l in sorted(lines, key=lambda x: -x[4]):
    print("%-12s %-30s x%-3d @%-8.4f = %7.4f %s stk=%d" % (l[0], l[1], l[2], l[3], l[4], "B" if l[5] else "E", l[6]))
print()
print("stock-floor failures:", fails or "none")
print("distinct part lines:", len(parts), " Basic:", basic_n, " Extended:", ext_n)
print("placed components/board:", tot_pcs)
print("BOM cost per board (order-qty tiers, build %d): $%.2f" % (BUILD_QTY, tot_cost))
print("BOM cost for %d boards: $%.2f" % (BUILD_QTY, tot_cost * BUILD_QTY))
