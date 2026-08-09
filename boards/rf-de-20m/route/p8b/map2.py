import sys
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
OX, OY = F.OX, F.OY
HOLE = float(sys.argv[1]); HEAD = float(sys.argv[2])
x0, x1, y0, y1, s = 18.0, 42.0, 11.0, 41.0, 0.2
hdr = '      '
i = 0
x = x0
while x <= x1 + 1e-9:
    hdr += (f'{int(x)%10}' if abs(x - round(x)) < 1e-9 and int(round(x)) % 2 == 0 else ' ')
    x += s
print(f'hole {HOLE} head {HEAD}  x {x0}..{x1} y {y0}..{y1} step {s}')
print(hdr)
y = y0
while y <= y1 + 1e-9:
    row = ''
    x = x0
    while x <= x1 + 1e-9:
        row += '.' if F.legal(x + OX, y + OY, HOLE, HEAD) else '#'
        x += s
    print(f'{y:5.1f} {row}')
    y += s
