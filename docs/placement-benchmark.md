# Placement benchmark: hwde's placer against the Quilter bar

Backlog item 3 of `docs/competitive-research.md`. `SPEC.md` section 1 sets the bar:
fast-route completion of at least 98% after placement. On the reference 161-net board,
naive simulated annealing reached 93.8% Freerouting completion and Quilter's placement
reached 99.4%.

## Verdict

**Still short of the 98% target: 5 of the 14 boards that routed reached it.**
The corpus rerun finished 16 of the 17 boards. rf-term-150w, bb-mcu, bb-ldo, bb-amp
and bb-adc routed 100%, and all of those are small (2 to 15 nets). Ten boards got a
legal anneal. On the other six the anneal found no legal placement, so they routed
the seed placement: four of them left 3 to 8 nets each (57% to 73%). The two lumina
boards did not route at all: Freerouting produced nothing usable and the KRT fallback did not help. The
17th board, astra-amp, was renamed to stereo-class-d-amp in the boards repo while the
run was going, which crashed the run; bench now records such a board as failed and
goes on, and stereo-class-d-amp has not been benchmarked. No runtime is valid,
because the load average peaked between 28 and 785 during every board, against the
12 the brief sets.

**The next placement fix is room for the power nets.** On every board with a legal
placement that did not route fully, exactly one net was left, and it was a power or
ground net: GND on stm32-blinky, +3V3 on usb-buck and VBUS on pd-trigger and both
pd-trigger-lite boards. On the three pd-trigger boards VBUS is also the widest net
class (1.75 and 1.248 mm). On stm32-blinky GND has only the default width, and on
usb-buck +3V3 shares the widest power class with VBUS, so "the widest power net"
holds on three of the five, and "a power or ground net" on all five. Where the
anneal found no legal placement the widest nets fail too (`/SW` and the tank nets
on rf-de-20m, `/SW` on sbuck-5v3a), along with some signals. route_auto's
own `placement_adjust_request` names that net and asks for the clusters around it
to be spread apart. The anneal packs each board far tighter than its designer did:
HPWL fell 26%, 25% and 31% below the designer's placement (231 -> 171 mm,
358 -> 270 mm, 370 -> 256 mm), and the designer's looser placements of the same
boards route fully. The anneal's congestion term is blind to exactly these nets:
it leaves GND out of the flight-line demand entirely, counts a power net at half
a signal (`MST_PWR = 0.5` in `place_anneal.py`), and counts each net as one track
whatever its width. Its route feedback (`--route-feedback`) is off by default, so
nothing else tells it that a wide power net needs a channel. The fix is to charge
power and ground nets their track width in the congestion demand, or to turn
route feedback on by default and feed it route_auto's `placement_adjust_request`. stm32-blinky is the
smallest regression case (12 nets, one GND connection left). PR #42 has since made the anneal
charge each net its width. The first four boards finished before #42 merged; I can't
tell which code the later boards ran, so this run does not measure #42.

One router defect also showed up, which is not the placer's: pd-trigger has 10
`track_width` errors and 4 `hole_clearance` errors, and route_auto's
`dsn_net_rules` is empty there, so I think its width rules live in the project's
net classes rather than the `.kicad_dru` that #37 reads. I haven't traced it.

## Results

### Rerun on current main (2026-09-27, `bench.py --corpus`)

One board at a time, niced, on the host toolchain. Runtime is wall-clock for the
whole board (strip, seed, anneal, route, DRC). It counts only when the 1-minute
load average stayed below 12 for the whole board, and it never did. Where the anneal
found no legal placement, the hwde HPWL is the seed's.

