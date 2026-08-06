"""bench - run ONE pipeline stage in isolation on a frozen fixture (T5).

The per-stage tuning loop's judge (v2 plan appendix): edit a stage's
script/prompt/template, re-run `bench.py --stage PN --fixture F`, keep the
change iff the composite improves.  Fixtures are frozen under
tests/fixtures/stages/ (manifest.yaml, every file sha256-pinned); a score
computed from a drifted fixture is refused (exit 2).

Stages (registry below): P2 architecture, P4 schematic, P5 board_init,
P6 place, P7 route, P8 verify, P9 dfm, P10 order-dryrun.

score.json metric classes (the determinism contract, LEARNINGS 2026-08-06
[tests][freerouting]):
  metrics       offline-deterministic (pure venv).  Declared noise: ZERO -
                two runs on one fixture must match exactly (everything is
                rounded via checklib.rnd conventions upstream).
  metrics_live  deterministic GIVEN the pinned toolchain (kicad-cli 10.0.3
                ERC/DRC/netlist-export legs).  Exact-compare too, but only
                present when kicad-cli resolves; tests needing them are
                smoke-marked.
  informational wall_s, tokens, cost_usd, renders - NEVER compared, never
                in the composite.  Wall-clock and completion ratios of LIVE
                routing runs belong here, not in metrics (bench never runs
                Freerouting; it scores frozen routed boards).
  composite     100 - weighted penalties (benchlib.WEIGHTS), computed from
                metrics (+ metrics_live when available; composite_inputs
                records which).  Comparable ONLY within one
                (stage, fixture): raw metrics are not cross-board
                normalised.

Baselines: tests/fixtures/stages/baselines/<fixture>.score.json, written by
--baseline (refused with --artifact/--file overrides), compared by
--compare.  A compare fails (exit 1) iff composite < baseline composite;
metric drift at equal-or-better composite is reported, not failed.
--compare refuses (exit 2) when composite_inputs differ between the two.

Token/cost: for agent-driven stages the DRIVER session knows the spend, the
script cannot - pass --tokens/--cost-usd and bench records them
informationally.

CLI: bench.py --list
     bench.py --stage P6 --fixture pd_trigger_place [--artifact PATH]
              [--file name=PATH ...] [--baseline] [--compare [PATH]]
              [--work-dir DIR] [--render] [--tokens N] [--cost-usd X]
              [--out score.json]
Exit 0 scored (no regression), 1 known-answer miss or composite regression,
2 error/drifted fixture/missing toolchain for a live-only stage.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
for p in (SCRIPTS, SCRIPTS / "lib"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import benchlib  # noqa: E402
import checklib  # noqa: E402
from checklib import CheckError  # noqa: E402

SCRIPT = "bench"

# stage -> {title, primary artifact key (--artifact target), live legs}
STAGES = {
    "P2": {"title": "architecture (constraints vs netlist)", "primary": "constraints", "live": "none"},
    "P4": {"title": "schematic", "primary": "sch", "live": "optional"},
    "P5": {"title": "board_init", "primary": "netlist", "live": "required"},
    "P6": {"title": "place", "primary": "pcb", "live": "none"},
    "P7": {"title": "route (frozen board)", "primary": "pcb", "live": "optional"},
    "P8": {"title": "verify", "primary": "pcb", "live": "none"},
    "P9": {"title": "dfm", "primary": "pcb", "live": "none"},
    "P10": {"title": "order-dryrun", "primary": "pcb", "live": "none"},
}


def _sev(violations: list[dict]) -> tuple[int, int]:
    e = sum(1 for v in violations if v.get("severity") == "error")
    w = sum(1 for v in violations if v.get("severity") == "warning")
    return e, w


def _kinds(violations: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in violations:
        k = v.get("kind") or v.get("check") or "?"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _find_cli():
    import env
    try:
        return env.find_kicad_cli()
    except Exception:
        return None


def _cli_version(cli) -> str | None:
    try:
        r = subprocess.run([str(cli), "version"], capture_output=True,
                           text=True, timeout=30)
        return (r.stdout or "").strip().splitlines()[0] if r.returncode == 0 \
            else None
    except OSError:
        return None


def _require_pinned_siblings(ctx, artifact: Path):
    """A live ERC/DRC leg reads <stem>.kicad_pro/.kicad_dru SIBLINGS of the
    artifact (LEARNINGS 2026-08-06 [bench][kicad-cli]).  If such a sibling
    exists but is not sha-pinned in the manifest, the freeze is a lie -
    refuse rather than score against unpinned config.  Skipped for
    overridden artifacts: a tuning-loop candidate brings its own copies of
    the fixture's project files (see --artifact help)."""
    primary = None
    for name, path in ctx["files"].items():
        if Path(path) == Path(artifact):
            primary = name
    if primary in ctx["overridden"]:
        return
    pinned = {(benchlib.repo_root() / rec["path"]).resolve()
              for rec in (ctx["entry"].get("files") or {}).values()}
    for ext in (".kicad_pro", ".kicad_dru"):
        sib = Path(artifact).with_suffix(ext)
        if sib.exists() and sib.resolve() not in pinned:
            raise CheckError(
                f"unpinned sibling project file feeds this live leg: {sib} - "
                "pin it in the stage-fixture manifest (it carries severities/"
                "netclasses/custom rules that change the score)")


