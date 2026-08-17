"""Generator for the bb-mcu root schematic - ONE FLAT SHEET (sheets.md s1).

The schematic SOURCE is this Python file; `../bb-mcu.kicad_sch`, the
`.kicad_pro` and `../decoupling.json` are BUILD OUTPUT. Rebuild:

    .venv/Scripts/python boards/bb-mcu/kicad/gen/root.py

Grounding (SPEC section 5 - nothing here comes from family memory):
  - U1 pin numbers/names: parts/C89040.json `pinout` ONLY (ST DocID024849
    Rev 3, Table 11 / Figure 8, TSSOP20 column). `expect=` re-checks all 20
    against the pulled symbol at build time.
  - J1 / J2 / J3 pin numbering: parts/C8465.json, parts/C32713271.json.
  - Component set + values: parts/parts.json (P3), which is the P2 BOM.
  - Net names: architecture/sheets.md s2.
  - Header pin orders: J2 `GND SWCLK 3V3 SWDIO NRST` is sheets.md s3, RULED
    at P1 and unchanged. J3 is `IO1 IO2 IO3 IO4 GND` - a P4-REVIEW AMENDMENT
    that supersedes sheets.md s3's `IO1 IO2 GND IO3 IO4` (see J3 below).

TWO P4-REVIEW AMENDMENTS are built in here and are NOT yet reflected in
architecture/sheets.md or architecture/constraints.json - both are owner
rulings recorded in state.json, and this file is the amended source:
  1. C5, a 100 nF NRST-to-GND capacitor, is ADDED (sheets.md s3's part
     table and blocks.md s2's exclusion list both still say no NRST cap).
  2. J3's ruled order MOVES GND from the centre to position 5.

Canonical nets (sheets.md s2): `+3V3` and `GND` are POWER SYMBOLS, so they
export BARE; every signal is a root-sheet LOCAL LABEL, which exports with one
leading slash (`/SWDIO /SWCLK /NRST /BOOT0 /IO1../IO4`). The label TEXT here
carries no slash - KiCad adds it on export.

Deliberately absent, each a recorded ruling (blocks.md s2, constraints.json
`notes`) - do not "fix" them back in:
  - no VDDA filter: VDDA is tied straight to `+3V3`. Figure 12 puts the
    internal RC + PLL on VDDA and this board has no crystal, so VDDA IS the
    clock supply; Table 21 also requires VDDA >= VDD, which any series
    element can only violate.
  - no series resistors and no external pulls on SWDIO/SWCLK/NRST (the
    STM32F0's internal 25/40/55 k pulls are live at reset - DS Table 11
    footnote 7).
  - the NRST capacitor is NO LONGER absent: see C5 below. The earlier "no
    NRST cap" ruling read AN4325's Optional-components table ("for RESET
    button") and missed DS Figure 21 note 1, which recommends the cap
    unconditionally as PARASITIC-RESET protection - a different
    justification, and one this board's unshielded NRST flying lead is the
    textbook exposure for.
  - no `"role": "reg_input"` on any cap: that flag exists for a SWITCHING
    regulator's VIN pin and there is no regulator anywhere on this board.

H1-H4 (M3 clearance holes) are footprint-only mechanical items with no net
and no LCSC part - they enter at P5/P6 via `board_init --mounting-holes`,
not here, and their count is a P6 call (sheets.md s1).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/bb-mcu
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402
import kicad_sch_api as ksa  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table. Register the pulled project lib BEFORE any add - or
# save() silently guts the lib_symbols block (LEARNINGS 2026-08-06).
LIB = BOARD / "lib" / "aiee.kicad_sym"
ksa.get_symbol_cache().add_library_path(LIB)

FP = "aiee"   # footprint lib nickname (kicad/fp-lib-table)

# ---- symbols (lib/aiee.kicad_sym) and footprints (lib/aiee.pretty) --------
S_U1 = "aiee:STM32F030F4P6TR"
S_C1 = "aiee:CC0603KRX7R9BB104"       # 100 nF
S_C2 = "aiee:CGA0603X7R475K160JT"     # 4.7 uF
S_C3 = "aiee:CC0603KRX7R8BB103"       # 10 nF
S_C4 = "aiee:CC0603KRX7R7BB105"       # 1 uF
S_R1 = "aiee:0603WAF1002T5E"          # 10 k
S_J1 = "aiee:WJ500V-5.08-2P-14-00A"   # 2P 5.08 mm screw terminal
S_JH = "aiee:HXPZ2.54-1X5PZZ"         # 1x5 0.1 in header (J2 and J3)

F_U1 = f"{FP}:SOP-20_L6.5-W4.4-P0.65-LS6.4-BL"
F_C = f"{FP}:C0603"
F_R = f"{FP}:R0603"
F_J1 = f"{FP}:CONN-TH_2P-P5.00_WJ500V-5.08-2P"
F_JH = f"{FP}:HDR-TH_5P-P2.54-V-M"

# ---- values: parts/parts.json, verbatim ----------------------------------
V_U1 = "STM32F030F4P6TR"
V_C1 = "100nF 50V X7R"
V_C2 = "4.7uF 16V X7R"
V_C3 = "10nF 25V X7R"
V_C4 = "1uF 16V X7R"
V_R1 = "10k"
V_J1 = "2P 5.08mm screw terminal THT"
V_JH = "1x5 2.54mm male THT"

# ---- LCSC codes (parts/parts.json); bom_cpl reads the "LCSC" field -------
LCSC = {
    "U1": "C89040", "C1": "C14663", "C2": "C22399629", "C3": "C327204",
    "C4": "C106248", "C5": "C14663",   # C5 is the SAME part as C1
    "R1": "C25804", "J1": "C8465",
    "J2": "C32713271", "J3": "C32713271",
}

# U1 STM32F030F4P6TR TSSOP-20: pad -> net. Ground truth parts/C89040.json.
# "NC" = explicit no-connect flag; the one-line reason follows each.
U1_PINS = {
    "1": "BOOT0",   # -> R1 10k -> GND. No internal pull, hardware-sampled
                    #    on the 4th SYSCLK edge after reset (DS Table 11
                    #    type "B" legend), so the strap is REQUIRED.
    "2": "NC",      # PF0-OSC_IN: no crystal (internal RC); tie-off is
                    #    RECOMMENDED-only EMC guidance (AN4325 5.6), excluded
                    #    by the scope tier.
    "3": "NC",      # PF1-OSC_OUT: same, no crystal.
    "4": "NRST",    # -> J2.5, plus C5 100nF to GND (DS Figure 21 note 1
                    #    parasitic-reset protection). Permanent internal
                    #    pull-up 25/40/55 k, so NO external pull-up.
    "5": "+3V3",    # VDDA, tied DIRECTLY to VDD - no ferrite/bead/resistor.
                    #    C3 10nF + C4 1uF return to VSS (no VSSA on TSSOP20).
    "6": "IO1",     # PA0 -> J3.1
    "7": "IO2",     # PA1 -> J3.2
    "8": "IO3",     # PA2 -> J3.3
    "9": "IO4",     # PA3 -> J3.4
    "10": "NC",     # PA4: spare GPIO, brief asks for four only (blocks.md s4)
    "11": "NC",     # PA5: spare GPIO
    "12": "NC",     # PA6: spare GPIO
    "13": "NC",     # PA7: spare GPIO
    "14": "NC",     # PB1: spare GPIO
    "15": "GND",    # VSS - the only ground pin, and the VDDA return too
    "16": "+3V3",   # VDD - C1 100nF + C2 4.7uF (DS Figure 12, REQUIRED)
    "17": "NC",     # PA9: spare GPIO
    "18": "NC",     # PA10: spare GPIO
    "19": "SWDIO",  # PA13 -> J2.4. SWD alt-fn at reset, internal pull-UP.
    "20": "SWCLK",  # PA14 -> J2.2. SWD alt-fn at reset, internal pull-DOWN.
}

# Every pin name re-checked against the pulled symbol at build time.
U1_EXPECT = {
    "1": "BOOT0", "2": "PF0", "3": "PF1", "4": "NRST", "5": "VDDA",
    "6": "PA0", "7": "PA1", "8": "PA2", "9": "PA3", "10": "PA4",
    "11": "PA5", "12": "PA6", "13": "PA7", "14": "PB1", "15": "VSS",
    "16": "VDD", "17": "PA9", "18": "PA10", "19": "PA13", "20": "PA14",
}


def _wire_pin_out(sh: schlib.Sheet, ref: str, pad: str, net: str,
                  extra: float = 0.0) -> None:
    """schlib.wire_pin with a LONGER outward stub (STUB + `extra`, still on
    the 1.27 mm grid). Electrically identical - stub plus local label, same
    foreign-wire label guard - and the only reason it exists is drawing
    legibility: schlib's stub length is a module constant, so two pins closer
    together than the label text is wide get their labels printed on top of
    each other and there is no public knob for it."""
    p = sh.pin_pos(ref, pad)
    schlib.assert_on_grid(p, f"{ref} pin {pad}")
    d = sh._pin_out_dir(ref, pad)
    reach = schlib.STUB + extra
    end = (round(p[0] + d[0] * reach, 4), round(p[1] + d[1] * reach, 4))
    schlib.assert_on_grid(end, f"{ref} pin {pad} label")
    seg = sh._add_wire(p, end)
    sh._assert_label_clear(end, net, own=seg)
    sh.sch.add_label(net, position=end)
    sh._pin_nets[(ref, pad)] = net


def build() -> schlib.Sheet:
    sh = schlib.Sheet("bb-mcu",
                      title="bb-mcu: STM32F030F4P6TR minimum system",
                      paper="A3", date="2026-08-16", company="ai-ee",
                      pwr_base=1)

    # ---- U1 + its four REQUIRED decouplers -------------------------------
    # DS Figure 12 caution: each supply pair "must be decoupled with
    # filtering ceramic capacitors ... as close as possible to ... the
    # appropriate pins". TSSOP-20 bonds exactly ONE VDD/VSS pair, so the
    # per-pair set applies once: C1 100nF + C2 4.7uF at VDD(16), and the
    # VDDA branch C3 10nF + C4 1uF at VDDA(5). The explicit hf/bulk classes
    # are constraints.json's own DECOUPLING.JSON note, not the value-derived
    # default: they hold the two HF ceramics to the 5/7.5 mm class limit.
    # Rail/gnd wiring labels are "+3V3"/"GND" and BOTH export bare (power
    # symbols), so the recorded metadata needs no rail_net/gnd_net override.
    sh.place_ic_with_decoupling(
        "U1", S_U1, V_U1,
        at=(203.2, 127.0), pins=U1_PINS,
        footprint=F_U1, expect=U1_EXPECT,
        decoupling=[
            {"cap": "C1", "pin": "16", "rail": "+3V3", "value": V_C1,
             "class": "hf", "lib_id": S_C1, "footprint": F_C},
            {"cap": "C2", "pin": "16", "rail": "+3V3", "value": V_C2,
             "class": "bulk", "lib_id": S_C2, "footprint": F_C},
            {"cap": "C3", "pin": "5", "rail": "+3V3", "value": V_C3,
             "class": "hf", "lib_id": S_C3, "footprint": F_C},
            {"cap": "C4", "pin": "5", "rail": "+3V3", "value": V_C4,
             "class": "bulk", "lib_id": S_C4, "footprint": F_C},
        ],
        caps_at=(152.4, 167.64), caps_dx=25.4)

    # ---- R1: BOOT0 strap, 10k to GND (AN4325 R2's value, no switch) ------
    sh.add_component(S_R1, "R1", V_R1, at=(152.4, 190.5), footprint=F_R)
    sh.wire_pins("R1", {"1": "BOOT0", "2": "GND"})

    # ---- C5: NRST parasitic-reset protection, 100 nF to GND -------------
    # DS Figure 21 note 1 recommends this cap unconditionally to protect
    # against PARASITIC resets - not (as AN4325's optional-components table
    # frames it) to debounce a reset button. This board routes NRST out to
    # an unshielded flying lead on J2.5, which is exactly that exposure, and
    # requirements.md s2 point 5 scoped datasheet support on the NRST /
    # boot-mode pins as in-scope from the start. Same physical part as C1
    # (C14663), so the BOM gains a quantity, not a line.
    # Deliberately placed with add_component, NOT through
    # place_ic_with_decoupling: C5 is a signal-net RC, not a supply
    # decoupler, and must NOT enter decoupling.json - that file stays at
    # exactly 4 associations (C1/C2 on U1.16, C3/C4 on U1.5). Feeding it to
    # the helper would also be rejected outright, since pins["4"] is "NRST"
    # and no decoupling entry can name a rail the pin is not wired to.
    sh.add_component(S_C1, "C5", V_C1, at=(190.5, 190.5), footprint=F_C)
    sh.wire_pins("C5", {"1": "NRST", "2": "GND"})

    # ---- J1: power in. 1 = +3V3, 2 = GND (silk +/- is P6/P7's job) -------
    # Both pins leave the body downward only 2.54 mm apart, and a local
    # label prints HORIZONTALLY from its anchor whatever the stub direction,
    # so two equal-length stubs put "+3V3" and "GND" on top of each other
    # (measured: the export reads "+3VGNID"). Stagger the second run by
    # 5.08 mm - J1's polarity marking is this board's ONLY defence against a
    # swapped supply, so its two nets must be readable on the drawing.
    sh.add_component(S_J1, "J1", V_J1, at=(76.2, 101.6), footprint=F_J1)
    _wire_pin_out(sh, "J1", "1", "+3V3")
    _wire_pin_out(sh, "J1", "2", "GND", extra=5.08)

    # ---- J2: SWD header. RULED order GND / SWCLK / 3V3 / SWDIO / NRST ----
    # 3V3 at the CENTRE is the unique arrangement in which reversing an
    # unkeyed 5-way shell (i -> 6-i) lands the probe's high-Z VTref INPUT on
    # the rail instead of a probe OUTPUT (blocks.md s2). Do not re-order.
    # RE-EXAMINED at P4 review and KEPT: a one-position slip on this header
    # is real, but every alternative is worse - moving the rail to an END
    # lets a slip land the probe's GND wire on it, a hard short instead of a
    # current-limited driver contact. J3 moved; J2 stays.
    # The 3V3 pin is a SENSE input and takes NO series element (UM08001 13.5).
    sh.add_component(S_JH, "J2", V_JH, at=(299.72, 127.0), footprint=F_JH)
    sh.wire_pins("J2", {"1": "GND", "2": "SWCLK", "3": "+3V3",
                        "4": "SWDIO", "5": "NRST"})

    # ---- J3: GPIO header. AMENDED order IO1 / IO2 / IO3 / IO4 / GND ------
    # P4-review amendment, SUPERSEDING sheets.md s3's centre-GND ruling.
    # J2 and J3 are the SAME unkeyed 5-position part, so a cable built for
    # one physically mates with the other. GND at J3's centre put it
    # opposite +3V3 at J2's centre, so a cross-plug shorted the rail through
    # the cable's own return - a hard short, the worst outcome on this
    # board. With GND at an end the worst cross-plug outcome is a GPIO
    # contacting rail or ground, current-limited by the pin's own driver.
    # That beats the return-distance and self-mapping-centre arguments the
    # original ruling was built on, neither of which is a damage mode.
    # PA13/PA14 are still NOT routed here - J2 needs them as SWD permanently.
    sh.add_component(S_JH, "J3", V_JH, at=(299.72, 190.5), footprint=F_JH)
    sh.wire_pins("J3", {"1": "IO1", "2": "IO2", "3": "IO3",
                        "4": "IO4", "5": "GND"})

    # ---- rails -----------------------------------------------------------
    # Power symbols force the BARE global names (+3V3, GND) over the
    # coincident local labels. Nothing on this board DRIVES either rail -
    # both arrive from an external 3.3 V source through J1, whose pins are
    # passive - so both carry a PWR_FLAG or ERC raises pin_not_driven on
    # U1's power_in pins (5, 15, 16).
    sh.power_flag("+3V3", at=(63.5, 215.9), sym="power:+3V3", flag=True)
    sh.power_flag("GND", at=(63.5, 228.6), sym="power:GND", flag=True)

    # ---- LCSC fields (bom_cpl.py keys on the property literally named
    #      "LCSC"; the pulled symbols' own "LCSC Part" does not match) -----
    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    return sh


def _assert_lib_symbols_intact(path: Path) -> None:
    """ksa.save() re-serialises lib_symbols from its GLOBAL cache and drops
    anything it cannot resolve - silently, exit 0 (LEARNINGS 2026-08-06).
    Every project symbol this sheet places must survive into the file."""
    text = path.read_text(encoding="utf-8")
    embedded = set(re.findall(r'\(symbol "(aiee:[^"]+)"', text))
    want = {S_U1, S_C1, S_C2, S_C3, S_C4, S_R1, S_J1, S_JH}
    missing = sorted(want - embedded)
    if missing:
        raise ValueError(f"lib_symbols gutted on save: {missing} absent from "
                         f"{path.name}")


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]   # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        _assert_lib_symbols_intact(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.bb-mcu", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.bb-mcu", "status": "pass",
        "files": [str(sch), str(out_dir / "bb-mcu.kicad_pro"), str(meta)],
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