| Board | Nets | Seed | Anneal | Net completion | FR completion | DRC errors / warnings | HPWL, designer -> hwde | Runtime | Load (max / mean) |
|---|---|---|---|---|---|---|---|---|---|
| PCB-0001-A stm32-blinky | 12 | legal | legal | 91.7% (11/12), unrouted GND | 100% | 1 / 60 | 231 -> 171 mm, crossings 21 -> 14 | 289 s, **not valid** | 47.7 / 32.5 |
| PCB-0002-A usb-buck | 16 | legal | legal | 93.8% (15/16), unrouted +3V3 | 41% | 1 / 107 | 358 -> 270 mm, crossings 45 -> 31 | 458 s, **not valid** | 27.9 / 19.4 |
| PCB-0003-A pd-trigger | 21 | legal | legal | 95.2% (20/21), unrouted VBUS | 97% | 16 / 128 | 370 -> 256 mm, crossings 37 -> 17 | 765 s, **not valid** | 53.7 / 31.0 |
| PCB-0004-A lumina-carrier | - | 7 violations | none legal (3 on best) | route failed | - | - | 3535 -> 4639 mm, crossings 601 -> 957 | 8478 s, **not valid** | 515.2 / 45.1 |
| PCB-0005-A lumina-par | - | legal | legal | route failed | - | - | 2403 -> 1578 mm, crossings 420 -> 285 | 11224 s, **not valid** | 784.7 / 81.7 |
| PCB-0007-A rf-de-20m | 20 | legal | none legal (27 on best) | 60.0% (12/20), unrouted +40V, /SW, /stage/GATE_Q1, /stage/GATE_Q2, /tank/RFOUT, /tank/TANK_A, /tank/TANK_B, GND | 23% | 49 / 75 | 700 -> 700 mm, crossings 41 -> 41 | 1262 s, **not valid** | 436.6 / 78.8 |
| PCB-0008-B sbuck-5v3a | 15 | legal | none legal (3 on best) | 73.3% (11/15), unrouted +5V, +VIN, /SW, GND | 79% | 15 / 55 | 234 -> 345 mm, crossings 11 -> 23 | 688 s, **not valid** | 79.8 / 44.3 |
| PCB-0009-A rf-term-150w | 2 | legal | legal | 100.0% (2/2) | 100% | 0 / 3 | 54 -> 59 mm, crossings 1 -> 1 | 102 s, **not valid** | 80.2 / 63.0 |
| PCB-0010-A bb-buck | 7 | 2 violations | none legal (2 on best) | 57.1% (4/7), unrouted +5V, /FB, GND | 85% | 17 / 31 | 125 -> 157 mm, crossings 7 -> 10 | 301 s, **not valid** | 73.7 / 55.7 |
| PCB-0011-A bb-mcu | 10 | 2 violations | none legal (1 on best) | 100.0% (10/10) | 100% | 3 / 63 | 161 -> 172 mm, crossings 9 -> 16 | 169 s, **not valid** | 53.2 / 48.6 |
| PCB-0012-A bb-ldo | 3 | legal | legal | 100.0% (3/3) | 80% | 0 / 10 | 74 -> 73 mm, crossings 2 -> 4 | 109 s, **not valid** | 87.4 / 62.8 |
| PCB-0013-A bb-amp | 11 | legal | legal | 100.0% (11/11) | 100% | 0 / 41 | 166 -> 229 mm, crossings 11 -> 19 | 176 s, **not valid** | 83.2 / 66.7 |
| PCB-0014-A bb-adc | 15 | legal | legal | 100.0% (15/15) | 100% | 0 / 0 | 229 -> 229 mm, crossings 16 -> 16 | 47 s, **not valid** | 56.6 / 55.4 |
| PCB-0015-A g0-sense | 16 | 7 violations | none legal (2 on best) | 68.8% (11/16), unrouted +3V3, +5V, /main/NRST, GND, VBUS | 100% | 36 / 166 | 243 -> 356 mm, crossings 26 -> 59 | 627 s, **not valid** | 76.3 / 41.5 |
| PCB-0016-A pd-trigger-lite | 11 | legal | legal | 90.9% (10/11), unrouted VBUS | 100% | 4 / 6 | 103 -> 80 mm, crossings 9 -> 4 | 342 s, **not valid** | 66.0 / 44.0 |
| PCB-0016-B pd-trigger-lite-dip | 12 | 3 violations | legal | 91.7% (11/12), unrouted VBUS | 90% | 5 / 23 | 129 -> 96 mm, crossings 9 -> 9 | 350 s, **not valid** | 67.7 / 45.0 |
| PCB-0017-A astra-amp | | not run: renamed to stereo-class-d-amp in the boards repo mid-run | | | | | | | |

