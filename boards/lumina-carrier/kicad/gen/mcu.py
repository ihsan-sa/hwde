"""LUM-CAR-A `mcu` sheet: ESP32-S3-WROOM-1-N8 + decoupling, EN/BOOT network,
recovery header J2, status LED D30.

Refdes range (architecture/sheets.md s2): U30-U39, J2, R100-R129, C80-C119,
D30-D39, SW1; pwr_base 400. The sheet NAME is contractual - sheet-internal
nets come out as `/mcu/NAME` and sheets.md s1.3 names five of them
(`/mcu/EN`, `/mcu/BOOT`, `/mcu/TXD0`, `/mcu/RXD0`, `/mcu/STATUS`).

+3V3 and GND are power SYMBOLS -> global and bare across the hierarchy, so
they get NO sheet pin (sheets.md s1.1). Their single PWR_FLAG lives on the
`pwr` sheet; do not add one here.

This sheet exposes 27 hierarchical pins - essentially every cross-sheet
signal on the board (sheets.md s1.2). The root stitches on these exact
names; `netlist_audit --constraints` fails on any mismatch.

GROUND TRUTH for every pin number below is parts/C2913198.json (Espressif
ESP32-S3-WROOM-1 / 1U datasheet v1.8), never memory. 41 pads: 40 castellated
+ EPAD(41). 3V3 = pin 2 (SOLE supply); GND = pins 1, 40, 41.

Three brick-class facts this sheet is built around:
  * GPIO45 (pad 26) must NOT be pulled high at power-up. On this no-PSRAM
    -N8 SKU a high GPIO45 selects a 1.8 V VDD_SPI and the 3.3 V on-module
    flash never boots. It is left as an explicit no-connect so only the
    internal weak pull-down (= 0) acts on it. NOTHING on this sheet touches
    it.
  * GPIO0 (pad 27) must read 1 at reset for SPI Boot. R101 10k to +3V3 holds
    the /mcu/BOOT net high; SW1 and J2 pin 6 can only pull it DOWN.
  * EN (pad 3) must never float: R100 10k to +3V3 + C85 1uF to GND, the
    Espressif Figure 9-1 RC (tSTBL >= 50 us; this RC reaches VIH ~14 ms
    after the rail, decades of margin, and it holds the strapping levels far
    longer than the tH >= 3 ms hold time).

Rebuild (standalone; the root generator is authoritative for the project):
    .venv/Scripts/python boards/lumina-carrier/kicad/gen/mcu.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

import schlib  # noqa: E402

# kicad-sch-api's global symbol cache never reads kicad/sym-lib-table, so a
# project library is invisible without this (LEARNINGS 2026-07-28).
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

# ---------------------------------------------------------------------------
# U30 pad -> net. Pad numbers and pad NAMES from parts/C2913198.json.
#
# The GPIO allocation is architecture/blocks.md s4.2 verbatim (28 of the 28
# legal GPIOs; the budget is exhausted). Every analogue function is on ADC1
# (GPIO1-10) because ADC2 is unusable while Wi-Fi is active, and Wi-Fi is a
# supported control path (H1 closed Q8).
#
# The five no-connects, each with its justification:
#   13 IO19 / 14 IO20 - USB_D-/D+. No USB-C on this board by design (a
#       non-isolated 802.3 PD may have no accessible non-isolated conductor,
#       sheets.md s2.4), and both pins carry 3.2 ms / 2.0 ms power-up glitch
#       windows. Left floating; the USB-Serial-JTAG PHY simply idles.
#   15 IO3  - strapping (JTAG source select) with NO internal pull. It may
#       only be used by a permanently-driven, never-Hi-Z output; nothing here
#       qualifies. With the default eFuses (all 0) its strap is Ignored.
#   16 IO46 - strapping (boot mode + ROM print), internal weak pull-DOWN = 0.
#       Boot mode is selected by GPIO0 alone (Table 4-3: SPI Boot needs
#       GPIO0 = 1, GPIO46 any value), so nothing needs to drive it.
#   26 IO45 - strapping (VDD_SPI select), internal weak pull-DOWN = 0 ->
#       VDD_SPI 3.3 V. See the module docstring: pulling it high bricks boot.
# ---------------------------------------------------------------------------
U30_PINS_SIDE = {
    # --- left column, pads 1-14 ------------------------------------------
    "1": "GND",
    "2": "+3V3",        # sole supply pin; >= 0.5 A source, 355 mA Wi-Fi TX
    "3": "EN",          # -> R100/C85 RC + J2 pin 5
    "4": "PWM0",        # IO4  - LEDC ch0, timer 0
    "5": "PWM1",        # IO5  - LEDC ch1, timer 0
    "6": "PWM2",        # IO6  - LEDC ch2, timer 0
    "7": "PWM3",        # IO7  - LEDC ch3, timer 0
    "8": "PWM4",        # IO15 - LEDC ch4, timer 1
    "9": "PWM5",        # IO16 - LEDC ch5, timer 1
    "10": "I2C_SCL",    # IO17
    "11": "I2C_SDA",    # IO18
    "12": "IMON",       # IO8  - ADC1_CH7, U22 current monitor
    "13": "NC",         # IO19 USB_D- - see note above
    "14": "NC",         # IO20 USB_D+ - see note above
    # --- right column, pads 27-41 ----------------------------------------
    "27": "BOOT",       # IO0  - strapping, held HIGH by R101
    "28": "PWM6",       # IO35 - LEDC ch6, timer 1 (free: no octal PSRAM)
    "29": "ENABLE",     # IO36 - no power-up glitch; this is why ENABLE is here
    "30": "FAULT",      # IO37 - input, open-drain wire-OR (pull-up on J4/pwr)
    "31": "PWM7",       # IO38 - LEDC ch7, timer 1
    "32": "DSPI_SCK",   # IO39 - SPI3 via the GPIO matrix; forfeits JTAG MTCK
    "33": "DSPI_MOSI",  # IO40 - forfeits MTDO
    "34": "DSPI_MISO",  # IO41 - forfeits MTDI
    "35": "DSPI_CSn",   # IO42 - forfeits MTMS
    "36": "RXD0",       # U0RXD = GPIO44 -> J2 pin 4
    "37": "TXD0",       # U0TXD = GPIO43 -> J2 pin 3
    "38": "ADC1",       # IO2  - ADC1_CH1
    "39": "ADC0",       # IO1  - ADC1_CH0
    "40": "GND",
    "41": "GND",        # EPAD - optional to solder, but grounded for thermals
}

# Bottom row, pads 15-26. Wired separately (see build()): twelve pins on a
# 2.54 mm pitch all stubbing DOWNWARD would stack nine horizontal labels on
# top of each other, so these get a longer stub and a vertical label. Same
# geometry contract as schlib.wire_pin - stub from the real pin position,
# label ON the wire endpoint.
U30_PINS_BOTTOM = {
    "15": "NC",         # IO3  - strapping, no internal pull - see note above
    "16": "NC",         # IO46 - strapping, weak pull-down - see note above
    "17": "ID_ADC",     # IO9  - ADC1_CH8, daughter ID divider
    "18": "ETH_CSn",    # IO10 - FSPICS0 (IO_MUX); 10k pull-up on the eth sheet
    "19": "ETH_MOSI",   # IO11 - FSPID
    "20": "ETH_SCLK",   # IO12 - FSPICLK
    "21": "ETH_MISO",   # IO13 - FSPIQ
    "22": "ETH_INTn",   # IO14 - FSPIWP, unused in 4-wire SPI
    "23": "ETH_RSTn",   # IO21 - plain GPIO, no ADC, no power-up glitch
    "24": "T2P",        # IO47 - Type-2 flag via U1's level shift on `poe`
    "25": "STATUS",     # IO48 - firmware heartbeat LED D30
    "26": "NC",         # IO45 - BRICK RISK, must not be pulled high
}

# expect={} on every pad: pin-name insurance against a wrong symbol. The
# module IS the sheet, so a wrong pin here is a dead board.
U30_EXPECT = {
    "1": "GND", "2": "3V3", "3": "EN", "4": "IO4", "5": "IO5", "6": "IO6",
    "7": "IO7", "8": "IO15", "9": "IO16", "10": "IO17", "11": "IO18",
    "12": "IO8", "13": "IO19", "14": "IO20", "15": "IO3", "16": "IO46",
    "17": "IO9", "18": "IO10", "19": "IO11", "20": "IO12", "21": "IO13",
    "22": "IO14", "23": "IO21", "24": "IO47", "25": "IO48", "26": "IO45",
    "27": "IO0", "28": "IO35", "29": "IO36", "30": "IO37", "31": "IO38",
    "32": "IO39", "33": "IO40", "34": "IO41", "35": "IO42", "36": "RXD0",
    "37": "TXD0", "38": "IO2", "39": "IO1", "40": "GND", "41": "EP",
}

# Cross-sheet nets, in the order the root should stitch them (sheets.md s1.2
# order). Shapes are this sheet's direction: the MCU drives PWM/DSPI/ETH
# control and reads the flags. Column split is layout only.
HIER_A = [
    ("T2P", "input"),          # U1 Type-2-detected flag, level-shifted
    ("ETH_SCLK", "output"),    # 22R series R lives on the `eth` sheet
    ("ETH_MOSI", "output"),
    ("ETH_MISO", "input"),
    ("ETH_CSn", "output"),
    ("ETH_INTn", "input"),
    ("ETH_RSTn", "output"),
    ("ENABLE", "output"),      # -> U22 SHDN + J4-23; R69 pull-down on `pwr`
    ("FAULT", "input"),        # open-drain wire-OR, pull-up on `expansion`
    ("IMON", "input"),         # U22 current monitor -> ADC1_CH7
    ("PWM0", "output"),
    ("PWM1", "output"),
    ("PWM2", "output"),
    ("PWM3", "output"),
]
HIER_B = [
    ("PWM4", "output"),
    ("PWM5", "output"),
    ("PWM6", "output"),
    ("PWM7", "output"),
    ("DSPI_SCK", "output"),
    ("DSPI_MOSI", "output"),
    ("DSPI_MISO", "input"),
    ("DSPI_CSn", "output"),
    ("I2C_SCL", "bidirectional"),   # 4k7 pull-ups on `expansion`
    ("I2C_SDA", "bidirectional"),
    ("ADC0", "input"),              # series R + clamp on `expansion`
    ("ADC1", "input"),
    ("ID_ADC", "input"),
]

# parts/parts.json is the ONLY refdes authority. Three symbols on this sheet
# carry a misleading Reference default and are overridden here:
#   C7430362 DS1021-1x6SF11-B -> symbol default "U",   must be J2
#   C2297    KT-0805G         -> symbol default "LED", must be D30
#   C380359  TCC1206X5R226M250HT -> symbol default "U", must be C80
LCSC = {
    "U30": "C2913198",
    "J2": "C7430362",
    "SW1": "C720477",
    "D30": "C2297",
    "R100": "C25804", "R101": "C25804", "R102": "C23138",
    "C80": "C380359",
    "C81": "C14663", "C82": "C14663", "C83": "C14663",
    "C84": "C15849", "C85": "C15849",
}

V_22U = "22uF 25V X5R"
V_100N = "100nF 50V X7R"
V_1U = "1uF 50V X5R"


def _stub_down(sh: schlib.Sheet, ref: str, pad: str, net: str,
               depth: float = 20.32) -> None:
    """wire_pin with a longer stub and a VERTICAL label, for a dense pin row.

    Identical electrical contract to schlib.wire_pin (stub from the real pin
    position, label on the wire ENDPOINT); only the stub length and the label
    angle differ, so twelve pins on a 2.54 mm pitch stay readable.
    """
    if net == "NC":
        sh.wire_pin(ref, pad, net)
        return
    p = sh.pin_pos(ref, pad)
    schlib.assert_on_grid(p, f"{ref} pin {pad}")
    d = sh._pin_out_dir(ref, pad)
    end = (round(p[0] + d[0] * depth, 4), round(p[1] + d[1] * depth, 4))
    sh.sch.add_wire(start=p, end=end)
    sh.sch.add_label(net, position=end, rotation=schlib._label_rotation(d))


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "mcu", title="LUM-CAR-A: ESP32-S3 module, EN/BOOT, recovery header",
        paper="A3", date="2026-07-28", company="ai-ee", pwr_base=400)

    # ---- U30 + module supply decoupling ----------------------------------
    # Espressif Figure 9-1 asks for 22 uF bulk + 0.1 uF at VDD33. sheets.md
    # s2.4 adds two more 100 nF and a 1 uF because the module must sustain a
    # 355 mA Wi-Fi TX burst (peak 500 mA supply requirement) out of LOCAL
    # bulk, not out of the 12->3.3 V converter's loop bandwidth.
    # rail "+3V3" is a global power SYMBOL name, so the wiring label and the
    # final netlist name are the same bare "+3V3" - no rail_net override.
    sh.place_ic_with_decoupling(
        "U30", "aiee:ESP32-S3-WROOM-1-N8", "ESP32-S3-WROOM-1-N8",
        at=(152.40, 152.40), pins=U30_PINS_SIDE,
        footprint=f"{FP}:WIFIM-SMD_ESP32-S3-WROOM-1-N8",
        expect=U30_EXPECT,
        decoupling=[
            {"cap": "C80", "pin": "2", "rail": "+3V3", "value": V_22U,
             "lib_id": "aiee:TCC1206X5R226M250HT", "footprint": f"{FP}:C1206"},
            {"cap": "C81", "pin": "2", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C82", "pin": "2", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C83", "pin": "2", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C84", "pin": "2", "rail": "+3V3", "value": V_1U,
             "lib_id": "aiee:CL10A105KB8NNNC", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(45.72, 228.60), caps_dx=30.48)

    # bottom pin row (pads 15-26) - see _stub_down
    for pad, net in sorted(U30_PINS_BOTTOM.items(), key=lambda kv: int(kv[0])):
        _stub_down(sh, "U30", pad, net)

    # rails: power symbols on the module's own supply/ground stubs make
    # "+3V3" and "GND" GLOBAL, which is what binds every other label of that
    # name on this sheet to the hierarchy-wide net. No PWR_FLAG here - the
    # rails are flagged once, on `pwr` (sheets.md s1.1).
    sh.power_symbol_at_pin("U30", "2", "power:+3V3")
    for pad in ("1", "40", "41"):
        sh.power_symbol_at_pin("U30", pad, "power:GND")

    # ---- EN network: 10k / 1uF RC (datasheet Section 9, Figure 9-1 R1/C2) --
    # "Do not leave the EN pin floating." R100 to +3V3, C85 to GND. J2 pin 5
    # taps the same node so a jig can hold the module in reset.
    sh.add_component("aiee:0603WAF1002T5E", "R100", "10k", at=(63.50, 127.00),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R100", {"1": "EN", "2": "+3V3"})
    sh.add_component("aiee:CL10A105KB8NNNC", "C85", V_1U, at=(63.50, 139.70),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C85", {"1": "EN", "2": "GND"})

    # ---- recovery header J2: 1 GND, 2 +3V3, 3 TXD0, 4 RXD0, 5 EN, 6 BOOT --
    # sheets.md s4. Inside the enclosure, no panel cutout. SILKSCREEN MUST
    # READ "PoE OFF or ISOLATED ADAPTER ONLY" (sheets.md s2.4 / s3.7): an
    # earthed USB-UART adapter ties the floating PoE return to earth and
    # breaks PD signature detection outright.
    sh.add_component("aiee:DS1021-1X6SF11-B", "J2",
                     "1x6 2.54mm header (recovery)", at=(63.50, 88.90),
                     footprint=f"{FP}:CONN-TH_DS1021-1X6SF11-B")
    sh.wire_pins("J2", {"1": "GND", "2": "+3V3", "3": "TXD0", "4": "RXD0",
                        "5": "EN", "6": "BOOT"})

    # ---- BOOT strap: 10k pull-up + optional tactile switch ----------------
    # GPIO0 has a weak INTERNAL pull-up and must read 1 for SPI Boot. R101
    # makes that idle-high explicit and stiff; SW1 (and J2 pin 6) can only
    # pull the net DOWN, for Joint Download Boot. Nothing on this sheet can
    # drive BOOT high other than the rail through R101.
    sh.add_component("aiee:0603WAF1002T5E", "R101", "10k", at=(215.90, 190.50),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R101", {"1": "BOOT", "2": "+3V3"})
    sh.add_component("aiee:TS-1088-AR02016", "SW1", "SMD tactile switch",
                     at=(215.90, 203.20), footprint=f"{FP}:SW-SMD_L3.9-W3.0-P4.45")
    sh.wire_pins("SW1", {"1": "BOOT", "2": "GND"})

    # ---- status LED: GPIO48 -> R102 330R -> D30 anode, cathode to GND -----
    # Source drive, ~3.6 mA at Vf 2.1 V - far inside the 40 mA IOH typ.
    # D30 is rotated 180 so the anode faces the resistor (symbol default puts
    # pin 1 = A on the right).
    sh.add_component("aiee:0603WAF3300T5E", "R102", "330R", at=(215.90, 228.60),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R102", {"1": "STATUS", "2": "STATUS_A"})
    sh.add_component("aiee:0805G", "D30", "Green LED 0805", at=(254.00, 228.60),
                     rotation=180, footprint=f"{FP}:LED0805-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D30", {"1": "STATUS_A", "2": "GND"})

    # ---- cross-sheet pins -------------------------------------------------
    # Free-cluster variant (sheets.md s3 note 3): a local label of the net
    # name plus the hierarchical label on ONE wire, so the hier label joins
    # the net by wire geometry and the local label merges with the pin stub.
    for i, (net, shape) in enumerate(HIER_A):
        sh.hier_pin(net, shape=shape, at=(292.10, 63.50 + i * 7.62))
    for i, (net, shape) in enumerate(HIER_B):
        sh.hier_pin(net, shape=shape, at=(355.60, 63.50 + i * 7.62))

    # ---- schematic notes (graphic text; carries no net, no ref) ----------
    # add_text is CENTRE-justified, so x is the middle of the string.
    for i, note in enumerate((
            "J2 SILKSCREEN: \"PoE OFF or ISOLATED ADAPTER ONLY\" - an earthed "
            "USB-UART adapter breaks PD signature detection",
            "GPIO45 (U30 pad 26) IS A NO-CONNECT BY DESIGN: pulled high at "
            "power-up on this no-PSRAM -N8 it selects 1.8 V VDD_SPI and the "
            "3.3 V flash never boots",
            "BOOT idles HIGH through R101 (GPIO0 = 1 -> SPI Boot); SW1 and "
            "J2 pin 6 can only pull it low",
            "Keep the antenna end of U30 (the pad 1 / pad 40 corner) clear of "
            "copper, parts and traces on EVERY layer")):
        sh.sch.add_text(note, position=(139.70, 241.30 + i * 6.35), size=1.27)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(BOARD / "kicad"),
                    help="directory to write mcu.kicad_sch into")
    ap.add_argument("--project", action="store_true",
                    help="also write mcu.kicad_pro (standalone ERC only; the "
                         "root generator owns the real project file)")
    args = ap.parse_args(argv)
    try:
        sh = build()
        path = sh.save(args.out, project=args.project)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.mcu", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.mcu", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
