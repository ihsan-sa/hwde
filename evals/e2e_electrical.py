"""e2e_electrical - score a finished board on whether it would work.

The e2e eval's electrical scorer. It reads one board workspace (either arm's
layout: the bare arm's board/kicad/, hwde's boards/<name>/kicad/) and checks
it against a HIDDEN known-answer for the brief, evals/known_answers/<brief>.yaml,
written from the chosen chip's datasheet typical application:

  connectivity  every supply pin of each IC has a decoupling cap of the right
                value to ground, bootstrap caps sit between the right pins,
                strap pins (mode, gain) sit at a value the datasheet allows,
                no required pin floats, USB-C CC pins have 5.1k to ground.
  values        LDO input/output caps against the datasheet minimum, the input
                coupling high-pass corner, the output LC filter's cutoff (by
                ngspice, an AC sweep of the filter the board actually has).
  power         LDO dissipation against its package (junction temperature at
                the brief's load), thermal-pad vias, trace width against the
                current each power net carries (IPC-2152, external layer).
  placement     decap distance from each supply pin on the PCB.

ERC and DRC run by kicad-cli (error severity, unrouted nets included) and
act as gates: E is multiplied by max(0, 1 - GATE_STEP * errors), because a
board that fails its own rule check is not one we can call working however
good its parts are.  A CRITICAL check scoring 0 (no Rd on a CC pin, an LDO
pin off its rail, a missing bootstrap cap, an amp held in shutdown, no path
for its heat) caps E at CRITICAL_CAP before the gate.

It is INDEPENDENT of hwde: it imports nothing from the skill (no checklib,
simlib, e2elib, check_*), reads no sidecar the hwde arm writes (decoupling.json,
parts.json's roles), exports its own netlist from the schematic and parses
the PCB itself, so both arms are scored by the same code from the same files.

Composite: electrical dominates, size and cost are minor:
  composite = 100 * (0.70*E + 0.15*layout + 0.15*cost)
where layout and cost are the old scorer's categories (bench.py --stage E2E)
when the caller passes them, and E is this module's score.

CLI:
  e2e_electrical.py --brief usbc_ldo --workspace DIR [--old-score score.json]
                    [--out FILE]
  e2e_electrical.py --rescore (RECORDS.jsonl | RUN_DIR)... [--out FILE]
      re-score every run record whose workspace still exists, and every
      <stamp>-<brief>-<arm>-s<n> run dir with a score.json; one
      {run_id, arm, old_composite, electrical, composite, findings} row each.

e2e_run.py calls score_workspace after bench.py for every brief that has a
known-answer here (usbc_ldo and stereo_amp so far).

Exit 0 when scored, 1 when the board can't be read (no schematic, kicad-cli
failed), 2 on bad input (unknown brief, missing workspace).
"""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
ANSWERS = REPO / "evals" / "known_answers"
WEIGHTS = {"electrical": 0.70, "layout": 0.15, "cost": 0.15}
GROUP_WEIGHTS = {"connectivity": 0.40, "values": 0.25, "power": 0.20,
                 "placement": 0.15}
GATE_STEP = 0.10               # per ERC/DRC error
# A check here scoring 0 means the board would not work (no Rd, an LDO pin
# off its rail, a missing bootstrap cap, an amp held in shutdown, no path
# for its heat): E is capped at CRITICAL_CAP however good the rest is.
CRITICAL = re.compile(r"(cc[12]_rd|cc_separate|usbc_connector|ldo|ldo_vin|"
                      r"ldo_vout|ldo_gnd|ldo_en|ldo_floating|ldo_tj|ldo_current|"
                      r"amp|pvcc_rail|gnd_pins|bootstrap_\d+|gain_strap|sdz|mute|"
                      r"lc_left|lc_right|thermal_vias)")
CRITICAL_CAP = 0.5
SKIP_DIRS = {"log", "tmp", "backup", "backups", "anneal", "gen", "lib"}


class BoardError(Exception):
    """The board can't be read: no schematic, or kicad-cli failed."""


# ----------------------------------------------------------------- s-expr

_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def sexpr(text: str):
    """KiCad s-expression -> nested lists of str (quoted strings unescaped)."""
    stack, cur, pos = [], [], 0
    n = len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            if text[pos:].strip():
                raise BoardError(f"s-expr: bad token at {pos}")
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(m.group(3).replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(m.group(4))
    return cur[0] if cur else []


def kids(node, tag):
    return [k for k in node[1:] if isinstance(k, list) and k and k[0] == tag]


def kid(node, tag):
    ks = kids(node, tag)
    return ks[0] if ks else None


def atom(node, tag, default=None):
    k = kid(node, tag)
    return k[1] if k and len(k) > 1 else default


# ------------------------------------------------------------------ values

_SI = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3,
       "K": 1e3, "M": 1e6, "R": 1.0, "r": 1.0, "G": 1e9}
_VAL = re.compile(r"(\d+(?:\.\d+)?)\s*([pnuµmkKMRrG]?)(\d*)")


def parse_value(text: str | None) -> float | None:
    """'5.1k' / '5k1' / '2u2' / '100nF' / '10uH' / '0R' -> SI float."""
    if not text:
        return None
    m = _VAL.search(str(text).replace(",", "."))
    if not m:
        return None
    whole, pre, frac = m.groups()
    mult = _SI.get(pre, 1.0)
    num = float(f"{whole}.{frac}") if frac and "." not in whole else float(whole)
    return num * mult


# ------------------------------------------------------------------- board

def _pick(kdir: Path, suffix: str) -> Path | None:
    cands = [p for p in kdir.glob(f"*{suffix}")
             if not any(s in p.name.lower() for s in ("backup", "-bak", "_bak"))]
    if not cands:
        return None
    # the one named after its project, else the newest
    pro = list(kdir.glob("*.kicad_pro"))
    for p in cands:
        if pro and p.stem == pro[0].stem:
            return p
    return max(cands, key=lambda p: p.stat().st_mtime)


