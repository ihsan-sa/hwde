# Knowledge ladder triage (T4, 2026-08-06)

One row per `LEARNINGS.md` entry (175 of them; the last starts at
line 2226), placed on the maturity ladder from
`design/routing-knowledge-notes.md` section 6, with the artifact that owns - or
must own - it.

The failure mode is knowledge sitting at the WRONG LEVEL, not knowledge volume:
**if a script can check it, it does not belong in the prompt.** This register is
the outer-loop worklist. `open` rows (72) are the gaps nothing owns yet -
they are the input to T6 (per-stage deep evaluation) and to any later step
looking for the next promotion.

## Levels

| L | Form | Context cost | Guarantee |
|---|---|---|---|
| L0 | prose in a prompt, or written down only in LEARNINGS | every run | a hope |
| L1 | a script measures it and reports the number | zero | you find out afterward |
| L2 | a check with a failing threshold - a gate fails on it | zero | it cannot ship broken |
| L3 | a generator/pin/template makes it correct by construction | zero | it cannot be built broken |

## Statuses

- **done** - already at target; the named artifact really encodes it (grep-verified).
- **planned-T`<N>`** - the v2 plan step that already owns the promotion.
- **open** - a real gap no plan step owns. Also used when the LEVEL is right but
  the owning artifact is wrong or incomplete (those rows read `Lx -> Lx` with the
  residual in the Note).
- **n/a** - cannot climb: external-service behaviour, a human/process step, or a
  host fact already recorded once.

## Summary

| Level | now | target |
|---|---|---|
| L0 | 56 | 5 |
| L1 | 7 | 7 |
| L2 | 31 | 36 |
| L3 | 79 | 125 |

75 entries want to climb at least one level. Status: **done 74**,
**open 66**, **n/a 6**, planned 22
(T1 10, T10 1, T2 10, T8 1).

Read that as: 71 entries are already correct-by-construction and 34
are gated, but 56 still live only as prose or as this file - and 123
of all 168 belong at L3. The backlog is concentrated in the library/parts
pull path, the placement legality model, and the KRT/Freerouting driver.

Open rows by owning artifact (top of the T6 worklist):

- `scripts/lib_pull.py` x5
- `scripts/route_critical.py` x5
- `scripts/fp_verify.py` x4
- `scripts/lib/placelib.py` x4
- `scripts/lib/checklib.py` x3
- `scripts/schlib.py` x3
- `scripts/datasheet_extract.py` x3
- `scripts/place_anneal.py` x2
- `scripts/gate.py` x2
- `scripts/netlist_audit.py` x2
- `scripts/stitch_vias.py` x2
- `scripts/planes_gen.py` x2

## Health metric

`SKILL.md` = **286 lines** at T4 (the baseline). The playbook must shrink as
knowledge climbs, never grow; `tests/test_remediations.py::test_skill_md_does_not_grow`
enforces the ceiling. Knowledge that would have been appended to it belongs in a
script, a gate threshold, a template, or `reference/remediations/<check_id>.md`.

## Method, and how far to trust a row

