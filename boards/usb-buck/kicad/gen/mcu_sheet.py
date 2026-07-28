"""usb-buck `mcu` sheet: STM32F103C8T6 core + HSE clock, user I/O, SWD.

Refdes range 200s (architecture/sheets.md s2); pwr_base 200.
Exposes USB_DP / USB_DM to the root (-> /USB_DP, /USB_DM); everything else
stays sheet-internal (-> /mcu/OSC_IN, /mcu/OSC_OUT, /mcu/NRST, /mcu/BOOT0,
/mcu/SWDIO, /mcu/SWCLK, /mcu/LED, /mcu/LED_A, /mcu/BTN). constraints.json
names /mcu/OSC_IN and /mcu/OSC_OUT, so the sheet name "mcu" is contractual.
+3V3 and GND are power SYMBOLS -> global and bare, no sheet pins.

Every pin number below is re-confirmed against parts/C8734.json (ST DS5319
Rev 18), not memory: PB0 = 18, PA11 = 32, PA12 = 33, PA13 = 34, PA14 = 37,
BOOT0 = 44, VDD 24/36/48, VSS 23/35/47, VDDA 9, VSSA 8, VBAT 1, NRST 7,
OSC_IN 5, OSC_OUT 6, PC13 2.
"""
from __future__ import annotations

from pathlib import Path

import kicad_sch_api as ksa

import schlib

BOARD = Path(__file__).resolve().parents[2]
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

V_100N = "100nF 50V X7R"
V_4U7 = "4.7uF 16V X5R"
V_1U = "1uF 50V X5R"
V_22P = "22pF 50V C0G"

# U1 LQFP-48 pad -> net. Unused GPIOs are explicit no-connects so ERC is
# clean (an unconnected pin is an error).
#  - PC14/PC15 (3/4): no 32.768 kHz LSE crystal on this board.
#  - PB2/BOOT1 (20): don't-care while BOOT0 is strapped low (sheets.md s4).
#  - PA0/WKUP (10): deliberately left free - standby wake-up needs an
#    active-HIGH edge, which the active-low SW1 would fight (decisions 11).
U1_PINS = {
    "1": "+3V3",       # VBAT - no battery/supercap fitted, tied to the rail
                       # (ASSUMED; DS5319 2.3.9 permits it, run (a) precedent)
    "2": "LED",        # PC13 sinks D1 (3 mA backup-domain limit -> R1 1k)
    "3": "NC", "4": "NC",
    "5": "OSC_IN",     # PD0-OSC_IN, HSE
    "6": "OSC_OUT",    # PD1-OSC_OUT
    "7": "NRST",
    "8": "GND",        # VSSA
    "9": "+3V3",       # VDDA
    "10": "NC", "11": "NC", "12": "NC", "13": "NC", "14": "NC",
    "15": "NC", "16": "NC", "17": "NC",
    "18": "BTN",       # PB0 - user button, active low
    "19": "NC", "20": "NC", "21": "NC", "22": "NC",
    "23": "GND",       # VSS_1
    "24": "+3V3",      # VDD_1
    "25": "NC", "26": "NC", "27": "NC", "28": "NC", "29": "NC",
    "30": "NC", "31": "NC",
    "32": "USB_DM",    # PA11 / USBDM - no series resistors (the F103 PHY's
    "33": "USB_DP",    # PA12 / USBDP    output impedance is internal)
    "34": "SWDIO",     # PA13 / JTMS-SWDIO (reset default)
    "35": "GND",       # VSS_2
    "36": "+3V3",      # VDD_2
    "37": "SWCLK",     # PA14 / JTCK-SWCLK (reset default)
    "38": "NC", "39": "NC", "40": "NC", "41": "NC", "42": "NC", "43": "NC",
    "44": "BOOT0",     # R3 10k pull-down -> boot from user flash
    "45": "NC", "46": "NC",
    "47": "GND",       # VSS_3
    "48": "+3V3",      # VDD_3 (DS 5.1.6: the bulk cap belongs at this pin)
}