def find_kicad(ws: Path) -> Path | None:
    """The workspace's kicad/ dir (either arm's layout) or ws itself."""
    for d in (ws / "kicad", ws):
        if d.is_dir() and list(d.glob("*.kicad_sch")):
            return d
    for d in sorted(ws.rglob("kicad")):
        if d.is_dir() and not SKIP_DIRS & set(d.relative_to(ws).parts) \
                and list(d.glob("*.kicad_sch")):
            return d
    return None


def kicad_cli() -> str:
    return (os.environ.get("HWDE_KICAD_CLI") or shutil.which("kicad-cli")
            or str(Path.home() / ".local/kicad10/bin/kicad-cli"))


def _cli(args: list[str], timeout=300) -> subprocess.CompletedProcess:
    return subprocess.run([kicad_cli(), *args], capture_output=True,
                          text=True, timeout=timeout)


def load_netlist(sch: Path, tmp: Path) -> dict:
    """Export the schematic's netlist with kicad-cli and parse it.

    -> {comps: {ref: {value, footprint, fields, lib}},
        nets: {name: [(ref, pin, pinfunction, pintype)]},
        pin_net: {(ref, pin): name}}"""
    out = tmp / "board.net"
    r = _cli(["sch", "export", "netlist", "--format", "kicadsexpr",
              "-o", str(out), str(sch)])
    if r.returncode != 0 or not out.is_file():
        raise BoardError(f"netlist export failed: {(r.stderr or r.stdout)[-400:]}")
    root = sexpr(out.read_text(encoding="utf-8"))
    comps = {}
    for c in kids(kid(root, "components") or ["components"], "comp"):
        fields = {}
        # (field (name "X") "value")
        for f in kids(kid(c, "fields") or ["fields"], "field"):
            nm = atom(f, "name")
            if nm is not None:
                fields[nm] = next((x for x in f[1:] if isinstance(x, str)), "")
        ls = kid(c, "libsource")
        comps[atom(c, "ref")] = {
            "value": atom(c, "value", ""), "footprint": atom(c, "footprint", ""),
            "fields": fields,
            "lib": (atom(ls, "part", "") if ls else "")}
    nets, pin_net = {}, {}
    for n in kids(kid(root, "nets") or ["nets"], "net"):
        name = atom(n, "name", "")
        nodes = []
        for nd in kids(n, "node"):
            ref, pin = atom(nd, "ref"), atom(nd, "pin")
            # KiCad 10 writes a pin's function as <name>_<number>
            func = re.sub(rf"_{re.escape(pin)}$", "",
                          atom(nd, "pinfunction", "") or "")
            nodes.append((ref, pin, func, atom(nd, "pintype", "") or ""))
            pin_net[(ref, pin)] = name
        nets[name] = nodes
    return {"comps": comps, "nets": nets, "pin_net": pin_net}


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def load_pcb(path: Path) -> dict:
    """.kicad_pcb -> {fps: {ref: {x, y, layer, value, pads: {num: [pad]}}},
    tracks: [{net, width, len, layer}], vias: [{x, y, net}],
    zones: [{net, layers}], nets: {code: name}}.  A pad is
    {x, y, net, w, h, type} in board coordinates (mm)."""
    root = sexpr(path.read_text(encoding="utf-8"))
    nets = {k[1]: k[2] for k in kids(root, "net") if len(k) > 2}

    def netname(node):
        k = kid(node, "net")
        if not k or len(k) < 2:
            return ""
        # KiCad 10 writes (net "name"); older (net 3 "name")
        return k[2] if len(k) > 2 else nets.get(k[1], k[1])

    fps = {}
    for fp in kids(root, "footprint"):
        at = kid(fp, "at") or ["at", "0", "0"]
        fx, fy = float(at[1]), float(at[2])
        frot = float(at[3]) if len(at) > 3 else 0.0
        ref = value = ""
        for p in kids(fp, "property"):
            if p[1] == "Reference":
                ref = p[2]
            elif p[1] == "Value":
                value = p[2]
        for t in kids(fp, "fp_text"):
            if t[1] == "reference" and not ref:
                ref = t[2]
        pads = {}
        for pd in kids(fp, "pad"):
            pat = kid(pd, "at") or ["at", "0", "0"]
            # pad (at) angle is absolute in KiCad; position is rotated by fp
            dx, dy = _rot(float(pat[1]), float(pat[2]), -frot)
            size = kid(pd, "size") or ["size", "0", "0"]
            pads.setdefault(pd[1], []).append({
                "x": fx + dx, "y": fy + dy, "net": netname(pd),
                "w": float(size[1]), "h": float(size[2]), "type": pd[2]})
        fps[ref] = {"x": fx, "y": fy, "layer": atom(fp, "layer", "F.Cu"),
                    "value": value, "pads": pads}
    tracks = []
    for s in kids(root, "segment"):
        a, b = kid(s, "start"), kid(s, "end")
        tracks.append({"net": netname(s), "width": float(atom(s, "width", 0)),
                       "layer": atom(s, "layer", ""),
                       "len": math.dist((float(a[1]), float(a[2])),
                                        (float(b[1]), float(b[2])))})
    for s in kids(root, "arc"):
        tracks.append({"net": netname(s), "width": float(atom(s, "width", 0)),
                       "layer": atom(s, "layer", ""), "len": 0.0})
    vias = []
    for v in kids(root, "via"):
        at = kid(v, "at")
        vias.append({"x": float(at[1]), "y": float(at[2]), "net": netname(v)})
    zones = []
    for z in kids(root, "zone"):
        layers = kid(z, "layers")
        zl = list(layers[1:]) if layers else [atom(z, "layer", "")]
        zones.append({"net": atom(z, "net_name", "") or netname(z),
                      "layers": zl})
    return {"fps": fps, "tracks": tracks, "vias": vias, "zones": zones}


