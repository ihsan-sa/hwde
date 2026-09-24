# pd-trigger-lite learnings

## 2026-09-24 [parts] CH224A beats CH224K on a trigger board
CH224A (C42459160) takes VBUS directly on VHV (32 V abs max), ties its VBUS sense pin to VHV, and
has a published Rset table (6.8k/24k/56k/120k = 9/12/15/20 V). The CH224K needs a 0.28 W dropper,
a 10k sense resistor and CFG pull-ups, and has no published Rset table. Net fewer parts.

## 2026-09-24 [routing] Freerouting ignores a declared power pour band
With VBUS as an F.Cu zone band, Freerouting routed CC/CFG1 on F.Cu straight across it (splitting
the zone into islands) and put CFG1 on F.Cu under the USB-C body. On a small board with a pour
band, hand-route the few signals with route_edit (drop crossings to B.Cu) instead.

## 2026-09-24 [planes] planes_gen zones default to thermal relief; a 3 A pour needs solid
The VBUS F.Cu zone came out with thermal spokes and DRC raised starved_thermal on the USB-C VBUS
pads and J2. Set the zone pad connection to solid (done here with a pcbnew edit; planes_gen has no
flag for it).

## 2026-09-24 [routing] A 1.25 mm power width rule cannot reach a 1 mm-pitch IC pin
Split the controller supply off the 3 A net with a 0R (R7, /VHV) so its pins take thin copper.

# pd-trigger-lite-dip learnings

## 2026-09-24 [parts][library] easyeda2kicad DIP switch pulls as through_hole with a body-only courtyard
C7421518 (1.27-5P TPPT) came in with `(attr through_hole)` although every pad is SMD, and a
courtyard drawn round the body only, leaving the gull-wing pads outside it. Set attr smd (so the
CPL keeps it) and grow the courtyard to enclose the pads before board_init.

## 2026-09-24 [parts] Half-pitch DIP datasheets rarely say which side is ON
The SHOU HAN drawing shows no ON mark. The silk assumes the usual convention (ON on the side away
from the pin 1-n row); the guide tells the owner to trust the mark on the switch body.
