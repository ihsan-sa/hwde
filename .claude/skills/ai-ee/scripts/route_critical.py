"""route_critical - script-driven routing of CRITICAL nets before Freerouting
(S11, SPEC P7.1).

Wraps the vendored KiCadRoutingTools (KRT, tools/krt via env.find_krt) to route
the nets whose geometry is load-bearing BEFORE route_auto hands the remainder
to Freerouting: differential pairs (route_diff.py), RF single-ended nets at
impedance width, and high-current power nets at IPC-2152 width (route.py).
Pre-routed copper survives Freerouting by construction: the DSN exporter emits
it as guide wires which Freerouting protects (see route_auto.py).

Critical-net sources (constraints.json, sidecar default like place_metrics):
  diff pairs  constraints["diff_pairs"] [{p, n, gap_mm?, impedance_ohm?,
              max_skew_mm?, max_uncoupled_mm?}] PLUS auto-discovery over the
              high_speed net names via check_diffpair.discover_pairs - the S5
              checker's own suffix rules (_P/_N, DP/DM, D+/D-), so the pipeline
              and the checker can never pair differently.
  rf          constraints["rf"] [{net, impedance_ohm}] plus high_speed entries
              carrying impedance_ohm that are not half of a diff pair; routed
              single-ended at solve_width() impedance width. Via FENCING is
              NOT done here: each routed RF fact carries a fence_handoff note
              (stitch_vias.py --fence-net <net> owns the fence).
  power       constraints["power"] [{net, current_a, dt_c?}]; width = IPC-2152
              minimum (check_current.required_width_mm, rules_gen's helper)
              * 1.5 margin, clamped >= 0.3 mm.

KRT facts this adapter encodes (all machine-verified against KRT 0.19.0):
  * KRT scripts are invoked as subprocesses of THIS python with
    cwd=<plugins dir> (they sys.path-insert relative dirs) and args as a list
    (never a shell - Git Bash mangles "/USB_DP" into a path). The final
    "JSON_SUMMARY: {...}" stdout line (the LAST one - a reconcile pass may
    print a scoped second summary) is the machine-readable outcome; KRT's own
    exit code / internal DRC are advisory only.
  * --no-fix-drc-settings is ALWAYS passed (without it KRT rewrites the
    .kicad_pro DRC floors - prior-attempt fact), so routed copper must grade
    clean against the board's EXISTING settings. The adapter therefore passes
    explicit floors read from the .kicad_pro (KiCad stock defaults when
    absent: clearance 0.2, via 0.5/0.3, copper-to-edge 0.5) as --clearance /
    --via-size / --via-drill / --board-edge-clearance, plus a --fab-overrides
    file pinning the same values so KRT's fab-tier escalation can never route
    below what kicad-cli will grade (S11: its 0.3/0.15 escalation via drew
    annular/hole/diameter DRC errors on a stock board).
  * Every KRT call routes staged -> FRESH output file; on success the output
    replaces the staged board (which keeps its .kicad_pro sidecar - KRT reads
    netclasses from the INPUT's sibling, and boards must never travel without
    their project file).
  * DP/DM suffixes ARE in KRT's pair detector (net_queries.extract_diff_pair_base
    rule r'^(.*?)D([PMN])$'), verified live on /USB_DP + /USB_DM.
  * KRT 0.19.0 limitation + workaround: a 2-terminal pair where one net has an
    extra stub pad (USB pull-up R, series tap) MISPAIRS its route terminals
    (connectivity.get_net_endpoints Case 3 makes the stub pad a "source" and
    the ref-midpoint target selector then prefers a degenerate cross pairing)
    and the pair dies with "no-escape-path" at both ends. The adapter detaches
    such stub pads - pads outside every matched terminal per
    check_diffpair.matched_terminals - from their net in the KRT INPUT text,
    routes, then restores the net node in the OUTPUT (KRT's writer preserves
    footprint text byte-identical; the restore is verified before the board is
    accepted). The stub itself is ordinary Freerouting work later.
  * Diff-pair width ladder: the impedance-derived width is tried first; if the
    pair defers/fails (fine-pitch escape), one fallback rung at 0.2 mm width
    retries. --grid-step 0.05 (default here) matters: 0.1 quantizes away the
    tap corridors of 0.5 mm-pitch parts (S11-verified: +3V3 15/16 pads at 0.1,
    21/21 at 0.05).

Layer discipline: diff pairs and RF prefer the outer layer over the first
inner reference plane (F.Cu on the 4-layer stack, cost 1) with the far outer
layer allowed at cost 3 (power: cost 2); inner layers are excluded and KRT
marks them as forbidden obstacles for via spans. Actual layers used are
re-read from the output (geom) and reported as facts.

Verification before the board is touched: kicad-cli DRC (kc.run_drc,
--all-track-errors) runs on the staged board BEFORE and AFTER; any violation
type whose count increased -> exit 2, original board untouched
(unconnected_items legitimately DROPS). The S5 diff-pair check
(check_diffpair.check_pair) then runs in-process on the routed pairs; its
violations gate status like the router's own.

Determinism: KRT's routing is deterministic for identical inputs, but it
stamps fresh uuid4s on every track/via, so byte-identical reruns are
impossible. Determinism here (and in tests) = same nets routed + same DRC
outcome, never same bytes.

Contract (SPEC section 6):
  route_critical.py --pcb B.kicad_pcb [--constraints c.json]
      [--only diff|power|rf] [--plan plan.json] [--grid-step MM]
      [--timeout-s S] [--work-dir DIR] [--out-report r.json]
  exit 0 = every critical item routed + DRC gained nothing + diff-pair check
  passes; 1 = some item failed or a check flags (board still updated with
  what succeeded - only reachable when DRC gained no new errors); 2 = error
  (original board untouched).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import check_current  # noqa: E402  (required_width_mm - rules_gen's helper)
import check_diffpair  # noqa: E402  (discover_pairs / matched_terminals / check_pair)
import checklib  # noqa: E402
import env  # noqa: E402
import geom  # noqa: E402
import impedance as imp  # noqa: E402
import kc  # noqa: E402
import route_edit  # noqa: E402  (width normalization ops)
import routelib  # noqa: E402  (fresh_work_dir / swap_in)
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "route_critical"
DEFAULT_ORDER = ("diff", "rf", "power")
POWER_MARGIN = 1.5          # IPC-2152 minimum * this
POWER_WIDTH_FLOOR = 0.3     # mm - never route a declared power net thinner
FALLBACK_PAIR_WIDTH = 0.2   # mm - diff ladder rung 2 (fine-pitch escape)
BASE_TRACK_WIDTH = 0.2      # mm - KRT base width (power-tap neckdown target)
KRT_REMEDIATION = (
    "KiCadRoutingTools not found (env.find_krt). Re-fetch: download "
    "https://github.com/drandyhaas/KiCadRoutingTools/releases/download/"
    "v0.19.0/KiCadRoutingTools-0.19.0.zip, unzip under tools/krt/, and copy "
    "grid_router-windows-x86_64.pyd to plugins/rust_router/grid_router.pyd "
    "(see tools/krt/PROVENANCE.txt). AIEE_KRT_DIR overrides.")

# KiCad stock board-setup floors, used when the .kicad_pro carries no value.
KICAD_DEFAULTS = {
    "clearance": 0.2,        # Default netclass clearance
    "track_width": 0.2,      # rules.min_track_width
    "via_diameter": 0.5,     # board setup min via diameter
    "via_drill": 0.3,        # board setup min through hole
    "edge_clearance": 0.5,   # board setup copper-to-edge
}


# ------------------------------------------------------------ pure helpers

def parse_summary(stdout: str) -> dict | None:
    """The LAST 'JSON_SUMMARY: {...}' line of a KRT run, parsed."""
    last = None
    for line in stdout.splitlines():
        if line.startswith("JSON_SUMMARY:"):
            last = line[len("JSON_SUMMARY:"):].strip()
    if last is None:
        return None
    try:
        return json.loads(last)
    except json.JSONDecodeError:
        return None


def power_width_mm(current_a: float, dt_c: float = 10.0,
                   cu_mm: float = 0.035) -> float:
    """Routing width for a power net: IPC-2152 minimum * margin, floored."""
    need = check_current.required_width_mm(float(current_a), dt_c, cu_mm)
    return round(max(need * POWER_MARGIN, POWER_WIDTH_FLOOR), 4)


def default_impedance(p: str, n: str) -> int:
    """rules_gen's default: USB pairs 90 ohm differential, else 100."""
    return 90 if "USB" in (p + n).upper() else 100


def diff_specs(constraints: dict, board_nets) -> list[dict]:
    """Explicit constraints['diff_pairs'] entries PLUS S5-discovered pairs
    over the high_speed net names. Returns [{p, n, impedance_ohm, ...}]."""
    hs = constraints.get("high_speed", []) or []
    imp_of = {e.get("net"): e.get("impedance_ohm") for e in hs}
    specs: list[dict] = []
    used: set[str] = set()
    for entry in constraints.get("diff_pairs", []) or []:
        p, n = entry.get("p"), entry.get("n")
        if not p or not n:
            continue
        spec = dict(entry)
        spec.setdefault("impedance_ohm",
                        imp_of.get(p) or imp_of.get(n) or default_impedance(p, n))
        specs.append(spec)
        used.update((p, n))
    hs_nets = [e.get("net") for e in hs if e.get("net")]
    for p, n in check_diffpair.discover_pairs(hs_nets):
        if p in used or n in used:
            continue
        z = imp_of.get(p) or imp_of.get(n) or default_impedance(p, n)
        specs.append({"p": p, "n": n, "impedance_ohm": z})
        used.update((p, n))
    del board_nets  # membership is judged (with a warning) at route time
    return specs


def rf_specs(constraints: dict, pair_nets: set[str]) -> list[dict]:
    """constraints['rf'] plus high_speed entries with impedance_ohm that are
    not half of a diff pair."""
    specs: list[dict] = []
    seen: set[str] = set()
    for entry in constraints.get("rf", []) or []:
        net = entry.get("net")
        if net and net not in pair_nets and net not in seen:
            specs.append({"net": net,
                          "impedance_ohm": entry.get("impedance_ohm", 50)})
            seen.add(net)
    for entry in constraints.get("high_speed", []) or []:
        net, z = entry.get("net"), entry.get("impedance_ohm")
        if net and z and net not in pair_nets and net not in seen:
            specs.append({"net": net, "impedance_ohm": z})
            seen.add(net)
    return specs


def power_specs(constraints: dict, cu_mm: float = 0.035) -> list[dict]:
    specs = []
    for entry in constraints.get("power", []) or []:
        net = entry.get("net")
        if not net or entry.get("current_a") is None:
            continue
        cur = float(entry["current_a"])
        dt = float(entry.get("dt_c", 10.0))
        ipc = round(check_current.required_width_mm(cur, dt, cu_mm), 4)
        specs.append({"net": net, "current_a": cur, "dt_c": dt,
                      "ipc_min_mm": ipc,
                      "width_mm": power_width_mm(cur, dt, cu_mm)})
    return specs


def plan_order(only: str | None, plan: dict | None) -> list[str]:
    """Item-kind order: --plan {'order': [...]} overrides, --only filters."""
    order = list(DEFAULT_ORDER)
    if plan:
        want = plan.get("order")
        if not (isinstance(want, list) and want
                and all(k in DEFAULT_ORDER for k in want)):
            raise CheckError(f"plan 'order' must be a non-empty subset of "
                             f"{list(DEFAULT_ORDER)}, got {want!r}")
        order = list(dict.fromkeys(want))
    if only:
        order = [k for k in order if k == only]
    return order


def grading_floors(pro_path: Path | None) -> dict:
    """The floors kicad-cli DRC will grade at, from the .kicad_pro (KiCad
    stock defaults when a value is absent). clearance = the LOOSEST netclass
    (a --clearance ceiling at that value caps nothing that matters, but pins
    the no-netclass fallback base to the graded default)."""
    floors = dict(KICAD_DEFAULTS)
    if pro_path is None or not Path(pro_path).is_file():
        return floors
    try:
        proj = json.loads(Path(pro_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return floors
    rules = proj.get("board", {}).get("design_settings", {}).get("rules", {})
    if rules.get("min_track_width"):
        floors["track_width"] = float(rules["min_track_width"])
    if rules.get("min_copper_to_edge"):
        floors["edge_clearance"] = float(rules["min_copper_to_edge"])
    if rules.get("min_via_diameter"):
        floors["via_diameter"] = float(rules["min_via_diameter"])
    if rules.get("min_through_hole_diameter"):
        floors["via_drill"] = float(rules["min_through_hole_diameter"])
    classes = proj.get("net_settings", {}).get("classes", []) or []
    clearances = [c.get("clearance") for c in classes
                  if isinstance(c.get("clearance"), (int, float))]
    if clearances:
        floors["clearance"] = float(max(clearances))
    return floors


def pair_geometry(bg: geom.BoardGeom, impedance_ohm: float,
                  gap_c2c_mm: float | None = None) -> tuple[float, float]:
    """(track_width, edge_gap) mm for a differential pair on the preferred
    outer layer, from the board stackup (impedance.diff_pair - the same math
    rules_gen uses). constraints gap_mm is CENTER-to-center (check_diffpair's
    convention); KRT's --diff-pair-gap is edge-to-edge."""
    outer = bg.copper_layers[0]
    _, below = bg.stackup.adjacent(outer)
    if below is None or not bg.stackup.dielectrics:
        return FALLBACK_PAIR_WIDTH, 0.2
    h = bg.stackup.height_between(outer, below)
    er = bg.stackup.epsilon_between(outer, below)
    t = bg.stackup.copper_thickness.get(outer, 0.035)
    if gap_c2c_mm is not None:
        # solve width for the pinned center-to-center pitch: w + s = pitch
        w, s = imp.diff_pair(float(impedance_ohm), h, t, er)
        # re-solve with gap pinned so pitch holds approximately
        for _ in range(8):
            s = max(float(gap_c2c_mm) - w, 0.05)
            w, s = imp.diff_pair(float(impedance_ohm), h, t, er, gap=s)
        return w, s
    return imp.diff_pair(float(impedance_ohm), h, t, er)


def rf_width(bg: geom.BoardGeom, impedance_ohm: float) -> float:
    outer = bg.copper_layers[0]
    _, below = bg.stackup.adjacent(outer)
    if below is None or not bg.stackup.dielectrics:
        return BASE_TRACK_WIDTH
    h = bg.stackup.height_between(outer, below)
    er = bg.stackup.epsilon_between(outer, below)
    t = bg.stackup.copper_thickness.get(outer, 0.035)
    return round(imp.solve_width(float(impedance_ohm), h, t, er), 4)


# ------------------------------------------------------------ stub-pad surgery

_NET_NODE = r'\n[ \t]*\(net(?:\s+\d+)?\s+"{name}"\s*\)'


def _footprint_block(text: str, ref: str) -> tuple[int, int]:
    """(start, end) of the footprint block whose Reference property is `ref`."""
    m = re.search(r'\(property\s+"Reference"\s+"%s"' % re.escape(ref), text)
    if not m:
        raise CheckError(f"footprint {ref!r} not found in board text")
    start = text.rfind("(footprint", 0, m.start())
    if start < 0:
        raise CheckError(f"no (footprint block encloses Reference {ref!r}")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise CheckError(f"unbalanced footprint block for {ref!r}")


def detach_stub_pads(text: str, targets: list[tuple[str, str]]
                     ) -> tuple[str, list[tuple[str, str]]]:
    """Remove the (net ...) node of every pad of net inside footprint ref,
    for each (ref, net) target. Returns (new_text, restores) where restores
    is [(detached_block, original_block)] for restore_stub_pads."""
    restores: list[tuple[str, str]] = []
    for ref, net in targets:
        start, end = _footprint_block(text, ref)
        block = text[start:end]
        pat = _NET_NODE.format(name=re.escape(net))
        newblock, nsub = re.subn(pat, "", block)
        if nsub == 0:
            raise CheckError(f"no pad of net {net!r} found in footprint {ref!r}")
        if text.count(block) != 1:
            raise CheckError(f"footprint block for {ref!r} is not unique")
        text = text.replace(block, newblock, 1)
        restores.append((newblock, block))
    return text, restores


def restore_stub_pads(text: str, restores: list[tuple[str, str]]) -> str:
    """Re-insert the original footprint blocks into KRT's output. KRT's
    writer preserves footprint text byte-identical; anything else is a hard
    error (the caller rolls back).

    Applied in REVERSE detach order: when two stub targets share one
    footprint, detach_stub_pads nests its edits (the second detach was made
    on the once-detached block), so only the innermost (last) detached form
    exists in the routed output (S11 review finding)."""
    for detached, original in reversed(restores):
        if text.count(detached) != 1:
            raise CheckError("cannot restore stub pad net: detached footprint "
                             "block not found verbatim in routed output "
                             "(KRT writer changed footprint text?)")
        text = text.replace(detached, original, 1)
    return text


def unmatched_stub_pads(bg: geom.BoardGeom, p: str, n: str
                        ) -> list[tuple[str, str]]:
    """(ref, net) groups of pair pads outside every matched terminal (USB
    pull-up, series tap). Grouped by (ref, net); a group is a stub only when
    NONE of its pads is a matched terminal."""
    matched: set[tuple[str, tuple[float, float]]] = set()
    for pp, nn in check_diffpair.matched_terminals(bg, p, n):
        matched.add((pp.ref, (round(pp.center[0], 3), round(pp.center[1], 3))))
        matched.add((nn.ref, (round(nn.center[0], 3), round(nn.center[1], 3))))
    groups: dict[tuple[str, str], list[bool]] = {}
    for net in (p, n):
        for pad in bg.pads_of(net=net):
            key = (pad.ref, net)
            is_matched = (pad.ref, (round(pad.center[0], 3),
                                    round(pad.center[1], 3))) in matched
            groups.setdefault(key, []).append(is_matched)
    return sorted(k for k, flags in groups.items() if not any(flags))


# ------------------------------------------------------------ KRT invocation

def _tools() -> tuple[Path, Path]:
    cli = env.find_kicad_cli()
    if cli is None:
        raise CheckError("kicad-cli not found (check_env.py --full has "
                         "remediation); pipeline pins KiCad 10.0.3")
    krt = env.find_krt()
    if krt is None:
        raise CheckError(KRT_REMEDIATION)
    return cli, krt


def _stage_board(pcb: Path, work: Path) -> Path:
    """Board + every same-stem sidecar (pro/prl/dru/sch) -> work dir."""
    work.mkdir(parents=True, exist_ok=True)
    staged = work / pcb.name
    for src in pcb.parent.glob(pcb.stem + ".*"):
        if src.is_file() and not src.name.endswith(".lck"):
            shutil.copy2(src, work / src.name)
    if not staged.is_file():
        raise CheckError(f"staging failed: {staged}")
    return staged


def write_fab_overrides(work: Path, floors: dict) -> Path:
    """Pin KRT's fab floor to the board's DRC grading floors (hard floor: the
    overrides file disables fab-tier escalation below what DRC grades)."""
    p = work / "fab_overrides.txt"
    p.write_text(
        f"clearance = {floors['clearance']}\n"
        f"track_width = {floors['track_width']}\n"
        f"via_diameter = {floors['via_diameter']}\n"
        f"via_drill = {floors['via_drill']}\n"
        f"board_edge = {floors['edge_clearance']}\n", encoding="utf-8")
    return p


def run_krt(krt_dir: Path, script: str, staged: Path, out: Path,
            extra: list[str], floors: dict, fab_file: Path,
            grid_step: float, timeout_s: int) -> dict:
    """One KRT run staged -> fresh out. Returns the parsed LAST JSON_SUMMARY.
    Args are a list (no shell) so net names like '/USB_DP' survive."""
    args = [sys.executable, script, str(staged), "--output", str(out),
            "--no-fix-drc-settings",
            "--grid-step", str(grid_step),
            "--clearance", str(floors["clearance"]),
            "--via-size", str(floors["via_diameter"]),
            "--via-drill", str(floors["via_drill"]),
            "--board-edge-clearance", str(floors["edge_clearance"]),
            "--fab-overrides", str(fab_file)] + extra
    try:
        cp = subprocess.run(args, cwd=str(krt_dir), capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise CheckError(f"KRT {script} timed out after {timeout_s}s") from exc
    summary = parse_summary(cp.stdout or "")
    if summary is None:
        # KRT's "nothing to route" path (every target net already fully
        # connected) prints no JSON_SUMMARY but rc=0 + writes an unchanged
        # copy - a legitimate no-op on idempotent re-runs, not an error.
        if cp.returncode == 0 and out.is_file() \
                and "nothing to route" in (cp.stdout or ""):
            return {"already_routed": True, "successful": 0, "failed": 0}
        tail = ((cp.stdout or "") + "\n" + (cp.stderr or "")).strip()[-600:]
        raise CheckError(f"KRT {script} produced no JSON_SUMMARY "
                         f"(rc={cp.returncode}): {tail}")
    return summary


def _pair_outcome(summary: dict, p: str, n: str) -> tuple[bool, str]:
    """(routed_as_coupled_pair, reason) from a route_diff JSON_SUMMARY."""
    for rep in summary.get("pair_reports", []) or []:
        if rep.get("p_net") == p and rep.get("n_net") == n:
            if rep.get("outcome") == "coupled" and \
                    rep.get("pair") in (summary.get("routed_diff_pairs") or []):
                return True, "coupled"
            return False, (rep.get("failure_reason") or rep.get("outcome")
                           or "not-routed")
    # no report row for this pair at all -> it was never even detected
    return False, "pair-not-detected"


def _net_failed(summary: dict, net: str) -> str | None:
    """Failure reason if a route.py summary says `net` did not fully route."""
    if net in (summary.get("failed_single") or []):
        return "single-ended route failed"
    for item in summary.get("failed_multipoint") or []:
        if item.get("net_name") == net:
            k = len(item.get("failed_pads") or [])
            return f"multipoint: {k} pad(s) unconnected"
    return None


def _outer_layers(bg: geom.BoardGeom) -> list[str]:
    cl = bg.copper_layers
    return [cl[0]] if len(cl) < 2 else [cl[0], cl[-1]]


def _slim(summary: dict, keys: tuple[str, ...]) -> dict:
    return {k: summary.get(k) for k in keys if k in summary}


# ------------------------------------------------------------ item runners

def _next_out(ctx: dict, tag: str) -> Path:
    """A FRESH output path per KRT attempt (route.py re-reads DRC floors from
    an output-sibling .kicad_pro on same-path reruns)."""
    ctx["seq"] = ctx.get("seq", 0) + 1
    return ctx["work"] / f"krt_{ctx['seq']:02d}_{tag}.kicad_pcb"


def route_diff_item(ctx: dict, spec: dict) -> tuple[dict | None, dict | None]:
    """Route one diff pair (width ladder + stub-pad detach). Returns
    (fact, violation): exactly one is None."""
    p, n = spec["p"], spec["n"]
    staged = ctx["staged"]
    bg = geom.BoardGeom.from_file(staged)
    if p not in bg.nets or n not in bg.nets:
        missing = [x for x in (p, n) if x not in bg.nets]
        return None, violation(
            SCRIPT, "warning", None, None, p, [],
            f"diff pair {p}/{n} names net(s) not on the board: {missing} "
            f"(stale constraints?)", SCRIPT,
            kind="critical_missing_net", pair=[p, n], missing=missing)

    z = spec.get("impedance_ohm", default_impedance(p, n))
    w, g = pair_geometry(bg, z, spec.get("gap_mm"))
    ladder = [(w, g)]
    if abs(w - FALLBACK_PAIR_WIDTH) > 1e-6:
        ladder.append((FALLBACK_PAIR_WIDTH, max(g, ctx["floors"]["clearance"])))

    stubs = unmatched_stub_pads(bg, p, n)
    original_text = staged.read_text(encoding="utf-8")
    restores: list[tuple[str, str]] = []
    if stubs:
        detached_text, restores = detach_stub_pads(original_text, stubs)
        staged.write_text(detached_text, encoding="utf-8")

    outer = _outer_layers(bg)
    costs = ["1"] if len(outer) == 1 else ["1", "3"]
    try:
        last_reason = "no attempt"
        for rung, (rw, rg) in enumerate(ladder, 1):
            out = _next_out(ctx, f"diff_r{rung}")
            summary = run_krt(
                ctx["krt"], "route_diff.py", staged, out,
                ["--nets", p, n, "--layers", *outer, "--layer-costs", *costs,
                 "--track-width", f"{rw:g}", "--diff-pair-gap", f"{rg:g}"],
                ctx["floors"], ctx["fab_file"], ctx["grid_step"],
                ctx["timeout_s"])
            if summary.get("already_routed"):
                # idempotent re-run: both nets already fully connected; the
                # post-run check_diffpair pass still validates coupling.
                ok, reason = True, "already_routed"
            else:
                ok, reason = _pair_outcome(summary, p, n)
            if ok:
                text = out.read_text(encoding="utf-8")
                if restores:
                    text = restore_stub_pads(text, restores)
                out.write_text(text, encoding="utf-8")
                os.replace(out, staged)
                restores = []          # consumed: staged now holds original pads
                bg2 = geom.BoardGeom.from_file(staged)
                layers = sorted({t.layer for net in (p, n)
                                 for t in bg2.tracks_of(net=net)})
                fact = {"kind": "diff", "nets": [p, n],
                        "impedance_ohm": z,
                        "width_mm": rw, "gap_mm": rg,
                        "impedance_width_mm": w, "ladder_rung": rung,
                        "stub_pads_detached": [list(s) for s in stubs],
                        "layers_used": layers,
                        "krt": _slim(summary, ("routed_diff_pairs",
                                               "total_vias", "total_time",
                                               "min_clearance_used"))}
                return fact, None
            last_reason = reason
        return None, violation(
            SCRIPT, "error", None, None, p, [],
            f"critical diff pair {p}/{n} failed to route as a coupled pair "
            f"({last_reason}); tried widths "
            f"{[rw for rw, _ in ladder]}", SCRIPT,
            kind="critical_route_failed", pair=[p, n], reason=last_reason)
    finally:
        if restores:  # pair never routed - undo the detach on the staged board
            staged.write_text(original_text, encoding="utf-8")


def _route_single_item(ctx: dict, kind: str, nets: list[str],
                       extra: list[str], per_net_meta: dict) -> tuple[list, list]:
    """Shared route.py runner for power/rf. Returns (facts, violations)."""
    staged = ctx["staged"]
    out = _next_out(ctx, kind)
    summary = run_krt(ctx["krt"], "route.py", staged, out,
                      ["--nets", *nets] + extra,
                      ctx["floors"], ctx["fab_file"], ctx["grid_step"],
                      ctx["timeout_s"])
    os.replace(out, staged)  # keep partial successes; failures become violations
    bg2 = geom.BoardGeom.from_file(staged)
    facts, violations = [], []
    for net in nets:
        reason = _net_failed(summary, net)
        layers = sorted({t.layer for t in bg2.tracks_of(net=net)})
        if reason is None:
            facts.append({"kind": kind, "nets": [net], **per_net_meta.get(net, {}),
                          "layers_used": layers,
                          "krt": _slim(summary, ("successful", "failed",
                                                 "multipoint_pads_connected",
                                                 "multipoint_pads_total",
                                                 "total_vias", "total_time"))})
        else:
            violations.append(violation(
                SCRIPT, "error", None, None, net, [],
                f"critical {kind} net {net} failed to route: {reason}",
                SCRIPT, kind="critical_route_failed", reason=reason,
                layers_used=layers))
    return facts, violations


_SEG_BLOCK_RE = re.compile(r"\(segment\b.*?\(uuid \"([0-9a-f-]+)\"\)\s*\)",
                           re.S)
_SEG_FIELD_RES = {
    "start": re.compile(r"\(start ([-\d.]+) ([-\d.]+)\)"),
    "end": re.compile(r"\(end ([-\d.]+) ([-\d.]+)\)"),
    "width": re.compile(r"\(width ([-\d.]+)\)"),
    "layer": re.compile(r"\(layer \"([^\"]+)\"\)"),
    "net": re.compile(r"\(net \"((?:[^\"\\]|\\.)*)\"\)"),
}
CRUMB_MM = 0.05


def normalize_power_widths(staged: Path, specs: list[dict]) -> dict:
    """Post-KRT width discipline (S11 acceptance finding): KRT can emit a few
    base-width segments and sub-grid crumbs on power nets even with
    --no-power-tap-neckdown, which violate rules_gen's aiee_pwr_width_* DRU
    floors. Raise segments below the net's IPC-2152 minimum (the DRU floor -
    the un-margined check_current/rules_gen number) to exactly that floor
    (remove + re-add via route_edit - atomic, verified) and drop crumbs
    (< 0.05 mm). Targeting the floor, not the 1.5x-margined command, keeps
    legitimate fine-pitch neckdowns of low-current nets intact.
    Returns {"widened": n, "crumbs_removed": n}."""
    want = {s["net"]: s["ipc_min_mm"] for s in specs}
    text = staged.read_text(encoding="utf-8")
    ops = []
    widened = crumbs = 0
    for m in _SEG_BLOCK_RE.finditer(text):
        block, uid = m.group(0), m.group(1)
        net_m = _SEG_FIELD_RES["net"].search(block)
        if not net_m or net_m.group(1) not in want:
            continue
        net = net_m.group(1)
        w = float(_SEG_FIELD_RES["width"].search(block).group(1))
        if w >= want[net] - 1e-3:
            continue
        sx, sy = map(float, _SEG_FIELD_RES["start"].search(block).groups())
        ex, ey = map(float, _SEG_FIELD_RES["end"].search(block).groups())
        layer = _SEG_FIELD_RES["layer"].search(block).group(1)
        ops.append({"op": "remove", "uuid": uid})
        if math.hypot(ex - sx, ey - sy) < CRUMB_MM:
            crumbs += 1
            continue
        ops.append({"op": "add_track", "start": [sx, sy], "end": [ex, ey],
                    "width": want[net], "layer": layer, "net": net})
        widened += 1
    if ops:
        route_edit.apply_ops(staged, ops)
    return {"widened": widened, "crumbs_removed": crumbs}


def route_power_item(ctx: dict, specs: list[dict]) -> tuple[list, list]:
    bg = geom.BoardGeom.from_file(ctx["staged"])
    live = [s for s in specs if s["net"] in bg.nets]
    missing = [s for s in specs if s["net"] not in bg.nets]
    # A power net that a plane carries is NOT trunk-routed on the outer
    # layers: the plane IS the trunk (golden usbbuck4 pattern - +3V3 lives on
    # In2). Outer trunk tracks + their vias fragment the plane locally (S11
    # acceptance: a routed +3V3 trunk starved J2's thermal spokes onto an
    # In2 island - error starved_thermal). PTH pads reach the plane through
    # thermal spokes; SMD pads get vias from stitch_vias (next chain step).
    plane_carried = [s for s in live
                     if any(z.filled for z in bg.zones_of(net=s["net"]))]
    live = [s for s in live if s not in plane_carried]
    violations = [violation(
        SCRIPT, "warning", None, None, s["net"], [],
        f"power net {s['net']} not on the board (stale constraints?)",
        SCRIPT, kind="critical_missing_net") for s in missing]
    plane_facts = [
        {"kind": "power", "nets": [s["net"]], "plane_carried": True,
         "current_a": s["current_a"],
         "plane_layers": sorted(
             ly for z in bg.zones_of(net=s["net"])
             for ly, polys in z.fills.items() if polys),
         "note": "plane is the trunk; SMD pads stitched by stitch_vias, "
                 "PTH pads via thermal spokes"}
        for s in plane_carried]
    if not live:
        return plane_facts, violations
    outer = _outer_layers(bg)
    costs = ["1"] if len(outer) == 1 else ["1", "2"]
    # Per-net neckdown policy (S11 acceptance finding): KRT necks power taps
    # down to the 0.2 mm base width near fine-pitch pads. That is legal only
    # for nets whose IPC-2152/DRU floor is <= 0.2 (e.g. +3V3 @0.4A -> 0.20);
    # nets with a fatter floor (+5V @0.5A -> 0.25) must route with
    # --no-power-tap-neckdown or the neck violates aiee_pwr_width_*. A pad
    # that cannot take the un-necked width then fails loudly.
    relaxed = [s for s in live if s["ipc_min_mm"] <= BASE_TRACK_WIDTH + 1e-3]
    strict = [s for s in live if s["ipc_min_mm"] > BASE_TRACK_WIDTH + 1e-3]
    facts, vs = list(plane_facts), []
    for group, extra in ((strict, ["--no-power-tap-neckdown"]), (relaxed, [])):
        if not group:
            continue
        nets = [s["net"] for s in group]
        widths = [f"{s['width_mm']:g}" for s in group]
        f, v = _route_single_item(
            ctx, "power", nets,
            ["--power-nets", *nets, "--power-nets-widths", *widths,
             "--track-width", f"{BASE_TRACK_WIDTH:g}", *extra,
             "--layers", *outer, "--layer-costs", *costs],
            {s["net"]: {"current_a": s["current_a"],
                        "width_mm": s["width_mm"],
                        "ipc_min_mm": s["ipc_min_mm"],
                        "neckdown": not extra} for s in group})
        facts.extend(f)
        vs.extend(v)
    norm = normalize_power_widths(ctx["staged"], live)
    if facts:
        facts[0]["width_normalization"] = norm
    return facts, violations + vs


def route_rf_item(ctx: dict, specs: list[dict]) -> tuple[list, list]:
    bg = geom.BoardGeom.from_file(ctx["staged"])
    live = [s for s in specs if s["net"] in bg.nets]
    missing = [s for s in specs if s["net"] not in bg.nets]
    violations = [violation(
        SCRIPT, "warning", None, None, s["net"], [],
        f"rf net {s['net']} not on the board (stale constraints?)",
        SCRIPT, kind="critical_missing_net") for s in missing]
    facts = []
    outer = _outer_layers(bg)
    costs = ["1"] if len(outer) == 1 else ["1", "3"]
    for s in live:
        w = rf_width(bg, s["impedance_ohm"])
        f, vs = _route_single_item(
            ctx, "rf", [s["net"]],
            ["--track-width", f"{w:g}", "--layers", *outer,
             "--layer-costs", *costs],
            {s["net"]: {"impedance_ohm": s["impedance_ohm"], "width_mm": w,
                        "fence_handoff":
                            f"stitch_vias.py --fence-net {s['net']}"}})
        facts.extend(f)
        violations.extend(vs)
    return facts, violations


# ------------------------------------------------------------ verification

def drc_by_check(report: dict, severity: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in report["violations"]:
        if severity is not None and v.get("severity") != severity:
            continue
        counts[v["check"]] = counts.get(v["check"], 0) + 1
    return counts


def drc_delta(before: dict, after: dict) -> dict:
    """Per-check-type count changes. 'new' = ERROR-severity types that
    INCREASED (the rollback trigger); 'new_warnings' = increased warning
    types, reported only - post-route hygiene (dangling crumbs etc.) is
    route_cleanup's job later in the P7 chain, not a reason to discard a
    good critical route."""
    b, a = drc_by_check(before), drc_by_check(after)
    be = drc_by_check(before, "error")
    ae = drc_by_check(after, "error")
    new = {k: c - be.get(k, 0) for k, c in ae.items() if c > be.get(k, 0)}
    bw = drc_by_check(before, "warning")
    aw = drc_by_check(after, "warning")
    new_w = {k: c - bw.get(k, 0) for k, c in aw.items() if c > bw.get(k, 0)}
    return {"before": b, "after": a, "new": new, "new_warnings": new_w}


def diffpair_postcheck(staged: Path, routed_pairs: list[dict]) -> tuple[list, list]:
    """S5 check_diffpair on the routed pairs only. Returns (violations, facts)."""
    if not routed_pairs:
        return [], []
    bg = geom.BoardGeom.from_file(staged)
    violations, checked = [], []
    for fact in routed_pairs:
        p, n = fact["nets"]
        spec = {"p": p, "n": n,
                "gap_mm": round(fact["width_mm"] + fact["gap_mm"], 4)}
        for k in ("max_skew_mm", "max_uncoupled_mm", "coupling_factor"):
            if k in fact.get("constraint", {}):
                spec[k] = fact["constraint"][k]
        vs, cf = check_diffpair.check_pair(bg, spec)
        violations.extend(vs)
        checked.append(cf)
    return violations, checked


# ------------------------------------------------------------ CLI

def _sidecar(pcb: Path, explicit: str | None, name: str) -> Path | None:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise CheckError(f"{name} not found: {p}")
        return p
    cand = pcb.parent / name
    return cand if cand.is_file() else None


def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--constraints", default=None,
                    help="constraints.json (default: next to the board)")
    ap.add_argument("--only", choices=list(DEFAULT_ORDER), default=None)
    ap.add_argument("--plan", default=None,
                    help='plan.json {"order": ["diff","rf","power"]}')
    ap.add_argument("--grid-step", type=float, default=0.05,
                    help="KRT routing grid (mm); 0.05 keeps 0.5 mm-pitch tap "
                         "corridors routable")
    ap.add_argument("--timeout-s", type=int, default=600,
                    help="per-KRT-invocation process timeout")
    ap.add_argument("--work-dir", default=None)
    ap.add_argument("--out-report", default=None)
    args = ap.parse_args(argv)

    pcb = Path(args.pcb).resolve()
    if not pcb.is_file():
        raise CheckError(f"board not found: {pcb}")
    cons_path = _sidecar(pcb, args.constraints, "constraints.json")
    constraints = checklib.load_json(cons_path, "constraints") if cons_path else {}
    plan = checklib.load_json(args.plan, "plan") if args.plan else None
    order = plan_order(args.only, plan)

    bg0 = geom.BoardGeom.from_file(pcb)
    cu_outer = bg0.stackup.copper_thickness.get(bg0.copper_layers[0], 0.035)

    d_specs = diff_specs(constraints, bg0.nets)
    pair_nets = {x for s in d_specs for x in (s["p"], s["n"])}
    r_specs = rf_specs(constraints, pair_nets)
    p_specs = [s for s in power_specs(constraints, cu_outer)
               if s["net"] not in pair_nets]
    by_kind = {"diff": d_specs, "rf": r_specs, "power": p_specs}
    todo = [(k, by_kind[k]) for k in order if by_kind[k]]
    skipped = [{"kind": k, "count": len(by_kind[k]), "why": "not in --only/plan"}
               for k in DEFAULT_ORDER if by_kind[k] and k not in order]

    if not todo:
        payload = checklib.report(SCRIPT, str(pcb), [], facts={
            "routed": [], "skipped": skipped, "board_updated": False,
            "note": "no critical nets declared or selected"})
        return payload, args.out_report

    cli, krt = _tools()
    work = Path(args.work_dir) if args.work_dir else pcb.parent / "route_critical"
    routelib.fresh_work_dir(work)
    staged = _stage_board(pcb, work)
    floors = grading_floors(work / (pcb.stem + ".kicad_pro"))
    ctx = {"staged": staged, "work": work, "krt": krt, "floors": floors,
           "fab_file": write_fab_overrides(work, floors),
           "grid_step": args.grid_step, "timeout_s": args.timeout_s}

    # fresh fills before the baseline so stale pours don't skew the DRC delta
    if bg0.zones_of():
        kc.run_drc(cli, staged, refill=True, save_board=True)
    before = kc.run_drc(cli, staged, all_track_errors=True)

    routed, violations = [], []
    for kind, specs in todo:
        if kind == "diff":
            for spec in specs:
                fact, v = route_diff_item(ctx, spec)
                if fact:
                    for k in ("max_skew_mm", "max_uncoupled_mm", "coupling_factor"):
                        if k in spec:
                            fact.setdefault("constraint", {})[k] = spec[k]
                    routed.append(fact)
                if v:
                    violations.append(v)
        elif kind == "power":
            facts, vs = route_power_item(ctx, specs)
            routed.extend(facts)
            violations.extend(vs)
        elif kind == "rf":
            facts, vs = route_rf_item(ctx, specs)
            routed.extend(facts)
            violations.extend(vs)

    # verification on the staged result, before the original is touched
    if bg0.zones_of():
        kc.run_drc(cli, staged, refill=True, save_board=True)
    after = kc.run_drc(cli, staged, all_track_errors=True)
    delta = drc_delta(before, after)
    if delta["new"]:
        raise CheckError(
            "routing introduced new DRC errors (rolled back, original board "
            f"untouched): {delta['new']}; work dir kept at {work}")

    dp_viol, dp_facts = diffpair_postcheck(
        staged, [f for f in routed if f["kind"] == "diff"])
    violations.extend(dp_viol)

    board_updated = bool(routed)
    if board_updated:
        routelib.swap_in(staged, pcb)

    payload = checklib.report(SCRIPT, str(pcb), violations, facts={
        "routed": routed,
        "skipped": skipped,
        "drc_delta": delta,
        "diffpair_check": "pass" if not dp_viol else "violations",
        "diffpair_facts": dp_facts,
        "floors": floors,
        "board_updated": board_updated,
        "work_dir": str(work),
    })
    return payload, args.out_report


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
