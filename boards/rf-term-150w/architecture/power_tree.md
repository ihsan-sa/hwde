# rf-term-150w - power tree

## 1. There are no rails

**This board has no DC supply, no regulator, no rail and no decoupling.** It is fully
passive: one RF port, one resistive element, one trimmer, three mounting holes.
`requirements.md` s3 fixed this; nothing in P1/P2 changed it.

| Rail | Status |
|---|---|
| any DC input | **none** |
| battery / charger | **none** |
| mains | **none** |
| bias / detector / telemetry supply | **none** - explicitly refused in requirements s2 |

Consequences that propagate:

- `constraints.json` carries **no `+xVx` entry under `power`** - the only `power` entry is
  the RF net itself, declared so `rules_gen` sizes its track and `check_current` adjudicates
  1.732 Arms. It carries `"pdn": false` because nothing decouples an RF launch by design;
  without that flag `check_pdn` would demand a decoupling inventory for a net that has no IC
  to decouple.
- `decoupling.json` will be **empty / absent**. That is correct, not a P4 omission.
- `check_pdn` and `check_decoupling` have nothing to audit on this board.

## 2. The only power flow is RF, and it leaves the board immediately

| Node | Power | Where it goes |
|---|---|---|
| RF port J1 | **150 W CW, 100% duty, DC-25 MHz** (A1, A2) | absorbed |
| R1 element | ~149.8 W | conducted out through the flange to the user's heatsink (A4) |
| C1 trimmer branch | **39 - 195 mW** | dissipated on-board |
| J1 contacts + trace + solder joints, I^2R | **< 40 mW** | dissipated on-board |
| **total dissipated IN the PCB** | **< 0.25 W** | negligible; no copper thermal design needed |

Derived operating point at the port (from `requirements.md` s1, reproduced because every
later phase is sized against it):

    V = sqrt(P*R) = sqrt(150*50) = 86.6 Vrms   ->  122.5 Vpeak, 244.9 Vpp
    I = sqrt(P/R) = sqrt(3)      = 1.732 Arms  ->  2.449 Apeak

### 2.1 C1 branch dissipation, re-derived at the actual part

Requirements s3 asked for this to be re-checked against the chosen trimmer.
`I = V*w*C`, `Xc = 1/(w*C)`, `P = I^2 * Xc/Q`:

| C setting | I (Arms) | Xc (ohm) | P at tan-delta 1e-3 (Q 1000) | P at Q 200 |
|---|---|---|---|---|
| 4.30 pF (low stop, incl. parasitics) | 0.058 | 1480 | 5 mW | 25 mW |
| 33 pF (Cmax) | 0.449 | 193 | 39 mW | 195 mW |

The datasheet publishes tan-delta <= 10e-4 at **1 MHz** only; no 25 MHz figure exists for
this dielectric row, so the Q 200 column is the pessimistic bound. **Confirmed: voltage,
not power, is the gate on this part** - as requirements s3 predicted. Self-resonance
300 MHz at Cmax, 12x above the operating frequency, no in-band resonance.

**But** see `blocks.md` s8 OPEN-1: the part's **-40 to +70 C** operating range, not its
40-200 mW of self-heating, is what puts it at risk - the board is bolted 1 mm above a
heatsink base running at ~88 C at full power.

### 2.2 Conductor sizing

At 1.732 Arms the board is **below** the 3 A high-current threshold, so the high-current
compliance flag does not apply (requirements s8). Sizing is driven by the voltage/clearance
case, not ampacity:

- Skin depth in Cu at 25 MHz = 13.1 um; 1 oz = 35 um = 2.7 skin depths. 1 oz is adequate;
  2 oz would buy nothing and is an upcharge the brief forbids.
- IPC-2152 at 1.732 A / 10 C rise / 1 oz external asks ~0.75 mm. The narrowest point of the
  RF net is **1.1 mm** (the neck between J1's ground pads) and everything else is 4.4 mm
  wide. Comfortable.
- AC loss on the whole launch: `R_dc = 1.3 mohm`, AC/DC factor ~2.5 at 2.7 skin depths ->
  ~3.3 mohm -> `I^2R = 10 mW`. Confirms the "< 40 mW" line above.

## 3. Thermal path (the real "power tree" of this board)

The heat path is a series chain that never touches the PCB:

```
R1 element  ->  R1 flange  ->  thermal grease  ->  user heatsink  ->  ambient 25 C
             (derating is                  0.212 C/W        <= 0.42 C/W
              specified on                (2.359 cm^2       (Wakefield 392-300AB
              FLANGE temp,                 flange,           publishes 0.33 C/W
              so element-to-flange          0.5 C.cm^2/W)    natural convection)
              Rth is NOT needed
              and is ABSENT from
              the datasheet)
```

    T_flange allowed at 150 W = 120 C          (curve: 250 W flat to 100 C, -5.0 W/C to 0 at 150 C)
    Rth_total  = (120-25)/150 = 0.633 C/W
    Rth_sink  <= 0.633 - 0.212 = 0.42 C/W
    P(Rth)     = 250 W                for Rth <= 0.30 C/W
    P(Rth)     = 625 / (1 + 5*Rth)    for Rth  > 0.30 C/W

All five expressions were re-derived from `parts/T50R0-250-12X.json` and agree with the
orchestrator's P2 decisions to the digit. Full working, the two cited real heatsinks and
the no-heatsink case are in `blocks.md` s6.

**The PCB is a parasitic load on this path, not a member of it.** It sits on the same hot
surface, so heat flows *into* the board, which is why `blocks.md` s8 OPEN-1 exists. Nothing
on the board needs thermal vias, copper pours for heat, or a `thermal` entry in
`constraints.json` - and `constraints.json` deliberately omits that key so `check_thermal`
does not demand via arrays for a 150 W part that dissipates none of it into FR4.
