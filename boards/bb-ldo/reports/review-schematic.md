# bb-ldo - schematic review (P4, adversarial)

Reviewer: schematic-reviewer, fresh context. Inputs read: `requirements.md`,
`reference/build-modes.md` (scope tier `block-only`, binding `canonical`),
`reference/checklists/power.md` + `connector.md` (the two domains on this
board), `parts/C6186.json`, `parts/parts.json`, `architecture/constraints.json`,
`architecture/blocks.md` s.6/s.9, `architecture/sheets.md`,
`kicad/bb-ldo.net`, `kicad/bb-ldo.kicad_sch`, `kicad/decoupling.json`,
`lib/aiee.kicad_sym`, `lib/aiee.pretty/*.kicad_mod`, `reports/gate-erc.json`,
and the six VERIFIED knowledge records `knowledge.py --select` returns for this
workspace. `reports/schematic.pdf` was read page-by-page and re-rasterised at
900 dpi in four crops (U1, C1+J1, C2+J2, the flag block) because the whole-page
view is too small to judge glyph collisions.

**Verdict: the circuit is right. The board is not yet safe to hand to a user,
and one drawing artefact plus one constraints artefact will bite later.**
1 error, 5 warnings.

## Scope handled as the mode requires

`block-only` excludes protection, filtering beyond the datasheet's own,
indicators, test points, config, second rail, mechanical and enclosure-fit.
Nothing below reports any of those as absent. Specifically NOT reported:
missing reverse-polarity diode/FET, missing fuse, missing TVS, missing power
LED, missing test points, missing enable strap, and the absent 0.1 uF ceramic
(the AMS1117 requires no HF bypass - no switch node - and `blocks.md` s.3
records why none is fitted). The owner's answer 3 accepted a destructive
miswire; finding 1 is not about adding protection, it is about the board not
telling anyone which way is right.

## What I verified GREEN (checked, not assumed)

- **Tab identity - the headline risk on this part.** `bb-ldo.net` net `+3V3`
  carries `U1 pin 2 (VOUT_2)` AND `U1 pin 4 (VOUT_4)`, plus C2 pin 1 and J2
  pin 1. The tab is on the output net, not floating and not on GND. The
  footprint `SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR` really does carry a pad 4
  (2.34 x 3.60 mm), so the symbol pin has copper to land on - the "netless tab
  behind green gates" failure mode is not present. Pin 4 is typed `passive`,
  which is why two VOUT pins coexist without an ERC power-conflict.
- **Tantalum polarity, both caps.** Symbol pin 1 is the anode on both
  (`TAJA106K016RNJ` carries a '+' beside pin 1; `293D226X9016D2TE3` draws the
  straight plate + '+' on pin 1 and the curved plate on pin 2). Netlist: C1
  pin 1 -> `+5V`, pin 2 -> `GND`; C2 pin 1 -> `+3V3`, pin 2 -> `GND`. Both
  correct. Footprint silk agrees on both (C1 has a '+' glyph on the pad-1 side;
  C2 has the polarity band and pin-1 dot on the pad-1 side).
- **Cout is treated as a compensation element, not a bypass.** Value string
  `22uF 16V solid tantalum ESR 0.8ohm`, and `decoupling.json` records
  "COMPENSATION element, NOT bypass ... Do not substitute a ceramic or a
  polymer tantalum, and do not change the value." That is the correct reading
  of `linear-regulator-1117-output-cap-esr-window` /
  `linear-regulator-esr-zero-compensation`, and the usual "just use a ceramic"
  defect is absent. 0.8 ohm sits inside the 0.3-22 ohm window (see warning 3
  for the one soft edge).
