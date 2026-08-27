# P7 routing - working record (router, iteration 3 resume)

## Resume state found on disk (2026-08-27 ~17:4xZ)
Prior P7 work exists from iter 1 + iter 2 (iter 2's router died backgrounded but its
scripts finished and the iter-2 checkpoint committed the board + artifacts):
- route/pad_window.json (16:05, iter1): route_critical --pad-window PASS - all power pads ok.
  J1 VBUS pads A4B9/B4A9: widest 1.315 mm vs rule 0.8 -> ok=true.
- route/planes_gen.json (16:19, iter1): 9 zones. B.Cu GND 3 zones (744.6+49.7+47.5 mm2)
  with the U3 island window (x>48.15, y 36.5..46.5) left VOID on B.Cu.
  F.Cu VBUS 4 trunk pours (J1 pads -> D1/F1/C1 L-trunk). F.Cu +3V3 2 zones
  (193.6 + 12.2 mm2) = U1 tab pour (obligation C - measured area BELOW the 600 mm2 floor,
  to re-measure after final refill and report).
- route/island_prelay*.json (16:24, iter1): 23 route_edit ops - U3 island necked crossings
  (+3V3 0.15, GND 0.127 + via, SDA/SCL 0.127 neck widening to 0.2) applied+verified.
- route/route_critical.json (17:30, iter2): PASS. +5V routed 1.2 mm F.Cu (KRT 3/3 pads).
  VBUS + +3V3 treated plane-carried (per design). unconnected 41->39.
- route/route_auto.json (17:31, iter2): status violations, completion 0.75,
  unrouted nets [+3V3, /main/SDA, GND, VBUS], best rung 1 (fr_completion 0.854),
  KRT finish tried and DISCARDED (kept=false, would add track_width/hole_clearance errs).
  Emitted a placement_adjust_request - see judgment below.
- Board kicad/g0-sense.kicad_pcb @17:31: 132 segments, 18 vias, 9 zones. In git (iter2 ckpt).

## Judgment on the iter-2 placement_adjust_request
route_auto emitted it because 4 nets remained unrouted after 3 FR rungs - but on the
2-layer chain stitch_vias and plane_repair run AFTER route_auto by design, and 3 of the
4 nets (GND, +3V3, VBUS) are exactly the plane-carried nets those two steps exist to
finish. Escalating P7->P6 before running the rest of the chain would be premature.
Decision: finish the chain (stitch_vias -> refill -> plane_repair -> point fixes),
re-measure, and only escalate if nets remain genuinely unroutable. /main/SDA is the one
real signal suspect - measure the gap and point-fix with route_edit if small.

## Plan (2-layer chain, resume position)
1. Verify obligations on current copper: island voids/necks (B), U-slot check (B),
   VBUS entry geometry + DRC (A), +3V3 tab pour area (C).
2. stitch_vias -> refill -> DRC probe.
3. Snapshot -> plane_repair.
4. Point fixes (SDA etc.) via route_edit.
5. NO route_cleanup (obligation D, S14 2L-pour regression).
6. gate drc_routed until 0/0, completion 1.0.

## Iteration-3 execution record (this session)
Chain position on resume: planes_gen/route_critical/route_auto DONE (iter1+2);
resumed at the post-route_auto point of the 2-layer chain.

1. JUDGMENT on iter-2 route_auto placement_adjust_request: NOT escalated. Its reason
   ("unrouted after 3 FR rungs": +3V3, /main/SDA, GND, VBUS) predates stitch_vias +
   plane_repair, which on the 2L chain run AFTER route_auto and own exactly those
   plane-carried nets. Finishing the chain + point fixes closed all of them:
   final DRC 0 violations, 0 unconnected, gate drc_routed PASS. Request is moot.
2. B4 island audit on the resumed board: found FR had routed SCL *through* the island
   (a second 0.2 mm crossing at y=41.70, U2/R11 -> island -> J2). Contract says four
   necked crossings only. Removed the pass-through (3 segments) and built the I2C trunk
   U2-area -> J2-area on B.Cu (F.Cu corridor is blocked by R12/D10/C3/R3/D2):
   SDA via(41.80,35.90)->B.Cu->via(43.30,48.27); SCL stub + via(42.83,40.40)->B.Cu->
   via(44.30,48.90). First SDA via attempt at (41.57,35.90) shorted an SCL track
   (caught by DRC, moved +0.23 mm east). Final crossing audit: exactly 4 crossings at
   x=49.25: SDA 0.127 / SCL 0.127 / GND 0.127 / +3V3 0.150 (0.15 = aiee_pwr_width_3V3
   lawful minimum). No B.Cu tracks/vias and no pour fill in the tongue (x>49.25).
