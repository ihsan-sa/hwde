"""LUM-PAR-A `thermal` sheet: NTC dividers, window comparator, FAULT driver.

Refdes range (architecture/sheets.md s1.4): 400-499, `#PWR` base 400.
Block B4 - the board's ONLY firmware-independent protection (PAR-REQ-12).

WHAT THIS SHEET IS
------------------
Two 10 k / NTC dividers feed one quad OPEN-DRAIN comparator (U401) whose four
outputs wire-OR onto `FAULT`.  `FAULT` low pulls `/EN_OK` low through U201 on
the `control` sheet, so every driver stage dies through exactly the node
ENABLE uses.  The same two divider nodes also leave the board as `ADC0` /
`ADC1` so the carrier can roll duty back long before FAULT asserts.

  emitter hot      (module RT_LED, 90 C target)   -> CMP on OUT pin 1
  emitter OPEN     (implausibly cold / broken harness) -> CMP on OUT pin 2
  emitter SHORT    (rail-pinned low)              -> CMP on OUT pin 13
  board hot        (RT401, 110 C target)          -> CMP on OUT pin 14

The open+short pair is the point of the whole block (D-T17, E-10): in either
divider orientation a broken harness conductor reads as *cold*, so a single
over-temperature threshold is FAIL-DANGEROUS against the most likely fault in
an off-board module.  The window converts it to fail-safe.

GROUND TRUTH (SPEC s5 - no wiring, no threshold, no value from memory)
----------------------------------------------------------------------
parts/C3658338.json (LM339LV extract), parts/parts.json (every value and
LCSC below), architecture/p4-wiring-notes.md s3 (BINDING errata), and the
library pin table printed by
  schlib.py --pins "aiee:LM339LVPWR" --lib ../lib/aiee.kicad_sym

  * DATASHEET ERRATUM - WIRE BY PIN NUMBER, NEVER BY CHANNEL NAME.  LM339LV
    Figure 5-3 and Table 5.2 transpose the OUT labels (Table 5.2 footnote 1
    admits it).  The pin-NUMBER groupings are identical in both and are what
    this file uses:
        OUT 1  <-> IN- 6  / IN+ 7
        OUT 2  <-> IN- 4  / IN+ 5
        OUT 13 <-> IN- 10 / IN+ 11
        OUT 14 <-> IN- 8  / IN+ 9
    The pulled symbol agrees pin-for-pin (its names follow the Figure 5-3
    convention, so pin 13 prints "OUT4" and pin 14 prints "OUT3" - that is
    the naming collision, not a wiring difference).  `expect=` below pins
    the symbol's own names so a library refresh cannot silently re-map them.
  * Outputs are OPEN-DRAIN, sinking only, explicitly wire-OR-able (four
    independent datasheet statements).  THE `FAULT` ARCHITECTURE IS SAFE.
  * Inputs are rail-to-rail (GND-100 mV to V+ +100 mV), which is exactly what
    disqualifies the classic LM339: the open/cold threshold sits at 3.03 V on
    a 3.3 V rail, above LM339's V+ - 1.5 V input common-mode ceiling.
  * NO INTERNAL HYSTERESIS.  See "HYSTERESIS" below - the answer is not the
    obvious one and three of the four channels cannot have reference-side
    hysteresis at all.
  * POR: the outputs are Hi-Z for up to 30 us after V+ crosses 1.5 V, so
    `FAULT` reads NO-FAULT for that window on every power-up.  This is a
    documented device characteristic, NOT a defect, and it is deliberately
    NOT fixed in hardware (p4-wiring-notes s3).  It is harmless here because
    /EN_OK also needs ENABLE from the carrier, which cannot be asserted
    30 us into the daughter's own power-up.
  * Total sink across all four outputs must stay < 200 mA.  Worst case here
    is the FAULT pull-ups: 3.3 V / (10 k carrier || 100 k R207) = 0.36 mA.

DIVIDER ORIENTATION - SETTLED, NOT ASSUMED
------------------------------------------
Both NTCs are the BOTTOM leg:  +3V3 -> 10 k -> node -> NTC -> GND, so
    V(node) = 3.3 x Rntc / (10k + Rntc)     hot -> LOW, cold -> HIGH
    broken harness / open NTC -> 3.30 V      shorted NTC -> 0.00 V
Two independent confirmations:
  1. J5 carries a "dedicated NTC sense return" joined to GND at the
     comparator reference point (blocks.md B6), so RT_LED's far end is GND.
  2. Only this orientation lets the R405-R408 ladder produce TWO distinct hot
     thresholds (89.7 C and 110.8 C).  Inverted, the same chain yields
     91.0 C / -20.1 C / -29.4 C - one hot tap, and the board-hot threshold
     becomes unreachable.  blocks.md B4's "CMP3 ... above ~3.1 V" is the
     INVERTED-orientation number for that row and does not apply; in this
     orientation "above ~3.1 V" is the OPEN case, which CMP on pin 2 owns.

REFERENCE LADDER - the arithmetic a reviewer must be able to check
------------------------------------------------------------------
Ratiometric off `+3V3` (so every threshold tracks the carrier's ADC
reference), chain +3V3 -> R405 2.7k -> A -> R406 27k -> B -> R407 1.2k ->
C -> R408 1.6k -> GND.  Sum 32.5 k, 101.5 uA - inside power_tree s4's
0.10 mA allowance.  With RT(T) = 10k x exp(3950 x (1/T - 1/298.15)):

  tap A = 3.3 x 29.8/32.5 = 3.0258 V  -> Rntc 110.5k -> -20.8 C  OPEN/COLD
  tap B = 3.3 x  2.8/32.5 = 0.2843 V  -> Rntc  941.6 ->  89.7 C  EMITTER HOT
  tap C = 3.3 x  1.6/32.5 = 0.1625 V  -> Rntc  517.8 -> 110.8 C  HOT no.2

tap C is deliberately shared by two channels on two DIFFERENT sensors:
board-hot (110 C target on RT401) and emitter-rail-pinned-low (a shorted
RT_LED or a sense-to-return short reads 0 V, far below this tap).
Sensitivity at the emitter hot tap is -7.72 mV/K.

HYSTERESIS - WHY IT IS WIRED THE WAY IT IS.  DO NOT "TIDY" THIS.
-----------------------------------------------------------------
A comparator only gets POSITIVE feedback from OUT to IN+.  With an
active-low open-drain wire-OR, OUT is LOW on fault and can therefore only
ever pull a node DOWN.  That fixes the sign of everything:

  * A channel that trips when its sensor node goes HIGH (emitter OPEN) has
    the sensor on IN- and the ladder tap on IN+, so feedback into the TAP is
    positive.  R410 does exactly that -> 7 K of clean hysteresis.
  * A channel that trips when its sensor node goes LOW (all three HOT/SHORT
    channels) has the sensor on IN+ and the tap on IN-.  Feedback into the
    tap would be NEGATIVE feedback around a 600 ns comparator = a relaxation
    OSCILLATOR, not hysteresis.  Feedback must go into the SENSOR node.
  * NTC_BRD is private to one channel, so R412 -> NTC_BRD is unconditionally
    safe: 4.0 K of real hysteresis on board-hot.
  * NTC_LED is shared by THREE channels and is IN+ for two of them and IN-
    for the third.  Any feedback there is positive for hot/short and
    NEGATIVE for open.  Measured: a single 56 k from FAULT to NTC_LED makes
    a BROKEN HARNESS chatter (released node 3.24 V > tap 3.03 V -> trips;
    asserted node 2.80 V < tap 2.90 V -> releases; repeat) - i.e. it breaks
    the one fault this block exists to catch.
    R409 + R411 IN SERIES (112 k) is the resolution: 110 k is the minimum
    that keeps a broken harness LATCHED (asserted node 3.03 V still above
    the asserted tap 2.90 V, 132 mV margin) while still delivering real
    positive feedback to the two lower-bound emitter channels.

Solved DC network (nodal, with the real FAULT pull-up 10 k carrier || 100 k
R207, VOL 20 mV, and every feedback path in place):

  channel            trips      releases   band    target
  emitter hot         92.3 C     91.0 C    1.25 K  90 / 75 C
  emitter short      113.7 C    112.4 C    1.35 K  n/a (integrity rail)
  emitter open       -20.6 C    latched at a genuine break (see above)
  board hot          116.2 C    112.2 C    4.04 K  110 / 95 C

DEVIATIONS / RESIDUALS (the orchestrator must fold these back)
--------------------------------------------------------------
 1. Trip points land 2-6 K HIGH and the bands are 1.2-4.0 K, not the 15 K
    blocks.md B4 quotes.  Root cause is not this wiring: 56 k feedback
    cannot produce a 15 K band against a FAULT node whose only pull-up is
    10 k || 100 k, because the same 56 k also drags the RELEASED FAULT level
    down.  Measured released FAULT: 3.00 V at 25 C and 2.78 V at 85/70 C
    mated (VIH 2.0 V - fine), 2.42 V / 1.80 V with J4 unmated (i.e. below
    VIH when hot on a J3-only bench mate - fail-safe direction, but
    blocks.md's "defined when unmated" claim does not survive at
    temperature).  Both are still well inside spec-dimming R10: a 1.25 K
    band against a 30-120 s module time constant cycles at <= 0.02 Hz,
    nowhere near the 1-65 Hz IEEE 1789 band.  The clean fix is a stronger
    FAULT pull-up (R207 100 k -> 10 k) on the `control` sheet, NOT more
    feedback here; that is a cross-sheet change and is reported, not taken.
 2. The 112 k feedback loads NTC_LED, so ADC0 reads ~1.6 K low at 25 C and
    ~2.3 K low at 85 C; R412 makes ADC1 read ~3.0 K low at 25 C and ~4.0 K
    low at 70 C.  Both are exact, monotonic, ratiometric functions of the
    NTC - firmware can invert them - but they DO change the ADC transfer
    function the ICD documents.
 3. blocks.md/parts.json claim the ADC source impedance is "5.0 kohm max at
    25 C, falling monotonically as the NTC heats".  It falls going HOT and
    RISES going cold: 10k||Rntc -> 10 k as the NTC opens.  With R402/R404 at
    1 k the total is 5.2 k at 25 C and 1.8 k at 90 C (both inside the
    <= 6 kohm claim), but 10.2 k at a broken harness - marginally over the
    ICD s3.3 10 kohm ceiling.  The feedback resistors help here (they shunt
    the cold end); without them it would be 11.0 k.

 4. TOOLING, not the design: LM339LVPWR is a FOUR-UNIT symbol - the only one
    in lib/aiee.kicad_sym - and kicad-sch-api places ONE unit per component
    while reporting every unit's pins on every instance.  Placing it the
    normal way silently produces a sheet whose units B/C/D pins are wired to
    dangling wire ends (measured: kicad-cli ERC `missing_unit` + 9 x
    `unconnected_wire_endpoint`, netlist pins 2/4/5/8/9/10/11/13/14 floating).
    `_place_unit` / `_merge_units` below are the workaround; anyone adding a
    multi-unit part to another sheet needs the same treatment.

VERIFIED (this session, kicad-cli 10.0.3)
-----------------------------------------
Built standalone, then stitched into a throwaway single-sheet root that adds
what the real siblings provide (PWR_FLAG on +3V3/GND from `power`, one load
per interface net from `control`/`led_if`):
    ERC 0 errors / 0 warnings
    netlist_audit: pass, unconnected_pins 0, 54/54 pins connected,
                   C401 <-> U401.3 decoupling association verified
    U401 pins 1..14 land on exactly the nets in section D, 0 mismatches
The project ERC gate itself belongs to the root agent and was NOT run.

Rebuild (writes <out>/thermal.kicad_sch; the ROOT generator owns the project
file and the real kicad/ directory):
    .venv/Scripts/python boards/lumina-par/kicad/gen/thermal.py [out_dir]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import kicad_sch_api as ksa

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-27) - register the pulled library.
ksa.get_symbol_cache().add_library_path(BOARD / "lib" / "aiee.kicad_sym")

FP = "aiee"

# ---------------------------------------------------------------- part table
# refdes -> LCSC, straight from parts/parts.json.  No deviations: this sheet
# uses every part sheets.md s1.4 allocates to it, at its allocated value.
LCSC = {
    "U401": "C3658338",    # LM339LVPWR quad open-drain comparator, TSSOP-14
    "RT401": "C49247666",  # 10k B3950 +-1% NTC, 0603
    "R401": "C25804", "R403": "C25804",     # 10k 1% - divider top legs
    "R402": "C21190", "R404": "C21190",     # 1k 1%  - ADC series
    "R405": "C13167",      # 2.7k 1% ladder top
    "R406": "C22967",      # 27k  1% ladder
    "R407": "C22765",      # 1.2k 1% ladder
    "R408": "C22847",      # 1.6k 1% ladder bottom
    "R409": "C23206", "R410": "C23206",     # 56k 1% feedback
    "R411": "C23206", "R412": "C23206",
    "C401": "C14663",      # 100nF - U401 V+ bypass
    "C402": "C14663", "C403": "C14663",     # 100nF - ADC filters
}

# ------------------------------------------------------------------- values
V_10K = "10k 0603 1%"
V_1K = "1k 0603 1%"
V_2K7 = "2.7k 0603 1%"
V_27K = "27k 0603 1%"
V_1K2 = "1.2k 0603 1%"
V_1K6 = "1.6k 0603 1%"
V_56K = "56k 0603 1%"
V_100N = "100nF 50V X7R 0603"
V_NTC = "10k B3950 +-1% NTC 0603"

# --------------------------------------------------------------- footprints
R0603 = f"{FP}:R0603"
C0603 = f"{FP}:C0603"

# ------------------------------------------------------------------ symbols
SYM_10K = f"{FP}:0603WAF1002T5E"
SYM_1K = f"{FP}:0603WAF1001T5E"
SYM_2K7 = f"{FP}:0603WAF2701T5E"
SYM_27K = f"{FP}:0603WAF2702T5E"
SYM_1K2 = f"{FP}:0603WAF1201T5E"
SYM_1K6 = f"{FP}:0603WAF1601T5E"
SYM_56K = f"{FP}:0603WAF5602T5E"
SYM_100N = f"{FP}:CC0603KRX7R9BB104"
SYM_NTC = f"{FP}:HNTC0603-103F3950FB"

# ------------------------------------------------------------------- nets
# Sheet-LOCAL label spellings.  The four interface nets are exposed as
# hierarchical pins with these bare names; the ROOT sheet places the local
# label that turns them into the canonical "/FAULT", "/NTC_LED", "/ADC0",
# "/ADC1" of sheets.md s2 (a child-only label would yield "/thermal/NAME").
# NTC_BRD is sheet-internal by design (sheets.md s2) and therefore becomes
# "/thermal/NTC_BRD" - nothing in constraints.json or P5-P8 keys off it.
# +3V3 and GND are bare GLOBAL power symbols, never hierarchical pins.
N_FAULT = "FAULT"
N_NTC_LED = "NTC_LED"
N_NTC_BRD = "NTC_BRD"
N_ADC0 = "ADC0"
N_ADC1 = "ADC1"
N_VREF_OPEN = "VREF_OPEN"      # ladder tap A, 3.026 V, -20.8 C equivalent
N_VREF_EHOT = "VREF_EHOT"      # ladder tap B, 0.284 V,  89.7 C equivalent
N_VREF_HOT2 = "VREF_HOT2"      # ladder tap C, 0.163 V, 110.8 C equivalent
N_HYS_LED = "HYS_LED"          # R409/R411 series midpoint (no other load)


def _place_unit(sh: schlib.Sheet, tmp_ref: str, unit: int, at, pins: dict,
                expect: dict, lib_id: str, value: str, footprint: str):
    """Place ONE unit of a multi-unit symbol and wire that unit's pins.

    LM339LVPWR is the only 4-UNIT symbol in lib/aiee.kicad_sym (units 1-4 =
    the four comparators; unit 1 also carries V+ pin 3 and GND pin 12).
    Two things follow, and both are load-bearing:

      1. A single ksa component covers ONE unit.  Place only unit 1 and
         kicad-cli ERC raises `missing_unit` ("unplaced units [B, C, D]")
         plus an `unconnected_wire_endpoint` for every wire drawn at a
         units-2..4 pin - measured, not assumed.  All four must be placed.
      2. ksa reports EVERY pin of EVERY unit on any instance, each at its own
         sub-symbol offset from that instance's anchor.  With all four units
         stacked on one anchor the bodies overlap and the fan-outs collide -
         e.g. pin 7 (unit 1) sits 2.54 mm from pin 10 (unit 4) on the same
         horizontal line, so pin 7's standard stub would END ON pin 10 and
         short NTC_LED to VREF_HOT2.  Giving each unit its own anchor is what
         removes that hazard; only the pads listed in `pins` are wired.

    ksa refuses a duplicate reference in BOTH `components.add` and the
    `reference` property setter, so each unit is added under its KiCad unit
    letter as a temporary ref (U401B/C/D - which also keeps schlib's per-ref
    pin/anchor/net bookkeeping distinct while wiring) and renamed to the real
    one afterwards by `_merge_units`.
    """
    with schlib._quiet():
        c = sh.sch.components.add(lib_id, reference=tmp_ref, value=value,
                                  position=tuple(at[:2]), unit=unit)
    c.footprint = footprint
    sh._lib_ids[tmp_ref] = lib_id
    sh._rotations[tmp_ref] = 0
    sh._anchors[tmp_ref] = (at[0], at[1])
    names = {p.number: p.name for p in c.pins}
    for pad, want in expect.items():
        if want not in names.get(pad, "<missing>"):
            raise ValueError(f"{tmp_ref} unit {unit} pin {pad}: expected name "
                             f"~'{want}', got '{names.get(pad)}'")
    sh.wire_pins(tmp_ref, pins)
    return c


def _merge_units(comps: list, ref: str) -> None:
    """Rename temporary unit refs onto the real one (post-wiring)."""
    for c in comps:
        c._data.reference = ref        # bypasses ksa's duplicate guard
        c.set_property("Reference", ref)


def build() -> schlib.Sheet:
    sh = schlib.Sheet("thermal",
                      title="LUM-PAR-A: thermal (NTC dividers, window "
                            "comparator, FAULT)",
                      paper="A3", date="2026-08-07", company="ai-ee",
                      pwr_base=400)

    # =====================================================================
    # A.  Module (emitter) NTC divider  ->  NTC_LED  ->  ADC0
    # =====================================================================
    # RT_LED itself is MODULE BOM, not board BOM: it sits on an RGB package's
    # slug copper (the 1.035 W site, not the 0.383 W white site) and reaches
    # this sheet through two J5 harness conductors, which is why J5 is 10-way
    # (blocks.md B4/B6).  Only the 10 k top leg is on this board.
    #   V(NTC_LED) = 3.3 x Rntc/(10k + Rntc): 1.650 V at 25 C, 0.284 V at
    #   89.7 C, 3.300 V at a broken harness, 0.000 V at a shorted one.
    sh.add_component(SYM_10K, "R403", V_10K, at=(38.10, 38.10),
                     footprint=R0603)
    sh.wire_pins("R403", {"1": "+3V3", "2": N_NTC_LED})

    # R402 <= 1 k is a HARD requirement, not a preference (D-T16, L-11): the
    # divider's own Thevenin impedance is up to 10 k (see deviation 3), and
    # the ICD s3.3 ceiling on what the carrier ADC will accept is 10 k.
    # R402 x C402 = 1 k x 100 nF = 100 us - a slow-signal filter for a sensor
    # with a 5 s thermal time constant, NOT a pulse filter.  The comparator
    # inputs tap the RAW node, ahead of R402, so the filter cannot delay the
    # protection.
    sh.add_component(SYM_1K, "R402", V_1K, at=(38.10, 76.20), footprint=R0603)
    sh.wire_pins("R402", {"1": N_NTC_LED, "2": N_ADC0})
    sh.add_component(SYM_100N, "C402", V_100N, at=(38.10, 114.30),
                     footprint=C0603)
    sh.wire_pins("C402", {"1": N_ADC0, "2": "GND"})

    # =====================================================================
    # B.  Board NTC divider  ->  NTC_BRD  ->  ADC1
    # =====================================================================
    # RT401's PLACEMENT is load-bearing and belongs to P6, not here (T-3):
    # ON the copper of the hottest driver stage, OUTSIDE the ICD s7.6 DC-DC
    # hot zone (2,46)-(36,68).  constraints.json already carries it as the
    # `ntc_brd` placement group anchored on U301.
    sh.add_component(SYM_10K, "R401", V_10K, at=(88.90, 38.10),
                     footprint=R0603)
    sh.wire_pins("R401", {"1": "+3V3", "2": N_NTC_BRD})
    rt = sh.add_component(SYM_NTC, "RT401", V_NTC, at=(88.90, 76.20),
                          footprint=R0603)
    sh.wire_pins("RT401", {"1": N_NTC_BRD, "2": "GND"})
    rt.set_property("Note", "P6: ON the hottest driver stage copper, "
                            "OUTSIDE the DC-DC hot zone (2,46)-(36,68)")
    sh.add_component(SYM_1K, "R404", V_1K, at=(88.90, 114.30), footprint=R0603)
    sh.wire_pins("R404", {"1": N_NTC_BRD, "2": N_ADC1})
    sh.add_component(SYM_100N, "C403", V_100N, at=(88.90, 152.40),
                     footprint=C0603)
    sh.wire_pins("C403", {"1": N_ADC1, "2": "GND"})

    # =====================================================================
    # C.  Reference ladder - ratiometric off +3V3 (see the module docstring)
    # =====================================================================
    #   +3V3 -R405 2.7k- A -R406 27k- B -R407 1.2k- C -R408 1.6k- GND
    #   A = 3.0258 V = -20.8 C   B = 0.2843 V = 89.7 C   C = 0.1625 V = 110.8 C
    #   101.5 uA total, R405 Thevenin at A 2.48 k / at B 2.56 k / at C 1.52 k.
    # Ratiometric matters: the carrier's ADC reference is the same +3V3, so a
    # rail error moves the thresholds and the ADC readings by the same factor
    # and the reported temperature does not shift.
    for ref, sym, val, y, top, bot in (
            ("R405", SYM_2K7, V_2K7, 38.10, "+3V3", N_VREF_OPEN),
            ("R406", SYM_27K, V_27K, 76.20, N_VREF_OPEN, N_VREF_EHOT),
            ("R407", SYM_1K2, V_1K2, 114.30, N_VREF_EHOT, N_VREF_HOT2),
            ("R408", SYM_1K6, V_1K6, 152.40, N_VREF_HOT2, "GND")):
        sh.add_component(sym, ref, val, at=(139.70, y), footprint=R0603)
        sh.wire_pins(ref, {"1": top, "2": bot})

    # =====================================================================
    # D.  U401 - the window comparator.  WIRED BY PIN NUMBER (erratum).
    # =====================================================================
    # Channel map, pin numbers only.  "trips" always means the output SINKS,
    # pulling FAULT low, which is the only thing an open drain can do:
    #
    #   OUT 1  IN- 6 = tap B (0.284 V), IN+ 7 = NTC_LED
    #          -> sinks when NTC_LED < 0.284 V  = EMITTER HOT (92.3/91.0 C)
    #   OUT 2  IN- 4 = NTC_LED,        IN+ 5 = tap A (3.026 V)
    #          -> sinks when NTC_LED > 3.026 V  = EMITTER OPEN / IMPLAUSIBLY
    #             COLD (-20.6 C; a broken harness parks the node at 3.30 V)
    #   OUT 13 IN- 10 = tap C (0.163 V), IN+ 11 = NTC_LED
    #          -> sinks when NTC_LED < 0.163 V  = EMITTER SHORT / RAIL-PINNED
    #             LOW (113.7 C equivalent; a real short parks it at 0.00 V)
    #   OUT 14 IN- 8  = tap C (0.163 V), IN+ 9  = NTC_BRD
    #          -> sinks when NTC_BRD < 0.163 V  = BOARD HOT (116.2/112.2 C)
    #
    # THE RULE THAT MUST SURVIVE EVERY FIX LOOP:
    #   FAULT IS OPEN DRAIN AND MUST NEVER BE DRIVEN HIGH (ICD s3.3,
    #   sheets.md s4 note 2).  ERC will want a driving pin on this net; the
    #   four outputs above plus R207 (100 k pull-up, `control` sheet) plus the
    #   carrier's own 10 k are it.  DO NOT add a push-pull buffer, a logic
    #   gate, a totem-pole driver, or a second pull-up here.  The carrier's
    #   eFuse fault is wire-OR'd onto the same node from the other side.
    # No pin of U401 is unused, so there is no no-connect and no floating
    # input: the datasheet's "do NOT tie the two inputs of an unused channel
    # together" trap cannot arise on this board.
    #
    # The symbol has FOUR UNITS; each is placed on its own anchor and only
    # its own pads are wired.  See _place_unit for why both halves of that
    # sentence are mandatory.  Unit 1 carries V+ (3) and GND (12), so it is
    # the one that goes through place_ic_with_decoupling and owns C401.
    u1_lib = f"{FP}:LM339LVPWR"
    u1_val = "LM339LVPWR quad open-drain comparator TSSOP-14"
    u1_fp = f"{FP}:TSSOP-14_L5.0-W4.4-P0.65-LS6.4-BL"
    # Library pin NAMES follow the datasheet's Figure 5-3 convention, NOT the
    # extract's Table 5.2 names (that is the erratum: pin 13 prints "OUT4"
    # and pin 14 prints "OUT3").  The minus signs are U+2212, which is what
    # the pulled symbol stores.  These assertions are the wiring insurance.
    sh.place_ic_with_decoupling(
        "U401", u1_lib, u1_val,
        at=(215.90, 63.50),
        pins={"1": N_FAULT,        # OUT, emitter hot
              "3": "+3V3",         # V+, 1.65-5.5 V rec (6 V abs)
              "6": N_VREF_EHOT,    # IN-, emitter hot
              "7": N_NTC_LED,      # IN+, emitter hot   <- R409/R411 land here
              "12": "GND"},
        footprint=u1_fp,
        expect={"1": "1OUT", "3": "VCC", "6": "1IN\u2212", "7": "1IN+",
                "12": "GND"},
        decoupling=[
            # Sec 9: "Bypass the supply directly at each device with a low ESR
            # 0.1 uF ceramic bypass capacitor directly between VCC pin and
            # ground pins."  Critical here because the output edges are tens
            # of ns - an un-bypassed supply rings and false-triggers.
            {"cap": "C401", "pin": "3", "rail": "+3V3", "value": V_100N,
             "lib_id": SYM_100N, "footprint": C0603,
             "max_dist_mm": 3.0},
        ],
        caps_at=(165.10, 63.50))
    units = [
        _place_unit(sh, "U401B", 2, (215.90, 114.30),
                    {"2": N_FAULT,          # OUT, emitter open / cold
                     "4": N_NTC_LED,        # IN-, open channel
                     "5": N_VREF_OPEN},     # IN+, open   <- R410 lands here
                    {"2": "2OUT", "4": "2IN\u2212", "5": "2IN+"},
                    u1_lib, u1_val, u1_fp),
        _place_unit(sh, "U401C", 3, (215.90, 152.40),
                    {"8": N_VREF_HOT2,      # IN-, board hot
                     "9": N_NTC_BRD,        # IN+, board hot <- R412 lands here
                     "14": N_FAULT},        # OUT, board hot
                    {"8": "3IN\u2212", "9": "3IN+", "14": "OUT3"},
                    u1_lib, u1_val, u1_fp),
        _place_unit(sh, "U401D", 4, (215.90, 190.50),
                    {"10": N_VREF_HOT2,     # IN-, emitter short
                     "11": N_NTC_LED,       # IN+, emitter short
                     "13": N_FAULT},        # OUT, emitter short
                    {"10": "4IN\u2212", "11": "4IN+", "13": "OUT4"},
                    u1_lib, u1_val, u1_fp),
    ]

    # =====================================================================
    # E.  Hysteresis / positive feedback.  READ THE DOCSTRING BEFORE EDITING.
    # =====================================================================
    # Every one of these resistors runs from FAULT (= all four OUT pins, one
    # net) to a comparator IN+ pin.  IN+ IS THE ONLY LEGAL DESTINATION: a
    # feedback resistor to IN- is negative feedback around a 600 ns
    # comparator and oscillates.  Do not "balance" them onto the IN- side.
    #
    # R409 + R411 IN SERIES = 112 k, FAULT -> NTC_LED.  The series pair is
    # deliberate and 56 k alone is WRONG here: NTC_LED is IN+ for the hot and
    # short channels but IN- for the OPEN channel, so this path is positive
    # feedback for two channels and negative for the third.  112 k is the
    # first value that keeps a broken harness latched (asserted node 3.03 V
    # vs asserted tap 2.90 V) instead of chattering; 56 k gives 2.80 V vs
    # 2.90 V and the open detector - the whole point of block B4 - buzzes.
    # HYS_LED is the midpoint and carries nothing else.
    sh.add_component(SYM_56K, "R409", V_56K, at=(292.10, 38.10),
                     footprint=R0603)
    sh.wire_pins("R409", {"1": N_FAULT, "2": N_HYS_LED})
    r411 = sh.add_component(SYM_56K, "R411", V_56K, at=(292.10, 76.20),
                            footprint=R0603)
    sh.wire_pins("R411", {"1": N_HYS_LED, "2": N_NTC_LED})
    r411.set_property("Note", "In SERIES with R409 on purpose - 56k alone "
                             "makes the open-harness detector chatter")

    # R410, FAULT -> tap A (IN+ pin 5).  The one reference-side feedback the
    # topology allows: the open channel's sensor is on IN-, so pulling the
    # TAP down on fault reinforces the trip.  2.48 k tap against 56 k gives
    # 3.028 V armed / 2.899 V tripped = 129 mV, i.e. a 7 K cold-side band.
    # Its 12 mV of coupling down the ladder to taps B and C is accounted for
    # in the trip numbers in the docstring.
    sh.add_component(SYM_56K, "R410", V_56K, at=(292.10, 114.30),
                     footprint=R0603)
    sh.wire_pins("R410", {"1": N_FAULT, "2": N_VREF_OPEN})

    # R412, FAULT -> NTC_BRD (IN+ pin 9).  NTC_BRD is used by exactly one
    # channel, so this is unconditionally positive feedback with no
    # cross-coupling: 116.2 C trip / 112.2 C release, 4.0 K.
    sh.add_component(SYM_56K, "R412", V_56K, at=(292.10, 152.40),
                     footprint=R0603)
    sh.wire_pins("R412", {"1": N_FAULT, "2": N_NTC_BRD})

    # =====================================================================
    # rails - CONSUMING power symbols only
    # =====================================================================
    # The `power` sheet owns the PWR_FLAG for every rail (each one enters the
    # board through J3's passive pins there).  A second flag on the same net
    # collides power_out <-> power_out at the project ERC, which is the same
    # trap p4-wiring-notes s2 documents for the driver VCC nodes - hence
    # flag=False on both.  A power SYMBOL is still required: without one, a
    # bare "GND"/"+3V3" label inside a child sheet names "/thermal/GND".
    sh.power_flag("GND", at=(330.20, 38.10), sym="power:GND", flag=False)
    sh.power_flag("+3V3", at=(330.20, 63.50), sym="power:+3V3", flag=False)

    # =====================================================================
    # sheet interface (sheets.md s2)
    # =====================================================================
    # Free-cluster variant: local label + hierarchical label on one stub, so
    # the hier label joins the net by wire geometry rather than by name.
    # Shapes are semantic (kicad-sch-api drops the shape on a CHILD's label -
    # LEARNINGS 2026-07-28 - but Project.add_sheet honours it on the ROOT's
    # sheet pin, which is where it is read).
    #   FAULT    output : driven HERE (open drain, sinking only)
    #   NTC_LED  input  : arrives from `led_if` (J5 harness pin)
    #   ADC0/1   output : sourced HERE, on to `control` -> J4
    for i, (net, shape) in enumerate([
            (N_FAULT, "output"),
            (N_NTC_LED, "input"),
            (N_ADC0, "output"),
            (N_ADC1, "output")]):
        sh.hier_pin(net, shape=shape, at=(330.20, 114.30 + i * 12.70))

    for ref, code in LCSC.items():
        sh.sch.components.get(ref).set_property("LCSC", code)
    # Units 2-4 are still under their temporary refs, so the loop above missed
    # them: give every instance the same identity fields, then merge the refs.
    for c in units:
        c.set_property("LCSC", LCSC["U401"])
    _merge_units(units, "U401")
    return sh


def main(argv=None) -> int:
    # Default out dir is kicad/, and project=False: the ROOT generator owns
    # <root>.kicad_pro and this sheet must never write one.
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.thermal", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.thermal", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "decoupling_associations": len(sh.decoupling),
        "place_report": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