- **Cin.** 10 uF solid tantalum at VIN, per the record's `cin_uf` / 
  `cin_dielectric`; `decoupling.json` correctly refuses the `reg_input` role
  (that role is for a switcher's hot loop).
- **Abs max vs applied rails (C6186.json).** Input abs max 15 V vs 5.25 V
  worst-case line - 2.9x margin. Tj abs max 125 C vs the 115 C design target;
  the copper area that buys theta_JA <= 65 C/W is the P6 job and is recorded in
  `constraints.json` (`dt_c` 65 kept honest rather than softened to pass
  `check_thermal`). Cap voltage: 16 V on 5.25 V (3.0x) and on 3.3 V (4.8x),
  both above the 2x tantalum floor.
- **Dropout.** 4.75 V low line - 3.3 V = 1.45 V headroom against a 1.3 V MAX
  dropout specified at 0.8 A (we draw 0.51 A), per
  `linear-regulator-fixed-variant-min-load`. Thin but in spec, and it is the
  recorded design.
- **No bleed resistor is correct.** The 1117 minimum-load spec belongs to the
  ADJUSTABLE variant; the fixed part's divider is internal and Kelvin-tied. R1
  was resolved out at P2 on that verified record - re-checked, agreed.
- **No pin-function abuse to find.** The part has no EN, no PG, no ADJ (fixed
  variant), no strapping pins, no open-drain outputs. GND (pin 1) is on GND;
  nothing is floating; no output is shorted to a rail.
- **ERC is not hollow.** `bb-ldo.kicad_pro` ignores only
  `lib_symbol_issues`/`lib_symbol_mismatch`/`footprint_link_issues`; the
  power-pin-not-driven check runs at default severity, so the 0/0 result does
  mean U1's power inputs are driven (the PWR_FLAG block is on the same nets).

## Findings

### 1. ERROR - no polarity legend on either screw terminal (J1, J2)

`connector.md` requires a polarity legend on silk that is visible AFTER
assembly, and requires the reverse-plug consequence to be stated and flagged if
destructive. Here it is destructive and there is no legend. The
`CONN-TH_2P-P5.00_WJ500V-5.08-2P` footprint's entire silk vocabulary is: a body
outline, a `REF**` designator, two identical wire-entry arrows (one over EACH
pin, so they distinguish nothing), and a single 0.2 mm dot at the outline
corner (`fp_circle` r=0.03, width 0.15) that is neither a '+' nor a '-' and
sits at the body edge. The F.Fab pin circles are drawn on BOTH pads. Nothing in
`architecture/`, `requirements.md` or the P0-P3 logs plans any silk text; the
word "silk" does not appear in the design docs at all.

Consequence, on this board specifically: the owner ruled no input protection
(answer 3) with a source that can push 2 A (answer 2). A reversed input puts
-5 V on U1's VIN, a condition its abs-max table does not rate at all (the table
starts at "Input Voltage 15 V" and has no reverse entry), and reverse-biases
C1, a solid MnO2 tantalum, which fails SHORT and can vent with 2 A behind it.
Accepting the absence of protection is not the same as accepting the absence of
the information needed to avoid the fault - the legend is not a protection
feature and is not excluded by the tier.

Remedy is layout-side only and does not reopen the schematic: silk text `+5V`
and `GND` beside J1's two pins and `+3V3` / `GND` beside J2's, placed clear of
the connector body so they survive assembly.

### 2. WARNING - nothing marks which block is the input (J1, J2)

J1 and J2 are the same LCSC part (C8465), the same footprint and the same silk.
Only the `J1` / `J2` designators separate them, and neither says "IN" or "OUT".
Applying the 5 V supply to J2 forces VOUT above VIN; the AMS1117 abs-max table
rates no output-forced-above-input condition, so the outcome is unspecified
rather than merely inefficient. Same remedy as finding 1 - the legend must name
IN/OUT as well as polarity.

### 3. WARNING - C2's ESR has no guaranteed LOWER bound (C2)

The stability window is asymmetric in kind: 22 ohm is a ceiling that "can
usually be ignored", 0.3 ohm is a FLOOR, and per the records the floor is to be
compared against the capacitor's MINIMUM ESR over frequency, not a headline
number. What the workspace actually holds for C2 is `800 mOhm@100kHz` taken
from LCSC's parametric field (`parts.json` role note says so in as many words),
i.e. the series' 100 kHz maximum. No minimum-ESR figure exists anywhere in the
workspace, and no 293D datasheet is in `research/sources/` to read one from.
So the part clears the window on the number available, but the margin at the
end that actually oscillates this regulator generation is unquantified: a
part at the low tail of a max-only distribution, measured above 100 kHz, moves
toward 0.3 ohm.