class Board:
    """One workspace's netlist + PCB, with the lookups the checks share."""

    def __init__(self, nl: dict, pcb: dict | None):
        self.comps, self.nets, self.pin_net = nl["comps"], nl["nets"], nl["pin_net"]
        self.pcb = pcb
        self.gnd = next((n for n in self.nets
                         if re.fullmatch(r"/?(GND|PGND|AGND|0|VSS)", n)), "GND")

    def find_ic(self, pattern: str) -> str | None:
        rx = re.compile(pattern, re.I)
        for ref, c in sorted(self.comps.items()):
            text = " ".join([c["value"], c["lib"], *c["fields"].values()])
            if rx.search(text):
                return ref
        return None

    def find_by_funcs(self, prefix: str, funcs: list[str]) -> str | None:
        """First part with ref prefix whose pin functions match every regex."""
        for ref in sorted(self.comps):
            if not ref.startswith(prefix):
                continue
            names = [f for f, _ in self.pins(ref)]
            if all(any(re.fullmatch(rx, n, re.I) for n in names) for rx in funcs):
                return ref
        return None

    def pins(self, ref: str) -> list[tuple[str, str]]:
        """[(function, pin)] of one part."""
        return [(f, p) for nodes in self.nets.values()
                for r, p, f, _ in nodes if r == ref]

    def pins_by_func(self, ref: str, rx: str) -> list[str]:
        return [p for f, p in self.pins(ref) if re.fullmatch(rx, f, re.I)]

    def net(self, ref: str, pin: str) -> str | None:
        n = self.pin_net.get((ref, pin))
        return None if n is None or self.floating(n) else n

    def floating(self, net: str) -> bool:
        return net.startswith("unconnected-") or len(self.nets.get(net, [])) < 2

    def two_pin(self, ref: str) -> tuple[str, str] | None:
        ns = [n for (r, _), n in sorted(self.pin_net.items()) if r == ref]
        return (ns[0], ns[1]) if len(ns) == 2 else None

    def passives(self, prefix: str, a: str, b: str | None = None) -> list[tuple]:
        """[(ref, value_si, other_net)] two-pin parts with ref prefix on net a
        (and on net b when given)."""
        out = []
        for ref, c in self.comps.items():
            if not re.fullmatch(rf"{prefix}\d+", ref):
                continue
            tp = self.two_pin(ref)
            if not tp or a not in tp:
                continue
            other = tp[1] if tp[0] == a else tp[0]
            if b is not None and other != b:
                continue
            out.append((ref, parse_value(c["value"]), other))
        return out

    def caps(self, a: str, b: str) -> list[tuple]:
        return self.passives("C", a, b)

    def pad_xys(self, ref: str, pin: str) -> list[tuple[float, float]]:
        """Every pad of one pin (a SOT-223 tab is a second pad 2)."""
        fp = (self.pcb or {}).get("fps", {}).get(ref)
        return [(p["x"], p["y"]) for p in (fp["pads"].get(pin, []) if fp else [])]

    def dist_to(self, ref: str, pin: str, cap_ref: str, net: str) -> float | None:
        """mm, centre to centre, from one IC pin's pads to the cap's pad on
        the same net."""
        a = self.pad_xys(ref, pin)
        fp = (self.pcb or {}).get("fps", {}).get(cap_ref)
        if not a or not fp:
            return None
        ds = [math.dist(xy, (p["x"], p["y"])) for xy in a
              for ps in fp["pads"].values()
              for p in ps if p["net"].lstrip("/") == net.lstrip("/")]
        return min(ds) if ds else None


# ------------------------------------------------------------------ scores

def chk(cid: str, group: str, score: float | None, detail: str, **kw) -> dict:
    s = None if score is None else round(max(0.0, min(1.0, score)), 4)
    return {"id": cid, "group": group, "score": s, "detail": detail, **kw}


def band(v: float | None, lo: float, hi: float, decades: float = 0.5):
    """1 inside [lo, hi]; falls to 0 at `decades` (log10) outside."""
    if v is None or v <= 0:
        return 0.0
    if lo <= v <= hi:
        return 1.0
    d = math.log10(lo / v) if v < lo else math.log10(v / hi)
    return max(0.0, 1 - d / decades)


def at_most(v: float | None, limit: float, zero_at: float) -> float | None:
    """1 at or under limit, linear to 0 at zero_at."""
    if v is None:
        return None
    if v <= limit:
        return 1.0
    return max(0.0, 1 - (v - limit) / (zero_at - limit))


def ipc_width_mm(amps: float, rise_c: float = 10.0, oz: float = 1.0) -> float:
    """External-layer width for a current: the IPC-2221 fit to the IPC-2152
    external-conductor chart (I = 0.048 dT^0.44 A^0.725, A in mil^2)."""
    area = (amps / (0.048 * rise_c ** 0.44)) ** (1 / 0.725)
    return area / (1.378 * oz) * 0.0254


def check_width(b: Board, net: str | None, amps: float, cid: str) -> dict:
    if not net or not b.pcb:
        return chk(cid, "power", None, "no PCB or net")
    need = ipc_width_mm(amps)
    zone = any(z["net"].lstrip("/") == net.lstrip("/") for z in b.pcb["zones"])
    # a neck-down into a pad under 1 mm long is not the conductor
    ws = [t["width"] for t in b.pcb["tracks"]
          if t["net"].lstrip("/") == net.lstrip("/") and t["len"] >= 1.0]
    if not ws:
        return chk(cid, "power", 1.0 if zone else None,
                   f"{net}: {'pour only' if zone else 'no tracks'}")
    w = min(ws)
    return chk(cid, "power", 1.0 if zone and w >= need / 2 else w / need,
               f"{net}: narrowest {w:.2f} mm, {amps:g} A needs {need:.2f} mm"
               f"{' (net also poured)' if zone else ''}", net=net)


