# P6 digest (stm32-blinky)
seed 443->313 HPWL, anneal 3 candidates (best 160), chose cand1 + DRC-semantics
clearance repair + judgment edits (D2 out of U1.48 corridor; C1 8.7->2.7mm).
Final: gate place PASS 0/0, HPWL 227, route probe 1.0 (46/46 at 25 passes),
KiCad DRC clean except 46 expected unconnected. Crystal 4.1mm, decouplers
1.5-7.6mm all in class. Renders reports/place/render_final/.
FINDING (major): place gate passed 9 shorting pad pairs - courtyard-only
legality blind where EasyEDA courtyards < pad fields (LQFP48, D2). Agent
built DRC-semantics repair (reports/place/tools/). Hardening: placelib
effective-courtyard = union(courtyard, pad bbox+margin) + fp_verify
courtyard-covers-pads warning.