Not a re-selection demand - `blocks.md` s.6.1's fallback rule was followed and
no surveyed 22 uF part landed inside 0.3-0.5 ohm. It is a demand that bring-up
settle it the way the record says it is settled: a fast load-transient step
with a ring count (<= 4 rings = enough phase margin), recorded as evidence
before this rail is called stable or the record is `--prove`d.

### 4. WARNING - the 12 thermal vias have nowhere to go (U1)

`constraints.json` `thermal[0].min_vias = 12` asks for a 3x4 via array in the
tab pour, while `planes` declares exactly two pours: F.Cu `+3V3` and B.Cu
`GND`. The tab net is VOUT, so `linear-regulator-live-tab-thermal-vias` forbids
stitching that pour to the GND plane ("a via from that pour to a GND plane is a
short, not a heat path"), and `constraints.json` itself says so in
`_net_is_tab` - then requires the vias anyway. As drawn, those 12 `+3V3` vias
land on a bottom side that carries only GND: DRC will hold them clear, so they
buy no heat path and instead punch 12 antipads through the backside copper
directly under the hottest part of the board, weakening the dielectric coupling
that AMS Table 1's backside rows (and this board's 65 C/W sizing) depend on.

Resolve before P6/P7, not at H4: either declare a bottom-side `+3V3` island
under the tab (the record allows a same-net island) and stitch into that, or
set `min_vias` to 0 and take the `check_thermal` finding to the P8 waiver that
`blocks.md` decision 7 already plans, with the copper sweeps as evidence.

### 5. WARNING - C1's symbol is not drawn polarized (C1)

`TAJA106K016RNJ` draws two straight plates - the non-polarized capacitor
glyph - for a solid tantalum on a 5 V rail. The only anode cue is a ~1 mm '+'
polyline, and at render scale it collides with the pin-1 number (it prints as
`+1`). C2's symbol, by contrast, is properly polarized (straight plate vs
curved plate). Today's netlist is correct, so this is not a live defect; it is
the removal of the one visual guard against a reversed tantalum on any future
edit, on the part whose failure mode is a short.

### 6. WARNING - the sheet does not read as a circuit

Read at 900 dpi, the render shows: every net label overlapping its pin number
because the stubs are one grid unit long (`+3V23`, `+5V3`, `GND1` at U1;
`+1`/`2` at C1), the `LCSC` field text drawn straight through the J1/J2 pin
stubs (`C8465` sideways across both) and through U1's value (`C6186` over
`AMS1117-3.3`), and five parts scattered across an A4 sheet with NO wire
between any two of them - all connectivity is by label. A human at bring-up
cannot see from this drawing that C1 sits at VIN and C2 at VOUT, which is the
one thing this schematic exists to show.

Two related facts, same artefact: the labels are LOCAL labels
(`(label "+5V")` x15), while `constraints.json` and `sheets.md` both record
"all three are global power symbols" and "no local labels exist on this board".
It works today - one flat sheet, and the netlist/ERC prove the local labels
merged with the PWR_FLAG'd power symbols - but the recorded contract and the
file disagree, and local labels stop connecting the moment a second sheet
appears.

## Not findings, recorded so the next reviewer does not re-litigate them

- Absent 0.1 uF ceramic, reverse-polarity protection, fuse, TVS, LED, test
  points, enable strap, mounting holes: excluded by `block-only`.
- The `power_no_consumers` netlist_audit warning on `+3V3`: expected, the
  consumer is off-board through J2.
- The PWR_FLAG block in the sheet corner: needed, since `+5V` and `GND` are
  driven only by J1's passive pins.
- Board size: binding is `canonical`, geometry is an OUTPUT, so there is no
  stated dimension to drift from.
