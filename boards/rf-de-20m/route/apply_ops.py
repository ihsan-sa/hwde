"""route_edit driver with a drop-and-retry loop.

route_edit is atomic: one op that does not survive the save rolls the whole
batch back.  A few of the bridge vias are rejected by pcbnew on save; rather
than guess at the cause, this parses the verify message, drops exactly those
ops and retries until the batch applies (or nothing is left).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PY = r'C:/dev/ai-ee3/.venv/Scripts/python.exe'
RE = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts/route_edit.py'
PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'

ops_path = Path(sys.argv[1])
report = sys.argv[2]
ops = json.loads(ops_path.read_text())['ops']
work = ops_path.with_suffix('.retry.json')

for attempt in range(8):
    work.write_text(json.dumps({"version": 1, "ops": ops}, indent=1))
    p = subprocess.run([PY, RE, '--pcb', PCB, '--ops', str(work),
                        '--out-report', report],
                       capture_output=True, text=True)
    out = (p.stdout or '') + (p.stderr or '')
    if p.returncode == 0 and '"status": "error"' not in out:
        print(f'applied {len(ops)} ops on attempt {attempt + 1}')
        sys.exit(0)
    bad = set()
    for m in re.finditer(r'ops\[(\d+)\]', out):
        bad.add(int(m.group(1)))
    if not bad:
        print(out[:800])
        sys.exit(1)
    print(f'attempt {attempt + 1}: dropping {len(bad)} rejected ops '
          f'{sorted(bad)[:12]}')
    ops = [o for i, o in enumerate(ops) if i not in bad]
    if not ops:
        print('nothing left to apply')
        sys.exit(1)
print('did not converge')
sys.exit(1)
