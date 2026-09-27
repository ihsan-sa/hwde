# Placement benchmark: hwde's placer against the Quilter bar

Backlog item 3 of `docs/competitive-research.md`. `SPEC.md` section 1 sets the bar:
fast-route completion of at least 98% after placement. On the reference 161-net board,
naive simulated annealing reached 93.8% Freerouting completion and Quilter's placement
reached 99.4%.

## Verdict

**Not measured yet.** Only one of the 15 boards finished, and it did not route at all,
so this run cannot say whether the placer meets the 98% bar. The corpus run needs a
quiet box: on 2026-09-27 the load average stayed near 140 on 6 cores, `place_anneal`
got about 4% of a CPU per process, and three boards were still annealing after
20 minutes (the same step took 50 s on bb-ldo earlier in the hour).

A first attempt earlier the same hour is void. Its copper-strip step crashed before it
saved, so every board kept its old routed copper. On bb-ldo that left nine KRT GND stubs,
which sent Freerouting's DSN reader into the known `PolylineTrace.combine` recursion
(`LEARNINGS.md`, 2026-07-23), and route_auto correctly skipped the other rungs of a wedged
DSN. That was the benchmark's fault, not the placer's or the router's. The rerun checks
that no track or via is left before it places anything.

## Results

| Board | Seed | Anneal | Route | Net completion | FR completion | DRC | Runtime |
|---|---|---|---|---|---|---|---|
| PCB-0012-A bb-ldo | ok, 4 s | ok, 50 s | error (exit 2) | none | none | not run | 854 s |
| 14 other boards | not finished inside the run window (see Verdict) | | | | | | |

For comparison, `SPEC.md` 1 asks for at least 98%. Quilter's placement reached 99.4%
and naive simulated annealing 93.8% on the reference board.

## Method

Every board in the boards repo that has a `.kicad_pcb` (15 of 18; `PCB-0006-A` and
`PCB-0008-A` have none) was copied to `/tmp/pbench/<board>/kicad/`. The boards repo
was never written. On each copy:

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
was also running other sessions, so the runtimes are wall-clock under load and
only good for comparing boards with each other.

Two host problems had to be worked around. The host JRE lacks `libXtst`, so Freerouting
died at AWT start-up until the runs set `JAVA_TOOL_OPTIONS=-Djava.awt.headless=true`.
The SWIG DSN export also failed now and then with "wxEntryStart failed" on the shared
Xvfb, so the driver retried the route step up to three times.

Two completion numbers are reported. **Net completion** is route_auto's own `completion`:
the share of routable nets with no unrouted connection in the final DRC. **FR
completion** is Freerouting's connection-level completion from its log
(`fr_completion`), which is the number the Quilter comparison used.
