# LEARNINGS

Append-only, non-obvious gotchas. Recall by tag/keyword before touching an area.
Entries sourced from prior attempts are marked; re-verify at first use here.

## Tags
[windows] [kicad] [kicad-cli] [ipc] [swig] [freerouting] [easyeda2kicad] [python] [prior-attempts] [geometry] [shapely] [parts] [datasheet] [gerber] [gerbonara] [dfm] [jlc] [fab] [skill] [git] [latex] [spice]

## 2026-07-06 [windows] cp1252 console crashes on non-ASCII output
Printing degree signs, ohms, plus-minus, emoji to a default Windows console raises
UnicodeEncodeError. Every script does `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`
and keeps its own strings ASCII. (Source: ai-ee2, re-affirmed S0.)

## 2026-07-06 [windows] Python does not resolve MSYS /c/ paths
Bash redirects understand `/c/dev/...`; Python `open()` does not. Always pass `C:/dev/...`
style to Python. Bit prior attempts in bash-heredoc + `python -c` mixes. (Source: ai-ee2.)

## 2026-07-06 [kicad] File formats are not forward-compatible - pin ONE KiCad
A KiCad-10-format board is unreadable by kicad-cli 9 (exit 3). This host has 8.0/9.0.5/10.0.3
side by side. The whole pipeline resolves kicad-cli, bundled python, and templates through
`scripts/lib/env.py` (pinned: 10.0.3; AIEE_KICAD_CLI overrides). Never mix versions mid-pipeline.
(Source: ai-ee2 spike; enforced here at S0.)

## 2026-07-06 [kicad-cli] Host quirks: not on PATH; refill-zones is 10.x-only; pos defaults to inches
kicad-cli is NOT on PATH (full path via env.py). `pcb drc --refill-zones --save-board` exists on
10.0.3 but NOT 9.0.5 (S0-verified) - a reason KiCad 10 is the pin. From prior attempts (re-verify
at S2/S12): `pcb export pos` defaults to INCHES (pass `--units mm`); pos CSV headers are
Ref,Val,Package,PosX,PosY,Rot,Side with Side values top/bottom; ERC json nests violations
per-sheet while DRC's are flat.

## 2026-07-06 [ipc] No `kicad-cli api-server` in 9.0.5/10.0.3 - sandboxed-GUI IPC works instead
kipy 0.7.1 ships kipy/server.py driving `kicad-cli api-server`, but that subcommand exists in
neither installed KiCad (spec's "headless=True" claim corrected). S0-verified working path:
launch pcbnew.exe with KICAD_CONFIG_HOME pointed at a scratch config that sets
api.enable_server=true and seeds empty fp/sym-lib-tables (skips first-run dialogs) -> kipy
connects and reads the board; user's real config untouched. Automated in scripts/smoke_ipc.py.
A PCB editor window appears (fine on this desktop host). Headless alternative: SWIG bundled python.

## 2026-07-06 [swig] pcbnew lives in KiCad's BUNDLED bin/python.exe, verified on 9.0.5 and 10.0.3
The venv python has no pcbnew; the bundled one roundtrips CreateEmptyBoard/Save/LoadBoard and has
ExportSpecctraDSN + ImportSpecctraSES on both versions (S0-verified). Prior-attempt gotchas to
re-verify at first SWIG use (S9/S11): Specctra export WEDGES headless on a wx assert unless
suppressed (make wx.App, wx.DisableAsserts(), APP_ASSERT_SUPPRESS); bulk board.Remove() of
tracks/vias corrupts the process heap (do reads first, then save + fresh interpreter);
GetCourtyard() is empty until fp.BuildCourtyardCaches(); bundled python maps bare /tmp to C:\tmp.

## 2026-07-06 [freerouting] 2.2.4 needs Java 25 (not "21+"); batch flags are non-obvious
Java 24 fails with UnsupportedClassVersionError - portable Temurin 25 vendored at tools/jre/
(gitignored; check_env remediation has the re-fetch URL). Batch recipe from prior attempts
(re-verify at S11): `--gui.enabled=false -de in.dsn -do out.ses -mp <passes> -da`; `-da` is
mandatory or it phones home and can stall; `-h` not `--help` (--help launches the GUI). Do not
trust FR's success signal or internal DRC: parse the "(N unrouted)" completion line and gate on
kicad-cli DRC only.

## 2026-07-06 [easyeda2kicad] Imported footprints: missing courtyards + library defects + UA 403s
Prior attempts found easyeda2kicad imports lack courtyard geometry (courtyard-based checks
silently degrade) and can ship self-violating footprints (EP pad with no net, thermal drills
under min-hole). S6's fp_verify must check courtyard presence and a per-part DRC baseline.
EasyEDA endpoints 403 some default User-Agents (browser UA passes). Output layout:
`<base>.pretty/<name>.kicad_mod` + `<base>.kicad_sym`. (Source: both attempts; re-verify S6.)

## 2026-07-06 [python] skidl prints env-var warnings on import - keep JSON stdout clean
Importing skidl without KICAD*_SYMBOL_DIR set emits warnings; check_env redirects
stdout/stderr around package imports so its JSON contract holds. Do the same in any script
importing skidl/kicad_sch_api before emitting JSON.

## 2026-07-06 [python] skidl drops `<script>.log` / `<script>.erc` files in CWD on import
Merely importing skidl creates log/erc files named after the running script (or `skidl_REPL.*`
from `python -c`) in the current directory - the litter visible in AI-EE's repo root. Import
skidl with CWD pointed at scratch (`contextlib.chdir`, see check_env.py) or expect droppings;
gitignore patterns added as backstop. Applies to S7 schematic tooling.

## 2026-07-06 [prior-attempts] Deep routing/placement/fab gotchas archived in the old repos
C:/dev/ai-ee2/LEARNINGS.md and C:/dev/AI-EE/docs/LEARNINGS.md hold machine-verified findings
(2-layer GND-pour fragmentation, stitch-via keepouts, header pin-order routability lever, JLC
CPL rotation handling, wx/SWIG details). Consult them before S9-S12 sessions for FACTS ONLY -
do not port their architecture (user directive: this build follows SPEC.md fresh).

## 2026-07-11 [swig] pcbnew.ZONE_FILLER segfaults headless on Windows 10.0.3 - fill via kicad-cli
ZONE_FILLER(board).Fill(...) segfaults the bundled python headless (with or without the wx.App
+ DisableAsserts recipe). Working pattern (used by tests/golden/generators): build+save the board
UNFILLED via SWIG, then `kicad-cli pcb drc --refill-zones --save-board` fills and persists (fill
survives; a later plain DRC is clean). Also: board.Save() writes a DEFAULT .kicad_pro next to the
board, clobbering any custom one - write the project file AFTER pcb generation.

## 2026-07-11 [kicad] .kicad_pro is the DRC/ERC authority; keep it minimal and hand-rolled
With a .kicad_pro present, DRC rules come from the PROJECT, not the board's embedded setup
(pcb_build's ds.m_TrackMinWidth is ignored; KiCad's 0.2 mm default applied until
board.design_settings.rules.min_track_width went into the pro). rule_severities overrides
(lib_symbol_issues/lib_footprint_issues/footprint_link_issues/lib_symbol_mismatch: ignore) work
from a MINIMAL pro, but pasting the full default-shaped blob (defaults/net_settings/teardrops...)
made KiCad reject/ignore the overrides - warnings returned. Golden corpus: sch_build.write_project.

## 2026-07-11 [python] kicad-sch-api 0.5.6 quirks (verified against kicad-cli 10.0.3 ERC)
(wheel 0.5.6; its __version__ string lies "0.5.5"). Output opens clean in KiCad 10 (V2 evidence).
Gotchas: add_global_label() writes NOTHING to the file (silent no-op) - local labels only, so
root-sheet nets come out "/NAME" in netlists/boards; alphanumeric pin numbers get renumbered when
embedding symbols (USB_B_Micro shield "SH" -> "6") - sch_build._apply_pin_number_fixups repairs
the saved file; a pin touching a wire MID-SPAN does not connect (pins connect at wire ENDPOINTS
only - a PWR_FLAG placed mid-wire ERCs as unconnected); component anchors snap to the 1.27 mm
grid, so off-grid positions silently shift symbols and wires miss pins.

## 2026-07-11 [python] kiutils needs encoding="utf-8" passed explicitly on Windows
SymbolLib/Board/Footprint.from_file default to the locale codec (cp1252) and crash on official
libs containing non-ASCII (RF.kicad_sym). Also kiutils pad size.X/Y are pre-rotation values -
do not derive board-space bounding boxes from them (SMA edge-mount pads are 5.08 mm along X;
kiutils showed 1.5x5.08). Use pcbnew pad dumps (generators/pcb_build.py --pads-out) for geometry.

## 2026-07-11 [kicad] KiCad 10 board files store nets by NAME in segments/vias - mutation surgery
`(net "GND")` (not numeric ids) appears in segment/via/pad blocks, so deterministic text surgery
keyed on coordinates+netnames works (tests/golden/mutations/mutlib.py: exact-match asserts, fixed
UUIDs for added items, refill via kicad-cli after). Double-run byte-identical verified for all 7
mutants. Mutants must be re-run whenever goldens regenerate (gen.py assigns fresh UUIDs).

## 2026-07-11 [kicad-cli] Misc 10.0.3 flags: render uses --width/--height; ERC exit = count
`pcb render` wants --width/--height (-w exists but -h collides with help; use long forms) plus
--quality high. With --exit-code-violations the exit CODE equals the violation count (saw exit 5
= 5 violations) - treat nonzero as "has violations", never as errno. `sch export netlist --format
kicadsexpr` emits multiline-formatted s-exprs (regex across lines, see gen.py parse_netlist).

## 2026-07-11 [kicad-cli][windows] A stale persistent AIEE_KICAD_CLI silently pins the WRONG KiCad
S2 start: env.find_kicad_cli() resolved 9.0.5, not the 10.0.3 pin, because a User-level (registry)
`AIEE_KICAD_CLI` env var pointed at 9.0 - it takes precedence over env.py's 10.x preference (by
design: the documented "flip the pin" override). But 9.0 CANNOT load 10-format goldens (version
20260206): kicad-cli exits 3 "Failed to load board" and writes NO json report, so any wrapper that
reads the report file dies on FileNotFoundError. Removed it via
`[Environment]::SetEnvironmentVariable("AIEE_KICAD_CLI",$null,"User")` (old value
C:\Program Files\KiCad\9.0\bin\kicad-cli.exe). NOTE: a persistent User var is INHERITED by an
already-running shell - deleting the registry value does not clear it from the current process;
`unset AIEE_KICAD_CLI` per shell too. If goldens suddenly "fail to load", suspect this first.

## 2026-07-11 [kicad-cli] DRC/ERC JSON: layer/net/refdes are embedded in item description strings
kicad-cli violation objects are `{type, severity, description, items:[{description, pos{x,y},
uuid}]}`. There are NO separate layer/net/ref fields - they live in the item description text:
"Pad 1 [GND] of D1 on F.Cu" -> net in [brackets], layer after " on ", refdes = [A-Z]{1,4}\d+ (strip
[brackets] FIRST or bracketed pin names like [PB0] get mis-read as refdes). DRC report has three
parallel sections that share this shape and must be merged: violations + unconnected_items +
schematic_parity; ERC nests per sheet under sheets[].violations. `--severity-all` is required or
warnings are omitted. Normalizer + parsers: scripts/kc.py (parse_drc_data / parse_erc_data).

## 2026-07-11 [kicad] cpl-rotation mutant does NOT fail --schematic-parity (manifest note is wrong)
S2 spot-check: `pcb drc --schematic-parity` on the committed tests/golden/mutants/cpl-rotation board
reports 0 violations under 10.0.3, contradicting manifest.yaml's note ("intentionally fails
--schematic-parity too"). The board IS mutated (test_golden proves it differs from golden), and its
DESIGNATED catcher is dfm_check (S12, CPL polarity), not parity - so this is a stale secondary claim,
not a broken fixture. S12 must catch it via CPL/polarity validation, NOT lean on parity. Registered
as verify-later V9.

## 2026-07-11 [geometry][kicad] Pad absolute geometry: center = fp + R(-fp_angle).local; shape angle absolute
S3-verified against pcbnew on usbbuck4/rf4 (10.0.3): in the .kicad_pcb, a pad's `(at lx ly a)` gives
lx/ly RELATIVE to the footprint anchor (pre-rotation) and `a` is the pad's ABSOLUTE board-frame angle
(already includes footprint orientation - a pad drawn at 0 in a fp rotated 90 is saved with pad angle
90). Absolute center = fp_pos + R(-fp_angle).(lx,ly) where R is the standard CCW matrix (KiCad rotates
CW for positive angle because Y points down). Probe: C10 fp(104.8,105.5,90deg), pad1 local(-0.95,0) ->
pcbnew GetPosition (104.8,106.45) = R(-90).(-0.95,0)+fp. shapely: affinity.rotate(pt,-fp_angle,origin=0).
All corpus pad shapes (rect/roundrect/oval/circle) are axis-symmetric, so the SHAPE rotation SIGN does
not change the covered region (rect(+t)==rect(-t)) - only the center convention matters, and it is
locked. Non-symmetric pads (trapezoid/custom) are absent from the corpus; validate their shape-rotation
sign against the pcbnew oracle when first encountered. No FLIPPED footprints in the corpus either (the
B.Cu pads are J1 SMA edge tabs + J2 thru-hole header on non-flipped fps); flip = mirror local x + swap
F/B, implemented but corpus-unvalidated.

## 2026-07-11 [geometry][kicad] KiCad-10 .kicad_pcb: net refs by NAME, no numeric net table; zone fills are keyhole rings
Copper items reference nets as `(net "NAME")` (name only, no number) - there is NO `(net N "name")` table
in these SWIG-saved boards. geom.py resolves a net node by taking its trailing string, falling back to a
number->name table if present (robust to both KiCad formats). Zone fill = one or more `(filled_polygon
(layer L) (pts ...))` blocks; holes are stitched into the outer ring via zero-width keyhole slits, so
`shapely.Polygon(pts).area` gives the correct filled area directly (validated vs zone.GetFilledArea).
Multi-layer zones emit one filled_polygon per layer (group by the block's own `(layer)` tag, authoritative).
An unfilled zone has an outline but zero filled_polygon blocks -> geom flags it (freshness gate).

## 2026-07-11 [geometry][kicad] FLIP is baked into the file (parser must NOT mirror); keepouts never fill
S3 Fable review, verified vs pcbnew on a SWIG-flipped usbbuck4 (C10 rot-90 + J1 USB micro: 15 copper
pads incl. asymmetric x and duplicate "SH" numbers - all exact): pcbnew Flip() REWRITES the footprint
block - pad local coords come out mirrored, angles negated (90 -> 270, fp 90 -> -90), pad (layers)
renamed to B.* - so the SAME abs = fp_pos + R(-fp_angle).local formula covers front AND back parts,
and pad copper layers are read literally. Any parser-side mirror or F/B swap DOUBLE-flips (the bug
geom.py shipped with earlier today; fixed + regression-tested same day). CORRECTS the "flip = mirror
local x + swap F/B" guess in the earlier [geometry] entry above. Also: rule areas
`(zone ... (keepout ...))` NEVER carry filled_polygon blocks - any zone-freshness gate must exclude
them or it hard-fails on every board with a keepout (the plane-split mutant, S4's PRIMARY
check_return_path fixture, has exactly one; geom.assert_fresh() excludes rule areas and exposes them
as BoardGeom.rule_areas metadata instead). Duplicate pad numbers in one footprint are legal (J1 has
3x thru + 4x smd "SH") - never key pad collections by number alone.

## 2026-07-11 [shapely] Per-net copper = union of tracks(buffered)/pads/vias/zone-fills; oracle via TransformShapeToPolygon
S3 round-trip: build per-(net,layer) copper as unary_union of track LineString.buffer(w/2,round),
via Point.buffer(size/2), pad shape polys, and zone filled polys, then `.area` (mm^2; file is already mm).
Ground truth = pcbnew: for the same net/layer, BooleanAdd each track/pad/via TransformShapeToPolygon +
zone.GetFilledPolysList(layer) into a SHAPE_POLY_SET, Simplify, `.Area()`/1e12. Both sides union the SAME
KiCad primitives so they agree tightly on big nets (GND pours <0.5%); tiny signal nets differ more in %
(pad-corner faceting) but negligibly in absolute mm^2 - test tolerances are relative-with-absolute-floor.

## 2026-07-11 [geometry][shapely] Spec-literal return-path corridors FP on every legit board - 3 artifact classes
S4: buffering the centerline by k*w (spec 6.3 step 3) and differencing the reference fill flags
all three CLEAN goldens. The artifact classes and the shipped fixes (check_return_path.py):
(1) round end-caps poke past the landing pad into neighbouring clearance channels -> flat-capped
chain buffers (corridor ends where the trace ends); (2) the net's OWN via/thru-pad punches the
plane (annular clearance void at every legal transition; containment-in-disk waivers fail at the
CORNERS - deficit bits sit just outside any disk); (3) a lone other-net via antipad nicking the
corridor (usbbuck4 golden: VBUS via 0.65 mm from USB_DM = 0.94 mm centerline crossing - benign at
FS, board is clean by design). Fix for 2+3: EXCISE disks (item_r + 0.65 zone clearance) around
every via punching the ref layer + own/refnet thru pads from the deficit, then judge the REMAINDER
(>= 0.05 mm2); slots/moats survive excision because they are not at vias (rf4 slot mutant still
caught at full 1.4 mm crossing). Severity = centerline crossing (error) vs corridor-edge nick
(warning). Other-net THT pad FIELDS deliberately not excised (connector row under a clock is real).

## 2026-07-11 [shapely] linemerge() raises ValueError on a bare LineString input
shapely 2.1.2 ops.linemerge accepts MultiLineString/sequences but raises "Cannot linemerge
LINESTRING(...)" when unary_union of one segment collapses to a single LineString. Guard:
`merged = linemerge(u) if u.geom_type == "MultiLineString" else u`. Bit check_return_path on
single-segment synthetic boards (corpus boards always had multi-segment nets, so it hid).

## 2026-07-22 [kicad-cli][drc] Custom .kicad_dru IS auto-loaded by kicad-cli; rule name is in the description
S8-verified (10.0.3): `kicad-cli pcb drc` reads `<board-basename>.kicad_dru` sitting next to the
board automatically (no flag to point at it). A violated custom rule reports type = the constraint
kind (e.g. "track_width") and description = "Track width (rule 'NAME' min width X; actual Y)" - the
rule NAME is embedded in the description string, so kc.py's normalizer surfaces it in `msg` (parse
`rule '([^']+)'`). This is the enforcement backbone for rules_gen (SPEC P5): any width/clearance/
via/diff-pair minimum expressible as a rule becomes a named DRC violation for free.

## 2026-07-22 [kicad-cli][drc] DRU condition token is A.NetName (A.Net silently matches nothing); LATER rule wins
S8-verified: in a `(condition ...)` the net-name property is `A.NetName == 'GND'` (fired on 20 tracks).
`A.Net == 'GND'` evaluates FALSE silently (0 matches, no error) - a wrong token degrades to "rule never
fires", never an error, so ALWAYS smoke a new condition against a board you know violates it. `A.NetClass
== 'Default'` works (all nets are Default when net_settings is null/empty). When TWO rules of the same
constraint type match one item, the LATER rule in file order wins (a broad `A.NetClass=='Default'` rule
placed after a specific `A.NetName=='GND'` rule overrode it - GND showed 0, default showed all 72).
=> rules_gen must emit GENERIC/baseline rules FIRST and SPECIFIC per-net/per-class rules LAST so specifics win.

## 2026-07-22 [swig][kicad] Headless netlist->board import: SWIG place from netlist = parity-clean; bbox-pack to avoid density DRC
S8-verified: kicad-cli has NO netlist->board path (`pcb import` is for non-KiCad formats only). Working
headless import mirrors pcb_build.py: bundled-python SWIG loads each footprint (FootprintLoad from
share/kicad/footprints/<lib>.pretty), assigns pad nets from the netlist netmap {REF.PAD:net}, saves
unfilled. `kicad-cli pcb drc --schematic-parity` then reports 0 parity issues (proves the import is
correct) with only unconnected_items (expected - unrouted). Footprints placed too close trigger
courtyards_overlap/shorting_items/solder_mask_bridge/silk_over_copper: pack them on a shelf grid by
GetBoundingBox(False,False) (needs BuildCourtyardCaches() first) + margin => 0 non-parity violations.
board_init acceptance = parity==0 AND (violations - unconnected_items)==0. Bundled python has NO yaml -
board_init runs in venv (yaml+sexpdata) and shells the SWIG worker a JSON job (bundled python has json).

## 2026-07-22 [kicad][swig][geometry] Stackup: SWIG can't build it - inject the (stackup) block as text
S8: `ds.GetStackupDescriptor().BuildDefaultStackupList` is absent on the 10.0.3 SWIG wrapper
('SwigPyObject' has no attribute) - confirms S1's "stackup didn't serialize". Working path: after the
SWIG save, TEXT-inject a `(stackup ...)` block right after `(setup\n` in the .kicad_pcb, built from
stackups.yaml. geom._build_stackup reads it (assumed=False, source "board (stackup)") and kicad-cli DRC
still loads the board. geom's copper-to-copper walk ignores the outer silk/paste/mask layers correctly
(they sit before the first / after the last copper), so a full realistic block parses to the right
per-gap dielectric heights + epsilon_r. Layer names must match the board's copper layers exactly.

## 2026-07-22 [parts][easyeda2kicad] Pinned easyeda2kicad 1.0.1 wraps an ANONYMOUS JLCPCB parts search (resolves V5)
`from easyeda2kicad.easyeda.easyeda_api import EasyedaApi; EasyedaApi().search_jlcpcb_components(
keyword, page=1, page_size=N, part_type="base"|"expand")` hits JLCPCB's public parts endpoint
(`jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`) with NO
credential and returns `{total, results:[{lcsc, name, model, brand, package, category, stock,
type: Basic|Extended, price, price_breaks, min_qty, reel_qty, description, url, datasheet,
attributes:[{name,value}]}]}`. Verified live from this host 2026-07-22: "100nF 0603 X7R" -> total
18783, C14663 Basic stock 88M. This is parts_search.py's PRIMARY path - the spec's "credentialed
JLCPCB Parts API" (V5, still needs an access application) is NOT required. jlcparts SQLite is an
optional local cache (none present on this host); web-search is the agent-level last resort. Also
`EasyedaApi().get_cad_data_of_component(lcsc)` pulls raw CAD JSON. Endpoint could change/rate-limit
- network tests are `net`-marked; parts_search exits 2 with remediation when the live call fails
and no --db cache is given.

## 2026-07-22 [easyeda2kicad][kicad-cli] Full export layout + LEGACY footprint format that still loads in KiCad 10
`python -m easyeda2kicad --lcsc_id=Cxxxx --full --output <base>` writes THREE artifacts:
`<base>.kicad_sym`, `<base>.pretty/<fpname>.kicad_mod`, `<base>.3dshapes/<name>.{wrl,step}` (the
fp/sym names come from EasyEDA, e.g. C1525 0402 cap -> footprint "C0402"). Footprints come out in
the KiCad-5 LEGACY format: `(module NAME (layer F.Cu) (tedit ..) ... (pad N smd rect (at x y rot)
(size w h) (layers F.Cu F.Paste F.Mask)))` - top token is `module` not `footprint`, layer tokens
are UNQUOTED. They still load in KiCad 10: `kicad-cli fp upgrade <lib.pretty>` rewrites them to
`(footprint "NAME" ...)`, and `kicad-cli fp export svg` renders them. So fp_verify must parse BOTH
`(module ...)` and `(footprint ...)` (unquoted AND quoted layer tokens). Courtyard presence is
PART-DEPENDENT (C1525 0402 HAS an F.CrtYd rect; the old [easyeda2kicad] entry's "missing
courtyards" is not universal) - fp_verify checks for it and warns if absent, never assumes.

## 2026-07-22 [kicad-cli] `fp export svg <lib.pretty> --output <dir>` needs the output dir to EXIST first
It prints "Plotting footprint ..." then "Failed to create file ... Error creating svg file" and
writes nothing if <dir> is missing (the overall exit is still success-ish). mkdir the output dir
before calling. With the dir present it writes one `<fpname>.svg` per footprint. (Used as the
"footprint loads in KiCad" gate for lib_pull / fp_verify.)

## 2026-07-22 [datasheet][python] No PDF lib was in the venv; added pypdf 6.14.2 (pure-python)
S6 needs PDF text extraction for datasheet_extract.py; none of pypdf/pdfplumber/PyMuPDF/pdfminer
were installed. Added `pypdf==6.14.2` (pure-python wheel, no native deps, imports clean on 3.13) to
requirements.txt/lock. `from pypdf import PdfReader; PdfReader(path).pages[i].extract_text()` works
on text-based PDFs (image-only datasheets yield empty text - the LLM agent reads those from the PDF
pages directly). A minimal valid one-page text PDF can be hand-assembled in ~15 lines for a
hermetic fixture (see tests/fixtures/parts builder) - no authoring lib needed.

## 2026-07-22 [geometry][kicad] KiCad 10 stores refdes/value as (property ...); fp_text/property angle is ABSOLUTE
S5 check_silk: reference designators and values are NOT fp_text in KiCad-10 .kicad_pcb - they are
`(property "Reference" "U1" (at lx ly angle) (layer "F.SilkS") (effects ...))` inside the footprint
(there are also separate fp_text user items). A silk-over-pad checker that only reads fp_text sees
1 text per board (the top-level gr_text label) and misses all 17-24 refdes. Parse `property` nodes
too (text = the 2nd string). CRUCIAL: the stored text `angle` is ABSOLUTE board-frame (already
includes the footprint rotation), exactly like pad angles ([geometry] entry above) - do NOT add the
footprint rotation. Adding it swung a vertical refdes (rf4 C15, fp rot -90, text angle 270)
horizontal across its own pads -> false positive. Position IS local (transform by fp_pos +
R(-fp_angle).local); only the angle is pre-baked. (hide) detection: `(hide yes)` hides, `(hide no)`
does not - test the value, not mere presence.

## 2026-07-22 [geometry][kicad] KiCad text bounding box, calibrated vs pcbnew GetBoundingBox (10.0.3)
For silk-over-pad geometry, KiCad's PCB_TEXT.GetBoundingBox at size s (mm), stroke thickness t:
height ~= 1.6*s + t (glyph-independent); width is PROPORTIONAL/per-glyph (W~1.39*s, M~1.23, digits
& caps ~0.94-1.03, i~0.56). A per-char advance of 1.0*s + t is a good average box. Golden refdes
clear pads by as little as 0.10 mm (bbox), so a silk-over-pad rule keyed on bbox-touch false-positives;
use "pad CENTER inside the silk box OR silk covers >=50% of the pad" instead - robust to +/-0.1 mm
box error and still catches centered text (the mutant). Measure with the bundled pcbnew, not a font lib.

## 2026-07-22 [shapely][geometry] Diff-pair "skew" mutant is a COUPLING defect, not a length mismatch
S5 check_diffpair: the diffpair-skew mutant adds a 6.2 mm meander to the SHORTER net (USB_DM), so raw
total-length skew goes DOWN (golden |DP-DM|=5.55 mm -> mutant 0.65 mm) - a length-match check both
FALSE-POSITIVES on the clean golden (5.55>5) and MISSES the mutant. The real signature is UNCOUPLED
LENGTH (run of one trace whose partner is >~3x the nominal gap away): golden 2.48 mm, mutant 12.96 mm
- clean separation. Manifest "golden ~2.5 mm skew" == golden uncoupled length, confirming intent.
Also: length skew must be measured on the BRANCH-FREE trunk (segment-graph shortest path between the
two matched pad terminals), else a USB D+ pull-up stub (R3, +3.1 mm) inflates DP and breaks the match;
a stub joins mid-segment so it lands in its own graph component and Dijkstra naturally excludes it.
Report gap deviation as facts only (never gate on it): a legit pair fans out to >nominal gap at its
pad breakouts. Guard empties: an unrouted half -> shapely distance to an empty geom is NaN (invalid
JSON + silently disables the check); a 1-copper-layer board -> epsilon_between divides by zero.

## 2026-07-22 [python] kicad-sch-api 0.5.6 hierarchical sheets DO serialize (global labels still do not)
S7: add_sheet / add_sheet_pin / add_hierarchical_label all write to the saved file and ERC/netlist
correctly under kicad-cli 10.0.3 (S1 only proved the flat path; add_global_label remains a silent
no-op). API shape: sheets come back as plain DICTS (sch.sheets.get_sheet_by_name(name)["pins"]);
sheet-pin positions are ABSOLUTE, with left-edge position_along_edge measured from the sheet BOTTOM.
Hierarchy net-name semantics: power SYMBOLS make a net global across all sheets (no sheet pin
needed); a child net merged with the root via a sheet pin takes the ROOT-side name ("/VIN");
child-internal nets become "/<sheet>/NAME". Consequence: wiring labels are sheet-local, so metadata
recording "exact board net names" (decoupling rail) must carry the FINAL name - schlib.py's
rail_net/gnd_net override exists for this, and netlist_audit.py --decoupling catches the drift.

## 2026-07-22 [python][erc] Labels attach anywhere ALONG a wire; every wire endpoint needs a pin or label
A label whose anchor lands on a foreign wire RUN merges the two nets (ERC multiple_net_names plus a
real netlist short): hierdemo's cap row initially put a vertical cap stub through the IC's GND label
anchor -> GND merged with +3V3. Pins connect at wire ENDPOINTS only, but labels bind mid-span too -
generated placement must keep label anchors off foreign wires (schlib caps_at is caller-guaranteed
free area). Conversely a wire ENDPOINT carrying neither pin nor label warns unconnected_wire_endpoint;
a label ON the endpoint terminates it legally (flag-only rail clusters label the start endpoint).

## 2026-07-22 [kicad-cli] Netlist export facts (10.0.3, kicadsexpr)
Netlists are MULTILINE pretty-printed - parse with sexpdata, not line regexes. Every NC/unconnected
pin appears as a singleton net "unconnected-(REF-PINNAME-PadN)" with a "+no_connect" pintype suffix
(blinky2: 32 of 43 nets). Power symbols and PWR_FLAG (#PWR/#FLG refs) are EXCLUDED from netlist
nodes entirely, so "is this rail driven" is NOT answerable from the netlist when the driver is a
flag or connector - ERC owns that check; netlist_audit.py warns on undeclared power_in feeders
instead of driver presence.

## 2026-07-22 [ipc] Sandboxed-GUI IPC REGRESSED on this host: "KiCad is not ready to reply" (V8 evidence)
S9: the S0-verified gui-sandboxed path (scripts/smoke_ipc.py, unchanged) now returns verdict
`unavailable` - pcbnew.exe launches, the kipy socket answers, but every request within the 45 s
window errors "ApiError: KiCad returned error: KiCad is not ready to reply" (a custom V8 probe
opening a real golden also never connected in 60 s). kipy 0.7.1 edit-op coverage (move/rotate via
update_items - the API exists: FootprintInstance.position/.orientation setters + b.update_items +
b.save) is therefore UNVERIFIABLE at this pin, and library research confirms headless kipy only
arrives with KiCad 11. S9 decision: place_edit.py drives SWIG bundled python (headless, proven at
S8); kipy/IPC is the KiCad-11 migration target. If a future session needs the GUI-IPC path, debug
with pcbnew stdout/stderr UNsuppressed first (a modal dialog is invisible under DEVNULL).

## 2026-07-22 [swig] Placement-edit API facts on 10.0.3 (place_swig.py, live-verified)
FindFootprintByReference/SetOrientationDegrees/SetPosition/Flip/SetLocked all exist and work
headless. SetOrientationDegrees NORMALIZES to (-180, 180]: setting 270 stores -90 in the file and
GetOrientationDegrees returns -90 - always compare angles mod 360 (place_edit._angdiff), never
literally. pcbnew.FLIP_DIRECTION_LEFTRIGHT does NOT exist on the 10.0.3 SWIG wrapper - use the
legacy bool: fp.Flip(fp.GetPosition(), True) (flip_fixture.py's fallback branch is the ONLY branch
here). mm->IU: pcbnew.pcbIUScale.mmToIU(32.3) == 32300000 (correct rounding) while
pcbnew.FromMM(32.3) == 32299999 (float truncation, prior-attempt fact re-verified) - workers that
write coordinates must use mmToIU. board.Save() writes sibling project files; place_edit sidesteps
any clobber by staging in a scratch dir and os.replace()-ing ONLY the .kicad_pcb back (the real
.kicad_pro is test-guarded byte-identical across edits).

## 2026-07-22 [geometry][placement] Courtyard containment needs edge-part exemptions (corpus-calibrated)
Two legality-gate false-positive classes on legitimate boards: (1) edge-mount connectors - the rf4
SMA clamps the board edge and keeps only 35% of its courtyard on-board (usbbuck4's USB micro also
overhangs) -> declared-edge parts get a >=25% on-board threshold (placelib.ON_BOARD_MIN), not full
containment, and EDGE_TOL 2.5 mm accepts the golden's ~2 mm-inboard THT headers; (2) board_init's
corner mounting holes (board_only) sit with courtyards kissing/crossing the outline by construction
-> non-movable footprints are exempt from outline containment (they stay overlap obstacles).
Golden refdes/angle probe C10 (fp 104.8,105.5 rot90, pad local -0.95,0 -> abs 104.8,106.45) is
pinned as placelib's transform regression test.

## 2026-07-22 [placement][python] Spring embedding: classic F-R attraction is d^2/k - linear-in-d starves it
place_seed's first cut used attraction ~ w*d/k against repulsion k^2/d; repulsion dominated at
board scale (k = sqrt(area/n) ~ 14 mm), exploding singletons/crystal cluster to the interior
corners - seed HPWL came out WORSE than the S8 shelf pack (948 vs 832 mm). Classic
Fruchterman-Reingold attraction w*d^2/k fixed it in place: seed HPWL 484 mm vs golden hand
placement 452 mm (within 7%), crystal + load caps adjacent to the MCU, decoupler Manhattan
2.5-6.6 mm. Render and EYEBALL the seed (kicad-cli render) whenever touching the force model -
the legality gate cannot see "legal but scattered".

## 2026-07-23 [placement][python] SA stall detection must not count the hot phase
place_anneal's first schedule counted "epochs without a new best" unconditionally: at high T the
walk sits far above the incumbent best by design, so stall=15 killed the run at epoch 15 while
acceptance was still ~75% - 17.1% HPWL improvement instead of 43.4% on the same seed. Fix: the
stall counter only ticks when the epoch acceptance ratio is < 0.2 (cold regime); hot epochs reset
it. Companion facts that worked as-is: T0 = 20x mean uphill delta from ~50 sampled moves,
TimberWolf-style window W *= (0.56 + alpha), cooling 0.6/0.9/0.95/0.9/0.75 by acceptance band.
Perf on usbbuck4 (13 movable clusters, 46 nets): ~0.8 ms/move with incremental cost (per-net HPWL
rebuild, moved-cluster-only shapely overlap with bbox prefilter, per-net MST + crossing recount,
congestion cell diffs); full_sync() every epoch kills float drift (invariant pinned by test).

## 2026-07-23 [swig][freerouting] S11 DSN/SES roundtrip verified on 10.0.3 (V1/V7/V3 resolved)
ExportSpecctraDSN(board, path) and ImportSpecctraSES(board, path) (two-arg forms) work headless
from the bundled python WITH the wx recipe (wx.App() + wx.DisableAsserts() +
app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)); wx sprays "Adding duplicate image handler" lines to
stdout, so SWIG workers must return results via a FILE (route_swig.py's contract), never stdout.
A FILLED zone exports as "(plane NET ...)" and Freerouting connects pads to it ITSELF, including
dropping new stitch vias to reach a back-side plane (blinky2 smoke: 26 vias with plane vs 7
without). Post-SES the pre-existing fills are STALE (33 clearance/hole violations on the smoke
board); `kicad-cli pcb drc --refill-zones --save-board` clears them (0 after). SES import only
ADDS copper; ImportSpecctraSES on an already-routed board would re-add echoed guide wires as
duplicates - route_auto never imports into a board that already got that session's copper.

## 2026-07-23 [freerouting] 2.2.4 verified flags + completion parse (this host, our own DSN)
`--gui.enabled=false -mt 1 -is sequential -da --logging.file.enabled=false -mp N -de in.dsn -do
out.ses` exits 0 and is the deterministic set (-mt >=2 has a known clearance bug + nondeterminism;
-is sequential removes item-order randomness). -da does NOT disable the update check (an outbound
"New version available" call still happens and must be tolerated offline); it disables analytics.
Completion parse priority: session line "final score: S (N unrouted)" > LAST pass line "(N
unrouted)" > a pass line WITHOUT the parenthetical means 0 unrouted. FR's own success flag and
internal DRC stay untrusted - kicad-cli DRC is the gate (routelib.parse_fr_log pins all of this).

## 2026-07-23 [parts][python] KRT (KiCadRoutingTools 0.19.0) vendored: no-KiCad headless router
tools/krt/KiCadRoutingTools-0.19.0/plugins (MIT, pinned zip + prebuilt abi3 grid_router pyd -
imports clean in venv python 3.13; sha256s in tools/krt/PROVENANCE.txt; env.find_krt() resolves).
Facts: scripts must run with cwd=plugins (relative sys.path inserts); pass args as a LIST (net
names like "/USB_DP" get MSYS-path-mangled through a shell); ALWAYS pass --no-fix-drc-settings
(route.py silently rewrites the sibling .kicad_pro DRC floors); route to a FRESH output path per
attempt; results = last "JSON_SUMMARY: {...}" stdout line; output uuids are uuid4 (reruns never
byte-identical - compare parsed state); scipy is a hard dependency (added scipy==1.18.0 to the
venv pins, S6-pypdf precedent).

## 2026-07-23 [freerouting][routing] FR 2.2.4 DSN reader can WEDGE on KRT guide-wire copper - detect + fall back
Boards carrying KRT-routed copper (either power net's tracks+vias) drove Freerouting into
INFINITE RECURSION at app.freerouting.board.PolylineTrace.combine while READING the design
(before pass 1); the same board with all routed copper stripped routes in 2.8 s. Signature:
rung process timeout with ZERO parsed pass lines. route_auto's mitigation (S11-verified): skip
the remaining ladder rungs (same DSN, same wedge) and fall back to KRT for the whole remainder
(batched route.py --nets over the DRC-unconnected nets, kept only when the DRC strictly
improves). Related Windows fact: killing the parent shell does NOT kill the FR JVM - orphaned
java.exe grinds forever; kill the process tree explicitly when cancelling.

## 2026-07-23 [routing][placement] P7 chain order is board-class dependent; plane nets are never outer-trunked
2-layer: route_critical -> route_auto -> stitch -> repair -> cleanup (pre-route stitch vias are
FR obstacles - prior-attempt fact confirmed). 4-layer: route_critical -> stitch -> route_auto
(stitch pre-connects SMD pads to inner planes; FR's remaining work shrinks ~40%). A power net
CARRIED BY A PLANE must not be trunk-routed on outer layers: the trunk's vias fragment the
plane locally (live: a +3V3 outer trunk starved J2's thermal spokes onto an In2 island -
error starved_thermal). route_critical skips plane-carried nets (plane IS the trunk).

## 2026-07-23 [stitch][geometry] Via-candidate obstacles = WIRED copper only; single-layer-bond vias dangle
Foreign ZONE FILLS must not block via candidates (fills re-flow at refill - a via through a
foreign plane gets a legal antipad): treating fills as obstacles rejected 40/40 candidates on
the 4-layer board (In1/In2 planes cover everything). Only foreign tracks/pads/vias block, plus
rule-area keepouts and the 0.5 mm hole-to-hole floor (net-agnostic - same-net drills count).
Separately, KiCad flags via_dangling for a via bonded on only ONE layer even when it sits in a
plane fill - grid/area stitch vias must verify same-net copper contact on >= 2 layers.

## 2026-07-23 [kicad-cli][drc][zones] zones_intersect fires on same-net same-priority overlaps
KiCad 10 DRC rejects overlapping zones of the SAME net at the SAME priority - a plane generator
re-run that duplicates a pour breaks DRC. planes_gen guards with an existing-fill coverage skip
(>= 80% covered -> no-op "existing") and assigns distinct priorities to any same-layer
overlapping pair (island-in-pour needs the island HIGHER).

## 2026-07-23 [placement][routing] Courtyard-only packing is silk-blind; KRT leaves sub-grid crumbs
place_anneal's tight packing (courtyard legality only) put refdes silk over neighbour pads -
12 silk DRC warnings that fail the err+warn drc_routed gate; the SEEDED placement is silk-clean.
Until placement/fixers are silk-aware (P6 stage-3 agent / P8 silk fixer, S13), route from the
seed. Also: KRT output can contain sub-0.05 mm segments that KiCad flags track_dangling but sit
below route_cleanup's touch tolerance - route_auto's KRT pass sweeps them (removal is
connectivity-safe: neighbouring round caps overlap far beyond the crumb length). And
route_cleanup's loop-breaking can remove a load-bearing segment when connectivity runs through
a plane (union-find/fill edge case) - it SELF-DETECTS (exit 1 cleanup_regression, board left
modified); the orchestrator restores (git or snapshot) and continues without cleanup.

## 2026-07-24 [gerbonara][gerber][geometry] ArcPoly.outline drops curvature - tessellate arcs before shapely
gerbonara's `Flash.to_primitives('mm')[0].to_arc_poly()` returns an ArcPoly whose `.outline` holds
only the segment ENDPOINTS; the curvature lives in its arc segments (`.segments` / `.arc_centers`).
Feeding `.outline` straight into `shapely.Polygon` therefore turns a ROUND pad into a coarse polygon
(measured on our own exports: a 0.6 mm via pad read as ~0.55 mm inscribed, i.e. a phantom 0.025 mm
annular-ring shortfall that failed all 25 blinky2 vias). Fix: `.approximate_arcs(max_error=1e-3)`
BEFORE `.outline` (gerblib.ARC_MAX_ERROR_MM). Even then, keep a geometric tolerance in the
comparisons - blinky2's vias sit EXACTLY on JLC's 0.15 mm annular floor, so micron-scale flattening
error must not fail them (dfm_check.GEOM_TOL_MM = 2e-3, two orders below any real DFM delta).

## 2026-07-24 [dfm][gerber] Annular ring must be measured against PAD FLASHES only, never pours
A zone fill exports as a Region whose exterior is a keyhole ring threading past every via's antipad
(the LEARNINGS [geometry] keyhole entry). Counting pours as "the copper around the hole" therefore
measures the ANTIPAD GAP, not the ring, and invents a ~1 mil shortfall on perfectly good vias
(blinky2: one hole reported 0.1245 mm). dfm_check.check_annular_ring considers `lg.pads` (flashes)
on the OUTER layers only; a hole with no flash around it (NPTH, inner-only) is skipped, not failed.

## 2026-07-24 [dfm][kicad] CPL polarity: compare per PAD NUMBER, not per net (this is what catches V9)
`pcb drc --schematic-parity` compares NET MEMBERSHIP, so a polarized part rotated 180 deg with its
pad nets swapped is invisible to it (confirmed 10.0.3, the cpl-rotation mutant - V9 resolved S12).
Comparing the board's `pad number -> net` against the netlist's `pin -> net` catches it immediately,
and the pad GEOMETRY yields the misorientation: find the pad actually carrying each expected net,
take the angle from the footprint's pad centroid to that pad vs the pad that should hold it; a
consistent delta (spread < 5 deg) is the rotation the CPL would ship (D1 -> exactly 180.0). A
mismatch with no consistent permutation is a wiring error (`pad_net_mismatch`), not a rotation.

## 2026-07-24 [dfm][gerber] Clearance from gerbers = gaps between UNIONED copper islands
Gerbers carry no net data, so the only honest grouping is "touching copper is one conductor" - union
the layer, explode into components, measure pairwise gaps. That is exactly what a fab's DFM engine
sees. Two guards are required: skip distances <= 1e-4 mm (numerically-abutting features that are
really connected, else every trace/pad junction is a phantom zero-clearance short), and prefilter
pairs with an STRtree or the comparison is quadratic over hundreds of islands.

## 2026-07-24 [jlc][kicad-cli][fab] JLC export facts (10.0.3, verified on our goldens)
`pcb export gerbers` with no `--layers` emits 25 files incl. Adhesive/Courtyard/Fab/User_* - curate
to copper + silk + mask + paste + Edge.Cuts for the upload zip. There is NO Protel-extension toggle
in kicad-cli (it always writes standard .gtl/.gbl/.g1/.gts/... which current JLC accepts), and the
drill lands as ONE .drl alongside. Do NOT pass `--subtract-soldermask`: silk-over-pad must stay
VISIBLE in the gerber or dfm_check cannot see what the fab would clip. Board copper order in the
file's `(layers)` block is by layer ID, where B.Cu (31) can precede the inners - re-sort to
PHYSICAL order (F, In1..InN, B) or outer-vs-inner copper-weight rules get applied to the wrong
layer. `pos` defaults to inches (kc.py forces mm). kicad-cli writes G90 after the Excellon header,
which makes gerbonara emit a SyntaxWarning it then parses correctly - suppress it at the read site
(gerblib) so library callers like gate.py keep clean stderr, not just the CLI.

## 2026-07-27 [skill][git] gate.py --commit is a repo-root `git add -A` - dirty trees get swept
The gate-pass commit helper (S2, wired into the S13 SKILL.md flow) stages EVERYTHING at
env.repo_root() and commits - it cannot scope to the design workspace. During /ai-ee runs (S14+)
any unrelated dirty file in the repo (parallel-session WIP, scratch edits - this repo has had
parallel WIP at S6/S7/S12) silently rides along in gate commits. Keep the tree clean during
pipeline runs, or commit/stash WIP first. Also the reason dry-run tests must NEVER use --commit
(they run inside this repo; test workspaces live in pytest tmp dirs instead).

## 2026-07-27 [easyeda2kicad][erc][python] Pulled-lib pin electrical types are junk; ERC gate needs a retype pass
easyeda2kicad symbols carry `unspecified` electrical type on nearly every pin (a few arbitrary
`input`, e.g. chip resistors and crystals). kicad-cli 10.0.3 ERC --severity-all then floods
`pin_to_pin` warnings ("Unspecified and Unspecified are connected", one per pin pair) plus FALSE
`pin_not_driven` errors on the input-typed pins - the P4 gate (errors+warnings=0) cannot pass on
an untouched pulled lib. Fix at the SOURCE, not the .kicad_pro severities: retype pins in
lib/aiee.kicad_sym from the datasheet-extract JSON (supplies/grounds -> power_in, regulator output
-> power_out, everything else passive; a duplicate output pin like a SOT-223 tab stays passive or
ERC raises power_out<->power_out). stm32-blinky reference: boards/stm32-blinky/kicad/gen/
lib_pin_types.py (idempotent, re-run after any lib_pull refresh). Two subtleties: (a) schlib.py
--pins REPORTS "passive" for pins the file stores as `unspecified` (kicad-sch-api mapping) - the
lib file text / ERC output is the type ground truth, not pin_table; (b) kicad-sch-api resolves
lib_ids via its global cache which does NOT read the project sym-lib-table - generators must call
`ksa.get_symbol_cache().add_library_path(<abs path to aiee.kicad_sym>)` before add_component, and
the mtime-based cache DID pick up the lib edit correctly on rebuild (verified: embedded lib_symbols
in the saved .kicad_sch carried the new types).

## 2026-07-27 [board_init][kicad] P5 gate: --schematic SameFileError in-place + LCSC field parity warnings fail self-check
Two board_init findings from the first real P5 run (stm32-blinky). (a) `--schematic` does a bare
shutil.copy to `<out>/<name>.kicad_sch`; when the schematic ALREADY lives in the out dir under that
name (the normal pipeline layout), copy raises SameFileError -> exit 2 AFTER the board is written
but BEFORE self_check runs. Workaround without code/hand edits: pass a byte-identical staged copy
from a temp dir (parity check still runs). Omitting --schematic silently skips parity - don't.
(b) Boards whose symbols carry an LCSC field (every real P4 output; goldens didn't) fail the parity
gate: netlist has the LCSC property but board_swig.py copies NO fields into footprints, so KiCad 10
DRC (--severity-all) emits `footprint_symbol_field_mismatch` "Missing symbol field 'LCSC' in
footprint" - one warning per component, counted as parity. Net-membership parity itself was 0.
Fix belongs in board_init/board_swig (copy netlist component properties into footprint fields), not
in the schematic.

## 2026-07-27 [placement][drc][geometry] P6 gate is courtyard-blind: place_seed output shorted 9 pad pairs while gate=PASS
First real P6 run (stm32-blinky, 20 parts). place_seed's satellite ring passed `gate.py --gate place`
with 0 violations, yet KiCad DRC on the SAME board reported 21 copper errors (9 shorting_items,
9 solder_mask_bridge, 2 clearance, 1 copper_edge_clearance) + 68 silk warnings. Cause: placelib's
legality is courtyard-only, and several footprints have courtyards SMALLER than their pad field -
the LQFP48 U1's courtyard is a 7.05 mm box while its pads span 10 mm, so decouplers legally parked
"outside the courtyard" sat ON the pin tips (the deferred D2 quirk is not an isolated library bug).
Corollary: check_silk is far more lenient than DRC (its "pad centre covered OR >=50% of pad" rule
reported 12 hits where DRC found 68) - never treat check_silk=0 as silk-clean. Two more facts: the
board-setup edge clearance (0.50 mm) is STRICTER than the generated .kicad_dru floor (0.30 mm), and
`check_silk` violation `refs` names the PAD's owner, not the silk's owner (attribute the silk owner
yourself before blaming a part). Practical P6 recipe that ended err+warn=0: anneal candidate ->
clearance-driven repair against real DRC semantics (pad-pad >=0.5, silk-pad/silk-silk >=0.25,
courtyard gap >=0.15, pad-edge >=0.62 mm) -> verify with `kc.py drc`, not the place gate alone.

## 2026-07-27 [placement][python] Coordinate descent cannot evict a blocker; anneal candidates repair better than the seed
Two placement-search facts from the same run. (a) A per-part cost descent never moves a part whose
OWN cost does not improve, so a blocker parked between a decoupler and its pin is immovable: C1 sat
8.7 mm from U1.48 with D2 in the corridor and no single-part move (even at 30x decoupler weight,
12 mm cap) could fix it. A 2-level cooperative search (grid over the blocker x best-response grid
for the riders) dropped C1 to 2.7 mm. (b) The S13 note "the SEEDED placement is silk-clean, route
from the seed" is board-specific: here the anneal candidates were silk-DIRTIER than the seed
(22-26 vs 12 check_silk hits) but structurally far better (HPWL 160 vs 313, crystal 4.1 vs 5.5 mm),
and repairing cand1 beat repairing the seed on every metric (HPWL 227 vs 330, crystal 4.1 vs 12.0,
both DRC-clean). Repair the best candidate; do not fall back to the seed on silk counts alone.

## 2026-07-28 [easyeda2kicad][parts] Symbol pulls are NOT idempotent for names with spaces or '/', and lib_pull hides a failed symbol pull
Three machine-verified facts from the usb-buck P3 library pull (18 parts, easyeda2kicad 1.0.1).
(a) `ExporterSymbolKicad.save_to_lib` guards with `id_already_in_symbol_lib(component_name=
self.input.info.name)` - the RAW EasyEDA name - but writes the block under `sanitize_fields(name)`
(spaces stripped, `/`->`_`). Any part whose EasyEDA name contains a space or slash therefore never
matches its own guard and is APPENDED AGAIN on every re-run: `HX PZ2.54-1x4P ZZ`,
`TS263065A 340gf SX BD SMD Tactile Switch`, `CKCS4030-4.7uH/M` turned an 18-symbol lib into 21 on
the second pull. Duplicate `(symbol "NAME")` blocks are silently accepted by kicad-cli. lib_pull.py's
"registration is idempotent, re-runs are safe" only covers the lib-TABLES; the symbol library is not.
Re-pull only with `--overwrite`, or de-duplicate afterwards (keep first occurrence).
(b) `_pull_one` returns "pulled"/"exists" whenever the LCSC id is found in ANY existing footprint file,
so a part whose footprint is already present reports success even when its symbol pull failed - a full
18-part re-pull reported 12 "pulled" while the EasyEDA API 403'd every single symbol request and the
symbol lib was never recreated. Check `payload.symbol_lib` / the symbol count, never the per-part status.
(c) The anonymous EasyEDA CAD endpoint rate-limits: ~3 full passes over 18 LCSC ids within ~15 min
returned `HTTP Error 403: Forbidden` for every subsequent part, and a 60 s backoff was not enough.
Treat a pulled lib as expensive: back it up before deleting, and do not re-pull to "clean up".

## 2026-07-28 [datasheet][parts] LCSC datasheet PDFs are fetchable via the wmsc.lcsc.com path transform
`https://www.lcsc.com/datasheet/lcsc_datasheet_<id>_<name>_<lcsc>.pdf` serves a JS-rendered viewer
shell (curl gets `<!doctype html>`, ~50 KB), which is why direct datasheet fetches "fail". The same
document is served as a real PDF from
`https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/<id>_<name>_<lcsc>.pdf`
(drop `lcsc_datasheet_`, swap the host/path). Verified on C2286 (KT-0603R, 11 pages) and C2939564
(HOOYA USB-111FD-B-SU, 1 page) with a browser User-Agent. Some parts.json entries already carry the
wmsc URL directly. The venv has pypdf (text only) - no rasteriser - but the Read tool renders PDF
pages, which is how the J1 land pattern was read.

## 2026-07-28 [easyeda2kicad][drc] Every pulled footprint ships silk under 0.25 mm from copper; 4 put a silk dot INSIDE pad 1
Measured across all 12 footprints of the usb-buck pull (silk stroke edge to pad copper edge, stroke
width included). C0603, C0805, R0603 and LED-SMD_L1.6-W0.8-R-RD each carry a tiny `fp_circle` on
F.SilkS (r 0.03-0.05, width 0.06-0.10) sitting ON or INSIDE pad 1 - gaps -0.11, -0.105, -0.092,
-0.10 mm. On this board that is ~20 component instances each contributing a guaranteed
silk_over_copper DRC hit BEFORE placement, which explains most of the S13 run's 68 silk warnings.
The remaining 8 footprints have no overlap but sit well under the 0.25 mm silk-pad rule
(SW-SMD 0.015, IND 0.055, LQFP-48 0.060, USB 0.085, TSOT-26 0.105, SOT-23-6 0.154). The offending
dots all have stroke width < 0.15 mm (JLC's minimum silk line width), so a safe library sanitiser is
"drop F.SilkS graphics with width < 0.15". Related: those same sub-0.15 strokes are why some pin-1
marks do not print - the TSOT-26 (AP63203) pin-1 indicator is a width-0 zero-area `fp_poly` plus a
0.06-wide dot, and its real marker circle is on Cmts.User, so U2 has NO printable pin-1 mark.

## 2026-07-28 [easyeda2kicad][drc] CORRECTION + fix recipe for the silk-on-pad dots (measured against real DRC)
The entry above over-claimed: it predicted ~20 guaranteed silk_over_copper hits from the four
library dots. MEASURED with a scratch board (one instance each of C0603/C0805/R0603/LED-SMD/
TSOT-26, `kc.py drc --severity-all`, KiCad 10.0.3): only ONE fires - the LED's dot (r 0.05,
stroke 0.10, centred exactly on pad 1's corner) -> `silk_over_copper` "Silkscreen clipped by
solder mask". The three 0.06-stroke dots on C0603/C0805/R0603 sit INSIDE pad 1 and do NOT trip
DRC; KiCad's clipped-by-mask test evidently needs the item to straddle the mask aperture by more
than a hair (each of those crosses the pad edge by only ~0.01 mm). Geometry checkers that measure
stroke-edge-to-copper-edge see all four; DRC sees one. Verify a silk claim with `kc.py drc`, never
with a geometry script alone - and note this cuts the other way from the S13 finding that check_silk
is more lenient than DRC.
Fix recipe that worked (approved, see boards/usb-buck/lib/EDITS.md): delete the artifact circles;
where the remaining outline then still sat under a 0.15 mm silk-to-copper bar, NARROW the stroke
rather than move coordinates (0.25 -> 0.20 on C0603's outline buys 0.025 mm per edge and keeps the
geometry byte-identical; 0.20 and 0.15 are both >= JLC's 0.15 mm minimum line width). Result:
worst gaps 0.150-0.156 mm across the four, DRC 1 -> 0. A printable pin-1 dot is
`(fp_circle (center X Y) (end X+0.15 Y) (layer F.SilkS) (width 0.15))` - 0.3 mm diameter, outer
radius 0.225, so its centre must be >= 0.375 mm from the nearest pad edge to clear copper by 0.15.
Scratch-board trick for verifying a footprint edit in isolation: bundled python + `pcbnew.
CreateEmptyBoard()` + `FootprintLoad(pretty, name)` spaced 30 mm apart + an Edge.Cuts rect, save,
then `kc.py drc` - only intra-footprint findings can appear.

## 2026-07-28 [kicad-cli][python] Hierarchical netlist export DROPS the no-connect singleton nets; schlib --pins cannot see a project lib
Two P4 facts from the usb-buck schematic build (3 child sheets, 28 parts, KiCad 10.0.3).
(a) The 2026-07-22 entry "every NC/unconnected pin appears as a singleton net
`unconnected-(REF-PINNAME-PadN)`" holds only for FLAT designs. Same board, same
`kc.py netlist`: exporting the ROOT of the hierarchy gives 16 nets and ZERO `unconnected-*`
entries (the 29 NC-flagged U1 pins + J1's ID pin are simply absent from the netlist and from
U1's node list), while exporting the child `mcu.kicad_sch` STANDALONE gives 29 of them. The
no_connect s-exprs are byte-shaped identically to stm32-blinky's (which does emit 32), and ERC
is clean either way - it is the export that differs. Consequence for P5: those pads arrive at
board_init with NO net at all rather than an `unconnected-` net, unlike run (a)'s flat board.
(b) `schlib.py --pins "aiee:SYM"` - the documented P4 grounding aid - CANNOT read a project
library: it builds a scratch schematic through kicad-sch-api's global symbol cache, which never
reads kicad/sym-lib-table, so every project symbol comes back `LibraryError: not found ...
Common libraries include: Device, Connector_Generic, ...`. Ground against a 6-line wrapper that
calls `ksa.get_symbol_cache().add_library_path(<lib/aiee.kicad_sym>)` before `schlib.pin_table()`
(same call the generators already need). Also note `--pins` takes ONE lib_id, not a list.

## 2026-07-28 [placement][geometry] placelib's FpPad DROPS per-pad rotation - re-derive pad boxes for any clearance check
`(pad N smd rect (at x y ROT) (size w h))`: placelib._parse_fp reads at[0:2] and size verbatim and
never applies ROT, so `_pad_box_local` (and therefore the EFFECTIVE courtyard that S14's fix unions
in) is built from unrotated pads. usb-buck's USB micro-B (J1) has all five signal pads at ROT 90 and
both oval shield pads at 90: placelib sees a 9.5 x 4.28 pad box where the truth is 8.3 x 4.13 mm.
Here the error is conservative in x and hidden in y by the courtyard, but it is NOT conservative in
general (a rotated tall pad reads as a short wide one). Any pad-pad / pad-edge clearance check must
re-parse `(at ... ROT)` and swap w/h at 90/270 - do not reuse FpPad.size. The place gate never
noticed because its legality is courtyard-only.

## 2026-07-28 [placement][kicad] Connector mating direction: read the WRL, not the silk outline
J1 (HOOYA USB-111FD-B-SU, easyeda2kicad) at footprint angle 0 has its MOUTH at local +Y, so 270 deg
points it out of the board's left edge. Two traps: (a) the silk outline has a GAP at the -Y end and a
solid line at +Y, which reads backwards - the gap is just clearance around the SMT signal pads and
the two round shield holes at y=-1.34; (b) the shield legs are not a reliable cue either (the wider
7.20 mm pair sits mid-body, not at the flange). Decisive cheap test: parse the `.wrl` (KiCad units =
0.1 inch, and wrl_y = -pcb_y), bucket the vertices near each Y extreme and print the (x,z)
occupancy - the mouth end is a hollow FRAME, the closed end is filled. A `kicad-cli pcb render --views
iso` crop confirms it visually but is ambiguous at small scale.

## 2026-07-28 [placement][drc][silk] Pulled footprints park Reference 4 mm off-origin -> 47 silk DRC warnings from placement alone
Every easyeda2kicad footprint in the usb-buck pull carries `(property "Reference" ... (at 0 -4 ...))`
- a 4 mm offset that lands a 0603's refdes squarely on its neighbour once parts are packed. First
DRC after the P6 repair: 24 silk_overlap + 15 silk_over_copper, ALL of them Reference fields, plus 8
silk_edge_clearance from J1's own mouth-end outline poking 0.05 mm off the board edge (fix: nudge the
connector inboard; the silk stroke reaches |local y| 4.10 + width/2). Both classes are scriptable via
S14's `move_text` op. A greedy solver works if it (1) offers BOTH text angles on ALL FOUR sides
(0-deg-above/below + 90-deg-left/right only is not enough in a channel), (2) scores
`(min(clearance, 0.30), -distance_to_own_silk+pads)`, and (3) processes the most CROWDED parts first
(descending neighbour count within 4 mm) - largest-first orphans the boxed-in small caps. Hard limit:
a 3-char refdes at size 1.0 needs ~3.5 x 1.75 mm, so in a channel narrower than ~4 mm no label can be
closer to its own part than to the parts flanking it. Relieve that structurally (move the loosest-
constrained cap out) rather than fighting the solver.

## 2026-07-28 [easyeda2kicad][parts] lib_pull with a RELATIVE --out-dir bakes unresolvable 3D model paths
`easyeda2kicad --output <base>` copies the base string verbatim into each footprint's
`(model "<base>.3dshapes/<name>.wrl")`. Invoke lib_pull.py with a RELATIVE `--out-dir`
(`--out-dir boards/pd-trigger/lib`) and every footprint ends up with
`(model "boards/pd-trigger/lib/aiee.3dshapes/X.wrl")`, which KiCad resolves against the PROJECT dir
(`boards/pd-trigger/kicad/`) and therefore never finds - STEP export and 3D render silently lose all
models. The usb-buck pull was run with an absolute `--out-dir` and has absolute model paths, which is
why this never showed up before. Always pass an absolute `--out-dir`; repairing after the fact is a
pure string rewrite of the 16 `(model ...)` lines (no re-pull needed - re-pulling would duplicate the
space/slash-named symbols per the entry above).

## 2026-07-28 [easyeda2kicad][drc] Pulled 16P USB-C: plated peg holes = 4 DRC ERRORS; DIP switch ships 8 silk_overlap
Scratch-board DRC (one instance of each of pd-trigger's 16 pulled footprints, 30 mm apart, bare
board, `kicad-cli 10.0.3 pcb drc --severity-all`, defaults clearance 0.20 / min annular 0.10):
17 findings, and they are NOT evenly spread.
(a) `USB-C-SMD_MC-311D` (C5184243 GCT USB4105) alone accounts for all 4 errors + 3 warnings: its two
Ø0.65 locating-peg holes are emitted as `(pad "" thru_hole circle (size 0.65 0.65) (drill 0.65))` -
copper diameter == drill diameter, so `annular_width` 0.000 mm (x2 error) and `padstack` "hole leaves
no copper" (x2 warning), and each peg sits 0.1801 mm from the outer GND pad (A1-B12 / B1-A12) ->
`clearance` (x2 error). The pegs are mechanical (GCT drawing: 2x Ø0.50 plastic pegs, no electrical
function). Converting both to `np_thru_hole` + deleting the 0.06 artifact silk dot = **0 violations**
(measured). Applies to any pulled USB-C receptacle with peg holes.
(b) `SW-SMD_6P-L7.6-W6.0-P2.54-LS9.3-BL` (C7421520 3-pos DIP switch) ships 8 `silk_overlap` warnings
out of the box: its own `fp_text user` marks ("1","2","3","ON","KE") collide with its own silk body
outline. All five texts sit INSIDE the body outline, i.e. hidden under the part once assembled.
(c) Only 3 of the 10 sub-0.15 mm silk artifact dots actually trip `silk_over_copper` (both LED0603
variants + the USB-C one). The dots on C0603/C1206/F1206/R0603/R0805/R1206 and a 0.15-wide circle
overlapping the ESSOP-10 thermal pad by 0.013 mm do NOT fire - consistent with the earlier
"geometry checkers see 4, DRC sees 1" correction. Always measure with `kc.py drc`.

## 2026-07-28 [placement][kicad][render] Connector mating direction: the WRL bbox is a COINCIDENCE TRAP - fit the below-board pins, or just render an orthographic SIDE view
Follow-up to the 2026-07-28 "read the WRL, not the silk outline" entry, from pd-trigger P6
(`USB-C-SMD_MC-311D` + `CONN-TH_P5.08_KF128-5.08-2P`). Two traps and one cheap decisive test.
(a) Aligning the WRL by matching its BOUNDING BOX to the footprint is unreliable. The MC-311D's raw
wrl y-range (x2.54) is [-5.07, 2.83]; negating y gives [-2.83, 5.07], which matches the courtyard's
+y limit (5.07) EXACTLY and the THT pad extent (-2.85) to 0.02 mm - a perfect-looking 2-point fit
that is WRONG. Cavity ray-casts under that mapping put the mouth at local -Y; the truth is +Y.
The reliable anchor is the BELOW-BOARD geometry: cluster the wrl vertices with z < -0.3 (leg/peg
tips) and least-squares fit (sign_x, sign_y, y_offset) against the footprint's own thru-hole/NPTH
pad centres. For the MC-311D that lands `pcb = (+x, +y + 2.10)` on all 6 features with residual
sum-sq 0.013 mm2 - i.e. the shipped model is offset 2.1 mm in y (easyeda2kicad), which is exactly
what made the bbox "match" under the wrong sign. easyeda2kicad's `(rotate (xyz 0 0 180))` plus
KiCad's own y-flip cancel, so raw wrl x,y map straight to footprint x,y here.
(b) MUCH cheaper decisive test: `render.py <board> --views front,back,left,right`. These are
ORTHOGRAPHIC side views - a connector opening appears FACE-ON (dark slot / visible wire cages) in
exactly one of them, and its rear is solid in the opposite one. Unlike `--views iso`, there is no
axis-mapping guesswork. Verified both ways here. Do NOT judge orientation from an iso render: a
first read of the pd-trigger iso called J2 backwards, and the side views proved it correct.
(c) Both of this board's connectors open toward local **+Y** (USB-C mouth AND KF128 wire entry), so
with placelib/KiCad's `to_abs` = `_rot(local, -angle)`: angle **270 points the opening out the LEFT
edge, 90 out the RIGHT**, 180 up (-Y), 0 down (+Y). place_seed got J1's 270 right by luck of the
edge constraint; it has no mating-direction model, and it left J2 at 0 (wires into the board).

## 2026-07-28 [drc][kicad-cli] DRC on a board copy OUTSIDE the project dir silently changes the rules
Staging `kicad/<board>.kicad_pcb` to `work/try1.kicad_pcb` and running `kc.py drc` reported 30
bogus `lib_footprint_issues` ("configuration does not include the footprint library 'aiee'") AND
5 `copper_edge_clearance` errors quoting "board setup constraints edge clearance 0.5000 mm" - but
the project's `.kicad_pro` sets `min_copper_edge_clearance: 0.30`. KiCad fell back to its DEFAULT
0.5 mm because the sibling `.kicad_pro` was missing. Copy `fp-lib-table` + `<stem>.kicad_pro` +
`<stem>.kicad_dru` next to any staged board or both the library warnings and the clearance numbers
lie (in opposite directions: noise added, and a stricter rule than the real one).

## 2026-07-28 [routing][placement] Freerouting cannot merge a USB-C's two VBUS pads at 1.75 mm - it is a topology fact, not a placement defect
pd-trigger P6 route probe (2-layer, 2 oz, VBUS min width 1.75 mm by DRU rule). 150-pass probe
converges at pass 13 and stops: 65/68 connections routed, and ALL 3 residuals are net VBUS
(`J1-B4-A9 -> J1-A4-B9`, `R14-1 -> C1B-1`, `C1B-1 -> J2-1`). Cause: on the 16P USB-C the pad row is
GND,VBUS,CC1,<6 nc>,CC2,VBUS,GND at 0.5 mm pitch, so CC1/CC2 are SANDWICHED between the two VBUS
pads. Escaping VBUS leftward (around the pad row, under the connector body) is pinched to 1.50 mm
between the GND pad (y 39.61) and the CC1 pad (y 41.11) - narrower than the 1.75 mm rule. Escaping
right forces the merge to cross both CC escapes. So on ONE layer the merge is impossible; it needs
CC1/CC2 (or VBUS) to hop to the other layer. Consequence: a P6 route probe on any USB-C PD board
will cap around 0.95, below the >=0.98 bar, no matter how good the placement - judge the probe by
WHICH connections fail. The fix is P7's KRT-wrapped critical nets (power routed first, thin nets
displaced to B.Cu), not more Freerouting passes or a placement change.

## 2026-07-28 [placement][python] place_edit ops files need the {"version":1,"ops":[...]} envelope
`place_seed --ops-out` writes it, but a hand-built bare JSON list fails with
`CheckError: ops file must be {'version': 1, 'ops': [...]}` (exit 2). Also: `place`/`move` ops set
the footprint ORIGIN, not the courtyard centre - for asymmetric parts (USB-C: extents
x[-5.07,+3.10] about the origin) compute the target from the origin or the part lands offset.

## 2026-07-28 [routing][kicad][drc] A net-wide `track_width` DRU floor can be geometrically UNMEETABLE at a fine-pitch pad - pour it, do not neck it
pd-trigger P7. `aiee_pwr_width_VBUS (min 1.75mm)` applies to every VBUS **track**. Measured on the
real board (widest track whose copper can touch the pad while holding the 0.1524 mm clearance
floor): J1-A4-B9 / J1-B4-A9 = **1.465 mm** - i.e. NO legal VBUS track can reach the USB-C's own
VBUS pads, because CC1/CC2 and the 6 unconnected pads sit 0.2 mm away on a 0.5 mm-pitch column.
Every other VBUS pad measured >= 6 mm, so the defect is local to the connector. Corollary: the
prior entry's "CC1/CC2 dive to B.Cu so VBUS merges on F.Cu" does NOT fix it - displacing the CC
*escapes* does not remove the CC *pads*, which are what pinch the fan-in. The fix is a **zone**:
a zone is not a track, so the DRU width rule does not apply, and KiCad's filler necks around the
foreign pads by itself. `planes_gen --constraints <file with only a "planes" key>` creates it
(region is a rect only); then patch `(connect_pads (clearance X))` -> `(connect_pads yes
(clearance X))` on that zone's block - planes_gen leaves KiCad's default THERMAL relief, which
would spoke-starve a 5 A pad. Result: 3.5 mm of continuous copper across the merge vs 1.75 needed.
Reusable test: for each pad, max over centreline points P of `2*(dist(P,foreign)-CLR)` subject to
`dist(P,pad) <= W/2` - that is the widest connectable track.

## 2026-07-28 [routing][rules_gen][freerouting] rules_gen puts EVERY power net in one "Power" netclass at the WIDEST width - Freerouting then routes 20 mA nets at 5 A width
`rules_gen.net_classes()` emits a single `Power` class at `max(min_width_mm)` over all
constraints["power"] entries and assigns all of them to it. On pd-trigger that put /VDD (0.02 A,
DRU floor 0.005 mm) and /VIND (0.05 A) into a 1.75 mm class. The DSN export carries netclass
widths, so FR would have tried 1.75 mm traces into U1's 0.6 mm-wide 0.5 mm-pitch pads and failed
those nets. The DRU rules are per-net and were already correct - only the .kicad_pro netclass is
wrong. Fix before route_auto: split `netclass_patterns` so the wide class holds only the fat net
and the thin ones get their own class (or Default), leaving the .kicad_dru untouched. With that
done FR hit completion 1.0 on rung 1 (55 -> 3 unrouted, the 3 finished by the KRT/dedup pass).

## 2026-07-28 [routing][check_current] check_current's via-count rule is NET-WIDE - a 5 A net must not change layers at all
`need = ceil(current_a / via_amps)` is applied to EVERY via cluster of the net, with no
per-segment override (`overrides` only feeds the track-width check, not vias or pour necks). VBUS
at 5 A / 0.5 A-per-via => 10 vias at EVERY layer transition, including a bulk-cap or 1 A fuse tap
that carries nothing like 5 A. Practical consequence on a 2-layer board: keep the whole high-
current net on ONE layer (pour + rule-width tracks, zero vias) and give the boxed-in taps a
detour rather than a via pair. Bonus: `pour_neck` only measures between via attachments and
returns None with < 2 vias in the fill, so a via-free pour is also exempt from the neck check -
do not lean on that silently, state the measured channel widths in the report. pd-trigger shipped
VBUS with 0 vias, min track 1.75 mm, 3.0 mm x 32 mm trunk -> check_current 0 violations.

## 2026-07-28 [routing][stitch][drc] KiCad hole_to_hole does NOT test a via drill against a same-net THT PAD drill - the 0.5 mm floor must be enforced by the generator
Live test on pd-trigger (scratch copy, `aiee_hole_to_hole_floor` min 0.4995 mm): a 0.3 mm-drill via
placed so its hole edge sits **0.121 mm** from J1-1's THT oval drill produced ZERO violations
against that pad; the same DRC run DID flag the identical via against another VIA at 0.403 mm. So
KiCad checks via<->via but skips via<->pad-hole when the via lands on the same-net pad's copper.
Consequence: stitch_vias' pad-attachment vias can ship drill spacing the fab cannot produce and
DRC stays green - two such vias (0.12 mm to J1-1 / J1-4) were sitting on this board. Any generator
that drops a via next to a THT pad must compute the pad's drill itself. Doing that needs the
footprint transform: inside a `(footprint ... (at fx fy frot))`, a pad's `(at px py prot)` stores
prot as the ABSOLUTE board angle (frot is already folded in) - so position rotates by `-frot` but
the pad/drill SHAPE rotates by `-prot`. Using `prot - frot` silently yields a drill turned 90 deg
(caught here only because the derived drill boxes disagreed with the pad bounding boxes).

## 2026-07-28 [routing][placement] A USB-C's SMD GND contact pads need a pour lobe + via field, not stitch_vias' one-via-per-pad
pd-trigger P8 review: the 5 A return choked at J1. Freerouting attaches GND contact pads
(A1-B12 / B1-A12, ~2.5 A each) with 0.2 mm track = **0.80 A** at 2 oz, and stitch_vias adds ONE via
per pad - neither script models per-pad current, and check_current only audits nets in
constraints["power"] (GND is deliberately NOT one, decisions D7). Fix that held: two F.Cu GND zone
lobes (planes_gen with a planes-only sidecar) spanning the contact pads AND the THT shell/EH pads,
at **priority 1 so the neighbouring VBUS pour yields**, patched to `connect_pads yes` (planes_gen
leaves KiCad's default THERMAL relief, which would spoke-starve a 2.5 A pad). Result 2.09 mm /
1.62 mm narrowest pad->via cross-section (5.68 A / 4.70 A) and 8 / 7 vias. Cross-net zone overlap
at distinct priorities is fine - `zones_intersect` only fires same-net same-priority.

## 2026-07-28 [skill][fab] Silk strap tables must print the SWITCH positions, not the raw config bits
The CH224K map is `(CFG1,CFG2,CFG3)`: 1XX=5 V, 000=9 V, 001=12 V, 011=15 V, 010=20 V - but the DIP
switch shorts to GND, so ON = logic 0 and the bit table is INVERTED relative to what the user sets.
Printing "000=9V" on the silk would tell someone to set all three OFF, which selects 5 V. Print the
ON/OFF table from decisions.md D3 instead. Also: `place_edit add_text` auto-mirrors any `B.*` layer
(place_swig `SetMirrored(True)`), so B.SilkS text is written in board coordinates and reads
correctly in the bottom render - do not pre-mirror the string or the position.

## 2026-07-28 [datasheet][python] Zooming a datasheet drawing without a rasterizer: pypdf crop + scale
No pymupdf/pdf2image in the venv (pypdf + PIL only). To read a pin diagram or dimension table
visually: pypdf `page.scale_by(s)` (s~5), then set `mediabox.lower_left/upper_right` to the crop
region multiplied by s, write a single-page PDF, and Read that. Resolved the CH224K pin numbers
and the L78L33 table columns when the text layer was garbled/misaligned. (Derived by the S14
extractor agents; both used it successfully.)

## 2026-07-28 [python] kicad-sch-api preserves compound alphanumeric pad names ("A4-B9") through save
Unlike the known alphanumeric renumbering of simple names ("SH" -> "6", repaired by fixups),
COMPOUND pad names like "A4-B9"/"B1-A12" on the USB4105 USB-C receptacle survive
kicad-sch-api save/netlist intact - no fixup needed. (S14 run (c); the fixup machinery stays
for the simple-name case.)

## 2026-07-28 [placement] place_anneal separation refs absent from the board were silently dropped
A refdes rename (R2 -> R2A/R2B split) invisibly lost a thermal-separation constraint - the
anneal ignores unknown refs. Now surfaced as facts.separation_unknown_refs (test-pinned);
orchestrators must sync constraints refs after any refdes change (sheets.md tracking rule).

## 2026-07-28 [latex][windows] pdfpages 2026 passes an `artifact` key older graphics stacks reject
MiKTeX auto-installs pdfpages v0.6h (2026), which emits an `artifact` keyval into
\includegraphics on MULTI-page \includepdf insertions; a 2024-era graphics/graphicx lacks the
key -> "keyval Error: artifact undefined", fatal - while SINGLE-page includes work fine (why
quick probes miss it). report_gen's preamble defines the key as a no-op iff absent
(\makeatletter/\makeatother guard). Recognize it by: 1-page schematic embeds fine, 4-page dies.

## 2026-07-28 [jlc][api] JLCPCB Open API facts (probe-verified on a live app)
Base URL open.jlcpcb.com (/overseas/openapi/...) - api.jlcpcb.com is the portal/console only.
Auth "JOP" scheme: 5-line HMAC-SHA256 string-to-sign (METHOD, path[+?query], unix-ts, 32-char
nonce, raw body - EACH line \n-terminated INCLUDING the last), Base64; header carries
appid+accesskey+timestamp+nonce+signature (the secret never travels). Official doc vector
reproduced exactly (pinned in test_jlcapi). Error taxonomy: HTTP 401 = bad signature; HTTP 403 =
app valid but service scope unapproved (live body while scopes are "Reviewing":
{"code":403,"success":false,"message":"API insufficient permissions, access denied"}); business
code 1000 = IP-whitelist block and wins at ANY HTTP status; 1002/429 = rate. NO sandbox exists -
pcb/create places a REAL order. NO PCBA/assembly API (official api-list 2026-07-16): BOM/CPL
ordering stays the web flow. IP whitelist optional; two keys per app for rotation. Contract
brief + sources: C:/dev/ai-library/jlcpcb-openapi-2026/.

## 2026-07-28 [jlc][api] pcbParam keys are layer/width/length/qty/thickness - NOT stencil*
The hendley console-PDF transcription is the key-name authority; stencilLayer/stencilPly belong
to the impedance-template request only. An early build inferred stencil* names for
calculate/create - unknown keys could have priced/ordered a DEFAULT board with real money
(caught by adversarial review, round 1). Watch item: copperWeight is typed "Number" in both
tables but the official create example sends string "2" - code sends strings; a strict live
parser rejects at calculate (fail-safe, before money). 2 oz derives ONLY from stackup.md's
"## Chosen:" id (e.g. JLC2313_1.6_2oz) - spec_snapshot/quote.json do not carry copper weight,
and the guard refuses when order-note oz mentions exceed the derived value.

## 2026-07-28 [latex] Escaping the special chars is not enough: [ and * are context-sensitive
After the \\ that joins tt-block/longtable lines, a line-initial "[" parses as the OPTIONAL ARG
of \\ ("! Missing number", fatal - a digest line "[ok] ..." or BOM comment "[NRND] ..." kills
the compile); "\item [x]" swallows [x] as the item label (silent content loss in task lists /
human_steps); "\\*" swallows a line-initial star. Per-char escaping cannot see context; fix is
brace-wrapping in the map ("[" -> "{[}", "]" -> "{]}", "*" -> "{*}") - renders identically,
inert everywhere. Related: OT1 text mode prints raw < > | as inverted punctuation/em-dash -
map to \textless{}/\textgreater{}/\textbar{}. (Adversarial review of report_gen, probe-verified.)

## 2026-07-28 [geom][layout] Arc endpoints were recomputed, so any arc-based board outline parsed as POLYGON EMPTY
geom._arc_points sampled the arc from the fitted centre+radius, so its first/last points were
`cx + r*cos(a1)` rather than the DECLARED start/end - off by ~1e-14. unary_union then refuses to
node the arc against the gr_line meeting it, polygonize finds no closed face, and
BoardGeom.outline silently becomes an empty Polygon (no error, no warning). Any rounded or
arc-cornered outline hit this, not just generated ones - and every downstream consumer
(planes_gen, DFM, order_quote, area checks) reads that empty outline. Fix: pin pts[0]/pts[-1] to
the declared start/end (they ARE the endpoints by definition). Detect it by asserting
outline.area > 0, never by trusting board_init's self_check - that passed the whole time.

## 2026-07-28 [testing][windows] tests/test_report.py is not concurrency-safe - it diffs global `git status`
test_smoke_pd_trigger_with_residue_and_rerun and test_smoke_stm32_blinky snapshot
`git status --porcelain` before/after and assert the ONLY new lines are `?? .../reports/design_doc/`.
Anything else touching the working tree during the run fails them - a second ai-ee orchestrator
writing under boards/, or a research agent dropping a scraped page at the repo root
(`?? docs_start.html` was a real instance). Failures look like flaky asserts on a list of git
lines and are NOT caused by the code under test. Re-run the file in isolation to confirm before
chasing it; when running boards concurrently, expect these two to be unreliable.

## 2026-07-28 [layout] Corner radius must be clamped to the mounting-hole inset, not solved by moving holes
board_init packs parts on a shelf grid that already routes around the corner mounting holes at
inset = margin/2. Pushing a hole inward so it clears a larger corner radius therefore drives it
into a neighbour's courtyard (observed: H1 vs C1 on golden usbbuck4 at radius 4, inset 3).
Shrink the radius to the inset instead and tell the caller to raise --margin if it wants more.

## 2026-07-28 [kicad][python] A power symbol's net name comes from its VALUE field, not its library pin name
P4 lumina-carrier, kicad-cli 10.0.3. A board rail with no stock power symbol (`+48V_SW`) is NOT a
dead end and must NOT fall back to a local label (that yields `/<sheet>/NAME` and
`netlist_audit --constraints` then raises missing_net at ERROR). Place any power symbol and set its
Value: `power:+48V` with Value `+48V_SW` exports a bare global net `+48V_SW`. Measured both ways on
a 2-part scratch sheet: with the wire carrying local label `+48V_SW` but the symbol left at Value
`+48V`, the netlist net is `+48V` - the POWER SYMBOL WINS over a coincident local label, so the two
must be made to agree or the label is silently ignored. Two API traps in the same idiom:
(a) `component.set_property("Value", x)` is a SILENT NO-OP on kicad-sch-api 0.5.6 - Value is a
dedicated attribute (`component.value = x`), and the generic property store is a different thing;
(b) schlib's `power_flag(..., flag=False)` is the clean "rail cluster with no PWR_FLAG" form for a
sheet that consumes a rail another sheet drives.

## 2026-07-28 [python][kicad-sch-api] add_hierarchical_label() DROPS its shape argument; rotated 2-pin symbols get INWARD stubs
Two schlib/kicad-sch-api 0.5.6 defects found building a P4 child sheet.
(a) `Schematic.add_hierarchical_label(text, position, shape=...)` documents five shapes and then
discards the argument: it calls `self._hierarchical_labels.add(text, position, rotation, size)`
with no shape, and `_sync_hierarchical_labels_to_data` emits no shape key at all - every
hierarchical label is written `(shape input)` whatever you ask for. There is no API path to it.
`Schematic.add_sheet_pin` DOES honour pin_type, so `Project.add_sheet` still writes correct shapes
on the ROOT's sheet pins and only the child's labels are wrong. NOT worth patching: the S7 golden
already has the mismatch (`tests/s7_regen/hierdemo` root sheet pin `CTL` is `passive`, the child
label is `input`) and that root's ERC is 0/0 - KiCad 10.0.3 does not check sheet-pin/label shape
parity. Keep the semantic shape in the generator; it lands where it matters.
(b) schlib's `stub_dir` and kicad-sch-api disagree on the SIGN of a 90 deg symbol rotation, so for
any rotated 2-pin part BOTH auto-stubs are emitted pointing INWARD through the symbol body, putting
the local-label anchors inside the part (10k 0603 at rot 90, anchor y 127.0: pin1 121.92 -> 124.46,
pin2 132.08 -> 129.54). Electrically survivable - the stubs stay 5.08 mm apart and the labels still
bind - but visually broken. Generators should keep every component at rotation 0 until this is
fixed; hierdemo and pd-trigger never rotate, which is why it had not surfaced.

## 2026-07-28 [geom][layout] An inner Edge.Cuts gr_rect silently BECOMES the board outline
geom._parse_outline scans gr_rect on Edge.Cuts FIRST and returns on the first match, before it ever
looks at gr_line/gr_arc. So an interior cutout emitted the obvious way - a SHAPE_T_RECT window -
replaces the outline entirely rather than punching a hole in it. Measured: a 10x10 mm window on a
100x80 mm board parsed as outline.area == 100.0, not 7892. planes_gen, DFM, order_quote and every
area check would then see a 10x10 board, with no error raised anywhere. board_init now REFUSES
interior cutouts: --cutout must touch an outline edge and become a notch (exit 2 with remediation).
If interior windows are ever genuinely needed, _parse_outline must collect ALL closed loops and
subtract the inner ones instead of returning the first rect it finds.

## 2026-07-28 [spice][windows] InSpice + KiCad's bundled ngspice.dll: the working recipe has traps
KiCad 10.0.3 ships ngspice.dll v46 beside kicad-cli; InSpice 1.7.0.5 (transitive via skidl, now
pinned) drives it - no standalone ngspice needed. Traps (all machine-verified): (1)
NGSPICE_LIBRARY_PATH must be the BARE name "ngspice.dll" + KiCad bin prepended to PATH -
find_library splits at the first "." so a full path containing "KiCad/10.0" truncates; (2)
SPICE_LIB_DIR must be SET (any dir) or _load_library crashes on Path(None) ("can't find spinit"
is benign); (3) circuits passed to load_circuit() must end ".end" or you get a silent "no
circuits loaded". .measure only works for tran/dc/ac (never op) and results are NOT vectors -
parse "name = value" lines from captured stdout; a FAILED .measure makes run() raise while the
successful measures stay parseable. Always inject .options rshunt=1e9 (one floating node makes
.ac singular while DC stays perfect); keep refs to all callback thunks; run each bench in a
killable subprocess (in-process DLL hangs are unkillable on Windows). KiCad "1M" resistor value
means 1 MEG in SPICE (map it); a bare-"F" cap value ("1F") silently becomes femtofarads - treat
prefix-less F as unresolved. kicad-cli spice export is UNUSABLE without Sim.* fields (model-less
symbols emit REF __REF with ZERO nodes - topology destroyed); synthesize fragments from the
kicadsexpr .net instead.

## 2026-07-28 [spice][geometry] PDN cavity-model band edges are validity limits, not layout facts
With no VRM branch (low f) and no package/die capacitance (high f), max|Z| over the sweep ALWAYS
lands at a band edge - gating a target on band-max fails every known-good board (adversarial
B-1; a 165 mOhm target read 1.4-1.6 Ohm at 200 MHz on the clean usbbuck4 golden). Gate
antiresonance PEAKS only; judge peaks/first_min, never z_max. Empty bounds sidecars must be
rejected like missing ones - "[]" gate-passes an unproven testbench (A-1); JSON NaN/Infinity
bound limits validate as numbers and can never trip (A-2) - require finite.

## 2026-07-28 [parts][datasheet] parts_search returns www.lcsc.com datasheet URLs that curl CANNOT fetch; rewrite them to the wmsc mirror
`parts_search.py` faithfully returns whatever LCSC publishes, and for most parts that is
`https://www.lcsc.com/datasheet/lcsc_datasheet_<stamp>_<Vendor-MPN>_<Cxxxx>.pdf`. That URL serves a
**JS-shell HTML page** to any non-browser client - `curl -sL` writes a ~46-48 kB file starting
`<!doctype html>`, exit 0, no error anywhere. A minority of parts instead return
`https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/<stamp>_<Vendor-MPN>_<Cxxxx>.pdf`, which serves
the real PDF. Same catalogue, two URL forms, only one of them fetchable.

Measured on lumina-strobe P3: **7 of 9** datasheet URLs from parts.json were the unfetchable form.
The fix is a pure string rewrite - drop `/datasheet/lcsc_datasheet_`, keep the
`<stamp>_<Vendor-MPN>_<Cxxxx>.pdf` stem, and prefix
`https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/`:

    www.lcsc.com/datasheet/lcsc_datasheet_2304140030_STMicroelectronics-LM2901DT_C142961.pdf
 -> wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-LM2901DT_C142961.pdf

All 7 recovered on the first try (294 kB - 2.2 MB, all `%PDF`). **Always check the first 4 bytes are
`%PDF` after downloading a datasheet** - the failure is silent and the datasheet-extractor would
otherwise "extract" a pinout from an HTML error page, and its output is the ONLY pinout source the
schematic agents may wire from.

Second, unrelated trap seen in the same batch: **many distinct parts share one LCSC date stamp**
(`2304140030` covered LM2901DT, IRF640NSTRLPBF and both CONNFLY DS1023 sockets). That looks exactly
like a pattern-fabricated URL and is not - it is LCSC's own batch-upload date. Verify against
`parts_search` output before accusing a sourcing agent of inventing URLs. Relatedly, the two DS1023
sockets (2x7 and 2x12) return byte-identical PDFs because one family datasheet covers the range.

## 2026-07-28 [parts] parts_search returns zero rows for value tokens like "10K"
Queries containing resistor/capacitor value tokens (`10K`, `1K`, `56K`) and some long
multi-word phrases silently return **zero results** - not an error, just an empty set that
reads like "no such part exists". Search by exact MPN (`0603WAF1002T5E`) or by a spelled-out
value (`10 ohm`) instead. Cost the lumina-par P3 part-sourcer several wasted round-trips
before it worked out the pattern. The failure mode is dangerous because an empty result set
looks identical to a genuine stock-out and can push an agent into re-architecting around a
part that is actually available.

## 2026-07-28 [parts] LCSC www/datasheet URLs return HTML; rewrite to the wmsc host
`parts_search` hands back two URL shapes. `https://www.lcsc.com/datasheet/lcsc_datasheet_<stamp>_<name>_<lcsc>.pdf`
serves a **47 kB HTML page**, not a PDF - 15 of 18 datasheets on lumina-par came back that way,
including the main LED driver and both emitters. The working form is
`https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/<stamp>_<name>_<lcsc>.pdf` - i.e. strip
`lcsc_datasheet_` and swap the host. Rewriting recovered all 18 on the first retry.
Combined with the existing `%PDF` magic-byte rule this is a two-step must: rewrite the URL, then
verify the first 4 bytes. Without the byte check the extractor "extracts" a pinout from an error
page, and that pinout is the only source the schematic agents may wire from.

## 2026-07-28 [datasheet][parts] TI SN74LVC00A (SCAS279R) Pin Functions table has shifted TYPE/DESCRIPTION columns
The sec 6 table prints `3Y ... - / Power Pin`, `3A|3B ... Gate 4 input`, `4A|4B ... Gate 3 input`,
`VCC ... O / Gate 3 output`: the TYPE and DESCRIPTION columns are shifted one row up from the 3Y row
down, so a text-layer extraction reads pin 8 as a power pin and pin 14 as a gate output. The pin
NUMBER columns and the D-package Top View diagram are correct and self-consistent
(7=GND, 8=3Y, 14=VCC) - read the pin-configuration DIAGRAM as the authority whenever a TI pin table
disagrees with it, and cross-check against the package diagram on the same page before trusting a
name/number pair pulled from the table text. Found on lumina-par P3 (C485072).

## 2026-07-28 [datasheet] LM339LV pin drawing and pin table transpose the channel names
TI's LM339LV datasheet gives conflicting channel labels: Figure 5-3 (pin drawing) and Table 5.2
(Pin Functions) **transpose the OUT names**, and Table 5.2 is self-inconsistent - it names pin 13
"OUT3" while describing it as "Output pin of the comparator 4". The datasheet's own footnote admits
the transposition. Both sources DO agree on the pin-number groupings, so the rule is:
**wire quad comparators by pin number, never by channel name.**
Correct groupings: out1<->in6/7, out2<->in4/5, out13<->in10/11, out14<->in8/9.
Two more traps in the same part: **no internal hysteresis** (needs external, or the output chatters
on slow signals like an NTC ramp), and POR holds outputs **Hi-Z for up to 30 us**, so an
open-drain fault line reads "no fault" during that window.

## 2026-07-28 [librarian][kicad] A wrong lib-table URI silently pulls into the REPO ROOT and every board then shares it
`lib_pull.py --project <ws>/kicad` writes symbols/footprints to whatever `${KIPRJMOD}`-relative path
the board's `fp-lib-table` / `sym-lib-table` already contain - it does NOT derive the path from
`--project`, and it does NOT complain when the URI escapes the workspace. lumina-strobe shipped with
`${KIPRJMOD}/../../../lib/aiee.pretty` (three levels up from `boards/<name>/kicad/` = the repo root)
where lumina-carrier correctly had `${KIPRJMOD}/../lib/aiee.pretty`. The first pull therefore created
an untracked repo-root `C:\dev\ai-ee3\lib\`, left `boards/lumina-strobe/lib/` empty, and `lib_pull`
reported `status: pass` with `load_check ok` - because the pull genuinely succeeded, just into a
shared location three concurrent board runs would have collided in.

**Check both lib-table URIs before the first `lib_pull` of a run**, not after: the correct form from
`boards/<name>/kicad/` is `${KIPRJMOD}/../lib/aiee.pretty` and `${KIPRJMOD}/../lib/aiee.kicad_sym`.
The tell is an untracked top-level `lib/` in `git status` plus an empty `boards/<name>/lib/`.

Recovery is safe and cheap: fix the two URIs, copy `aiee.kicad_sym` / `aiee.pretty` / `aiee.3dshapes`
into the board's own `lib/`, delete the stray root `lib/`, and re-run the pull (registration is
idempotent). Do this before P4 - after P5 the board file carries absolute-ish footprint references
and the cleanup gets more expensive.

Related, same run: **easyeda2kicad numbers a D2PAK/TO-263 MOSFET's drain terminal pin 4 and omits
pin 2 entirely** (the cropped centre lead has no land, so the pulled footprint has 3 copper pads:
1 = gate, 3 = source, 4 = the 8.4 x 10.6 mm tab = drain). The datasheet/JEDEC numbering is 1/2/3+TAB.
A schematic that wires the drain to pin "2" or "TAB" connects nothing, and `fp_verify` reporting
`pad_count` 4 vs 3 on such a part is EXPECTED, not a real error. Reconcile the two numbering schemes
in the part's extraction JSON before P4 wiring.

## 2026-07-28 [datasheet] JST catalog PDFs hide dimensions in a non-embedded CID font
Every dimension number in the JST PH-series drawing is drawn in a **non-embedded Adobe-Japan1
Identity-H CID font**: it renders BLANK in pdftoppm/poppler and extracts as mojibake, so the
drawing looks dimensionless in both text and image paths. Recover by decoding the CID stream
directly - **CID = ASCII - 31**, with CID 692/693/694/695 = `+ - +/- x` - using per-glyph device
coordinates, then cross-check against the drawing's own vector rectangles (the pitch gives you
the pt/mm scale). On lumina-par every pad matched within 0.001 mm. Applies to any JST catalog PDF.

## 2026-07-28 [parts][concurrency] lib_pull's --out-dir default is RELATIVE, so it lands in the repo root and is shared by every run
--out-dir defaulted to the bare string "lib", resolved against the CWD - and orchestrators run scripts
from the repo root, so omitting the flag silently created <repo>/lib and registered
${KIPRJMOD}/../../../lib/ in the board's fp-/sym-lib-table. The board's own lib/ stayed EMPTY, three
concurrent runs would have written parts into one shared library (symbol-name collisions across
boards, --overwrite clobbering), and lib_pull still reported status: pass. Found by the lumina-strobe
run as its BLOCKING-06. Fixed centrally: the default now derives from --project
(<project>/../lib), and the resolved dir is refused outright if it equals <repo>/lib (exit 2 with
remediation). Symptom to recognise: a populated <repo>/lib, an empty boards/<name>/lib, and lib-table
URIs with three or more ../ segments.

## 2026-07-28 [check_creepage][gates][magnetics] check_creepage only knows working VOLTAGE, so it cannot see a magjack isolation-barrier collapse
`check_creepage.py` derives required spacing from `constraints.json.voltages` via IPC-2221B - i.e.
purely from the DC working voltage between two nets. On a PoE board the 48 V domain gives 0.635 mm
(51-100 V band) and everything passes at that number.

That is the wrong model for an RJ45 magjack. The barrier that matters there is **chip-side to
line-side**, and it is not sized by the 57 V working voltage at all - it is sized by the cable-side
hipot requirement (1500 Vrms / 2250 VDC) and by the vendor's own land-pattern guidance. HALO's app
note asks **55 mils = 1.40 mm** at 2.54 mm pitch. `check_creepage` will happily pass a 1.05 mm gap,
because 1.05 mm > 0.635 mm and the checker has no concept of an isolation barrier.

Found on lumina-carrier while evaluating a replacement magjack: the candidate's land pattern
collapsed the chip-side/line-side pad gap from 3.58 mm to **1.05 mm** - a real defect that no gate in
the pipeline would have flagged. The P8 verify suite would have been green.

Recognise it whenever a part carries an isolation barrier that is NOT a function of the board's own
rail voltages: Ethernet magnetics, opto-isolators, isolated DC-DC, digital isolators, mains-facing
anything. For those, the spacing requirement comes from the *part's* datasheet and the safety
standard, not from `voltages[]`, and it must be enforced by hand - a `.kicad_dru` rule keyed on
`A.NetName`, plus a placement `separation` entry - and checked by a human reading the land pattern.

Related trap already recorded: `rules_gen.py` never reads the `voltages` key at all, so even the
0.635 mm figure is not enforced during routing and only surfaces at P8.

## 2026-07-28 [easyeda2kicad][parts] lib_pull reports "pulled" for parts it never pulled, once the lib is non-empty
Second, worse variant of the 2026-07-28 "lib_pull hides a failed symbol pull" entry, measured on the
lumina-par P3 pull (44 LCSC ids). `_pull_one` bails to `status: "error"` only when
`not fps and not sym_lib.exists()`. `sym_lib` is the ONE shared `aiee.kicad_sym`, so as soon as the
FIRST part of a run succeeds, that file exists and **every subsequent part reports
`status: "pulled"` no matter what happened** - including a hard `HTTP 403` where nothing at all was
written. Observed: a 44-part run logged `status: pass`, `pulled/exists = 44 of 44`, and
`load_check.ok = true`, while only **13** parts actually had both a symbol and a footprint on disk.
The per-part `footprints: []` list is the only tell in the payload, and it is empty for legitimately
shared footprints too (see below), so it is not a reliable discriminator either.
**Ground truth, and the only check worth writing:** a part is present iff `aiee.kicad_sym` holds a
top-level `(symbol ...)` block carrying `(property "LCSC Part" "<id>")` AND the `aiee:<name>` in that
block's `Footprint` property exists in `aiee.pretty`. Verify per part after each pull and re-pull the
failures; never batch-trust the exit code.
**Corollary trap:** do NOT map LCSC -> footprint by grepping the LCSC id out of the `.kicad_mod`.
Footprints are SHARED (one `C0603.kicad_mod` served 5 parts, `R0603` 12, `SOIC-14` 2) and the file
records only the FIRST puller's id, so every later sharer looks unpulled. Map through the symbol's
`Footprint` property instead.

## 2026-07-28 [easyeda2kicad][parts] The EasyEDA CAD endpoint rate-limit is a CloudFront WAF block on one path, and it clears in ~60 s
Refines the earlier "~3 full passes ... and a 60 s backoff was not enough" note with measurements.
Only `https://easyeda.com/api/products/<id>/components` 403s; `easyeda.com/` (200),
`modules.easyeda.com` (404 = alive) and the JLCPCB search API (405 = alive) all still answer, so the
block is per-path, not per-host. The body is CloudFront's `Request blocked.` page with
`X-Cache: Error from cloudfront` - i.e. a WAF/rate rule at the edge, NOT an application response.
It is immune to every client-side fix: bare UA, no UA, a full Chrome header set with
`sec-fetch-*`/`X-Requested-With`, and a real `easyeda_session` cookie fetched from the homepage all
403 identically. The only thing that works is waiting - a 1-probe-per-60 s poll recovered on the
**second** probe (~60-120 s). Budget: `--full` costs ~3 requests/part (components + 3dmodel + step);
4 parts per ~35 s tripped it after ~13 parts, while **one part per 15 s ran 31 parts with only 2
transient failures**, each cleared by a single 90 s backoff. Pace one part at a time, verify on disk,
back off 90 s on failure.

## 2026-07-28 [easyeda2kicad][placement] Pulled courtyards enclose the BODY only - 20 of 22 exclude their own pads
Measured across the whole lumina-par pull (pad bbox with per-pad rotation applied vs F.CrtYd bbox).
Every footprint HAS an F.CrtYd - `fp_verify`'s `no_courtyard` warning never fires - but the outline
is the package body, so the pads protrude by up to **3.7 mm** (TO-252 tab, `TO-252-2_L6.6-...`),
1.69 mm (SOIC-14), 1.42 mm (MSOP-10-EP) and 0.30-1.13 mm on the small stuff. Only the two THT
headers contain their pads. This is the general case of the S14 LQFP48 finding, not an outlier.
`placelib.PlacedFp.extents_local()` already unions `_pad_box_local()` into the courtyard, so P6
legality is covered - EXCEPT that `_pad_box_local` reads `(size w h)` verbatim and ignores
`(at x y ROT)`. On this board exactly one footprint is exposed: `SOT-23-3_L2.9-W1.5-P1.90-LS2.6-BR`
(C427379 BSS123, Q102) has all three pads at ROT 90 with `(size 0.700 1.250)`, so placelib builds a
0.70 mm-wide box where the truth is 1.25 mm - under-estimating each side by 0.275 mm.
Checking courtyard presence is not the same as checking courtyard adequacy; measure the pad bbox.
Corroboration from the same board: when L301's pull was swapped to KiCad stock
`Inductor_SMD:L_Cenker_CKCS4030`, the stock footprint's courtyard CONTAINS its pads with 0.25 mm to
spare (pull: pads 0.40 mm outside). "Swap to KiCad stock" fixes courtyard adequacy as a side effect.
Watch the parser though: KiCad 10 stock uses the multi-line form where `(layer "F.CrtYd")` sits on
its own line, so a line-oriented `if "CrtYd" in line` scan finds NO courtyard and reports a false
"missing" - `fplib.parse_footprint` gets this right, ad-hoc greps do not.

## 2026-07-28 [librarian][easyeda2kicad] EasyEDA rate-limits at ~31 fetches / 13 min and lib_pull reports pass while symbols silently fail
Extends the 2026-07-28 entry on `_pull_one`'s success heuristic. On a 50-part pull the anonymous
EasyEDA CAD endpoint began returning **403 after ~31 fetches in ~13 minutes**. `lib_pull.py` reported
`status: pass` for an entire 10-part batch while **7 of those 10 produced no symbol at all** - because
`_pull_one` decides success on "this LCSC id appears in some existing footprint file", and a part
reusing an already-pulled package (R0603, C0805, SOD-123 ...) satisfies that test even when the API
returned nothing for it.

**Exit code cannot detect this. Symbol COUNT can.** After a bulk pull, assert
`len(symbols in aiee.kicad_sym) == len(parts.json parts)` and check that every symbol's `Footprint`
property resolves to a file in `aiee.pretty`. Recovery that worked: 10 min cool-down, then ~20 s
per part with a 180 s backoff-retry on failure - 26/26 recovered, two parts needing one retry each.
Budget roughly one second per part of pacing on any pull over ~30 parts rather than discovering it
at P4 when a symbol is missing.

Two smaller findings from the same run:
- **`fp_verify`'s pad-size check uses the MODE, so asymmetric packages slip through.** An SSOP-20
  land pattern has pins 1-10 at 0.4 x 1.8 and pins 11-20 at 0.4 x 2.0; `_modal_size` hit a 10/10 tie,
  returned 1.8, passed, and never compared the 2.0 column (which was 0.25 mm over the datasheet max).
  The check should bound min/max, not the mode.
- **Pulled symbol libraries contain non-ASCII** (178 chars in a 50-symbol lib: CJK manufacturer names
  like `Infineon(...)`, plus Ohm and +/- signs). kiutils' `from_file` defaults to cp1252 and raises on
  these, so any downstream netlist/BOM reader must force UTF-8 explicitly.

## 2026-07-29 [parts][thermal] A bridge rectifier's CURRENT rating is not a thermal rating - check RthJA before believing "1 A"
Selecting the two PD input bridges on lumina-carrier: the obvious pick was an MB6S/MB10S in MBS,
sold as a "1 A" bridge and stocked as JLC Basic. It fails thermally at the actual operating point.

At 802.3at only ONE Alternative conducts, so a single package takes the whole load - not half of it.
`2 x Vf(0.6 A) x 0.6 A` is ~0.83 W hot / ~1.06 W with no thermal credit. Measured from the
datasheets: MBS package **RthJA 90 C/W**, mean rectifying current actually **0.5-0.8 A not 1 A**, and
Vf ~1.03 V at 0.6 A -> **Tj ~176 C**, over the 150 C limit. The ABS/SOP-4 package (ABS210, 2 A /
1000 V) is **65 C/W** -> Tj 118-133 C at the board's 64 C worst-case internal air. Same nominal
"amps", completely different answer.

Rule: for any rectifier or pass element, size on **RthJA x P_dissipated + T_ambient_internal**, not on
the headline current. And check the *mean rectifying current* spec, which is often well below the
part's marketing number. Note the JLC Basic constraint pushed toward the wrong part here - Extended
was the correct choice and the only Basic bridge available was exactly the one that fails.

## 2026-07-29 [magnetics][check_creepage] A magjack's shell board-lock pads can collapse HV-to-shield creepage independently of the isolation barrier
Distinct from the chip-side/line-side barrier (see 2026-07-28 [check_creepage][gates][magnetics]).

A magjack's shell board-lock pads are frequently the ONLY shell-to-board copper path - the large
mounting holes are usually NPTH and carry no copper. On lumina-carrier's LPJG0926HENL land those
pads sat 2.287 mm centre-to-centre from the VC1/VC4 PoE centre taps, giving **0.487 mm** of copper
against the board's 0.635 mm HV rule.

Unlike the isolation barrier, this one **IS** voltage-derived (48 V tap to a shell that is tied to
GND through the shield hybrid), so `check_creepage` DOES model it and would have failed the board at
P8 - after routing. Worth catching in the library.

The fix is constrained from both sides at once: `gap = c_c - (w_a + w_b)/2` while every pad must keep
>= 0.15 mm annular ring. On a 1.70 mm board-lock drill and a 0.90 mm tap drill the best simultaneous
result is 0.687 mm, with both annulars exactly at the 0.15 mm minimum. Making the board-lock pad OVAL
(narrow toward the tap, tall along it) buys the clearance while keeping copper under a pad that takes
insertion force. Check both numbers after any such edit - it is easy to fix creepage and silently
create an annular-ring violation instead.

## 2026-07-29 [parts] lib_pull reported every part "pulled" once ONE part had landed
_pull_one's failure gate was `not fps and not sym_lib.exists()` - but aiee.kicad_sym is SHARED across
every part in the run, so after the first successful pull `sym_lib.exists()` was permanently true and
every later part returned status "pulled" whether or not anything was written for it. Measured on
lumina-par: `status: pass`, `44 of 44 pulled`, `load_check.ok: true`, and **13 parts actually on
disk**. A half-empty library ships through a green gate and only fails much later at board_init or
fp_verify. Fixed: the gate is now `not fps` alone - _footprints_for_lcsc greps the pretty dir for
that part's own LCSC id, so it is a true per-part filesystem signal. Corollary for orchestrators:
never accept lib_pull's own count; re-derive completeness from the filesystem, which is how the
lumina-par librarian caught this.

## 2026-07-29 [gates] fp_verify has NO drill handling, so a wrong THT annulus passes silently
fp_verify.py / fplib.py model pads but not drills. On lumina-par the ICD-mandated connector geometry
(1.70 mm annulus / 1.10 mm drill) came out of easyeda2kicad as J3 1.80 mm and J4 1.60 mm on a 1.050 mm
drill, and fp_verify returned `pass` on both - because the annulus is unchecked AND the DS1023
extraction omits `pad_size_mm` (the vendor publishes none), so both halves of the check were absent.
Note the failure was ICD CONFORMANCE, not safety: as-pulled J3 still gave a 0.74 mm gap = 1.17x the
0.635 mm rule. But a frozen interface two boards mate through is exactly where conformance matters.
Verify THT annulus/drill against the ICD by hand at P3; the gate cannot do it.

## 2026-07-29 [jlc][api] First live calculate: field rules the doc tables get wrong
Scopes approved; live pd-trigger quote succeeded after two corrections the transcribed tables
could not predict: (1) insideCuprumThickness is a 4+ LAYER selection only - a 2L board rejects
it with code 2129 "Only boards with four layers or more support the selection of inner copper
weight" (table says Required=yes unconditionally); (2) isAddCustomerCode/markOnPcb/
autoConfirmProductionFile must be OMITTED from calculate - the "Yes"+2 pairing rejects with
code 2708 "The Remove Order Number error" and the doc's own calculate example omits all three
(create-side options; decide at the first gated create). CONFIRMED live: copperWeight "2"
STRING form accepted on a 2L 2oz board (watch item closed); upload->fileKey->calculate chain
works; real price 40.00 USD for 10x 48x30 2L 2oz HASL vs our 19.65 estimate - order_quote's
2oz/options undercount is large, always present the API quote. Still async/missing: pcb/audit
returns code 2501 no_audit_result_error immediately after upload (JLC DFM runs async - re-poll
later; quote proceeds without it); calculate returned NO shipList because we pass no country -
freight attestation (N3 gate) needs a country input plumbed before the first create.

## 2026-07-29 [routing][drc] A net-wide HV clearance rule makes fine-pitch HV PADS unroutable, not just tight
lumina-carrier P7. The hand-written `HV_48V_clearance` (0.635 mm, TI TPS2378 guidance) excluded
only `!(A.Type=='Pad' && B.Type=='Pad')`. That stops the rule firing between two pins of a package
but NOT between a pin and the fan-out stub that must land on it - a track inherits its pad's
neighbourhood. Measured: 15 of 37 48 V pads sit < 0.635 mm from foreign copper OF THEIR OWN
footprint (U1 SOIC-8 0.200 mm, U22 HTSSOP-20 0.250-0.375 mm, U20 pad-3-to-its-own-EP 0.295 mm,
0805 caps 0.590 mm across their own pads), so those pads could not be connected at all. Confirmed
live: a V48_RAW stub on U22 pad 6 fired the rule twice at 0.250 mm against pins 5 and 7. Fix that
held: extend the exclusion to "both items inside ONE named footprint's courtyard"
(`!(A.intersectsCourtyard('U22') && B.intersectsCourtyard('U22'))`, enumerated per refdes, never
wildcarded). Generalisation: any `clearance` DRU floor above a package's own pad gap is
unsatisfiable for that package - check `min(distance to foreign copper)` per pad BEFORE routing
(work/p7/hv_escape.py is 40 lines and answers it).

## 2026-07-29 [routing][kicad] Netclass clearance is PAD-BLIND - it cannot carry an HV rule
Same board: setting the three 48 V netclasses to 0.635 mm clearance so Freerouting would honour it
in the DSN produced 30 instant DRC errors between adjacent pins of U1/U22 and across C61/C62/C63's
own two pads - a netclass has no pad-pair exclusion and no scoping at all. The .kicad_dru rule is
the only mechanism that can express "0.635 mm except inside a package". Consequence for P7: the HV
netclass clearance must stay at the routing floor (0.2 mm) and the DRU stays the DRC authority;
Freerouting therefore routes HV at 0.2 mm and open-board HV spacing must be audited after routing.

## 2026-07-29 [routing][parts] KRT: a 3-pad diff net routes as a MESH, and only the FIRST leg closes
lumina-carrier MDI runs J1 (magjack) -> D10 (ESD array) -> U10 (PHY). Handed all three pads,
`route_diff.py` builds J1-D10 + J1-U10 + D10-U10 (a ring: 96 mm of copper for a 50 mm chain, RX
skew 51 mm); `--ordering mps` gives the same star. route_critical's own mitigation (detach the
"unmatched stub pads" - here J1's staggered magjack pads) routes ONLY the short D10->U10 leg and
silently leaves the 38 mm haul to Freerouting, i.e. uncoupled. Routing the legs sequentially does
not work either: whichever leg runs second is DEFERRED ("electrically-short"/multipoint) because
the first leg's copper already hangs off the shared middle pad. What works: route each leg on its
OWN branch from the SAME clean board (detach U10 for one, J1 for the other, via
route_critical.detach_stub_pads/restore_stub_pads) and graft the two copper sets with route_edit.
The branches cannot see each other, so give them disjoint layers - F.Cu for one leg, B.Cu-preferred
(`--layer-costs 3 1`) for the other - or they overlap and merge into a short (measured: 18
shorting_items + 3 tracks_crossing when both preferred F.Cu). Post-graft, the two legs land on the
shared pad at different points, so check_diffpair reports `branch_free: false` and falls back to
TOTAL copper length - a bogus 45 mm "skew" that a short in-pad joining segment mostly resolves.

## 2026-07-29 [parts][python] KRT: relative --work-dir silently breaks, and bash mangles net names
route_critical passes `--fab-overrides <work>/fab_overrides.txt` through unchanged and runs KRT with
`cwd=<krt plugins dir>`, so a RELATIVE `--work-dir` makes KRT die with "fab-overrides file not
found" and route_critical reports `no JSON_SUMMARY`. Always pass absolute --pcb/--work-dir. Second
trap, the LEARNINGS 2026-07-23 argv rule seen from the other side: it is not enough for the SCRIPT
to pass a list - a net name typed on a Git-Bash command line is already mangled before python sees
it (`/ETH_TXP` -> `C:/Program Files/Git/ETH_TXP`). Hard-code pair names in the driver, read them
from a file, or set `MSYS2_ARG_CONV_EXCL='*'`.

## 2026-07-29 [planes_gen][drc] Two footprint facts planes_gen cannot see: existing vias-in-pad, and touching regions
(a) `ep_pads` picks the largest netted SMD pad per footprint and grids vias into it without checking
whether the FOOTPRINT already ships thermal vias. U22 (HTSSOP-20 eFuse) carries 15 thru-hole
0.6/0.3 mm vias-in-pad in its own land; planes_gen added 21 more on top -> 24 hole_to_hole warnings
and 2 holes_co_located at 0.000 mm. Check `pads_of(ref)` for thru-hole pads inside the EP first.
(b) planes_gen only de-conflicts zone priorities for regions that OVERLAP. Three same-net plane
rectangles that merely TOUCH along a shared edge (the standard "positive rectangles cannot have a
hole" pattern for a keepout band) are still `zones_intersect` ERRORS in KiCad 10 - assign distinct
priorities explicitly. Same-net fills at different priorities still merge into one island (measured:
7162 mm2 In1 GND, 1 island).

## 2026-07-29 [drc][gates] drc_routed's --parity finds footprint/symbol mismatches the P6 place gate never runs
The place gate runs DRC without `--parity`, so `footprint_symbol_mismatch` never appears until P7.
On lumina-carrier H5 (mounting hole) had `exclude_from_bom` on the footprint and `(in_bom yes)` on
the symbol - one warning, and drc_routed fails at err+warn = 0. Its four siblings H1-H4 are
`board_only` so parity skips them entirely. Fix at the symbol (a mounting hole is not a BOM line),
not the footprint. Worth a --parity DRC at the END of P6.

## 2026-07-29 [routing][kicad] A module's own pads can sit INSIDE its declared antenna keepout
lumina-carrier's ESP32-S3-WROOM-1 keepout was authored as 10 x 22 mm at the board edge (Espressif's
normative zone is 6 x 18 mm; the extra 4 mm was margin). With U30 placed at its ICD datum the
module's outermost pad columns (pins 1/2/3 and 38/39/40) land 2.0 mm INSIDE that band, so a rule
area with "no tracks" over the literal rectangle makes six module pins unconnectable - and "copper
free on every layer" is false the moment the module is placed. Author the rule area as the true
antenna zone (measured from the footprint: `at` + courtyard extent, antenna = the last 6 mm of the
25.5 mm body) plus a margin band that stops short of the pad rows. KiCad's Specctra export DOES
carry rule areas to Freerouting as `(keepout "" (polygon <layer> 0 ...))`, one per layer - verified
in the exported DSN - so the keepout is honoured by the autorouter, and stitch_vias skips pads
inside it with `no_clear_spot`. No pipeline script creates rule areas; planes_gen only makes
positive pours, so a small bundled-python SWIG worker (`SetIsRuleArea` + `SetDoNotAllowTracks/Vias/
ZoneFills` + `SetLayerSet`) is the sanctioned way to add one.

## 2026-07-29 [easyeda2kicad][kicad] 3D-model origin offsets in renders are NOT footprint defects
pd-trigger J1 (GCT USB4105-GF-A-120, LCSC C5184243): the render showed the connector body
overhanging the board edge with contacts/peg-slots exposed behind it - user flagged possible
misalignment AFTER the fab order was placed. Ground truth: the fab drill/copper matched GCT's
recommended layout dimension-for-dimension (2x O0.65 pegs at 5.78; slots 1.0x2.1 + 1.0x1.8 at
3.68/4.18; 12x1.15 contacts 8x0.30+4x0.60 at 0.5 pitch) - the EasyEDA 3D model origin is just
~2 mm off along the mating axis. Verification path that settles it in minutes: (1) the ordered
.drl (tool table + hit coords) is the truth the fab received; (2) the manufacturer's drawing
PDF (gct.co/files/drawings/<part>.pdf worked with a browser UA; LCSC's /datasheet/<code>.pdf
URL returns HTML). Renders judge MODELS, drills judge BOARDS. fp_verify only covers parts with
datasheet extracts (pd-trigger had U1 only) - connector footprints deserve the extract+verify
treatment before ordering, and 3D-model offsets deserve a fix in the workspace lib so design-doc
renders stop alarming humans.

## 2026-07-29 [geometry][keepout][planes] Keepout checks need STRICT-interior containment: plane regions deliberately ABUT the band they exclude
Verifying that the ESP32-S3 antenna band was copper-free on lumina-carrier, a hand-written check
reported **14 violations** on In1.Cu and In2.Cu. All 14 were false.

The cause is structural, not a coding slip. The recipe that carves a hole out of a plane uses three
positive rectangles per layer, because a single positive rectangle cannot have a hole - so the middle
region is authored to **stop exactly at the keepout's edge** (`ex2 - 10`, i.e. x = 109.58, the band's
left boundary). Its fill polygon therefore *legitimately* carries vertices lying precisely ON the
boundary. An inclusive test (`BAND[0] <= x <= BAND[2]`) counts every one of them as copper inside the
band. A strict test with a small epsilon (`BAND[0] + EPS < x < BAND[2] - EPS`) returns zero.

**Any containment test against a deliberately-abutting region must be strict, not inclusive.** This
will bite every future keepout, courtyard, plane-void, board-edge and exclusion-zone check, because
"the excluded region and the thing excluded from it share an edge" is the normal case, not the
exception - that is what makes the exclusion exact.

The dangerous part is the failure direction: an inclusive test cries wolf on a board that is
**correct**, and the obvious "fix" is to tear up good copper or shrink a plane that was already right.
Fix the checker, not the board. Confirm by sweeping epsilon (0.00 / 0.01 / 0.10 / 0.50 mm) - if the
count collapses to zero at any nonzero epsilon, every hit was a boundary artifact and the geometry was
never wrong.

Related: no gate in the pipeline checks a keepout band at all. `constraints.json.placement.keepouts`
is read only by the P6 placement scripts; the router and `planes_gen` never see it, so an F.Cu/B.Cu
keepout RULE AREA has to be added at P7 and the inner-layer exclusion has to come from the plane
region shaping. Verifying it is therefore a manual geometric step - which is exactly why the checker
being trustworthy matters.

## 2026-07-29 [geometry][creepage][measurement] A pad-gap formula is only valid for one pad SHAPE - using the wrong one moves the answer by 0.3-0.5 mm in either direction
Measuring the cable-side/PHY-side barrier on lumina-carrier's magjack, I produced **three different
numbers for the same pair of pads** - 1.451, then 1.148, then 1.613 mm - and reported two of them
upstream before the third settled it. The cause was never the parser; it was applying a formula that
did not match the pad shape.

    circle-circle : gap = hypot(dx, dy) - (r1 + r2)                       <- radial form
    oval          : stadium - distance between the two spine SEGMENTS, minus radii
    rect-rect     : per-axis - dx = |dx_c| - (w1+w2)/2 ; dy likewise ;
                    gap = hypot(max(dx,0), max(dy,0))

**The radial form is EXACT for circles and overestimates rectangles** (by 0.303 mm on one diagonal
pair here). **The rect form is EXACT for rectangles and underestimates circles** (by 0.465 mm on the
same pair). I used each on the wrong shape in turn, so I first over-reported a gap, then "corrected"
a number that had been right, declared a false failure, and shrank a pad that did not need shrinking.

KiCad tells you the shape in the pad header - `(pad "2" thru_hole circle ...)` - and it is the second
token after the pad number. Read it. THT signal pads are usually `circle`; board-lock and shield tabs
are often `oval`; SMD pads are `rect`/`roundrect`. A single footprint routinely mixes all three, so a
gap tool that assumes one shape is wrong somewhere in every real footprint.

Write ONE shape-aware helper and use it everywhere. A capsule model covers all three: a circle is a
degenerate segment with a radius, an oval is a segment along its long axis with radius = half the
short axis, and only true rectangles need the per-axis form.

Two second-order lessons:
- **The direction of the error matters more than the size.** Over-reporting a gap hides a real
  violation; under-reporting invents one and invites you to "fix" correct hardware. I did both, and
  the under-report was worse - it cost a pad shrink and a retraction.
- **Re-deriving a number is not the same as re-deriving it correctly.** When a measurement is
  contested, fix the METHOD and state which model you used, rather than producing another figure.

## 2026-07-29 [routing][parts] KRT's default 200k A* iteration cap, not congestion, is what fails a long haul - and the log says which
lumina-carrier P7 spent three routers and ~10 rip-set attempts on `/FAULT` (U22 pin 15 -> the J4 end,
a 68 mm MST edge) and `/ADC0` (D41 -> U30, 59 mm). Every attempt reported `No route found after
200000 iterations (forward) ... 410000 (both directions)` and `All rip-up attempts failed`; broad rip
sets only traded one net for another. Raising `--max-iterations` from its 200000 default to 4000000
(with `--max-probe-iterations 60000`) routed BOTH on the first try, and neither needed a wider rip set
than the log's own hint list. The tell is in the rip-up ladder's own diagnostic:
`Coverage: 1863/13659 frontier cells attributed to routed nets; 11796 static/unrippable` - 86 % of the
blocking frontier was static copper (pads, 48 V tracks at 0.635 mm, plane vias), so no amount of
ripping could open it; the flood front simply needed to be allowed to go further around. Read that
Coverage line BEFORE building a rip set: high static share => raise the iteration budget, not the rip set.

## 2026-07-29 [routing][gates] KRT output boards must be refilled before DRC, or the gate reports ~375 phantom zone errors
`krt_finish.py` writes a new .kicad_pcb with fresh vias but does NOT refill the pours, so
`gate.py --gate drc_routed` on the raw KRT output reported 375 failing (261 errors) - 371 of them
`clearance`/`hole_clearance` between a NEW via and a `Zone [GND] on In1.Cu` / `Zone [+3V3] on In2.Cu`
whose fill still predates the via. Only 4 were real. Copy the KRT output over
`kicad/<board>.kicad_pcb` first (so the .kicad_pro/.kicad_prl/.kicad_dru sidecars are beside it -
kicad-cli needs them for correct rules), then
`kc.run_drc(kc.resolve_cli(), pcb, refill=True, save_board=True)`, and only then gate. Same board,
same copper: 375 -> 7.

## 2026-07-29 [routing][placement] "Widen the corridor" was the wrong diagnosis for a boxed-in QFP GND pad - measure the pad extent, not the footprint origin
lumina-carrier U10 (LQFP-48, 0.5 mm pitch) pad 9 (GND) read as needing a wider gap between the south
pad row (ends y 83.6819) and C35. A P7 predecessor moved C35 +0.300 mm in y, computing the corridor
from C35's FOOTPRINT y (85.813 - 0.45 = 85.363) instead of its pad-1 CENTRE y (85.113 - 0.45 =
84.663) - a 0.700 mm error, so the "1.6811 mm corridor" was really 0.9811 mm. The move also put pad 1
on top of an existing `/ETH_RSTn` run at y 85.55: `gate place` PASS and `check_decoupling` unchanged,
but +6 DRC errors (1 shorting_items, 4 clearance, 1 solder_mask_bridge). ALWAYS re-run DRC after a
placement micro-adjust; the place gate does not model copper.
And the corridor was never the blocker: `via_why.py` showed the real ones were a `+3V3` fan-out rail
crossing at y 84.02, a void in the In1 GND fill created by the neighbouring +3V3 plane vias' clearance
holes (the via would land in the void and connect to nothing), and `/ETH_MISO`'s B.Cu descent at
x 97.55/97.40. The pad escaped NORTH instead, into the QFP's own 7x7 mm die shadow (via at
(96.35, 80.65), 0.5 mm) - which needed only `/eth/EXRES` ripped and re-routed, because its y-81.85
horizontal was the one wall sealing the north side (0.2319 mm residual gap; a 0.1 mm track needs 0.5).

## 2026-07-29 [place][gates][routing] STOP: after P7 begins, `gate place` and `check_decoupling` are NOT valid oracles for a placement change - only DRC is
**This mistake shorted a board and both checkers said PASS.**

On lumina-carrier I moved C35 by +0.300 mm to widen a fan-out corridor on a board that already carried
**3089 routed segments**. I validated the move the way P6 taught me to:

    gate place            -> PASS (0 failing)
    check_decoupling      -> unchanged, no new warnings

Then DRC found **6 new errors including `shorting_items` and `solder_mask_bridge`**: the pad had landed
on an existing `/ETH_RSTn` run at y 85.55.

**Both oracles are structurally blind to routed copper.** `place_metrics`/`placelib` reason about
courtyards, pad extents, keepouts and the outline. `check_decoupling` reasons about cap-to-pin distance
and loop inductance. **Neither one looks at a single track or via.** They are complete oracles at P6,
when there is no copper, and they silently stop being complete the instant the router lays the first
segment - and nothing in the pipeline tells you that transition happened.

**Rule: any footprint move after routing has started must be validated with `kc.py drc` (or the
`drc_routed` gate), not with the place gate.** Use the place gate as a NECESSARY-but-not-sufficient
pre-filter: it still catches courtyard and keepout illegality, which DRC will not phrase as such.

Two aggravating factors worth knowing:
- The correct sequence is snapshot -> move -> **DRC** -> place gate -> check_decoupling, and revert on
  any new DRC violation. I had the snapshot (which is why the revert was clean) but ran the checks in
  the wrong order and stopped at the first PASS.
- The same move was ALSO built on a bad measurement: the corridor figure read the footprint's `(at ...)`
  ORIGIN y rather than the **pad-1 centre** y, off by exactly 0.700 mm - so a claimed 1.681 mm corridor
  was really 0.981 mm. When measuring clearance to a specific pad, resolve the pad, never the footprint
  origin; on a 0603 they differ by roughly half the pad pitch.
- And it could not have worked regardless: the true blocker was a **void in the In1 GND fill** created
  by neighbouring plane vias' clearance holes, so a via in that corridor would have connected to
  nothing. Check that a plane actually has copper where you intend to land a stitching via.

## 2026-07-29 [routing][krt] KRT's iteration cap, not the rip set, is usually what blocks a long haul - and its own diagnostic tells you which
Two long nets on lumina-carrier (`/FAULT` 68 mm, `/ADC0` 59 mm) defeated roughly ten rip-set attempts.
The ladder's own diagnostic line explained why:

    Coverage: 1863/13659 frontier cells attributed to routed nets; 11796 static/unrippable

**86 % of the frontier was static**, i.e. pads, keepouts, plane edges and locked copper - things no rip
set can move. Ripping more nets could not help by construction. Raising `--max-iterations` from the
200000 default to **4000000** routed both nets on the first try.

Read that coverage line before choosing a rip set. High static fraction -> raise iterations. Low static
fraction -> a rip set may genuinely help.

Second finding from the same board: **broad rip sets trade nets 1-for-1.** One set fixed STATUS+RXD0 but
broke BOOT+I2C_SDA; the next fixed BOOT but broke ENABLE_M+ETH_RSTn. What converged was **one target net
at a time, with only its own hint list, gate after each attempt, and keep the result only if strictly
better** - otherwise revert. Keep a snapshot ladder so "strictly better" is enforceable.

## 2026-07-29 [krt][clearance] KRT's `--clearance` is a CAP on the netclass map, not a floor - but `--net-clearances` is not capped
On a board with a hand-written HV rule (0.635 mm on the 48 V nets) and a 0.2 mm general floor:

- Passing `--clearance 0.2` **silently produced 480 HV violations.** The flag caps the netclass map, so
  it pulled the HV nets DOWN to 0.2 mm rather than raising anything.
- Passing an explicit **`--net-clearances` file is NOT capped** (only the auto-read path is), which is
  how per-net HV clearance survives while everything else keeps the floor.

Also: KRT cannot read a `.kicad_dru`. Every `PWR_*` netclass in the `.kicad_pro` carried 0.2 mm and the
0.635 mm existed only in the DRU file, so the router had no way to know about it except the explicit
net-clearances file. If a hand-written DRU rule is the only thing holding a safety clearance, the
autorouter is not enforcing it - pass it explicitly and re-run DRC after.

Practical note: Git-Bash mangles a leading `/` in net names on the command line, so pass net lists via a
JSON job file rather than argv.

## 2026-07-29 [geom][drc][clearance] `bg.nets` omits UNNETTED pads, so any clearance model built from it is blind to 37 real copper items
lumina-carrier P8. A widening pass computed each undersized power segment's max width as
`2*(dist(centreline, foreign_copper) - clearance)`, iterating foreign copper as
`for onet in bg.nets: bg.net_copper(onet, layer)`. `BoardGeom.nets` contains only NAMED nets, so every
pad with no net is invisible to that loop - **37 of them on this board** (U10 x16, J1 x6, U30 x4,
U22 x4, D10, U20, H1-H5). The pass widened four +3V3 escapes to 0.500 mm and DRC came back with 4
clearance errors at **0.0665 / 0.0689 mm** against `U10-18`, an unconnected LQFP-48 pin. Fix:
`for p in bg.pads_of(): if not p.net and layer in p.layers: ...`. Same trap applies to any
`net_copper`-driven audit (stitch candidates, via placement, creepage sweeps).

Second, related: `net_copper(net, layer)` counts a through VIA's own barrel as copper on **every layer
it spans**. So "which layers does this via bridge?" answered by intersecting the via with
`net_copper` returns *all four* on a 4-layer board, always. Build the bridged-layer set from
tracks + pads + zone fills only.

## 2026-07-29 [route_edit][kicad] route_edit adds BEFORE it removes, so you cannot replace an item at the SAME position in one ops file
`route_swig.verb_apply_ops` indexes existing items first, applies every `add_*`, and only then applies
`remove` (documented at the top of the module, easy to miss). `add_via` dedups on
(position, net) with a 0.001 mm tolerance, so an ops file that does
`remove <uuid of via at P>` + `add_via at P (different size)` has its add skipped as `"exists"`, the
removal then deletes the original, and the post-apply verify fails with
`via at (x, y) (NET) not in saved board` - the whole file rolls back. Changing a via's pad size or a
track's width **at unchanged geometry** needs TWO route_edit invocations (remove, then add). Widening a
track works in one file only because the width is part of `_track_key`, so the wider copy is not a
duplicate.

## 2026-07-29 [check_diffpair][gates] check_diffpair's graph ignores vias AND pads - a 0.14 mm endpoint mismatch silently turns "skew" into TOTAL COPPER LENGTH
`net_graph()` nodes are track endpoints snapped to 3 dp; **vias and pad copper are not edges.** So two
track chains that meet only *through* a via (or through a pad's copper) land in different graph
components, `trunk_length` cannot connect the terminals, and it falls back to
`sum(all track lengths)` - reported only as `branch_free: false` in `checked`, never as its own
violation. On lumina-carrier's grafted MDI this produced "skew 35.65 mm / 45.54 mm" against a 2.5 mm
limit on pairs whose real trunk skew was 6.27 mm and 0.98 mm. Three separate causes, all
sub-0.3 mm and all electrically fine (the copper OVERLAPS in every case, so DRC and the netlist are
clean):
- `/ETH_TXN` B.Cu (93.95, 83.1851) vs (93.80, 83.35) - **0.2229 mm** apart, 0.26 mm tracks
- `/ETH_RXP` B.Cu (82.7474, 85.8649) vs (83.00, 85.85) - **0.2530 mm** apart
- `/ETH_RXP` F.Cu escape ending at (96.15, 81.85) and its B.Cu continuation starting at
  (96.05, 81.95) - joined only by the via at (96.15, 81.85), **0.1414 mm** of endpoint mismatch
Adding one same-net segment per break (3 tracks, 0.14-0.25 mm long) made both pairs `branch_free:
true`. **Always read `branch_free` before believing a skew number** - and if it is false, the number is
not a skew at all.

Second limitation in the same check: `matched_terminals` pairs a p-pad with an n-pad only within
`TERM_PAIR_MM = 2.5`. A magjack's differential pads are further apart than that (LPJG0926HENL:
TXP/TXN pads 2.84 mm, RXP/RXN pads **4.58 mm**), so J1 is not a matched terminal and the "trunk" is
measured from the ESD array to the PHY only. On this board the gate PASSED `/ETH_RXP//ETH_RXN` at
0.98 mm while the true magjack-pad-to-PHY-pad skew was **6.451 mm (43 ps)**, 4.326 mm of it inside the
J1 escape the gate never looks at. Measure connector-pad to IC-pad yourself before believing a pass.

## 2026-07-29 [check_current][gates] the via-count rule is unsatisfiable for a PLANE-fed rail, and `overrides` cannot reach it
Extends the 2026-07-28 pd-trigger entry. `check_current` needs
`ceil(current_a / via_amps)` vias in EVERY cluster, and `segment_current`'s `overrides` feed only the
track-width test - vias and pour necks always use the full rail budget. For a rail whose trunk is a
POUR, every via is a single-pin leaf tap by construction: on lumina-carrier `+3V3` (1.0 A, 0.5 A/via)
had **27 clusters of exactly one via**, each a pad -> 0.2-0.6 mm escape -> plane tap.
Machine-measured feasibility of doubling them (0.6/0.3 vias, 0.2 mm clearance, 0.5 mm hole-edge floor,
companion must sit on the net's copper on the same two layers): **2 of 44 clusters placeable**; 26 had
**zero** candidate positions because the outer-layer stub is shorter than the 0.8 mm minimum
via-to-via pitch. Doubling needs new outer-layer copper, i.e. a re-route, not a via drop. Budget for
this at P5/P7 (fan the rail out with 2-via taps from the start) - it cannot be retrofitted at P8.

## 2026-07-29 [check_creepage][gates] `voltages` is net-to-REFERENCE, so it cannot express a bridge-input PAIR - a 0.33 mm 57 V gap passes silently
`check_creepage` computes `dv = v_hv - v_other` from `constraints.json.voltages` and skips any pair
with `abs(dv) <= 30`. The four PoE centre taps are all declared 57 V, so **A1<->A2 and B1<->B2 are
never checked** - yet those are the two AC inputs of one external bridge, i.e. the full line voltage
sits between them. Measured on lumina-carrier: `/poe/POE_TAP_A1` <-> `/poe/POE_TAP_A2` =
**0.3295 mm on all four layers** (the two transition vias at (49.650, 74.213) and (49.200, 73.400),
0.9295 mm centre-to-centre, 0.6 mm pads), against an IPC-2221B B2 requirement of 0.60 mm outer.
B1<->B2 measures 1.4778 mm and is fine. Nothing in the gate suite reports the A-pair. Declare the
negative-side tap of each bridge at **-57 V** (as `V48_RTN` already is) and the pair becomes a
114 V difference the checker can see - or add an explicit `.kicad_dru` rule.

Also worth knowing: `check_creepage`'s violation `pos` is `ca.representative_point()` - a point
somewhere on the offending NET's copper, **not** the location of the tight gap. Locating a creepage
violation means re-deriving the nearest-item pair yourself.

**FOLLOW-UP (same day, after fixing it): a worst-pair-only sweep HIDES ITS SIBLINGS.** The A1<->A2
fix above moved both transition vias and took the gap to 0.6502 mm (F.Cu) / 0.6524 mm (inner, B.Cu),
DRC-confirmed. Only *then* did a re-sweep of the same net pair find a SECOND violating pair -
A1's south transition via against A2's B.Cu run at **0.5500 mm**, and A1's run against A2's corner at
**0.5826 mm**. Both were masked by the 0.3292 mm pair while it existed. So: after fixing a
geometric-minimum violation, RE-SWEEP the whole net pair; do not trust the pre-fix list, and do not
trust one violation per pair as the whole story. Same applies to any check that reports a minimum.

Two more from the same fix, both cheap and both worth doing every time:
- **A DRU rule that does not parse and a DRU rule that never fires look identical** (DRC just says
  0 violations). PROVE a new rule is live by temporarily setting its threshold to something
  unreachable and confirming it fires with the actual distances you expect, then set it back. Raising
  `poe_tap_differential_pair` from 0.60 to 0.90 mm produced 17 hits reporting `actual 0.6502 mm` and
  `actual 0.6524 mm` - which simultaneously proved the rule live AND independently confirmed the fix
  with a second oracle (KiCad DRC) instead of only the geometry script that made the fix.
- **Where a checker's model structurally cannot express a constraint, encode it in `.kicad_dru`.**
  The tap-pair gap is now held by a named rule for exactly the reason
  `magjack_isolation_barrier` exists: a voltage-derived checker cannot see a hipot/differential
  requirement, so without the rule any future reroute silently reopens the gap and nothing reports it.

## 2026-07-30 [jlcapi][order_submit][SPEND] `pcb/create` returned `unknown_error` code 2 on HTTP 200 - and there is NO way to ask the API whether the order landed
First live `--api-create` on this account. Everything upstream was clean - `uploadGerber` ok,
`audit` ok/200 with `red[]` and `yellow[]` empty, `calculate` returning the exact authorised
43.19 USD - and `pcb/create` came back **HTTP 200 with `{"code": 2, "message": "unknown_error"}`**,
trace `4e0f08d4e3c04a9b80b19553624c43a8`. `classify()` has no rule for code 2, so it falls through to
the generic `error` bucket and `REMEDIATION` has no entry, i.e. **the tool cannot tell you what to do
next and neither can the API**.
**The dangerous part is not the failure, it is the unobservability.** The Open API exposes
`pcb/order/detail` and `pcb/wip/get`, and **both require a `batchNum` you must already hold**;
`wip/get` with an empty payload returns `param_empty` (code 3), and there is **no list/search endpoint
at all**. So after an ambiguous create you cannot ask "did an order appear on my account?" - the only
oracle is the JLCPCB web portal. Combined with the fact that an HTTP-200-plus-business-error is
indistinguishable from a partially-applied create, **a blind retry is how you buy the board twice.**
Protocol that follows, and it should be in the playbook: on any create verdict that is not `created`,
STOP. Do not retry. Report the trace id, state that the created-latch is unarmed (so the tool WILL
allow a retry - the latch is not protecting you here), and require a human portal check before any
second attempt. The latch only arms on success, which means it defends against a *deliberate* second
order and not at all against an *ambiguous first* one - the exact case that costs money.

## 2026-07-30 [order_submit][stackup] `derive_copper_oz` silently defaults to 1 oz on a heading it cannot parse, and says "no stackup.md" when the file exists
`derive_copper_oz` scans `architecture/stackup.md` for a line starting with `## Chosen`. This board's
heading is `## 1. Chosen stackup` - numbered - so `startswith("## Chosen")` is False, the loop finds
nothing, and the function falls through to the **wrong** terminal message:
`"no architecture/stackup.md -> default 1 oz"` on a board whose `stackup.md` is present and 
readable. Two separate defects in one line: a parser that misses any numbered heading, and a
diagnostic that blames a missing file for a parse miss.
It was harmless here only because the board really is 1 oz (JLC04161H-3313). The module's own
docstring calls copper weight "a board-killer" and `_check_oz_mentions` exists specifically to stop a
2 oz design being quoted at 1 oz - so a 2 oz board with a numbered stackup heading would defeat that
guard **silently and by default**, which is the failure the guard was written to prevent. Match on
`"## " ... "Chosen"` anywhere in the heading, and distinguish "file absent" from "no Chosen line
found" in the source note.

## 2026-07-30 [fab_export][order_submit][jlcapi] The gerber sha256 is NOT a design fingerprint - every export changes it, so a sha-bound order latch self-invalidates
`fab_export.py` re-exports gerbers whose headers embed a creation timestamp, so **re-running it on an
unmodified board produces a different zip sha256**. Measured on lumina-carrier: sha
`3afe6590...` -> `4e192c7e...` across two exports 55 minutes apart with **zero** design change - and the
only differing line in the entire 12-file package was
`; DRILL file KiCad 10.0.3 date 2026-07-30T07:07:03` vs `...T08:02:01`. Everything else, including all
four copper layers, was byte-identical.
Two consequences that matter:
1. **A changed sha does not prove the design changed**, and a coordinator or reviewer asking "re-upload,
   the board changed" may be reacting to nothing. Diff the package with the date lines filtered
   (`grep -v -iE "creationdate|generation software|^G04 .*20[0-9][0-9]"`) before believing it.
2. `order_submit`'s order latch is **gerber-sha-bound**, so a harmless re-export invalidates a
   previously approved quote token and forces a re-upload + re-audit. That is fail-safe (it errs
   toward re-checking before money), but it means **the sha cannot be used as a "has the design
   changed" test** - only as a "is this exact file the one I quoted" test.
Fix worth having: a canonicalised design hash (copper + drill coordinates only, headers stripped) as a
separate field alongside the file sha.

## 2026-07-30 [jlcapi][order_submit] The Open API has NO assembly surface at all - it cannot answer any PCBA question, even to refute one
Confirmed by grepping the entire `calculate` response and request: the only assembly-adjacent keys in
the whole payload are `stencilFee`, `originStencilMoney` and `stencilLayer` - and a stencil is a
PCB-side product. `calculate_request` carries exactly `{achieveDate, country, fileKey, orderType,
pcbParam}`: **there is no `bomParam`, no `smtParam`, no assembly quantity, no BOM or CPL reference.**
`pcb_cost_info` is entirely fabrication line items (`insideCuprumThicknessFee`, `adornPutFee`,
`halfHoleFee`, ...).
So questions of the form "does ordering bare PCBs now foreclose assembling a subset later?" are
**not answerable from this API in either direction** - it has no concept of an assembly order to
relate a bare order to. Extends the existing "PCB ordering only, no assembly/PCBA API" limit with the
practical corollary: do not attempt to infer PCBA business rules from `calculate` output, and say
plainly that it cannot be determined rather than reasoning from the absence of a field.
Useful real numbers the API *does* give, which the estimator does not: at qty 10 the bare-PCB total was
**35.47 USD**, of which **17.07 USD (48 %) is `insideCuprumThicknessFee`** - the inner-copper-weight
charge on a 4-layer 1 oz stackup. `order_quote`'s estimate for the same 10 boards was 9.90 USD of PCB,
i.e. **3.6x low**, because it models outer-layer area and not inner-copper weight. Also: JLC rejects
non-standard quantities (`pcb_qty_error` code 2103 for qty 14) but accepts 5/10/15/30, and PCB price is
**not monotonic per unit** - 10 boards cost 35.47 (3.55 each) while 15 cost 62.70 (4.18 each).

## 2026-07-30 [board_init][dfm][gates] `min_hole_to_hole: 0.25` at severity WARNING is the SECOND sub-fab floor in the shipped `.kicad_pro` - and it hid two real defects until P9
Companion to the `min_track_width: 0.1` entry, same shape, found the same way. The generated
`.kicad_pro` carries `min_hole_to_hole: 0.25` where **every** JLC profile in
`reference/jlc_capabilities.yaml` says `min_hole_to_hole_mm: 0.5` - and it is severity **warning**.
Consequence on lumina-carrier: two drill pairs at **0.3136 mm** and **0.3505 mm** were above 0.25 and
therefore never fired, surviving to `gate dfm` as 5 errors (each defect produced one hole-to-hole plus
one or two copper-clearance findings, because the annular rings were 0.0136 / 0.0505 mm apart).
Raising the floor to 0.5 mm and the severity to `error` still leaves the board at DRC 0/0 - the
board-wide minimum is **0.5016 mm** across 440 drills - so this costs nothing and would have caught
both at P7.
**Standing check at P7 entry, now covering two fields**: assert
`.kicad_pro.min_track_width >= profile.min_trace_width_mm` AND
`.kicad_pro.min_hole_to_hole >= profile.min_hole_to_hole_mm`. Better: have `rules_gen` emit an
`aiee_hole_to_hole_floor` DRU rule alongside `aiee_track_width_floor`, so a hand-written `.kicad_dru`
that replaces the generated file loses both floors loudly rather than silently.
Margin note worth a policy decision: after the fix, 38 drill pairs sit between 0.50 and 0.56 mm, the
tightest at **0.5016 mm** - legal, but 1.6 micrometres over the fab floor. A router that optimises to
the bare limit leaves nothing for drill wander.

## 2026-07-30 [kicad][connectivity][route_edit] A track endpoint inside a VIA or PAD is connected; inside another TRACK's body it is NOT
Machine-verified while repairing a deleted via's stub. KiCad's connectivity treats an endpoint landing
inside a via or a pad as connected, but an endpoint landing inside another **track's body** is not -
even well within that track's half-width. A replacement bridge that ended **0.0368 mm** from the stub
end, i.e. deep inside its 0.250 mm half-width, still produced `track_dangling` in DRC.
So: **deleting a via that a track end rested on always requires the replacement to share an EXACT
vertex with that track end**, not merely to overlap it. Snap to the endpoint coordinate, do not
approximate. This is the same family as the 2026-07-29 `check_diffpair` finding that sub-0.3 mm
endpoint mismatches split a net's graph into separate components - two different subsystems, one
underlying rule: **KiCad joins copper at coincident vertices, not at overlapping geometry.**

## 2026-07-30 [stitch_vias][dfm] `stitch_vias` puts a stitch 0.35 mm from a thermal-via drill INSIDE the pad it is stitching
Both P9 DFM hole-to-hole defects on lumina-carrier were generator output, and one was this: a GND
stitch via at (44.46, 96.46) landed 0.3505 mm from U22 pad 21's own plated thermal-via array - 15
drills on a 1.3 mm grid inside the HTSSOP-20 exposed pad. `stitch_vias`' hole floor is a centre-point
test that does not read footprint-embedded plated pad drills at all (extends the existing note that its
hole floor cannot see slot extents). It should (a) read footprint pad drills, applying the `-frot` /
`-prot` position and shape transforms already recorded here, and (b) skip candidates inside a pad that
already carries its own via array.
Recovery that worked, and the reasoning is the reusable part: **move the via rather than delete it**,
to the centroid of the surrounding thermal-via cell - that held the via count constant, so no
`check_current` cluster changed and `check_thermal`'s `nearest_via_mm` moved only 0.27 mm. When you
must delete instead, check which member of a via cluster you remove: on the +3V3 cluster here,
removing one via left a 2-via cluster that still passes `check_current`'s 1 A / 2-via rule, while
removing the *other* would have split it into two 1-via clusters and ADDED two violations.

## 2026-07-30 [place_edit][placement][silk] Moving a footprint on a ROUTED board: two things nothing in the pipeline does for you
From a scoped P6/P7 backward edge that moved 5 parts on a board with ~3294 tracks and landed at
`drc_routed` 0/0 - but only on the second attempt.
1. **`place_edit` / `place_metrics` have no silkscreen model.** Attempt 1 was courtyard-legal AND
   copper-clean (0 DRC errors) and still failed the gate with **39 silk warnings**, because
   `drc_routed` counts warnings. A courtyard-legal move is not a legal move. Until `placelib` owns a
   silk legality class, build the obstacle set from KiCad's own
   `TransformShapeToPolygon` / `TransformTextToPolySet` (see `work/p8/silk/probe_geom.py`) and screen
   candidates against it before touching the board.
2. **Moving a footprint ORPHANS the GND stub and stitching via that served its pads.** Nothing rips
   them; they become `track_dangling` / `via_dangling` warnings that fail `drc_routed`. On this edit
   that was 4 stubs + 4 vias, removed by hand after confirming nothing else touched them. A
   `place_edit`-adjacent detach/reattach-pad-stubs helper should own it
   (cf. `route_critical.detach_stub_pads`).
**Correct op order, and it is the whole difference between this and the C35 short earlier in the run:**
rip the affected nets FIRST (`route_edit` remove by uuid), THEN move the parts, THEN route fresh.
Moving parts while their old copper is still attached is what lands a pad on a live run.
Refinement to the transform note above: a footprint text field's stored `at` **angle is ABSOLUTE**,
not local-plus-footprint, even though its **position** is local. A hand-rolled model that adds the two
mis-rotates the refdes obstacle of every rotated part - R34's label is 1.21 x 2.68 mm tall, not
3.0 x 1.15 wide - and then silently optimises against the wrong obstacle set. And a 3-char refdes at
size 1.0 / thickness 0.15 inks to **2.64-2.69 x 1.16 mm** (advance ~0.845 x size), so guessing 0.8 or
0.95 per character both give wrong answers. Probe it, do not assume it.

## 2026-07-30 [check_return_path][stackup] On an F / GND / +3V3 / B stackup the check fails EVERY B.Cu trace by construction - name it as a waiver CLASS
`check_return_path` compares a signal layer against the nearest plane carrying its DECLARED reference.
On lumina-carrier (F.Cu / In1=GND / In2=+3V3 / B.Cu) the nearest plane to any B.Cu trace is **+3V3**,
so every GND-referenced B.Cu run reports `corridor_void` no matter how good the layout is. All 13
current findings are this, including the 2 that appeared the moment three oscillator nets were
declared in `high_speed`. Consequence worth internalising: **declaring a net can only ever raise the
finding count**, and on this stackup a B.Cu route is unfixable-by-construction, so the count is not a
quality signal. Either resolve the reference plane per signal layer (the real fix) or record it once as
a stackup waiver class - otherwise every future B.Cu route silently adds errors nobody can clear, and
teams learn to ignore the check.

## 2026-07-30 [kicad_dru][check_creepage][safety] A DRU rule that covers an HV net against SOME neighbours reads as protection and is not - audit COVERAGE, not existence
The most important systemic finding of the lumina-carrier run. The board declared **7 nets at
|V| >= 30 V** and had 5 hand-written HV rules, and a reviewer still found two sub-requirement 57 V
gaps on a board reporting **0 DRC errors**. Cause: only **3 of the 7** (`V48_RAW`, `V48_RTN`,
`+48V_SW`) were named in a *general* clearance rule. The four `/poe/POE_TAP_*` nets appeared only in
rules that constrained them against a NAMED subset - `magjack_isolation_barrier` (taps vs the four
`/ETH_*` nets) and `poe_tap_differential_pair` (taps vs each other). Nothing held a tap to 0.635 mm
against the rest of the board, so:
- `/poe/POE_TAP_A2` <-> `/poe/LED_Y_A` sat at **0.2031 mm** (217 pairs), and
- tap <-> J1 board lock sat at **0.6029 mm**,
both invisible to DRC *and* to `check_creepage` (the latter for separate reasons - netless pads have
no declared voltage, and equal-potential pairs are skipped).
**Standing check after authoring any HV rule set**: enumerate every net in `constraints.json.voltages`
with `|V| >= 30` and assert each appears in at least one clearance rule whose condition does NOT
restrict `B` to a named list. Grep for `B.NetName ==` in your own rules - every occurrence is a
coverage hole unless a general rule also covers that `A`.
Second, narrower trap in the same family: **netless conductors**. J1's two board locks are plated
3.2 mm pads on all four layers with no net, 0.66 mm from 57 V. `check_creepage` cannot see them
(no net -> no declared voltage -> no `dv`), and a `.kicad_dru` pad-pair exclusion - added for the good
reason that a lead frame is not a routing choice - also excludes them, because the tap side is a pad
too. Reach them with `B.NetName == ''`, and set the threshold to what the LAND can actually achieve
(0.60 mm here, IPC-2221 B2), not the board-wide aspiration, or the rule is permanently waived.

## 2026-07-30 [board_init][rules_gen][dfm] `min_track_width: 0.1` is below EVERY JLC profile - and this is the second time the same defect bit
Already recorded on 2026-07-29 from the DFM side; repeating the actionable half because it cost a
second fix cycle. `board_init.write_pro(pro_path, min_track: float = 0.1)` hard-codes 0.1 mm.
`reference/jlc_capabilities.yaml` minimums are 0.1016 (4-layer 1 oz), 0.127 (2-layer), 0.1524 (2 oz) -
**all coarser**. `rules_gen` emits the correct floor plus an `aiee_track_width_floor` DRU rule, but a
hand-written `.kicad_dru` REPLACES that file rather than extending it, so on lumina-carrier the floor
was absent and 189 tracks were laid at exactly 0.1000 mm - legal against the board's own DRC, and
**1.6 micrometres** under what the fab can make.
Two rules: (1) a hand-written `.kicad_dru` must START from the `rules_gen` output, never replace it;
(2) assert `.kicad_pro.min_track_width >= jlc_capabilities[profile].min_trace_width_mm` at P7 entry.
The general form of the lesson is the dangerous part: **`drc_routed` 0/0 does not imply
manufacturable**, because DRC checks the board against rules the pipeline itself wrote.

## 2026-07-29 [silk][place_edit][kicad] `GetTextBox()` is 1.70 mm where DRC's INKED stroke box is 1.16 mm - use the wrong one and correct refdes targets look infeasible
Measured on KiCad 10.0.3 at text size 1.0 mm / thickness 0.15 mm: `PCB_TEXT.GetTextBox()` reports
**1.6965 mm** of height, but the polygon DRC actually tests - `TransformTextToPolySet`, the inked
stroke outline - is **1.162 mm**. Sizing refdes placement off `GetTextBox` therefore over-constrains by
about **0.27 mm per side**, which on a 2.5 mm-pitch passive row is the difference between a solvable
label and an "impossible" one. This is what let a greedy solver take lumina-carrier from 95
mis-attributed refdes to 3 on its first clean DRC run.
Four more facts from the same pass, all measured against real DRC on KiCad 10.0.3:
- KiCad **does** report `silk_overlap` between a footprint's own outline and its own reference field -
  a part's silk is not exempt from its own label.
- `silk_over_copper` is silk vs **pad mask apertures only**. Tracks and vias never triggered it across
  283 sampled violations, so a refdes over a bare track is not a DRC finding (still bad practice).
- `silk_edge_clearance` fires on actual clipping when `min_silk_clearance` is 0;
  `min_copper_edge_clearance` (0.5 mm here) does **not** apply to silk.
- `place_edit._parse_board_texts`' local->absolute transform
  (`ax = fx + lx*cos + ly*sin`, `ay = fy - lx*sin + ly*cos`) was verified exact on all 116 footprints
  across 0/90/180/-90 degrees. Trust it; do not re-derive the signs by hand.
Also: a **sandbox DRC** - copy `pcb + pro + dru + sch` to scratch - reproduces `drc_routed` exactly at
**3.4 s/run**. That is what makes "DRC is the only oracle" affordable when you have 111 candidate
edits to screen, and it carries zero risk to the live board. Do this instead of hoping a geometry
model agrees with the gate.
Caveat on the metric itself: `refdes_prox.py` compares a LOCAL offset magnitude against a RADIAL
pad-corner extent, so it is direction-blind and scores large rectangular parts generously (the ESP32
module's label sits 0.064 mm off the module outline yet scores `beyond = -3.17`). `offset_max` alone is
not a quality signal - read `beyond_extent` counts.
Corollary for `lib_refdes_norm.py`: its formula should be
`min(pad_top, silk_top) - margin - inked_h/2`. As written it ignores the footprint's own silk outline
and uses `size/2` for the half-height, so applying its targets verbatim to a placed board produced
**283 DRC warnings across 85 of 111 refs**. The targets are the right *starting point*, not the answer.

## 2026-07-29 [check_creepage][gates][ipc] `check_creepage` cannot express a COATED board, so it over-reports every outer-layer pair on any soldermasked design
`check_creepage.py` hardcodes exactly two rows of IPC-2221 Table 6-1 -
`CLEAR_EXTERNAL = [0.10, 0.10, 0.60, 0.60, ...]` and `CLEAR_INTERNAL` - and its own docstring names
them "Bare board", i.e. **B2 external UNCOATED** and B1 internal. There is no flag, no
`constraints.json` key, and no per-net way to say the board has soldermask. Every real board does.
The full table has seven rows, and the 51-100 V band spans **0.10 to 1.50 mm** depending on which one
applies (verified 2026-07-29 against ema-eda, Altair Pollex - which quotes 6.3.4 verbatim - and
protoexpress; all three agree):

| row | 51-100 V | 101-150 V | applies to |
|---|---|---|---|
| B1 | 0.10 | 0.20 | internal conductors |
| B2 | 0.60 | 0.60 | external conductors, UNCOATED, <= 3050 m |
| B3 | 1.50 | 3.20 | external conductors, uncoated, > 3050 m |
| **B4** | **0.13** | **0.40** | **external conductors with permanent polymer coating** (any elevation) |
| A5 | 0.13 | 0.40 | external conductors, conformal coating over the assembly |
| **A6** | **0.50** | **0.80** | **external component lead/termination, UNCOATED** |
| A7 | 0.13 | 0.40 | external lead/termination with conformal coating |

**B4 is 4.6x more permissive than B2 at 51-100 V.** Cost on lumina-carrier: the single reported item
`/poe/POE_TAP_A2 <-> /poe/LED_Y_A at 0.2031 mm` is trace-to-trace under soldermask, so its real
requirement is 0.13 mm and it **passes with +0.073 mm** - but it was reported as a 3x shortfall,
generated a 217-pair population, consumed two bounded fixer attempts, and produced one edit that had
to be applied, tested and retracted. That is the most expensive single tool gap this run hit.

**The subtlety that is easy to get wrong** (and that a first reading of this got wrong): exposed
copper does NOT fall back to B2. IPC-2221 6.3.4 says, verbatim: *"The assembly electrical clearances
of lands and leads that are not conformably coated require the electrical clearance requirements
stated in category A6."* B2/B3 describe a board with no coating **at all**. A masked board whose lands
are open by mask relief puts those lands on **A6 (0.50 mm at 51-100 V, 0.80 mm at 101-150 V)**. So the
adjudication is per-ITEM-TYPE, not per-layer: masked trace or tented via -> B4; exposed land -> A6;
inner layer -> B1. Note A6 is *stricter* than B2 in the 101-150 V band.
Fix proposal (recorded, not implemented): a `--coating {none,soldermask,conformal}` flag or a
`constraints.json` `"coating"` key, plus per-item-type row selection. Until then, **re-adjudicate every
outer-layer creepage finding by hand before spending any fix budget on it**, and record which row you
used - the interpretation of LPI mask as "permanent polymer coating" is industry-standard but is a
judgement the owner should get to see, not one a tool should make silently.

## 2026-07-29 [check_creepage][gates] the violation COUNT is not a violation count - it reports only the WORST pair per net pair, and hid 216 siblings
`check_creepage` emits one violation per (net_a, net_b, layer) at the minimum spacing. On
lumina-carrier the single reported item `/poe/POE_TAP_A2 -> /poe/LED_Y_A on F.Cu: 0.203 mm` was
**1 of 217 pairs under the 0.600 mm requirement** (17 of 36 LED_Y_A segments against 21 of 27 A2 F.Cu
segments, spanning 0.2031-0.5071 mm over roughly 10 mm of parallel run). A fixer that sizes a repair
from the one reported coordinate is sizing a 10 mm reroute from a point sample, and a reviewer reading
"15 creepage errors" is reading a number that understates the real defect count by more than an order
of magnitude. **Always re-sweep the whole net pair before believing, or acting on, a creepage count.**
Same shape as the sibling-masking note above, but worse: there the siblings appeared only after the
worst was fixed; here 216 of them were never reported at all.
Fix proposal for the script: emit every pair below the requirement, or at minimum carry a
`pairs_under_requirement` count and the distribution alongside the minimum.

## 2026-07-29 [check_current][gates] no bridge awareness: the script asks the fixer for a parallel path it cannot itself detect
`check_current`'s `undersized_track` fires per SEGMENT with the full rail current, and its own
remediation guidance tells the fixer to check whether a parallel same-net path carries some of it -
but the script has no connectivity graph, so it cannot answer its own question. On lumina-carrier all
five investigated segments turned out to be **cut edges (bridges) in their net's graph**, so each
really did carry the whole rail and the widths were genuine defects; but that had to be proven by
hand. ~40 lines (build the net graph from track endpoints, find bridges) would let the check label
each undersized segment `bridge: true|false`, which is the difference between "this is a real
bottleneck" and "this is one of four parallel feeds". Worth doing before anyone waives a width
finding on a parallelism assumption.

## 2026-07-29 [geometry][pads][python] roundrect pads carry 20 points, not 4 - a `sum/len` centroid silently drops them all
A shape-aware pad model that windows candidate pads by centroid-from-vertices (`sum(pts)/len(pts)`)
works for rect (4 points) and breaks for **roundrect**, whose corner arcs are emitted as ~20 points -
the average is pulled off the true centre enough to fall outside the search window, so every roundrect
pad vanishes from the model. Consequence measured on lumina-carrier: a "feasible" solve that placed a
via **inside U22 pin 11's pad**, caught only by a full-board pre-flight against real DRC rather than
by the solver's own model. Two corollaries: (a) window pads by their BOUNDING BOX, never by a
vertex-average centroid; (b) roundrect corner radius is load-bearing, not cosmetic - modelling
U22-11 (1.575 x 0.40, rratio 0.25) as a sharp rectangle understated its gap by ~0.041 mm and flipped
one item from "capped at 0.4624 mm" to "ceiling 0.5453 mm", i.e. from unfixable to nearly fixable.
Related: a circumscribed CIRCLE for a 1.90 x 2.50 rect pad hid a real 1.100 mm ceiling entirely.
This geometry (rotated rect + arc-approximated roundrect + oval stadium + circle + zone fills)
now exists three times over in `work/` scratch files on this board alone
(`p7/pad_gap.py`, `p8/tapcreep/capsule.py`, `p8/hvpwr/board_model.py`) because the first two run
argparse at import and cannot be imported. It belongs in `scripts/lib/`.

## 2026-07-29 [constraints][gates] two copies of constraints.json, two different answers - 61 vs 53 undersized_track
The playbook says sidecars resolve from the BOARD's directory from P5 onward, so
`kicad/constraints.json` is canonical - but `architecture/constraints.json` survives as the P2 record
and nothing keeps them in step. On lumina-carrier the architecture copy still carried
`V48_RAW current_a: 1.5` after the P8 correction to 1.0, and a check run against it reported
**61** `undersized_track` instead of **53**. Nothing warns you which file you loaded. Either delete
the architecture copy at P5 or (as done here) correct it and keep the original value in a
`_p2_original_current_a` field with the reason - annotation alone in a long `_comment` is too easy to
miss, and a stale current rating is how a wrong number gets quoted at P9.

## 2026-07-29 [board_init][rules_gen][dfm][gates] `board_init` writes `min_track_width: 0.1`, BELOW every JLC profile - so `drc_routed` 0/0 does not mean fabricable
`board_init.write_pro(pro_path, min_track: float = 0.1)` hard-codes 0.1 mm into
`design_settings.rules.min_track_width`. **Every** JLC profile in
`reference/jlc_capabilities.yaml` is coarser than that: 4-layer 1 oz is
`min_trace_width_mm: 0.1016` (4 mil), 2-layer is 0.127, 2 oz is 0.1524. `rules_gen` DOES emit the
right floor (`min_track_width: cap["min_trace_width_mm"]` plus an `aiee_track_width_floor` DRU rule),
but on lumina-carrier the `.kicad_dru` was hand-written for the 48 V rules and therefore contains
**zero** `aiee_*` rules, and `board_init` was re-run three times (`work/board_init{,2,3}.json`), so
the 0.1 default is what survived into the `.kicad_pro`.
Consequence measured on a board sitting at `drc_routed` **0 errors / 0 warnings**: `gate dfm` reports
**189 errors of "trace width 0.1000 mm below JLC minimum 0.1016 mm"** (136 F.Cu + 53 B.Cu) out of 194
total. The traces are legal against the board's own DRC floor and unmanufacturable against the fab's,
and the gap is **1.6 micrometres** - far too small to notice by eye in any report.
Two rules follow: (1) whenever you hand-write a `.kicad_dru`, START from the `rules_gen` output and
add to it - do not replace it, or you silently drop the fab floor, the annular floor and the
hole-size floors; (2) if `board_init` is ever re-run after `rules_gen`, re-run `rules_gen`
afterwards. Cheap standing check at P7 entry: assert
`.kicad_pro.min_track_width >= jlc_capabilities[profile].min_trace_width_mm`.

## 2026-07-29 [parts][silk] easyeda2kicad puts EVERY refdes at a blanket (0,-4.0) mm regardless of part size
Every footprint pulled by lib_pull carries its reference text 4.0 mm above the part origin - which on an
0603 (pad extent ~1.2 mm) puts the label ~3 mm clear of its own body and frequently nearer a NEIGHBOUR
than its own part, so a populated board cannot be read. Nothing catches it: KiCad's silk DRC checks
overlap/edge/copper, never proximity-to-owner, and check_silk only covers silk-over-pad. Measured on
lumina-carrier: median refdes offset 4.079 mm, and 100 of 116 labels more than 1 mm beyond their own
part's pad extent. It is a LIBRARY defect, inherited by every board built from the library, so fixing it
per-board is treating the symptom. New script `lib_refdes_norm.py --lib <dir>.pretty` re-derives each
offset from the footprint's own pad bbox (0603 -> -1.18, 0805 -> -1.44, 1210 -> -2.1, WROOM -> -10.15);
idempotent, text-surgery only, verified to keep all footprints parsing under kicad-cli 10.0.3 and fplib.
Run it after every lib_pull, BEFORE board_init - once footprints are placed the offsets are copied into
the .kicad_pcb and only place_edit move_text can fix them.

## 2026-07-29 [geometry][fixer] A min-over-endpoints segment distance reports a SHORT as clearance
`work/p7/pad_gap.py`'s `seg_seg_dist`, copied verbatim into `work/p8/tapcreep/capsule.py`, computes the
minimum over endpoint-to-segment distances. That is exact for DISJOINT segments but returns a positive
nearest-endpoint number for two segments that properly CROSS - so a dead short reads as clearance. A P8
fixer's optimiser found and exploited it, producing an "opens by +0.0037 mm" candidate that DRC rejected
with 2 x "Tracks crossing"; the fixer's own full-board pre-flight passed it too, because the pre-flight
used the same primitive. Fix is a `seg_cross()` test returning -1.0 on intersection before measuring
(reference implementation: `work/p8/hvpwr/board_model.py::gap_of`).
Scope, verified: the SKILL's checkers are unaffected - none of them use this primitive, and
check_creepage measures with shapely `.distance()`, which correctly yields 0 for intersecting geometry.
So the damage was wasted fixer iterations, not corrupted gate results, and any board that passes
drc_routed 0/0 provably has no crossings, which makes its disjoint-segment gaps exact.
Rule for fixers: ad-hoc geometry helpers must test intersection FIRST, or just use shapely (already a
dependency). And a model-based pre-flight gates cheap iteration - it never substitutes for the gate.

## 2026-07-29 [parts][silk] Refdes placement must clear the footprint's OWN silk, and layer names are unquoted in easyeda2kicad output
Two bugs in the first cut of lib_refdes_norm.py, both found only by DRC and by inspecting raw files:
(a) it reserved `size/2` for the text half-height, but KiCad's DRC measures the INKED box - glyph height
PLUS stroke thickness (measured: nominal 1.0 + thickness 0.15 -> 1.162 mm inked, while GetTextBox
reports 1.6965 mm). Correct reservation is `(size_h + thickness)/2`.
(b) it positioned labels clear of PADS only, ignoring each footprint's own silkscreen outline - which on
an 0603 sits at y=0.71 vs the pad edge at 0.45, so the label landed on the part's own outline. Applied
verbatim it produced 283 DRC silk warnings across 85 of 111 refdes. Correct form:
`min(pad_top, silk_top) - margin - inked_h/2`.
And the trap that hid (b): silk layer names are **QUOTED** in KiCad-10 stock footprints, `(layer
"F.SilkS")`, but **UNQUOTED** in the older format easyeda2kicad emits, `(layer F.SilkS)`. A regex
requiring quotes matched nothing, reported silk_top=None for every part, and produced a plausible wrong
answer with no error - the same silent-failure shape as the min-over-endpoints distance bug. Related:
KiCad 10 stock also uses a multi-line `(layer "F.CrtYd")` that line-oriented greps miss.

## 2026-07-30 [pipeline] There is no incremental board-from-netlist update, so adding ANY part after P5 costs all of P6+P7
board_init.py regenerates a .kicad_pcb from a netlist; place_edit's op vocabulary is move/rotate/flip/
lock/add_text/move_text and CANNOT add a footprint; no script anywhere calls AddFootprint or syncs a
board against a changed schematic. So a P4 rewind that adds even one passive discards the entire
placement and routing - there is no KiCad-GUI-style "update PCB from schematic". On lumina-carrier this
forced two genuine electrical fixes to be deferred to rev B rather than applied: an HF input ceramic on
the 3.3 V buck (which had one 22 uF at 9.2 mm / 8.378 nH and no ceramic, feeding the MCU, the W5500 and
every daughter) and PESD clamping on +3V3 / the LED nets. Plan for it: get decoupling and protection
parts into the schematic BEFORE P5, because after that the choice is a full re-route or a deferral.

## 2026-07-30 [gates][dfm] drc_routed 0/0 does NOT imply fabricable - board_init's track floor is below every JLC profile
board_init writes `min_track_width: 0.1` mm, but JLC's minimum is 0.1016 mm (4 mil), so a board can route
to 0.1000 mm tracks, pass drc_routed at 0 errors AND 0 warnings, and then fail the P9 dfm gate - on
lumina-carrier, 189 of 194 dfm errors were "trace width 0.1000 mm below minimum 0.1016 mm", a 1.6 um gap
repeated 189 times. It is worse when the board carries a HAND-WRITTEN .kicad_dru (as this one does for
its 0.635 mm HV rule), because that file then contains none of rules_gen's fab floors at all. Fix at P5:
set the floor to the fab profile's minimum, and if you hand-write a .kicad_dru, port rules_gen's floors
into it rather than replacing them.

## 2026-07-30 [ordering][impedance] insideCuprumThickness was hardcoded to 1 oz, fabricating a different stackup than the one designed
order_submit.build_pcb_param set `insideCuprumThickness: "1"` on EVERY 4+ layer order, copied from the
JLC create-example. JLC's standard 4-layer inner copper is 0.5 oz. Two consequences, the second serious:
(a) it silently bought a premium - measured `insideCuprumThicknessFee` $17.07 on lumina-carrier, 48% of
the whole PCB cost, which is also why order_quote read 3.6x low against the real API price; and (b) it
would have FABRICATED A DIFFERENT STACKUP than the impedance was solved against. lumina-carrier targets
100 ohm differential MDI on JLC04161H-3313, whose inner layers are 17.5 um / 0.5 oz; 35 um inner copper
moves the reference spacing and the controlled impedance with it - on a board that is 4-layer solely to
hold that 100 ohm. Nothing downstream would have caught it: the gates check geometry against the stackup
file, never against what the order actually asks the fab to build. Now derives from
spec.inner_copper_weight_oz, defaulting to 0.5. Rule: any pcbParam value taken from a vendor EXAMPLE
rather than from the board's own stackup is a fabrication defect waiting to happen.

## 2026-07-30 [ordering] JLC Open API `pcb/create` refuses 4-layer boards with an unclassified `code 2`, while `calculate` accepts them
Three live attempts on lumina-carrier (4L, 100x80, qty 10, US, HKTHZXR-RMB) all returned HTTP 200 with
`{"code": 2, "message": "unknown_error"}` - traces 4e0f08d4…, f90769b3…, b1eba7f4… - differing only in
`insideCuprumThickness` ('1' / '0.5' / absent). Control: pd-trigger (2L) created successfully as
W2026073002475378 on the SAME account, API, shippingMethod and country, with a byte-identical payload
shape and byte-identical values for every shared pcbParam field. `calculate` priced the 4L board
correctly at every variant; only `create` refuses. So the cause is not the payload, the ship method, the
freight, the confirm token or the account scope - the remaining differences are `layer` (2 vs 4) and
board size. Treat 4-layer API ordering as UNAVAILABLE until JLC support explains code 2; the manual cart
works and the fab package is independently JLC-audited.
Two related tooling gaps this exposed: (a) jlcapi.classify() has no rule for code 2 and REMEDIATION no
entry, so an unclassified business error yields no guidance; (b) the created-latch arms only on SUCCESS,
so it guards a deliberate second order but not an ambiguous FIRST one - the case that actually risks
double-buying. And there is no order list/search endpoint at all (`order/detail` and `wip/get` both
require a batchNum you must already hold), so after an ambiguous create the portal is the only oracle.

## 2026-07-30 [stackup][ordering] reference/stackups.yaml's JLC04161H-3313 IS NOT A REAL JLC STACKUP
Verified live: `getImpedanceTemplateSettingList` for 4L / 1.6 mm / 1 oz outer / 0.5 oz inner returns
exactly three templates - `JLC04161H-自定义` (20220811093551), `JLC04161H-1080B` (202601040426384154,
L1-L2 0.2444 mm, core 1.065 mm) and `JLC04161H-7628G` (202607130748059522, L1-L2 0.5124 mm, core
0.500 mm) - and **no -3313**. Swept plateType 0-3 and delamination 0-3; only plateType 1 returns data
and it always returns the same three. All three carry `enableFlag: false`.
This matters because stackups.yaml's -3313 entry (prepreg 0.2104 mm, er 4.05) is the ONLY 4-layer entry
publishing a 100 ohm differential profile, so it is the reason lumina-carrier is 4-layer at all and it
produced the routed MDI geometry 0.260 / 0.210 / 0.470 mm. Measured against the real templates at that
same geometry: 1080B = 105.5 ohm (+5.5%), 7628G = 127.6 ohm (+27.6%), vs 99.9 ohm on the phantom.
1080B is acceptable for 100BASE-TX (2.7% reflection, spec allows +-15% on the cable) but it is a
DIFFERENT BOARD than the one solved for, and nothing in the pipeline would have said so.
Fourth instance on this board of the same failure mode - after the hardcoded 1 oz inner copper, the
`## Chosen` heading miss, and `impedanceFlag: "no"` on an impedance-controlled design - where the ORDER
asks the fab for a different board than the one designed and verified. Gates check the design against
its own stackup file; nothing checks the stackup file against what the fab actually sells.

## 2026-08-06 [ordering] order_track.py sees WEB-created orders fine - `order/detail` keys only on batchNum, not on how the order was created
lumina-carrier's 4-layer order failed via `pcb/create` (code 2, see the entry above) and was placed
manually through the JLC cart instead, so the workspace never captured a batchNum the way pd-trigger's
API-created order did. Owner supplied the web order's batch number (W2026073100331078) this session;
`order_track.py --workspace boards/lumina-carrier --batch W2026073100331078` returned a normal `pass`
payload on the first try - status Shipped, total_money 15.72, same shape as pd-trigger's API-created
order. No distinction in the response between an order the API created and one placed by hand in the
browser: `pcb/order/detail` (and by extension `pcb/wip/get`) is keyed purely on batchNum/orderUUID, which
the cart UI surfaces to the human the same way batchNum is returned from `create`. Recorded the number
into `fab/order.json.order_number` (no `api.order` block, since the API never created it) - order_track's
`_batch_from_order_json` already falls back to `order_number` when `api.order.batchNum` is absent, so no
code change was needed. Answers the open question from S12/T0: a 4-layer web order is trackable exactly
like an API order, once you have its batch number in hand.
Rule: validate any impedance-controlled stackup against the vendor's live template list BEFORE solving
geometry against it, not at order time.

## 2026-08-06 [kicad-sch-api][python] `Schematic.save()` SILENTLY GUTS lib_symbols for any symbol its cache cannot resolve
kicad-sch-api 0.5.6 re-serialises the whole `(lib_symbols ...)` block on save from its GLOBAL symbol
cache, which never reads `sym-lib-table` (see the 2026-07-28 `--pins` entry). Load and save
`boards/pd-trigger/kicad/pd-trigger.kicad_sch` as-is and the file goes 8879 -> 4359 lines: every
`aiee:` definition disappears, with no error, no warning and exit 0. The schematic still parses, so
nothing downstream notices until KiCad opens it. Register the project library FIRST -
`ksa.get_symbol_cache().add_library_path(<lib>/aiee.kicad_sym)` before `Schematic.load` - and the
round trip is faithful (8879 -> 8879, 92 cosmetic `(at x y 0)` -> `(at x y 0.0000)` diffs only,
measured on both pd-trigger and the s7 fixtures). Rule for ANY ksa write path: register the project
libs, then assert the lib_symbols NAME SET is unchanged after save before trusting the file
(`schem_refdes.write_placements` does exactly this and raises otherwise). The T3 plan called for
placement "via kicad-sch-api"; this is why the READ side is a direct s-expression parse instead - the
schematic's own embedded lib_symbols needs no library resolution at all.

## 2026-08-06 [kicad-sch-api][silk][python] ksa places instance property positions with the WRONG Y SIGN, mirroring every field to the far side of its part
Library symbol coordinates are y-UP, page coordinates are y-DOWN, so KiCad maps a library offset
`ly` to `page_y = py - ly`. kicad-sch-api 0.5.6 ADDS it (`page_y = py + ly`), so every Reference and
Value lands mirrored through the symbol origin. Measured on the s7 blinky2 fixture: C1 at page
(152.40, 240.03), Device:C Reference library offset (0.635, +2.54) -> written at page y 242.57
(BELOW the cap) while its pin at library (0, +3.81) is wired at page y 236.22 (ABOVE) - the pin
proves the sign. Net effect on a generated sheet: reference below / value above, the reverse of
KiCad's convention, and on a dense sheet the mirrored fields land on wires, labels and neighbours
(27 overlaps on blinky2 counted against symbol bodies, pin-number bands, wires and labels).
`schem_refdes.py` re-places both fields from a class table and reports what it cannot clear. Note
the fields are cosmetic - ERC stays 0 and the exported netlist is byte-identical either way - so
nothing in the pipeline catches this; it is a readability defect only a human or this script sees.

## 2026-08-06 [easyeda2kicad][drc][parts] The whole known-bad pull set is 16 DRC violations, and one measured recipe takes it to 0 - but only if filled graphics are left alone
A live pull of the four worst-known parts (C14663 0603, C2286 LED, C7421520 3-pos DIP switch,
C5184243 GCT USB-C) DRCs at **16 violations = 4 errors + 12 warnings** on a scratch board
(annular_width x2, clearance x2, padstack x2, silk_overlap x8, silk_over_copper x2) - the exact
numbers the three shipped boards' `EDITS.md` recorded by hand. `fpfix.py` now applies the same
recipe at pull time and measures **0** after. Three things the generalisation turns on:
(a) narrowing is arithmetic, not judgement: a stroke clears copper by `d_centerline - w/2`, so the
widest legal width is `w_max = 2*(d - min_gap)`, floored to the 0.05 grid and never below JLC's
0.15 mm line width. Violators sharing an ORIGINAL width narrow together, which reproduces the
approved hand edit exactly (C0603 0.25 -> 0.20, gaps 0.135 -> 0.160; LED glyph 0.25 -> 0.15, gaps
0.105/0.135 -> 0.155/0.185).
(b) a FILLED graphic must be exempt from the "promote sub-0.15 strokes so they print" rule: its ink
comes from the fill, and widening the stroke grows the printed shape. The DIP switch's three solid
slider indicators are `fp_poly` at stroke 0 - promoting them would have silently redrawn the part.
(c) `Path("SW-SMD_6P-...-LS9.3-BL").stem` returns `...-LS9`: footprint names contain dots, so stem
strips a fake extension and the footprint is skipped with no error. Match on the literal
`.kicad_mod` suffix instead.
Unchanged conclusion from the 2026-07-28 CORRECTION: verify silk claims with `kc.py drc`, never with
a geometry script alone.

## 2026-08-06 [schematic][placement] On a generated sheet the space above and below a symbol is NOT free - the corners are
The S1/S7 generator pattern stubs a wire and a local label at EVERY pin, so the bands directly above
and below a block symbol are crossed by a wire every 2.54 mm for the symbol's whole width: on
blinky2 the STM32's centred-above and centred-below candidates, and every 1.27 mm slide along them,
all collide. The free area is DIAGONALLY outside the pin bounding box corners, where no stub runs -
which is where a human puts the label too. A field placer that only offers above/below/left/right
will report false residue on any real sheet; add corner rings (and for power symbols, lateral
offsets - two rails 5.08 mm apart cannot both carry a centred `PWR_FLAG`, whose text is 7.5 mm
wide). Second trap in the same area: KiCad prints each pin NUMBER alongside its pin line, outside
the body and absent from the library graphics, so a field cleared against pin lines alone still
lands on printed text - model the pin as a band (0.7 mm) not a line.

## 2026-08-06 [stackup][jlcapi][ordering] JLC's impedance-template list CHURNS - and the endpoint lies quietly when you under-specify it
T1 re-probed `pcb/getImpedanceTemplateSettingList` (read-only, free) to rebuild
`reference/stackups.yaml` from what JLC actually sells. Three facts worth keeping:
1. **The list changes week to week.** For 4L / 1.6 mm / 1 oz outer / 0.5 oz inner, 2026-07-30
   returned THREE templates and 2026-08-06 returns TWO: `JLC04161H-7628G`
   (202607130748059522) was withdrawn in between, same account, same request. So "verified
   live" has a shelf life measured in days: re-probe before solving impedance geometry, and
   record the date next to the numbers (stackups.yaml now does, per entry).
2. **`insideCuprumThickness` is REQUIRED even where it is meaningless.** Omit it and the API
   answers `{"code": 3, "message": "param_empty"}` - not an empty list. A 2-layer probe
   without it therefore looks identical to "no 2L templates exist". WITH it, 2L returns a
   legitimate empty list at both 1 oz and 2 oz: JLC sells no impedance-controlled 2-layer
   stackup, which is a real (negative) answer worth recording.
3. **Inner copper weight selects a different template FAMILY**, not a variant: 1 oz inner
   returns `JLC041611-7628E/J/K/L`, 0.5 oz inner returns `JLC04161H-1080B`, 2 oz outer
   returns `JLC04162H-7628A`. Ordering a different `insideCuprumThickness` than the stackup
   was solved for silently buys a different lamination (see the 2026-07-30 entry).
Also: `enableFlag: false` on EVERY template of every family, so it does not mean "not
orderable" - do not gate on it. The API returns materials + thicknesses but NO dielectric
constant, so er stays an assumption (stackups.yaml flags `epsilon_r_assumed: true`; V12).
Re-probe recipe: `jlcapi.session_from_env().post_json("/overseas/openapi/pcb/getImpedanceTemplateSettingList",
{"stencilLayer": 4, "stencilPly": 1.6, "cuprumThickness": "1", "insideCuprumThickness": "0.5", "plateType": 1})`.

## 2026-08-06 [fab_export][ordering][dfm] The exact volatile set in a KiCad fab package - 5 line forms + 2 JSON keys
Implementing T1's normalized design hash (`lib/fabhash.py`) needed the complete list of what
KiCad restamps on every export. Measured against real 10.0.3 output, it is exactly:
gerber `%TF.CreationDate,..*%`, `%TF.GenerationSoftware,..*%`, `G04 Created by KiCad (PCBNEW ..) date ..*`;
Excellon `; DRILL file KiCad .. date ..`, `; #@! TF.CreationDate,..`, `; #@! TF.GenerationSoftware,..`;
and in the `.gbrjob` the JSON keys `Header.CreationDate` + `Header.GenerationSoftware`.
The `.gbrjob` is the trap: `GenerationSoftware` is an OBJECT spanning four lines, so a
line-filter normalizer silently leaves the version behind and the "design hash" drifts on a
KiCad upgrade. Parse that file as JSON and drop the keys recursively.
`%TF.ProjectId` is NOT volatile (stable per project) - keep it hashed, it catches a board
exported from the wrong project. Verified end to end: two real `fab_export` runs of an
unchanged golden board produce different zip sha256 and IDENTICAL design hashes, while moving
one track coordinate changes the design hash (tests/test_fab.py::test_design_hash_*).

## 2026-08-06 [board_init][rules_gen][gates] Raising the .kicad_pro floors to the fab profile at ERROR costs the corpus nothing
The fear that stopped this fix earlier ("stricter floors will fail existing boards") is
unfounded, measured: with `min_track_width` at the profile value, `min_hole_to_hole` at
0.5 mm and both checks pinned to `error` (plus clearance / annular / hole_clearance /
copper_edge_clearance / drill_out_of_range), `board_init` on golden usbbuck4 still
self-checks at parity 0 / setup_violations 0, and all three goldens stay DRC-clean.
lumina-carrier measured the same thing from the other side: its tightest drill pair is
0.5016 mm across 440 drills.
The reusable root cause is not the numbers, it is that **two different writers owned the same
block** - `board_init.write_pro` hard-coded floors while `rules_gen.update_pro` derived them
from `jlc_capabilities.yaml`, so whichever ran LAST won and re-running board_init silently
downgraded the board. One source (`lib/fabfloors.py`) + `check_pro()` asserted by both
writers is what actually fixes it; the severities are stated explicitly so the project never
inherits a KiCad default (`hole_to_hole` defaults to *warning*).

## 2026-08-06 [tests][skill] A live-run fix that does not update its test leaves the suite RED and nobody notices
`test_build_pcb_param_inner_copper_by_layer_count` asserted `insideCuprumThickness == "1"`.
The 2026-07-30 lumina-carrier run FIXED that hardcoded 1 oz inner copper (it was buying a
premium and fabricating a stackup the impedance was not solved against) but did not update
the test, so `check.cmd` was already failing when T1 started - and the whole point of the
green-suite session protocol is that a red suite is a stop sign, not background noise.
Rule: when a live run edits a script's constant, `grep tests/ for the OLD value` in the same
change. And a session that opens on a red suite must say so before adding to it.

## 2026-08-06 [tests][freerouting][skill] Wave-1 parallel sessions make the route_auto completion assert flaky - re-run it ALONE before believing it
`test_route_auto_full_flow` asserts `completion >= 0.9` on blinky2. It failed at **0.8182** in a
full-suite run while three other v2 sessions (T2/T3/T4) were running their own suites against the
SAME working tree, and passed minutes later in isolation with nothing changed. Freerouting is
time-bounded (`-mp` passes plus route_auto's wedge timeout), so CPU contention ends a pass early
and the failure reads exactly like a routing regression.
Two consequences for the v2 protocol: (a) a tree-wide pass count from a parallel wave is not
attributable to one session - report YOUR files' counts and say the full number is shared;
(b) T5's stage bench must keep wall-clock and completion-ratio metrics out of the deterministic
class, or run the bench alone. Standing rule: re-run a failing smoke test alone before treating it
as a regression, and never "fix" a threshold from a contended run.

## 2026-08-06 [bench][kicad-cli][tests] A frozen KiCad fixture is the file PLUS its stem-matched project files
T5's first P7 bench run reported **122 DRC errors on the shipped pd-trigger board** (114
clearance + 8 copper_edge_clearance) - a board that shipped DRC 0/0 - and 60 ERC warnings on
its schematic. Cause: the fixture copy was renamed (`routed.kicad_pcb`), and kicad-cli resolves
`<stem>.kicad_pro` / `<stem>.kicad_dru` as SIBLINGS BY STEM - netclass clearances, custom
rules and the severity map all live there, so the orphaned board was judged under KiCad
defaults. With per-role dirs keeping the ORIGINAL stem (`route/pd-trigger.kicad_pcb` +
`.kicad_pro` + `.kicad_dru`) the same board scores 0/0 and the sheet ERCs clean. The golden
boards never showed this because they are referenced IN PLACE next to their project files.
Rule: a KiCad artifact fixture = artifact + stem-matched project files, all sha-pinned;
pure-geometry consumers (geom.py, the P8 checks) are exempt - they never read the project.

## 2026-08-06 [bench][schematic][geometry] Label-vs-symbol-body overlap is a pin-line artifact - measure label-vs-label only
benchlib's first `label_collisions` metric counted label text boxes against symbol bodies too.
Measured on the SHIPPED pd-trigger sheet: **50 of 50 hits were a local label grazing the pin
LINE of the very pin it names** (`Sheet.body()` includes pin segments; a stub label sits at
the wire end by construction) - zero label-label overlaps. The dirty s7 blinky2 fixture shows
the real signal the other way: 11 genuine label-label text overlaps. So the v0 metric counts
ONLY label/global/hier/text box PAIRS; field-vs-body coverage already exists in the
schem_refdes audit (which models pin-number bands properly instead of raw pin lines).

## 2026-08-06 [git][gates][windows] `git status --porcelain` collapses an untracked directory to one `dir/` line - scoped staging must use `-uall`
T6 gate.py commit scoping: the workspace filter matched porcelain paths against the
`boards/<name>/` prefix, but for a NEW workspace porcelain emits a single collapsed
`?? boards/` line, so the "inside the workspace" set came up empty and the scoped commit
refused with "nothing to commit inside the workspace" while the files sat right there.
Silent-failure shape: no error, just a wrong empty set. `git status --porcelain -uall`
lists every untracked FILE individually and the prefix filter works. Any code that
partitions porcelain output by path prefix (scoped staging, litter assertions, workspace
diffs) needs `-uall` or a directory-aware matcher.

## 2026-08-06 [kicad-sch-api][kicad][python] ksa mirrors PIN POSITIONS at 90/270; KiCad rotates FIRST then mirrors - and ERC cannot see swapped pins
Two transform facts settled by the T6 rotmirror fixture (kicad-cli 10.0.3 ERC + netlist
oracle, tests/fixtures/sch/rotmirror), correcting the 2026-07-28 "inward stubs" entry:
(a) The V19 inward-stub defect was NEVER stub_dir's sign - stub_dir's composition matches
real KiCad at every rotation. kicad-sch-api 0.5.6 `get_component_pin_position` rotates the
wrong way at 90/270, returning the true position MIRRORED through the anchor (R(-t) vs
R(t); at right angles the correction is a point reflection). ERC-measured: rot-90 Device:R
pin1 (lib (0,+3.81)) is truly at anchor x-3.81; ksa says x+3.81. schlib.pin_pos now
reflects ksa's answer back through the anchor for rot 90/270, so generators may rotate
freely. (b) KiCad composes instance transforms ROTATION FIRST, THEN mirror (page frame).
schem_refdes.to_page originally mirrored first - identical results for mirror-only or
rotation-only instances, but a rot90+mirror part gets its two pins SWAPPED. ERC is blind
to this (the pin position SET is unchanged - both wires still land on pins); only the
exported netlist shows the wrong memberships. Any transform fixture must therefore assert
per-pin NET assignment, not just ERC 0/0.
## 2026-08-06 [gerbonara][gerber][dfm] gerblib LayerGeom.pads holds PRIMITIVE FRAGMENTS, not one polygon per flash - a KiCad RoundRect aperture is 9 of them
T6 P9-3 (check_pad_tented): _flash_polys expands each Flash via to_primitives(), and
KiCad's RoundRect aperture MACRO decomposes into 9 primitives (1 box polygon + 4 corner
circles + 4 edge rects), so ONE paste aperture contributed 9 entries to lg.pads and the
first tented-pad implementation reported the same pad 9 times. Area/union checks never
noticed (they union everything first), which is why this stayed invisible since S12.
Any NEW check that iterates lg.pads per-aperture (counting, per-pad predicates) must
group by connected component first - LayerGeom.components() is the honest unit.