def _render_pcb(cli, pcb: Path, work: Path, renders: list):
    import kc
    out = work / f"{pcb.stem}_top.png"
    r = kc.render_png(cli, pcb, out, side="top", width=1600, height=900)
    if r.get("status") == "pass":
        renders.append(str(out))


# ------------------------------------------------------------------ scorers
# Each returns (metrics, metrics_live, penalties, ka_violations)
# ka_violations: findings list the fixture's known_answer (if any) is matched
# against.  metrics_live is None when the leg did not run.


def score_p2(ctx):
    import netlist_audit
    cons_p, net_p = ctx["files"]["constraints"], ctx["files"]["netlist"]
    payload, _ = netlist_audit.run(["--netlist", str(net_p),
                                    "--constraints", str(cons_p)])
    errors, warnings = _sev(payload["violations"])
    parsed = netlist_audit.parse_netlist(net_p)
    cons = json.loads(cons_p.read_text(encoding="utf-8"))
    missing = benchlib.placement_refs_missing(cons, parsed["components"])

    stackup = (ctx["args"] or {}).get("stackup")
    stackup_ok = None
    if stackup:
        import yaml
        table = yaml.safe_load(
            (SCRIPTS.parent / "reference" / "stackups.yaml")
            .read_text(encoding="utf-8"))
        rec = (table.get("stackups") or {}).get(stackup)
        stackup_ok = bool(rec) and rec.get("available", True) is not False

    metrics = {"nets": payload.get("nets"),
               "components": payload.get("components"),
               "audit_errors": errors, "audit_warnings": warnings,
               "by_kind": _kinds(payload["violations"]),
               "placement_refs_missing": missing,
               "stackup": stackup, "stackup_ok": stackup_ok}
    penalties = {"audit_errors": errors, "audit_warnings": warnings,
                 "placement_refs_missing": len(missing),
                 "stackup_bad": 0 if stackup_ok in (True, None) else 1}
    return metrics, None, penalties, payload["violations"]


def score_p4(ctx):
    sch = ctx["files"]["sch"]
    metrics = benchlib.sch_metrics([sch])
    penalties = {
        "wire_crossings": metrics["wire_crossings"],
        "label_collisions": metrics["label_collisions"],
        "refdes_overlaps": metrics["refdes_overlaps"],
        "sheet_balance_excess": max(0.0, metrics["sheet_balance"] - 2.0),
    }
    live = None
    if ctx["cli"]:
        import kc
        import netlist_audit
        _require_pinned_siblings(ctx, sch)
        erc = kc.run_erc(ctx["cli"], sch)
        live = {"erc_errors": erc["counts"]["by_severity"].get("error", 0),
                "erc_warnings": erc["counts"]["by_severity"].get("warning", 0),
                "kicad_version": erc.get("kicad_version")}
        golden = ctx["files"].get("golden_net")
        if golden:
            exported = ctx["work"] / "exported.net"
            r = kc.export_netlist(ctx["cli"], sch, exported)
            if r.get("status") != "pass":
                raise CheckError(f"netlist export failed: {r.get('stderr_tail')}")
            cmp_payload, _ = netlist_audit.run(["--netlist", str(exported),
                                                "--compare", str(golden)])
            live["netlist_identical"] = bool(cmp_payload.get("identical"))
            live["netlist_diffs"] = cmp_payload["counts"]["total"]
        penalties["erc_errors"] = live["erc_errors"]
        penalties["erc_warnings"] = live["erc_warnings"]
        penalties["netlist_diffs"] = live.get("netlist_diffs", 0)
        if ctx["render"]:
            out = ctx["work"] / f"{sch.stem}.pdf"
            r = kc.export_sch_pdf(ctx["cli"], sch, out)
            if r.get("status") == "pass":
                ctx["renders"].append(str(out))
    return metrics, live, penalties, []


