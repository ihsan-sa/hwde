"""g0-sense `main` sheet: B3 MCU (STM32G030F6P6) + B4 SHT40 sensor,
I2C/Qwiic bus, SWD/UART headers, NRST button, user LED.

The schematic SOURCE is this file; `kicad/main.kicad_sch` is BUILD OUTPUT.
Rebuild standalone (from repo root):

    .venv/bin/python boards/g0-sense/kicad/gen/main_sheet.py

The root generator imports `build()` and stitches this sheet with
`schlib.Project.add_sheet(main_sheet.build(), at, size, nets=[])` - this
sheet exposes NO hier pins: `+3V3` and `GND` are GLOBAL power nets bound by
power symbols placed here (bare netlist names, no sheet pins), and every
signal net is sheet-local (final names `/main/SDA`, `/main/SCL`,
`/main/SWDIO`, `/main/SWCLK`, `/main/UART_TX`, `/main/UART_RX`,
`/main/NRST`, `/main/LED_USER`, plus the internal LED midnode
`/main/LED_A`).

Refdes ranges (architecture/sheets.md): U2-U9, J2-J9, D10-D19, R10-R19,
C10-C19, SW1-SW9; #PWR pwr_base=200. H1-H4 (M2 mounting holes) are
MECHANICAL and CONDITIONAL on the P6 layout - deliberately NOT placed in
the schematic (the generator idiom needs no symbol for them).

WIRING FACTS - ground truth, not memory
---------------------------------------
U2 STM32G030F6P6 TSSOP-20 (parts/C724040.json, DS12991 Table 12; canonical
pin map re-checked at P2 against research/refdesign-stm32g030-minimal.md):
  - pin 4 = VDD/VDDA (bonded; VBAT and VREF+ are internally bonded to it on
    this package, Sec 3.7.1), pin 5 = VSS/VSSA.
  - pin 6 = NRST: permanent internal pull-up RPU 25-55k (Table 52).
  - pin 9 = PA2 = USART2_TX, pin 10 = PA3 = USART2_RX, pin 12 = PA5 (user
    LED GPIO), pin 16 = PA9 (I2C1_SCL, symbol name "PA11[PA9]" - remap row),
    pin 17 = PA10 (I2C1_SDA, symbol name "PA12[PA10]"), pin 18 = PA13 =
    SWDIO, pin 19 = PA14 = SWCLK (bonded pad "PA15/PA14-BOOT0", doubles as
    the BOOT0 strap).
  - Unused pins 1/2/3/7/8/11/13/14/15/20 are GPIO bonded pads whose reset
    state is analog input (floating-safe, DS12991 Table 12); each gets an
    explicit no-connect flag so ERC is clean.
U3 SHT40-AD1B-R2 DFN-4 (parts/C2909890.json): 1 = SDA, 2 = SCL, 3 = VDD,
  4 = VSS. Symbol pin 5 = EP: the central die pad is "not directly
  connected to any pin" (DS Fig 11 caption) and the P3 footprint
  DELIBERATELY OMITS the die-pad copper per Sensirion Sec 5.3
  (sht4x-thermal-isolation-island) - explicit no-connect, nothing to wire.
SW1 TS-1187A-B-A-B: symbol drawing (aiee.kicad_sym, matches the XKB
  datasheet circuit) bars pins 1+2 (A/B) as ONE terminal and 3+4 (C/D) as
  the OTHER - wire both pads of each pair or a pad floats and one solder
  joint carries the contact.
J2 SM04B-SRSS-TB: pin order is FIXED by the Qwiic standard - 1 = GND,
  2 = 3.3V, 3 = SDA, 4 = SCL (P3 verified pin 1 against JST's own drawing;
  do not renumber). Pads 5/6 are the JST SH mechanical reinforcement tabs.
J3 SWD / J4 UART (sheets.md canonical, silk is the contract): both
  1 = GND, 2 = +3V3; J3 3 = SWDIO, 4 = SWCLK; J4 3 = TX (MCU transmit,
  PA2), 4 = RX (MCU receive, PA3). DNP - plated holes only, owner-soldered.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/g0-sense
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-28) - register the pulled lib, or
# save() silently guts lib_symbols (LEARNINGS 2026-08-06).
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

FP = "aiee"

V_100N = "100nF 50V X7R"
V_4U7 = "4.7uF 16V X5R"

# U2 TSSOP-20 pad -> net. Every unused pad is an explicit no-connect:
# DS12991 Table 12 resets all GPIOs to analog input (floating-legal), and
# nothing else on this board needs them. Specifically:
#  - 1 (PB7/PB8), 15 (PB0/PB1/PB2/PA8), 20 (PB3/PB4/PB5/PB6): unused
#    multi-bonded GPIO pads.
#  - 2 (PB9/PC14-OSC32_IN), 3 (PC15-OSC32_OUT): no LSE crystal on this
#    board (HSI16 internal oscillator, architecture/blocks.md B3).
#  - 7 (PA0), 8 (PA1), 11 (PA4), 13 (PA6), 14 (PA7): unused GPIOs.
U2_PINS = {
    "1": "NC", "2": "NC", "3": "NC",
    "4": "+3V3",        # VDD/VDDA (bonded - the ONLY supply pin)
    "5": "GND",         # VSS/VSSA (bonded - the ONLY ground pin)
    "6": "NRST",
    "7": "NC", "8": "NC",
    "9": "UART_TX",     # PA2 = USART2_TX (MCU transmit)
    "10": "UART_RX",    # PA3 = USART2_RX (MCU receive)
    "11": "NC",
    "12": "LED_USER",   # PA5 -> R12 -> D10
    "13": "NC", "14": "NC", "15": "NC",
    "16": "SCL",        # PA9 via SYSCFG remap row (symbol "PA11[PA9]"),
    "17": "SDA",        # PA10 (symbol "PA12[PA10]") - both FT_f: 5V-
                        # tolerant, Fm+-capable open-drain in I2C AF
    "18": "SWDIO",      # PA13, reset-default SWDIO (internal PU at reset)
    "19": "SWCLK",      # PA14/SWCLK/BOOT0 bonded pad + R13 strap below
    "20": "NC",
}

LCSC = {
    "U2": "C724040", "U3": "C2909890",
    "C10": "C14663", "C11": "C19666", "C12": "C14663", "C13": "C14663",
    "R10": "C22843", "R11": "C22843", "R12": "C22775", "R13": "C25804",
    "D10": "C2297", "SW1": "C318884",
    "J2": "C160404", "J3": "C32713270", "J4": "C32713270",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("main",
                      title="g0-sense: MCU + SHT40 + I2C/Qwiic + headers",
                      paper="A3", date="2026-08-27", company="ai-ee",
                      pwr_base=200)

    # ---- U2 + decoupling: exactly ONE 100nF + 4.7uF pair -----------------
    # TSSOP-20 bonds VDD/VDDA (and internally VBAT/VREF+) onto pin 4 and
    # VSS/VSSA onto pin 5, so the whole requirement collapses to ONE
    # network tight to the pin 4/5 pair; there is NO second (VDDA/VREF+)
    # network to add on this package (mcu-decoupling-bonded-vdda-single-pair,
    # mcu-decoupling-per-supply-pin-pair; DS12991 Fig 9 + Sec 3.7.1).
    sh.place_ic_with_decoupling(
        "U2", "aiee:STM32G030F6P6", "STM32G030F6P6",
        at=(215.90, 127.00), pins=U2_PINS,
        footprint=f"{FP}:TSSOP-20_L6.5-W4.4-P0.65-LS6.4-BL",
        expect={"4": "VDD", "5": "VSS", "6": "NRST", "9": "PA2",
                "10": "PA3", "12": "PA5", "16": "PA9", "17": "PA10",
                "18": "PA13", "19": "PA14"},
        decoupling=[
            {"cap": "C10", "pin": "4", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C11", "pin": "4", "rail": "+3V3", "value": V_4U7,
             "lib_id": "aiee:CL10A475KO8NNNC", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(45.72, 215.90), caps_dx=30.48)

    # ---- NRST: C12 100nF + SW1 button to GND, NO external pull-up --------
    # The G030's NRST pin has a PERMANENT internal pull-up (RPU 25-55k,
    # DS12991 Table 52); ST's Fig 19 network is exactly cap + button, cap
    # as close as possible to the device, and 100nF must NOT be oversized
    # (mcu-nrst-internal-pullup-and-cap). No series R on the button.
    sh.add_component("aiee:CC0603KRX7R9BB104", "C12", V_100N,
                     at=(76.20, 101.60), footprint=f"{FP}:C0603")
    sh.wire_pins("C12", {"1": "NRST", "2": "GND"})
    # 4-pad tactile switch: symbol bars 1+2 as one terminal, 3+4 as the
    # other - wire both pads of each pair so no pad floats.
    sh.add_component("aiee:TS-1187A-B-A-B", "SW1", "Tactile button",
                     at=(76.20, 127.00),
                     footprint=f"{FP}:SW-SMD_4P-L5.1-W5.1-P3.70-LS6.5-TL_H1.5",
                     expect={"1": "A", "2": "B", "3": "C", "4": "D"})
    sh.wire_pins("SW1", {"1": "NRST", "2": "NRST", "3": "GND", "4": "GND"})

    # ---- R13: 10k BOOT0 pull-down on pin 19 (PA14/SWCLK), POPULATED ------
    # DELIBERATE - do NOT optimise this away. The research record that
    # would have justified leaving BOOT0 unstrapped (factory option bytes
    # nBOOT_SEL=1 making the pin ignored) was REFUTED at the P2 coverage
    # exit: its only source is a community.st.com forum page and RM0454/
    # AN2606 could not be acquired (st.com unreachable from this
    # container). The pull-down holds BOOT0 = 0 at reset, so the board
    # boots main flash under EITHER option-byte state. It loads SWCLK with
    # ~330uA - negligible against any debugger's push-pull driver - and
    # pulls the same direction as PA14's own internal pull-down at reset.
    sh.add_component("aiee:0603WAF1002T5E", "R13", "10k",
                     at=(76.20, 152.40), footprint=f"{FP}:R0603")
    sh.wire_pins("R13", {"1": "SWCLK", "2": "GND"})

    # ---- user LED: PA5 -> R12 100R -> D10 green -> GND -------------------
    # R12 is 100R, NOT 220R - do not "correct" it back. D10 (KT-0805G) has
    # Vf 2.6-3.1V against the 3.3V rail: 220R gave only 0.9mA at the worst
    # Vf bin (dim); 100R gives 2-7mA across the bin spread, inside the
    # GPIO's rating (parts.json R12 entry, coordinator electrical fix).
    sh.add_component("aiee:0603WAF1000T5E", "R12", "100R",
                     at=(76.20, 177.80), footprint=f"{FP}:R0603")
    sh.wire_pins("R12", {"1": "LED_USER", "2": "LED_A"})
    sh.add_component("aiee:0805G", "D10", "Green 0805",
                     at=(114.30, 177.80), footprint=f"{FP}:LED0805-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D10", {"1": "LED_A", "2": "GND"})

    # ---- I2C pull-ups: R10/R11 1.5k to +3V3, ONCE, at the MCU host end ---
    # 1.5k, not 2.2k and not the SHT4x datasheet's 10k typical: UM10204
    # Eq 1 at tr = 300ns (Fast mode) gives Rp(max) = 354/Cb[pF] kOhm, so
    # the ceiling is only 1.77k at the 200pF end of the budget for the
    # on-board bus + ~0.5m Qwiic cable leg + one downstream device; 1.5k
    # holds the ceiling out to ~236pF and clears both floors (970R I2C-spec
    # at 3.3V/3mA, 390R SHT4x) - sht4x-i2c-pullup-bus-cap. Fitted once on
    # this board (the host); downstream nodes must not duplicate them.
    sh.add_component("aiee:0603WAF1501T5E", "R10", "1.5k",
                     at=(76.20, 63.50), footprint=f"{FP}:R0603")
    sh.wire_pins("R10", {"1": "SDA", "2": "+3V3"})
    sh.add_component("aiee:0603WAF1501T5E", "R11", "1.5k",
                     at=(76.20, 76.20), footprint=f"{FP}:R0603")
    sh.wire_pins("R11", {"1": "SCL", "2": "+3V3"})

    # ---- U3 SHT40 + C13 100nF at its VDD pin -----------------------------
    # C13 directly at the sensor's VDD/VSS pins, smallest loop: the on-chip
    # heater pulls up to 100mA (table max) and the supply must not sag into
    # a sensor reset (sht4x-vdd-decoupling-heater-transient). Pin 5 "EP" is
    # the die pad - not connected to any pin, and the P3 footprint has NO
    # die-pad copper per Sensirion (sht4x-thermal-isolation-island): NC.
    sh.place_ic_with_decoupling(
        "U3", "aiee:SHT40-AD1B-R2", "SHT40-AD1B-R2",
        at=(292.10, 165.10),
        pins={"1": "SDA", "2": "SCL", "3": "+3V3", "4": "GND", "5": "NC"},
        footprint=f"{FP}:DFN-4_L1.5-W1.5-P0.8-TL-EP",
        expect={"1": "SDA", "2": "SCL", "3": "VDD", "4": "VSS", "5": "EP"},
        decoupling=[
            {"cap": "C13", "pin": "3", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(266.70, 215.90))

    # ---- J2 Qwiic: pin order FIXED by the Qwiic standard -----------------
    # 1 = GND, 2 = 3.3V, 3 = SDA, 4 = SCL (P3 verified pin 1 against JST's
    # own drawing - do not renumber). Pads 5/6 are the JST SH mechanical
    # reinforcement tabs: solder anchors on the plastic housing, touching
    # no contact metal (J2_JST_eSH_official.pdf) - explicit no-connect so
    # the sensor-corridor copper stays unconstrained at P6/P7.
    sh.add_component("aiee:SM04B-SRSS-TB", "J2", "Qwiic JST SH 4P",
                     at=(304.80, 101.60),
                     footprint=f"{FP}:CONN-SMD_4P-P1.00_SM04B-SRSS-TB-LF-SN",
                     expect={"1": "1", "4": "4", "5": "5", "6": "6"})
    sh.wire_pins("J2", {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL",
                        "5": "NC", "6": "NC"})

    # ---- J3 SWD 1x4 (DNP): 1 GND, 2 +3V3, 3 SWDIO, 4 SWCLK ---------------
    # No vendor 4-pin SWD standard exists - sheets.md's silk labels are the
    # contract. SWDIO/SWCLK need no external resistors (silicon pulls at
    # reset, DS12991 Table 12 note 5); R13 on SWCLK is the BOOT0 strap.
    sh.add_component("aiee:HXPZ2.54-1X4PZZ", "J3", "1x4 2.54mm THT (DNP)",
                     at=(304.80, 50.80), footprint=f"{FP}:HDR-TH_4P-P2.54-V-M",
                     expect={"1": "1", "4": "4"})
    sh.wire_pins("J3", {"1": "GND", "2": "+3V3", "3": "SWDIO", "4": "SWCLK"})

    # ---- J4 UART 1x4 (DNP): 1 GND, 2 +3V3, 3 TX(=PA2), 4 RX(=PA3) --------
    # TX is MCU-transmit (UART_TX net), RX is MCU-receive - MCU-perspective
    # naming per architecture/blocks.md; silk labels per pin.
    sh.add_component("aiee:HXPZ2.54-1X4PZZ", "J4", "1x4 2.54mm THT (DNP)",
                     at=(304.80, 76.20), footprint=f"{FP}:HDR-TH_4P-P2.54-V-M",
                     expect={"1": "1", "4": "4"})
    sh.wire_pins("J4", {"1": "GND", "2": "+3V3", "3": "UART_TX",
                        "4": "UART_RX"})

    # ---- rails: power symbols bind this sheet's labels to the globals ----
    # +3V3/GND arrive as GLOBAL power nets (bare netlist names) - no sheet
    # pins. PWR_FLAGs live on the power sheet (rail entry owner), not here.
    sh.power_flag("+3V3", at=(139.70, 215.90), sym="power:+3V3", flag=False)
    sh.power_flag("GND", at=(139.70, 228.60), sym="power:GND", flag=False)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)

    # J3/J4 ship UNPOPULATED (Economy PCBA is SMT-only; owner hand-solders).
    # kicad-sch-api 0.5.6 cannot write the KiCad DNP flag (LEARNINGS
    # 2026-08-07) - the Variant field is the machine-readable record.
    for ref in ("J3", "J4"):
        sh.sch.components.get(ref).set_property("Variant", "DNP")

    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]      # .../kicad
    try:
        sh = build()
        # project=False: the ROOT generator owns g0-sense.kicad_pro and the
        # merged decoupling.json (Project.save collects children).
        sch = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.main_sheet", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.main_sheet", "status": "pass",
        "files": [str(sch)],
        "components": len(LCSC),
        "hier_pins": sorted(sh.hier_pins),   # [] - rails are global symbols
        "decoupling_associations": len(sh.decoupling),
        "place_report": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
