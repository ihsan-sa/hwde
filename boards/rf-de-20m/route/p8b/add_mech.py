"""rf-de-20m P8-b - the three board items no pipeline op can write.

place_edit has no add-footprint op and route_edit only does tracks/vias, so
these go in as raw s-expressions on the UNFILLED board, then the refill + DRC
+ verify_geom pass is what verifies them (same precedent as the P8
zone-outline edit recorded in reports/verify-waivers.md s1.1).

  E3  HS2_LAND - the B.Cu mask-opened heatsink land. Written as GND-netted
      B.Cu+B.Mask PADS, not as a graphic on B.Mask: a netless graphic aperture
      raises one `solder_mask_bridge` error per copper item it exposes (43 of
      them, measured), because KiCad reads the graphic as its own net. Pads
      carrying GND expose only GND and raise none. zone_connect 2 so the GND
      pour bonds solid instead of through thermal spokes.
      The rectangle set is HS-2 [5,10,36,70] minus (a) a retained-mask notch
      over the six non-GND vias in the land - HS-2 forbids untented vias - and
      (b) a 1.4 mm keep-out square at each new NPTH clamp hole.
  E4  H5/H6/H7 - three M2 NPTH clamp holes bracketing the EPC2019 pair.
  W3  FID1..3 - three global fiducials, L arrangement.

Reference text is hidden on all six new footprints: this board already carries
six `silk_misattributed` findings and the gate-drive cluster has no room for
more silk - visible refdes on these added 5 silk_over_copper + 2 silk_overlap.
"""
import re
import uuid
from pathlib import Path

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
LIB = Path(r'C:/Program Files/KiCad/10.0/share/kicad/footprints')
OX, OY = 6.634999, 39.334999

HOLES = [('H5', 26.25, 11.35), ('H6', 26.15, 36.80)]
FIDS = [('FID1', 18.0, 8.0), ('FID2', 112.0, 4.0), ('FID3', 25.0, 52.0)]
LAND_ANCHOR = (20.5, 40.0)
LAND = [  # board-local rects, see module docstring.
    # west edge is 5.60, not HS-2's 5.00: J101.1 (+40V, through-hole, so it is
    # on B.Cu too) ends at x = 4.90 and carries a 0.5 mm clearance rule.
    (5.60, 10.00, 24.75, 20.70),
    (5.60, 38.20, 24.75, 70.00),
    (24.75, 12.75, 27.65, 20.70),
    (24.75, 38.20, 27.65, 70.00),
    (27.65, 10.00, 36.00, 70.00),
]


def load_mod(lib, name):
    t = (LIB / f'{lib}.pretty' / f'{name}.kicad_mod').read_text(encoding='utf-8')
    t = t.replace('\r\n', '\n')
    for k in ('version', 'generator', 'generator_version'):
        t = re.sub(rf'\n\t\({k} [^\n]*\)', '', t, count=1)
    return t


def instantiate(lib, name, ref, x, y, attr):
    t = load_mod(lib, name)
    body = t.split('\n', 1)[1]
    body = body.replace('"REF**"', f'"{ref}"', 1)
    body = re.sub(r'\n\t\(attr [^\n]*\)', f'\n\t(attr {attr})', body, count=1)
    # hide the Reference field (silk density - see docstring)
    body = body.replace(f'(property "Reference" "{ref}"',
                        f'(property "Reference" "{ref}"', 1)
    i = body.index(f'(property "Reference" "{ref}"')
    j = body.index('(effects', i)
    body = body[:j] + '(hide yes)\n\t\t' + body[j:]
    body = body.replace('\t(layer "F.Cu")\n',
                        f'\t(layer "F.Cu")\n\t(uuid "{uuid.uuid4()}")\n'
                        f'\t(at {x + OX:.6f} {y + OY:.6f})\n', 1)
    block = ('(footprint "%s:%s"\n' % (lib, name)) + body
    return '\n'.join('\t' + ln if ln else ln for ln in block.rstrip().split('\n'))


def land_footprint():
    ax, ay = LAND_ANCHOR
    pads = []
    for i, (x0, y0, x1, y1) in enumerate(LAND, 1):
        cx, cy = (x0 + x1) / 2 - ax, (y0 + y1) / 2 - ay
        pads.append(
            f'\t\t(pad "1" smd rect\n'
            f'\t\t\t(at {cx:.4f} {cy:.4f})\n'
            f'\t\t\t(size {x1 - x0:.4f} {y1 - y0:.4f})\n'
            f'\t\t\t(layers "B.Cu" "B.Mask")\n'
            f'\t\t\t(net "GND")\n'
            f'\t\t\t(zone_connect 2)\n'
            f'\t\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t)')
    return ('\t(footprint "aiee:HS2_HEATSINK_LAND"\n'
            '\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(at {ax + OX:.6f} {ay + OY:.6f})\n'
            '\t\t(descr "E3 - bottom-side heatsink contact land: mask-opened '
            'GND copper inside HS-2, notched so the six non-GND vias in the '
            'land stay tented and so the three M2 clamp holes keep their hole '
            'clearance. Board feature, not a purchased part.")\n'
            '\t\t(attr board_only exclude_from_pos_files exclude_from_bom '
            'allow_missing_courtyard)\n'
            '\t\t(property "Reference" "HS1"\n'
            '\t\t\t(at 0 -32 0)\n\t\t\t(layer "F.SilkS")\n\t\t\t(hide yes)\n'
            f'\t\t\t(uuid "{uuid.uuid4()}")\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n'
            '\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
            '\t\t(property "Value" "HEATSINK_LAND"\n'
            '\t\t\t(at 0 32 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
            f'\t\t\t(uuid "{uuid.uuid4()}")\n'
            '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n'
            '\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
            + '\n'.join(pads) + '\n'
            '\t\t(embedded_fonts no)\n\t)')


t = PCB.read_text(encoding='utf-8').replace('\r\n', '\n')
for ref, _, _ in HOLES + FIDS:
    assert f'"{ref}"' not in t, ref
assert 'HS2_HEATSINK_LAND' not in t
new = [instantiate('MountingHole', 'MountingHole_2.2mm_M2_ISO7380', r, x, y,
                   'board_only exclude_from_pos_files exclude_from_bom')
       for r, x, y in HOLES]
new += [instantiate('Fiducial', 'Fiducial_1mm_Mask2mm', r, x, y,
                    'smd board_only exclude_from_pos_files exclude_from_bom')
        for r, x, y in FIDS]
new.append(land_footprint())
tail = t.rstrip()
assert tail[-1] == ')'
PCB.write_text(tail[:-1].rstrip('\n') + '\n' + '\n'.join(new) + '\n)\n',
               encoding='utf-8', newline='\r\n')
print(f'inserted {len(HOLES)} clamp holes, {len(FIDS)} fiducials, '
      f'1 heatsink land ({len(LAND)} pads, '
      f'{sum((b[2]-b[0])*(b[3]-b[1]) for b in LAND):.0f} mm2)')
