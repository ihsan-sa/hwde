"""Strip every (filled_polygon ...) block from a .kicad_pcb.

Workspace LEARNINGS 2026-08-08 [P7][kicad][swig]: a via added into an
ALREADY-FILLED zone takes the ZONE's net, non-deterministically. The reliable
procedure is: strip the fills, apply the ops on the bare board, then
`kicad-cli pcb drc --refill-zones --save-board`.
"""
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding='utf-8')
out, i, n = [], 0, 0
while True:
    j = t.find('(filled_polygon', i)
    if j < 0:
        out.append(t[i:])
        break
    out.append(t[i:j])
    depth, k = 0, j
    while True:
        c = t[k]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                k += 1
                break
        k += 1
    i = k
    n += 1
    while i < len(t) and t[i] in ' \t\r\n':
        i += 1
p.write_text(''.join(out), encoding='utf-8')
print(f'stripped {n} filled_polygon blocks from {p}')
