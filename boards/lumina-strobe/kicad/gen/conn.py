"""LUM-DTR-STROBE-A `conn` sheet - the ICD-01 boundary (J3 POWER / J4 SIGNAL).

The SOURCE of this sheet is this file; `kicad/conn.kicad_sch` is BUILD OUTPUT.
Standalone rebuild (sheet only - the root generator owns the .kicad_pro):

    .venv/Scripts/python boards/lumina-strobe/kicad/gen/conn.py

The root generator imports `build()` and stitches this sheet with
`schlib.Project.add_sheet(conn.build(), at=..., size=..., nets=HIER_NETS)`.
`HIER_NETS` below is the exact, ordered sheet-pin list the root must pass -
see "SHEET PINS" at the bottom of this docstring; three of the nineteen are
NOT in `architecture/sheets.md` s0's conn row and the root MUST still stitch
them or the hierarchical labels dangle.

ICD-01 IS THE AUTHORITY FOR J3 AND J4
-------------------------------------
`boards/lumina-carrier/architecture/connector-icd.md` s3.1 / s3.2 is frozen at
H1. The two pin maps below are transcribed from it VERBATIM and must not be
"improved" here: a change is a blocking issue against LUM-CAR-A, a new ICD
revision and a re-baseline of every daughter. This is the daughter (socket)
side; the carrier's `boards/lumina-carrier/kicad/gen/expansion.py` carries the
identical maps on the header side.

  J3 POWER, CONNFLY DS1023-2*7SF11 (C113344), 14 pos - ICD s3.1
      1 +48V_SW   2 GND        3 +48V_SW   4 GND
      5 +48V_SW   6 GND        7 GND       8 GND     <- col 4 = GND guard
      9 +12V     10 GND       11 +12V     12 +3V3
     13 GND      14 +3V3
     3x +48V_SW, 2x +12V, 2x +3V3, 7x GND.

  J4 SIGNAL, CONNFLY DS1023-2*12SF11 (C92265), 24 pos - ICD s3.2
      1 PWM0      2 PWM1       3 GND       4 GND
      5 PWM2      6 PWM3       7 PWM4      8 PWM5
      9 GND      10 GND       11 PWM6     12 PWM7
     13 GND      14 DSPI_SCK  15 DSPI_MOSI 16 DSPI_MISO
     17 DSPI_CSn 18 I2C_SCL   19 I2C_SDA  20 ADC0
     21 ADC1     22 ID_ADC    23 ENABLE   24 FAULT
     No 48 V exists anywhere on this connector. The interleaved GND pins
     (3/4, 9/10, 13) are PWM return paths and are not filler.

BOTH CONNECTOR SYMBOLS DEFAULT TO REFERENCE "H", NOT "J"
-------------------------------------------------------
Verified by reading `lib/aiee.kicad_sym`: `DS1023-2*7SF11` and
`DS1023-2*12SF11` both carry a default Reference of "H" (the carrier's
DS1021 pair default to "U" - same trap, different letter). The refdes is
forced here. `constraints.json.placement.edges` keys on J3/J4/H5 and two
other board runs cross-reference them, so a wrong refdes is expensive.

ICD-MANDATED AND NORMATIVE CONTENT ON THIS SHEET
------------------------------------------------
R1   100 k ENABLE pull-down to GND. ICD s8.2, MANDATORY: the daughter must
     fail de-energised when the connector is unmated, mis-seated by one
     position, or a pin is unsoldered. Never latched locally.
R2   2.7 kOhm 1 % ID_ADC BOTTOM leg to GND. ICD s3.4 (rev A3, NORMATIVE) is
     a code table, not a suggestion: 2.7 k = code 1 = LUM-STR-A, V_ID
     0.702 V against the carrier's 10 k top leg. 4.7 k is CODE 2 =
     LUM-PAR-A - fitting it would make this board announce itself as the
     RGBW par and be handed the wrong daughter profile (this was a real
     defect, fixed at parts.json rev D / P3-OPEN-5). 1 % is required, not
     5 %: adjacent-code separation is 0.353 V against ~+/-0.05 V of
     worst-case divider error and a +/-0.15 V firmware detection window.
     The carrier fits the TOP leg; the daughter fits ONLY the bottom leg.
NO I2C PULL-UPS ANYWHERE ON THIS BOARD. ICD s3.3: the carrier's 4.7 k own
     the bus, and a second pair would halve the bus resistance. Neither
     `I2C_SCL` nor `I2C_SDA` touches anything on this sheet except J4 and
     its sheet pin - that is deliberate and checkable by eye below.
NO FAULT PULL-UP. ICD s3.3 / sheets.md s3 point 2: `FAULT` is open drain,
     active low, wire-OR'd with the carrier's own eFuse fault output, and
     the carrier's 10 k is the only pull-up on the net board-wide. Nothing
     on this board may ever drive it high (the `protect` sheet's Q404 is
     the open-drain translator that keeps that true).

THE TWO ADC RC FILTERS - AND WHERE THE SERIES RESISTOR HAD TO GO
----------------------------------------------------------------
sheets.md s2.1 allocates `R3, C3` (1 k + 10 nF) to ADC0 and `R4, C4` to
ADC1. A series element necessarily SPLITS a signal into two nets, so for
each channel exactly one of the two nodes can carry the canonical name:

  ADC0:  /VBANK_SENSE --R3(1k)--> /ADC0 --C3(10n)--> GND, and J4-20 = /ADC0
         The canonical name lands on the CONNECTOR pin, which is what the
         ICD names. sheets.md s1.2 already declares `/VBANK_SENSE` and
         `/ADC0` as two different nets, so this split is the architecture's.

  ADC1:  /ADC1 --R4(1k)--> ADC1_CONN --C4(10n)--> GND, and J4-21 = ADC1_CONN
         Here the SOURCE side already owns the canonical name: sheets.md
         s1.2 makes `/ADC1` the protect->conn net. The connector-side node
         is therefore sheet-internal, `/conn/ADC1_CONN` - the same name the
         carrier uses for the mirror-image node on its side of the mated
         pair (expansion.py `ADC1_CONN`). No constraint references it.

C3/C4 are the reason the R exists at all: the bank divider's 9.43 k source
impedance sits at the ICD s3.3 10 kOhm ceiling and a SAR sample needs a
local charge reservoir. NOTE, and flagged to the orchestrator rather than
silently "fixed" here: the series 1 k adds to that source impedance, so
ADC0 presents 10.43 kOhm at J4-20 against the ICD's 10 kOhm limit (and the
carrier then adds its own 1 k, R136). That is an architecture number, not a
wiring choice - the topology below is what sheets.md s2.1 specifies.

TEST POINTS - THREE NETS THIS SHEET WOULD NOT OTHERWISE SEE
-----------------------------------------------------------
sheets.md s2.1 puts ALL SIX board test points on this sheet:
    TP1 +48V_SW   TP2 /VBANK    TP3 GND
    TP4 /OT_TRIP  TP5 /UVLO_n   TP6 /ENABLE
`+48V_SW`, `GND` and `ENABLE` are already here. `/VBANK`, `/OT_TRIP` and
`/UVLO_n` are NOT in sheets.md s0's conn interface-net column, so three
extra sheet pins are exposed to carry them (marked [TP] in HIER_NETS).
Two consequences the orchestrator owns, not this sheet:
  * The root MUST stitch all nineteen nets in HIER_NETS. Passing only s0's
    sixteen leaves three hierarchical labels with no sheet pin.
  * `/VBANK` is 57 V / 10.4 A and `constraints.json` requires it POURED
    (power_tree.md s11). TP2 drags that pour to wherever the annealer puts
    a test point, inside a sheet whose other nets are 3.3 V ICD signals at
    0.635 mm HV clearance. If P5/P6 would rather TP2 lived on `charge`,
    delete TP2 + the VBANK sheet pin here - nothing else on this sheet
    references either.
All six carry the floating-PoE silkscreen warning (sheets.md s2.1); that is
a P5/P6 silkscreen job, not a schematic one.

DSPI IS DELIBERATELY NOT CONNECTED
----------------------------------
J4-14/15/16/17 (`DSPI_SCK`, `DSPI_MOSI`, `DSPI_MISO`, `DSPI_CSn`) are ICD
signals this daughter does not use - no SPI device is on the BOM and
blocks.md s4 routes all telemetry over I2C. They are flagged no-connect
rather than left floating: the symbol types every J4 pin `input`, and an
unconnected input is an ERC error by the P4 gate's own rule.

NET NAMING (architecture/sheets.md s1)
--------------------------------------
* GND / +3V3 / +12V / +48V_SW are POWER SYMBOLS -> global, BARE names, no
  sheet pin. `+48V_SW` has no stock symbol: `power:+48V` is placed and its
  VALUE field is set to "+48V_SW" (a power symbol's net name comes from its
  Value, not its library pin name - measured on this host against
  kicad-cli 10.0.3, LEARNINGS 2026-07-28). A local label alone would give
  `/conn/+48V_SW` and `netlist_audit --constraints` would raise missing_net
  at ERROR, because constraints.json declares `+48V_SW` bare.
* ALL FOUR PWR_FLAGs live here (sheets.md s1.1) - this is the sheet that
  owns the connector, and every rail on this board is fed passively through
  J3 with no on-board regulator to drive it. #FLG100..#FLG103 via
  pwr_base=100 (schlib formats them 3-digit, sheets.md writes "#FLG0100+";
  the requirement is uniqueness across sheets and the other six sheets
  start at 200/300/.../700).
* The nineteen HIER_NETS cross the root and become `/NAME`.
* One net is sheet-internal and becomes `/conn/ADC1_CONN` (see above).

ROTATION IS DELIBERATELY UNUSED
-------------------------------
Every component is at rotation 0. schlib's `stub_dir` and kicad-sch-api
disagree on the sign of a 90 deg symbol rotation, so a rotated 2-pin part
gets BOTH auto-stubs pointing inward through its own body, putting the
local-label anchors inside the symbol (LEARNINGS 2026-07-28).

LIBRARY PIN TYPES MUST BE RETYPED BEFORE THE ERC GATE
-----------------------------------------------------
`lib/aiee.kicad_sym` is an untouched easyeda2kicad pull: `DS1023-2*12SF11`
types all 24 pins `input`, `DS1023-2*7SF11` types all 14 `unspecified`, and
every 0603/0805 passive here is `input` or `unspecified` (measured from the
library text, which is the ground truth - `schlib --pins` reports
`unspecified` as "passive"). kicad-cli 10.0.3 ERC --severity-all then emits
`pin_to_pin` warnings and FALSE `pin_not_driven` errors, and the P4 gate
wants errors+warnings=0. The board-wide fix is a `lib_pin_types.py` retype
pass (pattern: `boards/lumina-carrier/kicad/gen/lib_pin_types.py`), which is
a SHARED artifact across all seven sheets and is therefore the root/
orchestrator's to own, not this sheet's.
ORDER MATTERS: a saved .kicad_sch EMBEDS its lib symbols, so THIS SHEET MUST
BE REGENERATED AFTER the retype - fixing the library alone does not fix an
already-built sheet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-strobe
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-28) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

# ---------------------------------------------------------------- symbols
S_J3 = "aiee:DS1023-2*7SF11"        # default Reference "H" -> forced to J3
S_J4 = "aiee:DS1023-2*12SF11"       # default Reference "H" -> forced to J4
S_R_100K = "aiee:0603WAF1003T5E"
S_R_2K7 = "aiee:0603WAF2701T5E"
S_R_1K = "aiee:0603WAF1001T5E"
S_C_100N = "aiee:CC0603KRX7R9BB104"
S_C_10N = "aiee:0603B103K500NT"
S_C_4U7 = "aiee:CL21A475KAQNNNE"
S_TP = "Connector:TestPoint"
S_HOLE = "Mechanical:MountingHole"

# ------------------------------------------------------------- footprints
F_J3 = "aiee:HDR-TH_14P-P2.54-V-F-R2-C7-S2.54-1"   # 2x7 socket, 8.5 mm body
F_J4 = "aiee:HDR-TH_24P-P2.54-V-F-R2-C12-S2.54"    # 2x12 socket
F_R0603 = "aiee:R0603"
F_C0603 = "aiee:C0603"
F_C0805 = "aiee:C0805"
F_TP = "TestPoint:TestPoint_Pad_D1.5mm"
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ------------------------------------------------------------------ values
V_J3 = "DS1023-2*7SF11 2x7 socket"
V_J4 = "DS1023-2*12SF11 2x12 socket"
V_100K = "100k 1% 0603"
V_2K7 = "2.7k 1% 0603"
V_1K = "1k 1% 0603"
V_100N = "100nF 50V X7R 0603"
V_10N = "10nF 50V X7R 0603"
V_4U7 = "4.7uF 25V X5R 0805"

# LCSC codes, parts/parts.json. Stamped on every PURCHASED component: KiCad
# 10 DRC raises footprint_symbol_field_mismatch without them at the P5 gate
# (LEARNINGS 2026-07-27). H5 and TP1-TP6 are footprints, not parts.
LCSC = {
    "J3": "C113344", "J4": "C92265",
    "R1": "C25803",                       # 100k 0603 1%  - ENABLE pull-down
    "R2": "C13167",                       # 2.7k 0603 1%  - ID_ADC code 1
    "R3": "C21190", "R4": "C21190",       # 1k 0603 1%    - ADC series
    "C1": "C1779",                        # 4.7uF 0805    - +12V bulk
    "C2": "C14663", "C5": "C14663",       # 100nF 0603
    "C3": "C57112", "C4": "C57112",       # 10nF 0603     - ADC reservoirs
}

# ------------------------------------------ ICD-01 s3.1 - J3 POWER, 2x7
J3_PINS = {
    "1": "+48V_SW", "2": "GND",
    "3": "+48V_SW", "4": "GND",
    "5": "+48V_SW", "6": "GND",
    "7": "GND",     "8": "GND",       # column 4: the all-GND guard column
    "9": "+12V",    "10": "GND",
    "11": "+12V",   "12": "+3V3",
    "13": "GND",    "14": "+3V3",
}

# ----------------------------------------- ICD-01 s3.2 - J4 SIGNAL, 2x12
J4_PINS = {
    "1": "PWM0",        "2": "PWM1",
    "3": "GND",         "4": "GND",
    "5": "PWM2",        "6": "PWM3",
    "7": "PWM4",        "8": "PWM5",
    "9": "GND",         "10": "GND",
    "11": "PWM6",       "12": "PWM7",
    # DSPI x4: no SPI device on this daughter (see docstring). NC, not float.
    "13": "GND",        "14": "NC",     # DSPI_SCK  - unused
    "15": "NC",         "16": "NC",     # DSPI_MOSI / DSPI_MISO - unused
    "17": "NC",         "18": "I2C_SCL",  # DSPI_CSn - unused
    "19": "I2C_SDA",    "20": "ADC0",
    "21": "ADC1_CONN",  "22": "ID_ADC",
    "23": "ENABLE",     "24": "FAULT",
}

# The ordered sheet-pin list the ROOT must pass as `nets=`. Shapes are this
# sheet's point of view and land on the ROOT's sheet pins (the child's own
# hierarchical labels always come out `input` - kicad-sch-api 0.5.6 drops the
# shape argument; KiCad 10.0.3 does not check sheet-pin/label parity).
# [TP] = present only to carry a test point (see docstring); the root must
# stitch it anyway or the label dangles.
HIER_NETS = [
    ("PWM0", "output"), ("PWM1", "output"), ("PWM2", "output"),
    ("PWM3", "output"), ("PWM4", "output"), ("PWM5", "output"),
    ("PWM6", "output"), ("PWM7", "output"),
    ("ENABLE", "output"),          # conn -> charge, 4x drive, protect
    ("FAULT", "input"),            # protect -> conn (open drain, no pull-up)
    ("I2C_SCL", "bidirectional"), ("I2C_SDA", "bidirectional"),
    ("VBANK_SENSE", "input"),      # charge -> conn (divided bank voltage)
    ("ADC0", "output"),            # conn-local, canonical name per s1.2
    ("ADC1", "input"),             # protect -> conn
    ("ID_ADC", "output"),          # conn-local, canonical name per s1.2
    ("VBANK", "input"),            # [TP] TP2 only
    ("OT_TRIP", "input"),          # [TP] TP4 only
    ("UVLO_n", "input"),           # [TP] TP5 only
]

# Rails. `power:+48V` is re-VALUEd to "+48V_SW"; the other three re-VALUEs
# are no-ops. flag=True on all four: J3 feeds them passively and nothing on
# this board drives them, so without a PWR_FLAG ERC calls every rail
# undriven (sheets.md s1.1 puts all four flags here).
RAILS = [
    ("+48V_SW", "power:+48V", (114.3, 50.8)),
    ("+12V", "power:+12V", (114.3, 63.5)),
    ("+3V3", "power:+3V3", (114.3, 76.2)),
    ("GND", "power:GND", (114.3, 88.9)),
]

# TP1-TP6, sheets.md s2.1. Every one needs the floating-PoE silk warning.
TEST_POINTS = [
    ("TP1", "+48V_SW", (228.6, 50.8)),
    ("TP2", "VBANK", (228.6, 63.5)),
    ("TP3", "GND", (228.6, 76.2)),
    ("TP4", "OT_TRIP", (228.6, 88.9)),
    ("TP5", "UVLO_n", (228.6, 101.6)),
    ("TP6", "ENABLE", (228.6, 114.3)),
]


def _rail(sh: schlib.Sheet, net: str, sym: str, at) -> None:
    """Free-area rail cluster: power symbol + local label + PWR_FLAG. The
    power symbol makes the net global and BARE, and its VALUE field is what
    names it, so it is forced to `net` (this is what buys `+48V_SW` off the
    `power:+48V` symbol). The local label on the same wire is what merges
    every other same-named label on this sheet into the global rail."""
    sh.power_flag(net, at=at, sym=sym, flag=True)
    # NB: set_property("Value", ...) is a SILENT no-op on kicad-sch-api
    # 0.5.6 - Value is a dedicated attribute, not a generic property.
    sh.sch.components.get(f"#PWR{sh._pwr_i:02d}").value = net


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "conn",
        title="LUM-DTR-STROBE-A: conn - J3 power / J4 signal (ICD-01 s3)",
        paper="A3", date="2026-07-28", company="ai-ee", pwr_base=100)

    # ================================================ J3 - POWER socket 2x7
    # expect= is pin-name insurance: these symbols' pin NAMES are their pin
    # NUMBERS, so it also proves pad N exists for every N in the ICD map.
    sh.add_component(S_J3, "J3", V_J3, at=(63.5, 76.2), footprint=F_J3,
                     expect={str(n): str(n) for n in range(1, 15)})
    sh.wire_pins("J3", J3_PINS)

    # =============================================== J4 - SIGNAL socket 2x12
    sh.add_component(S_J4, "J4", V_J4, at=(63.5, 190.5), footprint=F_J4,
                     expect={str(n): str(n) for n in range(1, 25)})
    sh.wire_pins("J4", J4_PINS)

    # ================================================ rails (global) + flags
    for net, sym, at in RAILS:
        _rail(sh, net, sym, at)

    # ============================== R1 - ENABLE pull-down, 100 k (ICD s8.2)
    # MANDATORY. Unmated / mis-seated / unsoldered ENABLE => de-energised.
    sh.add_component(S_R_100K, "R1", V_100K, at=(165.1, 50.8),
                     footprint=F_R0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("R1", {"1": "ENABLE", "2": "GND"})

    # ============ R2 - ID_ADC bottom leg, 2.7 k 1% = ICD s3.4 code 1 (STR-A)
    # The carrier fits the 10 k TOP leg; this is the ONLY ID resistor on the
    # daughter. 4.7 k here would announce this board as LUM-PAR-A.
    sh.add_component(S_R_2K7, "R2", V_2K7, at=(165.1, 63.5),
                     footprint=F_R0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("R2", {"1": "ID_ADC", "2": "GND"})

    # ===================================== ADC0 RC: /VBANK_SENSE -> J4-20
    sh.add_component(S_R_1K, "R3", V_1K, at=(165.1, 76.2),
                     footprint=F_R0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("R3", {"1": "VBANK_SENSE", "2": "ADC0"})
    sh.add_component(S_C_10N, "C3", V_10N, at=(165.1, 88.9),
                     footprint=F_C0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("C3", {"1": "ADC0", "2": "GND"})

    # ======================================= ADC1 RC: /ADC1 -> J4-21
    sh.add_component(S_R_1K, "R4", V_1K, at=(165.1, 101.6),
                     footprint=F_R0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("R4", {"1": "ADC1", "2": "ADC1_CONN"})
    sh.add_component(S_C_10N, "C4", V_10N, at=(165.1, 114.3),
                     footprint=F_C0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("C4", {"1": "ADC1_CONN", "2": "GND"})

    # ============================================== rail decoupling at J3
    # C1 is deliberately SMALL (<= 4.7 uF, sheets.md s2.1 / power_tree s7.4)
    # so the drive-stage error amps die promptly on unplug instead of
    # holding a gate up on stored charge.
    sh.add_component(S_C_4U7, "C1", V_4U7, at=(165.1, 127.0),
                     footprint=F_C0805, expect={"1": "1", "2": "2"})
    sh.wire_pins("C1", {"1": "+12V", "2": "GND"})
    sh.add_component(S_C_100N, "C5", V_100N, at=(165.1, 139.7),
                     footprint=F_C0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("C5", {"1": "+12V", "2": "GND"})
    sh.add_component(S_C_100N, "C2", V_100N, at=(165.1, 152.4),
                     footprint=F_C0603, expect={"1": "1", "2": "2"})
    sh.wire_pins("C2", {"1": "+3V3", "2": "GND"})

    # =========================================== TP1-TP6 (sheets.md s2.1)
    for ref, net, at in TEST_POINTS:
        sh.add_component(S_TP, ref, net, at=at, footprint=F_TP,
                         expect={"1": "1"})
        sh.wire_pin(ref, "1", net)

    # ============================== H5 - ICD s7.2 / s7.5 5th mounting hole
    # board_init --mounting-holes makes CORNER holes only; H5 is added at P4
    # as a symbol so it carries a refdes and a deterministic placement
    # (constraints.json.placement.edges keys on it). Zero pins, no net.
    sh.add_component(S_HOLE, "H5", "MountingHole_3.2mm_M3",
                     at=(355.6, 50.8), footprint=F_HOLE)

    # =========================================== hierarchical sheet pins x19
    # Free-cluster variant: local label at one end, hierarchical label at the
    # other, joined by wire GEOMETRY rather than by label name-merging.
    for i, (net, shape) in enumerate(HIER_NETS):
        sh.hier_pin(net, shape=shape, at=(279.4, 45.72 + i * 10.16))

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
        print(json.dumps({"script": "gen.conn", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.conn", "status": "pass",
        "sheet": "conn",
        "files": [str(sch)],
        "components": len(LCSC) + len(TEST_POINTS) + 1,     # + H5
        "hier_pins": [n for n, _ in HIER_NETS],
        "internal_nets": ["ADC1_CONN"],
        "no_connects": ["J4-14 DSPI_SCK", "J4-15 DSPI_MOSI",
                        "J4-16 DSPI_MISO", "J4-17 DSPI_CSn"],
        "pwr_flags": ["+48V_SW", "+12V", "+3V3", "GND"],
        "decoupling_associations": len(sh.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
