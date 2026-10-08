## 2026-10-08 [check_thermal][thermal] An inductor rated for temperature rise must be judged on its rating, not the copper-area curve
PCB-0026-A (150 W GaN boost, 4 layers): check_thermal put L201, a Coilcraft
XAL1010-222 at 1.1 W, at 57.8 C/W and a 64 C rise, because it ran the part
through the IC-package area curve on its /VL copper (471 mm2 within reach).
That curve starts at 140-174 C/W for a package on its own pads and knows
nothing of a 10 mm wound body that sheds heat from its own surface. The
datasheet rates the part directly: Irms 24.5 A for a 40 C rise through
2.8 mOhm, so its own theta is 40 / (24.5^2 x 0.0028) = 23.8 C/W and 1.1 W is
a 26 C rise. A thermal entry now takes `rating` {rise_c, current_a, dcr_ohm,
source}, which replaces the copper model for that part, with power_w still the
total (copper + core) loss. An IC can carry its datasheet JEDEC theta_JA
instead (`theta_ja_c_w` + `theta_source`), used as-is with no area or via
credit on top; it is optimistic on a crowded board, so say so in the basis.
The same board needs a fan at 150 W, and the check had no way to say so. An
entry now takes `airflow_lfm` or `airflow_m_s`, which scales theta by the
least improvement among TI SCBA017D's modeled QFN tables (x0.876 at 150,
x0.817 at 250, x0.771 at 500 LFM and above). Declare it only when the board
really carries the fan. Still air is unchanged.
Not done, on purpose: thermal vias and 2 oz copper on 4 layers are still not
credited. The one cited 4-layer anchor (SCBA017D Fig. 15, 46.8 -> 29.9 C/W
with vias into the planes) is a 2 mm logic pad and has not been checked
against a power package. So a 4-layer power IC still sits at the 51.1 C/W
area floor, and the "add thermal vias" remedy cannot move it.

Triage: now L2 | target L2 | owner scripts/check_thermal.py | status done | note tests/test_checks_s5.py pins the rating and airflow paths.
