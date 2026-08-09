# rf-de-20m P7 - route build

`bash route/rebuild.sh` rebuilds every piece of copper on this board from the
P6 placement (it starts with `git checkout` of the `.kicad_pcb`). The order is
NOT arbitrary - two KiCad behaviours force it:

1. **A via added into an already-filled zone takes that zone's net**, not the
   net the op asked for (KiCad re-derives it from connectivity; the fill has
   no antipad yet). So the `+40V` B.Cu bridge vias go in on the BARE board and
   the GND stitch/thermal vias go in while ONLY GND is poured.
2. **A `.kicad_dru` rule beats a zone's local clearance during fill.** The
   0.8 mm `aiee_hv_143v_SW` rule therefore holds every pour off the EPC2019,
   and the die fan-in has to be tracks.

| step | script | what |
|---|---|---|
| 1 | `bridge_vias.py` | 39 x `+40V` vias, bare board |
| 2 | `planes.py gnd` + `planes_gen` | GND: In1/In2/B.Cu + F.Cu blanket + die lobes |
| 3 | `land_tracks.py`, `gate_tracks.py`, `die_fanin.py` | spiral lands, drain escapes, gate legs, source fan-in |
| 4 | `stitch_vias --dry-run` + `stitch_filter.py` | GND stitching, minus anything inside a future power pour |
| 4b | `thermal_vias.py` | the EPC2019 thermal via field |
| 5 | `planes.py pwr` + `planes_gen` | `+40V` / `/SW` / tank pours |
| 6 | - | drop planes_gen's dangling `/SW` vias in L202.2 |
| 7 | `island_vias.py` | one via per orphaned F.Cu GND island |
| 8 | ~~`krt_finish.py`~~ | superseded - KRT cannot finish one net on a 120 x 80 board |
| 8a | `fr_signals.py` | thin the DSN (drop wires with width/length >= 0.8), run Freerouting, filter the SES to the 10 signal nets |
| 8b | `ses_to_ops.py` + `route_edit` | apply the session ADDITIVELY - never `import_ses`, which replaces the board's wiring |
| 8c | `finish_signals.py` | the 9 connections Freerouting could not do, plus its two illegal legs |
| 8d | `island_vias.py` (again) | the F.Cu GND islands the new signal copper creates |
| 9 | `plane_repair`, DRC, `verify_geom.py` | acceptance |

Diagnostics, kept because the finding is reusable: `fr_spiral_probe.py` and
`fr_wire_bisect.py` bisect the DSN and show that Freerouting wedges on
pre-routed wires whose WIDTH rivals their LENGTH - the pour fan-in land tracks
that `remediations/track_width.md` itself mandates - and not on the spirals,
the keepouts or the 160 vias. Full write-up: `reports/route-notes.md` s9.

`apply_ops.py` is a drop-and-retry wrapper around `route_edit` (which is
atomic, and truncates its reject list to 10 per attempt).

Reference measurements and every deviation are in
`reports/route-notes.md`; the two KiCad behaviours above are written up in
the workspace `LEARNINGS.md`.
