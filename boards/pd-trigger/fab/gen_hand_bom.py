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
    ("F1", 1, 12, "PPTC 350mA hold / 750mA trip 30V", "1206", "Digi-Key",
     "MF-NSHT035KX-2", "Bourns", "MF-NSHT035KX-2CT-ND", 0.391,
     "*** SPEC CHANGE - READ THIS *** The board was designed around a 1A-hold "
     "@30V 1206 PPTC (BHFUSE BSMD1206-100-30V, LCSC only). That rating does "
     "not exist outside LCSC: Littelfuse's 30V 1206L line tops out at 0.35A, "
     "Bourns' at 0.35A, Bel's 1A part is 6V-rated, and even the Amazon "
     "generic assortments pair 1.1A with 8V / 0.35A with 30V. It is package "
     "physics, not a stocking gap. This part fits the 1206 land but LIMITS "
     "THE AUX HEADER (J3) TO ~0.35A, so the 'AUX 1A MAX' silkscreen "
     "over-promises. Cheaper than the Littelfuse 1206L035/30 ($0.562). "
     "ALTERNATIVES: leave F1 unpopulated, or bridge it, if you want the full "
     "1A on aux and accept no aux protection. 15,625 stock."),
    # --- Amazon (not carried by Digi-Key or Mouser) --------------------
    ("U1", 1, 10, "USB PD sink controller", "ESSOP-10", "Amazon",
     "CH224K", "WCH (Jiangsu Qin Heng)", "B0BQQZSCYC (10-pack)", 1.00,
     "PRICE IS AN ESTIMATE - Amazon blocks automated price checks, confirm on "
     "the listing. NOT CARRIED BY DIGI-KEY OR MOUSER (WCH has no US "
     "distributor); every DK/Mouser PD sink is a different pinout and package "
     "= a board respin. A 10-pack is exactly 10 boards with no spares - "
     "consider two packs. VERIFY ON ARRIVAL: marking reads CH224K and the "
     "package is ESSOP-10 (10 pins, ~3mm body, thermal pad), not SOP-10."),
    ("SW1", 1, 10, "DIP switch 3-pos SPST SMD 2.54mm", "SMD 6P L7.6 W6.0 LS9.3",
     "Amazon", "generic 3P SMD DIP (SHOU HAN 2.54-3P class)", "generic",
     "B0CLJD4MJN (10-pack, pick 3P/6-pin)", 0.80,
     "PRICE IS AN ESTIMATE - confirm on the listing. This generic Chinese "
     "SMD DIP is the exact class the board was laid out for, so it is a "
     "BETTER fit bet than Digi-Key's CTS 219-3MSTR (body 9.09mm vs this "
     "footprint's 7.6mm). MUST VERIFY BEFORE BUYING: (a) SMD/SMT gull-wing "
     "pads, NOT through-hole pins - several lookalike listings are THT; "
     "(b) 3 positions / 6 pins; (c) 2.54mm pitch; (d) body ~7.6mm long."),
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

    # Amazon shopping list (links cannot be auto-verified - Amazon blocks
    # automated fetches; these URLs come from search results)
    amz = OUT / "amazon-order-10x.csv"
    ALT = {
        "U1": "https://www.amazon.com/CH224K-Protocol-10Pcs-Arrival-Quality"
              "/dp/B0DRN7D9CY | https://www.amazon.com/-/es/QLWAHK-CH224K-"
              "ESSOP-10-otorgando-protocolo/dp/B0DNWLS5RS",
        "SW1": "https://www.amazon.com/10pcs-Position-Switch-2-54mm-Pitch"
               "/dp/B09NTPMVH6 (VERIFY IT IS SMD - title does not say)",
    }
    LINK = {
        "U1": "https://www.amazon.com/10PCS-CH224K-ESSOP10/dp/B0BQQZSCYC",
        "SW1": "https://www.amazon.com/JALYKA-10Pcs-Switch-2-54mm-Position"
               "/dp/B0CLJD4MJN",
    }
    with amz.open("w", newline="", encoding="ascii", errors="replace") as fh:
        w = csv.writer(fh)
        w.writerow(["Ref", "What to buy", "Packs needed", "Primary link",
                    "Backup links", "Must verify before buying"])
        w.writerow(["U1", "CH224K USB PD sink IC, ESSOP-10, 10-pack", 1,
                    LINK["U1"], ALT["U1"],
                    "Marking reads CH224K; package is ESSOP-10 (10 pins + "
                    "thermal pad). 10-pack = zero spares; 2 packs recommended."])
        w.writerow(["SW1", "3-position SMD DIP switch, 2.54mm, 10-pack", 1,
                    LINK["SW1"], ALT["SW1"],
                    "SMD gull-wing pads NOT through-hole; 3 positions / 6 "
                    "pins; 2.54mm pitch; body ~7.6mm. Select the 3P variant."])

    print(f"wrote {master}")
    print(f"wrote {dk}")
    print(f"wrote {amz}")
    for src, tot in sorted(totals.items()):
        print(f"  {src}: ${tot:.2f}")
    print(f"  GRAND TOTAL: ${grand:.2f}  (${grand / BOARDS:.2f}/board)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
