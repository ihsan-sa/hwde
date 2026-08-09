"""rf-de-20m P7 - turn a FILTERED Freerouting session into route_edit ops.

WHY NOT `import_ses`: KiCad's ImportSpecctraSES REPLACES the board's wiring
with the session's, it does not add to it. route_auto gets away with that
because the DSN it feeds Freerouting carries every existing track as a guide
wire, so the SES echoes them all back. This pass cannot: the DSN has to have
its 9 degenerate-aspect wires removed to get past Freerouting's reader at all
(fr_signals.py), and the session then has to be filtered down to the 10 nets
that actually needed routing. Importing that measured 209 -> 89 tracks and
24 -> 44 unconnected, i.e. it deleted the whole board.

So the session's wiring is converted to add_track/add_via ops and applied with
route_edit, which is additive, atomic and post-verified.

SES geometry: (resolution um 10) -> 1 unit = 0.1 um; y is Specctra-up, so
board_y_mm = -y/10000.

Usage: python ses_to_ops.py <session.ses> <ops.json>
"""
import json
import re
import sys
from pathlib import Path

NET_RE = re.compile(r'\(net (\"[^\"]+\"|\S+)')
WIRE_RE = re.compile(r'\(path (\S+) ([0-9.]+)\s*([-0-9.\s]+?)\)', re.S)
VIA_RE = re.compile(r'\(via \"([^\"]+)\" (-?[0-9.]+) (-?[0-9.]+)')
VIA_SIZE_RE = re.compile(r'Via\[[^\]]*\]_(\d+):(\d+)_um')


def blocks(text, start):
    """Yield (net_name, block_text) for every (net ...) under network_out."""
    i = text.index(start)
    while True:
        m = NET_RE.search(text, i)
        if not m:
            return
        depth, k = 0, m.start()
        while True:
            if text[k] == '(':
                depth += 1
            elif text[k] == ')':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        yield m.group(1).strip('"'), text[m.start():k + 1]
        i = k + 1


def mm(v):
    return round(float(v) / 10000.0, 6)


def main():
    ses = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = ses.read_text(encoding='utf-8', errors='replace')
    ops, stats = [], {}
    for net, blk in blocks(text, '(network_out'):
        n_t = n_v = 0
        for m in WIRE_RE.finditer(blk):
            layer, width, coords = m.group(1), float(m.group(2)), \
                m.group(3).split()
            pts = [(mm(coords[k]), -mm(coords[k + 1]))
                   for k in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                if a == b:
                    continue
                ops.append({"op": "add_track", "start": list(a),
                            "end": list(b), "width": round(width / 10000, 6),
                            "layer": layer, "net": net})
                n_t += 1
        for m in VIA_RE.finditer(blk):
            sm = VIA_SIZE_RE.search(m.group(1))
            size, drill = (int(sm.group(1)) / 1000.0,
                           int(sm.group(2)) / 1000.0) if sm else (0.45, 0.2)
            ops.append({"op": "add_via", "at": [mm(m.group(2)),
                                                -mm(m.group(3))],
                        "size": size, "drill": drill, "net": net})
            n_v += 1
        stats[net] = {"tracks": n_t, "vias": n_v}
    out.write_text(json.dumps({"version": 1, "ops": ops}, indent=1),
                   encoding='utf-8')
    print(json.dumps({"ops": len(ops), "by_net": stats,
                      "out": str(out)}, indent=1))


main()
