# LEARNINGS

Append-only, non-obvious gotchas. Recall by tag/keyword before touching an area.
Entries sourced from prior attempts are marked; re-verify at first use here.

## Tags
[windows] [kicad] [kicad-cli] [ipc] [swig] [freerouting] [easyeda2kicad] [python] [prior-attempts] [geometry] [shapely] [parts] [datasheet] [gerber] [gerbonara] [dfm] [jlc] [fab] [skill] [git] [latex]

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
