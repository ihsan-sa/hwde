"""gen_hand_bom.py - hand-assembly BOM for pd-trigger, 10 boards.

Every price/stock figure below was fetched from the distributor product page
on 2026-08-15 (see the 'verified' column). MPN is the primary key: Digi-Key
part numbers are a convenience column, because DK PN typos are what broke the
two previous sheets. Digi-Key bulk-add resolves MPNs directly.
"""
import csv
import sys
from pathlib import Path

BOARDS = 10
OUT = Path(__file__).parent

# ref, qty/board, buy qty (incl. hand-assembly spares), desc, package,
# source, mpn, mfr, dist_pn, unit_price, note
ROWS = [
    # --- Digi-Key -----------------------------------------------------
    ("C1A,C1B", 2, 22, "10uF 50V X5R MLCC", "1206", "Digi-Key",
     "CGA5L3X5R1H106M160AB", "TDK", "445-12883-1-ND", 0.521,
     "50V is load-bearing (X5R loses most of its value at 20V DC bias). "
     "+/-20% tol is fine for bulk. CHEAPER than the previous sheet's "
     "C3216X5R1H106K160AB ($0.609). 7,584 in stock."),
    ("C2", 1, 15, "100nF 50V X7R MLCC", "0603", "Digi-Key",
     "CC0603KRX7R9BB104", "YAGEO", "311-1344-1-ND", 0.055,
     "3.2M in stock."),
    ("C5", 1, 15, "1uF 50V X5R MLCC", "0603", "Digi-Key",
     "UMK107BJ105KA-T", "Taiyo Yuden", "587-2400-1-ND", 0.081,
     "886k in stock. Replaces the backordered Samsung CL10A105KB8NNNC."),
    ("D1", 1, 11, "TVS 22V flat clamp, 28V clamp", "WSON-6 2x2", "Digi-Key",
     "TVS2200DRVR", "Texas Instruments", "296-52187-1-ND", 0.688,
     "Most expensive semi, but WSON-6 footprint has no cheap drop-in and the "
     "22V flat clamp is what protects the CH224K on a 20V contract. 19,573 stock."),
    ("D2", 1, 12, "Zener 6.2V 250mW", "SOT-23", "Digi-Key",
     "BZX84C6V2LT1G", "onsemi", "BZX84C6V2LT1GOSCT-ND", 0.17,
     "Priced at the qty-1 rate ($0.17) - DK's qty-10 tier is likely lower "
     "(~$0.10); the cart will show the real break. Conservative here."),
    ("D3,D6", 2, 25, "LED green clear", "0603", "Digi-Key",
     "LTST-C191KGKT", "Lite-On", "160-1446-1-ND", 0.104,
     "1.85M in stock."),
    ("D5", 1, 15, "LED red clear", "0603", "Digi-Key",
     "LTST-C191KRKT", "Lite-On", "160-1447-1-ND", 0.104,
     "1.6M in stock."),
    ("J1", 1, 11, "USB-C receptacle 2.0 16P SMD RA", "SMD", "Digi-Key",
     "USB4105-GF-A-120", "GCT", "2073-USB4105-GF-A-120CT-ND", 0.676,
     "Same MPN as the board's LCSC part - exact footprint match. 59,075 stock."),
    ("J2", 1, 11, "Terminal block 2P 5.08mm THT", "THT P=5.08", "Digi-Key",
     "OSTTC022162", "On Shore Technology", "ED2609-ND", 0.423,
     "35,472 in stock."),
    ("J3", 1, 1, "Header 1x40 breakaway 2.54mm (SNAP 2 PINS PER BOARD)",
     "THT P=2.54", "Digi-Key",
     "PREC040SAAN-RC", "Sullins", "S1012EC-40-ND", 0.49,
     "ONE 40-pin breakaway strip covers all 10 boards (20 pins needed) with "
     "20 pins spare. Buying ten 2-pin headers instead costs ~6x more. 30,307 stock."),
    ("Q1", 1, 12, "Dual NPN 45V 100mA", "SOT-363", "Digi-Key",
     "BC847BS-TP", "Micro Commercial Components", "BC847BS-TPCT-ND", 0.238,
     "Cheaper DK Marketplace listings exist (Slkormicro ~$0.14, GOODWORK "
     "~$0.02) but Marketplace ships separately - not worth it for ~$1."),
    ("R1,R8", 2, 25, "10k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-0710KL", "YAGEO", "311-10.0KHRCT-ND", 0.0188,
     "qty-25 price tier. 723k stock."),
    ("R2A,R2B", 2, 25, "510R 1% 1/4W", "1206", "Digi-Key",
     "RC1206FR-07510RL", "YAGEO", "311-510FRCT-ND", 0.036,
     "1206 held - the series pair is the LED dropper off the 20V rail "
     "(~90mW each). qty-25 tier. 62,523 stock."),
    ("R3,R4,R5", 3, 35, "100k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-07100KL", "YAGEO", "311-100KHRCT-ND", 0.0188,
     "qty-25 tier. 3.3M stock."),
    ("R6", 1, 15, "6.8k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-076K8L", "YAGEO", "311-6.80KHRCT-ND", 0.025,
     "156k stock."),
    ("R7", 1, 15, "4.7k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-074K7L", "YAGEO", "311-4.70KHRCT-ND", 0.025,
     "1.65M stock."),
    ("R9", 1, 15, "47k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-0747KL", "YAGEO", "311-47.0KHRCT-ND", 0.025,
     "1.17M stock."),
    ("R10", 1, 15, "3.3k 1% 1/4W", "1206", "Digi-Key",
     "RC1206FR-073K3L", "YAGEO", "311-3.30KFRCT-ND", 0.036,
     "qty-25 tier. 14,302 stock."),
    ("R12", 1, 15, "1.5k 1% 1/10W", "0603", "Digi-Key",
     "RC0603FR-071K5L", "YAGEO", "311-1.50KHCT-ND", 0.027,
     "DK returned 311-1.50KHCT-ND for this MPN (the previous sheet's "
     "'corrected' 311-1.50KHRCT-ND may also resolve). ORDER BY MPN. 1.17M stock."),
    ("R13", 1, 15, "4.7k 1% 1/8W", "0805", "Digi-Key",
     "RC0805FR-074K7L", "YAGEO", "311-4.70KCRCT-ND", 0.034,
     "0805 - do NOT downsize to 0603, the land pattern is 0805. 261k stock."),
    ("R14", 1, 15, "0 ohm jumper 1/10W", "0603", "Digi-Key",
     "RC0603FR-070RL", "YAGEO", "311-0.0HRCT-ND", 0.011,
     "905k stock. Cheaper than the previous sheet's Panasonic ERJ-3GEY0R00V."),
    # --- NOT available at Digi-Key or Mouser --------------------------
    ("U1", 1, 12, "USB PD sink controller", "ESSOP-10", "LCSC (or Amazon)",
     "CH224K", "WCH (Jiangsu Qin Heng)", "C970725", 0.389,
     "NOT CARRIED BY DIGI-KEY OR MOUSER - WCH has no US distribution. "
     "Alternatives are all a schematic+layout respin (STUSB4500 QFN-24, "
     "AP33772 QFN-14, HUSB238 different pinout). Amazon sells 10-packs "
     "(~$8-12) if you want to avoid an LCSC order. 12,404 LCSC stock."),
    ("F1", 1, 12, "PPTC 1.0A hold / 1.8A trip 30V", "1206", "LCSC",
     "BSMD1206-100-30V", "BHFUSE", "C5358568", 0.0988,
     "NOT AVAILABLE AT DIGI-KEY OR MOUSER AT THIS RATING. Verified: "
     "Littelfuse 1206L at 30V tops out at 0.35A hold (1206L035/30, "
     "18-1206L035/30WRCT-ND, $0.562); Bel 0ZCJ0100FF2E is 1A but only 6V. "
     "1A@30V in 1206 is not a rating Western makers offer. "
     "SUBSTITUTE OPTION: 1206L035/30 fits the footprint but derates the AUX "
     "tap to 0.35A - contradicts the 'AUX 1A MAX' silk. Your call. "
     "133,924 LCSC stock."),
    ("SW1", 1, 12, "DIP switch 3-pos SPST SMD 2.54mm", "SMD 6P L7.6 W6.0 LS9.3",
     "LCSC", "2.54-3P TPGT", "SHOU HAN", "C7421520", 0.4083,
     "Digi-Key DOES have MOQ-1 options the previous sheet missed (CTS "
     "219-3MSTR $0.706, CUI DS04-254-2-03BK-SMT $0.587) - the earlier "
     "'60-piece tube minimum' claim only applied to the non-reel variants. "
     "BUT the CTS body is 9.09mm vs this footprint's 7.6mm and the land span "
     "is unconfirmed - FIT NOT VERIFIED. LCSC part is the exact one the board "
     "was laid out for. 16,907 stock."),
]

