"""Generator for the stm32-blinky root schematic (single flat sheet).

Schematic SOURCE is this Python file; `../stm32-blinky.kicad_sch` (+ the
.kicad_pro and ../decoupling.json) are BUILD OUTPUT. Rebuild:

    .venv/Scripts/python boards/stm32-blinky/kicad/gen/root.py

Wiring facts come from the datasheet-extract JSONs (parts/C8734.json,
parts/C6186.json) and architecture/sheets.md's canonical net table; symbols
are the pulled project lib lib/aiee.kicad_sym (registered in
kicad/sym-lib-table as `aiee`). `expect` entries pin the load-bearing pin
names against the library at build time.

Canonical nets (architecture/sheets.md): power rails bare (+5V, +3V3, GND -
power symbols force global names), all signal labels root-local -> "/NAME"
in the netlist (/VIN /SWDIO /SWCLK /LED_A /LED /OSC_IN /OSC_OUT /NRST
/BOOT0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/stm32-blinky
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402
import kicad_sch_api as ksa  # noqa: E402

# Project symbol lib: kicad-sch-api resolves lib_ids through its global
# cache, which does not read sym-lib-table - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"  # footprint lib nickname (kicad/fp-lib-table)

# STM32F103C8T6 LQFP-48 pad -> net (parts/C8734.json ground truth; sheets.md
# pin commitments). Every unused GPIO is an explicit no-connect.
# PB2/BOOT1 (20): NC - don't-care with BOOT0 strapped low (sheets.md).
# PC14/PC15 (3/4): NC - no 32.768 kHz LSE crystal on this board.
U1_PINS = {
    "1": "+3V3",       # VBAT: no battery, tied to +3V3 (sheets.md, ASSUMED)
    "2": "LED",        # PC13 sinks the LED, active-low
    "3": "NC", "4": "NC",
    "5": "OSC_IN",     # PD0-OSC_IN, HSE crystal
    "6": "OSC_OUT",    # PD1-OSC_OUT
    "7": "NRST",       # 100nF protection cap C9
    "8": "GND",        # VSSA
    "9": "+3V3",       # VDDA
    "10": "NC", "11": "NC", "12": "NC", "13": "NC", "14": "NC",
    "15": "NC", "16": "NC", "17": "NC", "18": "NC", "19": "NC",
    "20": "NC",        # PB2/BOOT1: floating is fine with BOOT0=0
    "21": "NC", "22": "NC",
    "23": "GND",       # VSS_1
    "24": "+3V3",      # VDD_1
    "25": "NC", "26": "NC", "27": "NC", "28": "NC", "29": "NC",
    "30": "NC", "31": "NC", "32": "NC", "33": "NC",
    "34": "SWDIO",     # PA13 / JTMS-SWDIO
    "35": "GND",       # VSS_2
    "36": "+3V3",      # VDD_2
    "37": "SWCLK",     # PA14 / JTCK-SWCLK
    "38": "NC", "39": "NC", "40": "NC", "41": "NC", "42": "NC", "43": "NC",
    "44": "BOOT0",     # R2 10k pulldown -> boot from main flash
    "45": "NC", "46": "NC",
    "47": "GND",       # VSS_3
    "48": "+3V3",      # VDD_3 (datasheet: bulk cap belongs at this pin)
}

# Values are the SOURCED parts (parts/parts.json), not datasheet ideals:
# - VDD bulk 4.7uF (DS 5.1.6) not sourced -> C5 10uF at the LDO output is
#   the board's bulk (blocks.md decision).
# - VDDA 1uF//10nF (DS Fig.40) not sourced -> C4 100nF (closest sourced).
V_100N = "100nF 50V X7R"
V_10U = "10uF 25V X5R"
V_22P = "22pF 50V C0G"

# refdes -> LCSC part number (parts/parts.json), stamped as an LCSC field
# on every placed component for the downstream BOM.
LCSC = {
    "U1": "C8734", "U2": "C6186", "D1": "C8678", "D2": "C84256",
    "Y1": "C12674", "R1": "C21190", "R2": "C25804",
    "C1": "C14663", "C2": "C14663", "C3": "C14663", "C4": "C14663",
    "C5": "C15850", "C6": "C15850", "C7": "C1653", "C8": "C1653",
    "C9": "C14663", "J1": "C32713268", "J2": "C32713270",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("stm32-blinky",
                      title="stm32-blinky: STM32F103C8T6 blinky board",
                      paper="A3", date="2026-07-27", company="ai-ee",
                      pwr_base=1)

    # ---- MCU core: U1 + C1-C3 (VDD 48/24/36) + C4 (VDDA 9) ----
    sh.place_ic_with_decoupling(
        "U1", "aiee:STM32F103C8T6", "STM32F103C8T6",
        at=(218.44, 152.4), pins=U1_PINS,
        footprint=f"{FP}:LQFP-48_L7.0-W7.0-P0.50-LS9.0-BL",
       
        expect={"1": "VBAT", "2": "PC13", "5": "OSC_IN", "6": "OSC_OUT",
                "7": "NRST", "8": "VSSA", "9": "VDDA", "20": "PB2",
                "23": "VSS_1", "24": "VDD_1", "34": "PA13", "36": "VDD_2",
                "37": "PA14", "44": "BOOT0", "47": "VSS_3", "48": "VDD_3"},
        decoupling=[
            {"cap": "C1", "pin": "48", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C2", "pin": "24", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C3", "pin": "36", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C4", "pin": "9", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(190.5, 198.12), caps_dx=20.32)

    # ---- Regulation: U2 AMS1117-3.3 + C5 out / C6 in (10uF) ----
    # Pin 4 = SOT-223 tab = VOUT (C6186.json: "tie to VOUT net, never GND").
    sh.place_ic_with_decoupling(
        "U2", "aiee:AMS1117-3.3", "AMS1117-3.3",
        at=(96.52, 58.42),
        pins={"1": "GND", "2": "+3V3", "3": "+5V", "4": "+3V3"},
        footprint=f"{FP}:SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
       
        expect={"1": "GND", "2": "VOUT", "3": "VIN", "4": "VOUT"},
        decoupling=[
            {"cap": "C5", "pin": "2", "rail": "+3V3", "value": V_10U,
             "lib_id": "aiee:CL21A106KAYNNNE", "footprint": f"{FP}:C0805"},
            {"cap": "C6", "pin": "3", "rail": "+5V", "value": V_10U,
             "lib_id": "aiee:CL21A106KAYNNNE", "footprint": f"{FP}:C0805"},
        ],
        caps_at=(86.36, 73.66), caps_dx=20.32)

    # ---- Power input: J1 (1=5V in, 2=GND) -> D1 SS34 series Schottky ----
    sh.add_component(f"aiee:HXPZ2.54-1X2PZZ", "J1", "1x2 2.54mm male THT",
                     at=(48.26, 58.42),
                     footprint=f"{FP}:HDR-TH_2P-P2.54-V-M-3")
    sh.wire_pins("J1", {"1": "VIN", "2": "GND"})
    # D1: anode (pin 2) to the raw /VIN stub, cathode (pin 1) feeds +5V.
    sh.add_component("aiee:SS34_C8678", "D1", "SS34", at=(66.04, 66.04),
                    
                     footprint=f"{FP}:SMA_L4.3-W2.6-LS5.2-RD",
                     expect={"1": "K", "2": "A"})
    sh.wire_pins("D1", {"1": "+5V", "2": "VIN"})

    # ---- SWD debug: J2 1=SWDIO 2=SWCLK 3=3V3 4=GND (requirements order) --
    sh.add_component("aiee:HXPZ2.54-1X4PZZ", "J2", "1x4 2.54mm male THT",
                     at=(299.72, 149.86),
                     footprint=f"{FP}:HDR-TH_4P-P2.54-V-M")
    sh.wire_pins("J2", {"1": "SWDIO", "2": "SWCLK", "3": "+3V3", "4": "GND"})

    # ---- Clock: Y1 8MHz HC-49S + 22pF load caps at the crystal ----
    sh.add_component("aiee:X49SM8MSD2SC", "Y1", "8MHz 20pF",
                     at=(147.32, 172.72),
                     footprint=f"{FP}:CRYSTAL-SMD_L11.5-W4.8-LS12.7",
                     expect={"1": "OSC1", "2": "OSC2"})
    sh.wire_pins("Y1", {"1": "OSC_IN", "2": "OSC_OUT"})
    sh.add_component("aiee:CL10C220JB8NNNC", "C7", V_22P,
                     at=(137.16, 185.42),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C7", {"1": "OSC_IN", "2": "GND"})
    sh.add_component("aiee:CL10C220JB8NNNC", "C8", V_22P,
                     at=(157.48, 185.42),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C8", {"1": "OSC_OUT", "2": "GND"})

    # ---- User LED: +3V3 -> R1 1k -> /LED_A -> D2 -> /LED -> PC13 sink ----
    sh.add_component("aiee:0603WAF1001T5E", "R1", "1k", at=(190.5, 218.44),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R1", {"1": "+3V3", "2": "LED_A"})
    sh.add_component("aiee:FC-2012HRK-620D", "D2", "Red 0805",
                     at=(210.82, 218.44),
                     footprint=f"{FP}:LED0805-RD",
                     expect={"1": "-", "2": "+"})
    sh.wire_pins("D2", {"1": "LED", "2": "LED_A"})

    # ---- BOOT0 strap (10k to GND) + NRST protection cap ----
    sh.add_component("aiee:0603WAF1002T5E", "R2", "10k", at=(231.14, 218.44),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R2", {"1": "BOOT0", "2": "GND"})
    sh.add_component("aiee:CC0603KRX7R9BB104", "C9", V_100N,
                     at=(251.46, 218.44),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C9", {"1": "NRST", "2": "GND"})

    # ---- Power rails ----
    # Power symbols force the bare global names (+5V/+3V3/GND win over the
    # local wiring labels). GND and +5V are driven only by a connector/diode;
    # +3V3 by U2's VOUT (power_out) - PWR_FLAG only where nothing drives.
    sh.power_flag("GND", at=(43.18, 236.22), sym="power:GND", flag=True)
    sh.power_flag("+5V", at=(43.18, 246.38), sym="power:+5V", flag=True)
    sh.power_symbol_at_pin("C5", "1", "power:+3V3")

    # ---- LCSC part-number fields (downstream BOM keys on them) ----
    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]  # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.stm32-blinky", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.stm32-blinky", "status": "pass",
        "files": [str(sch), str(out_dir / "stm32-blinky.kicad_pro"),
                  str(meta)],
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
