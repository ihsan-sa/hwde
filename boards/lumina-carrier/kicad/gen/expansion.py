"""LUM-CAR-A `expansion` sheet - J3 expansion POWER + J4 expansion SIGNAL.

The SOURCE of this sheet is this file; `kicad/expansion.kicad_sch` is BUILD
OUTPUT. Standalone rebuild (writes the sheet only, no .kicad_pro - the root
generator owns the project file):

    .venv/Scripts/python boards/lumina-carrier/kicad/gen/lib_pin_types.py
    .venv/Scripts/python boards/lumina-carrier/kicad/gen/expansion.py

ORDER MATTERS: `lib_pin_types.py` first. A saved .kicad_sch EMBEDS its lib
symbols, so a sheet built before the retype keeps the junk pin types even
after the library is fixed - it must be regenerated. As built here the
untouched library costs this sheet 31 `pin_to_pin` warnings ("Unspecified
and Unspecified are connected") and 9 false `pin_not_driven` errors;
retyping every pin of J3/J4/R13x/D4x to `passive` takes all 40 to zero
(measured this session on a retyped copy of the built sheet).

The root generator imports `build()` and stitches this sheet with
`schlib.Project.add_sheet(expansion.build(), at=..., size=..., nets=HIER_NETS)`.
`HIER_NETS` below is the exact, ordered sheet-pin list the root must pass.

ICD-01 IS THE AUTHORITY FOR J3 AND J4
-------------------------------------
`architecture/connector-icd.md` rev A2 s3.1 / s3.2 is frozen at H1 and two
other board runs (LUM-STR-A strobe, LUM-PAR-A RGBW par) are designing against
it. The two pin maps below are transcribed from it verbatim and must not be
"improved" here: a change is a blocking issue against LUM-CAR-A, a new ICD
revision and a re-baseline of every daughter.

  J3 POWER, DS1021-2x7SF11-B (C7430403), 14 pos - ICD s3.1
      1 +48V_SW   2 GND        3 +48V_SW   4 GND
      5 +48V_SW   6 GND        7 GND       8 GND      <- col 4 = GND guard
      9 +12V     10 GND       11 +12V     12 +3V3
     13 GND      14 +3V3
     3x +48V_SW, 2x +12V, 2x +3V3, 7x GND. The 7 GND pins are CAR-REQ-13
     (GND is the binding rail at 5.5 A worst case, not 48 V); the brief's
     ">= 4 GND" is BELOW requirement and is not what is built.

  J4 SIGNAL, DS1021-2x12SF11-B (C7430408), 24 pos - ICD s3.2
      1 PWM0      2 PWM1       3 GND       4 GND
      5 PWM2      6 PWM3       7 PWM4      8 PWM5
      9 GND      10 GND       11 PWM6     12 PWM7
     13 GND      14 DSPI_SCK  15 DSPI_MOSI 16 DSPI_MISO
     17 DSPI_CSn 18 I2C_SCL   19 I2C_SDA  20 ADC0
     21 ADC1     22 ID_ADC    23 ENABLE   24 FAULT
     The interleaved GND pins (3/4, 9/10, 13) are deliberate return paths
     adjacent to the PWM edges - they are not filler and must stay.
     No 48 V exists anywhere on this connector.

REFDES COMES FROM parts/parts.json, NEVER FROM THE SYMBOL
---------------------------------------------------------
Both connector symbols and the ESD clamp carry a DEFAULT Reference of "U"
in lib/aiee.kicad_sym (verified by reading the library):
    DS1021-2X7SF11-B   -> "U"  ... instantiated here as J3
    DS1021-2X12SF11-B  -> "U"  ... instantiated here as J4
    PESD3V3L1BA        -> "U"  ... instantiated here as D40/D41/D42
A wrong refdes propagates into the BOM and the CPL that two daughter runs
cross-reference, and `constraints.json.placement.edges` keys on J3/J4/H5.

SUPPORT CIRCUITRY - ICD s3.3
----------------------------
R130/R131  4.7 k I2C pull-ups to +3V3. CARRIER SIDE. Daughters must not fit
           their own (ICD s3.3), so these are the only pull-ups on the bus.
R132       10 k pull-up on /FAULT. FAULT is open drain from the daughter and
           wire-OR'd with the carrier eFuse's own FLT output on the `pwr`
           sheet, so exactly one pull-up exists board-wide and it is here.
R134       10 k ID-divider TOP leg to +3V3. The daughter fits the BOTTOM leg
           to GND (ICD s3.3). It sits on the CONNECTOR side of R135 on
           purpose: behind the 1 k series resistor the divider ratio would
           be 10 % wrong.
R135-R137  1 k series protection on ID_ADC / ADC0 / ADC1.
D40-D42    PESD3V3L1BA 3.3 V clamps, DOWNSTREAM of R135-R137 (parts.json
           role text). These three lines go off-board to an unknown daughter
           and a mis-seated daughter can bridge a neighbouring pin onto
           them; series R + clamp is the CAR-REQ-14 survivability measure,
           not just ESD hygiene.
H5         5th M3 mounting hole, CAR-REQ-15 board-to-board support between
           J3 and J4 so board flex is not carried by the connector pins.
           Mechanical only - no pins, no net.

PESD3V3L1BA ORIENTATION IS A NON-QUESTION
-----------------------------------------
The sourced part is UMW/Youtai, not Nexperia. Its datasheet states
"Bidirectional configurations", labels the SOD-323 only "Pin1 / Pin2" with
no anode/cathode, publishes no V_F, and the package carries no polarity
band. The symbol's generic "1"/"2" pin names are therefore correct and
EITHER orientation is valid. (Genuine Nexperia PESD3V3L1BA *is*
unidirectional - a future second-source to real Nexperia stock would make
orientation matter. Flagged to the orchestrator.)

NET NAMING (architecture/sheets.md s1)
--------------------------------------
* GND / +3V3 / +12V / +48V_SW are POWER SYMBOLS -> global, BARE names, no
  sheet pin. `+48V_SW` has no stock symbol: `power:+48V` is placed and its
  VALUE field is set to "+48V_SW". Verified on this host against
  kicad-cli 10.0.3 that a power symbol's net name comes from its Value
  field, not from its library pin name (netlist showed `+48V_SW`).
  A local label alone would give `/expansion/+48V_SW` and
  `netlist_audit --constraints` would raise missing_net at ERROR.
* No PWR_FLAGs here. All six live on `poe` / `pwr`, which own the sources.
* The 19 nets in HIER_NETS cross the root and become `/NAME`.
* Three nets are sheet-internal and become `/expansion/<NAME>`:
      ADC0_CONN, ADC1_CONN, ID_ADC_CONN
  These are the CONNECTOR-side nodes, upstream of the 1 k series
  resistors. The root-crossed `/ADC0` `/ADC1` `/ID_ADC` are the MCU-side
  nodes (clamped by D40-D42) that merge with the `mcu` sheet's GPIO nets -
  a series resistor necessarily splits the signal into two nets and the
  root-crossed half has to be the one the MCU shares. Not listed in
  sheets.md s1.3 (which has no expansion-sheet internal nets); no
  constraint references them.

NOT ON THIS SHEET
-----------------
* No ID EEPROM. The orchestrator ruled at P3 that it lives on the DAUGHTER,
  riding the shared I2C bus - which is exactly why ID is one pin and not
  two (ICD s2). parts.json carries U40 (M24C02, C83836) + C120 for it with
  its own role text flagging the conflict; both are deliberately dropped.
* No +48V_SW bleed. R70 lives on the `pwr` sheet.

SAFETY
------
J3 carries 48 V raw (57 V worst case) adjacent to logic. Board-wide HV
clearance is 0.635 mm (raised from 0.60 mm at P3 to honour TI's TPS2378
layout guidance); both connector footprints use a 1.70 mm annulus on a
2.54 mm pitch = 0.840 mm pad-to-pad = 1.32x. Nothing to do in the
schematic - but NO part is placed between a 48 V pin and a logic pin.

HIER-PIN SHAPES: THE ROOT SIDE IS THE ONE THAT LANDS
----------------------------------------------------
`HIER_NETS` carries a real electrical shape per net, and
`Project.add_sheet` writes those onto the ROOT's sheet pins (verified:
`add_sheet_pin` passes pin_type through). The CHILD's hierarchical labels
come out `input` regardless of what is asked for -
`Schematic.add_hierarchical_label` accepts a `shape` argument and then
drops it: it calls `self._hierarchical_labels.add(text, position,
rotation, size)` with no shape, and `_sync_hierarchical_labels_to_data`
emits no shape key at all (kicad-sch-api 0.5.6). There is no API path to
it; only a post-save text patch could fix it.
This is NOT a defect to work around here. The S7 reference design already
has it (`tests/s7_regen/hierdemo`: root sheet pin `CTL` is `passive`, the
child's label is `input`) and that root's ERC is 0/0 on kicad-cli 10.0.3 -
measured this session. KiCad does not check sheet-pin/label shape parity.

ROTATION IS DELIBERATELY UNUSED
-------------------------------
Every component here is at rotation 0. schlib's `stub_dir` and
kicad-sch-api disagree on the sign of a 90 deg symbol rotation: for a
rotated 2-pin part both auto-stubs are emitted pointing INWARD, through the
symbol body, putting the local-label anchors inside the part. Measured on
this host (10k 0603 at rot 90: pin1 121.92 -> 124.46, pin2 132.08 ->
129.54, body centre 127.0). Electrically survivable, visually broken.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-carrier
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-28) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

# ---------------------------------------------------------------- symbols
S_J3 = "aiee:DS1021-2X7SF11-B"          # default Reference "U" -> J3
S_J4 = "aiee:DS1021-2X12SF11-B"         # default Reference "U" -> J4
S_R_4K7 = "aiee:0603WAF4701T5E"
S_R_10K = "aiee:0603WAF1002T5E"
S_R_1K = "aiee:0603WAF1001T5E"
S_D_ESD = "aiee:PESD3V3L1BA_C2687129"   # default Reference "U" -> D4x
S_HOLE = "Mechanical:MountingHole"

# ------------------------------------------------------------- footprints
F_J3 = "aiee:HDR-TH_14P-P2.54-V-M-R2-C7-S2.54-1"   # 1.70 mm annulus (EDITS 1)
F_J4 = "aiee:HDR-TH_24P-P2.54-V-M-R2-C12-S2.54"    # 1.70 mm annulus
F_R0603 = "aiee:R0603"
F_SOD323 = "aiee:SOD-323_L1.7-W1.3-LS2.6-BI"
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ------------------------------------------------------------------ values
V_J3 = "DS1021-2x7SF11-B 2x7 male header"
V_J4 = "DS1021-2x12SF11-B 2x12 male header"
V_4K7 = "4.7k 1% 0603"
V_10K = "10k 1% 0603"
V_1K = "1k 1% 0603"
V_ESD = "PESD3V3L1BA 3.3V ESD clamp SOD-323"

# LCSC codes, parts/parts.json. Stamped on every purchased component: KiCad
# 10 DRC raises footprint_symbol_field_mismatch without them at the P5 gate
# (LEARNINGS 2026-07-27). H5 is mechanical and carries none.
LCSC = {
    "J3": "C7430403", "J4": "C7430408",
    "R130": "C23162", "R131": "C23162",
    "R132": "C25804", "R134": "C25804",
    "R135": "C21190", "R136": "C21190", "R137": "C21190",
    "D40": "C2687129", "D41": "C2687129", "D42": "C2687129",
}

# ------------------------------------------ ICD-01 rev A2 s3.1 - J3 POWER
J3_PINS = {
    "1": "+48V_SW", "2": "GND",
    "3": "+48V_SW", "4": "GND",
    "5": "+48V_SW", "6": "GND",
    "7": "GND",     "8": "GND",       # column 4: the all-GND guard column
    "9": "+12V",    "10": "GND",
    "11": "+12V",   "12": "+3V3",
    "13": "GND",    "14": "+3V3",
}

# ----------------------------------------- ICD-01 rev A2 s3.2 - J4 SIGNAL
J4_PINS = {
    "1": "PWM0",        "2": "PWM1",
    "3": "GND",         "4": "GND",
    "5": "PWM2",        "6": "PWM3",
    "7": "PWM4",        "8": "PWM5",
    "9": "GND",         "10": "GND",
    "11": "PWM6",       "12": "PWM7",
    "13": "GND",        "14": "DSPI_SCK",
    "15": "DSPI_MOSI",  "16": "DSPI_MISO",
    "17": "DSPI_CSn",   "18": "I2C_SCL",
    # ADC0/ADC1/ID_ADC reach the connector through R136/R137/R135, so the
    # connector-side node is a different net from the root-crossed one.
    "19": "I2C_SDA",    "20": "ADC0_CONN",
    "21": "ADC1_CONN",  "22": "ID_ADC_CONN",
    "23": "ENABLE",     "24": "FAULT",
}

# The ordered sheet-pin list the ROOT must pass as `nets=` (sheets.md s2.5).
# Shapes are this sheet's point of view: PWM/DSPI drive in from the mcu
# sheet, the analogue trio leaves toward the ADC, I2C and the open-drain
# wire-OR'd FAULT are bidirectional.
HIER_NETS = [
    ("PWM0", "input"), ("PWM1", "input"), ("PWM2", "input"),
    ("PWM3", "input"), ("PWM4", "input"), ("PWM5", "input"),
    ("PWM6", "input"), ("PWM7", "input"),
    ("DSPI_SCK", "input"), ("DSPI_MOSI", "input"),
    ("DSPI_MISO", "output"), ("DSPI_CSn", "input"),
    ("I2C_SCL", "bidirectional"), ("I2C_SDA", "bidirectional"),
    ("ADC0", "output"), ("ADC1", "output"), ("ID_ADC", "output"),
    ("ENABLE", "input"), ("FAULT", "bidirectional"),
]

# Rails present on this sheet. `power:+48V` is re-VALUEd to "+48V_SW"; the
# others are their own stock symbols and the re-VALUE is a no-op.
RAILS = [
    ("+48V_SW", "power:+48V", (127.0, 55.88)),
    ("+12V", "power:+12V", (127.0, 68.58)),
    ("+3V3", "power:+3V3", (127.0, 81.28)),
    ("GND", "power:GND", (127.0, 93.98)),
]


def _rail(sh: schlib.Sheet, net: str, sym: str, at) -> None:
    """Free-area rail cluster: power symbol + local label, NO PWR_FLAG.
    The power symbol makes the net global and BARE; its Value field is what
    names the net, so it is forced to `net` (this is what buys `+48V_SW`
    off the `power:+48V` symbol)."""
    sh.power_flag(net, at=at, sym=sym, flag=False)
    # NB: `set_property("Value", ...)` is a silent no-op on kicad-sch-api
    # 0.5.6 - Value is a dedicated attribute, not a generic property.
    sh.sch.components.get(f"#PWR{sh._pwr_i:02d}").value = net


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "expansion",
        title="LUM-CAR-A: expansion - J3 power / J4 signal (ICD-01 rev A2)",
        paper="A3", date="2026-07-28", company="ai-ee", pwr_base=500)

    # ============================================== J3 - expansion POWER 2x7
    # expect= is pin-name insurance: this symbol's pin NAMES are its pin
    # NUMBERS, so it also proves pad N exists for every N (sheets.md s3.5).
    sh.add_component(S_J3, "J3", V_J3, at=(76.2, 88.9), footprint=F_J3,
                     expect={str(n): str(n) for n in range(1, 15)})
    sh.wire_pins("J3", J3_PINS)

    # ============================================= J4 - expansion SIGNAL 2x12
    sh.add_component(S_J4, "J4", V_J4, at=(76.2, 190.5), footprint=F_J4,
                     expect={str(n): str(n) for n in range(1, 25)})
    sh.wire_pins("J4", J4_PINS)

    # ======================================================== rails (global)
    for net, sym, at in RAILS:
        _rail(sh, net, sym, at)

    # ================================= I2C pull-ups + FAULT pull-up (ICD s3.3)
    sh.add_component(S_R_4K7, "R130", V_4K7, at=(190.5, 55.88),
                     footprint=F_R0603)
    sh.wire_pins("R130", {"1": "I2C_SCL", "2": "+3V3"})
    sh.add_component(S_R_4K7, "R131", V_4K7, at=(190.5, 76.2),
                     footprint=F_R0603)
    sh.wire_pins("R131", {"1": "I2C_SDA", "2": "+3V3"})
    # FAULT: open drain from the daughter, wire-OR'd with U22's FLT on the
    # `pwr` sheet. This is the ONLY pull-up on the net board-wide.
    sh.add_component(S_R_10K, "R132", V_10K, at=(190.5, 96.52),
                     footprint=F_R0603)
    sh.wire_pins("R132", {"1": "FAULT", "2": "+3V3"})

    # ==================================== ID divider TOP leg (ICD s3.3 / Q10)
    # Connector side of R135 on purpose - the daughter's bottom leg and this
    # resistor form the divider, and 1 k inside the ratio would be a 10 %
    # error. Unmated, ID_ADC_CONN is pulled to +3V3 = "no daughter".
    sh.add_component(S_R_10K, "R134", V_10K, at=(190.5, 116.84),
                     footprint=F_R0603)
    sh.wire_pins("R134", {"1": "ID_ADC_CONN", "2": "+3V3"})

    # ============= series protection + 3V3 clamps on the three analogue lines
    # Chain per line:  J4 pin -> <NET>_CONN -> 1k -> <NET> -> clamp -> GND
    #                                                       -> root -> ADC
    for r_ref, d_ref, net, y in (("R135", "D40", "ID_ADC", 152.4),
                                 ("R136", "D41", "ADC0", 177.8),
                                 ("R137", "D42", "ADC1", 203.2)):
        sh.add_component(S_R_1K, r_ref, V_1K, at=(190.5, y),
                         footprint=F_R0603)
        sh.wire_pins(r_ref, {"1": f"{net}_CONN", "2": net})
        # Bidirectional part, generic "1"/"2" pin names: either orientation
        # is valid (see the module docstring). Signal on 1, GND on 2.
        sh.add_component(S_D_ESD, d_ref, V_ESD, at=(241.3, y),
                         footprint=F_SOD323)
        sh.wire_pins(d_ref, {"1": net, "2": "GND"})

    # =================================================== H5 - CAR-REQ-15 hole
    # Board-only mechanical item between J3 and J4 (ICD s7.2: centre 46,74).
    # Zero pins, so it carries no net; it exists to own a refdes and a
    # deterministic placement (constraints.json.placement.edges keys on H5).
    sh.add_component(S_HOLE, "H5", "MountingHole_3.2mm_M3",
                     at=(368.3, 60.96), footprint=F_HOLE)

    # ============================================ hierarchical sheet pins x19
    # Free-cluster variant: local label at one end, hierarchical label at the
    # other, joined by wire GEOMETRY rather than by label name-merging
    # (sheets.md s3.3 - every one of these has 2+ components on it).
    for i, (net, shape) in enumerate(HIER_NETS):
        sh.hier_pin(net, shape=shape, at=(304.8, 55.88 + i * 10.16))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]   # .../kicad
    project = bool(argv[1:] and argv[1] == "--project")
    try:
        sh = build()
        sch = sh.save(out_dir, project=project)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.expansion", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.expansion", "status": "pass",
        "sheet": "expansion",
        "files": [str(sch)],
        "components": len(LCSC) + 1,          # + H5
        "hier_pins": [n for n, _ in HIER_NETS],
        "internal_nets": ["ADC0_CONN", "ADC1_CONN", "ID_ADC_CONN"],
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
