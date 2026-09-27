# Placement benchmark: hwde's placer against the Quilter bar

Backlog item 3 of `docs/competitive-research.md`. `SPEC.md` section 1 sets the bar:
fast-route completion of at least 98% after placement. On the reference 161-net board,
naive simulated annealing reached 93.8% Freerouting completion and Quilter's placement
reached 99.4%.

## Verdict

**Still short of the 98% target, and the cause has moved from legality to room.**
The rerun on current main (after the edge-snap fix, PR #35, and the legal-placement
and DRC-rules fix, PR #37) finished 3 of the 17 boards before this report was
written: stm32-blinky, usb-buck and pd-trigger. All three got a legal seed and a
legal anneal, which the first run never managed on a real board. Each then routed
all but one net: 91.7%, 93.8% and 95.2% net completion, the same band as the
naive-annealing 93.8% on the reference board and short of 98%. rf-term-150w routed
100% with 0 DRC errors after #37 (below). The other boards were still in the queue;
the run keeps going and writes each result to disk, so the table can be finished
from it. No runtime is valid: the load average stayed between 19 and 54 during every
board, against the 12 the brief sets.

**The next placement fix is room for the power nets.** On every board the one net
left unrouted is the board's widest power net (GND, +3V3, VBUS), and route_auto's
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
smallest regression case (12 nets, one GND connection left).

One router defect also showed up, which is not the placer's: pd-trigger has 10
`track_width` errors and 4 `hole_clearance` errors, and route_auto's
`dsn_net_rules` is empty there, so I think its width rules live in the project's
net classes rather than the `.kicad_dru` that #37 reads. I haven't traced it.

## Results

### Rerun on current main (2026-09-27, `bench.py --corpus`)

One board at a time, niced, on the host toolchain. Runtime is wall-clock for the
whole board (strip, seed, anneal, route, DRC). It counts only when the 1-minute
load average stayed below 12 for the whole board, and it never did.

| Board | Nets | Seed | Anneal | Net completion | FR completion | DRC errors / warnings | HPWL, designer -> hwde | Runtime | Load (max / mean) |
|---|---|---|---|---|---|---|---|---|---|
| PCB-0001-A stm32-blinky | 12 | legal | legal | 91.7% (GND unrouted) | 100% | 1 / 60 | 231 -> 171 mm, crossings 21 -> 14 | 289 s, **not valid** | 47.7 / 32.5 |
| PCB-0002-A usb-buck | 16 | legal | legal | 93.8% (+3V3 unrouted) | 41% | 1 / 107 | 358 -> 270 mm, crossings 45 -> 31 | 458 s, **not valid** | 27.9 / 19.4 |
| PCB-0003-A pd-trigger | 21 | legal | legal | 95.2% (VBUS unrouted) | 97% | 16 / 128 | 370 -> 256 mm, crossings 37 -> 17 | 765 s, **not valid** | 53.7 / 31.0 |
| PCB-0009-A rf-term-150w | 2 | legal | legal | 100% | 100% | 0 / 3 | 62.9 -> 59.5 mm (anneal) | not measured | (PR #37 run) |
| 13 other boards | | still queued | | | | | | | |

stm32-blinky's and usb-buck's single error is the unrouted connection. pd-trigger's
16 are 10 `track_width`, 4 `hole_clearance` and 2 unconnected. usb-buck's FR
completion is low, I think because its +3V3 and GND connections go to the inner
planes, which Freerouting left and KRT's finish connected (42 unconnected items
before the finish, 1 after). The rf-term row is the PR #37 rerun
below; this corpus run re-runs it when it reaches it. To finish the table, rerun
the command under Method: it skips every board that has a `result.json`.

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