def check_decap(b: Board, ic: str, pin: str, net: str | None, cid: str,
                lo: float, hi: float, max_mm: float, gnd=None) -> list[dict]:
    """A cap of lo..hi farads from this pin's net to ground, and its
    distance on the PCB.  -> [connectivity check, placement check]."""
    gnd = gnd or b.gnd
    if not net:
        return [chk(cid, "connectivity", 0.0, f"{ic}.{pin} floats"),
                chk(cid + "_dist", "placement", 0.0, "no net")]
    caps = [c for c in b.caps(net, gnd) if c[1] and lo <= c[1] <= hi]
    if not caps:
        have = [f"{r}={v:g}" for r, v, _ in b.caps(net, gnd)]
        return [chk(cid, "connectivity", 0.0,
                    f"{ic}.{pin} ({net}): no {lo:g}..{hi:g} F cap to {gnd}"
                    f" (has {have or 'none'})", net=net),
                chk(cid + "_dist", "placement", 0.0, "no decoupling cap")]
    ds = [(b.dist_to(ic, pin, r, net), r) for r, _, _ in caps]
    ds = [d for d in ds if d[0] is not None]
    conn = chk(cid, "connectivity", 1.0, f"{ic}.{pin}: {caps[0][0]}", net=net)
    if not ds:
        return [conn, chk(cid + "_dist", "placement", None, "not on PCB")]
    d, r = min(ds)
    return [conn, chk(cid + "_dist", "placement", at_most(d, max_mm, 3 * max_mm),
                      f"{r} {d:.1f} mm from {ic}.{pin} (max {max_mm:g})",
                      refs=[ic, r])]


# ----------------------------------------------------------------- ngspice

_NG = {}


def ngspice(deck: str) -> dict[str, float] | None:
    """Run one deck in the shared-library ngspice; -> {measure: value}, or
    None when no ngspice library is on this host."""
    lib_path = os.environ.get("HWDE_NGSPICE_DLL") or "libngspice.so.0"
    if "lib" not in _NG:
        try:
            lib = ctypes.CDLL(lib_path)
        except OSError:
            return None
        out = []
        char_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                   ctypes.c_void_p)(
            lambda s, i, p: out.append(s.decode(errors="replace")) or 0)
        stat_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                   ctypes.c_void_p)(lambda s, i, p: 0)
        exit_cb = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool,
                                   ctypes.c_bool, ctypes.c_int,
                                   ctypes.c_void_p)(lambda *a: 0)
        lib.ngSpice_Init(char_cb, stat_cb, exit_cb, None, None, None, None)
        _NG.update(lib=lib, out=out, keep=(char_cb, stat_cb, exit_cb))
    lib, out = _NG["lib"], _NG["out"]
    out.clear()
    lines = [ln.encode() for ln in deck.strip().splitlines()]
    if lines[-1].strip().lower() != b".end":
        lines.append(b".end")
    arr = (ctypes.c_char_p * (len(lines) + 1))(*lines, None)
    lib.ngSpice_Circ(arr)
    lib.ngSpice_Command(b"run")
    lib.ngSpice_Command(b"remcirc")
    meas = {}
    for ln in out:
        m = re.match(r"stdout\s+(\w+)\s*=\s*([-+0-9.eE]+)", ln)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
    return meas


def lc_deck(b: Board, out_p: str, out_n: str, load_ohm: float):
    """The output filter the board has between one bridge's two outputs and
    its speaker, as an AC deck.  -> (deck, speaker nets) or None."""
    spk = []
    parts = {}
    for o in (out_p, out_n):
        ls = [p for p in b.passives("L", o) if p[2] != b.gnd]
        if len(ls) != 1:
            return None
        parts[ls[0][0]] = ls[0]
        spk.append(ls[0][2])
    # everything two-pin hanging off the speaker nets, one net deep
    frontier, seen = set(spk), set(spk) | {out_p, out_n, b.gnd}
    for _ in range(2):
        nxt = set()
        for n in frontier:
            for pre in ("C", "R", "L"):
                for ref, v, other in b.passives(pre, n):
                    if ref in parts or v is None:
                        continue
                    parts[ref] = (ref, v, other)
                    if other not in seen:
                        nxt.add(other)
                        seen.add(other)
        frontier = nxt
    names = {b.gnd: "0", out_p: "op", out_n: "on", spk[0]: "sp", spk[1]: "sn"}
    node = lambda n: names.setdefault(n, f"n{len(names)}")
    lines = ["* output LC filter", "V1 op 0 AC 0.5", "V2 on 0 AC 0.5 180"]
    for ref, v, _ in parts.values():
        a, c = b.two_pin(ref)
        if ref[0] == "R" and v == 0:
            v = 1e-3
        lines.append(f"{ref[0]}{ref} {node(a)} {node(c)} {v:.6g}")
    # ngspice's .meas takes no differential vector: E copies sp-sn to d
    lines += [f"RLOAD sp sn {load_ohm:g}", "EDIFF d 0 sp sn 1",
              ".ac dec 100 100 10meg",
              ".meas ac f3db when vdb(d)=-3 fall=1",
              ".meas ac peak max vdb(d)", ".end"]
    return "\n".join(lines), spk


# ------------------------------------------------------------------- gates

