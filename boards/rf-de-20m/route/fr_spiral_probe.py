"""rf-de-20m P7 - test WHY Freerouting wedges on this design.

Hypothesis handed down by the orchestrator: the two spiral footprints carry
1116 / 828-point custom pad polygons, and ~2000 pad-outline vertices jam the
DSN reader.

This exports a fresh DSN, then builds variants of it and runs Freerouting on
each with a short budget, so the wedge is bisected rather than guessed:

  v0  the DSN as exported                        (expected: wedge)
  v1  the two spiral winding padstacks reduced   (hypothesis under test)
      to their 2.8 x 8.0 mm terminal land rect
  v2  v1 + the four r=20.3/20.55 mm keepout      (control: the OTHER big
      polygons dropped                            polygon in the file)

RESULT: v1 and v2 both still wedge, so the spiral polygons are NOT the cause.
A JFR profile (fr.jfr / samples.txt) of the wedged run puts every hot sample
under `io.specctra.parser.Wiring.read_scope` -> ShapeSearchTree.insert ->
Simplex.intersects/remove_redundant_lines, so the second round bisects the
`(wiring)` scope instead:

  v3  wiring scope emptied                       (34 wires + 160 vias removed)
  v4  wiring: wires kept, the 160 vias dropped
  v5  wiring: vias kept, the 34 wires dropped
  v6  only the 4 FAT land tracks dropped         (width > 2 mm: the 11.894 mm
                                                  /SW rung, the two 8.412 mm
                                                  tank lands, the 7.651 mm
                                                  RFOUT land)

RESULT 2: v3 and v5 both RUN to completion; v4 wedges.  So it is the WIRES,
and v6 narrows it to the four pour fan-in land tracks, whose width is 6x to
600x their length.

Usage:  python fr_spiral_probe.py [variant ...]     default: v0 v1 v2
"""
import json
import re
import shutil
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
from lib import env, routelib                                      # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
WORK = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/fr2')
BUDGET = 240

CUST = re.compile(
    r'\(padstack (Cust\[[TB]\]Pad_2800\.000000x8000\.000000_[^\s\)]+)\s*'
    r'\(shape \(polygon (\S+) 0(?:[^()]*)\)\)\s*\(attach off\)\s*\)',
    re.S)


def land_rect(m):
    """Replace a spiral winding pad outline with its terminal land rect."""
    return ('(padstack %s\n      (shape (rect %s -1400 -4000 1400 4000))\n'
            '      (attach off)\n    )' % (m.group(1), m.group(2)))


WIDTH_RE = re.compile(r'\(path \S+ ([0-9.]+)')


def strip_wiring(text, drop_wires, drop_vias, fat_only_um=None):
    i = text.find('(wiring')
    head, tail = text[:i], text[i:]
    out = []
    for line in tail.splitlines():
        s = line.strip()
        if s.startswith('(wire '):
            if fat_only_um is not None:
                m = WIDTH_RE.search(s)
                if m and float(m.group(1)) > fat_only_um:
                    continue
            elif drop_wires:
                continue
        if drop_vias and s.startswith('(via '):
            continue
        out.append(line)
    print('  wiring %d -> %d lines' % (len(tail.splitlines()), len(out)))
    return head + '\n'.join(out)


def variant(text, name):
    if name == 'v0':
        return text
    if name == 'v6':
        return strip_wiring(text, False, False, fat_only_um=2000.0)
    if name in ('v3', 'v4', 'v5'):
        return strip_wiring(text, name in ('v3', 'v5'), name in ('v3', 'v4'))
    text, n = CUST.subn(land_rect, text)
    if n != 4:
        raise SystemExit('expected 4 spiral padstacks, patched %d' % n)
    if name == 'v1':
        return text
    # v2: also drop the big polygon keepouts (leave the r=3.7 mm circles)
    out, i, dropped = [], 0, 0
    while True:
        j = text.find('(keepout "" (polygon', i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        depth, k = 0, j
        while True:
            if text[k] == '(':
                depth += 1
            elif text[k] == ')':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        i = k + 1
        dropped += 1
    print('  dropped %d polygon keepouts' % dropped)
    return ''.join(out)


def main():
    which = sys.argv[1:] or ['v0', 'v1', 'v2']
    cli = env.find_kicad_cli()
    bp = env.find_kicad_python(cli)
    java, _ = env.find_java()
    jar = env.find_freerouting_jar()
    WORK.mkdir(parents=True, exist_ok=True)
    staged = WORK / PCB.name
    for src in PCB.parent.glob(PCB.stem + '.*'):
        if src.is_file() and not src.name.endswith('.lck'):
            shutil.copy2(src, WORK / src.name)

    base = WORK / 'base.dsn'
    if not base.is_file():
        routelib.run_worker(bp, {'verb': 'export_dsn', 'board': str(staged),
                                 'dsn': str(base),
                                 'layer_types': {'In1.Cu': 'power',
                                                 'In2.Cu': 'power'}},
                            WORK, timeout=300)
    text = base.read_text(encoding='utf-8', errors='replace')

    facts = {}
    for name in which:
        print('===', name)
        dsn = WORK / ('%s.dsn' % name)
        dsn.write_text(variant(text, name), encoding='utf-8')
        ses = WORK / ('%s.ses' % name)
        ses.unlink(missing_ok=True)
        f = routelib.run_freerouting(java, jar, dsn, ses,
                                     rung={'mp': 6}, timeout=BUDGET,
                                     log_file=WORK / ('%s.log' % name))
        f.pop('cmd', None)
        facts[name] = f
        print(' ', json.dumps(f)[:400])
    tag = '-'.join(which)
    (WORK / ('probe-%s.json' % tag)).write_text(json.dumps(facts, indent=1),
                                                encoding='utf-8')


main()
