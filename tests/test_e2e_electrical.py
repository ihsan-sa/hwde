"""evals/e2e_electrical.py: the e2e eval's electrical scorer.

Each case builds its own small board (a netlist dict and, where a distance
or a via count matters, a PCB dict), so nothing here needs kicad-cli except
the one real-board case at the end, which skips without it.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "evals"))
import e2e_electrical as E  # noqa: E402

from _boards import real_board  # noqa: E402

GND = "GND"


def board(parts: dict, pos: dict | None = None, vias=(), extra_pads=None):
    """parts {ref: (value, footprint, {pin: (function, net)})} -> Board.
    pos {ref: (x, y)} puts every pad of that part at (x, y) on a PCB."""
    comps, nets, pin_net = {}, {}, {}
    for ref, (value, fp, pins) in parts.items():
        comps[ref] = {"value": value, "footprint": fp, "fields": {}, "lib": value}
        for pin, (func, net) in pins.items():
            nets.setdefault(net, []).append((ref, pin, func, ""))
            pin_net[(ref, pin)] = net
    pcb = None
    if pos is not None:
        fps = {}
        for ref, (x, y) in pos.items():
            pads = {pin: [{"x": x, "y": y, "net": net, "w": 1, "h": 1,
                           "type": "smd"}]
                    for pin, (_, net) in parts[ref][2].items()}
            for pin, pad in (extra_pads or {}).get(ref, []):
                pads.setdefault(pin, []).append(pad)
            fps[ref] = {"x": x, "y": y, "layer": "F.Cu", "value": "",
                        "pads": pads}
        pcb = {"fps": fps, "tracks": [], "vias": list(vias), "zones": []}
    return E.Board({"comps": comps, "nets": nets, "pin_net": pin_net}, pcb)


def r(value, a, b):
    return (value, "R_0402", {"1": ("~", a), "2": ("~", b)})


def c(value, a, b):
    return (value, "C_0402", {"1": ("~", a), "2": ("~", b)})


def ids(checks, cid):
    return [x for x in checks if x["id"] == cid]


# ------------------------------------------------------------- primitives

def test_parse_value_reads_the_ways_values_are_written():
    assert E.parse_value("5.1k") == pytest.approx(5100)
    assert E.parse_value("5k1") == pytest.approx(5100)
    assert E.parse_value("2u2") == pytest.approx(2.2e-6)
    assert E.parse_value("100nF 50V X7R") == pytest.approx(1e-7)
    assert E.parse_value("10uH 4.4A") == pytest.approx(1e-5)
    assert E.parse_value("0R") == 0
    assert E.parse_value("red") is None


def test_sexpr_keeps_quoted_strings_whole():
    tree = E.sexpr('(a (b "x y") (c 1 2))')
    assert E.atom(tree, "b") == "x y"
    assert E.kid(tree, "c") == ["c", "1", "2"]


def test_ipc_width_matches_the_external_layer_chart():
    # 1 oz, 10 C rise: about 0.78 mm at 2 A, about 0.3 mm at 0.75 A
    assert E.ipc_width_mm(2.0) == pytest.approx(0.78, abs=0.03)
    assert E.ipc_width_mm(0.75) < 0.3 < E.ipc_width_mm(1.0)


def test_aggregate_caps_a_board_with_a_fatal_fault():
    fine = [E.chk("ldo_cin", "values", 1.0, ""),
            E.chk("ldo_gnd", "connectivity", 1.0, "")]
    assert E.aggregate(fine, 1.0)[0] == 1.0
    broken = fine + [E.chk("cc1_rd", "connectivity", 0.0, "")]
    e, _, _, fatal = E.aggregate(broken, 1.0)
    assert fatal == ["cc1_rd"] and e == E.CRITICAL_CAP
    # a zero on a non-critical check lowers E but does not cap it
    soft = fine + [E.chk("ldo_cout_dist", "placement", 0.0, "")]
    e, _, _, fatal = E.aggregate(soft, 1.0)
    assert fatal == [] and E.CRITICAL_CAP < e < 1.0
    # the gate multiplies
    assert E.aggregate(fine, 0.7)[0] == pytest.approx(0.7)


def test_old_categories_from_a_record_or_a_score_json():
    assert E.old_categories({"categories": {"layout": 0.5, "cost": 1}}) == \
        {"layout": 0.5, "cost": 1}
    sc = {"penalties": {"layout_shortfall": 0.25, "cost_shortfall": 0.0}}
    assert E.old_categories(sc) == {"layout": 0.75, "cost": 1.0}


# --------------------------------------------------------------- usbc_ldo

def usbc(ldo="AMS1117-3.3", ldo_fp="SOT-223-3", cin="10uF", cout="22uF",
         cc2_net="/CC2", rd2="5.1k"):
    parts = {
        "J1": ("USB_C", "USB_C_Receptacle", {
            "A4": ("VBUS", "+5V"), "B4": ("VBUS", "+5V"),
            "A5": ("CC1", "/CC1"), "B5": ("CC2", cc2_net),
            "A1": ("GND", GND), "B1": ("GND", GND)}),
        "U1": (ldo, ldo_fp, {"1": ("GND", GND), "2": ("VO", "+3V3"),
                             "3": ("VI", "+5V")}),
        "J2": ("HDR", "PinHeader_1x03", {"1": ("Pin_1", "+5V"),
                                         "2": ("Pin_2", "+3V3"),
                                         "3": ("Pin_3", GND)}),
        "R1": r("5.1k", "/CC1", GND), "R2": r(rd2, cc2_net, GND),
        "C1": c(cin, "+5V", GND), "C2": c(cout, "+3V3", GND),
    }
    pos = {"U1": (0, 0), "C1": (2, 0), "C2": (14, 0), "J1": (20, 0),
           "J2": (30, 0), "R1": (20, 5), "R2": (20, 6)}
    return board(parts, pos)


def test_usbc_ldo_good_board_passes_the_datasheet_checks():
    ka = E.load_answer("usbc_ldo")
    checks = E.score_usbc_ldo(usbc(), ka)
    bad = [x for x in checks if x["score"] is not None and x["score"] < 1]
    # only the output cap 14 mm away is off
    assert [x["id"] for x in bad] == ["ldo_cout_dist"]
    assert ids(checks, "ldo_tj")[0]["score"] == 1.0


def test_usbc_ldo_one_shared_rd_on_both_cc_pins_is_fatal():
    ka = E.load_answer("usbc_ldo")
    checks = E.score_usbc_ldo(usbc(cc2_net="/CC1", rd2="5.1k"), ka)
    assert ids(checks, "cc_separate")[0]["score"] == 0
    assert "cc_separate" in E.aggregate(checks, 1.0)[3]


def test_usbc_ldo_wrong_rd_value_fails_that_pin_only():
    ka = E.load_answer("usbc_ldo")
    checks = E.score_usbc_ldo(usbc(rd2="10k"), ka)
    assert ids(checks, "cc2_rd")[0]["score"] == 0
    assert ids(checks, "cc1_rd")[0]["score"] == 1


def test_usbc_ldo_sot23_regulator_overheats_at_300ma():
    ka = E.load_answer("usbc_ldo")
    checks = E.score_usbc_ldo(usbc(ldo="AP2112K-3.3", ldo_fp="SOT-23-5",
                                   cin="1uF", cout="1uF"), ka)
    tj = ids(checks, "ldo_tj")[0]
    assert tj["score"] == 0 and "Tj 171" in tj["detail"]
    # its 1 uF caps are what its datasheet asks, so values still pass
    assert ids(checks, "ldo_cout")[0]["score"] == 1


def test_usbc_ldo_ams1117_with_a_small_output_cap_loses_values():
    ka = E.load_answer("usbc_ldo")
    checks = E.score_usbc_ldo(usbc(cout="4.7uF"), ka)
    assert ids(checks, "ldo_cout")[0]["score"] == pytest.approx(4.7 / 22, abs=1e-3)


# ------------------------------------------------------------ stereo_amp

def amp(bs_other="/OUTPL", sdz_to="/GVDD", gain_r="5.6k", ep=True, vias=8,
        fp="HTSSOP-32_EP"):
    u = {"1": ("MODSEL", GND), "2": ("SDZ", "/SDZ"), "3": ("FAULTZ", "/SDZ"),
         "4": ("RINP", "/RINP"), "5": ("RINN", "/RINN"),
         "6": ("PLIMIT", "/GVDD"), "7": ("GVDD", "/GVDD"),
         "8": ("GAIN", "/GAIN"), "9": ("GND", GND), "10": ("LINP", "/LINP"),
         "11": ("LINN", "/LINN"), "12": ("MUTE", GND), "13": ("AM2", GND),
         "14": ("AM1", GND), "15": ("AM0", GND), "17": ("AVCC", "+12V"),
         "18": ("PVCC", "+12V"), "19": ("PVCC", "+12V"),
         "31": ("PVCC", "+12V"), "32": ("PVCC", "+12V"),
         "22": ("GND", GND), "25": ("GND", GND), "28": ("GND", GND)}
    parts = {"J1": ("PWR", "WirePad", {"1": ("1", "+12V"), "2": ("2", GND)}),
             "C1": c("100uF", "+12V", GND), "C2": c("100nF", "+12V", GND),
             "C3": c("1uF", "/GVDD", GND),
             "R1": r(gain_r, "/GAIN", GND), "R2": r("100k", "/SDZ", sdz_to)}
    n = 4
    for side, (bsp, op, bsn, on) in {"L": ("24", "23", "20", "21"),
                                     "R": ("30", "29", "26", "27")}.items():
        for bs, o, pol in ((bsp, op, "P"), (bsn, on, "N")):
            out_net = f"/OUT{pol}{side}"
            u[bs] = (f"BS{pol}{side}", f"/BS{pol}{side}")
            u[o] = (f"OUT{pol}{side}", out_net)
            other = bs_other if (side, pol) == ("L", "P") else out_net
            parts[f"C{n}"] = c("220nF", f"/BS{pol}{side}", other)
            parts[f"L{n}"] = ("10uH", "L_1210", {"1": ("~", out_net),
                                                 "2": ("~", f"/SPK{pol}{side}")})
            parts[f"C{n + 1}"] = c("680nF", f"/SPK{pol}{side}", GND)
            n += 2
    for name in ("LINP", "LINN", "RINP", "RINN"):
        parts[f"C{n}"] = c("1uF", f"/IN_{name}", f"/{name}")
        n += 1
    parts["U1"] = ("TPA3116D2", fp, u)
    extra = {"U1": [("33", {"x": 0, "y": 0, "w": 3.7, "h": 3.8, "net": GND,
                            "type": "smd"})]} if ep else None
    pos = {ref: (0, 0) if ref == "U1" else (2, 0) for ref in parts}
    holes = [{"x": 0.5 * i - 1, "y": 0, "net": GND} for i in range(vias)]
    return board(parts, pos, holes, extra)


def test_stereo_amp_good_board_passes_connectivity_and_values():
    ka = E.load_answer("stereo_amp")
    checks = E.score_stereo_amp(amp(), ka)
    conn = [x for x in checks if x["group"] in ("connectivity", "values")
            and x["id"] not in ("lc_left", "lc_right")]
    assert all(x["score"] == 1 for x in conn), [x for x in conn if x["score"] != 1]
    assert "20 dB master" in ids(checks, "gain_strap")[0]["detail"]
    assert ids(checks, "thermal_vias")[0]["score"] == 1


def test_stereo_amp_bootstrap_cap_to_the_wrong_pin_is_fatal():
    ka = E.load_answer("stereo_amp")
    checks = E.score_stereo_amp(amp(bs_other=GND), ka)
    assert ids(checks, "bootstrap_24")[0]["score"] == 0
    assert ids(checks, "bootstrap_20")[0]["score"] == 1
    assert "bootstrap_24" in E.aggregate(checks, 1.0)[3]


def test_stereo_amp_sdz_pulled_to_ground_holds_it_in_shutdown():
    ka = E.load_answer("stereo_amp")
    assert ids(E.score_stereo_amp(amp(sdz_to=GND), ka), "sdz")[0]["score"] == 0
    assert ids(E.score_stereo_amp(amp(), ka), "sdz")[0]["score"] == 1


def test_stereo_amp_gain_resistor_off_the_table_fails():
    ka = E.load_answer("stereo_amp")
    assert ids(E.score_stereo_amp(amp(gain_r="10k"), ka),
               "gain_strap")[0]["score"] == 0


def test_stereo_amp_thermal_pad_needs_vias_or_a_heatsink():
    ka = E.load_answer("stereo_amp")
    few = ids(E.score_stereo_amp(amp(vias=3), ka), "thermal_vias")[0]
    assert few["score"] == pytest.approx(0.5)
    top = ids(E.score_stereo_amp(amp(ep=False, fp="HTSSOP-32_TopEP"), ka),
              "thermal_vias")[0]
    assert top["score"] == 0 and "heatsink" in top["detail"]


def test_stereo_amp_output_filter_cutoff_by_ngspice():
    ka = E.load_answer("stereo_amp")
    b = amp()
    built = E.lc_deck(b, "/OUTPL", "/OUTNL", 8)
    assert built and "LL" in built[0]
    meas = E.ngspice(built[0])
    if meas is None:
        pytest.skip("no ngspice shared library on this host")
    # 10 uH with 680 nF per side: about 61 kHz, inside 20-100 kHz
    assert 40e3 < meas["f3db"] < 100e3
    lc = ids(E.score_stereo_amp(b, ka), "lc_left")[0]
    assert lc["score"] == 1


# ------------------------------------------------------------ real board

def test_real_amp_board_scores_without_fatal_faults():
    ws = real_board("PCB-0017-A")
    if not shutil.which(E.kicad_cli()):
        pytest.skip("no kicad-cli on this host")
    sc = E.score_workspace("stereo_amp", ws)
    assert sc["fatal"] == [] and sc["gate"] == 1.0
    assert sc["electrical"] > 0.85


# ------------------------------------------------------- the run driver

def test_run_driver_puts_the_electrical_composite_in_the_record(monkeypatch, tmp_path):
    import e2e_run
    bench = {"composite": 90.0, "penalties": {"layout_shortfall": 0.2},
             "metrics_live": {"checks": [{"id": "erc", "score": 1}]}}
    # a brief with no known-answer keeps the bench's score untouched
    assert e2e_run.with_electrical("e2e_buck_5v", tmp_path, bench,
                                   tmp_path / "el.json") is bench
    res = {"composite": 40.0, "electrical": 0.3,
           "checks": [E.chk("cc1_rd", "connectivity", 0.0, "no Rd")]}
    monkeypatch.setattr(E, "score_workspace", lambda f, ws, sc: res)
    sc = e2e_run.with_electrical("e2e_usbc_ldo", tmp_path, bench,
                                 tmp_path / "el.json")
    assert (sc["composite"], sc["composite_bench"]) == (40.0, 90.0)
    assert [f["check"] for f in e2e_run.findings(sc)] == ["cc1_rd"]
    assert (tmp_path / "el.json").is_file()

    def unreadable(*a):
        raise E.BoardError("no schematic")
    monkeypatch.setattr(E, "score_workspace", unreadable)
    sc = e2e_run.with_electrical("e2e_usbc_ldo", tmp_path, bench,
                                 tmp_path / "el.json")
    assert sc["composite"] is None and "no schematic" in sc["error"]