def gates(sch: Path, pcb: Path | None, tmp: Path) -> tuple[float, list[dict]]:
    """ERC + DRC errors by kicad-cli -> (factor on E, checks)."""
    out, errors = [], 0
    runs = [("erc", ["sch", "erc", "--format", "json", "--severity-error",
                     "-o", str(tmp / "erc.json"), str(sch)], tmp / "erc.json")]
    if pcb:
        runs.append(("drc", ["pcb", "drc", "--format", "json",
                             "--severity-error", "-o", str(tmp / "drc.json"),
                             str(pcb)], tmp / "drc.json"))
    else:
        out.append(chk("drc", "gate", 0.0, "no PCB"))
        errors += 10
    for cid, args, path in runs:
        r = _cli(args)
        if not path.is_file():
            out.append(chk(cid, "gate", None,
                           f"kicad-cli failed: {(r.stderr or r.stdout)[-200:]}"))
            continue
        rep = json.loads(path.read_text(encoding="utf-8"))
        if cid == "erc":
            vs = [v for s in rep.get("sheets", []) for v in s.get("violations", [])]
        else:
            vs = rep.get("violations", []) + rep.get("unconnected_items", [])
        vs = [v for v in vs if v.get("severity", "error") == "error"]
        kinds = sorted({v.get("type", "?") for v in vs})
        errors += len(vs)
        out.append(chk(cid, "gate", 1.0 if not vs else 0.0,
                       f"{len(vs)} errors {kinds[:6]}", count=len(vs)))
    return max(0.0, 1 - GATE_STEP * errors), out


# ----------------------------------------------------------- the briefs

def _first(rows: list[dict], text: str) -> dict:
    return next(r for r in rows if re.search(r["match"], text, re.I))


def score_usbc_ldo(b: Board, ka: dict) -> list[dict]:
    op, px = ka["operating"], ka["pins"]
    out = []
    j = b.find_by_funcs("J", [rf".*({px['cc1']}).*", rf".*({px['cc2']}).*"])
    u = b.find_by_funcs("U", [rf"({px['ldo_vin']})", rf"({px['ldo_vout']})"])
    if not j:
        out.append(chk("usbc_connector", "connectivity", 0.0,
                       "no USB-C receptacle with CC1/CC2 pins"))
    if not u:
        out.append(chk("ldo", "connectivity", 0.0, "no regulator with VIN/VOUT"))
    vbus = None
    if j:
        lo, hi = ka["cc_rd_ohm"]
        cc_nets = []
        for cc in ("cc1", "cc2"):
            ps = b.pins_by_func(j, rf".*({px[cc]}).*")
            net = b.net(j, ps[0]) if ps else None
            cc_nets.append(net)
            rd = [r for r in b.passives("R", net, b.gnd)] if net else []
            ok = [r for r in rd if r[1] and lo <= r[1] <= hi]
            out.append(chk(f"{cc}_rd", "connectivity", 1.0 if ok else 0.0,
                           f"{j}.{cc.upper()} ({net}): "
                           + (f"{ok[0][0]} {ok[0][1]:g} ohm to GND" if ok else
                              f"no 5.1k to GND (has {[(r, v) for r, v, _ in rd]})")))
        if cc_nets[0] and cc_nets[0] == cc_nets[1]:
            out.append(chk("cc_separate", "connectivity", 0.0,
                           "CC1 and CC2 share one net: a C-to-C source sees one Rd"))
        vb = {b.pin_net.get((j, p)) for p in b.pins_by_func(j, rf"({px['vbus']}).*")}
        vbus = next(iter(vb)) if len(vb) == 1 else None
        out.append(chk("vbus_pins", "connectivity", 1.0 if vbus and not b.floating(vbus)
                       else 0.0, f"VBUS pins on {sorted(map(str, vb))}"))
        gp = {b.pin_net.get((j, p)) for p in b.pins_by_func(j, r"GND.*")}
        out.append(chk("usbc_gnd", "connectivity", 1.0 if gp == {b.gnd} else 0.0,
                       f"receptacle GND pins on {sorted(map(str, gp))}"))
    if not u:
        return out
    c = b.comps[u]
    text = " ".join([c["value"], c["lib"], *c["fields"].values()])
    spec = _first(ka["ldos"], text)
    vin_p = b.pins_by_func(u, rf"({px['ldo_vin']})")
    vout_p = b.pins_by_func(u, rf"({px['ldo_vout']})")
    gnd_p = b.pins_by_func(u, rf"({px['ldo_gnd']})")
    vin = b.net(u, vin_p[0])
    vout = b.net(u, vout_p[0])
    out.append(chk("ldo_vin", "connectivity",
                   1.0 if vin and (vbus is None or vin == vbus) else 0.0,
                   f"{u} VIN on {vin}, VBUS is {vbus}"))
    out.append(chk("ldo_vout", "connectivity",
                   1.0 if vout and all(b.net(u, p) == vout for p in vout_p) else 0.0,
                   f"{u} VOUT on {vout}"))
    out.append(chk("ldo_gnd", "connectivity",
                   1.0 if gnd_p and all(b.net(u, p) == b.gnd for p in gnd_p) else 0.0,
                   f"{u} GND pins {gnd_p}"))
    for p in b.pins_by_func(u, rf"({px['ldo_en']})"):
        en = b.net(u, p)
        pulled = en == vin or any(o == vin for _, _, o in b.passives("R", en or "-"))
        out.append(chk("ldo_en", "connectivity", 1.0 if pulled else 0.0,
                       f"{u}.EN on {en}: {'tied high' if pulled else 'not tied to VIN'}"))
    floating = [f for f, p in b.pins(u) if not b.net(u, p)
                and not re.fullmatch(r"NC|N/C|DNC", f, re.I)]
    out.append(chk("ldo_floating", "connectivity", 0.0 if floating else 1.0,
                   f"floating pins {floating}" if floating else "no floating pins"))
    hdr = [r for r in b.comps if r.startswith("J") and r != j
           and {vbus, vout, b.gnd} <= {b.pin_net.get((r, p)) for f, p in b.pins(r)}]
    out.append(chk("header_rails", "connectivity", 1.0 if hdr else 0.0,
                   f"header with 5V/3V3/GND: {hdr or 'none'}"))
    # values: the datasheet's stability minimum
    for side, net, need in (("cin", vin, spec["cin_min_uf"]),
                            ("cout", vout, spec["cout_min_uf"])):
        tot = sum(v for _, v, _ in b.caps(net, b.gnd) if v) if net else 0
        out.append(chk(f"ldo_{side}", "values",
                       min(1.0, tot / (need * 1e-6)) if need else 1.0,
                       f"{u} {side} {tot * 1e6:.3g} uF, datasheet asks >= {need:g} uF"))
    # power: dissipation against the package, current, dropout
    theta = _first(ka["theta_ja"], c["footprint"])["c_per_w"]
    pdiss = (op["vin_max"] - op["vout"]) * op["iout_a"]
    tj = op["t_ambient_c"] + pdiss * theta
    out.append(chk("ldo_tj", "power", at_most(tj, op["tj_max_c"], op["tj_max_c"] + 25),
                   f"{pdiss:.2f} W in {c['footprint'].split(':')[-1]} "
                   f"({theta} C/W) -> Tj {tj:.0f} C (max {op['tj_max_c']})"))
    if spec["iout_max_a"]:
        out.append(chk("ldo_current", "power",
                       min(1.0, spec["iout_max_a"] / op["iout_a"]),
                       f"{c['value']} rated {spec['iout_max_a']} A for {op['iout_a']} A"))
    head = op["vin_min"] - op["vout"]
    out.append(chk("ldo_dropout", "power", min(1.0, head / spec["dropout_v"]),
                   f"{head:.2f} V headroom, dropout {spec['dropout_v']} V"))
    out.append(check_width(b, vbus or vin, ka["trace_a"]["vbus"], "width_vbus"))
    out.append(check_width(b, vout, ka["trace_a"]["vout"], "width_vout"))
    # placement: the in/out caps at the regulator's pins
    for side, pin, net in (("cin", vin_p[0], vin), ("cout", vout_p[0], vout)):
        caps = b.caps(net, b.gnd) if net else []
        ds = [(b.dist_to(u, pin, r, net), r) for r, _, _ in caps]
        ds = [d for d in ds if d[0] is not None]
        d = min(ds) if ds else None
        out.append(chk(f"ldo_{side}_dist", "placement",
                       at_most(d[0], ka["decap_max_mm"], 3 * ka["decap_max_mm"])
                       if d else (None if not b.pcb else 0.0),
                       f"{d[1]} {d[0]:.1f} mm from {u}.{pin}" if d else "no cap placed"))
    return out