HEADER = ["Ref(s)", "Qty per board", f"Qty for {BOARDS} boards",
          "Buy qty (incl. spares)", "Description", "Package", "Source",
          "Manufacturer PN", "Manufacturer", "Distributor PN",
          "Unit price USD", "Ext price USD", "Notes"]


def main() -> int:
    master = OUT / "BOM-hand-assembly-10x.csv"
    with master.open("w", newline="", encoding="ascii", errors="replace") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        totals = {}
        for (ref, qpb, buy, desc, pkg, src, mpn, mfr, dpn, price, note) in ROWS:
            need = qpb * BOARDS if ref != "J3" else 1
            ext = round(buy * price, 3)
            totals[src] = round(totals.get(src, 0.0) + ext, 3)
            w.writerow([ref, qpb, need, buy, desc, pkg, src, mpn, mfr, dpn,
                        f"{price:.4f}", f"{ext:.3f}", note])
        w.writerow([])
        for src, tot in sorted(totals.items()):
            w.writerow(["", "", "", "", "", "", f"SUBTOTAL {src}", "", "", "",
                        "", f"{tot:.2f}", ""])
        grand = round(sum(totals.values()), 2)
        w.writerow(["", "", "", "", "", "", "GRAND TOTAL (parts only, "
                    "no shipping/tax)", "", "", "", "", f"{grand:.2f}", ""])
        w.writerow(["", "", "", "", "", "", f"PER BOARD ({BOARDS} boards)",
                    "", "", "", "", f"{grand / BOARDS:.2f}", ""])

    # Digi-Key bulk-add: Quantity, Part Number, Customer Reference
    dk = OUT / "digikey-upload-10x.csv"
    with dk.open("w", newline="", encoding="ascii", errors="replace") as fh:
        w = csv.writer(fh)
        w.writerow(["Quantity", "Part Number", "Customer Reference"])
        for (ref, qpb, buy, desc, pkg, src, mpn, mfr, dpn, price,
             note) in ROWS:
            if src != "Digi-Key":
                continue
            w.writerow([buy, mpn, ref])

    print(f"wrote {master}")
    print(f"wrote {dk}")
    for src, tot in sorted(totals.items()):
        print(f"  {src}: ${tot:.2f}")
    print(f"  GRAND TOTAL: ${grand:.2f}  (${grand / BOARDS:.2f}/board)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
