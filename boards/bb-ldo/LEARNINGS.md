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

## 2026-08-20 [P6][planes_gen][board_edit][scripts] planes_gen has no re-pour path: on a board that already has zones and whose outline GREW, it ADDS a duplicate zone - and nothing in the skill can delete a zone

`board_edit --outline WxH` re-clips the existing fills but says plainly that
zone OUTLINES do not follow the edge, so the pour has to be regenerated. Run
`planes_gen` on that board and its idempotency guard - "an existing same-net
fill covering >= 80% of the planned region means skip" (`EXISTING_COVER`) -
reads only 73% here, because the old zone's rectangle stops at the old
boundary. So it ADDS a second `+3V3` F.Cu zone and a second `GND` B.Cu zone,
same nets, same layers, both at priority 0, on top of the two already there.
The fill union is correct (measured 1097.86 mm2 either way) but KiCad DRC
returns two hard `zones_intersect` errors: "intersecting zones must have
distinct priorities".

There is no way out with the sanctioned editors. `route_edit`'s `remove
{uuid}` indexes `board.GetTracks()` only, so a zone uuid comes back "absent"
and then fails the driver's own verify (the uuid is still in the file);
`place_edit` is footprints + text; `board_edit` only removes Edge.Cuts items;
`plane_repair` bridges splits. Nothing exposes `SetAssignedPriority` on an
existing zone either, which would have been the other legal fix.

The recovery that works is `state.py restore --label <a zone-free snapshot>`
and re-running the whole chain (place -> board_edit -> planes_gen -> silk) on
a board that has no zones. On bb-ldo `pre-P7-routing` was exactly that, and
diffing it against the delivered board (ignoring uuids, tracks, vias, zones)
showed a single line of difference - the `HOT SURFACE` legend - which
`place_edit add_text` puts back. So: **before re-pouring a board whose outline
changed, get it to a zero-zone state first**; discovering it afterwards costs
a full rebuild.

Wanted: `planes_gen --repour` (drop the same-net/layer zones it is about to
replace), or a `zone` op on route_edit.

## 2026-08-20 [P6][silk][placement] Centring both edge connectors on a small square leaves no room for pin-adjacent silk - and the binding obstacle is a neighbour's own polarity marker

Honouring `placement.edges pos 0.5` on the 34.655 mm square puts J1 and J2
courtyards 12.655 mm apart, and the U1+C1+C2 cluster only fits that corridor
turned 90 deg. Measured silk-to-silk (centreline + stroke/2, NOT courtyards),
the left channel is 16.270 -> 17.026 = 0.756 mm and the right is 26.957 ->
28.635 = 1.678 mm. A 1.2 mm silk label is 1.4 mm tall, so neither takes one -
and the left channel is narrow not because of a courtyard but because C1's
FOOTPRINT prints a 0.25 mm-stroke `+` polarity cross 3.1 mm out from its
centre, 1.1 mm beyond its own courtyard. Turning the labels 90 deg into the
channels was tried and real DRC rejected it (2 hits on that `+`, 1 on U1's
body line at 0.024 mm).

Two things to carry: courtyard extents are the wrong model for silk clearance
(footprint silk routinely exceeds the courtyard), and when the corridor loses,
the answer is to move the legends OUT - net name above the connector for the
upper pin, below for the lower, function label as the header. That keeps a
3.9 mm / 9.0 mm = 2.3:1 adjacency to the right pad and clears real DRC at 0.

## 2026-08-20 [P7][route_auto][freerouting] Freerouting cannot read this board at all - route_auto has nothing to contribute, so its KRT fallback is the ONLY thing it can do

Re-routing the 34.655 mm square: `route_critical` lays the +5V trunk with KRT,
and Freerouting 2.2.4 then dies with `StackOverflowError` at
`PolylineTrace.combine` while READING the DSN - ZERO pass lines, rung1.log is
75 KB of one repeated frame. That is the documented KRT-guide-wire wedge
(repo LEARNINGS 2026-07-23), and every rung parses the same DSN, so the whole
ladder is dead. `route_auto` therefore has exactly two outcomes on bb-ldo:
`--no-krt-finish` -> exit 2, "board untouched"; or the KRT finish, which is
the pass that daisy-chains the F.Cu GND SMD pads with traces across the
thermal pour (2026-08-17 entry). Running it to then rip what it laid buys
nothing: the deliberate `route_edit` via+stub pairs are the same end state.
Set `--timeout-s` low (120) - the default 600 makes the wedge cost 10 minutes
per rung for a result that is knowable from the first log line.

## 2026-08-20 [P7][stitch_vias][dfm] The in-pad defect reproduces on new geometry - all THREE proposals landed inside their pads

`stitch_vias --dry-run` on the re-placed board proposed (19.151, 29.395),
(23.552, 21.893) and (26.398, 32.252): inside C1.2 by 0.115 mm, inside C2.2 by
0.443 mm and inside U1.1 by 0.0035 mm respectively - measured centre-to-pad-
edge, so with a 0.3 mm land every barrel is wholly within pad copper and paste.
`--dry-run` is the way to see it: the report's `ops` list is the proposal, and
a two-line shapely `pad.poly.contains(Point(at))` test settles it before any
copper moves. The replacement is 5 authored via+stub pairs at 0.55 mm past the
pad edge (0.25 mm copper gap, 0.25 mm mask dam; vias are tented front+back and
`pad_to_mask_clearance` is 0, so the dam is real).

## 2026-08-20 [P7][check_current][plane] Via-redundancy and check_current's clustering pull in opposite directions

U1.1's two barrels sit 1.99 mm apart (N + E of the pad) and check_current reads
them as ONE transition with 2 vias - no warning. C2.2's two sit 4.88 mm apart
(W + E, the point being that one solder void cannot take both) and it reads
them as TWO transitions of 1 via each, warning on both, plus C1.2's single one:
3 advisory warnings. Moving C2.2's pair closer would silence the check and
destroy the redundancy it was placed for. The message carries its own
qualifier ("plane-fed rail, per-cluster current unattributed (each via is a
leaf tap off the plane)") and `drc_routed` does not gate on it - the same
ruling as 2026-08-18. Redundancy wins; the warnings stand.

## 2026-08-20 [P6][build-modes][canonical] Moving the edge parts in fixes the WIDTH; the SHAPE stays inherited

At P6 this board was found to have inherited its width from `board_init
--outline auto`'s provisional 86.29 mm, via `placement.edges` pinning the
connectors to whatever outline was on the board. The fix - move the connectors
inward, then `--outline fit` - corrected the width and was verified. It was
still only half a fix: `fit` wraps wherever the parts ended up, so the ASPECT
remained a property of the provisional rectangle. The board shipped at
50.000 x 26.420 (1.89:1) when the design wanted a square.

A 22-candidate measured study (build each candidate, pour it, measure the real
fill) found:

- The free-aspect optimum is a broad **plateau from 1.00 to 1.47**; r25 varies
  0.4% across it. There is no peak to chase, only a boundary to stay under.
- That boundary is **derivable, not empirical**: check_thermal's reach disc
  plus the pour inset fits wholly on the board only when the short dimension is
  >= 2 x (14.329 + 0.5) = 29.66 mm. At 1321 mm2 that caps aspect at 1.50:1.
  The delivered 26.42 mm height spilled 28.2 mm2 of the disc off both edges.
- `placement.edges` cost **0.00 mm2** at aspect <= 1.47 and only 31.8 mm2 at
  1.89. Its real width floor is ~32.3 mm. **The constraint the finding blamed
  was not the cause** - a 36.35 mm square satisfies J1-left/J2-right with the
  terminals CENTRED at the `pos: 0.5` the constraint actually declares, which
  the delivered board did not honour.
- The square at 1201 mm2 beat the 1321 mm2 rectangle on **all four** measures
  in 9.1% less board, and the rectangle met its own >= 1000 mm2 effective floor
  only on r25 - its r20 was 904 mm2, below it.

Lesson: at a canonical binding, verify the outline's ASPECT is derived, not
just its area. And when a review names a mechanism, measure the mechanism -
this one was wrong while its conclusion was right.

## 2026-08-20 [P8][silk][render] Silk can pass check_silk AND real DRC while being invisible

A relocated refdes was placed in an open pocket that passed `check_silk` (0
violations) and `kc.py drc` (0 violations) - and was completely invisible in
the render, hidden under the through-hole connector's own body, because the
pocket sat inside the footprint's envelope. Both checkers reason about
geometric collision in 2D; neither has a concept of "underneath the part".

Only the render caught it. On any board with tall through-hole parts, a silk
placement is not verified until it has been LOOKED at.

Related, same board: `silk_place --refs J2` reported an EMPTY residual list
while leaving a refdes 0.33 mm from a neighbouring part's pads, reading as that
part's label. Its collision-only scoring treats "close to the wrong part but
not touching" as good enough - `check_silk`'s `silk_misattributed` is the check
that catches it, and it is not what `silk_place` optimises for.

## 2026-08-20 [P7][freerouting] Freerouting 2.2.4 cannot parse this board at all

`StackOverflowError` in `PolylineTrace.combine` while reading the DSN, zero
pass lines, on EVERY rung - they all parse the same DSN, so the ladder is dead
rather than slow. `route_auto`'s only remaining contribution was its KRT
finish, which on a thermal-pour board is the very GND daisy-chain across the
pour that has to be ripped afterwards. Running it with `--no-krt-finish`
reached the same end state without laying and ripping copper.

Consequence worth stating: every trace and via on this board is deliberately
authored, not autorouted. That is fine for five parts and three nets; it would
not scale.