3. U-slot check (B): ALREADY IN Edge.Cuts from P6 - two 5.5 mm slots from the right edge
   (y 36.85-38.05 and y 44.95-46.15) making the island a tongue with open air on 3 sides
   (slot / board edge / slot). No cut needed; gate place had passed with it.
4. stitch_vias: 13 pad vias + 2 tracks, refilled. C13.2/U3.4 correctly skipped
   (island pads, track-connected). 4 of its vias violated hole_to_hole (0.5 mm floor)
   against existing route vias; 3 were redundant (pads already track-connected to a via
   through multi-segment chains it failed to see) -> removed; D1.2's was needed ->
   moved to (32.80,38.15).
5. VBUS pour join (A): plane_repair's VBUS bridge was catastrophic (0.5 mm tracks through
   J1's body: shorts to no-net pad B8, NPTH hole clearance, 5x track_width vs the 0.8 rule)
   -> snapshot pre-plane-repair RESTORED. Root cause of the split: CC1/CC2 tracks cut the
   planned F.Cu bridge zone, and the CC pads are geometrically boxed (any F.Cu exit crosses
   the bridge strip; dive vias pinch the fill below min width - measured). Fix: VBUS crosses
   on B.Cu: vias (27.65/28.50, 38.90) in the north pour and (27.65/28.50, 44.30) in the south
   pour (2 per side, holes clear of all pad edges), joined by a 0.8 mm B.Cu track. 0.8 =
   aiee_pwr_width_VBUS minimum. DRC clean.
6. plane_repair re-run restricted --net +3V3 --layer F.Cu: 4 groups -> 1 (3 bridges,
   0.25/0.5 mm, all >= the 0.15 +3V3 min; DRC clean). C10.1 connected by a hand 0.15 mm
   track around C11.2 (32.30,35.30)->(33.00,34.90)->(33.00,32.45)->pad.
7. starved_thermal C11.1 + U2.4 (1 spoke vs zone min 2, both geometry-bound: U2.4's west
   end channel is 0.86 mm total which cannot host track+fill+clearances (needs 0.83+ with
   zero margin); C11.1 sits in a narrow pocket): fixed with REAL copper - same-net stubs
   into open fill (U2.4: (35.20,35.52)->(37.00,35.52) 0.2 mm under U2 body; C11.1:
   (32.30,32.05)->(32.30,31.00) 0.15 mm). No zone/DRU/netclass property touched.
8. route_cleanup: SKIPPED (obligation D / S14 2L-pour regression).
9. GATE drc_routed: PASS exit 0, criteria err+warn max 0, total 0, recorded (attempt 1,
   board digest 0b12cafc...). Unconnected = 0 -> completion 1.0.

## Obligation A - final answer (J1 VBUS escape)
- Premise check (route_critical --pad-window, route/pad_window.json): J1 A4B9 and B4A9
  widest escape window 1.315 mm vs rule 0.8 -> ok=true; all other VBUS/+5V/+3V3 power
  pads ok (C1 6.378, D1 3.905, F1 3.124/3.355, U1.3 4.999...).
