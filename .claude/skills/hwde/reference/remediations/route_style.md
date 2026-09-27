# route_style

check_route_style.py found copper that works but is not routed the owner's way:
straight and 45-degree traces, no needless arcs (owner, from the g0-sense render).

- Emitted by: scripts/check_route_style.py via verify_all.py (`kind: "route_style"`,
  severity `warning`, never `error`). The verify gate fails on errors only, so this never
  blocks a board. It is a score: `style` in check_route_style.json holds segments, arcs,
  off_angle, jogs, flagged and `score` = 1 - flagged / tracks.
- Fixer domain: router   Scripts you may use: route_edit.py, kc.py, render.py,
  route_cleanup.py
- Fields: one violation per (net, layer, style). `style` is `arc`, `angle` or `jog`;
  every instance is an entry of `items` with `pos`, a detail in `msg` (arc radius,
  heading in degrees, or jog sidestep in mm) and the track `uuid`.

## Is it real?
- arc: every copper arc counts. An arc a net needs (an RF feed or a diff pair bend the
  constraints ask for) is real intent: leave it and recommend a waiver in the review, do
  not straighten it.
- angle: flagged only when the heading is more than 1 degree off a multiple of 45 AND
  the far end lands more than 0.01 mm off that heading, so coordinate rounding on a short
  stub is not a finding. A short escape into a rotated part's pad can be at the pad's
  angle on purpose; check the render before you move it.
- jog: s1 and s3 on the same heading, joined through a short s2 at two joints with no
  pad or via, and a sidestep under max(track width, 0.25 mm). A sidestep that small does
  not clear anything, but look for a foreign pad or via next to it before you flatten it.

## Fix ladder (cheapest first)
1. Jog: remove s2 (its `uuid`) and the two legs, then add_track one straight segment from
   s1's far end to s3's far end when that line stays clear of other nets. Two route_edit
   invocations: removes first, adds second.
2. Off-angle segment: replace it with a straight leg plus a 45-degree leg between the same
   two endpoints (remove by `uuid`, then two add_track ops meeting at the corner).
3. Arc with no stated intent: replace it with two straight legs and a 45-degree chamfer
   between the arc's end points.
4. A net with many findings (a whole bus or a net route_auto left wandering): stop editing
   and tell the orchestrator the net wants a re-route; give net and layer.

## Do not
- Do not put `remove <uuid at P>` and an `add_*` at position P in ONE ops file:
  route_edit adds before it removes, the add is deduped and the file rolls back. Two
  invocations.
- Do not trade a style warning for a DRC error: a straighter track closer to a pad than
  the clearance is worse than the jog it replaced.
- Do not raise this to an error or add it to a gate. The owner's U11 routing teaching
  is where rules for it come from.

## Verify
```
.venv\Scripts\python.exe .claude\skills\hwde\scripts\route_edit.py --pcb boards\<ws>\kicad\<board>.kicad_pcb --ops work\fix\ops.json --out-report work\fix\edit.json
.venv\Scripts\python.exe .claude\skills\hwde\scripts\check_route_style.py --pcb boards\<ws>\kicad\<board>.kicad_pcb --out work\fix\style.json
.venv\Scripts\python.exe .claude\skills\hwde\scripts\kc.py drc boards\<ws>\kicad\<board>.kicad_pcb --parity --all-track-errors --refill --out work\fix\drc.json
```

## Sources
- Owner routing preference from the g0-sense render: straight and 45-degree traces, no
  needless arcs (docs/competitive-research.md, backlog item 9)
- .claude/skills/hwde/scripts/check_route_style.py - thresholds and the score
- .claude/skills/hwde/reference/remediations/track_dangling.md - route_edit adds before
  it removes
