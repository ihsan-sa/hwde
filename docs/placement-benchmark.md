# Placement benchmark: hwde's placer against the Quilter bar

Backlog item 3 of `docs/competitive-research.md`. `SPEC.md` section 1 sets the bar:
fast-route completion of at least 98% after placement. On the reference 161-net board,
naive simulated annealing reached 93.8% Freerouting completion and Quilter's placement
reached 99.4%.

## Verdict

**Does not meet the spec on what finished.** Two of the 15 boards got through
placement and routing. bb-ldo routed 100% with no DRC errors, but rf-term-150w routed
only 50% (one of its two nets) with 17 DRC errors, and the cause is the placer. Both
are tiny boards (3 and 2 nets), so neither result says much about the 161-net
reference board that the 98%, 99.4% and 93.8% numbers come from. The other 13 boards
were still placing when the run window closed. Runtime was not measured: the box's
load average stayed between 135 and 160 on 6 cores all morning, so any time recorded
here measures the box, not the placer.

**The next placement fix is in `place_seed`'s edge snap.** `place_edge_clusters`
pushes a declared-edge cluster until its outermost courtyard point sits on the
board edge ("courtyard flush with the edge"). That is wrong for a part whose courtyard
is meant to hang off the board. rf-term's J1 is an SMA whose barrel courtyard runs
12 mm past its origin, and `constraints.json` says so (`rot 0 ... puts the 8.6 mm
barrel off-board`). The seed pulled J1 7.7 mm into the board (y 32.51 mm against the
designer's 24.81 mm), where it overlapped R1 by 30.3 mm², and J1's satellite C1 was
pushed 77.6 mm² off the right edge. `place_anneal` then found no legal candidate, so
route_auto routed an illegal placement. The designer's own placement of the same
board passes `place_metrics` with no violations, so the constraints are satisfiable.
The fix is to snap an edge part by its on-board body (or by the edge fraction
`placelib` already allows to overhang) and to leave satellites out of the outward
extent. rf-term-150w is the regression case.

One router defect also showed up, which is not the placer's: route_auto laid the
routed part of rf-term's `/RF` at 0.2 mm against the board's 0.94 mm minimum-width
rule (3 `track_width` errors).

A first attempt earlier the same morning is void. Its copper-strip step crashed before
it saved, so every board kept its old routed copper. On bb-ldo that left nine KRT GND
stubs, which sent Freerouting's DSN reader into the known `PolylineTrace.combine`
recursion (`LEARNINGS.md`, 2026-07-23). That was the benchmark's fault, not the
placer's or the router's. The rerun checks that no track or via is left before it
places anything.

## Results

| Board | Nets | Seed | Anneal | Net completion | FR completion | DRC errors / warnings | Placement quality (HPWL, designer -> hwde) |
|---|---|---|---|---|---|---|---|
| PCB-0012-A bb-ldo | 3 | legal | legal | 100% (3/3) | 100% | 0 / 16 (silkscreen only) | 74.2 -> 66.6 mm, crossings 2 -> 1 |
| PCB-0009-A rf-term-150w | 2 | 2 violations | no legal candidate | 50% (1/2) | 100% | 17 / 8 | 54.4 -> 68.5 mm, crossings 1 -> 2 |
| 13 other boards | | not finished in the run window | | | | | |

rf-term's DRC errors: 4 copper-edge clearance, 3 track width, 3 PTH inside courtyard,
2 solder-mask bridges, and one each of short, hole clearance, clearance, courtyard
overlap and unconnected. Its 100% FR completion and 50% net completion disagree
I think because the copper Freerouting laid for `/RF` is shorted to GND in the final
DRC, so the net does not count as connected; I haven't traced it further. Net completion
is the number to trust there.

For comparison, `SPEC.md` 1 asks for at least 98%. Quilter's placement reached 99.4%
and naive simulated annealing 93.8% on the reference board.

## Method

Every board in the boards repo that has a `.kicad_pcb` (15 of 18; `PCB-0006-A` and
`PCB-0008-A` have none) was copied to `/tmp/pbench2/<board>/kicad/`. The boards repo
was never written. Boards ran niced, and each wrote its result to disk as it
finished, so a later run skips the finished ones. On each copy:

1. Strip copper: every track, arc and via was removed through pcbnew SWIG, and the
   earlier `route/`, `route_probe/`, `route_critical/` and `anneal/` work dirs were
   deleted. Zones stay, because they are the planes route_auto routes to. Locked
   footprints stay locked, since a lock is the designer's placement intent.
2. `place_seed.py --pcb B --apply` with the board's own `constraints.json` and
   `decoupling.json`.
3. `place_anneal.py --pcb B --apply-best` at its defaults (3 candidates, seed 1,
   no route feedback).
4. `route_auto.py --pcb B` at its defaults (the three-rung Freerouting ladder, 600 s
   per rung, the KRT finish, then `kicad-cli pcb drc --schematic-parity
   --all-track-errors`). No `route_critical` pass ran first, so every net was left
   to the autorouter. That is the harder case, and the one the Quilter number measures.

Toolchain: host KiCad 10.0.6 from `~/.local/kicad10`, Freerouting 2.2.4 on Temurin 25,
KiCadRoutingTools 0.19.0, Xvfb `:99`. Three boards ran at a time on a 6-core box that
was also running other sessions at a load average near 140, so no runtime is reported.
To finish the corpus, rerun the driver on a quieter box; it skips any board whose
`summary.txt` already has a `total s=` line.

Two host problems had to be worked around. The host JRE lacks `libXtst`, so Freerouting
died at AWT start-up until the runs set `JAVA_TOOL_OPTIONS=-Djava.awt.headless=true`.
The SWIG DSN export also failed now and then with "wxEntryStart failed" on the shared
Xvfb, so the driver retried the route step up to three times.

Two completion numbers are reported. **Net completion** is route_auto's own `completion`:
the share of routable nets with no unrouted connection in the final DRC. **FR
completion** is Freerouting's connection-level completion from its log
(`fr_completion`), which is the number the Quilter comparison used.
