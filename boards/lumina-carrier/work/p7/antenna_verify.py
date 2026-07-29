"""Verify the ESP32-S3 antenna band is copper-free on every layer.

Wi-Fi is a supported control path on this board (owner decision at H1), so a
ground pour or a stray track under the PCB antenna is a functional defect, not
a cosmetic one. No gate in the pipeline checks this - placement's `keepouts`
key is read only by the P6 scripts, and neither the router nor planes_gen sees
it - so it is verified here by geometry.

Band: [109.58, 86.132, 119.58, 108.132] (absolute board coords).
U30's OWN pads are allowed inside it (the module owns the keepout).

Parses the board with a balanced-paren scan; prints findings only.
"""
import io
import re
import sys

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
BAND = (109.58, 86.132, 119.58, 108.132)


def blocks(text, token, start=0, end=None):
    end = len(text) if end is None else end
    i, pat = start, '(' + token
    while True:
        i = text.find(pat, i, end)
        if i < 0:
            return
        j, depth, instr = i, 0, False
        while j < end:
            c = text[j]
            if c == '"' and text[j - 1] != '\\':
                instr = not instr
            elif not instr:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


# STRICT interior test. The In1/In2 plane regions are deliberately shaped to
# STOP at x = 109.58, i.e. exactly the band's left edge, so their fill polygons
# legitimately carry vertices ON the boundary. An inclusive (<=) test counts
# those as violations and cries wolf - it reported 14 "hits" that were all
# boundary vertices. Copper is only in the band if it is STRICTLY inside.
EPS = 0.01  # mm


def inband(x, y, pad=0.0):
    return (BAND[0] + EPS - pad < x < BAND[2] - EPS + pad
            and BAND[1] + EPS - pad < y < BAND[3] - EPS + pad)


src = io.open(PCB, encoding='utf-8').read()
bad = []

# --- routed segments --------------------------------------------------------
seg_hits = 0
for (a, b) in blocks(src, 'segment'):
    body = src[a:b]
    st = re.search(r'\(start\s+(-?[\d.]+)\s+(-?[\d.]+)', body)
    en = re.search(r'\(end\s+(-?[\d.]+)\s+(-?[\d.]+)', body)
    ly = re.search(r'\(layer\s+"([^"]+)"', body)
    nt = re.search(r'\(net\s+(\d+)', body)
    if not (st and en):
        continue
    p1 = (float(st.group(1)), float(st.group(2)))
    p2 = (float(en.group(1)), float(en.group(2)))
    if inband(*p1) or inband(*p2):
        seg_hits += 1
        if seg_hits <= 5:
            bad.append('TRACK on %s net %s  %s -> %s'
                       % (ly.group(1) if ly else '?', nt.group(1) if nt else '?', p1, p2))

# --- vias -------------------------------------------------------------------
via_hits = 0
for (a, b) in blocks(src, 'via'):
    body = src[a:b]
    at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', body)
    if at and inband(float(at.group(1)), float(at.group(2))):
        via_hits += 1
        if via_hits <= 5:
            bad.append('VIA at (%s, %s)' % (at.group(1), at.group(2)))

# --- zone FILL polygons (the pour that would actually detune the antenna) ---
zone_hits = 0
zone_detail = []
for (a, b) in blocks(src, 'zone'):
    body = src[a:b]
    is_keepout = '(keepout' in body
    lys = re.findall(r'\(layers?\s+"([^"]+)"', body)
    net = re.search(r'\(net_name\s+"([^"]*)"', body)
    n_in = 0
    for (fs, fe) in blocks(body, 'filled_polygon'):
        fb = body[fs:fe]
        for m in re.finditer(r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', fb):
            if inband(float(m.group(1)), float(m.group(2))):
                n_in += 1
    if n_in and not is_keepout:
        zone_hits += n_in
        zone_detail.append('ZONE FILL net "%s" layers %s: %d filled vertices inside band'
                           % (net.group(1) if net else '?', lys, n_in))

print('=== ANTENNA BAND COPPER VERIFICATION ===')
print('band: [%.3f, %.3f, %.3f, %.3f]  (%.1f x %.1f mm)'
      % (BAND[0], BAND[1], BAND[2], BAND[3], BAND[2] - BAND[0], BAND[3] - BAND[1]))
print()
print('tracks with an endpoint inside : %d' % seg_hits)
print('vias inside                    : %d' % via_hits)
print('non-keepout zone fill vertices : %d' % zone_hits)
for d in zone_detail:
    print('   ' + d)
for d in bad[:10]:
    print('   ' + d)
print()
clean = (seg_hits == 0 and via_hits == 0 and zone_hits == 0)
print('VERDICT: %s' % ('CLEAN - no routed copper or pour in the antenna band'
                       if clean else '*** COPPER PRESENT IN ANTENNA BAND ***'))
sys.exit(0 if clean else 1)
