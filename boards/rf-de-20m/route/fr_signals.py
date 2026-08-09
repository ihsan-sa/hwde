"""rf-de-20m P7 - route the 10 remaining SIGNAL nets with Freerouting.

Both autorouters had failed on this board (route-notes s9). fr_spiral_probe.py
+ fr_wire_bisect.py found WHY Freerouting wedges, and it is not what anyone
guessed: not the spirals' 1116/828-point custom pads (v1/v2 still wedge), not
the r=20.55 mm keepout discs (v2), not the 160 pre-placed vias (v5 runs).

It is the PRE-ROUTED WIRES whose WIDTH is comparable to or greater than their
LENGTH. Drop the 9 highest-aspect ones (aspect >= 0.81) and Freerouting reads
the design in 1.5 s and finishes in 10 s; leave 7 of them in and it never gets
past the DSN reader. Those 9 are exactly the copper this board is made of:
the four pour fan-in land tracks that `remediations/track_width.md` mandates
(7.651 mm wide x 0.020 mm long is the extreme), and five short wide bars in
the U201 gate fan-out.

So the working recipe is:

  1. export the DSN;
  2. delete the 9 degenerate-aspect wires from it (they stay on the REAL
     board - the DSN is only the router's input);
  3. run Freerouting;
  4. FILTER the SES down to the nets that actually needed routing, because
     with those wires missing FR also "re-routes" nets that are already
     complete, and importing that would double the copper;
  5. import, refill, DRC, and keep the result only if unconnected fell and
     no new error kind appeared.

Usage: python fr_signals.py [--dry-run]
"""
import json
import math
import re
import shutil
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
import kc                                                          # noqa: E402
from lib import env, routelib                                      # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
WORK = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/fr3')
BUDGET = 600

# the nets with open connections at P7 (route-notes s9)
WANT = {'+5V', '+5V_DRV', '/hk/BUCK_SW', '/hk/FB', '/hk/RINJ', '/hk/RON',
        '/hk/VCC', '/hk/BST', '/stage/DRIVE', '/stage/L201_MID'}

WIRE_RE = re.compile(
    r'^\s*\(wire \(path (\S+) ([0-9.]+)\s+([-0-9.\s]+)\)\(net (\S+)\)')
ASPECT_CUT = 0.80          # drop wires with width/length >= this


def thin_dsn(text):
    """Remove wires whose width rivals their length - the FR reader jam."""
    keep, dropped = [], []
    for line in text.splitlines():
        m = WIRE_RE.match(line)
        if m:
            c = m.group(3).split()
            pts = [(float(c[k]), float(c[k + 1])) for k in range(0, len(c), 2)]
            ln = sum(math.dist(pts[k], pts[k + 1])
                     for k in range(len(pts) - 1))
            if not ln or float(m.group(2)) / ln >= ASPECT_CUT:
                dropped.append((m.group(4), float(m.group(2)), ln))
                continue
        keep.append(line)
    return '\n'.join(keep), dropped


def filter_ses(text, want):
    """Keep only (net X ...) blocks whose net is in `want`."""
    out, i, kept, skipped = [], 0, [], []
    pat = re.compile(r'\(net (\"[^\"]+\"|\S+)')
    while True:
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        depth, k = 0, m.start()
        while True:
            if text[k] == '(':
                depth += 1
            elif text[k] == ')':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        name = m.group(1).strip('"')
        if name in want:
            out.append(text[m.start():k + 1])
            kept.append(name)
        else:
            skipped.append(name)
        i = k + 1
    return ''.join(out), kept, skipped


DRU_RE = re.compile(
    r'\(rule\s+"[^"]*"\s*\(constraint clearance \(min ([0-9.]+)mm\)\)\s*'
    r'\(condition "A\.NetName == \'([^\']+)\'"\s*\)', re.S)


def rules_dru_floors(dru):
    """{net: max single-net clearance floor} from the .kicad_dru."""
    out = {}
    for m in DRU_RE.finditer(dru.read_text(encoding='utf-8')):
        net, mm_ = m.group(2), float(m.group(1))
        out[net] = max(out.get(net, 0.0), mm_)
    return out


def bump_class_clearances(pro, floors):
    """Raise each netclass's clearance to the max DRU floor of its members."""
    proj = json.loads(pro.read_text(encoding='utf-8'))
    ns = proj.get('net_settings') or {}
    pats = ns.get('netclass_patterns') or []
    want = {}
    for p in pats:
        f = floors.get(p.get('pattern'))
        if f:
            want[p['netclass']] = max(want.get(p['netclass'], 0.0), f)
    for c in ns.get('classes') or []:
        f = want.get(c.get('name'))
        if f and f > (c.get('clearance') or 0):
            c['clearance'] = f
    pro.write_text(json.dumps(proj, indent=2), encoding='utf-8')
    return want


def errs(rep):
    out = {}
    for v in rep['violations']:
        if v.get('severity') == 'error':
            out[v['check']] = out.get(v['check'], 0) + 1
    return out


