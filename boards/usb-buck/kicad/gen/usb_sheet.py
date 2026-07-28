"""usb-buck `usb` sheet: micro-B receptacle J1 + in-line USBLC6 ESD array U3.

Refdes range 300s (architecture/sheets.md s2); pwr_base 300.
Exposes USB_DP / USB_DM to the root through sheet pins -> final netlist names
/USB_DP and /USB_DM (constraints.json's diff pair). VBUS and GND are power
SYMBOLS, hence global and bare - no sheet pins for rails.

Pinouts are the P3 ground truth, not memory:
  J1  parts.json C2939564 + lib symbol pin table: 1 VBUS, 2 D-, 3 D+, 4 ID,
      5 GND, and FOUR shield pads 6/7/8/9 all named "EP" - every one is
      bonded to GND (decisions.md item 5: direct shell->GND bond; a floating
      shield pad would also be an ERC/netlist hole).
  U3  parts/C2687116.json: 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1.
      Pins 1+6 are ONE internal node and 3+4 are ONE internal node (sec.4
      internal schematic), so the array sits in-line: the connector side
      lands on one pad of the pair and the MCU side on the other, giving
      layout a stub-free pass-through. Electrically each channel is a single
      net, so both pads carry the same label here.
      D- -> I/O1 (1 connector side, 6 MCU side); D+ -> I/O2 (3, 4).
      Pin 5 is the positive clamp reference -> VBUS (without it neither
      channel has an upper clamp path).
"""
from __future__ import annotations

from pathlib import Path

import kicad_sch_api as ksa

import schlib

BOARD = Path(__file__).resolve().parents[2]
# kicad-sch-api resolves lib_ids through its global cache, which does NOT
# read kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

LCSC = {"J1": "C2939564", "U3": "C2687116"}


def build() -> schlib.Sheet:
    sh = schlib.Sheet("usb", title="usb-buck: USB port + ESD", paper="A3",
                      date="2026-07-28", company="ai-ee", pwr_base=300)

    # ---- J1 micro-B receptacle -------------------------------------------
    sh.add_component("aiee:USB-111FD-B-SU", "J1", "USB Micro-B receptacle SMD",
                     at=(76.20, 127.00),
                     footprint=f"{FP}:USB-SMD_USB-111FD-B-SU",
                     expect={"1": "VBUS", "2": "D-", "3": "D+", "4": "ID",
                             "5": "GND", "6": "EP", "7": "EP", "8": "EP",
                             "9": "EP"})
    sh.wire_pins("J1", {
        "1": "VBUS",
        "2": "USB_DM",
        "3": "USB_DP",
        # ID: no-connect. This is a DEVICE-only port, no OTG/host role, so
        # the ID contact has no function (decisions.md item 4 rejects the
        # VBUS-sense/OTG hardware outright); leaving it floating without an
        # NC flag would be an ERC unconnected-pin error.
        "4": "NC",
        "5": "GND",
        # All four shield/EP pads bonded straight to GND (decision 5).
        "6": "GND", "7": "GND", "8": "GND", "9": "GND",
    })

    # ---- U3 USBLC6-2SC6, in-line ------------------------------------------
    sh.add_component("aiee:USBLC6-2SC6_C2687116", "U3", "USBLC6-2SC6",
                     at=(152.40, 127.00),
                     footprint=f"{FP}:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL",
                     expect={"1": "I/O1", "2": "GND", "3": "I/O2",
                             "4": "I/O2", "5": "VBUS", "6": "I/O1"})
    sh.wire_pins("U3", {
        "1": "USB_DM",   # connector-side I/O1 pad
        "6": "USB_DM",   # MCU-side I/O1 pad (same internal node as pin 1)
        "3": "USB_DP",   # connector-side I/O2 pad
        "4": "USB_DP",   # MCU-side I/O2 pad (same internal node as pin 3)
        "2": "GND",
        "5": "VBUS",
    })

    # ---- rails ------------------------------------------------------------
    # A local label is sheet-scoped; the power SYMBOL is what binds this
    # sheet's VBUS/GND labels to the global rails. The PWR_FLAGs live on the
    # power sheet (sheets.md s5 item 4) - one flag per global net is enough.
    sh.power_flag("VBUS", at=(76.20, 177.80), sym="power:VBUS", flag=False)
    sh.power_flag("GND", at=(76.20, 190.50), sym="power:GND", flag=False)

    # ---- cross-sheet pair -------------------------------------------------
    # Free-cluster variant (sheets.md s5 item 2): local label + hier label on
    # one stub, so the hier label joins by wire geometry, not name merging.
    sh.hier_pin("USB_DP", shape="bidirectional", at=(203.20, 121.92))
    sh.hier_pin("USB_DM", shape="bidirectional", at=(203.20, 134.62))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh
