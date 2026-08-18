# Board review - bb-mcu (adversarial, P8)

Reviewer: verify-reviewer subagent, fresh context. All eight machine checks plus
`drc_routed`, `place`, `erc` and `verify` are clean (0/0 throughout, no skips) -
taken as given, not re-litigated. This pass hunts what those scripts cannot see:
renders I made myself (`reports/review-renders/bb-mcu_{top,bottom,iso,left,
right,front,back}.png`, 2400 px), direct extraction of pad/net/track/zone
geometry from the built `.kicad_pcb` via the KiCad 10 Python API, and an
independent re-run of `plane_repair.py --flag-only` against the built board.

**Scope tier applied**: `learning block-basics:` -> `block-only`, binding
`canonical`. Per `reference/build-modes.md` this excludes protection,
filtering, indicators, test-points, config, second-rail, mechanical and
enclosure-fit - none of that is reported below. Geometry is an OUTPUT the
board earned (34.77 x 22.26 mm from a 51.15 x 43.52 provisional outline,
recorded P6 decision); the board is not compared to that provisional number.

**Gate: 0 errors / 2 warnings.**

---

## Findings, worst first

### F1 (warning) - the bottom-right corner, where the wire-tug loads land, has no mounting hole nearby

`kind: unsupported-connector-corner` | domain: `placement` | refs J1, H2, H3

Measured from the built board (bbox 8.98,8.939 to 43.85,31.3 mm): H1 and H2
(top pair) sit at a true 4.0 mm inset from BOTH nearest edges - genuine
corners. H3 and H4 (bottom pair) do not: H4 is 8.2 mm in from the left edge,
and **H3 is 14.3 mm in from the right edge**, because J3 and J1 occupy the
bottom-left and right-edge real estate respectively (`state.json` P6 decision,
correctly earning the board this shape). That leaves the entire bottom-right
corner region - exactly where the screw terminal J1 sits - with no anchor
point closer than 9.2 mm (J1 to H2 measures 9.19 mm, J1 to H3 measures 9.26
mm; both are ordinary distances to the NEAREST hole, but neither hole pins the
corner itself, so that corner can flex/lift under a lever load in a way a true
corner hole would resist).

J1 is not a passive connector here - it is the interface that gets a wire
pushed in, a wire pulled out, and two screws torqued down, repeatedly, at the
bench, every time this board is used (`requirements.md` s1: "let it be
programmed and debugged" implies re-plugging cycles; the terminal itself is
rated for wire pull per its datasheet, but the PCB mounting is what resists
that force being transmitted into the board). Concentrating the least-anchored
corner directly under the highest cyclic mechanical load is the kind of thing
DRC/ERC/placement gates cannot see, because "four M3 holes present" is
satisfied literally (`gate-place` passed `courtyard/outline/edges/keepouts/
decoupler_distance`, none of which score corner support quality).

Not a fabrication defect and not a call to change the earned geometry - FR4 is
stiff at this scale and 9.2 mm is not a dramatic cantilever, so this is not
filed as an error. But it is a real, board-specific bench-reliability question
or the human, worth weighing before the 5 boards see repeated bench use:
either accept it (screws tightened by hand, not a lever-arm concern in
practice), or note it for a respin (nudging H3 a few mm toward the
bottom-right corner, or adding wire strain relief guidance in assembly notes).
Visible in `bb-mcu_top.png` and `bb-mcu_iso.png` - compare H1/H2's tight
corner hugging against H3's isolated position mid-bottom-edge.

### F2 (warning) - a 0.58 mm2 dead copper sliver sits on the GND layer near J3, unconnected to anything

`kind: zero-anchor-copper-island` | domain: `plane` | layer B.Cu | net GND |
refs J3 | pos (10.158, 30.122)

The board brief for this review named this item; I did not take it on report -
I re-ran `plane_repair.py --pcb boards/bb-mcu/kicad/bb-mcu.kicad_pcb
--flag-only` myself against the built board and reproduced it independently:
one GND-net component at 627.14 mm2 with 8 anchors (the real pour), and a
second GND-net component at **0.5822 mm2 with 0 anchors**, centred 0.34 mm
from the main pour's edge, about 0.9 mm diagonally from J3 pin 5 (GND, at
10.8, 29.48) in the board's bottom-left corner.