def score_p5(ctx):
    if not ctx["cli"]:
        raise CheckError("P5 board_init needs live kicad-cli + bundled python "
                         "(env.py); no offline leg exists for this stage")
    args = ctx["args"] or {}
    out_dir = ctx["work"] / "board_init"
    report = ctx["work"] / "board_init_report.json"
    cmd = [sys.executable, str(SCRIPTS / "board_init.py"),
           "--netlist", str(ctx["files"]["netlist"]),
           "--name", args.get("name", "bench"),
           "--out", str(out_dir),
           "--layers", str(args.get("layers", 2)),
           "--out-report", str(report)]
    if args.get("stackup"):
        cmd += ["--stackup", args["stackup"]]
    if "fp_lib" in ctx["files"]:
        cmd += ["--fp-lib", str(ctx["files"]["fp_lib"])]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if not report.is_file():
        raise CheckError(f"board_init emitted no report (rc {r.returncode}): "
                         f"{(r.stdout or r.stderr)[-400:]}")
    rep = json.loads(report.read_text(encoding="utf-8"))
    if rep.get("status") == "error":
        raise CheckError(f"board_init error: {rep.get('error', '?')[:400]}")
    sc = rep.get("self_check") or {}
    live = {"kicad_version": _cli_version(ctx["cli"]),
            "components": rep.get("components"), "nets": rep.get("nets"),
            "fab_profile": rep.get("fab_profile"),
            "setup_violations": len(sc.get("setup_violations") or []),
            "transient_silk": len(sc.get("transient_silk") or []),
            "parity_count": sc.get("parity_count"),
            "clean": bool(sc.get("clean"))}
    penalties = {"setup_violations": live["setup_violations"],
                 "not_clean": 0 if live["clean"] else 1,
                 "transient_silk": live["transient_silk"]}
    if ctx["render"]:
        pcb = next(out_dir.glob("*.kicad_pcb"), None)
        if pcb:
            _render_pcb(ctx["cli"], pcb, ctx["work"], ctx["renders"])
    return {}, live, penalties, []


def score_p6(ctx):
    import place_metrics
    argv = ["--pcb", str(ctx["files"]["pcb"])]
    if "constraints" in ctx["files"]:
        argv += ["--constraints", str(ctx["files"]["constraints"])]
    if "decoupling" in ctx["files"]:
        argv += ["--decoupling", str(ctx["files"]["decoupling"])]
    payload, _ = place_metrics.run(argv)
    m = payload["metrics"]
    decap_worst = max((f.get("manhattan_mm") or 0)
                      for f in m.get("decoupling") or [{}]) if m.get("decoupling") else 0.0
    metrics = {"footprints": m["counts"]["footprints"],
               "nets": m["counts"]["nets"],
               "hpwl_total_mm": m["hpwl"]["total_mm"],
               "crossings": m["crossings"]["count"],
               "congestion_max": m["congestion"]["max"],
               "congestion_mean_nonzero": m["congestion"]["mean_nonzero"],
               "violations_total": payload["counts"]["total"],
               "by_kind": _kinds(payload["violations"]),
               "decap_worst_mm": decap_worst,
               "utilization": m["utilization"]["ratio"]}
    penalties = {"hpwl_total_mm": metrics["hpwl_total_mm"],
                 "crossings": metrics["crossings"],
                 "congestion_max": metrics["congestion_max"],
                 "legality_violations": metrics["violations_total"],
                 "decap_worst_mm": decap_worst}
    if ctx["render"] and ctx["cli"]:
        _render_pcb(ctx["cli"], ctx["files"]["pcb"], ctx["work"], ctx["renders"])
    return metrics, None, penalties, payload["violations"]


def score_p7(ctx):
    import geom
    pcb = ctx["files"]["pcb"]
    bg = geom.BoardGeom.from_file(pcb)
    track_mm = round(sum(t.length for t in bg.tracks_of()), 2)
    metrics = {"track_mm": track_mm,
               "track_count": len(bg.tracks_of()),
               "via_count": len(bg.vias_of())}
    penalties = {"track_mm": track_mm, "via_count": metrics["via_count"],
                 "incompletion_pct": 0.0, "drc_errors": 0, "drc_warnings": 0}
    live = None
    ka: list[dict] = []
    if ctx["cli"]:
        import kc
        import route_auto
        _require_pinned_siblings(ctx, pcb)
        drc = kc.run_drc(ctx["cli"], pcb, parity=False, all_track_errors=True)
        routable = route_auto._routable_nets(bg)
        unrouted = route_auto._drc_unrouted(drc)
        completion = 1.0 if not routable else \
            round(1 - len(unrouted) / len(routable), 4)
        live = {"drc_errors": drc["counts"]["by_severity"].get("error", 0),
                "drc_warnings": drc["counts"]["by_severity"].get("warning", 0),
                "completion": completion,
                "routable_nets": len(routable),
                "unrouted_nets": sorted(unrouted),
                "kicad_version": drc.get("kicad_version")}
        penalties["incompletion_pct"] = round((1 - completion) * 100, 4)
        penalties["drc_errors"] = live["drc_errors"]
        penalties["drc_warnings"] = live["drc_warnings"]
        ka = drc["violations"]
        if ctx["render"]:
            _render_pcb(ctx["cli"], pcb, ctx["work"], ctx["renders"])
    return metrics, live, penalties, ka


def _si_scalars(reports_dir: Path) -> dict:
    """Derived-SI scalars from the per-check reports (defensive: absent
    checks/facts yield nulls, never a crash)."""
    out = {"decap_worst_loop_nh": None, "decap_worst_manhattan_mm": None,
           "diffpair_worst_skew_ps": None, "diffpair_worst_uncoupled_mm": None,
           "return_corridor_voids": None}

    def _load(name):
        p = reports_dir / f"{name}.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
        return None

    dec = _load("check_decoupling")
    if dec and dec.get("checked"):
        loops = [f.get("loop_nh") for f in dec["checked"] if f.get("loop_nh") is not None]
        dists = [f.get("manhattan_mm") for f in dec["checked"] if f.get("manhattan_mm") is not None]
        out["decap_worst_loop_nh"] = max(loops) if loops else None
        out["decap_worst_manhattan_mm"] = max(dists) if dists else None
    dp = _load("check_diffpair")
    if dp and dp.get("checked"):
        skews = [f.get("skew_ps") for f in dp["checked"] if f.get("skew_ps") is not None]
        unc = [max(f.get("uncoupled_p_mm") or 0, f.get("uncoupled_n_mm") or 0)
               for f in dp["checked"]]
        out["diffpair_worst_skew_ps"] = max(skews) if skews else None
        out["diffpair_worst_uncoupled_mm"] = max(unc) if unc else None
    rp = _load("check_return_path")
    if rp is not None:
        out["return_corridor_voids"] = sum(
            1 for v in rp.get("violations") or [] if v.get("kind") == "corridor_void")
    return out


def score_p8(ctx):
    import verify_all
    reports = ctx["work"] / "checks"
    argv = ["--pcb", str(ctx["files"]["pcb"]),
            "--reports-dir", str(reports),
            "--out", str(ctx["work"] / "verify_summary.json")]
    if "constraints" in ctx["files"]:
        argv += ["--constraints", str(ctx["files"]["constraints"])]
    if "decoupling" in ctx["files"]:
        argv += ["--decoupling", str(ctx["files"]["decoupling"])]
    payload, _ = verify_all.run(argv)
    bad = [n for n, c in payload["checks"].items() if c["status"] == "error"]
    if bad:
        raise CheckError(f"verify sub-checks errored: {bad}")
    errors, warnings = _sev(payload["violations"])
    metrics = {"errors": errors, "warnings": warnings,
               "by_check": payload["counts"].get("by_check", {}),
               "by_kind": _kinds(payload["violations"]),
               "si": _si_scalars(reports)}
    penalties = {"errors": errors, "warnings": warnings,
                 "known_answer_missed": 0, "forbidden_errors": 0}
    if ctx["render"] and ctx["cli"]:
        _render_pcb(ctx["cli"], ctx["files"]["pcb"], ctx["work"], ctx["renders"])
    return metrics, None, penalties, payload["violations"]


def score_p9(ctx):
    import dfm_check
    args = ctx["args"] or {}
    payload = dfm_check.run(Path(ctx["files"]["pcb"]),
                            fab_dir=Path(ctx["files"]["gerbers"]),
                            copper_oz=float(args.get("copper_oz", 1.0)),
                            netlist=Path(ctx["files"]["netlist"]))
    errors, warnings = _sev(payload["violations"])
    metrics = {"errors": errors, "warnings": warnings,
               "by_kind": _kinds(payload["violations"]),
               "polarity": (payload.get("polarity") or {}).get("status"),
               "capability_key": payload.get("capability_key")}
    penalties = {"errors": errors, "warnings": warnings,
                 "known_answer_missed": 0, "forbidden_errors": 0}
    if ctx["render"] and ctx["cli"]:
        _render_pcb(ctx["cli"], ctx["files"]["pcb"], ctx["work"], ctx["renders"])
    return metrics, None, penalties, payload["violations"]


def score_p10(ctx):
    import fabhash
    import order_quote
    import order_submit
    args = ctx["args"] or {}
    work_fab = ctx["work"] / "fab"
    if work_fab.exists():
        shutil.rmtree(work_fab)
    shutil.copytree(ctx["files"]["fab"], work_fab)

    quote_out = ctx["work"] / "quote.json"
    qtys = [int(q) for q in str(args.get("qty_matrix", "5,10,30")).split(",")]
    q_payload = order_quote.run(Path(ctx["files"]["pcb"]), qtys,
                                ["HASL"], ["green"])
    quote_out.write_text(json.dumps(q_payload, indent=1), encoding="utf-8")
    s_payload = order_submit.run(Path(ctx["files"]["pcb"]), work_fab,
                                 quote=quote_out,
                                 qty=int(args.get("qty", 5)))

    zips = sorted(work_fab.glob("*_gerbers.zip"))
    dh = dh2 = None
    if zips:
        dh = fabhash.design_hash(zips[0])
        dh2 = fabhash.design_hash(zips[0])
    cheapest = (q_payload.get("cheapest") or {})
    metrics = {"submit_status": s_payload.get("status"),
               "missing": len(s_payload.get("missing") or []),
               "quote_cheapest_total": cheapest.get("total"),
               "quote_cheapest_qty": cheapest.get("qty"),
               "spec": q_payload.get("spec"),
               "design_sha256": dh, "hash_stable": dh == dh2 and dh is not None}
    penalties = {"not_ready": 0 if s_payload.get("status") == "ready_for_human" else 1,
                 "missing_items": metrics["missing"]}
    return metrics, None, penalties, []


SCORERS = {"P2": score_p2, "P4": score_p4, "P5": score_p5, "P6": score_p6,
           "P7": score_p7, "P8": score_p8, "P9": score_p9, "P10": score_p10}


# ---------------------------------------------------------------- baselines

def baseline_path(manifest_path: Path, fixture: str) -> Path:
    return manifest_path.parent / "baselines" / f"{fixture}.score.json"


