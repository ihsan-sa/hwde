"""rf-de-20m P8-b - apply the 36 V / 162 W derate to kicad/constraints.json.

Idempotent: refuses to run twice (the P8 amendment key is the guard).
"""
import json
from pathlib import Path

p = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/constraints.json')
d = json.loads(p.read_text(encoding='utf-8'))
assert '_comment_amendment_P8_DERATE' not in d, 'already applied'

DERATE = (
 "P8 DERATE 2026-08-08 (owner ruling, checkpoint H4): THE BUS IS 36 V, NOT "
 "40 V, AND THE STAGE MAKES ~162 W, NOT 200 W. The network is UNCHANGED - "
 "R_opt stays 4.13 ohm - so Sokal's P.R/Vdd^2 = 0.51659 gives "
 "P = 0.51659 x 36^2 / 4.13 = 162.1 W, and every Class E quantity that is "
 "linear in Vdd scales by 36/40 = 0.900 while every power scales by 0.810: "
 "Vds,pk 142.5 -> 128.2 V; I_dc 5.96 -> 5.36 A; I_sw,rms 9.17 -> 8.25 A; "
 "I_tank 6.96 -> 6.26 A rms; I_Cm 6.66 -> 5.99 A rms; node peaks TANK_A "
 "156 -> 140.4 V, RFOUT 141 -> 126.9 V, TANK_B 41 -> 36.9 V; element-across "
 "peaks L_s 203 -> 182.7 V, C_s 151 -> 135.9 V, L_m 135 -> 121.5 V; bus "
 "ring-up 51 -> 45.7 V. P_in = 36 x 5.36 = 193 W, so efficiency is unchanged "
 "at ~84 percent. ZVS IS UNAFFECTED - the Class E equations are linear in "
 "Vdd and the ZVS/ZdVS conditions constrain only the SHAPE of the current "
 "waveform, which L_s, C_s, C_shunt, R and f fix (decisions.md D1/D2). "
 "WHY THE DECLARED current_a AND voltage NUMBERS BELOW ARE NOT LOWERED: they "
 "are machine inputs to rules_gen and to check_current / check_creepage, and "
 "this board's .kicad_dru, its three power netclasses and 100 percent of its "
 "routed copper were generated and laid at the 40 V / 200 W numbers. "
 "Lowering them would RELAX a check against copper that is not changing, and "
 "the bus is a bench knob the owner may raise back to 40 V once a real Tj is "
 "measured. They are therefore kept as the design ENVELOPE and the derated "
 "values are recorded on each entry. thermal[].power_w IS lowered, because "
 "that is an OUTPUT feeding check_thermal and the junction-temperature case, "
 "not a conductor-sizing input.")

d['_comment_amendment_P8_DERATE'] = DERATE

th = {t['ref']: t for t in d['thermal']}
th['Q201']['power_w'] = 4.78
th['Q202']['power_w'] = 4.78
th['L301']['power_w'] = 8.1
th['L302']['power_w'] = 5.4
th['L201']['power_w'] = 0.36
th['L202']['power_w'] = 0.36

th['Q201']['_note'] = (
 "EPC2019, one of a MIRRORED PAIR. P8 2026-08-08: 5.63 -> 4.78 W at the "
 "derated 36 V / 162 W bus WITH R205/R206 back at 4R7. Working: at 40 V the "
 "pair is 11.25 W nominal / 14.56 W at the max-datasheet corner (D1); gate "
 "drive is 0.36 W of that and is Vdd-independent (Qg.VDD.fSW), so the "
 "Vdd-dependent 10.89 W scales by the architecture's own 36 V factor "
 "(12.34/14.56 from the max-corner row of D1's derating ladder = 0.8437) to "
 "9.19 W, giving a pair total of 9.55 W nominal = 4.78 W each and 12.34 W = "
 "6.17 W each at the max-datasheet corner. The 6R8 turn-off resistors would "
 "add 0.72 W across the pair at 36 V; reverting them to 4R7 (H4) removes it. "
 "RthJB 7.5 C/W per package cannot be improved by layout - it is inside the "
 "package - and it is why a SINGLE FET exceeds the 150 C ABSOLUTE MAXIMUM "
 "even with a hypothetical 0 C/W heatsink. "
 "THETA_BS IS NOW COMPUTED OFF THE BOARD'S OWN STACKUP, NOT ASSUMED (this is "
 "as far as geometry can close OPEN-10): F.Cu 35 um / 0.2444 mm / In1 "
 "15.2 um / 1.065 mm / In2 15.2 um / 0.2444 mm / B.Cu 35 um; spreading "
 "lengths sqrt(k_cu.t_cu.h/k_fr4) = 3.38 / 4.65 / 2.23 mm; effective areas "
 "110 / 392 / 589 mm2 at k_fr4 0.3 give a bulk board-through path of "
 "17.9 C/W for the pair, in parallel with the via array. The architecture's "
 "assumed 1.5 C/W was never achievable; the P8 build lands at 3.1-3.4 C/W "
 "(was 6.9-7.3 with 18 vias). "
 "min_vias 10 IS NOW MET AND EXCEEDED: 19 (Q201) / 20 (Q202) GND vias within "
 "4.0 mm of each die centroid and 54 within 5.0 mm of the pair, up from 9 "
 "each. check_thermal still reports 'found 3/4' because its window is "
 "max(2.0, sqrt(pad_hull_area/pi)+1.5) = 2.27 mm and an EPC2019's pad hull "
 "is 1.84 mm2 - the window is smaller than the array, and the 0.8 mm "
 "aiee_hv_143v_SW rule is what holds the nearest barrel out to 1.58 mm. "
 "CORRECTION TO THE PREVIOUS TEXT: 'COPPER-FILLED vias' IS NOT A PURCHASABLE "
 "JLC PROCESS - JLC's filled/plugged option is EPOXY (POFV: resin filled, "
 "copper capped). A 0.3 mm barrel at the 20 um plating floor is 199 C/W "
 "(157 C/W at 25 um); epoxy fill adds 37,700 C/W in parallel, i.e. 0.5 "
 "percent. Any budget assuming a 2.5x copper-fill factor is unpurchasable "
 "and this board does not assume one - the 54-barrel array is 3.7 C/W of "
 "pure barrel and ~4.2 C/W including F.Cu lateral access. POFV IS STILL "
 "SPECIFIED, for FLATNESS not conductance: it caps the vias so the B.Cu "
 "heatsink land is a plane rather than a dimpled surface. Vias go BESIDE the "
 "source lands, not in them - the solder bars are ~0.2 mm wide. Mask-opened "
 "land on B.Cu: BUILT AT P8 (footprint HS1 - 1430 mm2 of B.Cu+B.Mask GND pad "
 "inside HS-2, notched so the six non-GND vias in the land stay tented and "
 "so the two new M2 clamp holes keep their hole clearance). blocks.md s4.1.")