Electrically this is a non-event: it is DC-floating, far too small and too
close to the reference pour to do anything at the frequencies on this board
(SWD's own worst edge is 5 ns against 2-layer traces under 15 mm - see
`architecture/blocks.md` s3), and `check_pdn`/`check_return_path`/DRC all
correctly see nothing wrong, because nothing electrically IS wrong. The
question is fab hygiene, not function: an unconnected copper sliver 0.34 mm
from its neighbour is closer to a clearance edge case than every other gap on
this board, it has zero purpose (0 anchors means it grounds nothing and
shields nothing), and it is exactly the sort of unexplained artifact a DFM
pass or a human fab reviewer flags for manual sign-off - a turnaround-time
cost for a feature that does nothing. **For the P9 DFM leg**: purge it. It has
no anchors, so deleting it (or raising the zone's island-area removal
threshold past 0.6 mm2 and re-filling) cannot disconnect anything real - this
is a zero-risk cleanup, not a routing change requiring re-verification of
anything else. Not visually distinguishable in the 3D renders at this scale
(both regions are the same copper-green fill); confirmed by direct zone-fill
geometry extraction, not by eye.

---

## Checked and cleared (worst-first hunting, not a rubber stamp on the gates)

**J2 and J3 silk - verified correct and unambiguous on the render, pad by
pad.** This was the hardest item on the hunt list and I did not take
`state.json`'s P6 "silk VERIFIED" decision on report. I extracted the exact
absolute pad coordinates and the exact silk-text anchor coordinates from the
built `.kicad_pcb` (not estimated from pixels) and confirmed every one of the
10 net labels sits with its text-anchor at EXACTLY its pad's X coordinate
(KiCad's default center-justify means this is exact centering, not
approximate): J2 reads, physical pin 1 (right, square pad, silk "1" clear of
the header body) to pin 5 (left): GND / SWCLK / 3V3 / SWDIO / NRST, matching
the P1 ruling exactly. J3 reads pin 1 (top, square pad, silk "1" clear of the
body) to pin 5 (bottom): IO1 / IO2 / IO3 / IO4 / GND, matching the P4-revised
order exactly (see next paragraph). J2's two-row stagger (SWDIO/SWCLK
indented below NRST/3V3/GND) is column-exact per pad, not merely close, and
reads correctly at 2400 px - `bb-mcu_top.png`, crop coordinates roughly
x980-1330,y150-300 for J2 and x650-1000,y300-720 for J3 in the full-res
render. Pin-1 markers (square pads plus an outside-the-body "1" digit) are
present on both and would survive assembly - the exact stm32-blinky failure
mode this board's own architecture doc calls out is not repeated here.

**J2/J3 cross-plug and reversal hazards - independently re-derived, and the
board matches the LATEST decision, not the one in the P4 schematic-review
doc.** `reports/review-schematic.md` W3 (as written) describes J3 as
GND-at-centre and flags a rail short if a cross-plugged cable's centre wire
meets J2's +3V3. That premise is now stale: `state.json` records a **later P4
decision, triggered by that exact W3 finding**, that moved J3's GND from
centre to the end specifically to kill the rail-short case (accepting a
messier reversal case - GND no longer self-maps - as the strictly safer
trade, since a GPIO-to-GND/rail contact is driver-current-limited and a direct
rail short is not). I re-derived the hazard tree against the AS-BUILT pinout
independently (not by reading the decision text) and agree with the ruling:
with J3 carrying no 3V3 pin anywhere, no reversal or cross-plug combination
between these two identical unkeyed headers can short the rail to ground
through the cable itself any more. `architecture/blocks.md`'s block-diagram
mermaid sketch still shows the superseded IO1/IO2/GND/IO3/IO4 order - a stale
diagram in an intermediate doc, not a board defect, since state.json is the
decision record of authority and the built board matches it.

**J2's one-position-slip residual risk (probe driver onto +3V3) - real, known,
accepted, and its only mitigation (silk) checks out.** `state.json` P4 already
worked the alternatives and ruled there is no 5-position order safe against
both a 180-reversal and a one-position slip simultaneously, and accepted the
slip case as the lesser risk with per-pin silk as the sole mitigation. Silk
verified above. Not re-filed as a new finding - re-litigating an already
reasoned, already-accepted, correctly-mitigated risk would be noise, not
signal.

