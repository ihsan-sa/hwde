# LEARNINGS - bb-ldo (workspace learnings)

Workspace-local. Every entry gets a date, tags (stage tag first: P0-P10), and a
one-line claim as its title. `learnings.py compile --workspace boards/bb-ldo` turns new
entries into `learnings/queue.yaml`; the `promote` verb rules on them.
Research tasks (research.py close) append their entries here automatically.

## 2026-08-16 [P2][research][knowledge][block:B2] research task block-linear-regulator-1: 6 verified record(s) for block:B2
Gap: research block 'linear-regulator': produce its coverage checklist, then populate it
Operating point: {"adjust_kind": "fixed", "board_layers": 2, "cooling_kind": "natural-convection", "copper_oz": 1, "cout_stability_kind": "esr-dependent", "dropout_kind": "standard", "iout_a": 0.51, "pass_device_kind": "bipolar-npn", "pdiss_w": 1.0, "source_kind": "dc-input", "ta_c": 50, "tab_net_kind": "vout", "vin_max_v": 5.25, "vin_min_v": 4.75, "vin_v": 5.0, "vout_v": 3.3}
Missing classes: coverage-checklist

Verified records (second reader signed). Promotion = the research verb's promote step (copies record + sources into the library), then the queue ruling with kind knowledge_record targeting reference/knowledge/records/<id>.yaml, then the owner's approval block:
- linear-regulator-1117-output-cap-esr-window [feedback, decoupling] boards/bb-ldo/research/records/linear-regulator-1117-output-cap-esr-window.yaml
- linear-regulator-copper-is-the-heatsink [thermal] boards/bb-ldo/research/records/linear-regulator-copper-is-the-heatsink.yaml
- linear-regulator-esr-zero-compensation [feedback] boards/bb-ldo/research/records/linear-regulator-esr-zero-compensation.yaml
- linear-regulator-fixed-variant-min-load [selection] boards/bb-ldo/research/records/linear-regulator-fixed-variant-min-load.yaml
- linear-regulator-live-tab-thermal-vias [thermal-via] boards/bb-ldo/research/records/linear-regulator-live-tab-thermal-vias.yaml
- linear-regulator-tab-copper-area-theta-ja [thermal] boards/bb-ldo/research/records/linear-regulator-tab-copper-area-theta-ja.yaml
Draft coverage checklist(s) for the owner to approve:
- linear-regulator boards/bb-ldo/research/checklists/linear-regulator.yaml (5 classes)
Sources (quarantined, sha-pinned in the task ledger):
- research/sources/2304140030_Advanced-Monolithic-Systems-AMS1117-3-3_C6186.pdf tier vendor-layout sha256 189a2651878a <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Advanced-Monolithic-Systems-AMS1117-3-3_C6186.pdf>
- research/sources/lm1117.pdf tier cross-vendor sha256 35892f3a8673 <https://www.ti.com/lit/ds/symlink/lm1117.pdf>
- research/sources/snva036b.pdf tier cross-vendor sha256 4f6aa9be526d <https://www.ti.com/lit/an/snva036b/snva036b.pdf>
- research/sources/slva115a.pdf tier cross-vendor sha256 ebbd820a8378 <https://www.ti.com/lit/an/slva115a/slva115a.pdf>
Task file: boards/bb-ldo/research/tasks/block-linear-regulator-1.json

