"""Switch the TPS16630 UVLO/OVP divider to 0.1 % thin-film (owner decision at H2).

Reviewer finding 4: with 1 % thick-film the OVP FALLING threshold has only
0.18 V of margin over the 57 V legal PSE maximum, and that margin does not
survive tempco - at +/-100 ppm/degC over a 60 degC excursion the worst case
lands near 56.5 V, i.e. BELOW 57 V, so after a genuine overvoltage event the
rail could fail to re-enable at a perfectly legal rail voltage.

Yageo RT series is 0.1 % AND 25 ppm/degC thin-film, so this fixes both the
initial tolerance and the tempco term - the tempco was the real problem.

Edits pwr.py (the generator is the source of truth), not the .kicad_sch.
Idempotent.
"""
import io
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\gen\pwr.py'
s = io.open(P, encoding='utf-8').read()

if 'C865592' in s:
    print('already applied - no change')
    sys.exit(0)

subs = [
    # --- LCSC map ---
    ('    "R66": "C185284",     # 620k 1% 0805 (UVLO string R1)  - VALUE CHANGED',
     '    "R66": "C865592",     # 620k 0.1% 25ppm 0805 thin-film (UVLO string R1)'),
    ('    "R67": "C17414",      # 10k  1% 0805 (UVLO string R2)  - VALUE CHANGED',
     '    "R67": "C110775",     # 10k  0.1% 25ppm 0805 thin-film (UVLO string R2)'),
    ('    "R73": "C17444",      # 12k  1% 0805 (UVLO string R3)  - VALUE CHANGED',
     '    "R73": "C865172",     # 12k  0.1% 25ppm 0805 thin-film (UVLO string R3)'),
    # --- value strings shown on the sheet ---
    ('V_620K = "620k 1% 0805"', 'V_620K = "620k 0.1% 0805"'),
    ('V_10K_0805 = "10k 1% 0805"', 'V_10K_0805 = "10k 0.1% 0805"'),
    ('V_12K = "12k 1% 0805"', 'V_12K = "12k 0.1% 0805"'),
    # --- identity fields ---
    ('            ("R66", "RC0805FR-07620KL", "YAGEO"),',
     '            ("R66", "RT0805BRD07620KL", "YAGEO"),'),
    ('            ("R67", "0805W8F1002T5E", "UNI-ROYAL(Uniroyal Elec)"),',
     '            ("R67", "RT0805BRD0710KL", "YAGEO"),'),
    ('            ("R73", "0805W8F1202T5E", "UNI-ROYAL(Uniroyal Elec)")):',
     '            ("R73", "RT0805BRD0712KL", "YAGEO")):'),
]

missing = [o for o, _ in subs if o not in s]
if missing:
    print('ABORT - %d anchors not found:' % len(missing))
    for m in missing:
        print('   ', m[:80])
    sys.exit(1)

for o, n in subs:
    s = s.replace(o, n, 1)

# V_10K_0805 is used ONLY by R67 here? Guard against it being shared with the
# T2P network (R4/R5), which must stay 1 %.
if s.count('V_10K_0805') > 2:
    print('WARNING: V_10K_0805 referenced %d times - verify R4/R5 did not '
          'change tolerance' % s.count('V_10K_0805'))

io.open(P, 'w', encoding='utf-8').write(s)
print('pwr.py updated: R66/R67/R73 -> Yageo RT 0.1 % 25 ppm/degC thin-film')
print('  R66 620k C185284 -> C865592')
print('  R67 10k  C17414  -> C110775   (R4/R5 keep C17414 1% for T2P)')
print('  R73 12k  C17444  -> C865172')