**J1 orientation and polarity silk - verified from an orthographic side
render, not assumed.** `bb-mcu_right.png` shows the wire-entry ports as two
dark rectangular openings facing the camera - i.e. facing off-board on the
edge J1 actually sits on (`placement.edges` says J1 edge=right, confirmed).
`bb-mcu_left.png`/`bb-mcu_back.png` show only the closed screw-access side
from those angles, consistent with a single wire-facing side. Top-down
(`bb-mcu_top.png`, crop ~x1300-1750,y150-720), "+3V3" sits fully clear above
the mounted 3D terminal body and "J1 -GND" fully clear below it - the ~14 mm
body does not encroach on either label once assembled. Screw terminal J1 is a
symmetric, unkeyed 2-pole part (confirmed in its own datasheet extraction);
a 180-degree assembly rotation error is theoretically possible since nothing
mechanical prevents it, but this is inherent to the part class (true of every
unkeyed 2-pin THT connector, mitigated industry-wide by CAD-derived placement
rotation data, not by keying) and not a defect specific to this design -
considered and not filed.

**Mounting hole basics** - all four are 3.2 mm drill (M3 clearance) as
required; none moved off `F.Cu`/board surface; H3's silk reference text was
relocated by an earlier fix pass and reads cleanly with no new collision
(`bb-mcu_top.png`, near x1050-1150,y500-560).

**No part silently flipped to the back.** Queried every footprint's side
directly (`fp.IsFlipped()`): all 14 (U1, C1-C5, R1, J1-J3, H1-H4) report
`front`. Bottom render (`bb-mcu_bottom.png`) shows only THT pin breakout,
mounting-hole clearances and via witness marks on the GND pour - no SMD
footprints - confirming single-sided assembly was actually delivered, not
just specified.

**SWCLK does not run long-and-parallel to the four GPIO** (the one EMI note
`constraints.json` flagged as advisory, unenforced by any check). Extracted
every track segment on `/SWCLK`, `/SWDIO`, `/IO1..4`: SWCLK is one 4.65 mm
segment confined to x=27.5, y=11.0-15.65 (top-right of the package); the four
GPIO traces run entirely in x=10.8-21.5, y=18.92-26.94 (left-center). The
regions do not overlap in X or Y - the architecture's own placement rationale
("maximum distance from SWCLK") holds up in the actual copper, not just in
the placement note.

**C5 (NRST cap, added at P4) is present, correctly wired, and close to its
pin.** Netlist-confirmed: C5 pad 1 on `/NRST`, pad 2 on `GND`, 3.13 mm from
U1 pin 4. Resolves the schematic review's W1 (which predates C5 being added).

**Cross-artifact delivery**: all three stated interfaces present with the
ruled pin orders (J1: pin1=+3V3/pin2=GND; J2: GND/SWCLK/3V3/SWDIO/NRST; J3:
IO1/IO2/IO3/IO4/GND, all confirmed against the netlist, not the schematic
picture). Both architecture blocks (B1 MCU minimum system, B2 SWD debug port)
are present with every datasheet-required part (C1-C4, R1) on the right nets.

**One stray B.Cu track, checked and cleared**: exactly one non-zone track
exists on the bottom copper layer (1.75 mm, net GND, x=29.55 near C1). It is
on the SAME net as the surrounding pour, so it cannot split or interrupt
anything and is not a "signal routed on the bottom" violation - almost
certainly a via-stitch leftover from routing. Not filed.

---

## Open / could not fully judge

1. **F1's severity is a bench-use-frequency judgment call**, not something a
   render settles definitively - how hard this board actually gets handled
   determines whether 9.2 mm-from-nearest-hole at an open corner matters in
   practice. Flagged with reasoning; the call is the human's.
2. **F2's exact fab risk** (whether a 0.34 mm gap survives JLC's process
   without bridging, or whether their DFM software auto-flags it) needs the
   actual P9 DFM/fab-rules pass, not a review render - I can confirm the
   geometry and the recommended action (purge, zero risk) but not JLC's own
   tolerance behavior.
3. Did not re-render or re-read `reports/schematic.pdf` directly - relied on
   the existing P4 schematic review plus my own direct netlist/pad extraction
   from the built board (which is generated from the same schematic and is at
   least as authoritative for the electrical facts I needed to check).
4. Screwdriver/standoff ergonomic access at H2 given J1's ~14 mm height:
   judged workable from the render (~2-2.5 mm clear lateral gap to the
   terminal body) but not physically tested.
