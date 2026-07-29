"""rip_nets.py - remove every segment/via/arc of the named nets from a board.

usage: python rip_nets.py <board.kicad_pcb> mdi|<net> [<net> ...]
"mdi" expands to the four MDI nets (net names with a leading "/" cannot be
typed on a Git-Bash command line without being path-mangled).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"
ALIAS = {"mdi": ["/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"]}

board = Path(sys.argv[1]).resolve()
nets = []
for a in sys.argv[2:]:
    nets.extend(ALIAS.get(a, [a]))
nets = set(nets)
print("ripping nets:", sorted(nets))

txt = board.read_text(encoding="utf-8")
ops = []
for tag in ("segment", "via", "arc"):
    i = 0
    while True:
        i = txt.find("\n\t(%s" % tag, i)
        if i < 0:
            break
        s, d, j = i + 1, 0, i + 1
        while j < len(txt):
            if txt[j] == "(":
                d += 1
            elif txt[j] == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = txt[s:j + 1]
        nm = re.search(r'\(net "([^"]*)"\)', blk)
        uu = re.search(r'\(uuid "([^"]+)"\)', blk)
        if nm and nm.group(1) in nets and uu:
            ops.append({"op": "remove", "uuid": uu.group(1)})
        i = j
print("items to remove:", len(ops))
if not ops:
    raise SystemExit(0)
f = board.parent / (board.stem + "_rip_ops.json")
f.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run([str(VENV), str(ROUTE_EDIT), "--pcb", str(board),
                     "--ops", str(f), "--out-report",
                     str(board.parent / (board.stem + "_rip.json"))],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
print((cp.stdout or cp.stderr)[-300:])
