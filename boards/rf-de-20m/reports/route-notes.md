# rf-de-20m P7 - routing notes

Authored 2026-08-08 by the P7 router. Reproduce with the scripts in
`boards/rf-de-20m/route/` (build order in `route/README.md`).

---

## 1. The premise check said "pour, do not track"

`route_critical --pad-window` exits 1 with **149 findings**: every pad of every
fat net is under its DRU width floor.

| net | DRU floor | widest connectable track at a pad |
|---|---|---|
| `+40V` | 5.50 mm | 3.30 mm (U101.2/.3), 4.29 (C105.1), 4.42 (C207/C209), 5.33 (C208/C210) |
| `/SW` | 11.89 mm | **2.63 mm** (Q201/Q202 drain bars) |
| `/tank/TANK_A` | 8.41 mm | 8.0 (probe cap) |
| `/tank/TANK_B` | 8.41 mm | 8.0 (probe cap) |
| `/tank/RFOUT` | 8.41 mm | **3.87 mm** (J301.5), 6.22 (C319/C322) |

So all five fat nets are **poured**, per `remediations/track_width.md` step 4,
and only the four spiral terminal lands (which sit inside the spirals'
`copperpour not_allowed` rule areas, where a pour cannot go) are tracks.

Three of those four land tracks meet their floor exactly. The fourth does not:

