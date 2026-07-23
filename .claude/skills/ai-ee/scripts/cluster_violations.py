"""cluster_violations.py - group open violations for fixer dispatch (SPEC 4).

The orchestrator's fix loop clusters violations "by net/region/type" and sends
one fixer agent per cluster, in parallel where regions don't overlap. This tool
produces those clusters from a verify_all summary (or any report carrying a
`violations` list): violations are grouped by (net, kind) and then split into
spatial regions (positions within `--radius` mm are one region). Each cluster
carries a bounding region and a suggested fixer domain so the orchestrator can
route it.

CLI: --input summary.json  (or --pcb-relative report) [--radius 5]
     [--out clusters.json]
Exit: 0 no clusters, 1 clusters present (work to do), 2 error.

Cluster schema:
    {"id", "net", "kinds"[], "checks"[], "severity", "count",
     "region": {"bbox": [xmin,ymin,xmax,ymax]|null, "center": [x,y]|null},
     "fixer": "<domain>", "violations": [ ...the raw violations... ]}
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402

SCRIPT = "cluster_violations"
DEFAULT_RADIUS_MM = 5.0
SEV_RANK = {"error": 2, "warning": 1, "info": 0}

# kind -> the fixer domain best suited to resolve it (advisory; S13 wires the
# actual agent dispatch off these).
FIXER_HINTS = {
    "corridor_void": "plane", "no_reference_plane": "plane",
    "missing_return_via": "router", "missing_stitch_cap": "router",
    "insufficient_transition_vias": "router",
    "undersized_track": "router", "pour_neckdown": "router",
    "decoupler_distance": "placement", "decoupler_loop": "placement",
    "gnd_stub_long": "placement", "metadata_mismatch": "schematic",
    "diffpair_skew": "router", "diffpair_uncoupled": "router",
    "diffpair_via_asymmetry": "router", "diffpair_missing_net": "schematic",
    "creepage": "placement",
    "thermal_area": "plane", "thermal_vias": "router",
    "silk_over_pad": "silk", "silk_illegible": "silk", "silk_thin": "silk",
    "pdn_undecoupled": "schematic", "pdn_no_bulk": "schematic",
}


def _uf_find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def spatial_split(items: list[dict], radius: float) -> list[list[dict]]:
    """Union-find the violations by position proximity; None-pos items each
    form their own group (they are net-level, not point defects)."""
    pts = [v.get("pos") for v in items]
    idx = [i for i, p in enumerate(pts) if p]
    parent = list(range(len(items)))
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            dx = pts[i][0] - pts[j][0]
            dy = pts[i][1] - pts[j][1]
            if (dx * dx + dy * dy) ** 0.5 <= radius:
                parent[_uf_find(parent, i)] = _uf_find(parent, j)
    groups: dict[int, list] = {}
    for i, v in enumerate(items):
        key = _uf_find(parent, i) if pts[i] else -(i + 1)
        groups.setdefault(key, []).append(v)
    return list(groups.values())


def region_of(vs: list[dict]) -> dict:
    pts = [v["pos"] for v in vs if v.get("pos")]
    if not pts:
        return {"bbox": None, "center": None}
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bbox = [checklib.rnd(min(xs)), checklib.rnd(min(ys)),
            checklib.rnd(max(xs)), checklib.rnd(max(ys))]
    center = [checklib.rnd(sum(xs) / len(xs)), checklib.rnd(sum(ys) / len(ys))]
    return {"bbox": bbox, "center": center}


def cluster(violations: list[dict], radius: float) -> list[dict]:
    by_key: dict[tuple, list] = {}
    for v in violations:
        by_key.setdefault((v.get("net"), v.get("kind")), []).append(v)
    clusters: list[dict] = []
    for (net, kind), items in by_key.items():
        for group in spatial_split(items, radius):
            sev = max((g.get("severity", "info") for g in group),
                      key=lambda s: SEV_RANK.get(s, 0))
            kinds = sorted({g.get("kind") for g in group if g.get("kind")})
            checks = sorted({c for g in group
                             if (c := g.get("source") or g.get("check"))})
            clusters.append({
                "net": net, "kinds": kinds, "checks": checks, "severity": sev,
                "count": len(group), "region": region_of(group),
                "fixer": FIXER_HINTS.get(kind, "review"),
                "violations": group,
            })
    # most severe, largest first; stable id
    clusters.sort(key=lambda c: (-SEV_RANK.get(c["severity"], 0), -c["count"]))
    for i, c in enumerate(clusters):
        c["id"] = i
    return clusters


def load_violations(path) -> tuple[list[dict], str | None]:
    data = checklib.load_json(path, "input report")
    if isinstance(data, list):
        return data, None
    return data.get("violations", []), data.get("board")


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Cluster open violations by (region, net, type).")
    ap.add_argument("--input", required=True,
                    help="verify_all summary.json or any report with violations")
    ap.add_argument("--radius", type=float, default=DEFAULT_RADIUS_MM,
                    help="mm; positions within this join one region (default 5)")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    violations, board = load_violations(args.input)
    clusters = cluster(violations, args.radius)
    by_sev: dict[str, int] = {}
    for c in clusters:
        by_sev[c["severity"]] = by_sev.get(c["severity"], 0) + 1
    payload = {
        "script": SCRIPT, "board": board,
        "status": "violations" if clusters else "pass",
        "counts": {"clusters": len(clusters), "violations": len(violations),
                   "by_severity": by_sev},
        "clusters": clusters,
    }
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