stm32-blinky's and usb-buck's single error is the unrouted connection. pd-trigger's
16 are 10 `track_width`, 4 `hole_clearance` and 2 unconnected. usb-buck's FR
completion is low, I think because its +3V3 and GND connections go to the inner
planes, which Freerouting left and KRT's finish connected (42 unconnected items
before the finish, 1 after). bb-mcu routed fully on a placement with one courtyard
overlap left, so its 3 DRC errors are 2 courtyard overlaps and a PTH inside a
courtyard. To bench stereo-class-d-amp, rerun the command under Method: it skips
every board that has a `result.json`.

### First run (13 boards unfinished at load ~140)

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

### rf-term-150w after the edge and hole fixes (2026-09-27)

After PR #35 fixed the edge snap, rf-term routed 100% with 13 DRC errors and 4
warnings, and the anneal still found no legal placement: only two of the three M3
holes fit. Three causes, all fixed:

- `place_seed` read an edge part's `pos` as a fraction of the cluster-centre span,
  so J1 and R1 sat at x 30.5 mm where the constraints meant their origin at 0.375 of
  the edge (x 34.0). It now reads `pos` as the fraction of the edge where the part's
  origin sits, clamped so its pads keep their copper-to-edge clearance.
- The seed kept every courtyard 0.8 mm inside the outline. The shipped board packs
  its holes 0.2 mm off the edge, and the rule that matters is the board's
  copper-to-edge clearance (0.3 mm). `placelib.edge_keep` now gives how far a
  courtyard must stay in so its pad copper clears that rule. The seed legalizes the
  holes against it and searches from the nearest corner, and the anneal and the
  courtyard-flush edge snap both honour it. That also removes the three R1 pad
  edge-clearance errors the flush snap caused.
- route_auto's DSN ignored the `.kicad_dru` per-net rules, so `/RF` routed at the
  default width and clearance (4 width and 3 clearance errors). The DSN now gives
  each net with a DRU width or clearance its own class.

Rerun on a stripped copy: seed legal, anneal legal (HPWL 62.9 -> 59.5 mm), 100%
completion, **0 DRC errors** and 3 warnings. All three warnings are silkscreen
(H2's reference clipped by mask, C1 and R1 silk clipped by the edge).

## Method

`bench.py --corpus WORK` runs it (steps in `lib/benchcorpus.py`). Every board in the
boards repo that has a `.kicad_pcb` (17 of 19; `PCB-0006-A` and `PCB-0008-A` have
none) is copied to `WORK/<board>/kicad/`, and the boards repo is never written. The
rerun used `~/.cache/hwde-pbench4`:

    . ~/.local/kicad10/hwde-env.sh
    ~/.local/hwde-venv/bin/python .claude/skills/hwde/scripts/bench.py \
        --corpus ~/.cache/hwde-pbench4 --out ~/.cache/hwde-pbench4/summary.json

Boards run one at a time under `nice`, under a `WORK/.lock` flock, with the run's
own Xvfb display. Each writes `WORK/<board>/result.json` the moment it finishes,
and a later run skips any board that has one (`--rerun A,B` redoes named boards).
A sampler reads the load average every few seconds while a board runs, and
`runtime_valid` is true only when its maximum stayed below 12. On each copy:

1. Strip copper: every track, arc and via is removed through pcbnew SWIG, and the
   earlier `route/`, `route_probe/`, `route_critical/` and `anneal/` work dirs are
   deleted. The run refuses to go on if the saved file still holds a track or via. Zones stay, because they are the planes route_auto routes to. Locked
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
KiCadRoutingTools 0.19.0. The first run used an uncommitted script, three boards at a
time at a load average near 140, and the shared Xvfb `:99`.

Two host problems are worked around. The host JRE lacks `libXtst`, so Freerouting
runs with `JAVA_TOOL_OPTIONS=-Djava.awt.headless=true`. The SWIG DSN export fails now
and then with "wxEntryStart failed", so the route step is retried up to three times.
A second `pcbnew.LoadBoard` in one process returns a bare `SwigPyObject`, so the
leftover-copper check reads the saved file instead of reloading it.

Two completion numbers are reported. **Net completion** is route_auto's own `completion`:
the share of routable nets with no unrouted connection in the final DRC. **FR
completion** is Freerouting's connection-level completion from its log
(`fr_completion`), which is the number the Quilter comparison used.