th['Q202']['_note'] = th['Q202']['_note'].replace(
 "The second EPC2019.",
 "The second EPC2019. P8 2026-08-08: power_w 5.63 -> 4.78 W - see Q201's "
 "note for the derate working, the computed theta_BS and the via count.")

th['L301']['_note'] = th['L301']['_note'].replace(
 "6.7 W at Q 150, 10.0 W at Q 100, 12.5 W at Q 80.",
 "6.7 W at Q 150, 10.0 W at Q 100, 12.5 W at Q 80 - THOSE ARE THE 200 W "
 "FIGURES. P8 2026-08-08 derate to 162 W: P = 162 x Q_L/Q_ind = 810/Q, so "
 "power_w 10.0 -> 8.1 W at Q 100, and the DRAWN part (measured Q 388, "
 "reports/spiral-design.md s4) dissipates 2.57 -> 2.09 W.")
th['L302']['_note'] = th['L302']['_note'].replace(
 "P = 200 x Q_m/Q_ind = 666/Q watts.",
 "P = 200 x Q_m/Q_ind = 666/Q watts; at the P8-derated 162 W that is 540/Q, "
 "so power_w 6.7 -> 5.4 W at Q 100 and the drawn part (measured Q 325) "
 "dissipates 2.06 -> 1.67 W.")
for r in ('L201', 'L202'):
    th[r]['_note'] = th[r]['_note'].replace(
        "P = I_dc^2 x DCR = 35.5 x DCR; 0.89 W at 25 mohm.",
        "P = I_dc^2 x DCR. P8 2026-08-08 derate: I_dc 5.96 -> 5.36 A, so "
        "28.7 x DCR (was 35.5 x DCR); the declared budget goes 0.45 -> 0.36 W "
        "each and the real pair figure is 5.36^2 x 8.2 mohm = 0.24 W total.")

for e in d['voltages']:
    e['_note'] = e.get('_note', '') + (
        " P8 DERATE: this node peaks at %.1f V at the 36 V bus; the declared "
        "figure is kept as the 40 V ENVELOPE - see "
        "_comment_amendment_P8_DERATE." % (e['voltage'] * 0.9))
for e in d['voltage_pairs']:
    e['_note'] = e.get('_note', '') + (
        " P8 DERATE: %.1f V pk at the 36 V bus; declared value kept as the "
        "40 V envelope." % (e['voltage'] * 0.9))
DER_I = {'+40V': 6.3, '/SW': 8.25, '/tank/TANK_A': 6.26,
         '/tank/TANK_B': 6.26, '/tank/RFOUT': 6.26}
for e in d['power']:
    if e['net'] in DER_I:
        e['_note'] = e.get('_note', '') + (
            " P8 DERATE: %.2f A at the 36 V / 162 W bus; the declared %.2f A "
            "is kept as the 40 V envelope that the .kicad_dru, the netclasses "
            "and 100 percent of the routed copper were built to - see "
            "_comment_amendment_P8_DERATE." % (DER_I[e['net']], e['current_a']))

p.write_text(json.dumps(d, indent=1, ensure_ascii=True), encoding='utf-8')
print('constraints.json: derate applied')