def _gain_row(b: Board, u: str, ka: dict):
    gnet, gvdd = b.net(u, ka["pins"]["gain"]), b.net(u, ka["pins"]["gvdd"])
    if not gnet:
        return None, "GAIN floats"
    r1 = [v for _, v, o in b.passives("R", gnet) if o == b.gnd]
    r2 = [v for _, v, o in b.passives("R", gnet) if o == gvdd]
    r1v, r2v = (r1[0] if r1 else None), (r2[0] if r2 else None)
    if gnet == b.gnd:
        return None, "GAIN tied straight to GND"
    tol = ka["gain_tol"]
    near = lambda a, e: (a is None and e is None) or (
        a is not None and e is not None and abs(a - e) <= tol * e)
    for row in ka["gain_table"]:
        if near(r1v, row["r1"]) and near(r2v, row["r2"]):
            return row, f"R1={r1v} R2={r2v}: {row['db']} dB {row['mode']}"
    return None, f"R1={r1v} R2={r2v} matches no datasheet gain row"


def score_stereo_amp(b: Board, ka: dict) -> list[dict]:
    px, cf, dm = ka["pins"], ka["caps_f"], ka["decap_max_mm"]
    u = b.find_ic(ka["chip"])
    if not u:
        return [chk("amp", "connectivity", 0.0, "no TPA3116D2/TPA3118D2")]
    out = []
    pv = [b.net(u, p) for pair in px["pvcc"] for p in pair]
    rail = pv[0]
    out.append(chk("pvcc_rail", "connectivity",
                   1.0 if rail and all(n == rail for n in pv) else 0.0,
                   f"PVCC pins on {sorted(set(map(str, pv)))}"))
    for i, pair in enumerate(px["pvcc"]):
        out += check_decap(b, u, pair[0], b.net(u, pair[0]), f"pvcc{i}_bypass",
                           *cf["pvcc_bypass"], dm["pvcc_bypass"])
    bulk = sum(v for _, v, _ in b.caps(rail, b.gnd) if v) if rail else 0
    out.append(chk("pvcc_bulk", "values", min(1.0, bulk / cf["pvcc_bulk_min"]),
                   f"{bulk * 1e6:.0f} uF on {rail}"))
    out += check_decap(b, u, px["gvdd"], b.net(u, px["gvdd"]), "gvdd",
                       *cf["gvdd"], dm["gvdd"])
    out += check_decap(b, u, px["avcc"], b.net(u, px["avcc"]), "avcc",
                       *cf["avcc"], dm["avcc"])
    gp = [p for p in px["gnd"] if b.net(u, p) != b.gnd]
    out.append(chk("gnd_pins", "connectivity", 0.0 if gp else 1.0,
                   f"GND pins off ground: {gp}" if gp else "GND pins grounded"))
    for bs, o in px["bootstrap"]:
        nb, no = b.net(u, bs), b.net(u, o)
        cs = [c for c in b.caps(nb, no) if c[1]] if nb and no else []
        ok = [c for c in cs if cf["bootstrap"][0] <= c[1] <= cf["bootstrap"][1]]
        out.append(chk(f"bootstrap_{bs}", "connectivity", 1.0 if ok else 0.0,
                       f"BS pin {bs} to OUT pin {o}: "
                       + (f"{ok[0][0]} {ok[0][1]:g} F" if ok else f"{cs or 'no cap'}")))
        d = b.dist_to(u, bs, ok[0][0], nb) if ok else None
        out.append(chk(f"bootstrap_{bs}_dist", "placement",
                       at_most(d, dm["bootstrap"], 3 * dm["bootstrap"])
                       if ok else 0.0, f"{d and round(d, 1)} mm"))
    row, why = _gain_row(b, u, ka)
    out.append(chk("gain_strap", "connectivity", 1.0 if row else 0.0, why))
    # strap pins that must be driven, and to a state that plays
    def strap(name, ok_gnd, ok_high):
        n = b.net(u, px[name])
        if not n:
            return chk(name, "connectivity", 0.0, f"{name.upper()} floats")
        conn = n not in (b.gnd, rail) and any(
            r.startswith("J") for r, *_ in b.nets[n])
        high = n == rail or n == b.net(u, px["gvdd"]) or any(
            o in (rail, b.net(u, px["gvdd"]), b.net(u, px["avcc"]))
            for _, _, o in b.passives("R", n))
        low = n == b.gnd or any(o == b.gnd for _, _, o in b.passives("R", n))
        good = conn or (high and ok_high) or (low and ok_gnd)
        state = "external" if conn else "high" if high else "low" if low else "undriven"
        return chk(name, "connectivity", 1.0 if good else 0.0,
                   f"{name.upper()} on {n}: {state}")
    out.append(strap("sdz", ok_gnd=False, ok_high=True))    # low = shutdown
    out.append(strap("mute", ok_gnd=True, ok_high=False))   # high = muted
    out.append(strap("modsel", ok_gnd=True, ok_high=True))
    out.append(strap("plimit", ok_gnd=True, ok_high=True))
    am = [b.net(u, p) for p in px["am"]]
    out.append(chk("am_pins", "connectivity", 1.0 if all(am) else 0.0,
                   f"AM0-2 on {am}"))
    # input coupling: a series cap on every input, corner below the band
    zi = row["zi"] if row else min(r["zi"] for r in ka["gain_table"])
    for name, p in px["inputs"].items():
        n = b.net(u, p)
        cs = [c for c in b.passives("C", n) if c[1]] if n else []
        if not cs:
            out.append(chk(f"in_{name}", "values", 0.0, f"{name}: no coupling cap"))
            continue
        fc = 1 / (2 * math.pi * zi * max(c[1] for c in cs))
        out.append(chk(f"in_{name}", "values",
                       at_most(fc, ka["input_hp_hz_max"], 4 * ka["input_hp_hz_max"]),
                       f"{name}: {cs[0][0]} x Zi {zi / 1e3:g}k -> {fc:.1f} Hz"))
    # output LC filter, simulated
    for side, (op_, on_) in px["bridges"].items():
        np_, nn = b.net(u, op_), b.net(u, on_)
        built = lc_deck(b, np_, nn, ka["load_ohm"]) if np_ and nn else None
        if not built:
            out.append(chk(f"lc_{side}", "values", 0.0,
                           f"{side}: no series inductor on each output"))
            continue
        meas = ngspice(built[0])
        if meas is None:
            out.append(chk(f"lc_{side}", "values", None, "no ngspice on this host"))
            continue
        f3, pk = meas.get("f3db"), meas.get("peak")
        lo, hi = ka["lc_cutoff_hz"]
        s = band(f3, lo, hi) if f3 else 0.0
        if pk is not None and pk > ka["lc_peak_db_max"]:
            s *= 0.5
        out.append(chk(f"lc_{side}", "values", s,
                       f"{side}: -3 dB at {f3 and round(f3)} Hz, peak "
                       f"{pk and round(pk, 1)} dB into {ka['load_ohm']} ohm"))
        out.append(check_width(b, np_, ka["trace_a"]["out"], f"width_out_{side}"))
    out.append(check_width(b, rail, ka["trace_a"]["pvcc"], "width_pvcc"))
    # thermal: exposed pad vias (DAP) or a heatsink (DAD's pad is on top)
    fp = (b.pcb or {}).get("fps", {}).get(u)
    ep = [p for num, ps in (fp or {"pads": {}})["pads"].items() for p in ps
          if p["w"] > 2 and p["h"] > 2]
    if fp and ep:
        e = ep[0]
        # board vias plus the footprint's own via pads; the square on the
        # pad's longer side, so a rotated part needs no w/h swap
        holes = b.pcb["vias"] + [p for ps in fp["pads"].values() for p in ps
                                 if p["type"] == "thru_hole"]
        half = max(e["w"], e["h"]) / 2
        vias = [v for v in holes if abs(v["x"] - e["x"]) <= half
                and abs(v["y"] - e["y"]) <= half]
        out.append(chk("thermal_vias", "power",
                       min(1.0, len(vias) / ka["thermal_vias_min"]),
                       f"{len(vias)} vias in the exposed pad (min {ka['thermal_vias_min']})"))
    elif fp:
        sink = [r for r, c in b.comps.items()
                if re.search(r"heat\s*sink|HS\d", c["value"] + c["footprint"], re.I)]
        out.append(chk("thermal_vias", "power", 1.0 if sink else 0.0,
                       "top-side pad package: " + (f"heatsink {sink}" if sink else
                       "no exposed pad on the PCB and no heatsink part")))
    return out