def _flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k in sorted(obj):
            out.update(_flatten(obj[k], f"{prefix}{k}."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}{i}."))
    else:
        out[prefix[:-1]] = obj
    return out


def compare_to_baseline(payload: dict, base: dict) -> dict:
    if base.get("composite_inputs") != payload.get("composite_inputs"):
        raise CheckError(
            f"composite_inputs mismatch: baseline {base.get('composite_inputs')} "
            f"vs current {payload.get('composite_inputs')} - rerun with the "
            "same toolchain availability before comparing")
    bv = (base.get("metrics_live") or {}).get("kicad_version")
    cv = (payload.get("metrics_live") or {}).get("kicad_version")
    if bv and cv and bv != cv:
        raise CheckError(
            f"kicad toolchain changed: baseline {bv} vs current {cv} - "
            "scores across toolchains are not comparable; re-record the "
            "baselines deliberately")
    diffs = []
    for section in ("metrics", "metrics_live", "penalties"):
        a = _flatten(base.get(section) or {})
        b = _flatten(payload.get(section) or {})
        for key in sorted(set(a) | set(b)):
            if key == "kicad_version":
                continue
            if a.get(key) != b.get(key):
                diffs.append({"metric": f"{section}.{key}",
                              "baseline": a.get(key), "current": b.get(key)})
    delta = round(payload["composite"] - base["composite"], 2)
    return {"composite": base["composite"], "delta": delta,
            "regressed": delta < 0, "metric_diffs": diffs}


# --------------------------------------------------------------------- main

def run(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true",
                    help="list stages and their fixtures")
    ap.add_argument("--stage", choices=sorted(STAGES, key=lambda s: int(s[1:])))
    ap.add_argument("--fixture")
    ap.add_argument("--manifest", help="override the stage-fixture manifest")
    ap.add_argument("--artifact", help="score this file as the stage's primary "
                    "artifact instead of the frozen one (tuning-loop "
                    "candidate). For live ERC/DRC legs put copies of the "
                    "fixture's .kicad_pro/.kicad_dru next to the candidate - "
                    "they carry severities/netclasses the score depends on")
    ap.add_argument("--file", action="append", default=None, metavar="NAME=PATH",
                    help="override any manifest file entry by name")
    ap.add_argument("--baseline", action="store_true",
                    help="write baselines/<fixture>.score.json")
    ap.add_argument("--compare", nargs="?", const="auto", default=None,
                    help="compare against a baseline score.json (default: the "
                    "committed one)")
    ap.add_argument("--work-dir", help="keep intermediates here (default: temp)")
    ap.add_argument("--render", action="store_true",
                    help="emit render(s) into the work dir (live kicad only)")
    ap.add_argument("--tokens", type=int)
    ap.add_argument("--cost-usd", type=float)
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    manifest_path = Path(args.manifest) if args.manifest else benchlib.default_manifest()

    if args.list:
        manifest = benchlib.load_manifest(manifest_path) \
            if manifest_path.is_file() else {"fixtures": {}}
        stages = {}
        for s, spec in STAGES.items():
            fixtures = sorted(f for f, e in manifest["fixtures"].items()
                              if e.get("stage") == s)
            stages[s] = {"title": spec["title"], "primary": spec["primary"],
                         "live": spec["live"], "fixtures": fixtures}
        return {"script": SCRIPT, "status": "pass", "stages": stages}, args.out

    if not args.stage or not args.fixture:
        raise CheckError("--stage and --fixture are required (or --list)")

    manifest = benchlib.load_manifest(manifest_path)
    entry = benchlib.fixture_entry(manifest, args.fixture)
    if entry.get("stage") != args.stage:
        raise CheckError(f"fixture '{args.fixture}' is a {entry.get('stage')} "
                         f"fixture, not {args.stage}")

    overrides: dict[str, Path] = {}
    if args.artifact:
        overrides[STAGES[args.stage]["primary"]] = Path(args.artifact)
    for spec in args.file or []:
        name, _, path = spec.partition("=")
        if not path:
            raise CheckError(f"--file wants NAME=PATH, got '{spec}'")
        overrides[name] = Path(path)
    if overrides and args.baseline:
        raise CheckError("--baseline records the FROZEN fixture; it cannot be "
                         "combined with --artifact/--file overrides")
    valid = set(entry.get("files") or {}) | set(entry.get("dirs") or {}) \
        | {STAGES[args.stage]["primary"]}
    unknown_names = sorted(set(overrides) - valid)
    if unknown_names:
        raise CheckError(f"--file names not in this fixture: {unknown_names} "
                         f"(have: {sorted(valid)})")
    judge_side = sorted(set(overrides) - {STAGES[args.stage]["primary"]})
    if args.compare and judge_side:
        raise CheckError("--compare only supports overriding the stage's "
                         f"primary artifact; judge-side overrides {judge_side} "
                         "would invalidate the baseline comparison")
    if args.render and not args.work_dir:
        raise CheckError("--render requires --work-dir (renders written to "
                         "the default temp dir would be deleted on exit)")

    pinned = {k: v for k, v in entry.items() if k in ("files", "dirs")}
    check_entry = {kind: {n: r for n, r in (pinned.get(kind) or {}).items()
                          if n not in overrides}
                   for kind in ("files", "dirs")}
    drift = benchlib.verify_fixture(check_entry)
    if drift:
        raise CheckError("fixture drifted - refusing to score: "
                         + "; ".join(drift))

    files = benchlib.fixture_paths(entry)
    for name, path in overrides.items():
        if not path.exists():
            raise CheckError(f"override {name}={path} does not exist")
        files[name] = path.resolve()

    if args.work_dir:
        work = Path(args.work_dir)
        work.mkdir(parents=True, exist_ok=True)
        tmp = None
    else:
        import tempfile
        tmp = tempfile.TemporaryDirectory(prefix="bench_")
        work = Path(tmp.name)

    try:
        cli = _find_cli()
        if STAGES[args.stage]["live"] == "required" and cli is None:
            raise CheckError(f"stage {args.stage} needs kicad-cli (pinned via "
                             "lib/env.py) and none resolved")
        ctx = {"entry": entry, "files": files, "args": entry.get("args"),
               "work": work, "cli": cli, "render": args.render, "renders": [],
               "overridden": set(overrides)}
        t0 = time.perf_counter()
        metrics, live, penalties, ka_violations = SCORERS[args.stage](ctx)
        wall_s = round(time.perf_counter() - t0, 2)

        known = entry.get("known_answer")
        ka = None
        if known:
            if not {"known_answer_missed", "forbidden_errors"} \
                    <= set(benchlib.WEIGHTS[args.stage]):
                raise CheckError(
                    f"known_answer is only scoreable on stages whose weight "
                    f"table has known_answer_missed/forbidden_errors (P8/P9); "
                    f"'{args.fixture}' is {args.stage}")
            ka = benchlib.match_known_answer(known, ka_violations)
            penalties["known_answer_missed"] = len(ka["missed"])
            penalties["forbidden_errors"] = ka["forbidden_errors"]

        composite = benchlib.composite(args.stage, penalties)
        composite_inputs = "full" if (live is not None or
                                      STAGES[args.stage]["live"] == "none") \
            else "offline"

        payload = {
            "script": SCRIPT, "status": "pass",
            "stage": args.stage, "fixture": args.fixture,
            "board": entry.get("board"),
            "artifact": str(files.get(STAGES[args.stage]["primary"], "")),
            "overridden": sorted(overrides),
            "metrics": metrics, "metrics_live": live,
            "penalties": {k: round(float(v), 4) for k, v in penalties.items()},
            "composite": composite, "composite_inputs": composite_inputs,
            "known_answer": ka,
            "informational": {"wall_s": wall_s, "tokens": args.tokens,
                              "cost_usd": args.cost_usd,
                              "renders": ctx["renders"]},
        }
        if ka and ka["status"] != "ok":
            payload["status"] = "violations"

        if args.compare:
            bpath = baseline_path(manifest_path, args.fixture) \
                if args.compare == "auto" else Path(args.compare)
            if not bpath.is_file():
                raise CheckError(f"no baseline at {bpath} (run --baseline first)")
            base = json.loads(bpath.read_text(encoding="utf-8"))
            payload["baseline"] = {"path": str(bpath),
                                   **compare_to_baseline(payload, base)}
            if payload["baseline"]["regressed"]:
                payload["status"] = "violations"

        if args.baseline:
            bpath = baseline_path(manifest_path, args.fixture)
            bpath.parent.mkdir(parents=True, exist_ok=True)
            keep = {k: payload[k] for k in
                    ("script", "stage", "fixture", "board", "metrics",
                     "metrics_live", "penalties", "composite",
                     "composite_inputs", "known_answer")}
            keep["_baseline"] = {"created": time.strftime("%Y-%m-%d"),
                                 "kicad_version":
                                     (live or {}).get("kicad_version")
                                     if isinstance(live, dict) else None}
            bpath.write_text(json.dumps(keep, indent=1, sort_keys=False,
                                        ensure_ascii=True) + "\n",
                             encoding="utf-8")
            payload["baseline_written"] = str(bpath)

        return payload, args.out
    finally:
        if tmp is not None:
            tmp.cleanup()


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