## 2026-08-16 [P4][schematic][easyeda2kicad][kicad-sch-api] A pulled symbol's reversed pin ANGLES make schlib emit INWARD stubs, and rotating the part is not the fix
`aiee:293D226X9016D2TE3` (C2, the 22 uF compensation tantalum) came out of easyeda2kicad with
its two pin angles backwards relative to its own graphics: pin 1 at x=-5.08 carried angle 180
and pin 2 at x=+5.08 carried angle 0, so both leads are DRAWN away from the plates (connecting
to nothing, 3.5 mm short of the electrode) and `schlib.stub_dir` - which reads outward as the
opposite of the pin angle - emitted both auto-stubs INWARD. Result: the rail and ground labels
land 5.08 mm apart ON the body and render as one run-together string ("+3V3GND") with the rail
label over the plate. ERC is 0/0 and the netlist is correct throughout - a pin's connection
point is its `(at ...)`, which the angle does not move - so NO machine gate sees it; only the
H2 schematic PDF does. The obvious workaround (rotate the cap to a vertical shunt) is WORSE and
already on the ladder: KiCad rotates field TEXT with the symbol while schem_refdes does not, so
a rot-90/270 2-pin passive overprints its own Reference/Value (2026-08-09 entry) - measured here
too, the 22-char value string ran vertically through the refdes and the LCSC field. Fix at the
SOURCE, like the pin-TYPE repair does: `kicad/gen/lib_fixups.py` (idempotent, `--check`
mode, re-run after any lib_pull) rewrites the two angles and trims both lead lengths to 3.81 mm.
Nothing electrical changes - verified by `netlist_audit --compare` against the pre-repair
netlist: 0 differences. Sibling symbol `aiee:TAJA106K016RNJ` (C1, same vendor family, same
pull) has CORRECT angles, so this is per-symbol damage and cannot be assumed away: check any
pulled 2-pin passive by placing it and reading `Sheet._pin_out_dir`, not by reading the file.

## 2026-08-16 [P4][schematic][erc] Hang a rail's power symbol in its own cluster, not on a pin stub, when the IC's pins are on 2.54 mm pitch
`power_symbol_at_pin("U1", "2", "power:+3V3")` puts the symbol's PIN on the stub end and the
symbol BODY (the arrow) extends from there - on the AMS1117's 2.54 mm pin pitch that body lands
on the neighbouring pin's local label, so the rendered sheet shows the +3V3 arrow drawn through
U1 pin 1's "GND" text. Electrically fine (ERC 0/0), unreadable on the PDF. Measured root cause:
every KiCad power symbol is EXACTLY 2.54 mm tall (GND's triangle hangs 2.54 below its pin, the
rail arrows rise 2.54 above), which is exactly the pin pitch - so a symbol on any middle pin
reaches precisely into the neighbouring pin's row, and the geometry is unsolvable by stub length
alone (whichever of two adjacent pins gets the shorter stub, its symbol lands on the other's
wire). The arrangement that works on bb-ldo's final sheet: the middle pin (VOUT) takes the short
stub and its rail symbol, and the neighbour (GND) is routed OFF its own row first - out 1.27,
up, across, then down into its symbol - which is also the only ordering of the three left-side
pins with no wire crossing. `power_flag(net, at=..., sym=..., flag=False)` remains the clean
form for a free-area rail cluster that must not carry a PWR_FLAG.

## 2026-08-16 [P4][schematic][easyeda2kicad] A pulled 2-pin passive names its pins "1"/"2" - KiCad prints those names ON the body, on top of each other
Every easyeda-pulled 2-pin part on this board (both tantalums, both screw terminals) carries pin
NAMES that are the same strings as the pin NUMBERS. KiCad renders names INSIDE the symbol body, so
on a small part both names land at the body centre and overprint each other and the numbers - a
garbled glyph in the middle of every passive, which is what the schematic reviewer saw. Nothing
machine-checkable notices: ERC 0/0, netlist unchanged, `schem_refdes` reports `residue: []` because
pin names are symbol graphics, not fields it places. Fix at the source with `(pin_names hide)` on
the symbol (kept in `kicad/gen/lib_fixups.py`); the NUMBERS stay visible, which is what tells a
reader which end of a polarized part is pin 1. Write the bare-token form `(pin_names hide)` into a
`(version 20211014)` pulled lib - that file's own properties use bare `hide`, not `(hide yes)` -
and kicad-sch-api carries the token through into the schematic's embedded `lib_symbols`.

## 2026-08-16 [P4][schematic][erc][netlist] Two pins of ONE part are two nets on the sheet: a drawn run off the tab left the rail unnamed and ERC stayed 0/0
Redrawing bb-ldo with real wires, the +3V3 output path was drawn from U1 pin 4 (the SOT-223 tab)
through C2 to J2, while U1 pin 2 (VOUT) got the rail's `power:+3V3` symbol. Pins 2 and 4 are the
same node INSIDE the package, but on the sheet they are two separate nodes: the drawn run never
touched the symbol, so it exported as `Net-(C2-Pad1)` and `+3V3` held only U1.2. **ERC reported
0 errors / 0 warnings** - an unnamed net with three pins on it is perfectly legal - and the only
gate that caught it was `netlist_audit --compare` against the pre-redraw netlist. Two rules. (a) A
cosmetic redraw is not verified until the netlist is diffed against the version it replaced;
compare is the gate, ERC is not. (b) When a part exposes one node on two pins, each pin needs its
own connection to the rail - a second power symbol on the drawn run is the cheapest, and is what
joins them globally.

