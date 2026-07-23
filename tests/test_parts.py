"""S6 acceptance tests: parts / library / datasheet tooling.

Plan S6 accept criteria (5 test parts: MCU, buck, USB connector, crystal, 0603 R):
  - search returns in-stock LCSC hits          -> test_net_search_* (net)
  - pulled footprints load in KiCad            -> test_net_lib_pull_loads (net)
  - fp_verify flags a corrupted fp, passes good ones
                                               -> test_fp_verify_* (hermetic)
  - datasheet JSON validates                   -> test_datasheet_validate_* (hermetic)

Hermetic tests (no marker) use committed footprint fixtures + pure venv (jsonschema,
pypdf, sexpdata) and monkeypatched search results - no toolchain, no network. The
live tests carry the `net` marker and SKIP when the JLCPCB endpoint is unreachable,
so an offline run of check.cmd does not hard-fail on a third-party API.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "ai-ee" / "scripts"
FIXTURES = REPO / "tests" / "fixtures" / "parts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import datasheet_extract  # noqa: E402
import fp_verify  # noqa: E402
import fplib  # noqa: E402
import lib_pull  # noqa: E402
import partslib  # noqa: E402
import parts_search  # noqa: E402

LEGACY_FP = FIXTURES / "cap0402_legacy.kicad_mod"
MODERN_FP = FIXTURES / "cap0402_modern.kicad_mod"

# Correct land pattern for the committed 0402 cap fixtures.
CAP_DS = {
    "mpn": "CL05B104KO5NNNC", "lcsc": "C1525", "package": "0402",
    "pinout": [{"pin": "1", "name": "P1", "type": "passive"},
               {"pin": "2", "name": "P2", "type": "passive"}],
    "land_pattern": {"package": "0402", "pad_count": 2, "pitch_mm": 0.84,
                     "pad_size_mm": [0.5, 0.54], "pin1": "1"},
}


# ------------------------------------------------------------------ helpers

def run_main(mod, argv, tmp_path, capsys, name="out"):
    """Run a script's main() in-process; return (exit_code, payload_dict)."""
    out = tmp_path / f"{name}.json"
    code = mod.main([*argv, "--out", str(out)])
    cap = capsys.readouterr()
    if out.exists():
        payload = json.loads(out.read_text(encoding="utf-8"))
    else:
        payload = json.loads(cap.out) if cap.out.strip() else None
    return code, payload


def write_ds(tmp_path, data) -> Path:
    p = tmp_path / "ds.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def make_mini_pdf(path: Path, text: str) -> None:
    """A minimal one-page text PDF (no authoring lib needed; see LEARNINGS)."""
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (i, o)
    xref_at = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        pdf += b"%010d 00000 n \n" % off
    pdf += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"
            % (len(objs) + 1, xref_at))
    path.write_bytes(pdf)


# ============================================================ fplib (parsing)

def test_fplib_parses_both_formats_identically():
    leg = fplib.parse_footprint(LEGACY_FP)
    mod = fplib.parse_footprint(MODERN_FP)
    assert leg.name == mod.name == "C0402"
    for fp in (leg, mod):
        assert len(fp.copper_pads) == 2
        assert fp.has_courtyard and fp.has_layer_kind("SilkS")
        centers = sorted(round(p.center[0], 3) for p in fp.copper_pads)
        assert centers == [-0.42, 0.42]
        assert all(tuple(p.size) == (0.5, 0.54) for p in fp.copper_pads)


def test_fplib_npth_pad_not_copper(tmp_path):
    fp_text = ('(footprint "H" (layer "F.Cu")\n'
               '  (pad "" np_thru_hole circle (at 0 0) (size 2 2) (layers "*.Cu" "*.Mask"))\n'
               '  (pad "1" smd rect (at 1 0) (size 0.5 0.5) (layers "F.Cu"))\n)')
    p = tmp_path / "h.kicad_mod"
    p.write_text(fp_text, encoding="utf-8")
    fp = fplib.parse_footprint(p)
    assert len(fp.pads) == 2 and len(fp.copper_pads) == 1
    assert fp.copper_pads[0].number == "1"


def test_fplib_symbol_names(tmp_path):
    sym = ('(kicad_symbol_lib (version 20211014) (generator test)\n'
           '  (symbol "MyPart" (property "Reference" "U" (at 0 0 0))\n'
           '    (symbol "MyPart_1_1")))')
    p = tmp_path / "l.kicad_sym"
    p.write_text(sym, encoding="utf-8")
    assert fplib.symbol_names(p) == ["MyPart"]


# ============================================================ fp_verify

