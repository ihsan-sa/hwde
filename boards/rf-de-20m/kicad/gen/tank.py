"""rf-de-20m `tank` sheet (blocks.md B7-B9): the series resonant tank, the
L-match and the RF output connector.

Refdes range 300-399, `#PWR` base 300 (architecture/sheets.md s4).
Zones B (magnetics, NO planes, NO heatsink) and C (output, planes restored).

Rebuild (writes <out>/tank.kicad_sch; the ROOT generator owns the project):
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/tank.py [OUT_DIR]

GROUND TRUTH
------------
architecture/sheets.md s1/s4, architecture/blocks.md B7-B9 + s4.3 (SPIRAL-1..6),
architecture/decisions.md D3/D11 (the AMENDED values), constraints.json,
parts/parts.json, parts/C22418168.json (SMA), plus the library pin tables.

TOPOLOGY (one series chain, one shunt bank)
--------------------------------------------
    /SW --[ L301  L_s 164nH ]-- /tank/TANK_A --[ C301..C309 + C320/C321 ]--
        /tank/TANK_B --[ L302  L_m 110nH ]-- /tank/RFOUT --[ J301 ]
                                                  |
                                 [ C310..C319 + C322/C323  C_m ] -- GND

    (C321/C322/C323 are DNP bench-trim sites; C320 is POPULATED - see the
     "WHY C_s FALLS TO 419 pF" block below before you touch it.)

WHY C_s FALLS TO 419 pF - EXTRA SERIES L IS CANCELLED BY *LESS* SERIES C
-------------------------------------------------------------------------
**COUNTER-INTUITIVE, AND SOMEONE WILL "FIX" IT BACK. Read this before adding
capacitance to the C_s bank.** P8 fix a3, 2026-08-08, from the SPICE benches
in `kicad/sims/` (full derivation: reports/sim-notes.md s3).

The `TANK_A -> C_s bank -> TANK_B` run crosses zone B, where decisions.md D4
forbids any In1/In2/B.Cu pour (a plane under a PCB air-core spiral is a
shorted turn). A conductor with NO RETURN IMAGE does not carry microstrip
inductance `mu0.h/w` (~0.1 nH/mm, ~4 nH here); it carries free-space PARTIAL
SELF-inductance `(mu0.l/2pi)(ln(2l/w)+0.5)` - ~23 nH for 40 mm of 8 mm strip,
and the real path is longer. P8 carries it as **25-35 nH**, nominal 30 nH =
j3.77 ohm at 20 MHz = **0.91 R** dropped into a network whose ENTIRE design
reactance is 1.283 R. That is a 7x modelling error on the same copper, and it
is the sole cause of the as-built board missing ZVS.

    X_net = omega.(L_s + L_bridge) - 1/(omega.C_s) + X_match

`L_bridge` can only ADD positive reactance. The only element that subtracts it
is C_s, and `1/(omega.C_s)` GROWS AS C_s SHRINKS. So the correct move is to
**REMOVE** capacitors from the C_s bank, never to add them:

    C_s 504 pF (9 x 56),      30 nH bridge : X_net/R 2.00   NO ZVS, 53.4 W
    C_s 419 pF (7 x 56 + 27), 30 nH bridge : X_net/R 1.285  ZVS,   113.8 W
                              25 nH corner : X_net/R 1.144
                              35 nH corner : X_net/R 1.426

i.e. the fix holds across the whole 25-35 nH uncertainty band (the stray is an
ESTIMATE - OPEN-13 says measure it on the first article). Measured after the
change on the same deck, same 30 V bus: Vds at turn-on **1.41 V** (was 15.60),
dVds/dt **-1.21 V/ns** (was -5.89), P_out **113.8 W** (was 53.4), Vds,pk
122.2 V on a 200 V part, X_net/R 1.285 against the design's 1.283.

419 pF is reachable EXACTLY as 7 x 56 + 1 x 27, which is why C320 - a trim
site that existed only as bench headroom - is populated on the shipped board.

TANK_A is the highest node on the board at **156 V pk**, 14 V ABOVE the drain -
ordinary series-resonant magnification at Q_L = 5, declared at 180 V in
constraints.json and silkscreened at P6 (sheets.md s6 note 8).

THE SPIRALS ARE REAL SCHEMATIC COMPONENTS WHOSE FOOTPRINT *IS* THE PART
------------------------------------------------------------------------
L301 and L302 are ETCHED PCB AIR-CORE SPIRALS, not purchasable parts
(decisions.md D3: no LCSC part class closes them - molded power inductors sit
at Q 20-40 at 20 MHz, i.e. 25-50 W in one part, and genuine high-Q RF chip
inductors are rated 120-140 mA against 6.96 A rms; paralleling rescues
neither because Q_total = Q_each exactly).

They are stock `Device:L` symbols carrying no LCSC code and marked
`in_bom = False`, but they DO carry a footprint: the copper is the component,
so the winding lives inside the footprint rather than being drawn by hand at
P6.  Authored 2026-08-08 by `kicad/gen/spirals.py`, derived and cross-checked
in `reports/spiral-design.md`:

    L301  aiee:SPIRAL_L164N   3 turns, OD 33.10 mm, 2.5 mm trace, 1.0 mm gap
    L302  aiee:SPIRAL_L110N   2 turns, OD 32.57 mm, 2.5 mm trace, 1.0 mm gap

Both are wound on F.Cu AND B.Cu in parallel (SPIRAL-2) with the inner terminal
escaping on an In1+In2 radial bridge (SPIRAL-4), and both are KiCad NET TIES:
pad 1 and pad 2 are deliberately joined by the winding, which is what an
inductor is at DC.  Each part also carries its own four-layer rule area, so
"no plane under a spiral" travels with the footprint.

This unblocks P5: `board_init` can now place them.  What it does NOT do is
place them well - SPIRAL-5 (>= 38 mm centre-to-centre) and SPIRAL-6 (no metal
within 15 mm in plan view, either face) are still P6's to enforce, and the
courtyard is 39.99 x 33.69 mm (L301) / 39.46 x 33.16 mm (L302), which fits
zone B's 40 mm width with ~0.01 mm to spare in the E-W orientation only.

CAPACITOR BANK SIZING - MIXED-VALUE C_m AND FOUR TRIM SITES (P4 review W1)
---------------------------------------------------------------------------
Both banks are built from 1 kV C0G 1206 parts. C0G, never X7R: X7R's voltage
and temperature coefficients detune a resonant tank, which is the one place
on this board where capacitance is a frequency-setting quantity rather than a
bypass. TWO values are now stocked - CC1206JKNPOCBN560 (56 pF, C113875) and
CC1206JKNPOCBN270 (27 pF, C541492, the same Yageo family/rating/package).

    C_s  ideal-network target 518 pF     built 7 x 56 + 1 x 27  = 419 pF
         (the 518 pF target is the NO-BRIDGE design value; the board carries
          ~30 nH of un-imaged zone-B copper and 419 pF is what cancels it -
          see "WHY C_s FALLS TO 419 pF" above. C308/C309 are DNP.)
    C_m  target 530.4 pF (ideal L-match) built 9 x 56 + 1 x 27  = 531 pF

The pre-review build was 10 x 56 = 560 pF for C_m, +5.7 % on the ideal match,
and the sheet argued that the high side was the recoverable one. The review
priced what that actually costs, and it is not free:

    build              Z seen by the tank   VSWR    series X/R   Pout at 40 V
    560 pF (was)       3.737 + j0.675       1.220      1.47        ~221 W
    531 pF (now)       4.122 + j0.072       1.018      1.19        ~200 W
    ideal 530.4 pF     4.136 + j0.050       1.012      1.18         200 W

Both errors pushed the same way: R_in 9.5 % low raised P_out to ~221 W and
with it I_dc, conduction loss and the 11.25 W / Tj 114 C two-FET thermal
budget the whole paralleling decision rests on; and total series reactance
moved to X/R 1.47 against the Class E optimum 1.1525, so ZVS was off and
switching loss appeared on top. ONE 27 pF part in place of one 56 pF fixes
both: X/R 1.19 (that residual was computed with C_s at 504 pF and NO bridge
stray; the bridge is what later took C_s to 419 pF - see the block above).
Numbers computed at 20 MHz with L_s 164 nH, L_m 110 nH into 50 ohm.

TRIM SITES: C321 (C_s) and C322/C323 (C_m), 27 pF, DNP.  C320 IS POPULATED.
----------------------------------------------------------------------------
Neither bank had a trim site - only C_shunt got DNP pads (C205/C206) - so the
tank could only be trimmed DOWN, in 56 pF (11 %) steps, by depopulation. Four
27 pF sites give each bank a bidirectional bench trim. **C320 is no longer a
spare: the P8 fix a3 populate SPENDS it** (7 x 56 + 27 = 419 pF), so C_s's
remaining upward trim is C321 alone:

    C_s   419 pF as built (C308/C309 DNP, C320 POPULATED);
                            +27 pF by populating C321
                            +56 pF per re-populated 56 pF site (C308/C309)
                            -27 pF by depopulating C320
                            -56 pF per further depopulated 56 pF site
                            (392 / 419 / 446 / 448 / 475 / 502 / 504 ... pF)
    C_m   475 pF populated (C318 DNP at P8) + 46.1 pF of RFOUT pour
                            = 521 pF presented;
                            +27 / +54 pF by populating C322/C323
                            +56 pF by populating C318 again
                            -27 pF by depopulating C319 (the 27 pF part)

This matters because L301/L302 are ETCHED SPIRALS whose realised inductance
is the largest unknown in the tank - a +/-10 % spiral is ordinary, and the
capacitor banks are the only knob that answers it. C_s additionally carries
OPEN-12 (the P1 fragment's C_series coefficient is refuted; SIM-4 arbitrates),
which is why both banks stay PARALLEL ARRAYS rather than single parts.

Per-part duty, so nobody "simplifies" the split. Current divides in proportion
to capacitance, so DEPOPULATING TWO C_s SITES RAISES THE DUTY ON THE REST:
each populated 56 pF part now carries 56/419 x 6.96 = **0.93 A rms** (was
56/504 x 6.96 = 0.77 A over nine parts, +21 %) and C320 carries 0.45 A, so
per-part dissipation goes ~105 -> ~150 mW and the whole C_s bank ~0.95 ->
~1.15 W. Still inside a 1 kV C0G 1206's capability, but it is a real cost of
the fix and the C_s bank's temperature rise is a BRING-UP CHECK, not an
assumption. In C_m each 56 pF part carries 56/531 x 6.66 = 0.70 A rms and the
27 pF part 0.34 A - because C_m carries 6.66 A rms, nearly the full tank
current, NOT the 2.0 A load current. The 1 kV rating is 6.6x the 151 V pk
across the C_s bank.

NET NAMING (sheets.md s1 - BINDING)
------------------------------------
* `GND` is a POWER SYMBOL -> global and BARE, flag=False (`hk` owns the flags).
* `SW` is the ONLY hierarchical pin. It crosses the root (also exposed by
  `stage`), so the net comes out **`/SW`**.
* Three nets are sheet-internal and come out `/tank/<NAME>`: TANK_A, TANK_B,
  RFOUT - exactly the spellings constraints.json uses.
* `+40V` and `+5V` do not appear on this sheet at all.

NOT ON THIS SHEET
-----------------
No output TVS, no directional coupler, no VSWR sense, no DC block, no
harmonic filter. The harmonic windows (SIM-4: h2 <= -20 dBc, h3 <= -33 dBc)
are far short of any transmit compliance mask, which is why this board is
DUMMY-LOAD ONLY (blocks.md s5). A load that moves off the design point drives
peak drain stress toward 7x Vdd on a 200 V part.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

import genlib  # noqa: E402

ksa = schlib.ksa
ksa.get_symbol_cache().add_library_path(str(BOARD / "lib" / "aiee.kicad_sym"))

# --------------------------------------------------------------------- nets
GND = "GND"
SW = "SW"              # hier, in from `stage` via the root -> /SW
TANK_A = "TANK_A"      # -> /tank/TANK_A   156 V pk - highest node on the board
TANK_B = "TANK_B"      # -> /tank/TANK_B
RFOUT = "RFOUT"        # -> /tank/RFOUT

# ------------------------------------------------------------------ symbols
S_L = "Device:L"                          # PCB spiral - stock symbol, no fp
S_C56P = "aiee:CC1206JKNPOCBN560"         # 56pF 1kV C0G 1206
S_C27P = "aiee:CC1206JKNPOCBN270"         # 27pF 1kV C0G 1206 (W1)
S_SMA = "aiee:CONSMA001-SMD-G-T"          # default Reference "RF" -> J301

# --------------------------------------------------------------- footprints
F_C1206 = "aiee:C1206"
F_SMA = "aiee:SMA-SMD_CONSMA001-SMD-G-T"
# The spirals - the copper IS the part. kicad/gen/spirals.py authors both.
F_SPIRAL_LS = "aiee:SPIRAL_L164N"
F_SPIRAL_LM = "aiee:SPIRAL_L110N"

# ------------------------------------------------------------------- values
V_C56P = "56pF 1kV C0G 1206"
V_C27P = "27pF 1kV C0G 1206"
V_SMA = "SMA jack 50R SMD (CONSMA001)"

# Bank membership. (ref, pF, dnp) - the ONLY place the banks are defined.
# P8 FIX a3 2026-08-08 (kicad/sims SIM-2b/SIM-4, reports/sim-notes.md): C308
# and C309 are DEPOPULATED and the C320 trim site is POPULATED, taking C_s
# 504 -> 419 pF. DO NOT "restore" the two 56 pF parts: the ~30 nH of un-imaged
# zone-B copper in series with this bank is cancelled by LESS capacitance, not
# more - full derivation in the module docstring, "WHY C_s FALLS TO 419 pF".
CS_BANK = [(f"C{n}", 56, n in (308, 309))
           for n in range(301, 310)]                            # 392 pF
# P8 2026-08-08, board review E2: C318 is DEPOPULATED. C_m is not the bank
# alone - the /tank/RFOUT F.Cu pour sits 84.5 % over In1 GND at 0.2444 mm and
# adds a MEASURED 46.06 pF in parallel at the RFOUT node (route-notes.md s7,
# re-derived independently by the P8 review). 9 x 56 + 27 = 531 pF therefore
# SHIPPED as 577 pF - past the 560 pF bank P4 review W1 explicitly rejected
# (3.53 + j1.01 ohm, series X/R 1.65, ~233 W). 8 x 56 + 27 = 475 pF + 46.1 =
# 521 pF, -1.8 % on the 530.4 pF ideal: 4.26 - j0.15 ohm, X/R 1.10.
CM_BANK = ([(f"C{n}", 56, n == 318) for n in range(310, 319)]
           + [("C319", 27, False)])                    # 475 pF populated
CS_TRIM = [("C320", 27, False), ("C321", 27, True)]    # C320 POPULATED at P8
CM_TRIM = [("C322", 27, True), ("C323", 27, True)]

CS_REFS = CS_BANK + CS_TRIM
CM_REFS = CM_BANK + CM_TRIM

# The spiral symbols are stock Device:L, whose Description ("Inductor") does not
# match the rich `descr` the custom footprints carry. board_init's schematic
# parity check compares the two and reports footprint_symbol_field_mismatch,
# which is a P5 phase-gate failure. Carry the footprint text as an explicit
# Description field so symbol and footprint agree.
# MUST stay byte-identical to `(descr ...)` in lib/aiee.pretty/SPIRAL_*.kicad_mod
# - kicad/gen/spirals.py authors both, so change them together.
DESCR = {
    "L301": (
        "Etched PCB air-core planar spiral 164nH at 20MHz (rf-de-20m L_s, "
        "L301). 3 turns, OD 33.10mm, 2.5mm trace, 1.0mm gap, F.Cu||B.Cu "
        "parallel winding, In1+In2 inner-terminal bridge. NET TIE: pads 1-2 "
        "are joined by the winding. No plane or heatsink beneath - shorted turn."
    ),
    "L302": (
        "Etched PCB air-core planar spiral 110nH at 20MHz (rf-de-20m L_m, "
        "L302). 2 turns, OD 32.57mm, 2.5mm trace, 1.0mm gap, F.Cu||B.Cu "
        "parallel winding, In1+In2 inner-terminal bridge. NET TIE: pads 1-2 "
        "are joined by the winding. No plane or heatsink beneath - shorted turn."
    ),
}

LCSC = {"J301": "C22418168"}
for _r, _pf, _d in CS_REFS + CM_REFS:
    LCSC[_r] = "C113875" if _pf == 56 else "C541492"


def _pf_total(bank) -> int:
    return sum(pf for _, pf, dnp in bank if not dnp)


def _cs_note(ref: str, pf: int, dnp: bool) -> str:
    """Per-site C_s note. The bank is no longer uniform after P8 fix a3, so a
    single populated/DNP string would mislead: C308/C309 are DNP *because the
    fix removed them*, and C320 is populated *because the fix spends it*."""
    if ref in ("C308", "C309"):
        return ("C_s DEPOPULATED at P8 fix a3 (2026-08-08). C_s 504 -> 419pF "
                "cancels the ~30nH un-imaged zone-B tank bridge: extra series "
                "L needs LESS series C. RE-POPULATING BREAKS ZVS - X/R 2.00, "
                "Vds 15.6V at turn-on, 53W not 114W. See reports/sim-notes.md")
    if ref == "C320":
        return ("C_s FINE TRIM - POPULATED at P8 fix a3. 7x56 + this 27pF = "
                "419pF -> X/R 1.285 against the 1.283 design target, ZVS at "
                "1.41V and 113.8W at the 30V bench. Not spare headroom")
    if dnp:
        return ("C_s TRIM SITE - DNP. Populate for +27pF (446pF); after fix "
                "a3 spent C320 this is the bank's only remaining UP-trim")
    return ("C_s bank 7x56pF + C320 27pF = 419pF (P8 fix a3). Do NOT add C_s "
            "to 'improve' the tank - the zone-B bridge stray is cancelled by "
            "LESS series C. C0G, never X7R")


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None, note=None,
         in_bom=True, rotation=0, dnp=False):
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if dnp:
        # kicad-sch-api's writer hard-codes `(dnp no)`, so `Variant` is the
        # only do-not-populate marking reachable from a generator and it is
        # kept VISIBLE by genlib (LEARNINGS 2026-08-07). P9 filters by hand.
        fields["Variant"] = "DNP"
    if note:
        fields["Note"] = note
    descr = DESCR.get(ref)
    if descr:
        fields["Description"] = descr
    c = sh.add_component(lib_id, ref, value, at, rotation=rotation,
                         footprint=footprint, fields=fields or None,
                         expect=expect)
    if not in_bom:
        c.in_bom = False
    return c


def _note(sh, at, lines, dy=5.08):
    x, y = at
    for i, line in enumerate(lines):
        sh.sch.add_text(line, position=(x, round(y + i * dy, 4)))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("tank",
                      title="rf-de-20m: tank - L_s/C_s series tank, L-match, "
                            "RF output",
                      paper="A2", date="2026-08-07", company="ai-ee",
                      pwr_base=300)

    # GND is consumed here; `hk` owns every PWR_FLAG.
    sh.power_flag(GND, at=(25.4, 25.4), sym="power:GND", flag=False)

    # /SW arrives from `stage`. Free-cluster hier pin: local label at one end,
    # hierarchical label at the other, joined by wire geometry.
    sh.hier_pin(SW, shape="input", at=(25.4, 50.8))

    # =====================================================================
    # B7 - series resonant tank
    # =====================================================================
    # L301 = L_s = 164 nH. ETCHED PCB SPIRAL: Device:L, custom footprint that
    # IS the copper, not in the BOM. As drawn: 3 turns, OD 33.10 mm, 2.5 mm
    # trace / 1.0 mm gap, F.Cu||B.Cu -> 164.0 nH, Q 388, 2.6 W over 860 mm2
    # (2.99 mW/mm2 against the 7 mW/mm2 SPIRAL-1 ceiling).
    _add(sh, "L301", S_L, "164nH", (114.3, 114.3), footprint=F_SPIRAL_LS,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_s - ETCHED PCB AIR-CORE SPIRAL (net tie, pads 1-2 joined by "
              "the winding). 3T OD 33.1mm F.Cu||B.Cu. NO plane or heatsink "
              "beneath - shorted turn. See reports/spiral-design.md")
    sh.wire_pins("L301", {"1": SW, "2": TANK_A})

    # C_s bank: 7 x 56 pF + C320 27 pF = 419 pF POPULATED (P8 fix a3; C308,
    # C309 and C321 are DNP). NOT 504 pF and NOT the 518 pF ideal-network
    # target - the ~30 nH of un-imaged zone-B copper in series with this bank
    # is cancelled by REMOVING capacitance. See the module docstring.
    # C_s is a SERIES element and floats, which is why it can live in zone B
    # where there is no ground plane. Trim sites are part of the bank and must
    # be placed IN it, not on a stub.
    for i, (ref, pf, dnp) in enumerate(CS_REFS):
        _add(sh, ref, S_C56P if pf == 56 else S_C27P,
             V_C56P if pf == 56 else V_C27P,
             (88.9 + (i % 6) * 76.2, 190.5 + (i // 6) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"}, dnp=dnp,
             note=_cs_note(ref, pf, dnp))
        sh.wire_pins(ref, {"1": TANK_A, "2": TANK_B})

    # =====================================================================
    # B8 - L-match to 50 ohm
    # =====================================================================
    # L302 = L_m = 110 nH. SPIRAL-3: nearly as large as L301 despite being 67%
    # of the inductance, because the binding constraint is DISSIPATION AREA,
    # not L. Do not let a reviewer shrink it. As drawn: 2 turns, OD 32.57 mm,
    # same 2.5/1.0 trace -> 110.0 nH, Q 325, 2.1 W over 833 mm2.
    _add(sh, "L302", S_L, "110nH", (330.2, 114.3), footprint=F_SPIRAL_LM,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_m - ETCHED PCB AIR-CORE SPIRAL (net tie, pads 1-2 joined by "
              "the winding). 2T OD 32.57mm F.Cu||B.Cu. Centre-to-centre "
              ">=38mm from L301 (SPIRAL-5). See reports/spiral-design.md")
    sh.wire_pins("L302", {"1": TANK_B, "2": RFOUT})

    # C_m bank: 8 x 56 + 1 x 27 = 475 pF POPULATED (C318 depopulated at P8,
    # review E2) + 46.1 pF of RFOUT pour = 521 pF against the 530.4 pF ideal
    # (W1 - the 10 x 56 = 560 pF build gave 3.74 ohm, VSWR 1.22 and ~221 W),
    # plus two 27 pF DNP TRIM SITES. C_m RETURNS TO GROUND and carries
    # 6.66 A rms, so it lives in zone C where the plane stack exists.
    for i, (ref, pf, dnp) in enumerate(CM_REFS):
        _add(sh, ref, S_C56P if pf == 56 else S_C27P,
             V_C56P if pf == 56 else V_C27P,
             (88.9 + (i % 6) * 76.2, 279.4 + (i // 6) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"}, dnp=dnp,
             note=("C_m TRIM SITE - DNP. Populate for +27pF; depopulate C319 "
                   "for -27pF"
                   if dnp else
                   "C_m bank 8x56+1x27 = 475pF populated; the RFOUT pour "
                   "adds 46.1pF -> 521pF against the 530.4pF ideal. Carries "
                   "6.66A rms, not the 2A load current"))
        sh.wire_pins(ref, {"1": RFOUT, "2": GND})

    # =====================================================================
    # B9 - RF output
    # =====================================================================
    # Same part as J201. Pins 1-4 are the four square ground lands, pin 5 the
    # centre RF contact (parts/C22418168.json). 100 Vrms / 2.0 A rms at
    # 20 MHz is electrically trivial for an SMA; mount style and stock drove
    # the choice. /tank/RFOUT must stay <= 15 mm from the C_m node (D7).
    _add(sh, "J301", S_SMA, V_SMA, (495.3, 114.3), footprint=F_SMA,
         expect={str(n): str(n) for n in range(1, 6)},
         note="RF out, 200 W. SILK: burn + RF-exposure hazard (sheets.md s6.8)")
    sh.wire_pins("J301", {"1": GND, "2": GND, "3": GND, "4": GND, "5": RFOUT})

    # =====================================================================
    # sheet notes
    # =====================================================================
    _note(sh, (88.9, 355.6), [
        "L301 AND L302 ARE ETCHED PCB AIR-CORE SPIRALS - THE COPPER IS",
        "THE PART. No LCSC code, excluded from the BOM. The winding",
        "lives inside the footprint (kicad/gen/spirals.py); see",
        "reports/spiral-design.md for both inductance derivations.",
        "  L301 aiee:SPIRAL_L164N  3T OD 33.10mm, 2.5/1.0 trace/gap",
        "  L302 aiee:SPIRAL_L110N  2T OD 32.57mm, 2.5/1.0 trace/gap",
        "Both are KiCad NET TIES: pads 1-2 are joined by the winding,",
        "  which is what an inductor is at DC. Do not 'fix' the short.",
        "SPIRAL-2 is TAKEN: F.Cu and B.Cu carry identical windings in",
        "  parallel, stitched 14 vias per terminal, inner terminal out",
        "  on a 5 mm In1+In2 radial bridge (SPIRAL-4). Q 388 / 325,",
        "  2.6 W / 2.1 W - not the 10 W the power tree budgeted.",
        "SPIRAL-5: centre-to-centre >= 38 mm. At 38 mm the computed",
        "  mutual is -2.0 nH (k 1.5%), i.e. -4.1 nH / -1.5% on the",
        "  series total. P8 folds it in; the trim sites cover it.",
        "SPIRAL-6: no metal within 15 mm in plan view on either face.",
        "  A conductive plate under a spiral is a SHORTED TURN and no",
        "  copper cutout prevents it - that includes the heatsink,",
        "  brackets, standoffs and fasteners.",
        "Each footprint carries its own 4-layer rule area (no pour on",
        "  F/B, no tracks or vias on In1/In2) out to 20.5 mm radius.",
        "  Zone B's blanket In1/In2 void is still required beyond that.",
    ])
    _note(sh, (88.9, 431.8), [
        "C_m IS 8 x 56 pF + 1 x 27 pF (C319) = 475 pF POPULATED, with",
        "C318 DEPOPULATED (P8 review E2). The RFOUT F.Cu pour adds a",
        "MEASURED 46.1 pF to GND at this node, so the bank alone is not",
        "the match: 9 x 56 + 27 = 531 pF SHIPS as 577 pF, worse than the",
        "560 pF bank P4 W1 rejected (3.53 + j1.01 ohm, X/R 1.65, ~233 W).",
        "475 + 46.1 = 521 pF: 4.26 - j0.15 ohm, X/R 1.10, ideal 530.4 pF.",
        "-",
        "C_s IS 7 x 56 + C320 27 pF = 419 pF (P8 FIX a3, 2026-08-08).",
        "C308 AND C309 ARE DNP AND MUST STAY DNP. This is NOT the 518 pF",
        "ideal-network value and it is NOT a mistake: zone B carries NO",
        "plane (D4 - a plane under a spiral is a shorted turn), so the",
        "TANK_A->C_s->TANK_B run has no return image and contributes",
        "~30 nH (25-35 nH) of series inductance. EXTRA SERIES L IS",
        "CANCELLED BY LESS SERIES C: 1/(wC) grows as C shrinks.",
        "  504 pF + 30 nH bridge -> X/R 2.00, Vds 15.6 V at turn-on, 53 W",
        "  419 pF + 30 nH bridge -> X/R 1.285, Vds 1.41 V, 113.8 W",
        "Do NOT 'restore' the two 56 pF parts. Measured in kicad/sims/;",
        "reports/sim-notes.md s3 has the whole derivation.",
        "-",
        "REMAINING TRIM: C321 (C_s, +27 pF) and C322/C323 (C_m) are DNP;",
        "C320 is SPENT by the fix. Depopulate for -27 (C319/C320) or",
        "-56 pF. The spirals' realised L is the tank's largest unknown",
        "and OPEN-13 says MEASURE the bridge stray on the first article",
        "before finalising this bank.",
    ])
    _note(sh, (88.9, 482.6), [
        "NO X7R ANYWHERE IN THE TANK. C0G/NP0 only - X7R's voltage and",
        "temperature coefficients detune a resonant network. (X7R IS",
        "correct on the DC bus, and is used there.)",
        "/tank/TANK_A REACHES 156 V pk - the highest node on the board,",
        "14 V ABOVE the drain. Silkscreen it at P6.",
    ])
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
        hidden = genlib.hide_aux_fields(path)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.tank", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.tank", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "internal_nets": sorted({TANK_A, TANK_B, RFOUT}),
        "c_s_pf": _pf_total(CS_REFS),
        "c_m_pf": _pf_total(CM_REFS),
        "dnp": sorted(r for r, _, d in CS_REFS + CM_REFS if d),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