## 2026-08-17 [P7][planes_gen][thermal-via][knowledge] planes_gen would have via-stitched the live SOT-223 tab: its EP heuristic never reads constraints' `min_vias`
`planes_gen` places a thermal-via grid under "the largest NETTED SMD pad per footprint whose area
>= 4.0 mm2 and whose net is a plane net". U1's tab (pin 4, 2.34 x 3.6 = 8.4 mm2) is exactly that,
and its net `+3V3` IS the F.Cu plane net - so the default run drills a grid from the VOUT heatsink
pour straight into the B.Cu GND plane. That is the short forbidden by verified record
`linear-regulator-live-tab-thermal-vias`, and `constraints.thermal[U1].min_vias: 0` does NOT stop
it: grep the script - nothing in `planes_gen` reads `min_vias`, the two numbers never meet. On any
board whose plane net is a live tab net (1117-class VOUT, a high-side FET drain), run
`planes_gen --no-thermal-vias` and let the pour do the cooling by dielectric coupling. Same trap
waits on C2, whose 8.3 mm2 tantalum pads also clear the 4.0 mm2 floor.

## 2026-08-17 [P7][route_auto][stitch_vias][thermal] route_auto's KRT finish connects plane-net SMD pads with TRACES, not vias - on a thermal-pour board that silently eats the heatsink
Freerouting itself stopped at 0.60 completion (2 nets unrouted, all three rungs identical); the KRT
mop-up finished GND and DRC went to 0. But it did it by daisy-chaining the three F.Cu GND SMD pads
(U1.1, C1.2, C2.2) to J1's thru-hole with ~25.6 mm of 0.2575 mm F.Cu trace - straight across the
`+3V3` thermal pour, including a slit between U1 and C2 at 7 mm from the tab. Cost: pour 1210.8 ->
1189.6 mm2 and check_thermal's effective area 592.6 -> 577.1 mm2 (-2.6%), on a board whose whole
margin IS that number. The chain's own answer is in `route_critical`'s report note ("plane is the
trunk; SMD pads stitched by stitch_vias"): rip the KRT GND traces with `route_edit` and run
`stitch_vias`, which puts one via per pad on a ring just past the pad edge, away from the body -
inside the void the pad already cuts in the pour, so they cost ~0 mm2 and leave B.Cu continuous
under the tab. Recovered to 1199.2 / 585.0 mm2 with DRC still 0. On a 2-layer pour board the
stitch therefore has to come AFTER route_auto *and* after ripping what KRT laid, not merely after.

## 2026-08-17 [P7][route_critical][scripts] `--out-report` into a missing directory crashes AFTER the board is already written
`route_critical --out-report boards/bb-ldo/route/route_critical.json` mutated the board (4 +5V
segments landed), then died with a raw `FileNotFoundError` traceback from `checklib.emit` because
`route/` did not exist - no JSON, no facts, exit non-zero on a run that actually succeeded. The
workspace scaffold (`state.py`) creates `routing/`, while the P7 role prompt and every route script
default to `route/`, so the first `--out-report` of a session hits this. `mkdir` the report
directory before the first write; re-running `route_critical` afterwards is safe (it detects
`already_routed` and adds no duplicate copper).

## 2026-08-18 [P6][build-modes][place_metrics][canonical] A PROVISIONAL outline binds placement just as hard as a stated one

`placement.edges` is graded by `place_metrics` against whatever outline is on
the board. At a `canonical` binding the outline at P6 is `board_init --outline
auto`'s number - shelf-pack bbox plus whatever margin the orchestrator picked
- so edge-pinned connectors get pinned to an arbitrary width and the fitted
board inherits it. On bb-ldo that was 88.29 mm against a derived 50 mm: 38.7%
more board for 1.4% less effective thermal copper, with the place gate green
because the connectors genuinely were at the edges of the outline it was
handed.

This is the bb-buck defect mirrored. There a STATED size bound the layout;
here an UNEARNED PROVISIONAL one did, and it is harder to see because no
number was ever declared by anyone.

The order that works is **place -> fit -> silk -> gate**: move the edge parts
to the width the design wants, `board_edit --outline fit`, then gate, so the
edge check is evaluated against the outline the design earned. Worth enforcing
in the recipe rather than remembering.

## 2026-08-18 [P6][silk_place][canonical] silk_place solves against the outline ON the board, so at a canonical binding it must run AFTER the fit

Run before the fit it reported an EMPTY residual list while leaving J2's
refdes 0.925 mm outside the future board edge - visible only by fitting a copy
and running real DRC. Run after the fit, on the same board, it needed 0 moves
and left 0 silk DRC findings. The rev-1 hand-fix of that one refdes treated a
symptom; the defect was sequence.

## 2026-08-18 [P8][stitch_vias][dfm] stitch_vias places vias INSIDE large pads, and its own checker cannot see it

Two compounding defects. (1) `RING_RADII` are measured from the pad CENTRE, so
any pad with a half-extent > 0.65 mm gets its "just past the pad edge" via
placed inside the pad. (2) `via_check` only tests FOREIGN copper, so a via
landing in its OWN pad is never flagged. On JLC economy PCBA - which neither
fills nor plugs vias, with paste apertures equal to the pads - paste prints
over an open barrel and wicks down it at reflow: starved or open joints.

Third defect in the same family: it emits **no F.Cu stub** with a pad via, so
on a board whose top layer has no copper for that net (here GND, because the
top layer is the +3V3 heatsink pour) an off-pad via is orphaned. The tool
should emit stub + via as a pair.

Caught only by a human-style visual review at P8, three stages after the edit.

## 2026-08-18 [P8][planes_gen][assembly] No scripted way to set a per-pad zone connection - hand-soldered pins in a solid pour have no fix

The only `zone_connect` in the skill is planes_gen's ZONE-WIDE
`SetPadConnection`; `route_edit` is add_track/add_via/remove, `place_edit` is
footprint + text. So a through-hole pin sitting in a solid pour cannot be given
thermal relief by any allowed script, and the scripted workaround - a small
higher-priority thermal zone over the pad - is refused by planes_gen's
unconditional `>=80% existing same-net fill` idempotency guard.

Proposal: a `pad_zone_connect {ref, pad, mode}` op on route_edit backed by
`pad.SetLocalZoneConnection`, plus a per-entry force/override on that guard.

Also: a copper-coverage ring test for solid-vs-relief must sample INSIDE the
thermal gap band (r <= pad_r + gap). A ring at r = 1.6 mm reads full copper for
BOTH cases, because KiCad's default 0.5 mm gap lies between r = 1.0 and 1.5 -
the P8 review's relief test proved nothing either way.

## 2026-08-18 [P8][check_current][plane] check_current charges every transition via the whole net's current

It wants >= 1 via per 0.5 A and attributes the full rail current to each via.
On bb-ldo the 0.515 A load return never crosses the three GND stitch vias at
all: it flows J2's GND pin -> B.Cu plane -> J1's GND pin, and BOTH are
through-hole screw terminals whose pins penetrate every layer. Those vias carry
only the regulator's quiescent current and capacitor ripple. Doubling them to
satisfy the heuristic would have spent ~2 mm2 of heatsink pour to silence an
advisory. The check's own message says "per-cluster current unattributed" -
believe that qualifier before spending copper.

## 2026-08-18 [P0][build-modes][thermal] At block-only, thermal is the whole design - and the datasheet's copper table is the spec

Nothing about a 5 V -> 3.3 V linear regulator is interesting except where the
watt goes. The part choice turned on which candidate published a copper-area
-> theta_JA table measured on OUR board class (1 oz FR-4, 2 layer), not on
which had the better headline numbers: the electrically superior MCP1825S was
rejected because its only theta_JA figure is a JEDEC 4-layer number that a
2-layer board cannot reach and its datasheet gives no curve to design against.
Choosing it would have meant sizing the copper with no applicable data - the
exact error the board exists to teach against.