@pytest.mark.parametrize("fixture", [LEGACY_FP, MODERN_FP])
def test_fp_verify_passes_good(fixture, tmp_path, capsys):
    ds = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(
        fp_verify, ["--footprint", str(fixture), "--datasheet-json", str(ds),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    assert code == 0 and payload["status"] == "pass"
    assert payload["copper_pads"] == 2
    assert payload["measured_pitch_mm"] == pytest.approx(0.84, abs=1e-3)
    assert payload["violations"] == []
    assert (tmp_path / "o.svg").read_text(encoding="utf-8").startswith("<svg")


def test_fp_verify_flags_pad_count(tmp_path, capsys):
    text = LEGACY_FP.read_text(encoding="utf-8")
    corrupt = "\n".join(l for l in text.splitlines() if "(pad 2 smd" not in l)
    fp = tmp_path / "c.kicad_mod"
    fp.write_text(corrupt, encoding="utf-8")
    ds = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(
        fp_verify, ["--footprint", str(fp), "--datasheet-json", str(ds),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    assert code == 1 and payload["status"] == "violations"
    kinds = {v["kind"] for v in payload["violations"]}
    assert "pad_count" in kinds
    assert payload["copper_pads"] == 1


def test_fp_verify_flags_wrong_pitch(tmp_path, capsys):
    text = LEGACY_FP.read_text(encoding="utf-8")
    corrupt = text.replace("(at 0.42 0.00 0.00)", "(at 1.42 0.00 0.00)")
    assert corrupt != text
    fp = tmp_path / "c.kicad_mod"
    fp.write_text(corrupt, encoding="utf-8")
    ds = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(
        fp_verify, ["--footprint", str(fp), "--datasheet-json", str(ds),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    assert code == 1
    pitch = next(v for v in payload["violations"] if v["kind"] == "pad_pitch")
    assert pitch["severity"] == "error"
    assert pitch["measured_mm"] == pytest.approx(1.84, abs=1e-3)


def test_fp_verify_flags_missing_pin1(tmp_path, capsys):
    text = LEGACY_FP.read_text(encoding="utf-8")
    corrupt = text.replace("(pad 1 smd", "(pad 3 smd")
    fp = tmp_path / "c.kicad_mod"
    fp.write_text(corrupt, encoding="utf-8")
    ds = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(
        fp_verify, ["--footprint", str(fp), "--datasheet-json", str(ds),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    assert code == 1
    assert any(v["kind"] == "pin1_missing" for v in payload["violations"])


def test_fp_verify_courtyard_is_warning_not_failure(tmp_path, capsys):
    text = LEGACY_FP.read_text(encoding="utf-8")
    stripped = "\n".join(l for l in text.splitlines() if "F.CrtYd" not in l)
    fp = tmp_path / "nc.kicad_mod"
    fp.write_text(stripped, encoding="utf-8")
    ds = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(
        fp_verify, ["--footprint", str(fp), "--datasheet-json", str(ds),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    # a warning-only finding must NOT fail the gate
    assert code == 0 and payload["status"] == "pass"
    warns = [v for v in payload["violations"] if v["kind"] == "no_courtyard"]
    assert len(warns) == 1 and warns[0]["severity"] == "warning"
    assert payload["has_courtyard"] is False


def test_fp_verify_pad_size_warning(tmp_path, capsys):
    ds = dict(CAP_DS)
    ds["land_pattern"] = dict(CAP_DS["land_pattern"], pad_size_mm=[0.9, 0.9])
    dsp = write_ds(tmp_path, ds)
    code, payload = run_main(
        fp_verify, ["--footprint", str(LEGACY_FP), "--datasheet-json", str(dsp),
                    "--svg", str(tmp_path / "o.svg")], tmp_path, capsys)
    assert code == 0  # size mismatch is a warning only
    sz = [v for v in payload["violations"] if v["kind"] == "pad_size"]
    assert len(sz) == 1 and sz[0]["severity"] == "warning"


def test_fp_verify_bad_json_exit2(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    code, payload = run_main(
        fp_verify, ["--footprint", str(LEGACY_FP), "--datasheet-json", str(bad)],
        tmp_path, capsys)
    assert code == 2 and payload["status"] == "error"


# ============================================================ datasheet_extract

def test_datasheet_schema_is_valid():
    import jsonschema
    code = datasheet_extract.main(["--schema"])
    assert code == 0
    jsonschema.Draft202012Validator.check_schema(datasheet_extract.DATASHEET_SCHEMA)


def test_datasheet_validate_good(tmp_path, capsys):
    p = write_ds(tmp_path, CAP_DS)
    code, payload = run_main(datasheet_extract, ["--validate", str(p)], tmp_path, capsys)
    assert code == 0 and payload["status"] == "pass"
    assert payload["mpn"] == "CL05B104KO5NNNC" and payload["pins"] == 2


def test_datasheet_validate_bad(tmp_path, capsys):
    bad = {"lcsc": "C1", "pinout": [{"pin": "1", "type": "nonsense"}],
           "land_pattern": {"pitch_mm": -1}}
    p = write_ds(tmp_path, bad)
    code, payload = run_main(datasheet_extract, ["--validate", str(p)], tmp_path, capsys)
    assert code == 1 and payload["status"] == "invalid"
    msgs = " ".join(e["msg"] for e in payload["errors"])
    assert "mpn" in msgs and "pad_count" in msgs and "nonsense" in msgs


def test_datasheet_validate_unreadable_exit2(tmp_path, capsys):
    code, payload = run_main(
        datasheet_extract, ["--validate", str(tmp_path / "nope.json")], tmp_path, capsys)
    assert code == 2 and payload["status"] == "error"


def test_datasheet_pdf_text_extraction(tmp_path, capsys):
    pdf = tmp_path / "d.pdf"
    make_mini_pdf(pdf, "STM32F103 VDD VSS 100nF decoupling LQFP-48 0.5mm pitch")
    code, payload = run_main(
        datasheet_extract, ["--pdf", str(pdf), "--lcsc", "C8734"], tmp_path, capsys)
    assert code == 0 and payload["status"] == "extracted"
    assert payload["n_pages"] == 1 and payload["lcsc"] == "C8734"
    assert "STM32F103" in payload["text_by_page"][0]["text"]
    # the grounding payload carries the schema + a template for the agent
    assert "schema" in payload and payload["template"]["land_pattern"]["pad_count"] == 0


# ============================================================ partslib / parts_search (hermetic)

_CANNED = [
    {"lcsc": "C1", "model": "EXT", "type": "Extended", "stock": 100, "price": 0.5,
     "package": "0603", "brand": "ACME", "description": "ext part"},
    {"lcsc": "C2", "model": "BAS_LO", "type": "Basic", "stock": 50, "price": 0.2,
     "package": "0603", "brand": "ACME", "description": "basic low stock"},
    {"lcsc": "C3", "model": "BAS_HI", "type": "Basic", "stock": 9999, "price": 0.9,
     "package": "0805", "brand": "OTHER", "description": "basic high stock"},
]


def test_partslib_normalize_and_rank():
    parts = [partslib.normalize(x) for x in _CANNED]
    parts.sort(key=partslib.rank_key)
    # Basic first, then higher stock, then cheaper -> C3, C2, C1
    assert [p["lcsc"] for p in parts] == ["C3", "C2", "C1"]
    assert parts[0]["basic"] is True and parts[-1]["basic"] is False


def test_partslib_apply_filters():
    parts = [partslib.normalize(x) for x in _CANNED]
    assert {p["lcsc"] for p in partslib.apply_filters(parts, basic_only=True)} == {"C2", "C3"}
    assert {p["lcsc"] for p in partslib.apply_filters(parts, package="0603")} == {"C1", "C2"}
    assert {p["lcsc"] for p in partslib.apply_filters(parts, min_stock=1000)} == {"C3"}
    assert {p["lcsc"] for p in partslib.apply_filters(parts, max_price=0.3)} == {"C2"}
    assert {p["lcsc"] for p in partslib.apply_filters(parts, brand="acme")} == {"C1", "C2"}


def test_parts_search_ranks_and_filters(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: (list(_CANNED), 3))
    code, payload = run_main(
        parts_search, ["--query", "x", "--limit", "5"], tmp_path, capsys)
    assert code == 0 and payload["status"] == "pass"
    assert payload["source"] == "live"
    assert [r["lcsc"] for r in payload["results"]] == ["C3", "C2", "C1"]
    assert payload["results"][0]["rank"] == 0


def test_parts_search_basic_only_filter(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: (list(_CANNED), 3))
    code, payload = run_main(
        parts_search, ["--query", "x", "--basic-only", "--min-stock", "1000"],
        tmp_path, capsys)
    assert code == 0
    assert [r["lcsc"] for r in payload["results"]] == ["C3"]


def test_parts_search_bad_filter_key_exit2(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: (list(_CANNED), 3))
    code, payload = run_main(
        parts_search, ["--query", "x", "--filters", "bogus=1"], tmp_path, capsys)
    assert code == 2 and payload["status"] == "error"


def test_parts_search_offline_no_db_exit2(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: ([], 0))
    monkeypatch.setattr(partslib, "endpoint_reachable", lambda *a, **k: False)
    code, payload = run_main(parts_search, ["--query", "x"], tmp_path, capsys)
    assert code == 2 and payload["status"] == "error"
    assert "unreachable" in payload["error"]


def test_parts_search_empty_but_reachable_exit0(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: ([], 0))
    monkeypatch.setattr(partslib, "endpoint_reachable", lambda *a, **k: True)
    code, payload = run_main(parts_search, ["--query", "zzz"], tmp_path, capsys)
    assert code == 0 and payload["status"] == "empty" and payload["count"] == 0


# ------------------------------------------------ jlcparts SQLite fallback

def _make_jlcparts_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE components (lcsc INTEGER PRIMARY KEY, mfr TEXT, "
                "package TEXT, basic INTEGER, description TEXT, datasheet TEXT, "
                "stock INTEGER, price TEXT)")
    con.executemany(
        "INSERT INTO components VALUES (?,?,?,?,?,?,?,?)",
        [(25804, "RC0603FR-0710KL", "0603", 1, "10kOhm 0603 1% resistor",
          "http://d/r.pdf", 1_000_000, '[{"qFrom":1,"price":0.001}]'),
         (100, "CAPX", "0402", 0, "100nF 0402 X7R cap", "http://d/c.pdf",
          5000, '[{"qFrom":1,"price":0.01}]')])
    con.commit()
    con.close()


def test_db_search_reads_jlcparts_schema(tmp_path):
    db = tmp_path / "cache.sqlite3"
    _make_jlcparts_db(db)
    res = partslib.db_search(db, "10k")
    assert len(res) == 1
    r = res[0]
    assert r["lcsc"] == "C25804" and r["basic"] is True
    assert r["stock"] == 1_000_000 and r["price"] == pytest.approx(0.001)


def test_db_search_missing_file_raises():
    with pytest.raises(partslib.PartsError):
        partslib.db_search("no/such.sqlite3", "x")


def test_parts_search_db_fallback(tmp_path, capsys, monkeypatch):
    db = tmp_path / "cache.sqlite3"
    _make_jlcparts_db(db)
    monkeypatch.setattr(partslib, "live_search", lambda *a, **k: ([], 0))
    code, payload = run_main(
        parts_search, ["--query", "10k", "--db", str(db)], tmp_path, capsys)
    assert code == 0 and payload["source"] == "db"
    assert payload["results"][0]["lcsc"] == "C25804"


def test_lib_pull_registration_idempotent(tmp_path):
    """Lib-table registration writes portable URIs and is idempotent (no live pull)."""
    project = tmp_path / "kicad"
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "aiee.kicad_sym").write_text("(kicad_symbol_lib)", encoding="utf-8")
    pretty = lib_dir / "aiee.pretty"
    pretty.mkdir()
    r1 = lib_pull._register_project(project, "aiee",
                                    lib_dir / "aiee.kicad_sym", pretty)
    assert r1 == {"fp": "created", "sym": "created"}
    r2 = lib_pull._register_project(project, "aiee",
                                    lib_dir / "aiee.kicad_sym", pretty)
    assert r2 == {"fp": "present", "sym": "present"}
    fp_table = (project / "fp-lib-table").read_text(encoding="utf-8")
    assert fp_table.count('(name "aiee")') == 1
    assert "${KIPRJMOD}/../lib/aiee.pretty" in fp_table


# ============================================================ live (net) tests

def _skip_if_offline():
    if not partslib.endpoint_reachable(timeout=8.0):
        pytest.skip("JLCPCB endpoint unreachable (offline)")


@pytest.mark.net
@pytest.mark.parametrize("query", [
    "STM32F103C8T6",      # MCU
    "AP63203",            # buck regulator
    "USB Micro B connector",  # USB connector
    "8MHz crystal SMD",   # crystal
    "10k 0603 1%",        # 0603 resistor
])
def test_net_search_returns_in_stock_hits(query, tmp_path):
    _skip_if_offline()
    out = tmp_path / "pn.json"
    code = parts_search.main(["--query", query, "--min-stock", "1", "--limit", "5",
                              "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0, data
    assert data["count"] >= 1, f"no hits for {query!r}"
    assert all(r["stock"] >= 1 for r in data["results"])
    assert all(r["lcsc"].startswith("C") for r in data["results"])


@pytest.mark.net
def test_net_lib_pull_loads_in_kicad(tmp_path):
    _skip_if_offline()
    out = tmp_path / "r.json"
    code = lib_pull.main(["--lcsc", "C1525", "--out-dir", str(tmp_path / "lib"),
                          "--verify-load", "--out", str(out)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0, data
    assert data["results"][0]["status"] in ("pulled", "exists")
    assert data["load_check"]["ok"] is True, data["load_check"]
    # the pulled footprint is parseable and has copper pads
    fp_file = data["results"][0]["footprints"][0]["file"]
    assert len(fplib.parse_footprint(fp_file).copper_pads) >= 2