LCSC = {
    "U1": "C8734", "Y1": "C12674", "J2": "C32713270", "D1": "C2286",
    "SW1": "C49023761",
    "R1": "C21190", "R2": "C25804", "R3": "C25804", "R4": "C22843",
    "C10": "C1653", "C11": "C1653",
    "C12": "C14663", "C13": "C14663", "C14": "C14663",
    "C15": "C19666", "C16": "C14663", "C17": "C15849",
    "C18": "C14663", "C19": "C14663",
}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("mcu", title="usb-buck: MCU core, clock, I/O, SWD",
                      paper="A3", date="2026-07-28", company="ai-ee",
                      pwr_base=200)

    # ---- U1 + the full ST F1 decoupling scheme (decisions.md item 9) ------
    # 100 nF per VDD/VSS pair (C12/C13/C14), 4.7 uF bulk at VDD_3 (C15),
    # VDDA 1 uF + 100 nF (C17/C16 - kept, not waived: VDDA sits on the
    # buck's 1.1 MHz rail), 100 nF on VBAT (C18).
    sh.place_ic_with_decoupling(
        "U1", "aiee:STM32F103C8T6", "STM32F103C8T6",
        at=(215.90, 127.00), pins=U1_PINS,
        footprint=f"{FP}:LQFP-48_L7.0-W7.0-P0.50-LS9.0-BL",
        expect={"1": "VBAT", "2": "PC13", "5": "OSC_IN", "6": "OSC_OUT",
                "7": "NRST", "8": "VSSA", "9": "VDDA", "18": "PB0",
                "20": "PB2", "23": "VSS_1", "24": "VDD_1", "32": "PA11",
                "33": "PA12", "34": "PA13", "35": "VSS_2", "36": "VDD_2",
                "37": "PA14", "44": "BOOT0", "47": "VSS_3", "48": "VDD_3"},
        decoupling=[
            {"cap": "C12", "pin": "24", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C13", "pin": "36", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C14", "pin": "48", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C15", "pin": "48", "rail": "+3V3", "value": V_4U7,
             "lib_id": "aiee:CL10A475KO8NNNC", "footprint": f"{FP}:C0603"},
            {"cap": "C16", "pin": "9", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
            {"cap": "C17", "pin": "9", "rail": "+3V3", "value": V_1U,
             "lib_id": "aiee:CL10A105KB8NNNC", "footprint": f"{FP}:C0603"},
            {"cap": "C18", "pin": "1", "rail": "+3V3", "value": V_100N,
             "lib_id": "aiee:CC0603KRX7R9BB104", "footprint": f"{FP}:C0603"},
        ],
        caps_at=(45.72, 241.30), caps_dx=30.48)

    # ---- HSE clock: Y1 8 MHz + C10/C11 load caps --------------------------
    # Y1 is a CL = 20 pF part. C = 2 * (CL - C_stray); DS5319 5.3.6 puts the
    # PCB+pin stray at ~10 pF, giving 20 pF, and 22 pF is the nearest E-series
    # value - which is also what sheets.md/parts.json committed to (C1653,
    # C0G). No series damping resistor (sheets.md s2).
    sh.add_component("aiee:X49SM8MSD2SC", "Y1", "8MHz 20pF", at=(76.20, 76.20),
                     footprint=f"{FP}:CRYSTAL-SMD_L11.5-W4.8-LS12.7",
                     expect={"1": "OSC1", "2": "OSC2"})
    sh.wire_pins("Y1", {"1": "OSC_IN", "2": "OSC_OUT"})
    sh.add_component("aiee:CL10C220JB8NNNC", "C10", V_22P, at=(76.20, 96.52),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C10", {"1": "OSC_IN", "2": "GND"})
    sh.add_component("aiee:CL10C220JB8NNNC", "C11", V_22P, at=(76.20, 109.22),
                     footprint=f"{FP}:C0603")
    sh.wire_pins("C11", {"1": "OSC_OUT", "2": "GND"})

    # ---- NRST protection cap (DS5319 Figure 31) ---------------------------
    sh.add_component("aiee:CC0603KRX7R9BB104", "C19", V_100N,
                     at=(76.20, 127.00), footprint=f"{FP}:C0603")
    sh.wire_pins("C19", {"1": "NRST", "2": "GND"})

    # ---- BOOT0 strap: 10k to GND (fixed; the button is NOT a boot select) -
    sh.add_component("aiee:0603WAF1002T5E", "R3", "10k", at=(76.20, 139.70),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R3", {"1": "BOOT0", "2": "GND"})

    # ---- user button: SW1 to GND + R2 10k pull-up (decisions.md item 11) --
    sh.add_component("aiee:0603WAF1002T5E", "R2", "10k", at=(76.20, 152.40),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R2", {"1": "BTN", "2": "+3V3"})
    # 4-pad tactile switch: the symbol draws pins 1+2 on one internal bar and
    # 3+4 on the other, so each PAIR is one terminal - wire both pads of each
    # pair or a pad floats (ERC) and one solder joint carries the contact.
    sh.add_component("aiee:TS263065A340GFSXBDSMDTACTILESWITCH", "SW1",
                     "SMD tactile switch", at=(76.20, 177.80),
                     footprint=f"{FP}:SW-SMD_4P-L3.0-W2.6-P1.80-LS3.4-TL")
    sh.wire_pins("SW1", {"1": "BTN", "2": "BTN", "3": "GND", "4": "GND"})

    # ---- status LED: +3V3 -> R1 1k -> LED_A -> D1 -> LED -> PC13 sink -----
    sh.add_component("aiee:KT-0603R", "D1", "Red 0603", at=(76.20, 203.20),
                     footprint=f"{FP}:LED-SMD_L1.6-W0.8-R-RD",
                     expect={"1": "A", "2": "K"})
    sh.wire_pins("D1", {"1": "LED_A", "2": "LED"})
    sh.add_component("aiee:0603WAF1001T5E", "R1", "1k", at=(114.30, 203.20),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R1", {"1": "LED_A", "2": "+3V3"})

    # ---- USB D+ pull-up: MANDATORY, hard-wired (decisions.md item 3) ------
    # 1.5 k 1% to +3V3; the F103 has no internal USB pull-up and the 10 k many
    # Blue Pill clones fit fails enumeration. Lives on this sheet because
    # sheets.md s2 allocates R1-R4 to the mcu range (the net is /USB_DP either
    # way) and the pull-up belongs on the MCU side of the ESD array.
    sh.add_component("aiee:0603WAF1501T5E", "R4", "1.5k", at=(76.20, 215.90),
                     footprint=f"{FP}:R0603")
    sh.wire_pins("R4", {"1": "USB_DP", "2": "+3V3"})

    # ---- SWD header J2: 1 +3V3, 2 SWCLK, 3 GND, 4 SWDIO -------------------
    # ST Nucleo CN4 debug-row order minus NRST/SWO (decisions.md item 12 /
    # sheets.md s3); the +3V3 pin is a reference OUTPUT.
    sh.add_component("aiee:HXPZ2.54-1X4PZZ", "J2", "1x4 2.54mm male THT",
                     at=(304.80, 127.00), footprint=f"{FP}:HDR-TH_4P-P2.54-V-M")
    sh.wire_pins("J2", {"1": "+3V3", "2": "SWCLK", "3": "GND", "4": "SWDIO"})

    # ---- rails (power symbols bind this sheet's labels to the globals) ----
    sh.power_flag("+3V3", at=(304.80, 215.90), sym="power:+3V3", flag=False)
    sh.power_flag("GND", at=(304.80, 228.60), sym="power:GND", flag=False)

    # ---- cross-sheet pair --------------------------------------------------
    sh.hier_pin("USB_DP", shape="bidirectional", at=(304.80, 165.10))
    sh.hier_pin("USB_DM", shape="bidirectional", at=(304.80, 177.80))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh
