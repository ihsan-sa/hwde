# LEARNINGS

Append-only, non-obvious gotchas. Recall by tag/keyword before touching an area.
Entries sourced from prior attempts are marked; re-verify at first use here.

## Tags
[windows] [kicad] [kicad-cli] [ipc] [swig] [freerouting] [easyeda2kicad] [python] [prior-attempts] [geometry] [shapely] [parts] [datasheet] [gerber] [gerbonara] [dfm] [jlc] [fab]

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