- **`/tank/RFOUT` at L302's east land: 7.651 mm vs an 8.412 mm floor.** The
  corridor there is 9.106 mm wide (L302's winding edge at x 99.539 to the C_m
  bank's GND column at x 108.645); minus 0.8 mm of HV clearance each side that
  leaves **7.506 mm of legal conductor, and the track is 7.651 mm including its
  end caps.** The floor is geometrically unmeetable. It is also **above the
  architecture's own binding number** - `constraints.json` states the AC
  requirement is "~7.2 mm of poured copper on the tank nets" and that the
  IPC-2152 width "is a floor, not a pass ... wrong above ~1 MHz".

## 2. The EPC2019 die fan-in

`aiee_hv_143v_SW` (0.8 mm, from /SW's 143 V peak) applies to the zone filler
and **overrides a zone's local clearance** (measured; see LEARNINGS). The
EPC2019's 7 solder bumps sit on a 0.6 mm pitch with 0.35 mm drain-to-source
gaps, so:

- no pour reaches the die at all - the fill stops 0.20 mm short of the source
  bumps and 0.66 mm short of pin4;
- the only conductor that fits is the bump's own 0.25 mm width.

Built: per FET, **4 GND source escapes** (pin2 west, pin6/pin7 east, pin4
outward) at 0.25 mm, **2 drain escapes** down the drain columns at 0.25 mm, and
**1 rung at 0.45 mm** tying the drains into the /SW pour. Every one of them
lands at exactly **0.35 mm** from the nearest /SW conductor - the land
pattern's own pitch, so no spacing tighter than the 12 pre-approved pad-to-pad
findings is introduced anywhere.

GND has no per-net width rule, so the 8 source escapes cost no `track_width`
findings. `/SW` does, so the 2 drain escapes + 1 rung are `track_width`
findings by construction.

## 3. The +40V bus crosses on B.Cu

On F.Cu the x 39..51 / y 12..34 channel is a **single corridor** that both /SW
(FET drains out to L301) and +40V (bulk -> HF bank -> choke) have to traverse
vertically. Two nets cannot cross on one layer, and /SW owns F.Cu: its loop
area is the derate the whole design rests on.

So the DC bus takes a **B.Cu bridge**, `[42.5, 6.0] .. [51.3, 33.0]`
board-local, outside the heatsink land (which ends at x = 36), with 39 x
0.3 mm vias split between the two ends. In1 and In2 GND are untouched, so the
drive input and the power loop keep their return image.

## 4. The tank corridor

`/tank/TANK_A` leaves the C_s column **above** the bank: the bank's own TANK_B
pads own x 57.0..60.2 from y 36.3 down to y 69.7, and the L301 keepout owns
everything above y 31.7..34.4 there. The surviving lane is **4.6 mm wide at
x 57, narrowing to 1.9 mm at x 60.1** over ~3 mm, then opens into the ~6 mm
perpendicular gap between the two spiral keepouts. At 6.96 A rms that pinch
dissipates ~53 mW.

Per the brief the TANK_A pour is kept narrow where it crosses the B.Cu GND
bridge band and is **not** mirrored onto B.Cu there.

## 5. Deviations and residuals

Reported to the orchestrator rather than forced:

1. `/tank/RFOUT` land track 7.651 mm vs the 8.412 mm floor (s1) - unmeetable.
2. `/SW` die escapes 0.25/0.45 mm vs the 11.894 mm floor (s2) - unmeetable.
3. The +40V bus neck is the B.Cu bridge, not a 5.5 mm F.Cu conductor (s3).
4. U201's OUTH/OUTL fan-out is not planar; OUTL wraps west (see LEARNINGS).
   The turn-off loop is ~2x the turn-on loop's length.

## 6. The gate legs, and the OUTL topology problem

`GATE_Q1` and `GATE_Q2` are **exact copper mirrors** - both 3.441 mm of track
in the same three widths, 1.517 nH each by the microstrip model over In1 at
0.2444 mm. `GATE_ON` is a **single 1.30 mm bar down the mirror axis** that
lands on R203.1 and R204.1 simultaneously, so the two turn-on legs are
literally the same copper.

Loop inductance per FET (microstrip `mu0.h/w`, In1 return at 0.2444 mm):

| path | L | budget |
|---|---|---|
| turn-ON  (OUTH bar 0.982 + die escape 0.768 + leg 0.304) | **2.05 nH** | 1.70 nH |
| turn-OFF (OUTL feed 2.26 + leg 3.56 + die escape/leg 1.21) | **7.03 nH** | 1.70 nH |

Both FETs are identical to the last micron, which is what the +/-0.1 nH
matching spec exists for. The absolute numbers are over budget:

- **0.768 nH of every path is the 0.40 mm die escape** and 0.44 nH of the
  turn-on path is the 0.30 mm escape from U201's 0.2 mm ball - both forced by
  pad pitch, not by routing.
- The turn-off overrun is the **non-planar OUTL fan-out** (s5 item 4). At
  7.03 nH and R = 5.85 ohm the gate loop runs **Q ~ 1.0** (critical damping
  would want ~11.9 ohm), i.e. ~20 % ring on the turn-off edge - which drives
  VGS to about **-1 V against the EPC2019's -4 V limit**, so it is not a
  destruct risk, but it is not the damped edge the architecture asked for.

**Two ways out, for the orchestrator to choose:**
1. Raise R205/R206 from 4R7 to ~10R (BOM only, no layout change). Critical
   damping at 7 nH, at the cost of a slower turn-off.
2. Re-place U201 / R205 / R206 so the OUTL fan-out nests inside OUTH's
   instead of wrapping (P7 -> P6 backward edge).

## 7. Measured coupling the pours add

Computed from the ACTUAL fills, nearest GND plane wins:

| net | added C to GND | as a fraction of its design capacitor |
|---|---|---|
| `/SW` | **27.4 pF** (In1 at 0.2444 mm, 187 mm2) | 6.8 % of the 403 pF C_shunt |
| `/tank/TANK_A` | **13.4 pF** (mostly the B.Cu bridge) | 2.6 % of the 518 pF C_s |
| `/tank/TANK_B` | 0.8 pF | 0.2 % |
| `/tank/RFOUT` | **46.1 pF** (In1 under the zone-C pour, 314 mm2) | 8.7 % of the 531 pF C_m |

**THIS IS A P8 INPUT, NOT A P7 EDIT.** The populate move below is RECOMMENDED
and deliberately NOT applied: it interacts with SIM-4 and with the ~25-35 nH
tank-bridge stray, so it must be re-solved against the simulated network, not
against these numbers alone. P8 owns the decision; P7 changed no component
value for parasitics. (Re-measured on the FINAL fills after the signal
routing: /SW 27.40 pF, TANK_A 13.41 pF, TANK_B 0.82 pF, RFOUT 46.06 pF -
identical to the figures below, because the signal nets are all in zone A and
touch none of the tank pours.)

All three are inside the trim ranges the architecture provisioned, but they
are large enough that the **nominal populate should move**:

- C203-C206 (C_shunt trim, 0-133 pF): ~87 pF nominal -> **~60 pF** (2 x 33 pF).
- C_m bank: 531 pF populated -> depopulate one 56 pF (**475 pF + 46 stray =
  521 pF**, -1.8 % on the 530.4 pF ideal, inside the +/-3 %).
- C_s bank: 13.4 pF is inside C320/C321's +/-54 pF trim range.

The In1 under the RFOUT pour is design intent (`decisions.md` D7 / the
`constraints.json` RFOUT note require it as the return), so the 46 pF is the
price of the mandated return, not a routing defect.

## 8. Acceptance

- `plane_repair`: **pass, no repairs needed** - every pour is electrically
  whole as filled.
- Geometric acceptance on the ACTUAL fills (`route/verify_geom.py`):
  - **B.Cu GND is ONE island, 6002 mm2, spanning x 0.3..119.7** - zone A to
    zone C through the magnetics zone, as `constraints.json` requires.
  - **In1 and In2 carry zero POUR under either spiral** (strict-interior test
    at r - 0.01 mm). The 130-150 mm2 of inner-layer copper inside each disc is
    the spirals' own SPIRAL-4 inner-terminal bridge PAD, which is the
    structure the architecture specifies, not plane fill.
- Freerouting 2.2.4 **wedges** reading this design (rung 1 log stops after the
  version banner; no pass lines, no SES) - the documented failure mode on a
  board already carrying router-generated copper. The remainder is routed by
  KRT at the 0.2 mm floor with an explicit `--net-clearances` map.

## 9. RESOLVED: why Freerouting wedged, and how the last 24 connections closed

The P7 router left 24 ratsnest connections on 10 low-current signal nets
because **both** autorouters failed: Freerouting 2.2.4 stopped after its
version banner with no pass lines and no SES, and KRT `route.py` could not
finish a single net on a 120 x 80 mm outline at any grid (that KRT limit is
real and unchanged - see LEARNINGS). All 24 are now routed. Freerouting did
15 of them; the rest were hand-routed with `route_edit`.

### 9.1 The wedge is DEGENERATE PRE-ROUTED WIRES, not the spirals

The standing hypothesis was the two spiral footprints (49 pads, 1116 / 828
polygon points each). **It is wrong, and it was worth proving wrong.**
`route/fr_spiral_probe.py` + `route/fr_wire_bisect.py` bisect the exported
DSN, 240 s / 90 s per rung (a healthy run prints `Job ... started` at ~1.5 s
and finishes in ~10 s, so a missing `started` line IS the wedge signature):

| variant | DSN change | result |
|---|---|---|
| v0 | as exported | **wedges** (reproduces) |
| v1 | both spiral winding padstacks -> their 2.8 x 8.0 mm land rect | **wedges** |
| v2 | v1 + the four r=20.3/20.55 mm polygon keepouts dropped | **wedges** |
| v3 | `(wiring)` emptied (34 wires + 160 vias gone) | **runs**, 4 passes |
| v4 | wires kept, 160 vias dropped | **wedges** |
| v5 | vias kept, 34 wires dropped | **runs**, 5 passes |
| v6 | only the 4 land tracks wider than 2 mm dropped | **wedges** |
| b09 | the 9 highest width/length wires dropped | **runs** |

So: not the spirals, not the keepouts, not the 160 vias. **It is the
pre-routed WIRES whose WIDTH rivals or exceeds their LENGTH.** Dropping the
nine with aspect >= 0.81 is exactly enough; seven is not. A JFR profile of a
wedged run (70 s, 279 GCs; reproduce with `-XX:StartFlightRecording=
duration=70s,filename=fr.jfr,settings=profile` then `jfr print --events
jdk.ExecutionSample`) puts every hot sample under
`io.specctra.parser.Wiring.read_scope` -> `ShapeSearchTree.insert` ->
`Simplex.intersects` / `Simplex.remove_redundant_lines`, i.e. convex
decomposition of the wire polygons, never reaching pass 1.

The nine are precisely the copper this board is made of:

| net | width | length | aspect |
|---|---|---|---|
| `/tank/RFOUT` land | 7.651 mm | **0.020 mm** | 382 |
| `/tank/TANK_A` land | 8.412 | 0.700 | 12.0 |
| `/SW` rung | 11.894 | 1.200 | 9.9 |
| `/tank/TANK_B` land | 8.412 | 1.200 | 7.0 |
| `GATE_ON` bar | 1.300 | 0.900 | 1.4 |
| `GATE_Q1`/`GATE_Q2` legs (x2) | 1.000 | 0.990 | 1.0 |
| `GATE_ON` feed | 0.700 | 0.750 | 0.93 |
| `GATE_OFF` leg | 0.550 | 0.675 | 0.81 |

**This is a reusable pipeline finding, not a board quirk.**
`remediations/track_width.md` step 4 mandates pour fan-in - a short,
full-width land track into a pour - for any net whose DRU width floor exceeds
what a pad can take. That remedy *produces* wires of exactly this shape, so
any board that follows it will wedge Freerouting on the next pass. The same is
true of a wide gate bar. Freerouting is fine with 160 vias and with a 55-point
concave spiral pad; it is not fine with a 7.651 x 0.020 mm rectangle.

### 9.2 The recipe that worked

`route/fr_signals.py`:

1. export the DSN (In1/In2 **and B.Cu** declared `power` - see 9.3);
2. delete every wire with width/length >= 0.80 from the DSN **only** (they
   stay on the real board; the DSN is just the router's input);
3. run Freerouting - it now reads the design in 1.5 s;
4. **filter the SES down to the 10 nets that needed routing**, because with
   those wires missing FR also "re-routes" nets that are already complete;
5. **convert the session to `route_edit` ops** (`route/ses_to_ops.py`) rather
   than importing it. `ImportSpecctraSES` REPLACES the board's wiring with the
   session's - measured here at **209 -> 89 tracks and 24 -> 44 unconnected**,
   i.e. it deleted the board. route_auto gets away with the import only
   because its DSN carries every existing track as a guide wire, so the SES
   echoes them all back; a thinned DSN plus a filtered SES cannot.

### 9.3 Two things Freerouting got wrong that had to be undone

- **B.Cu.** Left declared as a signal layer, FR put a `+5V_DRV` detour with
  two vias on B.Cu inside the bottom-heatsink land - copper that would short
  to the sink. Declaring B.Cu `power` (it carries one 6002 mm2 GND island AND
  it is the mounting face) forces everything to F.Cu.
- **HV clearance.** FR reads clearances from the DSN, which KiCad writes from
  the `.kicad_pro` NETCLASSES only; the per-net `aiee_hv_*` rules live in the
  `.kicad_dru` and never reach it. Left alone FR ran `/hk/BST` 0.26 mm from a
  +40V pad (rule 0.5) and `+5V_DRV` 0.62 mm from a /SW pad (rule 0.8).
  **Pushing the DRU floors into the staged netclasses RE-WEDGES the reader**
  (0.5/0.8/0.8 -> no `Job started` in 600 s), so `--hv-clearance` exists in
  `fr_signals.py` and is off by default; the affected legs were re-run by
  hand instead.

## 10. The structural blocker underneath it: U201's OUTL wrap is a WALL

Neither router failed for lack of effort on `/stage/DRIVE` and `+5V_DRV`.
The turn-off fan-out has no planar solution (s5 item 4), so P7 ran OUTL west
around U201 as a 0.55 mm **U**: a vertical at x 28.91..29.46 spanning
y 61.485..66.735, and two horizontals at y 61.485..62.035 and 66.185..66.735
running east to x 33.11. That U **encloses U201's ball array, C202 and the
inner gate resistors**, and on F.Cu it has no gate:

- west of the wrap is outside it;
- the only open side is east of x = 33.11, which is the gate-resistor column,
  and the `GATE_ON` bar (1.30 mm wide, y 63.46..64.76) plugs the R203/R204 gap;
- the corridor between the wrap's bottom edge (62.035) and C202's pads
  (62.173) is **0.138 mm**.

`U201.C1` (/stage/DRIVE) and the `C201.1 -> C202.1` link of `+5V_DRV` both
have to cross it. Built: **two short In2 hops under the wrap**, plus one for
`/hk/BST` (see 11). In2 and not In1 on purpose - In1 at 0.2444 mm is the gate
loops' and the drive input's return image and stays whole; In2 is the third
GND layer and the slots cost nothing the design depends on. DRIVE keeps In1
directly above it for its whole length, so its reference is unchanged.

| net | In2 slot | vias | in the heatsink land? |
|---|---|---|---|
| `+5V_DRV` | 1.315 mm | 2 | **yes** |
| `/stage/DRIVE` | 3.359 mm | 2 | **yes** |
| `/hk/BST` | 6.830 mm | 2 | no (x 52.9) |

**FAB NOTE, CARRY TO P9.** The four `+5V_DRV` / `/stage/DRIVE` vias sit inside
the bottom-heatsink contact land (`constraints.placement.keepouts`
[11.635, 49.335, 42.635, 109.335]). HS-2 permits vias there but forbids
**untented** ones - these are non-GND nets and MUST stay tented on B.Cu or
they short to the sink. The board sets no per-via tenting, so the project
default governs; **do not enable via-tenting-off at plot time.**

**If this board is ever re-placed** (the P6 backward edge s5 item 4 already
names it): give U201 its own y-offset from the resistor column, or put the
OUTL resistors on the far side. That removes the wall and these three hops
with it.

## 11. What was hand-routed, and why

`route/finish_signals.py`. Freerouting closed 15 of 24 connections; these were
finished by hand because the corridor FR chose was illegal or did not exist.

| net | what was done |
|---|---|
| `+5V` | L101.2 -> C109.1 is blocked by BUCK_SW's own detour around L101's body. Routed **west and north** instead - x 32..40 / y 70..92 is completely empty - into the existing y = 74.55 trunk. No vias. |
| `+5V_DRV` | FR's dead-end branch (9 mm east into the FET area, 3 dangling stubs, 2 clearance errors against /SW) deleted; C201.1 -> C202.1 rebuilt as the In2 hop. |
| `/stage/DRIVE` | R202.1 -> U201.C1: east of FB201 at y = 56.2, down the 0.27 mm channel between FB201.2 and R205, then the In2 hop. |
| `/hk/BST` | U101.7 -> C107.1. East of U101 is FULL (VCC and FB own the only lane between C106's body and U101's top row; RON's diagonal closes the outside). Routed through the **0.546 mm channel between U101's top-row pads and its exposed pad**, then In2 past the +40V row. |
| `/hk/BUCK_SW` | FR's leg squeezed between U101.1 and U101.2 at 0.30 mm against a 0.5 mm +40V rule, and past C105.1 at 0.33 mm. Deleted; re-run **south of C108** at y = 95.5. Longer (~+8 mm on a 550 kHz, 0.3 A node) but it clears every +40V pad by more than 1 mm. |
| `GND` (U201.B1) | FR's `A1 -> C202.1` diagonal squeezed the GND pour above U201's ball row to **0.25 mm**, which will not fill, and B1 - a 0.2 mm WCSP ball whose only pour access is from the north - went open. Re-routed that link along y = 62.75, restoring a 0.76 mm band. `island_vias.py` re-run afterwards for the two F.Cu GND islands the new copper created. |

Two geometry traps worth recording: a track at x = 52.086 **swallowed** the
GND stitch via at (51.904, 93.17) and stole its net (`via_dangling`), and a
via at (29.85, 63.60) landed 0.584 mm from the GND via at (30.085, 64.135),
under the 0.4995 mm hole-to-hole floor. Both were found by DRC, not by
inspection - **always re-scan existing vias before choosing a lane.**

## 12. Footprint fixes made at P7

- **U101 `SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL-EP2.0` ->
  `SOIC-8-EP_LM5017_TI-MRA08B`.** The four EP thermal vias were **netless**
  plated holes (an easyeda2kicad artefact), which cost 4 `solder_mask_bridge`
  (a no-net hole inside pad 9's mask aperture) plus 4 `clearance` errors
  against pad 9 at 0.25 mm. They are now **pad 9**, i.e. on the exposed pad's
  own net - which is what an EP thermal via IS. All 8 violations clear. They
  remain tented on both faces (mandatory here: a mask-opened via on the bottom
  heatsink face takes solder and breaks flatness). The rename also retires a
  name the descr had already flagged as stale - the EP is 3.10 x 2.41 mm, not
  2.0 x 2.0.
- **J101 `CONN-TH_P5.08_KF128-5.08-2P` -> `..._EDGETRIM`.** J101 sits at
  board-local x = 3.70 rotated -90 because HS-3 keeps its THT pads out of the
  heatsink land, so its wire-entry face hangs 1.6 mm off the board: 6
  `silk_edge_clearance` warnings. Every F.SilkS element past local y = 3.375
  mm (0.2 mm clear of the edge once half the 0.25 mm stroke is allowed for) is
  trimmed or dropped - the body outline's west end, the two side-tab strokes,
  the pin-1 dot and two of the four wire-entry arrows. **The trim is clean**:
  everything removed was over air, and KiCad plots it nowhere. Pads, drills
  and courtyard are untouched, so the courtyard still carries the real body
  extent. No waiver needed.

Both were pushed onto the board with `board_update --netlist` (`swap_new_fp`
rips and re-places at the recorded position), then **re-locked with
`place_edit`** - the swap re-adds unlocked - and U101's Reference field was
moved back to (46.635, 85.75, 90 deg), which the swap had reset to the library
default on top of C106.

## 13. Residual after P7: the 55, as waiver-sidecar entries

`gate.py --gate drc_routed`: **fail, 55** (52 error + 3 warning), down from 93,
and **0 unconnected - routing is 100 % complete (24/24)**. Every one is a
pre-identified waiver class; no new class was introduced.

**No `reports/verify-waivers.json` was written.** `gate.py:load_waivers`
requires a non-empty `approved` (who/when) on every entry and treats waivers as
human artifacts - an agent instruction is not that. The owner signs these off
at H4. The table below is written so it maps **1:1 onto sidecar entries**:
`gate.py:waiver_matches` keys on `check` (or `kind`) + `net` + a `refs`
SUBSET test, so these nine `(check, net, refs)` tuples cover all 55 findings
and nothing else on the current board.

| # | `check` | `net` | `refs` | covers | `reason` |
|---|---|---|---|---|---|
| 1 | `clearance` | `/SW` | `["Q201","Q202"]` | 31 | Intra-EPC2019 die geometry. The land pattern is a 0.6 mm solder-bar row, so drain-to-source gaps are 0.3500 mm by construction, against this board's own `aiee_hv_143v_SW` 0.8 mm rule (IPC-2221 at /SW's 143 V peak). IPC-2221 creepage governs BOARD conductors, not the internal terminals of a manufacturer-qualified 200 V part, and EPC rates the device at 200 V *with that pitch*. No alternative part exists - every eGaN FET in this class has comparable bar pitch. |
| 2 | `clearance` | `GND` | `["Q201","Q202"]` | 13 | Same die, source side: the 0.25 mm GND source escapes sit 0.3500 mm from /SW conductors, which is the land pattern's own pitch. No pour can reach the die at all (a `.kicad_dru` rule beats a zone's local clearance during fill), so hand tracks at bump width are the only conductor that fits. |
| 3 | `clearance` | `/stage/GATE_Q1` | `["Q201"]` | 2 | Q201's gate escape vs its own drain bar, 0.3750 mm - same die geometry, gate-to-drain column. |
| 4 | `clearance` | `/stage/GATE_Q2` | `["Q202"]` | 2 | Q202's gate escape vs its own drain bar, 0.3750 mm. |
| 5 | `track_width` | `/SW` | - | 3 | The EPC2019 drain escapes (2 x 0.2500 mm) and their rung (0.4500 mm) against an `aiee_pwr_width_SW` floor of 11.8942 mm. Geometrically unmeetable: the widest connectable conductor at a drain bar is 2.63 mm. **Pour fan-in per `remediations/track_width.md` step 4 is what is in place** - /SW is one 263 mm2 F.Cu island and these three are the only /SW tracks on the board. |
| 6 | `track_width` | `/tank/RFOUT` | - | 1 | L302's east terminal land, 7.6510 mm against an 8.4123 mm floor. The corridor is 9.106 mm wide and 0.8 mm of HV clearance each side leaves 7.506 mm of legal conductor, so 8.4123 mm cannot exist there. It is also above the architecture's own binding number: `constraints.json` states the AC requirement is ~7.2 mm of poured copper and that the IPC-2152 width "is a floor, not a pass ... wrong above ~1 MHz". |
| 7 | `padstack` | `/tank/TANK_A` | `["L301"]` | 1 | "SMD pad has no outer layers" - L301's deliberate In1+In2 inner-terminal bridge (SPIRAL-4). Measured on 10.0.3: this warning is unavoidable for an inner-only SMD pad. |
| 8 | `padstack` | `/tank/RFOUT` | `["L302"]` | 1 | Same, L302. |
| 9 | `copper_sliver` | *(null)* | - | 1 | KiCad reports **no coordinate and no items** for it, so it cannot be located, inspected or fixed. Unchanged from the P7 baseline and from every fill since. |

One honest caveat on entries 1-2: 22 of those 44 findings are track-to-track
and therefore carry **empty** `refs`, so the subset test cannot exclude a
future /SW-or-GND clearance error that also has empty refs. The waiver cannot
be made tighter through this matcher; the compensating control is that the
count is fixed - if `drc_routed` ever reports more than 55, something new
happened and the delta must be read, not waived.

**Nothing was fixed by loosening a DRU rule.** The `.kicad_dru` regenerated at
P7 is byte-identical to the P6 one (`rules_gen` had to be re-run because
regenerating the schematic wipes `net_settings` out of the `.kicad_pro` - see
the workspace LEARNINGS).

Geometric acceptance re-run on the FINAL fills (`route/verify_geom.py`):
**PASS** - B.Cu GND is one 5999 mm2 island spanning x 0.3..119.7, In1 and In2
carry zero pour under either spiral, /SW is one F.Cu island, and the added
shunt capacitances are unchanged. In1/In2 GND island counts are unchanged from
before the signal routing (3 and 2). `plane_repair`: pass, no repairs needed.

## 14. R205/R206 4R7 -> 6R8 (BOM-only turn-off damping)

Applied in `kicad/gen/stage.py`, rebuilt, and pushed to the board with
`board_update` (field-only; `swap_part_same_fp`, 0 orphans, no geometry
touched, DRC unchanged).

**This value was ruled twice.** P7 was first instructed to fit 10R; the router
measured what that cost and the coordinator overruled the instruction. The
numbers that decided it, all at L = 7.03 nH (the as-routed turn-off loop) and
C_GS = 199 pF, so `sqrt(L/C_GS) = 5.944` and `R_crit = 2.sqrt(L/C_GS) = 11.89`:

| R_ext | R_loop | zeta | Q | overshoot | VGS min | pair P_off | Tj nom | Tj max corner |
|---|---|---|---|---|---|---|---|---|
| 4R7 | 5.85 | 0.492 | 1.02 | 16.9 % | -0.85 V | ~1.0 W | ~119 C | ~138 C |
| **6R8** | **7.95** | **0.669** | **0.75** | **5.9 %** | **-0.30 V** | **~1.85 W** | **~123 C** | **~142 C** |
| 10R | 11.15 | 0.938 | 0.53 | 0.02 % | ~0 V | ~3.6 W | ~132 C | ~151 C |

Turn-off loss scales as R_loop^2 because Class E turn-off is capacitively
snubbed: `E_off = I_off^2 . t_f^2 / (24 . C_shunt)` with t_f proportional to
the gate-loop R. Two independent routes agree on the 4R7 anchor - the board's
own R^2 fit (decisions.md D6's +0.3 W at 4.15 ohm) and a first-principles
estimate (I_off ~10 A total, C_shunt 403 pF, t_f ~2.1 ns -> 0.91 W). Tj uses
this stage's own ~5 C per pair-watt from the E1 note.

**Why 10R was rejected.** 150 C is the EPC2019 ABSOLUTE MAXIMUM. 10R lands the
max-datasheet corner on ~151 C - it spends the entire remaining thermal margin,
on the part whose thermal path was already this board's hardest problem, to
suppress a ring that is not a destruct risk. 6R8 costs ~+4 C and leaves **~8 C**
at that corner. (An earlier estimate of "roughly 12 C of margin" for 6R8 was
optimistic: 150 - 138 - 4 = 8 C, not 12.)

**Be clear that 4R7 was not unsafe.** On the published abs-max numbers 4R7
already passes both rails:

- **-4 V rail:** the turn-off undershoot is -0.85 V, i.e. **4.7x of margin**.
- **+6 V rail: unaffected by this choice either way.** R205/R206 damp the
  NEGATIVE-going edge. The positive rail is set by the OUTH loop, which is
  2.05 nH at 4R7 -> zeta 0.91, 0.1 % overshoot, VGS peaking at ~5.005 V.
- **Spurious re-turn-on:** the first positive recovery of the 4R7 turn-off ring
  is +0.14 V, far below the ~1.4 V threshold.

So what 6R8 buys is margin against what the second-order model does **not**
contain, and that is the honest case for it:

1. **The 7.03 nH is a microstrip estimate, not a measurement.** At 10 nH the
   4R7 ring would be 24 % (-1.21 V); at 6R8 it would be 10.6 %.
2. **Common-source inductance.** The 0.768 nH die escape is shared between the
   gate loop and a 16 A power loop with ~2 ns transitions (~8 A/ns), i.e. a
   `L_common.di/dt` term of the order of volts injected straight into the gate
   loop. A larger series R attenuates it, and the RLC ring model does not
   contain it at all. **This deserves a P8 SIM item** - it was never modelled
   by the architecture.

**If P8 finds both benign, reverting to 4R7 recovers ~4 C and is the cooler
part.** That remains the cheapest thermal lever after bus derating
(36 V / 162 W was already costed at -14 C).

### The part, and a sourcing warning

**ROHM `ESR10EZPF6R80`, LCSC `C5639707`** - 6.8 ohm +/-1 %, +/-100 ppm,
**400 mW**, 0805, **anti-surge thick film**, stock 360, no minimum order,
verified live 2026-08-08.

- Power: the external resistor now takes 6.8/7.95 = **85.5 %** of the turn-off
  half of Qg.VDD.fSW, i.e. 0.077 W typ / **0.107 W max per part**. An 0603
  (100 mW -> 65 mW at a 90 C local board) would repeat the E6 defect, and **so
  would a 125 mW 0805** (~96 mW at 90 C, below the 0.107 W requirement). This
  part is 400 mW -> 306 mW at 90 C = **35 % used**, better margin than the
  250 mW class. Anti-surge is the right family for a gate leg: the 0.63 A edge
  current puts ~2.7 W of instantaneous dissipation in the part for a few ns of
  every 50 ns cycle.
- **SOURCING RISK, CARRY TO P10.** This is the **only** 6R8 0805 at 1 % and
  >= 250 mW with stock at LCSC. Every other 1 % 6R8 reads stock 0 behind a
  451-3317 piece MOQ (KOA `RK73H2ATTD6R80F`, YAGEO `AC0805FR-7W6R8L`, KOA
  `SG73S2ATTD6R80F`, Uniroyal `CS05W4F680KT5E`), and the Stackpole RNCP
  thin-film family used for the rejected 10R option **has no 6R8 at all**.
  Stock 360 against 10 pieces needed clears the 5x50 rule 7.2x, which passes
  but is **the thinnest line on this BOM**. Fallbacks are recorded in
  `parts/parts.json` (Walsin `WF08P6R8JTL` 250 mW but 5 %, ROHM `ESR10EZPJ6R8`
  same body at 5 %, and KOA `SG73S2ATTD8R20F` 8R2 1 % stock 5000 as a
  value-shifted last resort - 8R2 is zeta 0.79 and 2.1 % ring but +1.55 W,
  which leaves only ~4 C and needs a thermal re-check).

TI's >= 2 ohm per-pin floor is still met with room: two branches on OUTL give
6.8/2 = **3.40 ohm**, peak sink current 1.47 A against 5 A capability. The
turn-ON pair stays at 4R7 - that loop is 2.05 nH against the same 1.70 nH
budget, so it needs almost nothing, and slowing the ZVS edge would cost
efficiency for no damping benefit.

## 15. Files

| file | what |
|---|---|
| `route/fr_spiral_probe.py` | the v0-v6 DSN bisection (spirals / keepouts / wiring) |
| `route/fr_wire_bisect.py` | narrows the wedge to the 9 degenerate-aspect wires |
| `route/fr_signals.py` | thin the DSN -> Freerouting -> filter the SES |
| `route/ses_to_ops.py` | SES -> `route_edit` ops (never `import_ses`) |
| `route/finish_signals.py` | the hand-routed remainder + FR's rejects |
| `route/fr2/`, `route/fr3/` | probe and production working dirs + Freerouting logs |
| `route/drc2.json` | the final DRC (55, all waiver candidates) |

---

## 16. P8 ADDENDUM - the copper the verify fixer changed (2026-08-08)

Five copper edits and one zone-outline edit, applied at P8 to close two
`check_current` errors and the +40V ampacity problem underneath them. Full
analysis, measurements and the residual waiver tables: **`reports/verify-waivers.md`**.
`drc_routed` after the pass is **55, unchanged and identical class-by-class**;
`route/verify_geom.py` still PASSes (B.Cu GND one 5999 mm2 island x 0.3..119.7,
In1/In2 zero pour under either spiral); the tank pours' added shunt capacitance
moved by +0.02 pF on TANK_A and by nothing at all elsewhere, so the s7 populate
recommendation is untouched.

### 16.1 The bus strip was a DEAD END, and that is what s3 missed

s3 declares the +40V F.Cu path as "left column -> bottom sweep east -> north past
the buck", with a second rung at board-local `y 31.0..34.2` running x 16.2..51.0
straight into the B.Cu bridge's south via field. **That rung never conducted.**
The `+5V` leg that s11 routed "west and north" for `L101.2 -> C109.1` crosses it
diagonally at x 20.0..23.2 (one 0.200 mm track, uuid `dd1db0c9`), splitting the
fill in two, so 100 % of the bus current took the long way round through the
x 46..51 corridor past the buck - where R104 pinches the pour to **2.50 mm** and
the `/hk/BUCK_SW` horizontal at y 56.2 pinches it to **2.25 mm**, against a
5.500 mm IPC-2152 requirement at 7.0 A.

Measured with a 2-D resistive-sheet solve of the actual copper
(`route/bus_solve.py`, `route/bus_cuts.py`):

| | before | after |
|---|---|---|
| bus R, J101 -> L201, copper at 100 C | 10.393 mOhm | **5.508 mOhm** |
| dissipation at 5.96 A | 369 mW | **196 mW** |
| current in the y 31..34.2 rung | **0 A** | **4.02 A** of 7.0 |
| R104 pinch (2.50 mm) | 2.800 A/mm, dT ~60 C | 1.192 A/mm, dT ~8.6 C |
| BUCK_SW crossing (2.25 mm) | 3.111 A/mm, dT ~76 C | 1.324 A/mm, dT ~10.9 C |
| worst section, equivalent width | 2.25 mm | **5.29 mm** (req. 5.500) |

### 16.2 What was built

| file | what |
|---|---|
| `route/ops_p8_5v_hop.json` | `dd1db0c9` deleted; `+5V` now hops the bus strip on **In2** (0.4 mm, vias at local (19.250, 30.233) and (24.232, 35.215), both >= 0.54 mm clear of the +40V pour). Same batch widens the `+5V_DRV` In2 hop under the OUTL wrap 0.200 -> 0.400 mm (0.3 A needs 0.345 mm on 0.5 oz inner). |
| *(zone outline, edited in place)* | the bus strip zone `(16.2, 31.0, 51.0, 34.2)` becomes a stepped polygon: `y 31.0..34.2` for x 16.2..41.0, `y 29.0..35.6` for x 41.0..41.8, **`y 28.4..35.6` for x 41.8..50.4**. North edge 28.4 keeps 0.8 mm (`aiee_hv_143v_SW`) to the /SW pour, which ends at y 27.5; the 29.0 step clears a GND stitch via at (40.987, 28.138). There is no pipeline op for a zone-outline edit - the board was refilled with `kicad-cli pcb drc --refill-zones --save-board` and re-verified. |
| `route/ops_p8_bridge_vias.json` | second via row at local y 31.3 (0.9 mm pitch): the bridge's south transition goes **8 -> 16** vias against `ceil(7.0/0.5) = 14`. |
| `route/ops_p8_via_move.json` | the 16th via moved (50.1, 32.2) -> (42.9, 30.4); at x 50.1 the pour is clipped to a 0.46 mm tongue by TANK_A's 0.8 mm HV clearance. |
| `route/bus_solve.py`, `route/bus_cuts.py` | the resistive-sheet solve above. `check_current` cannot produce these numbers: `pour_neck` only tests a zone holding >= 2 vias, and it tests each zone separately, so a bus poured as several abutting rectangles with parallel branches is invisible to it. |

**Both via batches had to go onto an UNFILLED board.** On the poured board KiCad
re-derived some of the new vias' nets from the In1/In2 GND plane even though 3 of
the 4 layers under them were +40V, and the loss was **non-deterministic** (batch 1
lost 1 of 8; the same 8 shifted one pitch west lost 4, three of them at
x-positions that had just succeeded). `route_edit` is atomic and post-verified so
both attempts rolled back cleanly. Procedure that works: strip every
`(filled_polygon ...)` block, apply the ops, refill.

**FAB NOTE, CARRY TO P9.** The two new `+5V` vias sit inside the bottom-heatsink
contact land, joining the four `+5V_DRV` / `/stage/DRIVE` vias of s10. HS-2
permits vias there but forbids **untented** ones. **Do not enable
via-tenting-off at plot time.**

### 16.3 What was NOT changed, and why

- **The /SW -> L301 return-path finding is not a defect** and was not "fixed":
  it is the 11.894 mm x 1.200 mm pour fan-in land at the edge of zone B, where
  D4 forbids an inner plane. 27 % of the reported 81.29 mm2 deficit is off the
  board; the /SW **pour** is 96.13 % imaged on In1 and C203-C206 and L202.1 are
  100 % imaged; the unimaged land adds **0.24 nH**, 0.15 % of the 164 nH it
  feeds. `verify-waivers.md` s1.2 carries the derivation.
- **No rule was loosened.** The `.kicad_dru`, the netclasses and every
  `constraints.json` current / dT / clearance are untouched.