Eight agents triaged 164 entries in slices of 21. Every level claim was
grounded in a grep or file read of this repo (evidence lives in the workflow
transcript; the Note column carries what a promotion needs instead). A
deterministic 27-row sample (16%) was then
re-derived by independent adversarial verifiers instructed to refute:
**9 of 27 were refuted** and are corrected here - mostly OWNER
mis-attribution, plus four genuine level errors (#75, #81, #111, #129).

So: the LEVEL column held up well under attack; the OWNER column did not, at
roughly a 1-in-3 rate on the sample. Re-check a row before acting on it, and fix
it here when you do.

- Corrected after refutation: #15, #57, #63, #75, #81, #111, #129, #141, #153
- Verified and upheld: #3, #9, #21, #27, #33, #39, #45, #51, #69, #87, #93, #99, #105, #117, #123, #135, #147, #159

## Appending

Adding a LEARNINGS entry means appending its row here in the same commit -
`tests/test_remediations.py::test_every_learnings_entry_has_a_triage_row` fails
otherwise and prints the row for you to paste. Promoting knowledge means editing
the row's Now level and status in the same commit as the code.

`#` = entry order in LEARNINGS.md, `LN` = its header line there.

## Register

| # | LN | Entry | Tags | Now | Target | Owner | Status | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | 9 | cp1252 console crashes on non-ASCII output | [windows] | L0 | L3 | scripts/lib/checklib.py | open | Call checklib.utf8_stdout() from every CLI main; add a test asserting each script's stdout is pure ASCII. |
| 2 | 14 | Python does not resolve MSYS /c/ paths | [windows] | L0 | L0 | LEARNINGS.md | n/a | Agent-side shell convention; no script surface can enforce how a bash heredoc is written. |
| 3 | 18 | File formats are not forward-compatible - pin ONE KiCad | [kicad] | L3 | L3 | scripts/lib/env.py | done |  |
| 4 | 24 | kicad-cli host quirks: not on PATH, refill-zones 10.x-only, pos inches | [kicad-cli] | L3 | L3 | scripts/kc.py | done |  |
| 5 | 31 | No kicad-cli api-server - sandboxed-GUI IPC works instead | [ipc] | L1 | L1 | scripts/smoke_ipc.py | done |  |
| 6 | 39 | pcbnew lives in KiCad's BUNDLED bin/python.exe | [swig] | L3 | L3 | scripts/lib/board_swig.py | done |  |
| 7 | 47 | freerouting 2.2.4 needs Java 25; batch flags are non-obvious | [freerouting] | L3 | L3 | scripts/lib/routelib.py | done |  |
| 8 | 55 | easyeda2kicad footprints: missing courtyards, defects, UA 403s | [easyeda2kicad] | L1 | L2 | scripts/fp_verify.py | open | Add the per-part DRC baseline fp_verify was specced for (EP pad with no net, drill under min hole); T3 covers pull-time fixes only |
| 9 | 62 | skidl prints env-var warnings on import - keep JSON stdout clean | [python] | L3 | L3 | scripts/check_env.py | done |  |
| 10 | 67 | skidl drops <script>.log/.erc files in CWD on import | [python] | L3 | L3 | scripts/check_env.py | done |  |
| 11 | 73 | Deep routing/placement/fab gotchas archived in the old repos | [prior-attempts] | L0 | L0 | LEARNINGS.md | n/a | Read-only external reference by user directive; individual facts get promoted on their own when used. |
| 12 | 79 | pcbnew.ZONE_FILLER segfaults headless - fill via kicad-cli | [swig] | L3 | L3 | scripts/planes_gen.py | done |  |
| 13 | 86 | .kicad_pro is the DRC/ERC authority; keep it minimal | [kicad] | L3 | L3 | scripts/board_init.py | done |  |
| 14 | 94 | kicad-sch-api 0.5.6 quirks | [python] | L3 | L3 | scripts/schlib.py | done |  |
| 15 | 103 | kiutils needs encoding=utf-8 passed explicitly on Windows | [python] | L3 | L3 | scripts/lib/fplib.py (sexpdata, not kiutils) | done | kiutils is pinned but imported nowhere; pad-size-is-pre-rotation half is tracked at #69/#110 |
| 16 | 109 | KiCad 10 board files store nets by NAME - mutation surgery | [kicad] | L0 | L2 | tests/test_golden.py | open | Re-run each mutation and byte-compare to the committed mutant so a golden regen fails loudly instead of leaving stale mutants. |
| 17 | 115 | kicad-cli render uses --width/--height; ERC exit = count | [kicad-cli] | L3 | L3 | scripts/render.py | done |  |
| 18 | 121 | A stale persistent AIEE_KICAD_CLI silently pins the WRONG KiCad | [kicad-cli][windows] | L0 | L2 | scripts/lib/env.py | open | Validate the resolved version against the 10.x pin: env.py should reject a 9.x pin (or check_env fail) since 9.x cannot load 10-fo |
| 19 | 132 | DRC/ERC JSON: layer/net/refdes embedded in description strings | [kicad-cli] | L3 | L3 | scripts/kc.py | done |  |
| 20 | 141 | cpl-rotation mutant does NOT fail --schematic-parity | [kicad] | L2 | L2 | tests/golden/manifest.yaml | open | Delete the refuted 'intentionally fails DRC --schematic-parity too' sentence from manifest.yaml; S2 measured 0 parity violations. |
| 21 | 149 | Pad absolute geometry: center = fp + R(-fp_angle).local | [geometry][kicad] | L3 | L3 | scripts/lib/geom.py | done |  |
| 22 | 163 | KiCad-10 pcb: net refs by NAME; zone fills are keyhole rings | [geometry][kicad] | L3 | L3 | scripts/lib/geom.py | done |  |
| 23 | 172 | FLIP is baked into the file (no parser mirror); keepouts never fill | [geometry][kicad] | L3 | L3 | scripts/lib/geom.py | done |  |
| 24 | 186 | Per-net copper = union of tracks/pads/vias/zone-fills; pcbnew oracle | [shapely] | L3 | L3 | scripts/lib/geom.py | done |  |
| 25 | 194 | Return-path corridor FPs on clean boards - 3 artifact classes | [geometry][shapely] | L2 | L2 | scripts/check_return_path.py | done |  |
| 26 | 208 | linemerge() raises ValueError on a bare LineString input | [shapely] | L3 | L3 | scripts/check_return_path.py | done |  |
| 27 | 214 | Custom .kicad_dru auto-loaded by kicad-cli; rule name in description | [kicad-cli][drc] | L2 | L2 | scripts/rules_gen.py | done |  |
| 28 | 222 | DRU token is A.NetName (A.Net matches nothing); LATER rule wins | [kicad-cli][drc] | L3 | L3 | scripts/rules_gen.py | done |  |
| 29 | 231 | Headless netlist->board SWIG import; bbox-pack to avoid density DRC | [swig][kicad] | L3 | L3 | scripts/board_init.py | done |  |
| 30 | 242 | Stackup: SWIG cannot build it - inject the (stackup) block as text | [kicad][swig][geometry] | L3 | L3 | scripts/board_init.py | done |  |
| 31 | 251 | easyeda2kicad 1.0.1 wraps an ANONYMOUS JLCPCB parts search | [parts][easyeda2kicad] | L3 | L3 | scripts/lib/partslib.py | done |  |
| 32 | 265 | easyeda2kicad LEGACY (module ...) footprints still load in KiCad 10 | [easyeda2kicad][kicad-cli] | L3 | L3 | scripts/fp_verify.py | done |  |
| 33 | 277 | fp export svg needs the output dir to EXIST first | [kicad-cli] | L3 | L3 | scripts/lib_pull.py | done |  |
| 34 | 283 | No PDF lib was in the venv; added pypdf 6.14.2 (pure-python) | [datasheet][python] | L3 | L3 | requirements.txt | done |  |
| 35 | 291 | KiCad 10 stores refdes as (property ...); text angle is ABSOLUTE | [geometry][kicad] | L3 | L3 | scripts/check_silk.py | done |  |
| 36 | 303 | KiCad text bbox calibrated vs pcbnew; center-in / 50% cover rule | [geometry][kicad] | L3 | L3 | scripts/check_silk.py | done |  |
| 37 | 311 | Diff-pair skew mutant is a COUPLING defect, not a length mismatch | [shapely][geometry] | L2 | L2 | scripts/check_diffpair.py | done |  |
| 38 | 324 | kicad-sch-api hierarchical sheets serialize; global labels do not | [python] | L3 | L3 | scripts/schlib.py | done |  |
| 39 | 335 | Labels attach anywhere ALONG a wire; every endpoint needs pin or label | [python][erc] | L3 | L3 | scripts/schlib.py | done | T6 (P4-7): every wire segment is recorded and _assert_label_clear raises on a label anchor hitting a FOREIGN run (interior or endpoint) at generation time; s7 corpus regen is the false-positive canary |
| 40 | 343 | Netlist facts: multiline sexpr, unconnected-* nets, PWR/FLG excluded | [kicad-cli] | L2 | L2 | scripts/netlist_audit.py | done |  |
| 41 | 351 | Sandboxed-GUI IPC REGRESSED on this host: KiCad is not ready to reply | [ipc] | L1 | L1 | scripts/check_env.py | n/a | External/host fact: headless kipy only arrives with KiCad 11; nothing to promote until then, probe already reports it |
| 42 | 362 | Placement-edit SWIG API facts on 10.0.3 (angle norm, mmToIU, flip) | [swig] | L3 | L3 | scripts/lib/place_swig.py | done |  |
| 43 | 374 | Courtyard containment needs edge-part exemptions (corpus-calibrated) | [geometry][placement] | L3 | L3 | scripts/lib/placelib.py | done |  |
| 44 | 384 | Spring embedding: classic F-R attraction is d^2/k, not linear-in-d | [placement][python] | L3 | L3 | scripts/place_seed.py | done |  |
| 45 | 393 | SA stall detection must not count the hot phase | [placement][python] | L3 | L3 | scripts/place_anneal.py | done |  |
| 46 | 404 | S11 DSN/SES roundtrip verified on 10.0.3 (V1/V7/V3 resolved) | [swig][freerouting] | L3 | L3 | scripts/lib/route_swig.py | done |  |
| 47 | 416 | Freerouting 2.2.4 verified flags + completion parse | [freerouting] | L3 | L3 | scripts/lib/routelib.py | done |  |
| 48 | 425 | KRT 0.19.0 vendored: no-KiCad headless router | [parts][python] | L3 | L3 | scripts/lib/env.py | done |  |
| 49 | 435 | FR DSN reader can WEDGE on KRT copper - detect + fall back | [freerouting][routing] | L3 | L3 | scripts/route_auto.py | done |  |
| 50 | 445 | P7 chain order is board-class dependent; plane nets not outer-trunked | [routing][placement] | L0 | L3 | agents/router.md | planned-T10 | T10 task recipes should encode the per-class stage order so it cannot drift; plane half already correct by construction |
| 51 | 453 | Via-candidate obstacles = WIRED copper only; 1-layer-bond vias dangle | [stitch][geometry] | L3 | L3 | scripts/stitch_vias.py | done |  |
| 52 | 461 | zones_intersect fires on same-net same-priority overlaps | [kicad-cli][drc][zones] | L3 | L3 | scripts/planes_gen.py | done |  |
| 53 | 467 | Courtyard-only packing is silk-blind; KRT leaves sub-grid crumbs | [placement][routing] | L3 | L3 | scripts/place_anneal.py + scripts/silk_place.py | done | T6 (P6A-6+p1): --margin-mm soft spacing (default 0.0; buffers SA overlap term + repair targets, legality keeps true courtyards) and silk_place.py owns the refdes sweep with real-DRC verify; a full silk model in SA was evaluated and rejected |
| 54 | 478 | ArcPoly.outline drops curvature - tessellate arcs before shapely | [gerbonara][gerber][geometry] | L3 | L3 | scripts/lib/gerblib.py | done |  |
| 55 | 488 | Annular ring must be measured against PAD FLASHES only, never pours | [dfm][gerber] | L3 | L3 | scripts/dfm_check.py | done |  |
| 56 | 495 | CPL polarity: compare per PAD NUMBER, not per net | [dfm][kicad] | L2 | L2 | scripts/dfm_check.py | done |  |
| 57 | 504 | Clearance from gerbers = gaps between UNIONED copper islands | [dfm][gerber] | L3 | L3 | scripts/lib/gerblib.py + dfm_check.py | done | union/components lives in gerblib.py:80-87; dfm_check consumes it |
| 58 | 511 | JLC export facts (10.0.3, verified on our goldens) | [jlc][kicad-cli][fab] | L3 | L3 | scripts/fab_export.py | done |  |
| 59 | 523 | gate.py --commit is a repo-root git add -A - dirty trees get swept | [skill][git] | L3 | L3 | scripts/gate.py | done | T6 (P8B-2/XC-3): staging scoped to the boards/<name>/ workspace derived from the gate input; outside-dirty paths reported as excluded_dirty, never swept; non-boards inputs refuse -A on a dirty tree |
| 60 | 531 | Pulled-lib pin electrical types are junk; ERC needs a retype pass | [easyeda2kicad][erc][python] | L3 | L3 | scripts/lib_pin_types.py | done | T6 (P3-PIN-RETYPE): productionized as scripts/lib_pin_types.py, NOT inside lib_pull - the retype map needs parts/<lcsc>.json extracts which do not exist at pull time. Datasheet-typed power_in/power_out (tab duplicate stays passive), blanket passive elsewhere; idempotent; librarian.md step 2 invokes it |
| 61 | 548 | P5 gate: --schematic SameFileError + LCSC field parity warnings | [board_init][kicad] | L3 | L3 | scripts/board_init.py | done |  |
| 62 | 561 | P6 gate was courtyard-blind: seed shorted 9 pad pairs while gate=PASS | [placement][drc][geometry] | L3 | L3 | scripts/lib/placelib.py | done |  |
| 63 | 576 | Coordinate descent cannot evict a blocker; repair candidates not seed | [placement][python] | L0 | L3 | scripts/place_anneal.py + agents/placement.md | open | T6 (p2): placement.md prompt half FIXED - repair the BEST candidate, never fall back to the seed on silk counts. Blocker eviction in _repair (2-level cooperative search) still open - P6A-7/p7 recorded and deferred |
| 64 | 587 | Symbol pulls not idempotent; lib_pull hides a failed symbol pull | [easyeda2kicad][parts] | L3 | L3 | scripts/lib_pull.py | done | T6 (P3-PULL-GATE): _dedupe_symbols drops duplicate top-level (symbol NAME) blocks after every batch (paren scanner, keep-first, refuses lossy decode) and the per-part gate verifies one symbol per LCSC id on disk |
| 65 | 605 | LCSC datasheet PDFs fetchable via the wmsc.lcsc.com path transform | [datasheet][parts] | L3 | L3 | scripts/lib/partslib.py | open | T6 (P3-WMSC-PDF): the transform now lives at the SOURCE (partslib.fix_datasheet_url in normalize(), row 99) + %PDF guard (row 101), so the agent's own fetch works. Residual: an in-script --url fetch mode in datasheet_extract was deliberately deferred |
| 66 | 615 | Pulled footprints ship silk <0.25mm from copper; dots inside pad 1 | [easyeda2kicad][drc] | L3 | L3 | scripts/lib/fpfix.py | done | T3: fpfix drops/promotes sub-0.15 mm silk at pull time (lib_pull runs it by default); measured 16 -> 0 real DRC violations on the pristine pull set |
| 67 | 628 | Fix recipe for the silk-on-pad dots, measured against real DRC | [easyeda2kicad][drc] | L3 | L3 | scripts/lib/fpfix.py | done | T3: rule B narrows to w_max = 2*(d_centerline - 0.15), floored to the 0.05 grid, violators of equal original width together - reproduces the hand recipe exactly |
| 68 | 650 | Hierarchical netlist export drops no-connect singleton nets | [kicad-cli][python] | L1 | L1 | scripts/netlist_audit.py | done | T6 (P4-5): pin_no_net warning - expected pins from the export's own units/libparts inventory vs net membership (unconnected-* counts as connected); facts pins_expected/pins_connected |
| 69 | 667 | placelib FpPad DROPS per-pad rotation - re-derive pad boxes | [placement][geometry] | L3 | L3 | scripts/lib/placelib.py | done | T6 (P6A-2/p3): FpPad stores the RELATIVE rotation (file ROT - fp angle; cumulative convention corpus-verified) so place_center cannot corrupt it; _pad_box_local uses rotation-aware half-extents; both P6 fixtures kept legality 0 |
| 70 | 677 | Connector mating direction: read the WRL, not the silk outline | [placement][kicad] | L0 | L3 | NEW reference/connector_orientation.yaml | open | record the mouth vector per connector footprint once and have place_seed orient from the table instead of guessing |
| 71 | 687 | Pulled footprints park Reference 4 mm off-origin -> silk DRC noise | [placement][drc][silk] | L3 | L3 | scripts/lib_pull.py + scripts/silk_place.py | done | T3: lib_pull runs lib_refdes_norm after every pull. T6 (p1): the board-side greedy solver is now owned code - silk_place.py (both angles x 4 sides, crowded-first, live min_silk_clearance, residuals reported, real-DRC verify) |
| 72 | 701 | lib_pull with a RELATIVE --out-dir bakes unresolvable 3D model paths | [easyeda2kicad][parts] | L3 | L3 | scripts/lib_pull.py | done | T3: lib_pull resolves --out-dir to an absolute path before invoking easyeda2kicad, so (model ...) can never be baked relative |
| 73 | 712 | Pulled USB-C peg holes = 4 DRC errors; DIP switch ships 8 silk_overlap | [easyeda2kicad][drc] | L3 | L3 | scripts/lib/fpfix.py | done | T3: rule C converts zero-annular peg pads to np_thru_hole (position/size/drill untouched); rule D deletes inside-body fp_text that collides with own silk |
| 74 | 731 | WRL bbox is a coincidence trap; use orthographic side renders | [placement][kicad][render] | L1 | L1 | agents/placement.md | done | T6 (p2): placement.md stage-3 now REQUIRES proving mating direction with an orthographic side render (--views left,right) or below-board WRL pin fit before accepting any connector rotation |
| 75 | 754 | DRC on a board copy OUTSIDE the project dir silently changes the rules | [drc][kicad-cli] | L3 | L3 | scripts/lib/checklib.py (lift _stage_board) | open | 3 scripts already stage by construction (route_auto:71, route_critical:403, planes_gen:436); lift ONE helper, add fp-lib-table |
| 76 | 763 | Freerouting cannot merge a USB-C's two VBUS pads at 1.75 mm | [routing][placement] | L0 | L1 | scripts/route_auto.py | open | probe must list WHICH connections stayed unrouted (net + pads) so a topology cap is not misread as a placement defect |
| 77 | 776 | place_edit ops files need the {version, ops} envelope | [placement][python] | L0 | L3 | scripts/lib/place_swig.py | open | document that place/move set the footprint ORIGIN (or add a courtyard-centre op); the envelope half is already done |
| 78 | 782 | A net-wide track_width DRU floor can be UNMEETABLE at a fine-pitch pad | [routing][kicad][drc] | L2 | L2 | scripts/route_critical.py (--pad-window) + scripts/planes_gen.py | done | T6 (P7B-1/P7B-2): --pad-window measures the width ceiling per power pad vs the DRU floor (exit 1 = unmeetable; pd-trigger J1 known-answer ~1.49 vs 1.75) and planes_gen grew the connect:solid key. Residual: rules_gen still does not run the probe at emission time (P7A-8 deferred) |
| 79 | 798 | rules_gen puts EVERY power net in one Power netclass at the widest width | [routing][rules_gen][freerouting] | L3 | L3 | scripts/rules_gen.py | done | T1: one netclass per REQUIRED width (Pwr_<w>mm; rails at or under the Default width stay Default); the 'split classes in .kicad_pro' prose is gone from SKILL.md and router.md |
| 80 | 808 | check_current's via-count rule is NET-WIDE, no per-segment override | [routing][check_current] | L2 | L2 | scripts/check_current.py | planned-T2 | fold into T2's check_current work: let overrides attribute current to via clusters and pour necks, not just track width |
| 81 | 819 | hole_to_hole skips via drill vs same-net THT pad drill | [routing][stitch][drc] | L3 | L3 | scripts/stitch_vias.py + lib/geom.py | done | T6 (P7A-4/P7B-4): geom.Pad carries drill/(drill_poly incl. slot stadiums, -prot transform); stitch_vias + plane_repair enforce the floor edge-to-edge against real drill extents (0.2 mm edge gap == the S11 0.5 mm centre floor for standard 0.3 drills). dfm_check P9 backstop untouched |
| 82 | 832 | USB-C SMD GND pads need a pour lobe + via field, not one via per pad | [routing][placement] | L2 | L3 | scripts/planes_gen.py | open | T6 (P7B-2): connect:solid key landed (the hand patch is gone; recipe trigger-indexed in remediations/track_width.md); Batch H added return-net coverage to check_current. Residual: auto lobe generation with per-pad current sizing (P7A-8 deferred) |
| 83 | 843 | Silk strap tables must print SWITCH positions, not raw config bits | [skill][fab] | L0 | L0 | reference/checklists/connector.md | n/a | Semantic design-review call, not scriptable; at best one connector-checklist line. Mirror half already L3 (place_swig.py:85) |
| 84 | 851 | Zooming a datasheet drawing without a rasterizer: pypdf crop + scale | [datasheet][python] | L0 | L3 | scripts/datasheet_extract.py | open | add a --crop/--zoom single-page extractor to datasheet_extract so the trick is one flag, not re-derived by each extractor agent |
| 85 | 858 | kicad-sch-api preserves compound pad names (A4-B9) through save | [python] | L0 | L0 | scripts/schlib.py | n/a | Negative finding: nothing to build. Library behaviour recorded once; the simple-name fixup machinery already exists at L3. |
| 86 | 864 | place_anneal separation refs absent from the board silently dropped | [placement] | L2 | L2 | scripts/netlist_audit.py | done | T6 (P4-4): missing_ref ERROR walks placement edges/groups/fixed/separation + thermal[].ref (the R2->R2A/R2B near-miss is the regression test); bench score_p2 filters the kind so the defect keeps one weight |
| 87 | 869 | pdfpages 2026 passes an artifact key older graphics stacks reject | [latex][windows] | L3 | L3 | scripts/report_gen.py | done |  |
| 88 | 876 | JLCPCB Open API facts (JOP auth, error taxonomy, no sandbox) | [jlc][api] | L3 | L3 | scripts/lib/jlcapi.py | done |  |
| 89 | 889 | pcbParam keys are layer/width/length/qty/thickness - NOT stencil* | [jlc][api] | L3 | L3 | scripts/order_submit.py | done |  |
| 90 | 899 | LaTeX escaping: [ and * are context-sensitive, brace-wrap them | [latex] | L3 | L3 | scripts/report_gen.py | done |  |
| 91 | 908 | Recomputed arc endpoints made arc outlines parse as POLYGON EMPTY | [geom][layout] | L3 | L3 | scripts/lib/geom.py | done |  |
| 92 | 918 | tests/test_report.py is not concurrency-safe - diffs global git status | [testing][windows] | L3 | L3 | tests/test_report.py | done | T6 (XC-7): porcelain diff scoped to the workspace under test (git status --porcelain -- boards/<name>); litter assertion keeps full power within scope |
| 93 | 927 | Corner radius must be clamped to the mounting-hole inset | [layout] | L3 | L3 | scripts/lib/board_swig.py | done |  |
| 94 | 933 | Power symbol net name comes from its VALUE field, not the pin name | [kicad][python] | L3 | L3 | scripts/schlib.py | done | T6 (P4-6): VALUE = rail net by construction - power_flag places the symbol with the net as VALUE; power_symbol_at_pin derives it from the pin's wired net and refuses unwired pins |
| 95 | 946 | add_hierarchical_label drops shape; rotated 2-pin stubs point INWARD | [python][kicad-sch-api] | L3 | L3 | scripts/schlib.py | done | T6 (P4-2): rotmirror fixture (ERC + netlist oracle) falsified the old diagnosis - stub_dir was CORRECT; ksa mirrors pin POSITIONS at 90/270, fixed in schlib.pin_pos. Shape drop stays not-worth-patching |
| 96 | 964 | An inner Edge.Cuts gr_rect silently BECOMES the board outline | [geom][layout] | L3 | L3 | scripts/lib/geom.py | open | Parser residual: hand-edited or imported boards (T9 intake) still parse a window as the outline. Collect all closed loops and subt |
| 97 | 974 | InSpice + KiCad bundled ngspice.dll: the working recipe has traps | [spice][windows] | L3 | L3 | scripts/lib/simlib.py | done |  |
| 98 | 991 | PDN cavity-model band edges are validity limits, not layout facts | [spice][geometry] | L3 | L3 | scripts/check_pdn_z.py | done |  |
| 99 | 999 | parts_search www.lcsc datasheet URLs are unfetchable; use wmsc mirror | [parts][datasheet] | L3 | L3 | scripts/lib/partslib.py | done | T6 (P3-WMSC-PDF): fix_datasheet_url applied inside partslib.normalize(), so live AND db rows are rewritten before any agent sees them; idempotent on the wmsc form, other hosts pass through |
| 100 | 1026 | parts_search returns zero rows for value tokens like 10K | [parts] | L3 | L3 | scripts/parts_search.py | done | T6 (P3-QUERY-NORM): on an empty live result, value tokens (10K/4R7/4K7) are spelled out and retried once (query_retried reported); every raw-empty payload carries a stock-out-vs-bad-query hint |
| 101 | 1035 | LCSC www/datasheet URLs return HTML; verify %PDF magic bytes | [parts] | L2 | L2 | scripts/datasheet_extract.py | done | T6 (P3-WMSC-PDF): --pdf exits 2 when the file does not start %PDF, naming the HTML-shell cause and the wmsc remediation - an HTML pinout can no longer reach the extractor |
| 102 | 1045 | TI SN74LVC00A pin table has shifted TYPE/DESCRIPTION columns | [datasheet][parts] | L0 | L3 | NEW reference/part_errata.yaml | open | Per-part errata table keyed by LCSC id, cross-checked by datasheet_extract --validate; plus a 'pin DIAGRAM outranks the table' rul |
| 103 | 1054 | LM339LV pin drawing and pin table transpose the channel names | [datasheet] | L0 | L3 | NEW reference/part_errata.yaml | open | Errata entry: wire quad comparators by pin NUMBER (out1<->in6/7 etc), no internal hysteresis, 30 us Hi-Z POR - so P4 cannot wire b |
| 104 | 1065 | A wrong lib-table URI silently pulls into the REPO ROOT | [librarian][kicad] | L3 | L3 | scripts/lib_pull.py | open | T3 shipped the URI guard (lib_pull refuses the repo root) but DECLINED the D2PAK/TO-263 renumber: renumbering pads changes the pad->net mapping, which the pull-time sanitiser must never do. Owner is the extraction JSON / P4 wiring path, not fpfix |
| 105 | 1091 | JST catalog PDFs hide dimensions in a non-embedded CID font | [datasheet] | L0 | L3 | NEW scripts/lib/pdflib.py | open | Add a CID-stream decoder (CID = ASCII-31; 692-695 = + - +/- x) with per-glyph coords to the extractor text path; applies to any JS |
| 106 | 1099 | lib_pull --out-dir default is RELATIVE, lands in repo root, shared by runs | [parts][concurrency] | L3 | L3 | scripts/lib_pull.py | done |  |
| 107 | 1110 | check_creepage only knows working VOLTAGE, misses magjack isolation barrier | [check_creepage][gates][magnetics] | L0 | L2 | scripts/check_creepage.py | planned-T2 | T2 net-PAIR voltage input must also accept a datasheet/standard barrier gap for a net pair, independent of rail voltage |
| 108 | 1134 | lib_pull reports pulled for parts it never pulled, once lib is non-empty | [easyeda2kicad][parts] | L3 | L3 | scripts/lib_pull.py | done | T6 (P3-PULL-GATE): per-part gate is fplib.symbol_index - success iff a top-level symbol carries (property "LCSC Part" <id>) AND its Footprint property resolves in aiee.pretty; exact id match (no substring), shared footprints attribute correctly; T1's footprint-grep gate removed |
| 109 | 1153 | EasyEDA CAD rate-limit is a CloudFront WAF block on one path, clears in ~60 s | [easyeda2kicad][parts] | L3 | L3 | scripts/lib_pull.py | done | T6 (P3B-1+P3-PULL-PACE): --parts batch mode paces pulls (--pace-s, auto 0/<=10 parts else 15 s), 403/Forbidden backs off 90 s and retries once, retried part re-verified on disk by the symbol gate; paced_s + retried reported |
| 110 | 1167 | Pulled courtyards enclose the BODY only - 20 of 22 exclude their own pads | [easyeda2kicad][placement] | L3 | L3 | scripts/lib/placelib.py | done | T6 (P6A-2/p3): same fix as row 69 - the effective-courtyard pad-box union now sees true rotated pad extents; the ROT-90 SOT-23 0.275 mm/side under-report has a regression test |
| 111 | 1186 | fp_verify's pad-size check uses the MODE, so asymmetric packages slip through | [librarian][easyeda2kicad] | L1 | L1 | scripts/fp_verify.py | done | T6 (P3-FPV-GEOM): pad_size bounds MIN and MAX distinct sizes vs the datasheet (a 10/10 tie can no longer hide a column); severity stays warning BY DESIGN (all 7 observed hits benign) - target revised L2->L1 |
| 112 | 1210 | Bridge rectifier CURRENT rating is not a thermal rating - check RthJA | [parts][thermal] | L0 | L2 | scripts/check_thermal.py | open | accept per-part package rthja_cw and mean rectifying current from datasheet_extract; fail when package theta dominates copper spre |
| 113 | 1226 | Magjack shell board-lock pads can collapse HV-to-shield creepage | [magnetics][check_creepage] | L2 | L2 | scripts/check_creepage.py | done |  |
| 114 | 1245 | lib_pull reported every part pulled once ONE part had landed | [parts] | L2 | L2 | scripts/lib_pull.py | done |  |
| 115 | 1256 | fp_verify has NO drill handling, so a wrong THT annulus passes silently | [gates] | L2 | L2 | scripts/fp_verify.py | done | T6 (P3-FPV-GEOM): fplib parses (drill ...) (largest dim); fp_verify errors on annulus (min(size)-drill)/2 < 0.15 mm JLC floor and on mismatch vs land_pattern drill_mm/annulus_mm (new optional schema fields); NPTH excluded |
| 116 | 1265 | First live JLC calculate: field rules the doc tables get wrong | [jlc][api] | L3 | L3 | scripts/order_submit.py | done |  |
| 117 | 1280 | A net-wide HV clearance rule makes fine-pitch HV PADS unroutable | [routing][drc] | L0 | L2 | NEW scripts/check_hv_escape.py | open | pre-route check: per HV pad, min distance to foreign copper vs the DRU floor; rules_gen must emit per-refdes courtyard exclusions |
| 118 | 1294 | Netclass clearance is PAD-BLIND - it cannot carry an HV rule | [routing][kicad] | L0 | L0 | scripts/rules_gen.py | n/a | Pure tool-behaviour fact, recorded once; the consequence (DRU is the authority, post-route audit) is already covered by check_cree |
| 119 | 1302 | KRT: a 3-pad diff net routes as a MESH, and only the FIRST leg closes | [routing][parts] | L0 | L3 | scripts/route_critical.py | open | teach route_critical to route N-pad diff nets leg-by-leg on separate branches with disjoint layer costs, then graft via route_edit |
| 120 | 1318 | KRT: relative --work-dir silently breaks, and bash mangles net names | [parts][python] | L3 | L3 | scripts/route_critical.py + route_auto.py | done | T6 (P7A-2): --work-dir resolved to absolute in route_critical, route_auto and route_probe; net names already travel via constraints.json + argv lists (S11), never a shell |
| 121 | 1327 | planes_gen cannot see existing vias-in-pad or touching plane regions | [planes_gen][drc] | L3 | L3 | scripts/planes_gen.py | done | T6 (P7A-5): thermal grid drops points inside the hole floor of existing drills in the land and skips wholesale at >=4 thru-hole items (U22 pattern); touching rects now conflict (<=) and get distinct priorities |
| 122 | 1338 | drc_routed --parity finds mismatches the P6 place gate never runs | [drc][gates] | L2 | L2 | reference/gates.yaml | done | T6 (XC-6): P6 drc gate runs parity:true; a placed-unrouted board's unconnected items stay non-failing warnings at the [error]-only gate |
| 123 | 1345 | A module's own pads can sit INSIDE its declared antenna keepout | [routing][kicad] | L0 | L3 | NEW scripts/rule_area.py | open | SWIG generator that derives the antenna band from footprint at+courtyard and refuses any band overlapping a pad of that module |
| 124 | 1359 | 3D-model origin offsets in renders are NOT footprint defects | [easyeda2kicad][kicad] | L0 | L1 | scripts/fp_verify.py | open | extend fp_verify to connectors via datasheet_extract and report 3D-model origin offset as a separate benign class, not a defect |
| 125 | 1373 | Keepout checks need STRICT-interior containment, not inclusive | [geometry][keepout][planes] | L0 | L2 | NEW scripts/check_keepout.py | open | copper-free keepout check with a strict epsilon test; abutting plane regions legitimately place fill vertices ON the band boundary |
| 126 | 1401 | A pad-gap formula is only valid for one pad SHAPE | [geometry][creepage][measurement] | L2 | L3 | scripts/lib/geom.py | planned-T2 | T2 pad-shape-correct gap should surface one geom-backed pad-pair gap helper/CLI so footprint reviews stop re-deriving the formula |
| 127 | 1433 | KRT default 200k A* iteration cap, not congestion, fails a long haul | [routing][parts] | L3 | L3 | scripts/route_critical.py | done | T6 (P7A-3/P7B-5): on 'No route found after N iterations' + static frontier share >=0.7 (or unknown), failed nets retry ONCE at 4M/60k probe iterations (the x20 that routed both carrier hauls first try); Coverage line parsed into facts/violations as static_share |
| 128 | 1445 | KRT output boards must be refilled before DRC or ~375 phantom zone errors | [routing][gates] | L3 | L3 | scripts/gate.py | done | T6 (P8B-2): drc_options.require_fresh_fills on drc_routed - geom assert_fresh preflight, exit 2 with a refill message instead of grading; keyed on an explicit flag (not parity) because XC-6 turned parity on for P6 whose boards may predate fills |
| 129 | 1455 | Measure the pad extent, not the footprint origin, for a corridor gap | [routing][placement] | L2 | L3 | scripts/lib/placelib.py + place_edit.py | open | placelib:67-97 already resolves pad boxes; expose a pad-to-pad gap query so agents cannot measure from the (at ...) origin |
| 130 | 1470 | After routing starts, gate place and check_decoupling are not valid oracles | [place][gates][routing] | L2 | L2 | scripts/place_edit.py | done | T6 (P6A-4): place_edit refuses footprint ops (place/move/rotate/flip) on a board carrying segment/via nodes unless --allow-routed; text ops exempt; the flagged report carries routed_board + a re-run-drc_routed warning |
| 131 | 1504 | High static frontier share means raise iterations, not widen the rip set | [routing][krt] | L3 | L3 | scripts/route_critical.py | done | T6 (P7A-3/P7B-5): static_share triage is script behavior (share <0.7 = no blind retry, violation carries the share for rip-set triage); retry targets only the failed nets; route_critical's DRC-delta guard still rolls back any net-new errors |
| 132 | 1522 | KRT --clearance is a CAP on the netclass map; --net-clearances is not capped | [krt][clearance] | L3 | L3 | scripts/route_critical.py | done | T6 (P7A-3c/P7B-5c): net_clearances.json built from .kicad_pro netclass patterns + .kicad_dru per-net clearance rules (max wins - nothing capped down), passed on every KRT call; parser fails open (no file) on unparseable rules |
| 133 | 1538 | bg.nets omits UNNETTED pads, so any clearance model built from it is blind | [geom][drc][clearance] | L0 | L3 | scripts/lib/geom.py | open | layer_copper must include netless pads; add a bridged-layer helper from tracks+pads+zones since net_copper counts a via barrel on  |
| 134 | 1553 | route_edit adds BEFORE it removes, so no same-position replace in one file | [route_edit][kicad] | L0 | L2 | scripts/route_edit.py | open | Validate the ops list: a remove whose item coincides with an add must be rejected by name, not surface as a post-apply verify roll |
| 135 | 1564 | check_diffpair's graph ignores vias AND pads; skew becomes total copper length | [check_diffpair][gates] | L1 | L2 | scripts/check_diffpair.py | planned-T2 | T2 adds vias+pads as graph edges; also make branch_free:false its own violation and widen/parameterize TERM_PAIR_MM for magjack pa |
| 136 | 1588 | via-count rule is unsatisfiable for a PLANE-fed rail and overrides cannot reac | [check_current][gates] | L2 | L2 | scripts/check_current.py | planned-T2 | T2 'plane-fed rails expressible'; the P5/P7 2-via-tap fan-out habit it implies belongs to T6 layout templates. |
| 137 | 1600 | voltages is net-to-REFERENCE so a bridge-input PAIR gap passes silently | [check_creepage][gates] | L2 | L2 | scripts/check_creepage.py | planned-T2 | T2 net-PAIR voltage input + report ALL violating pairs (a worst-pair sweep hid two siblings) + return the actual gap location. |
| 138 | 1635 | pcb/create returned unknown_error code 2 and no API can say if the order lande | [jlcapi][order_submit][SPEND] | L0 | L2 | scripts/order_submit.py | open | T1: code 2 now classifies as unknown_error with a DO-NOT-RETRY remediation, and ordering.md carries the STOP protocol (prose, L0). Still unowned: nothing MAKES a retry impossible after an ambiguous create - the latch arms only on success |
| 139 | 1654 | derive_copper_oz defaults 1 oz on an unparsed heading and blames a missing fil | [order_submit][stackup] | L2 | L2 | scripts/order_submit.py | done | T1: derive_copper_oz returns (None, why) - missing file, no Chosen heading, unresolvable id are three DISTINCT refusals - and _api_quote refuses instead of quoting a guessed 1 oz |
| 140 | 1668 | The gerber sha256 is not a design fingerprint, so a sha-bound latch self-inval | [fab_export][order_submit][jlcapi] | L3 | L3 | scripts/lib/fabhash.py | done | T1: design_hash() strips the volatile stamps (JSON-aware for .gbrjob) and --api-create binds to it; the file sha stays as the narrower 'is this the exact file I quoted' |
| 141 | 1686 | The Open API has NO assembly surface, and order_quote is 3.6x low on 4-layer | [jlcapi][order_submit] | L0 | L3 | reference/jlc_pricing.yaml + order_quote.py | open | a yaml line item has no consumer: pcb_cost (order_quote.py:69-92) has no copper-weight term and snaps qty silently |
| 142 | 1705 | min_hole_to_hole 0.25 at WARNING is the second sub-fab floor in the shipped pr | [board_init][dfm][gates] | L3 | L3 | scripts/lib/fabfloors.py | done | T1: board_init writes min_hole_to_hole from the profile AND pins hole_to_hole to error; check_pro asserts it before the file is written |
| 143 | 1724 | An endpoint inside a via or pad is connected; inside another track's body it i | [kicad][connectivity][route_edit] | L2 | L3 | scripts/route_edit.py | open | add_track should snap to (or require) an exact coincident vertex within tolerance; overlap-only joins split nets for graph-based c |
| 144 | 1735 | stitch_vias puts a stitch 0.35 mm from a thermal-via drill inside the pad | [stitch_vias][dfm] | L3 | L3 | scripts/stitch_vias.py | done | T6 (P7A-4): every existing drill (incl. footprint pad drills via the -prot transform) is a real-extent hole; candidates need edge gap 0.2 + own drill radius, so an in-pad 0.35 mm spot now rejects hole_to_hole |
| 145 | 1750 | Moving a footprint on a ROUTED board: no silk model, and GND stubs are orphane | [place_edit][placement][silk] | L2 | L3 | scripts/lib/placelib.py | open | T6 (p1): silk half largely closed - placelib.text_box owns the measured metrics (0.845*size advance, ABSOLUTE angle contract) and silk_place models silk obstacles. Residual: place_edit stub detach/reattach for moved footprints still unowned |
| 146 | 1774 | On F/GND/+3V3/B the check fails EVERY B.Cu trace by construction | [check_return_path][stackup] | L2 | L2 | scripts/check_return_path.py | planned-T2 | T2 'expected reference per stackup + formal waiver CLASS'; without it declaring a net can only raise an uncleanable count and team |
| 147 | 1785 | Audit HV rule COVERAGE, not existence; netless conductors reach nothing | [kicad_dru][check_creepage][safety] | L0 | L2 | NEW scripts/check_hv_coverage.py | open | Assert every /V/>=30 net appears in a clearance rule whose B side is unrestricted, and cover netless pads via B.NetName == '' at t |
| 148 | 1808 | min_track_width 0.1 is below every JLC profile (2nd recurrence) | [board_init][rules_gen][dfm] | L3 | L3 | scripts/lib/fabfloors.py | done | T1: floors come from the (layers, copper-oz) profile and both writers assert check_pro, so a sub-fab pro cannot be written. The P7-entry assert exists as fabfloors.check_pro but no GATE calls it yet (gates.yaml is T2's file this wave) |
| 149 | 1821 | GetTextBox 1.70 mm vs DRC inked stroke box 1.16 mm | [silk][place_edit][kicad] | L3 | L3 | scripts/place_edit.py | open | Library side done. Placed-board side has no inked-box feasibility model and no cheap sandbox-DRC screen for candidate move_text ed |
| 150 | 1851 | check_creepage cannot express a COATED board | [check_creepage][gates][ipc] | L2 | L3 | scripts/check_creepage.py | planned-T2 | T2: --coating flag plus per-item-type row select (masked trace B4 / exposed land A6 / inner B1); full IPC table into reference/ |
| 151 | 1889 | creepage count reports only the WORST pair per net pair | [check_creepage][gates] | L2 | L2 | scripts/check_creepage.py | planned-T2 | T2: emit every pair below the requirement, or at minimum carry pairs_under_requirement plus the distribution |
| 152 | 1902 | check_current has no bridge awareness for parallel same-net paths | [check_current][gates] | L2 | L2 | scripts/check_current.py | planned-T2 | T2: build the net graph from track endpoints, find cut edges, label each undersized segment bridge true/false |
| 153 | 1913 | roundrect pads carry 20 points - a sum/len centroid drops them all | [geometry][pads][python] | L3 | L3 | scripts/lib/geom.py | done | geom.py:260-296 is fully shape-aware; the residual is agent-side prose -> reference/remediations/ |
| 154 | 1929 | two copies of constraints.json, two different answers - 61 vs 53 | [constraints][gates] | L2 | L2 | scripts/verify_all.py | done | T6 (P8B-6): verify_all preflight emits a constraints_drift WARNING when the architecture/ twin parses to a different object (no winner picked - reconciliation is an owner decision, T7 owns canonicalization) |
| 155 | 1939 | board_init writes min_track_width 0.1 below every JLC profile | [board_init][rules_gen][dfm][gates] | L3 | L3 | scripts/lib/fabfloors.py | done | T1: one source for both writers, so re-running board_init can no longer lower the floors; board-setup.md still says re-run rules_gen after board_init (netclasses + DRU, not floors) |
| 156 | 1958 | easyeda2kicad puts EVERY refdes at a blanket (0,-4.0) mm | [parts][silk] | L3 | L3 | scripts/lib_pull.py | done | T3: lib_pull runs lib_refdes_norm automatically before board_init. Still unowned: nothing measures refdes-to-owner proximity on a BOARD |
| 157 | 1971 | min-over-endpoints segment distance reports a SHORT as clearance | [geometry][fixer] | L3 | L3 | agents/fixer.md | open | Fixer prompt must require lib/geom.py or shapely (intersection tested first) for ad-hoc geometry; grep geom in agents/fixer.md ->  |
| 158 | 1986 | refdes must clear the footprint's OWN silk; layer names unquoted | [parts][silk] | L3 | L3 | scripts/lib_refdes_norm.py | done |  |
| 159 | 2001 | no incremental board-from-netlist update - adding a part costs P6+P7 | [pipeline] | L0 | L3 | NEW scripts/board_update.py | planned-T8 | T8: apply a netlist diff (add_part/swap/del) to a placed and routed board while preserving copper |
| 160 | 2011 | drc_routed 0/0 does NOT imply fabricable | [gates][dfm] | L3 | L3 | scripts/lib/fabfloors.py | done | T1 fixed the .kicad_pro side; T6 (P5-5) closed the DRU half: fabfloors.check_dru + rules_gen --check-dru assert the aiee_* floors from the SAME map baseline_rules writes (exit 1 on drop/lower; finds 7 of 8 floors missing in carrier's shipped hand DRU). Residual: no gate calls it yet - one-line wiring belongs to the gates owner |
| 161 | 2020 | insideCuprumThickness hardcoded to 1 oz = different stackup built | [ordering][impedance] | L3 | L3 | scripts/order_submit.py | done |  |
| 162 | 2033 | JLC Open API pcb/create refuses 4-layer boards with code 2 | [ordering] | L0 | L3 | scripts/order_submit.py | open | T1: --api-create refuses 4+ layers locally (zero transport calls) and names the web-cart path. Unowned: the latch still arms only on SUCCESS (order_submit.py), not on an ambiguous first create - the case that risks double-buying |
| 163 | 2049 | stackups.yaml JLC04161H-3313 IS NOT A REAL JLC STACKUP | [stackup][ordering] | L3 | L3 | reference/stackups.yaml | done | T1: rebuilt from the live getImpedanceTemplateSettingList probe; every entry carries provenance + availability, board_init/rules_gen REFUSE available:false by name, and a test re-derives controlled_impedance from each stack. Caveat V18: the list churns and er is assumed |
| 164 | 2066 | order_track sees WEB-created orders fine - detail keys on batchNum | [ordering] | L3 | L3 | scripts/order_track.py | done |  |
| 165 | 2082 | kicad-sch-api save() silently guts lib_symbols it cannot resolve | [kicad-sch-api][python] | L3 | L3 | scripts/schem_refdes.py | done | write_placements registers the project libs then asserts the lib_symbols name set survived the save; raises otherwise |
| 166 | 2096 | ksa writes instance property positions with the WRONG y sign | [kicad-sch-api][silk][python] | L3 | L3 | scripts/schlib.py + schem_refdes.py | done | T6 (P4-1): schlib.save runs schem_refdes automatically (place_fields=True default, non-fatal with snapshot restore, Sheet.place_report) - fields born clean, regen smokes assert audit_sheet == [] |
| 167 | 2109 | Known-bad pull set = 16 DRC violations; recipe -> 0, filled graphics exempt | [easyeda2kicad][drc][parts] | L3 | L3 | scripts/lib/fpfix.py | done | Rules A-D plus lib_pull --verify-drc, which measures the pull on a scratch board instead of trusting geometry |
| 168 | 2129 | On a generated sheet the free space is diagonally outside the corners | [schematic][placement] | L3 | L3 | scripts/schem_refdes.py | done | Corner rings + power-symbol lateral offsets + a 0.7 mm pin-number band are in the candidate ladder and the collision model |
| 169 | 2141 | JLC's impedance-template list CHURNS - and the endpoint lies quietly w | [stackup][jlcapi][ordering] | L2 | L2 | scripts/board_init.py | done | T6 (P5-7): board_init.stackup_freshness warns when a jlc_open_api impedance-controlled stackup's verified date is >14 days old (report field + worker_notes; excluded from bench metrics by test). WARNING-only by design; the credentialed live re-probe of template codes stays with the ordering owner (P5-8 defer) |
| 170 | 2164 | The exact volatile set in a KiCad fab package - 5 line forms + 2 JSON  | [fab_export][ordering][dfm] | L3 | L3 | scripts/lib/fabhash.py | done | design_hash strips exactly this set; the .gbrjob needs JSON-aware key removal because GenerationSoftware spans lines. Proven against two real fab_export runs |
| 171 | 2178 | Raising the .kicad_pro floors to the fab profile at ERROR costs the co | [board_init][rules_gen][gates] | L3 | L3 | scripts/lib/fabfloors.py | done | One source for both project-file writers + check_pro asserted before every write; severities stated explicitly so no KiCad default can hide a floor |
| 172 | 2193 | A live-run fix that does not update its test leaves the suite RED and  | [tests][skill] | L0 | L2 | CLAUDE.md | open | Process rule, currently prose: a red suite at session start is a stop sign, and a live-run fix must update its test in the same change. L2 = a session-start check that reports the suite state before work begins |
| 173 | 2202 | Wave-1 parallel sessions make the route_auto completion assert flaky - | [tests][freerouting][skill] | L0 | L1 | tests/test_route_auto.py | open | Contended runs make the completion assert read as a regression. L1 = the test reporting its wall-clock/pass count so a contended run is recognisable; T5's bench must keep timing metrics out of the deterministic class |
| 174 | 2214 | A frozen KiCad fixture is the file PLUS its stem-matched project files | [bench][kicad-cli][tests] | L2 | L2 | tests/fixtures/stages/manifest.yaml | done | T5: fixtures live in per-role dirs under the ORIGINAL stem with .kicad_pro/.kicad_dru sha-pinned beside the artifact; bench.verify_fixture refuses any drift before scoring |
| 175 | 2226 | Label-vs-symbol-body overlap is a pin-line artifact - measure label-vs-label only | [bench][schematic][geometry] | L3 | L3 | scripts/lib/benchlib.py | done | T5: sch_metrics counts label-label text-box pairs only; the measured 50/50 FP class is pinned in the docstring and the field-vs-body case stays with the schem_refdes audit |
| 176 | 2235 | git status --porcelain collapses an untracked directory to one dir/ line | [git][gates][windows] | L3 | L3 | scripts/gate.py | done | T6: git_commit_on_pass uses --porcelain -uall so the workspace-prefix filter sees every untracked file; regression test covers a brand-new boards/<name>/ workspace |
| 177 | 2245 | ksa mirrors PIN POSITIONS at 90/270; KiCad rotates FIRST then mirrors | [kicad-sch-api][kicad][python] | L3 | L3 | scripts/schlib.py + schem_refdes.py | done | T6 (P4-2): pin_pos reflects ksa's 90/270 answer through the anchor; to_page rotates before mirroring; rotmirror fixture pins both with ERC AND per-pin netlist assertions (ERC alone cannot see swapped pins) |
