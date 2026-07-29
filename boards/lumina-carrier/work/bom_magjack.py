"""parts.json: retire C91754, add the LPJG0926HENL magjack, the two PD input
bridges and the recomputed RDEN half-value. ASCII only, existing key order.

refs / qty_per_board are written here for readability but are NOT authoritative
- work/bom_sync.py rebuilds them from the exported netlist and is run last.
"""
from __future__ import annotations

import io
import json

PARTS = r"C:\dev\ai-ee3\boards\lumina-carrier\parts\parts.json"

NEW = {
    "C22457393": {
        "ref_prefix_hint": "J", "block": "poe",
        "mpn": "LPJG0926HENL", "lcsc": "C22457393",
        "value": "LPJG0926HENL PoE+ RJ45 magjack",
        "qty_per_board": 1, "refs": ["J1"],
        "package": "Plugin", "basic": False, "stock": 3109, "price": 3.7852,
        "price_breaks": [{"qty": 1, "price": 4.4011}, {"qty": 10, "price": 3.7852},
                         {"qty": 50, "price": 3.4193}, {"qty": 100, "price": 3.0501},
                         {"qty": 500, "price": 2.8792}, {"qty": 1000, "price": 2.8019}],
        "min_qty": 1,
        "datasheet": "https://omo-oss-file110.thefastfile.com/portal-saas/new2023111719244971110/cms/file/lpjg0926henl.pdf",
        "url": "https://www.lcsc.com/product-detail/ethernet-connectors-modular-connectors-rj45-rj11_C22457393.html",
        "brand": "LINK-PP",
        "attributes": [
            {"name": "Number of Ports", "value": "1"},
            {"name": "PoE", "value": "With PoE"},
            {"name": "Connector Type", "value": "RJ45 Jack"},
            {"name": "Contact Plating", "value": "Gold 6 micro-inches min"},
            {"name": "Contact Material", "value": "Phosphor bronze"},
            {"name": "LED", "value": "With LED"},
            {"name": "Shielding", "value": "Shielded"},
            {"name": "Mounting Type", "value": "Right Angle"},
            {"name": "Operating Temperature", "value": "0C to +70C"},
            {"name": "JLCPCB Assembly Type", "value": "Wave Soldering"},
        ],
        "alternates": [],
        "role": ("THT right-angle shielded RJ45 with 1000BASE-T integrated magnetics for PoE+. "
                 "REPLACES C91754 (HY931147C). The reason for the swap is one published number: "
                 "'DC Current/Voltage Rating pse Pins: 720mA MAX @57VDC(Continuous)' (drawing "
                 "LP18022610 rev A, p1 item 7) = 1.20x the 802.3at 0.600 A DC ceiling and 1.05x "
                 "the 0.686 A peak - the only LCSC candidate that covers the peak. "
                 "NO INTERNAL BRIDGE: four raw line-side centre taps VC1..VC4 (11-14), "
                 "VC1/VC2 = Alternative A, VC3/VC4 = Alternative B, rectified by D2/D3. "
                 "Chip side 1 TD1+, 2 TD1-, 3 TD2+, 6 TD2-, 7/8 TD3+/-, 9/10 TD4+/-, with ONE "
                 "centre-tap bus on both 4 and 5. LEDs moved to 15-18 and swapped colour: "
                 "15/16 GREEN (LINK), 17/18 YELLOW (ACT), odd = anode. Shell reaches the board "
                 "only through board locks 19/20. Contains a NON-REMOVABLE internal Bob Smith "
                 "network (4x75R + 4x22nF -> 1nF/2kV to shield). Hipot 1500 Vrms, UL E484635. "
                 "Full screen: research/magjack-gigabit-screen.md; pinout: parts/C22457393.json."),
    },
    "C2892567": {
        "ref_prefix_hint": "D", "block": "poe",
        "mpn": "ABS210", "lcsc": "C2892567",
        "value": "ABS210 2A 1000V bridge rectifier",
        "qty_per_board": 2, "refs": ["D2", "D3"],
        "package": "SOP-4", "basic": False, "stock": 106023, "price": 0.0266,
        "price_breaks": [{"qty": 1, "price": 0.0266}, {"qty": 200, "price": 0.0215},
                         {"qty": 600, "price": 0.0186}, {"qty": 5000, "price": 0.0157},
                         {"qty": 10000, "price": 0.0142}, {"qty": 20000, "price": 0.0134}],
        "min_qty": 1,
        "datasheet": "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2109061630_YONGYUTAI-ABS210_C2892567.pdf",
        "url": "https://www.lcsc.com/product-detail/bridge-rectifiers_yongyutai-abs210_C2892567.html",
        "brand": "YONGYUTAI",
        "attributes": [
            {"name": "Type", "value": "Single-Phase Rectifier"},
            {"name": "Current - Rectified", "value": "2A"},
            {"name": "Voltage - DC Reverse(Vr)", "value": "1kV"},
            {"name": "Voltage - Forward(Vf@If)", "value": "1V@2A"},
            {"name": "Non-Repetitive Peak Forward Surge Current", "value": "50A"},
            {"name": "Reverse Leakage Current (Ir)", "value": "5uA@1kV"},
            {"name": "Thermal Resistance RthJA", "value": "65 C/W on 4 x (5x5mm) copper pads"},
            {"name": "Operating Junction Temperature Range", "value": "-55C to +150C"},
        ],
        "alternates": [
            {"mpn": "ABS210", "lcsc": "C123897",
             "note": "Shandong Jingdao, ABS package, 382k stock at $0.047. Same 2 A / 1000 V "
                     "ratings on the LCSC attributes but its datasheet is not fetchable "
                     "(lcsc.com 403s), so RthJA is UNVERIFIED. Use only after confirming it."},
            {"mpn": "ABS210", "lcsc": "C3014048",
             "note": "FOSAN, ABS package, 25k stock. Datasheet verified but RthJA is 75 C/W, "
                     "not 65 - Tj rises to 143 C worst case. Second choice."},
            {"mpn": "DB207S", "lcsc": "C5190147",
             "note": "Guangdong Hottech, DBS package, 2 A / 1000 V, RthJA 68 C/W. No thermal "
                     "gain over ABS210 despite a much larger land. Rejected on area."},
        ],
        "role": ("PD input bridge. TWO are fitted because the magjack has no internal "
                 "rectifier and 802.3 requires a PD to accept either Alternative and either "
                 "polarity: D2 across VC1/VC2 (Alt A), D3 across VC3/VC4 (Alt B), both onto "
                 "V48_RAW / V48_RTN. SIZED ON THERMALS, NOT CURRENT. Only one Alternative is "
                 "ever energised, so ONE package takes the whole 2 x Vf(0.6 A) x 0.6 A = "
                 "0.83-1.06 W; at the carrier's 64 C worst-case internal air (connector-icd "
                 "s7.7.3) and RthJA 65 C/W that is Tj = 118-133 C against a 150 C limit. "
                 "The MBS-package MB10S/MB6S reflex FAILS this: 90 C/W and Vf ~1.03 V at "
                 "0.6 A give Tj = 176 C, and its mean rectifying current is 0.5/0.8 A, not 1 A. "
                 "P7 MUST give each of the 8 pads its ~5x5 mm copper pour - the 65 C/W is "
                 "quoted on that condition. Datasheet: parts/C2892567.json."),
    },
    "C17431": {
        "ref_prefix_hint": "R", "block": "poe",
        "mpn": "0805W8F1212T5E", "lcsc": "C17431",
        "value": "12.1k 1% 0805",
        "qty_per_board": 2, "refs": ["R1", "R2"],
        "package": "0805", "basic": False, "stock": 29935, "price": 0.0045,
        "price_breaks": [{"qty": 1, "price": 0.0045}, {"qty": 1000, "price": 0.0036},
                         {"qty": 5000, "price": 0.0031}, {"qty": 10000, "price": 0.0029},
                         {"qty": 50000, "price": 0.0026}],
        "min_qty": 1,
        "datasheet": "https://www.lcsc.com/datasheet/lcsc_datasheet_2206010216_UNI-ROYAL-Uniroyal-Elec-0805W8F1212T5E_C17431.pdf",
        "url": "https://www.lcsc.com/product-detail/chip-resistor-surface-mount_uni-royal-uniroyal-elec-0805w8f1212t5e_C17431.html",
        "brand": "UNI-ROYAL(Uniroyal Elec)",
        "attributes": [
            {"name": "Resistance", "value": "12.1k ohm"},
            {"name": "Tolerance", "value": "+/-1%"},
            {"name": "Power(Watts)", "value": "125mW"},
            {"name": "Voltage-Supply(Max)", "value": "150V"},
            {"name": "Temperature Coefficient", "value": "+/-100ppm/C"},
            {"name": "Operating Temperature", "value": "-55C to +155C"},
        ],
        "alternates": [],
        "role": ("RDEN, split in two halves with the tap at /poe/DEN_TAP so grounding the tap "
                 "is the clean hardware PD-disable. 12.1k + 12.1k = 24.2k, DOWN from the "
                 "24.8k (2 x C30908) used with the HY931147C. The IEEE signature is an "
                 "incremental resistance measured at the PI, so it includes the input bridge; "
                 "with the bridge now a known part (2 x ABS210 junctions, ideality 2.10 from "
                 "the Fig.3 curve) the adder is +1.00k at the worst legal probe pair "
                 "(2.8/3.8 V) and +0.31k at 9/10 V. 24.8k left only 0.8% of margin under the "
                 "26.3k ceiling; 24.2k gives 24.3-25.5k across every probe pair and both "
                 "tolerance corners. Arithmetic in kicad/gen/poe.py. C30908 (12.4k) stays in "
                 "the BOM for R30 on the pwr sheet."),
    },
}

d = json.loads(io.open(PARTS, encoding="utf-8").read())
parts = d["parts"]

removed = [p for p in parts if p["lcsc"] == "C91754"]
assert len(removed) == 1, "expected exactly one C91754 line, got %d" % len(removed)
parts = [p for p in parts if p["lcsc"] != "C91754"]

have = {p["lcsc"] for p in parts}
for lcsc, rec in NEW.items():
    assert lcsc not in have, "%s already present" % lcsc

# Insert where the old magjack was: the poe block leads the file.
order = [p["lcsc"] for p in parts]
at = 0
parts[at:at] = [NEW["C22457393"], NEW["C2892567"], NEW["C17431"]]

d["parts"] = parts
io.open(PARTS, "w", encoding="utf-8", newline="\n").write(
    json.dumps(d, indent=1, ensure_ascii=True))

print(json.dumps({
    "script": "bom_magjack",
    "removed": [{"lcsc": p["lcsc"], "value": p["value"], "refs": p["refs"]}
                for p in removed],
    "added": [{"lcsc": k, "value": v["value"], "refs": v["refs"]}
              for k, v in NEW.items()],
    "lines_before": len(order) + 1,
    "lines_after": len(parts),
}, indent=1))