- CHOSEN: the "better third thing" = pour-carried VBUS (iter-1 planes_gen F.Cu VBUS zones,
  solid pad connection) + this session's B.Cu bridge. Why it beats options (1) and (2):
  * aiee_pwr_width_VBUS is conditioned on A.Type == 'track'; zone fill is not a track, so
    the pour needs NO rule exception (option 1's neck would have) - and the measured fill
    escape east of J1's pad column is a ~1.45 mm band, wider than the 0.8 mm the rule wants.
  * No via-in-pad on the mechanically loaded connector (option 2's JLC wicking risk).
    The 4 bridge vias sit in open pour, holes clear of every pad edge.
  * The two ganged VBUS pads each feed their own pour; the B.Cu bridge (0.8 mm, 2 vias
    per side in parallel) carries only the north pad's share (~half of the 1.5 A PTC-dwell
    fault; 0.25 A steady). DRC 0; no VBUS track below 0.8 anywhere.
- Rule exception needed: NONE.

## Obligation C - measured
+3V3 F.Cu pour after final refill: 145.8 (main, contains U1 tab pad U1.4) + 12.2 = 158.0 mm2
connected as ONE group, vs the constraints floor of 600 mm2. The earned 35.79 x 28.34 mm
outline (1014 mm2 gross) minus the island tongue, J1, MCU, headers and pours for VBUS
cannot fund 600 mm2 of top +3V3 copper - reported, not silently accepted. B.Cu remains
GND-only over U1 (no back-side spreading, no thermal vias), per the recorded decision.
U1 tab connects to the pour with full spokes (no starved_thermal on U1.4).

## Knowledge records applied (cited per contract)
- sht4x-thermal-isolation-island + sht4x-rht-pcb-conduction-principle: island_connections =
  "the four signal/supply traces only, as thin as the fab allows" -> enforced: exactly 4
  crossings (0.127/0.127/0.127/0.150 mm), FR's fifth crossing removed, copper under sensor =
  pin pads only, both layers void in the tongue.
- ldo-sot223-thermal-copper-sets-current: theta_ja references (66 C/W at 1 in2 top 1oz,
  90 C/W headline). Achieved 158 mm2 = 0.245 in2 -> theta_ja lands between those bounds;
  at the 0.51 W design point a rough Tj = Ta40 + 0.51*~80 = ~81 C << 125 C, so the 600 mm2
  shortfall is reportable, not fatal. Formal check is P8 check_thermal's.
- usbc-sink-vbus-tvs-before-series-element: order receptacle -> TVS -> PTC holds (TVS on
  the north pour at the receptacle side, PTC downstream of the pour system). Stub to the
  TVS from the north-pad escape is <1 mm of solid pour; the south pad's share reaches the
  clamp through the 6 mm B.Cu bridge - measured and accepted (pour sheet, sub-nH). TVS GND
  (D1.2) has its own dedicated via hard against the pad edge at (32.80,38.15); a second via
  does not fit (UART_TX/RX tracks box the pad; every candidate spot fails hole_to_hole 0.5
  or under-pad-hole - measured), single-via loop accepted for a VBUS surge clamp.
- usbc-sink-receptacle-land-all-shell-bond: all four shell pads on GND, THT legs into the
  B.Cu plane directly - untouched by routing, verified present.

## Decision texts handed to the orchestrator (for state.py decision, unattended defaults)
1. "unattended default: J1 VBUS escape resolved as pour-carried copper (option 3), no rule
   exception needed - route_critical --pad-window measured J1 A4B9/B4A9 escape windows at
   1.315 mm (>0.8); the F.Cu VBUS pours connect the pads with solid zone connection and a
   ~1.45 mm fill band east of the pad column; aiee_pwr_width_VBUS conditions on
   A.Type=='track' so zone fill is out of its scope by construction, no VBUS track anywhere
   is below 0.8 mm, no via-in-pad was placed on J1 (no JLC wicking remark needed), and the
   two pours are joined by a 0.8 mm B.Cu bridge on 2+2 vias in open pour (holes clear of
   all pad edges). Options (1) necked escape and (2) via-in-pad were both rejected on these
   measurements. Gate drc_routed PASS 0/0."
2. "unattended default: U3 island U-slot obligation satisfied by the P6 outline - Edge.Cuts
   already carries two 5.5 mm slots from the right edge (y 36.85-38.05 and 44.95-46.15)
   making the sensor region a tongue with open air on three sides; no new cut at P7, so
   gate place needed no re-run for outline reasons."
3. "unattended default: U1 tab TOP +3V3 pour delivered at 158.0 mm2 connected (145.8 main
   incl. the tab + 12.2), vs the 600-1000 mm2 constraints floor - the earned 35.79x28.34 mm
   outline (1014 mm2 gross) minus island tongue, J1, MCU, headers and VBUS pours cannot fund
   600 mm2; per ldo-sot223-thermal-copper-sets-current the achieved area still bounds Tj
   around ~81 C at the 0.51 W design point (P8 check_thermal to confirm formally). B.Cu
   stays GND-only over U1, no thermal vias, per the recorded decision."
4. "unattended default: iter-2 route_auto placement_adjust_request (nets +3V3, /main/SDA,
   GND, VBUS, 'unrouted after 3 freerouting rungs') judged premature and NOT escalated to
   P6 - it was emitted before stitch_vias/plane_repair, which own three of the four nets on
   the 2-layer chain; finishing the chain plus point fixes closed all four (DRC 0
   violations, 0 unconnected, completion 1.0, gate drc_routed PASS)."
5. "unattended default: starved_thermal on C11.1 and U2.4 fixed with same-net copper stubs
   into open fill (geometry caps both pads at 1 spoke; measured channels cannot host a
   second spoke lawfully); no zone, netclass, DRU or gate parameter was altered."
