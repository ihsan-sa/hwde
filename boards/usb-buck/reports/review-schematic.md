# Schematic review: usb-buck (adversarial, P4)

Reviewer stance: assume the generated schematic is wrong; verify every net
against datasheet ground truth (parts/C8734.json, parts/C5248536.json,
parts/C2687116.json), architecture/decisions.md, architecture/constraints.json,
and the four applicable checklists (power, mcu, connector, interface-usb).
Evidence base: reports/schematic.pdf (rendered + read), reports/top.net
(exported + read net-by-net), kicad/decoupling.json, lib/aiee.kicad_sym,
lib/aiee.pretty/*, reports/fp_verify_*.json. ERC 0/0 and netlist_audit were
already green; this review targets what those gates cannot see.

Verdict: 0 errors, 2 warnings. The as-built netlist is correct against every
ground-truth document I could obtain. Both warnings trace to parts whose
vendor documentation is weaker than the rest of the board, not to wiring
mistakes by the generator.

## What was positively verified (not just "no finding")

USB path (interface-usb checklist):
- /USB_DM = J1.2 (D-) + U3.1/U3.6 (I/O1) + U1.32 (PA11 = USBDM).
  /USB_DP = J1.3 (D+) + U3.3/U3.4 (I/O2) + U1.33 (PA12 = USBDP) + R4.1.
  No D+/D- swap at connector, ESD array, or MCU.
- R4 = 1.5k 1% from USB_DP to +3V3: correct line (D+ only), correct value,
  hard-wired per settled decision 3. No pull on D-. No series R / ferrites /
  edge caps on the pair (settled decision 6; correct for F103 FS).
- U3 USBLC6-2SC6: both pads of each internally-joined pin pair sit on the
  line net (flow-through by design, per C2687116.json sec.4 topology);
  VBUS clamp pin 5 tied to VBUS; GND pin 2 to GND. DM on channel 1, DP on
  channel 2 - matched-capacitance requirement trivially met.
- J1 (HOOYA USB-111FD-B-SU, fp_verify pass against the vendor drawing):
  pin 1 VBUS, 5 GND, ID (4) correctly NC for a B-device, all four shield
  lands (EP 6-9) bonded directly to GND per settled decision 5.
- VBUS net carries exactly J1.1, C1 (10uF), C2 (100nF), U2.VIN, U2.EN,
  U3.5 - the 10uF USB inrush ceiling of decision 7 is honored, nothing
  extra crept onto VBUS.

Buck (power checklist, vs C5248536.json):
- FB (U2.1) tied to +3V3 = VOUT, exactly what the fixed-output AP63203Q
  datasheet demands ("tie the FB pin directly to VOUT ... no R1/R2/C4").
  Not on SW, not on GND, no spurious divider.
- EN (U2.2) tied to VBUS = VIN: the datasheet's stated connection
  ("Connect to VIN ... for automatic startup"); EN abs max 35V, applied
  5.25V worst case. Enabled whenever VBUS present - intended behavior for
  a bus-powered board. It does not float.
- BST cap C3 100nF correctly bridges BST (U2.6) to SW (U2.5) - not to GND.
- L1 from SW to +3V3; output caps C4/C5 = 2x22uF ceramic per DS Table 2
  (internal compensation assumes ceramic - honored).
- Input caps at VIN: 10uF + 100nF HF, both on VBUS/GND. Dropout: fixed
  3.3V from >=4.75V VBUS clears POR-rising max 3.7V; low-dropout mode
  covers the rest. No sequencing hazards (single cascaded rail).

MCU (mcu checklist, vs C8734.json):
- All three VDD (24/36/48) + VDDA (9) + VBAT (1) on +3V3; all three VSS
  (23/35/47) + VSSA (8) on GND. No U1 pin touches VBUS (5V) anywhere -
  abs-max clean by construction.
- Decoupling is the full ST F1 scheme and kicad/decoupling.json binds each
  cap to its pin: C12->VDD_1(24), C13->VDD_2(36), C14->VDD_3(48),
  C15 4.7uF bulk ->VDD_3(48) (the DS 5.1.6 caution honored), C16 100nF +
  C17 1uF ->VDDA(9), C18->VBAT(1). C19 100nF on NRST per Figure 31.
  (VDDA pair is 1uF+100nF vs the DS's 1uF+10nF - settled decision 9,
  not re-litigated; no ADC in use.)
- BOOT0 strapped to GND through R3 10k (boot from flash); BOOT1/PB2
  floating is don't-care while BOOT0=0 and no boot jumper exists (settled).
- NRST: 100nF to GND, internal 40k pull-up, no external pull - per DS.
- Crystal: Y1 8MHz CL=20pF with C10/C11 22pF C0G on OSC_IN/OSC_OUT
  (pins 5/6). 22pF implies assumed Cstray ~9pF vs the DS's ~10pF rough
  estimate; effective CL ~20-21pF, frequency error tens of ppm against a
  2500 ppm USB FS budget - value is right.
- LED: PC13 -> D1 cathode, D1 anode -> R1 1k -> +3V3. Sink topology
  (PC13 must not source - DS Table 5 note 5), 1.4mA < 3mA backup-domain
  limit. Polarity is datasheet-verified: fp_verify_D1 record confirms
  KT-0603R pin 1 marked '+' = anode = symbol pin A.
- Unused GPIOs NC-flagged (ERC 0/0), no floating inputs that matter.

Connector / debug:
- J2 SWD: 1=+3V3(ref out), 2=SWCLK(PA14), 3=GND, 4=SWDIO(PA13) - matches
  settled decision 12 (Nucleo CN4 order), pins verified in netlist.
- Hierarchy contract: exactly two cross-sheet nets (/USB_DP, /USB_DM);
  constraint net names (/mcu/OSC_IN, /mcu/OSC_OUT, VBUS, +3V3) all exist
  verbatim in the exported netlist.

## Findings

### W1 (warning) SW1 internal pin pairing is unverifiable - button may be
permanently closed if the assumption is wrong
SW1 (SHOU HAN TS263065A, C49023761) has NO manufacturer datasheet (parts.json
admits the listing carries none). The schematic bridges pins {1,2}=BTN and
{3,4}=GND. That matches the LCSC/EasyEDA vendor symbol, which draws internal
bars joining 1-2 and 3-4, and the footprint's row layout (1,2 top row / 3,4
bottom row) - but the only authority is the vendor EDA library, not a part
datasheet. Small 4-pad SMD tacts exist in a same-column construction
({1,4}/{2,3}); if this part is built that way, BTN is shorted to GND through
the switch body regardless of press state: PB0 reads permanently low, the
user-button requirement is dead, +0.33mA burned in R2. No damage, and USB /
SWD / LED bring-up are unaffected. 30-second continuity check on a loose part
at bring-up settles it; rework if wrong is two lifted pins.

### W2 (warning) UMW USBLC6-2SC6 working-voltage rating is 5.0V but USB VBUS
may legally reach 5.25V
The UMW clone's datasheet (C2687116.json) specifies VRWM = 5V as the working
limit for the I/O and VBUS pins and has no abs-max supply row; the USB spec
range stated in requirements.md is 4.75-5.25V. Above VRWM nothing breaks
(VBR min 6V, clamp still ~10V at 1A), but leakage is no longer bounded by the
100nA spec and clamping margin shrinks - a spec-compliance gap introduced by
the clone substitution (the ST-brand original is rated 5.25V and is already
listed as alternate C7519 in parts.json; drop-in at order time, zero
schematic change).

## Not findings (checked and dismissed)
- Flow-through wiring of U3 (pins 1+6 / 3+4 on one net each): by design of
  the rail-clamp silicon; not a short.
- EN to VBUS, FB to +3V3, hard-wired 1.5k pull-up, VBAT to +3V3, 1k LED,
  buck-vs-LDO, no VBUS sense, 4-pin SWD without NRST, shield direct bond,
  L1 DCR waiver: all settled architecture decisions, verified implemented
  as decided.
- Sheet page-number cosmetics in the PDF title blocks (pages 2-4 all print
  "Id: 2/4"): cosmetic only, excluded per no-style-nits rule.

## Open (could not verify from files on disk)
- Physical realization of the U3 flow-through (pair entering pads 1/3 from
  J1 and leaving 6/4 to U1, not a stub) and the FB tap point relative to
  L1/C4/C5: both are single-net layout properties the netlist cannot
  express - confirm in the layout/routing review phase.
- J1 signal-pin ORDER rests on the fp_verify record plus the micro-B
  standard pin assignment; no parts/C2939564.json pin-table extract exists
  to cross-read (geometry was verified against the vendor drawing; pin
  order of micro-B receptacles is fixed by the USB spec, so residual risk
  is negligible).
- SW1 pairing (W1) - needs the physical part or a real datasheet.
