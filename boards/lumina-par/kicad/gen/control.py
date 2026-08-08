"""LUM-PAR-A `control` sheet - B2 (ENABLE gating + fail-safe logic) and
B5 (board ID + calibration store).

The SOURCE of this sheet is this file; `kicad/control.kicad_sch` is BUILD
OUTPUT. Standalone rebuild (sheet only - the root generator owns the
project file and the real ERC gate):

    .venv/Scripts/python boards/lumina-par/kicad/gen/control.py --out <dir>

Refdes range: 200-299 for every prefix, `#PWR` base 200 (sheets.md s1).
J4 is exempt by name - the ICD assigns it (sheets.md s1 "Exception").

architecture/p4-wiring-notes.md IS BINDING AND SUPERSEDES sheets.md.
Everything below traces to it, to parts/<lcsc>.json, or to
brief/06-connector-icd.md; nothing is wired from memory. Pin tables were
read with `schlib.py --pins ... --lib lib/aiee.kicad_sym` and every IC
carries `expect={}` pin-name insurance.

THREE ERRATA / TRAPS THIS SHEET IS BUILT AROUND
-----------------------------------------------
1. SN74LVC00A (U202): the datasheet's sec 6 Pin Functions table has its
   TYPE and DESCRIPTION columns SHIFTED BY ONE ROW from 3Y down - it
   prints 3Y (pin 8) as a power pin and VCC (pin 14) as gate 3's output,
   and it swaps the 3A/3B and 4A/4B descriptions. The pin NUMBERS and the
   D-package Top View diagram are self-consistent and are the authority
   (parts/C485072.json layout_notes, p4-wiring-notes s3). Wired from the
   diagram: 7 = GND, 8 = 3Y, 9/10 = 3A/3B, 11 = 4Y, 12/13 = 4A/4B,
   14 = VCC. VCC is 1.65-3.6 V ONLY (not 5 V rated) - fine at 3.3 V.
2. M24C32 (U203): E0/E1/E2 (pins 1/2/3) to VSS gives the 0x50 base
   address, and WC (pin 7) is ACTIVE HIGH write protect despite the
   overbar the datasheet renders - it must be tied to VSS (through R209)
   for the part to be writable at commissioning. Left floating it reads
   VIL and writes would still work, but "must be tied to VCC or VSS"
   applies to E0/E1/E2 and a defined WC is free.
3. R206 = 4.7 kOhm 1 % REQUIRED. sheets.md s1.2 still says "VALUE TBD -
   P4 blocker"; that text is STALE. CR-1 is CLOSED (state.json, twice):
   LUM-PAR-A is ID_ADC code 2, V_ID = 1.055 V against the carrier's 10 k
   top leg (ICD-01 s3.4, NORMATIVE). See the R206 note in build() for the
   library/BOM consequence.

FAIL-SAFE RULES THAT MUST SURVIVE EVERY LATER EDIT
--------------------------------------------------
* `/FAULT` IS OPEN DRAIN AND MUST NEVER BE DRIVEN HIGH. Its only drivers
  are the `thermal` sheet's LM339LV open-drain outputs and R207, the
  100 k local pull-up that keeps the node defined while unmated. ERC will
  want a driving pin; do not let a fix loop add a push-pull driver.
* NO I2C PULL-UPS ON THIS BOARD. The carrier fits 4.7 k (ICD s3.3) and a
  second pair is an ICD violation. This is P4's reflex - the decision is
  recorded as a schematic note as well as here.
* NO RC FILTER ON PWM0-3 OR `/SHUNT0-3`. tau <= 14 ns if any network is
  fitted at all (blocks.md B2) - the reflex 1 k + 100 pF is tau = 100 ns
  and would swallow the 141 ns pulse PAR-REQ-01 is about.
* `PWM4..7` and `DSPI_SCK/MOSI/MISO/CSn` land on J4 and are DELIBERATE
  no-connects (four channels on rev A; decisions.md D2 rejects a local
  PWM generator). Each carries an explicit `~` no-connect so ERC stays
  clean AND a reviewer can see the decision.
* R201 is the ICD s8.2 mandatory 100 k ENABLE pull-down, at the CONNECTOR
  END and BEFORE any series element. There is no series element on this
  board - U201's A input is fed directly from J4-23 - so "connector end"
  is a P6 placement obligation. See OPEN in the return block:
  constraints.json binds R202-R205 to the `gate` group but binds R201 to
  nothing.
* R218-R221 ARE THE `/DRV_ENn` FAIL-SAFE PULL-DOWNS AND MUST STAY 10 k.
  They are the only thing holding the four TPS92515HV PWM/enable pins low
  in the window where `+12V` is up and `+3V3` is not - every power-up
  passes through it, and a 12 V-only bench bring-up sits in it forever.
  U201 is Ioff-disabled there (partial-power-down, SCES217Y) and drives
  nothing, so without these the pins are undriven and ICD s8.2's "every
  output stage gated by ENABLE" does not hold.
  DO NOT "harmonise" them to the 100 k this board uses for every other
  pull-down. The PWM/UVLO pin SOURCES its own hysteresis current above
  threshold - IPWM(uvlo-hys) = -25 / -20 / -15 uA (parts/C213553.json
  sec 7.5; size to the 25 uA MAGNITUDE, which is the MIN column of a
  negative spec) - so any pull-down floats at I x R:
      100 k -> 2.50 V    47 k -> 1.18 V    22 k -> 0.55 V    10 k -> 0.25 V
  The release criterion is the worst-case FALLING threshold,
  VPWM(uvlo)min - VPWM(uvlo-hys)max = 0.95 - 0.150 = 0.80 V. 100 k and
  47 k sit ABOVE it: one noise event over 1.0 V latches all four drivers
  ON at full LED current and they never release. 22 k has no margin left
  once the rest of the node is counted.
  WHOLE-NODE WORST CASE AT 10 k (R214-R217 fitted, so `/EN_OK` and the
  four `/DRV_ENn` are one electrical node carrying four pull-downs in
  parallel = 2.5 k):
      4 x 25 uA (U301/U321/U341/U361 hysteresis)
    +     10 uA (U201-4 Ioff, VO = 5.5 V, SCES217Y)
    + 4 x  5 uA (U202 1B/2B/3B/4B II, SCAS279R - that datasheet has no
                 Ioff row, so II is the bound used)
    = 130 uA x 2.5 k = 0.325 V, i.e. 2.5x below the 0.80 V threshold.
  With the one-shot option populated the links come out and each channel
  stands alone: (25 + 5) uA x 10 k = 0.30 V. Same answer.
  COST: 4 x 3.3 V / 10 k = 1.32 mA on `+3V3` when `/EN_OK` is high (only
  1.22 mA of it from the rail - the hysteresis current is sourced from the
  drivers' own VCC). That takes power_tree.md s4's housekeeping inventory
  from 1.4 mA to 2.7 mA against a <= 5 mA budget. U201 sinks/sources it
  against a +-24 mA rating. Reported in OPEN: the s4 inventory needs the row.
  THEY BELONG ON THE `/DRV_ENn` SIDE OF R214-R217, NOT ON `/EN_OK`. The
  one-shot option removes those links, and U204 is powered from `+3V3`
  too, so an `/EN_OK`-side pull-down (one 2.5 k would be the same current)
  would put this exact defect straight back whenever the option is fitted.

NET NAMING - THE CONTRACT, AND THE /PWM0../PWM3 CASE (SETTLED)
---------------------------------------------------------------
sheets.md s2 is binding: power nets are bare GLOBAL power symbols
(`+3V3`, `GND` here); every inter-sheet signal is `/NAME`, which KiCad
only produces when the ROOT places a local label on the crossed wire
(schlib.Project.add_sheet does exactly that). A net named by a sheet-local
label alone comes out `/<sheet>/NAME` - measured, not assumed, on the
sibling board's shipped netlist (boards/lumina-carrier/work/board.net has
`/expansion/ADC0_CONN` and `/mcu/BOOT` beside root-crossed `/PWM0`).

CONSEQUENCE FOR /PWM0../PWM3 - SETTLED AT THE ROOT STITCH, THE OTHER WAY.
sheets.md s2 files the four PWM nets as "`control` (J4) internal", so they
come out `/control/PWM0`..`/control/PWM3`, while
`constraints.json.high_speed` originally spelled them `/PWM0`..`/PWM3` - a
mismatch that would make `netlist_audit` raise missing_net and silently
drop the jitter-sensitive nets from all SEVEN high_speed consumers.

The orchestrator ruled that the two must agree and preferred renaming the
NETS (append four `("PWM<n>", "input")` tuples here, let the root spell
them). **That mechanism was built and MEASURED, and it is not ERC-clean:**
a root-crossed net whose only connection point on the root sheet is ONE
sheet pin makes the root's local label raise `label_dangling` ("Label not
connected") - 4 errors, one per PWM. It is not a naming or geometry fault:
the label sits on the wire endpoint and the netlist is correct
(`/PWM0` = J4-1 + R202-1 + U202-1). Two independent probes pinned the
rule: a SECOND same-named root label does not satisfy it (8 errors, both
labels flagged), while one real symbol pin on the root net does (0/0).
Every other root net here escapes it only because two children expose it,
giving the root two sheet pins. Buying that for PWM would mean adding
four parts to the root, which is a design change, not a stitch fix.

So the SANCTIONED FALLBACK was taken instead: the four `high_speed`
entries were re-spelled `/control/PWM0..3` in `architecture/constraints.json`
and `kicad/constraints.json`, and this sheet keeps the PWM nets local
exactly as sheets.md s2 files them. Note that sheets.md s2's own net table
still prints `/PWM0`; p4-wiring-notes.md supersedes it.

`/ENABLE`, `/ID_ADC`, `/I2C_SCL`, `/I2C_SDA` are in the same position and
also come out `/control/NAME`. No constraint references any of them.

THE CONVERTER-IDLE ONE-SHOT IS A DNP OPTION, AND IT IS IN THE NETLIST
--------------------------------------------------------------------
U204 + R210-R213 + C210-C213 + D201-D204 (sheets.md s4 rule 1: a DNP part
still has pads, so its clearance and area are accounted for at P6/P7 and
the option stays a populate change rather than a respin). Marked
`Variant = DNP`.

Topology, per channel n, and WHY IT IS SOURCED FROM `/SHUNTn`:

    /SHUNTn --+--[ R21n 100k ]--+-- IDLEn --[ U204 inverter ]-- /DRV_ENn
              |                 |
              +--|<|-- D20n ----+          C21n 10nF from IDLEn to GND
                (A on IDLEn, K on /SHUNTn: fast DISCHARGE)

`/SHUNTn = NOT(PWMn AND /EN_OK)`, so it is an already-inverted PWM that
ALREADY carries `/EN_OK`. Every PWM pulse yanks IDLEn down through D20n;
between pulses it recovers through R21n with tau = 100 k x 10 nF = 1.0 ms.
Pulses stop (channel at 0 %, or `/EN_OK` low, which pins `/SHUNTn` high) ->
IDLEn crosses the LVC14A's VT+ in ~0.8 ms -> the inverter drops `/DRV_ENn`
and the converter stops free-running into the shunt FET. That is exactly
blocks.md B3's "ANDed with /EN_OK, so ENABLE still kills it, and it clears
itself", with no extra gate: a hex inverter has 6 gates and a
buffer-per-channel scheme would need 8.

IF THE OPTION IS POPULATED, R214-R217 MUST BE REMOVED (sheets.md s1.2) -
the 0 R links and the inverter outputs would otherwise both drive
`/DRV_ENn`. Both sets are in the netlist by design; the library pins are
all `passive` after the P4 retype pass, so ERC does not see a conflict.
Two bench items are recorded in the return block's OPEN (the 1N4148's Vf
floor under the Schmitt VT-, and the 10 nF the diode hangs off `/SHUNTn`).

DECOUPLING
----------
One 100 nF per supply pin, from each part's own datasheet extract:
C201/U201-5, C202/U202-14, C203/U203-8, C205/U204-14. `+3V3` and `GND`
are global power-SYMBOL names, so the wiring label and the final netlist
name are identical bare strings - no rail_net/gnd_net override is needed
(contrast a root-local rail, which would need one). C204 is not a
decoupler: it is the B5 `ID_ADC` settling cap.

NO PWR_FLAG ON THIS SHEET - CONSUMING POWER SYMBOLS ONLY.
`+3V3` and `GND` (and `+12V`/`+48V_SW`, which never reach this sheet) are
flagged exactly once, on the `power` sheet, where every rail enters the
board through J3's passive pins (sheets.md s2; confirmed by the `power`
sheet agent this session). PWR_FLAG's pin is `power_out`, so a second flag
on the same rail collides `power_out <-> power_out` at the project ERC and
fails the gate - the same failure mode p4-wiring-notes s2 warns about on
the driver VCC nodes. Every rail symbol here goes through
`power_symbol_at_pin`, which places a bare power symbol and no flag;
`Sheet.power_flag(..., flag=True)` must never be called from this file.
Standalone this sheet therefore ERCs with `power_pin_not_driven` on both
rails - that is expected and is what the root build resolves.

ROTATION IS DELIBERATELY UNUSED - every symbol is at rotation 0. schlib's
stub_dir and kicad-sch-api disagree on the sign of a 90 deg rotation
(LEARNINGS 2026-08-06 [kicad-sch-api]); the carrier run hit it and every
sheet there is at 0 too.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/lumina-par
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled lib.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

import schlib  # noqa: E402

FP = "aiee"

# ------------------------------------------------------------------ symbols
S_J4 = "aiee:DS1023-2*12SF11"
S_U201 = "aiee:SN74LVC1G08DBVR"
S_U202 = "aiee:SN74LVC00ADR"
S_U203 = "aiee:M24C32-WMN6TP"
S_U204 = "aiee:SN74LVC14ADR"
S_R_100K = "aiee:0603WAF1003T5E"
S_R_10K = "aiee:0603WAF1002T5E"
S_R_0R = "aiee:0603WAF0000T5E"
S_C_100N = "aiee:CC0603KRX7R9BB104"
S_C_10N = "aiee:0603B103K500NT"
S_D_SW = "aiee:1N4148W_C81598"

# --------------------------------------------------------------- footprints
F_J4 = f"{FP}:HDR-TH_24P-P2.54-V-F-R2-C12-S2.54"   # -F- = the SOCKET half
F_SOT235 = f"{FP}:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR"
F_SOIC14 = f"{FP}:SOIC-14_L8.7-W3.9-P1.27-LS6.0-BL"
F_SOIC8 = f"{FP}:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL"
F_R0603 = f"{FP}:R0603"
F_C0603 = f"{FP}:C0603"
F_SOD123F = f"{FP}:SOD-123F_L2.7-W1.6-LS3.8-RD"

# ------------------------------------------------- values (parts.json verbatim)
# bom_cpl groups BOM rows by (value, footprint, LCSC), and parts.json is the
# BOM of record, so these strings are copied from it rather than restyled.
V_J4 = ("DS1023-2*12SF11 2x12 socket, 2.54 mm, 600 V, 3 A/contact, "
        "8.5 mm body")
V_U201 = "SN74LVC1G08DBVR single 2-input AND, SOT-23-5"
V_U202 = "SN74LVC00ADR quad 2-input NAND, SOIC-14"
V_U203 = "M24C32-WMN6TP 32 kbit I2C EEPROM, SOIC-8"
V_U204 = "SN74LVC14ADR hex Schmitt-trigger inverter, SOIC-14"
V_100K = "100k 0603 1%"
V_10K = "10k 0603 1%"
V_0R = "0R 0603"
V_100N = "100nF 50V X7R 0603"
V_10N = "10nF 50V X7R 0603"
V_D = "1N4148W switching diode, SOD-123"
# CR-1 CLOSED (p4-wiring-notes s1, ICD-01 s3.4 code 2). NOT "TBD".
V_R206 = "4.7k 0603 1%"

# ----------------------------------------- ICD-01 rev A3 s3.2 - J4 SIGNAL 2x12
# Transcribed verbatim from brief/06-connector-icd.md s3.2. The DS1023
# datasheet publishes NO pin numbers (p4-wiring-notes s4), so the ICD is the
# only authority; a change here is a blocking issue against LUM-CAR-A, not an
# edit. Odd positions are row A, even row B, n and n+1 across from each other.
# The interleaved GND pins (3/4, 9/10, 13) are deliberate return paths beside
# the PWM edges - they are not filler.
# "NC" -> schlib emits an explicit no-connect at the pin (rule 4 above).
# ===================== MATED-VIEW ROW SWAP - READ BEFORE EDITING ============
# This map is the ICD s3.2 table with **row A and row B EXCHANGED**, and that
# is deliberate. It is NOT a transcription error. See the identical block in
# `power.py` for J3, which carries the full derivation.
#
# J4 is reverse-mounted on B.Cu facing down (ICD s7.3). Flipping a 2-row
# connector to the back swaps its ROWS while columns stay put, so carrier pin
# 2k+1 physically contacts this board's pin 2k+2. Measured on the real boards
# at P6, then verified pin-by-pin against boards/lumina-carrier's netlist.
#
# A literal transcription of ICD s3.2 on BOTH boards crossed 12 live contacts:
#     PWM0<->PWM1, PWM2<->PWM3, ENABLE<->FAULT, I2C_SDA<->ADC0,
#     ADC1<->ID_ADC, and the carrier's DSPI_SCK (a driven push-pull output)
#     landing on this board's GND.
# ENABLE<->FAULT is the dangerous one: FAULT is open-drain and must never be
# driven high, and it would have been wired to the carrier's ENABLE driver.
#
# NO GATE IN THIS PIPELINE CAN SEE THIS - erc, netlist_audit, DRC and verify
# all compare a board against ITSELF; the defect exists only BETWEEN boards.
#
# The NC positions move with the swap: they are the ICD's PWM4-7 and DSPI_*,
# which this board does not use, so which physical pin they land on is
# immaterial - but they must still occupy the MIRRORED slot so the live pins
# land correctly around them.
# ===========================================================================
J4_PINS = {
    "1": "PWM1",      "2": "PWM0",
    "3": "GND",       "4": "GND",
    "5": "PWM3",      "6": "PWM2",
    "7": "NC",        "8": "NC",        # PWM5 / PWM4 - no fifth channel
    "9": "GND",       "10": "GND",
    "11": "NC",       "12": "NC",       # PWM7 / PWM6
    "13": "NC",       "14": "GND",      # DSPI_SCK side
    "15": "NC",       "16": "NC",       # DSPI_MISO / DSPI_MOSI
    "17": "I2C_SCL",  "18": "NC",       # DSPI_CSn side
    "19": "ADC0",     "20": "I2C_SDA",
    "21": "ID_ADC",   "22": "ADC1",
    "23": "FAULT",    "24": "ENABLE",
}

# ------------------------------------------------------------- cross-sheet pins
# Shapes are THIS sheet's point of view. ADC0/ADC1 arrive from `thermal` and
# leave on J4, so they are inputs here even though sheets.md s2 calls them
# "out" (that column is the board-level source, `thermal`).
# `PWM0..3`, `/ENABLE`, `/ID_ADC`, `/I2C_SCL`, `/I2C_SDA` are sheet-local by
# sheets.md s2 and are deliberately ABSENT - they come out `/control/NAME`.
# DO NOT add PWM0..3 here to "fix" the constraints spelling: that mechanism was
# built and measured at the root stitch and costs 4 `label_dangling` ERC errors
# (see the module docstring). constraints.json now spells them `/control/PWMn`.
HIER_NETS = [
    ("FAULT", "bidirectional"),   # open drain, wire-OR'd; never driven high
    ("EN_OK", "output"),          # -> `power` branch-B gate pulldown (DNP)
    ("ADC0", "input"),            # thermal -> here -> J4-20
    ("ADC1", "input"),            # thermal -> here -> J4-21
    ("DRV_EN0", "output"), ("DRV_EN1", "output"),
    ("DRV_EN2", "output"), ("DRV_EN3", "output"),
    ("SHUNT0", "output"), ("SHUNT1", "output"),
    ("SHUNT2", "output"), ("SHUNT3", "output"),
]

# LCSC codes from parts/parts.json. Stamped on every purchased component:
# KiCad 10 DRC raises footprint_symbol_field_mismatch without them at the P5
# gate (LEARNINGS 2026-07-27).
LCSC = {
    "J4": "C92265",
    "U201": "C7666", "U202": "C485072", "U203": "C7998", "U204": "C133541",
    "R201": "C25803", "R202": "C25803", "R203": "C25803", "R204": "C25803",
    "R205": "C25803", "R207": "C25803",
    # R206: see the block comment in build() - parts.json's C25804 is a 10 k
    # placeholder that CR-1 has now superseded.
    "R206": "C23162",
    "R208": "C21189", "R209": "C25804",
    "R210": "C25803", "R211": "C25803", "R212": "C25803", "R213": "C25803",
    "R214": "C21189", "R215": "C21189", "R216": "C21189", "R217": "C21189",
    # R218-R221: the /DRV_ENn fail-safe pull-downs. C25804 = 10k 0603 1%,
    # already on the BOM (R209/R305/R325/R345/R365/R401/R403), so this adds
    # four pieces to an existing reel and no new line.
    "R218": "C25804", "R219": "C25804", "R220": "C25804", "R221": "C25804",
    "C201": "C14663", "C202": "C14663", "C203": "C14663", "C204": "C14663",
    "C205": "C14663",
    "C210": "C57112", "C211": "C57112", "C212": "C57112", "C213": "C57112",
    "D201": "C81598", "D202": "C81598", "D203": "C81598", "D204": "C81598",
}

# sheets.md s4 rule 1 / p4-wiring-notes s5.5: the converter-idle one-shot is
# in the netlist but must be excluded from the assembled set. parts.json
# carries the same dnp flag per refdes; this field is the schematic half.
DNP_REFS = ("U204",
            "R210", "R211", "R212", "R213",
            "C210", "C211", "C212", "C213",
            "D201", "D202", "D203", "D204")

# expect={} pin-name insurance. Values are SUBSTRINGS of the library pin name.
E_J4 = {str(n): str(n) for n in range(1, 25)}
E_U201 = {"1": "A", "2": "B", "3": "GND", "4": "Y", "5": "VCC"}
E_U202 = {"1": "1A", "2": "1B", "3": "1Y", "4": "2A", "5": "2B", "6": "2Y",
          "7": "GND", "8": "3Y", "9": "3A", "10": "3B", "11": "4Y",
          "12": "4A", "13": "4B", "14": "Vcc"}   # NB lowercase "cc" in the lib
E_U203 = {"1": "E0", "2": "E1", "3": "E2", "4": "VSS", "5": "SDA", "6": "SCL",
          "7": "WC", "8": "VCC"}                 # library renders pin 7 ~{WC}
E_U204 = {"1": "1A", "2": "1Y", "3": "2A", "4": "2Y", "5": "3A", "6": "3Y",
          "7": "GND", "8": "4Y", "9": "4A", "10": "5Y", "11": "5A",
          "12": "6Y", "13": "6A", "14": "VCC"}
E_DIODE = {"1": "K", "2": "A"}

# Kept to <= 145 characters each: at size 1.27 KiCad renders ~1.19 mm/char, so
# a longer line centred at NOTES_AT runs into the A3 title block (x ~ 293).
NOTES_AT = (190.5, 241.3)
NOTES_DY = 5.08
NOTES = (
    "NO I2C PULL-UPS ON THIS BOARD (ICD-01 s3.3): the carrier fits the only "
    "4.7 k pair. A second pair here is an ICD violation.",
    "/FAULT IS OPEN DRAIN AND MUST NEVER BE DRIVEN HIGH. Its only drivers are "
    "the thermal sheet's LM339LV open-drain outputs and R207.",
    "NO RC FILTER ON PWM0-3 OR /SHUNT0-3 (blocks.md B2): tau <= 14 ns if any "
    "network is fitted at all. The reflex 1 k + 100 pF is tau = 100 ns.",
    "PWM4-7 (J4 7/8/11/12) and DSPI_SCK/MOSI/MISO/CSn (J4 14/15/16/17) are "
    "DELIBERATE no-connects - rev A has four channels (decisions.md D2).",
    "R206 = 4.7 kOhm 1% REQUIRED: ICD-01 s3.4 code 2 (LUM-PAR-A), "
    "V_ID = 1.055 V. CR-1 CLOSED - sheets.md's 'VALUE TBD / P4 blocker' is "
    "STALE.",
    "U203 = M24C32 at 0x50: E0/E1/E2 strapped to VSS by R208. WC (pin 7) is "
    "ACTIVE HIGH write protect - R209 holds it at VSS so the part is "
    "writable.",
    "U204 + R210-R213 + C210-C213 + D201-D204 = converter-idle one-shot, "
    "DNP OPTION. IF IT IS EVER POPULATED, REMOVE R214-R217.",
    "J4 IS REVERSE-MOUNTED ON THE BOTTOM SIDE, FACING DOWN (ICD s7.3). Pin 1 "
    "needs a silkscreen triangle and MUST be checked in the MATED view.",
    "R218-R221 = 10k /DRV_ENn pull-downs, FITTED. NOT 100k: the TPS92515HV "
    "PWM pin sources 25 uA, so 100k rests at 2.5 V and latches the driver ON.",
)


def _hier_cluster(sh: schlib.Sheet, net: str, shape: str, at) -> None:
    """schlib.hier_pin's free-cluster variant, with the LOCAL label pointing
    AWAY from the hierarchical one.

    Identical electrical contract to Sheet.hier_pin(at=...): one wire, a
    local label of the net name on the start endpoint, the hierarchical
    label on the end endpoint, so the hier label joins the net by wire
    GEOMETRY and the local label merges the pin stubs by name. The only
    difference is the local label's text ANGLE: schlib emits both at
    rotation 0, so on a 2.54 mm stub the two text boxes always overlap -
    12 of 12 pins here, and benchlib.sch_metrics counts exactly those
    label-vs-label pairs (LEARNINGS 2026-08-06 [bench][schematic]). Turning
    the local label 180 deg sends its text left into free area and takes
    the sheet to 0 label collisions.
    """
    x, y = at[:2]
    schlib.assert_on_grid((x, y), f"hier pin {net}")
    end = (round(x + schlib.STUB, 4), y)
    seg = sh._add_wire((x, y), end)
    sh._assert_label_clear((x, y), net, own=seg)
    sh._assert_label_clear(end, net, own=seg)
    sh.sch.add_label(net, position=(x, y), rotation=180.0)
    sh.sch.add_hierarchical_label(net, position=end, shape=shape)
    sh.hier_pins[net] = shape


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "control",
        title="LUM-PAR-A: control - ENABLE gating, shunt logic, ID + EEPROM",
        paper="A3", date="2026-08-07", company="ai-ee", pwr_base=200)

    # ================================================ J4 - SIGNAL socket, 2x12
    # This symbol's pin NAMES are its pin NUMBERS, so expect= also proves pad
    # N exists for every N.
    sh.add_component(S_J4, "J4", V_J4, at=(63.5, 101.6), footprint=F_J4,
                     expect=E_J4)
    sh.wire_pins("J4", J4_PINS)

    # ============================ connector-end pull-downs and the ID divider
    # R201: the ICD s8.2 MANDATORY 100 k ENABLE pull-down. With the carrier's
    # own 10 k the parallel pair is 9.09 k and the carrier's push-pull GPIO
    # sources 0.363 mA. Nothing may be added in series ahead of it.
    # R202-R205: an unpowered or undriven carrier must not float a NAND input
    # high (blocks.md B2). Four resistors; do not skip them.
    for ref, net, y in (("R201", "ENABLE", 63.5),
                        ("R202", "PWM0", 76.2),
                        ("R203", "PWM1", 88.9),
                        ("R204", "PWM2", 101.6),
                        ("R205", "PWM3", 114.3)):
        sh.add_component(S_R_100K, ref, V_100K, at=(127.0, y),
                         footprint=F_R0603)
        sh.wire_pins(ref, {"1": net, "2": "GND"})

    # R206 - ID_ADC divider BOTTOM leg, ICD-01 s3.4 code 2 = 4.7 kOhm 1 %.
    #
    # LIBRARY / BOM NOTE, DELIBERATE AND REPORTED RATHER THAN SILENT:
    # lib/aiee.kicad_sym holds no 4.7 k 0603 symbol (lib_pull was driven from
    # a parts.json line that still says "VALUE TBD"), and this agent must not
    # run lib_pull - four sibling sheet agents are live. parts.json's own role
    # text says its C25804 "IS A 0603 FOOTPRINT PLACEHOLDER ONLY ... it must
    # be re-issued when the carrier owner allocates the code". The carrier
    # owner HAS allocated it, so the placeholder symbol is used exactly as
    # documented - as a footprint carrier - while the VALUE and the LCSC field
    # carry the real part (C23162 = Uniroyal 0603WAF4701T5E 4.7 k 1 % 0603,
    # the line the sibling LUM-CAR-A run uses for R130/R131). bom_cpl lets a
    # parts.json entry override the board field, so re-issuing that line is
    # the authoritative fix and this stamp is a correct default meanwhile.
    sh.add_component(S_R_10K, "R206", V_R206, at=(127.0, 127.0),
                     footprint=F_R0603)
    sh.wire_pins("R206", {"1": "ID_ADC", "2": "GND"})

    # C204 - ID_ADC settling cap (blocks.md B5). NOT a decoupler.
    sh.add_component(S_C_100N, "C204", V_100N, at=(127.0, 139.7),
                     footprint=F_C0603)
    sh.wire_pins("C204", {"1": "ID_ADC", "2": "GND"})

    # R207 - the local /FAULT pull-up. Open-drain wire-OR: the carrier fits
    # 10 k as well, so unmated the node is still defined here.
    sh.add_component(S_R_100K, "R207", V_100K, at=(127.0, 152.4),
                     footprint=F_R0603)
    sh.wire_pins("R207", {"1": "FAULT", "2": "+3V3"})

    # ===================================== U201 - /EN_OK = ENABLE AND FAULT
    # The single node through which BOTH the ICD's ENABLE and the thermal
    # FAULT kill every output stage: combinational, never latched (B2).
    sh.place_ic_with_decoupling(
        "U201", S_U201, V_U201, at=(203.2, 63.5),
        pins={"1": "ENABLE", "2": "FAULT", "3": "GND", "4": "EN_OK",
              "5": "+3V3"},
        footprint=F_SOT235, expect=E_U201,
        decoupling=[{"cap": "C201", "pin": "5", "rail": "+3V3",
                     "value": V_100N, "lib_id": S_C_100N,
                     "footprint": F_C0603}],
        caps_at=(266.7, 63.5))

    # ============================ U202 - /SHUNTn = NOT(PWMn AND /EN_OK) x4
    # NAND and not AND, because the shunt FET is ON when the LED is OFF.
    # One SO-14 covers all four channels. Gate map is the D-package DIAGRAM,
    # not the sec 6 table (erratum 1 in the module docstring):
    #   gate 1: 1A=1  1B=2  1Y=3      gate 3: 3A=9  3B=10 3Y=8
    #   gate 2: 2A=4  2B=5  2Y=6      gate 4: 4A=12 4B=13 4Y=11
    sh.place_ic_with_decoupling(
        "U202", S_U202, V_U202, at=(203.2, 114.3),
        pins={"1": "PWM0", "2": "EN_OK", "3": "SHUNT0",
              "4": "PWM1", "5": "EN_OK", "6": "SHUNT1",
              "7": "GND",
              "9": "PWM2", "10": "EN_OK", "8": "SHUNT2",
              "12": "PWM3", "13": "EN_OK", "11": "SHUNT3",
              "14": "+3V3"},
        footprint=F_SOIC14, expect=E_U202,
        decoupling=[{"cap": "C202", "pin": "14", "rail": "+3V3",
                     "value": V_100N, "lib_id": S_C_100N,
                     "footprint": F_C0603}],
        caps_at=(266.7, 114.3))

    # ============================================ U203 - M24C32 EEPROM @ 0x50
    # NO pull-ups on SDA/SCL here: the carrier owns them (ICD s3.3). The
    # datasheet's "a pull up resistor must be connected from SDA to VCC" is
    # satisfied on the CARRIER side of J4, not on this board.
    # E0/E1/E2 share one node so a single 0 R (R208) straps all three, which
    # is what parts.json allocates ("R208 = EEPROM A0-A2 strap to GND").
    sh.place_ic_with_decoupling(
        "U203", S_U203, V_U203, at=(203.2, 165.1),
        pins={"1": "EE_ADDR", "2": "EE_ADDR", "3": "EE_ADDR", "4": "GND",
              "5": "I2C_SDA", "6": "I2C_SCL", "7": "EE_WC", "8": "+3V3"},
        footprint=F_SOIC8, expect=E_U203,
        decoupling=[{"cap": "C203", "pin": "8", "rail": "+3V3",
                     "value": V_100N, "lib_id": S_C_100N,
                     "footprint": F_C0603}],
        caps_at=(266.7, 165.1))

    sh.add_component(S_R_0R, "R208", V_0R, at=(139.7, 165.1),
                     footprint=F_R0603)
    sh.wire_pins("R208", {"1": "EE_ADDR", "2": "GND"})
    # WC is ACTIVE HIGH write protect - held at VSS so writes are allowed.
    sh.add_component(S_R_10K, "R209", V_10K, at=(139.7, 177.8),
                     footprint=F_R0603)
    sh.wire_pins("R209", {"1": "EE_WC", "2": "GND"})

    # =================================== R214-R217 - /EN_OK -> /DRV_ENn links
    # FITTED BY DEFAULT: they are the strap that selects the default
    # configuration ("driver PWM/EN pins <- /EN_OK, all four in parallel",
    # blocks.md B2). If U204 is ever populated, all four MUST be removed.
    for i in range(4):
        ref = f"R{214 + i}"
        sh.add_component(S_R_0R, ref, V_0R, at=(317.5, 88.9 + i * 12.7),
                         footprint=F_R0603)
        sh.wire_pins(ref, {"1": "EN_OK", "2": f"DRV_EN{i}"})

    # ============================ R218-R221 - /DRV_ENn fail-safe pull-downs
    # THE VALUE IS 10 k AND IT IS LOAD-BEARING - see the R218-R221 bullet in
    # the module docstring for the full arithmetic before touching it. Short
    # form: the TPS92515HV PWM/enable pin sources up to 25 uA of its own UVLO
    # hysteresis current above threshold, so a pull-down rests at I x R and
    # must stay under the worst-case 0.80 V falling threshold. 100 k (this
    # board's value for every OTHER pull-down) rests at 2.5 V and latches the
    # driver ON; 10 k rests at 0.325 V worst case with the whole node counted.
    #
    # They hang off `/DRV_ENn`, DOWNSTREAM of the R214-R217 links, so they
    # survive the U204 one-shot option that removes those links. Same reason
    # R202-R205 sit on the connector side of their gates: put the fail-safe
    # where the thing being made safe is, not where the driver happens to be.
    #
    # P6 obligation, same class as R201's "connector end": place each one AT
    # THE DRIVER, next to the U3x1 PWM pin it protects, not next to its link.
    for i in range(4):
        ref = f"R{218 + i}"
        sh.add_component(S_R_10K, ref, V_10K, at=(317.5, 139.7 + i * 12.7),
                         footprint=F_R0603)
        sh.wire_pins(ref, {"1": f"DRV_EN{i}", "2": "GND"})

    # ============================== converter-idle one-shot - DNP option set
    # See the module docstring for the topology and why /SHUNTn is the source.
    # D20n: pin 2 = A (anode) on IDLEn, pin 1 = K (cathode) on /SHUNTn, i.e.
    # the diode is ACROSS R21n and its fast direction DISCHARGES C21n when
    # /SHUNTn goes low. Reversing it breaks retriggering outright.
    for i in range(4):
        y = 190.5 + i * 12.7
        sh.add_component(S_R_100K, f"R{210 + i}", V_100K, at=(63.5, y),
                         footprint=F_R0603)
        sh.wire_pins(f"R{210 + i}", {"1": f"SHUNT{i}", "2": f"IDLE{i}"})
        sh.add_component(S_D_SW, f"D{201 + i}", V_D, at=(127.0, y),
                         footprint=F_SOD123F, expect=E_DIODE)
        sh.wire_pins(f"D{201 + i}", {"1": f"SHUNT{i}", "2": f"IDLE{i}"})
        sh.add_component(S_C_10N, f"C{210 + i}", V_10N, at=(190.5, y),
                         footprint=F_C0603)
        sh.wire_pins(f"C{210 + i}", {"1": f"IDLE{i}", "2": "GND"})

    # U204 - hex Schmitt inverter, 4 of 6 gates used.
    # Gates 5 and 6 are SPARE: their inputs are tied to GND because an unused
    # LVC input must never float (parts/C133541 layout notes, same rule as the
    # LVC00A); their outputs are explicit no-connects.
    sh.place_ic_with_decoupling(
        "U204", S_U204, V_U204, at=(266.7, 209.55),
        pins={"1": "IDLE0", "2": "DRV_EN0",
              "3": "IDLE1", "4": "DRV_EN1",
              "5": "IDLE2", "6": "DRV_EN2",
              "9": "IDLE3", "8": "DRV_EN3",
              "11": "GND", "10": "NC",     # spare gate 5
              "13": "GND", "12": "NC",     # spare gate 6
              "7": "GND", "14": "+3V3"},
        footprint=F_SOIC14, expect=E_U204,
        decoupling=[{"cap": "C205", "pin": "14", "rail": "+3V3",
                     "value": V_100N, "lib_id": S_C_100N,
                     "footprint": F_C0603}],
        caps_at=(330.2, 209.55))

    # ======================================================= rails (global)
    # Power SYMBOLS make "+3V3" and "GND" global and BARE across the whole
    # hierarchy, so they need no sheet pin. NO PWR_FLAG here - the rails are
    # flagged once, on `power` (sheets.md s2). power_symbol_at_pin takes the
    # symbol VALUE (= the exported net name) from the pin's already-wired net,
    # so a name divergence cannot exist.
    for ref, pad, sym in (("U201", "5", "power:+3V3"),
                          ("U202", "14", "power:+3V3"),
                          ("U203", "8", "power:+3V3"),
                          ("U204", "14", "power:+3V3"),
                          ("U201", "3", "power:GND"),
                          ("U202", "7", "power:GND"),
                          ("U203", "4", "power:GND"),
                          ("U204", "7", "power:GND")):
        sh.power_symbol_at_pin(ref, pad, sym)

    # ============================================ hierarchical sheet pins x12
    # Free-cluster variant: a local label of the net name at one end and the
    # hierarchical label at the other, joined by wire GEOMETRY rather than by
    # label name-merging alone. See _hier_cluster for the one cosmetic
    # deviation from schlib.hier_pin.
    for i, (net, shape) in enumerate(HIER_NETS):
        _hier_cluster(sh, net, shape, at=(355.6, 50.8 + i * 10.16))

    # ================================================ schematic notes (graphic)
    # add_text is CENTRE-justified, so x is the middle of the string.
    for i, note in enumerate(NOTES):
        sh.sch.add_text(note, position=(NOTES_AT[0], NOTES_AT[1] + i * NOTES_DY),
                        size=1.27)

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    for ref in DNP_REFS:
        sh.sch.components.get(ref).set_property("Variant", "DNP")
    return sh


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(BOARD / "kicad"),
                    help="directory to write control.kicad_sch into")
    ap.add_argument("--project", action="store_true",
                    help="also write control.kicad_pro (standalone ERC only; "
                         "the root generator owns the real project file)")
    args = ap.parse_args(argv)
    try:
        sh = build()
        path = sh.save(args.out, project=args.project)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.control", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.control", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "bom_components": len(LCSC),
        "dnp": sorted(DNP_REFS),
        "hier_pins": [n for n, _ in HIER_NETS],
        "internal_nets": sorted(["PWM0", "PWM1", "PWM2", "PWM3", "ENABLE",
                                 "ID_ADC", "I2C_SCL", "I2C_SDA", "EE_ADDR",
                                 "EE_WC", "IDLE0", "IDLE1", "IDLE2", "IDLE3"]),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