def main():
    dry = '--dry-run' in sys.argv
    cli = env.find_kicad_cli()
    bp = env.find_kicad_python(cli)
    java, _ = env.find_java()
    jar = env.find_freerouting_jar()
    WORK.mkdir(parents=True, exist_ok=True)
    staged = WORK / PCB.name
    for src in PCB.parent.glob(PCB.stem + '.*'):
        if src.is_file() and not src.name.endswith('.lck'):
            shutil.copy2(src, WORK / src.name)
    shutil.copy2(PCB.parent / 'fp-lib-table', WORK / 'fp-lib-table')

    before = kc.run_drc(cli, staged, all_track_errors=True)
    b = errs(before)
    print('before:', b)

    # Freerouting reads clearances from the DSN, which KiCad writes from the
    # .kicad_pro NETCLASSES only - the per-net `aiee_hv_*` rules live in the
    # .kicad_dru and never reach it. Left alone, FR routes /hk/BST 0.26 mm
    # from a +40V pad (rule: 0.5) and +5V_DRV 0.62 mm from a /SW pad (0.8).
    #
    # --hv-clearance pushes the DRU floors into the STAGED project's classes.
    # MEASURED 2026-08-08: DOING SO RE-WEDGES THE DSN READER (0.5/0.8/0.8 on
    # the three Pwr classes -> no "Job started" line in 600 s), same failure
    # mode as the degenerate-aspect wires. So it is OFF by default and the
    # handful of HV-adjacent segments FR produces are fixed afterwards with
    # route_edit instead.
    if '--hv-clearance' in sys.argv:
        hv = rules_dru_floors(WORK / (PCB.stem + '.kicad_dru'))
        print('staged netclass clearances:',
              bump_class_clearances(WORK / (PCB.stem + '.kicad_pro'), hv))

    dsn = WORK / 'full.dsn'
    routelib.run_worker(bp, {'verb': 'export_dsn', 'board': str(staged),
                             'dsn': str(dsn),
                             # B.Cu is declared a PLANE too, not just the
                             # inner layers: it carries one 6002 mm2 GND
                             # island AND it is the heatsink mounting face
                             # (HS-2 - no signal copper, no untented via
                             # there). Left as signal, Freerouting put a
                             # +5V_DRV detour with two vias straight into the
                             # heatsink land, which would short to the sink.
                             'layer_types': {'In1.Cu': 'power',
                                             'In2.Cu': 'power',
                                             'B.Cu': 'power'}},
                        WORK, timeout=300)
    thin, dropped = thin_dsn(dsn.read_text(encoding='utf-8', errors='replace'))
    thin_dsn_path = WORK / 'thin.dsn'
    thin_dsn_path.write_text(thin, encoding='utf-8')
    print('dropped %d degenerate wires:' % len(dropped))
    for net, w, ln in dropped:
        print('   w %8.1f len %8.1f aspect %6.2f  %s'
              % (w, ln, w / ln if ln else 9e9, net))

    ses = WORK / 'thin.ses'
    ses.unlink(missing_ok=True)
    facts = routelib.run_freerouting(java, jar, thin_dsn_path, ses,
                                     rung={'mp': 30, 'oit': 0.05},
                                     timeout=BUDGET,
                                     log_file=WORK / 'fr.log')
    facts.pop('cmd', None)
    print('FR:', json.dumps(facts)[:300])
    if not facts.get('ses_written'):
        raise SystemExit('freerouting produced no session')

    filt, kept, skipped = filter_ses(ses.read_text(encoding='utf-8',
                                                   errors='replace'), WANT)
    ses_f = WORK / 'signals.ses'
    ses_f.write_text(filt, encoding='utf-8')
    print('SES kept nets:', sorted(set(kept)))
    print('SES dropped nets:', sorted(set(skipped)))
    if dry:
        return

    out = WORK / 'imported.kicad_pcb'
    r = routelib.run_worker(bp, {'verb': 'import_ses', 'board': str(staged),
                                 'ses': str(ses_f), 'out': str(out)},
                            WORK, timeout=300)
    print('import:', r)
    out.replace(staged)
    kc.run_drc(cli, staged, refill=True, save_board=True)
    after = kc.run_drc(cli, staged, all_track_errors=True)
    a = errs(after)
    print('after: ', a)
    delta = {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}
    print('delta: ', delta)
    (WORK / 'result.json').write_text(
        json.dumps({'before': b, 'after': a, 'delta': delta,
                    'fr': facts, 'dropped_wires': dropped,
                    'ses_nets_kept': sorted(set(kept))}, indent=1),
        encoding='utf-8')
    new_kinds = set(a) - set(b)
    if a.get('unconnected_items', 0) < b.get('unconnected_items', 0) \
            and not new_kinds:
        shutil.copy2(staged, PCB)
        print('KEPT: copied back to', PCB)
    else:
        print('NOT auto-kept: new kinds', new_kinds, 'delta', delta)


main()