BRIEFS = {"e2e_usbc_ldo": score_usbc_ldo, "e2e_stereo_amp": score_stereo_amp}


def load_answer(brief: str) -> dict:
    name = brief.removeprefix("e2e_")
    path = ANSWERS / f"{name}.yaml"
    if f"e2e_{name}" not in BRIEFS or not path.is_file():
        raise KeyError(f"no known-answer for {brief}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def aggregate(checks: list[dict], gate: float) -> tuple[float, float, dict, list]:
    """Checks + gate factor -> (E, E before the gate, group means, fatal ids).
    E = gate * min(weighted group mean, CRITICAL_CAP if a critical check is 0)."""
    groups = {}
    for g in GROUP_WEIGHTS:
        ss = [c["score"] for c in checks if c["group"] == g and c["score"] is not None]
        if ss:
            groups[g] = round(sum(ss) / len(ss), 4)
    wsum = sum(GROUP_WEIGHTS[g] for g in groups) or 1
    raw = sum(GROUP_WEIGHTS[g] * s for g, s in groups.items()) / wsum
    fatal = [c["id"] for c in checks
             if c["score"] == 0 and CRITICAL.fullmatch(c["id"])]
    if fatal:
        raw = min(raw, CRITICAL_CAP)
    return round(raw * gate, 4), round(raw, 4), groups, fatal


def score_workspace(brief: str, ws: Path, old: dict | None = None) -> dict:
    """One board -> {electrical, groups, gate, checks, composite}.  old is the
    bench.py E2E score (its layout and cost categories feed the composite)."""
    brief = brief if brief.startswith("e2e_") else f"e2e_{brief}"
    ka = load_answer(brief)
    kdir = find_kicad(ws)
    if not kdir:
        raise BoardError(f"no schematic under {ws}")
    sch, pcb = _pick(kdir, ".kicad_sch"), _pick(kdir, ".kicad_pcb")
    with tempfile.TemporaryDirectory(prefix="e2el-") as t:
        tmp = Path(t)
        b = Board(load_netlist(sch, tmp), load_pcb(pcb) if pcb else None)
        checks = BRIEFS[brief](b, ka)
        gate, gchecks = gates(sch, pcb, tmp)
    e, raw, groups, fatal = aggregate(checks, gate)
    cats = old_categories(old)
    comp = None
    if "layout" in cats and "cost" in cats:
        comp = round(100 * (WEIGHTS["electrical"] * e + WEIGHTS["layout"] * cats["layout"]
                            + WEIGHTS["cost"] * cats["cost"]), 2)
    return {"brief": brief, "workspace": str(ws), "electrical": e,
            "electrical_raw": round(raw, 4), "gate": round(gate, 4),
            "groups": groups, "fatal": fatal, "composite": comp,
            "checks": checks + gchecks}


def old_categories(old: dict | None) -> dict:
    """The old scorer's {electrical, layout, cost} from a run record or a
    bench.py score.json (whose penalties hold each category's shortfall)."""
    old = old or {}
    cats = old.get("categories") or (old.get("e2e") or {}).get("categories")
    if cats:
        return cats
    pen = old.get("penalties") or {}
    return {k.removesuffix("_shortfall"): round(1 - v, 4)
            for k, v in pen.items() if k.endswith("_shortfall")}


_RUN_DIR = re.compile(r"-(?P<brief>[a-z0-9_]+)-(?P<arm>bare|hwde)-s(?P<seed>\d+)$")


def run_targets(paths: list[Path]) -> list[dict]:
    """Run records (.jsonl lines) and run dirs (<stamp>-<brief>-<arm>-s<n>
    with a score.json) -> [{run_id, arm, fixture, workspace, old}]."""
    out = []
    for p in paths:
        if p.is_dir():
            m = _RUN_DIR.search(p.name)
            sc = p / "score.json"
            if not m or not sc.is_file():
                continue
            old = json.loads(sc.read_text(encoding="utf-8"))
            work = p / "work"
            ws = work / "board" if m["arm"] == "bare" else next(
                (k.parent for k in sorted((work / "boards").glob("*/kicad"))), None)
            out.append({"run_id": p.name, "arm": m["arm"],
                        "fixture": f"e2e_{m['brief']}", "workspace": ws,
                        "old": old})
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("kind") == "run" and r.get("workspace"):
                out.append({"run_id": r["run_id"], "arm": r["arm"],
                            "fixture": r["fixture"],
                            "workspace": Path(r["workspace"]), "old": r})
    return out


def rescore(paths: list[Path]) -> list[dict]:
    rows, seen = [], set()
    for t in run_targets(paths):
        if t["run_id"] in seen:
            continue
        seen.add(t["run_id"])
        row = {"run_id": t["run_id"], "arm": t["arm"], "fixture": t["fixture"],
               "old_composite": t["old"].get("composite"),
               "old_categories": old_categories(t["old"])}
        try:
            if not t["workspace"] or not Path(t["workspace"]).is_dir():
                raise BoardError("workspace gone")
            sc = score_workspace(t["fixture"], Path(t["workspace"]), t["old"])
        except (BoardError, KeyError) as exc:
            row["error"] = str(exc)
        else:
            row.update(electrical=sc["electrical"], gate=sc["gate"],
                       groups=sc["groups"], fatal=sc["fatal"],
                       composite=sc["composite"],
                       findings=[f"{c['id']}: {c['detail']}" for c in sc["checks"]
                                 if c["score"] is not None and c["score"] < 1])
        rows.append(row)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--brief")
    ap.add_argument("--workspace", type=Path)
    ap.add_argument("--old-score", type=Path,
                    help="bench.py --stage E2E score.json for layout and cost")
    ap.add_argument("--rescore", type=Path, nargs="+",
                    help="run records (.jsonl) and/or run dirs")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    try:
        if a.rescore:
            missing = [str(p) for p in a.rescore if not p.exists()]
            if missing:
                print(f"no such path {missing}", file=sys.stderr)
                return 2
            res = rescore(a.rescore)
        else:
            if not a.brief or not a.workspace or not a.workspace.is_dir():
                print("need --brief and an existing --workspace", file=sys.stderr)
                return 2
            old = (json.loads(a.old_score.read_text(encoding="utf-8"))
                   if a.old_score else None)
            res = score_workspace(a.brief, a.workspace, old)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (BoardError, subprocess.SubprocessError, OSError) as exc:
        print(f"cannot score: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(res, indent=1, ensure_ascii=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
