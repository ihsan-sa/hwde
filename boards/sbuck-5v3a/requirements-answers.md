# Delegate answers to requirements.md section 9

The brief's DECISION POLICY says: "Make every remaining decision yourself. Do not
ask clarifying questions. Where this brief is silent, take the conventional,
conservative option." The orchestrator therefore answers all 33 open questions as
DELEGATE. These are binding requirements for P1-P9. Anything marked OVERRIDE
differs from the analyst's proposed default.

| # | Answer |
|---|---|
| 1 | ACCEPT. +/-2% (4.90-5.10 V) is the DC setpoint window over line/load/temp. The 50 mV ripple and 200 mV transient are separate, additive allowances. |
| 2 | ACCEPT. Ripple measured at the output screw terminal, 20 MHz BW limit, short spring ground on the dedicated scope-ground pad. |
| 3 | ACCEPT. Load step 0->3 A at 2.5 A/us, Vin = 12 V. |
| 4 | ACCEPT. Efficiency is terminal-to-terminal: reverse-polarity FET, fuse and connector losses all count against the 88% floor. |
| 5 | ACCEPT. 3.0 A continuous is the true maximum. IC current limit must be >= 4.0 A minimum-spec (not typical). |
| 6 | ACCEPT + TIGHTEN. No surge spec given. Require IC absolute-max Vin >= 28 V and input MLCCs rated >= 50 V so the derated DC-bias capacitance is still real at 18 V. |
| 7 | ACCEPT. IC cycle-by-cycle limit with hiccup restart, PLUS a 4 A slow-blow input fuse (covers a shorted high-side switch, which the IC cannot). Fuse DCR <= 30 mOhm and its loss counts against the efficiency budget. |
| 8 | ACCEPT. The IC's internal thermal shutdown is sufficient; no discrete thermal cutout. |
| 9 | ACCEPT. 5.08 mm 2-pin THT screw terminal, horizontal outward wire entry, >= 10 A / 300 V, 12-24 AWG, whichever family is LCSC-stocked at depth. |
| 10 | ACCEPT. Input and output on opposite short edges, straight-through power flow. |
| 11 | ACCEPT. One green indicator LED on VOUT at ~1 mA. |
| 12 | ACCEPT. No PG connector. If the chosen IC has a PG pin, expose it as a test pad with its pull-up. |
| 13 | ACCEPT. 1.5 mm bare SMD test pads. VOUT test pad paired with a scope-ground pad ~5 mm away. No THT loops. |
| 14 | ACCEPT. EN not user-controllable. Resistor divider from VIN sets UVLO ~6.5 V rising / ~6.0 V falling. EN exposed as a test pad only. |
| 15 | ACCEPT. Operating ambient 0 to 50 C. All parts rated -40 C or wider. |
| 16 | ACCEPT. 50 C is free air, open frame on standoffs, natural convection on both faces. |
| 17 | ACCEPT. Use the full 50 x 40 mm envelope. Copper area is the thermal solution. |
| 18 | ACCEPT - 4 LAYER. Justification (goes in DECISIONS.md): the brief demands an uninterrupted ground plane on the layer directly under the switching components, a minimised input-loop area (which needs the image plane close to the loop), and 2.05 W of natural-convection cooling from a <= 50x40 mm board. A 2-layer board cannot provide the uncut image plane without sacrificing the bottom-side thermal/return copper, and JLC 4-layer at this size is a few dollars per board. |
| 19 | ACCEPT. 4x 3.2 mm NPTH, corners inset 3.5 mm from each edge, 6.5 mm mechanical keepout, isolated from GND copper. |
| 20 | ACCEPT. 15 mm maximum component height. |
| 21 | ACCEPT. 1 oz outer / 0.5 oz inner (JLC 4-layer standard). Escalate to 2 oz outer ONLY if IPC-2152 sizing or the Tj calculation fails at 1 oz - and record it as a decision if so. |
| 22 | ACCEPT. Build quantity 5. |
| 23 | ACCEPT. No hard unit-cost cap. Target ~$12/board at qty 5; flag any single line item over ~$3. |
| 24 | ACCEPT. "In stock" means >= 500 pcs for the IC, inductor and P-FET; >= 2000 pcs for passives. No EOL, no last-stock, no "on order" parts. |
| 25 | ACCEPT. JLC PCBA for SMT (economic/standard), screw terminals hand-soldered on receipt and marked DNP-for-assembly in the CPL. |
| 26 | ACCEPT. Single-sided assembly, top only. Bottom side reserved for ground and thermal copper. |
| 27 | ACCEPT. JLCPCB standard/economic process class. Confirm the live capability numbers at P5 rules_gen; do not design to remembered minimums. |
| 28 | ACCEPT. LCSC Basic/Preferred for passives and the LED. Extended is acceptable for the buck IC, inductor and P-FET. |
| 29 | ACCEPT. Survive a sustained output short indefinitely, auto-recover by hiccup, fuse intact (a blown fuse means a hard part failure, not a normal short). |
| 30 | ACCEPT. No active protection against a swapped in/out connection or output back-drive. Mitigation is unambiguous silkscreen: "VIN 7-18V" and "VOUT 5V 3A" with polarity at each terminal. 12 V forced into the 5 V output is NOT required to be survivable. |
| 31 | ACCEPT. No EMI standard applies and no testing is planned. Apply the brief's layout rules as best practice; keep the DNP RC snubber as the mitigation hook; no extra input filter stage. |
| 32 | ACCEPT + TIGHTEN. Prefer fsw in the 400-700 kHz band. This stays below the AM broadcast band (530 kHz-1.7 MHz is to be avoided where the part allows), keeps switching loss and 18 V-input duty-cycle minimums comfortable, and lets a reasonable inductor hit 20-40% ripple. Do not pick a fixed ~1 MHz-class part if a 400-700 kHz option meets the other requirements. |
| 33 | ACCEPT. Silkscreen: board name + rev A + date, per-terminal V/I text and polarity marks, pin-1 marks on every polarised part, every test point labelled, no logo. |

## Safety flags (requirements section 8) - delegate resolution

- Mains: NOT PRESENT. Confirmed from the brief (7-18 V DC input).
- Battery: NOT PRESENT.
- Motors / inductive loads: NOT PRESENT (resistive/electronic load assumed).
- >30 V: NOT PRESENT (18 V maximum input; parts rated >= 28 V absolute max).
- RF transmit: NOT PRESENT.
- High current: 3.0 A output sits exactly ON the >3 A threshold, not above it.
  Resolution: treat as high-current for copper sizing and connector rating
  (IPC-2152 sizing at 10-20 C rise, >= 10 A terminals), which is the conservative
  reading, but no agency-certification path is triggered.
- Fault energy: the upstream supply's current limit is unstated. Resolution: the
  4 A input fuse (Q7) bounds it on-board; downstream of the fuse, the IC's hiccup
  limit bounds the output.
