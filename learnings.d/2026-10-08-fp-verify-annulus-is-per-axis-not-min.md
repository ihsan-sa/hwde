## 2026-10-08 [fp_verify][fplib] THT annulus is per axis, not min(pad) minus the drill's long axis
fp_verify computed (min(pad size) - largest drill dimension) / 2, so the C165948 USB-C shell pad (1.2x2.0 oval, 0.8x1.5 oval drill) read -0.15 mm when the real annulus is 0.20 mm. Pad size and drill both sit in the pad's own frame, so fplib now keeps `Pad.drill_xy` and fp_verify takes min((sx - dx)/2, (sy - dy)/2). Round pads and drills give the old result. Do not reduce a slot drill to one number before comparing it with a pad.

Triage: now L2 | target L2 | owner scripts/fp_verify.py | status done | note tests/test_parts.py test_fp_verify_annulus_* pin it.
