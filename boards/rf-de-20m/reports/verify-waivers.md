# rf-de-20m P8 - verify residual, as waiver-sidecar entries

Authored 2026-08-08 by the P8 verify fixer, after fix pass `a2`.
Snapshot before the pass: `state_snapshots/pre-fix-verify-a1/`.

`gate.py --gate verify`: **fail, 31 error / 159 warning** (was 35 / 159).
`gate.py --gate drc_routed`: **fail, 55** - byte-for-byte the P7 residual
(`reports/route-notes.md` s13), no new class, no changed count.
Geometric acceptance (`route/verify_geom.py`): **PASS**.
`plane_repair`: **pass, 0 repairs**.

**No `reports/verify-waivers.json` was written.** `gate.py:load_waivers` requires a
non-empty `approved` (who/when) on every entry and treats waivers as human
artifacts; the owner signs these off at H4. The tables below are written so they
map **1:1 onto sidecar entries**: `gate.py:waiver_matches` keys on `check` (or
`kind`) + `net` + a `refs` SUBSET test, so the eight `(check, net, refs)` tuples
in s2 cover all 31 errors and nothing else on the current board.

**Nothing was fixed by loosening a rule.** No `.kicad_dru` rule, netclass,
constraint current, dT or clearance was changed in this pass. The two real
defects were fixed with copper.

---

## 1. What was actually fixed (and what it bought)

### 1.1 REAL DEFECT - the +40V bus: 47 % of its resistance and 7x its hot spot

**The finding under-reported the problem, and pointed at the wrong copper.**
`check_current` flagged a 3.16 mm neck in the `y 31.0..34.2` board-local F.Cu
strip. That strip was carrying **no current at all**: a single 0.200 mm `+5V`
track (`L101.2 -> C109.1`, laid at P7 step 8c) crossed it diagonally at
x 20.0..23.2 and cut it into two fills, so the strip was a dead-end stub hanging
off the east end. **All 7.0 A was going the long way round** - west column ->
south block -> up the x 46..51 corridor past the buck - and the real neck was
there, where `check_current` cannot see it (those zones hold no vias, and
`pour_neck` only tests a zone that contains >= 2 via attachments).

Measured with a 2-D resistive-sheet solve of the actual +40V copper (F.Cu + B.Cu
rasterised at 0.25 mm, layers tied at the net's vias, 5.96 A injected at J101.1
and drawn at L201.1, copper at 100 C; `route/bus_solve.py`):

| | before | after |
|---|---|---|
| bus resistance J101 -> L201 | **10.393 mOhm** | **5.508 mOhm** |
| drop / dissipation at 5.96 A | 61.9 mV / 369 mW | **32.8 mV / 196 mW** |
| current in the y 31..34.2 strip | **0 A** (dead end) | **4.02 A** of 7.0 |
| current in the buck corridor | 7.00 A | 2.98 A |
| R104 pinch, 2.50 mm of copper (local y 41.5) | 2.800 A/mm -> **dT ~60 C** | 1.192 A/mm -> **dT ~8.6 C** |
| BUCK_SW crossing, 2.25 mm (local y 56.2) | 3.111 A/mm -> **dT ~76 C** | 1.324 A/mm -> **dT ~10.9 C** |
| strip aperture, 3.25 mm (local x 16.4) | - | 1.237 A/mm -> dT ~9.4 C |
| **worst section: equivalent conductor width** | **2.25 mm** | **5.29 mm** |
| **IPC-2152 requirement (7.0 A, dT 10 C, 1 oz)** | **5.500 mm** | **5.500 mm** |

IPC-2152 at 7.0 A / dT 10 C / 1 oz is 5.500 mm, i.e. **1.273 A/mm**. Every
section of the bus now runs at or just above that (1.19-1.32 A/mm, dT 8.6-10.9 C
at the *declared* 7.0 A; at the nominal 5.96 A every section is under 8 C).
Before the fix two sections ran at 2.2-2.4x it.

Per-cell peaks including corner crowding (0.25 mm cells, so these are
conservative - a 0.25 mm corner singularity spreads out within a fraction of a
millimetre): worst F.Cu cell **5.578 -> 2.375 A/mm**, i.e. equivalent width
**1.26 -> 2.95 mm**.

**Three changes, all copper, no component moved and no rule touched:**

1. **`route/ops_p8_5v_hop.json`** - the offending `+5V` segment
   (uuid `dd1db0c9`, local (16.871, 27.854) -> (24.232, 35.215)) is replaced by a
   short F.Cu stub to a via at (19.250, 30.233), a **0.4 mm In2 hop** under the
   bus strip, and a via at (24.232, 35.215) on the existing trunk corner. Both
   vias sit clear of the +40V pour (0.54 and 0.79 mm against the 0.5 mm
   `aiee_hv_51v_40V` rule), so the strip is now uncut from x 16.2 to x 50.4.
   In2 and **not** In1 on purpose: In1 at 0.2444 mm is the gate loops' and the
   drive input's return image and stays whole (same rule P7 used for its three
   hops, `route-notes.md` s10). 0.4 mm and not 0.2 mm because IPC-2152 needs
   0.345 mm for 0.3 A on 0.5 oz inner copper.
2. **The bus strip zone was widened** from `y 31.0..34.2` to `y 28.4..35.6`
   over `x 41.8..50.4` (and 29.0..35.6 over x 41.0..41.8, where a GND stitch via
   at (40.987, 28.138) limits it). North edge 28.4 keeps the 0.8 mm
   `aiee_hv_143v_SW` clearance to the /SW pour, which ends at y 27.5.
   The zone outline was edited in place and the board refilled with
   `kicad-cli pcb drc --refill-zones --save-board`; there is no pipeline op for
   a zone-outline edit, so it is recorded here and the before/after fill is
   measured in `route/verify_geom.py`.
3. **`route/ops_p8_bridge_vias.json` + `route/ops_p8_via_move.json`** - the
   B.Cu bridge's south transition went **8 vias -> 16** (a second row at local
   y 31.3, 0.9 mm pitch, against the 0.7995 mm hole-to-hole floor), clearing
   `check_current`'s `ceil(7.0 A / 0.5 A) = 14`. The 16th via was moved from
   (50.1, 32.2) to (42.9, 30.4): at x 50.1 the pour is clipped to a 0.46 mm
   tongue by the 0.8 mm TANK_A HV clearance.

   Both via batches had to be applied to an **unfilled** board (fills stripped,
   ops applied, `--refill-zones --save-board`): on the poured board KiCad
   re-derived 1-4 of the 8 vias' nets from the In1/In2 GND plane and `route_edit`
   correctly rolled the batch back. This is the workspace LEARNINGS entry
   *"a via added into an ALREADY-FILLED zone takes the ZONE's net"*, hit from the
   3-of-4-layers-are-+40V side, where it is **non-deterministic** - see s4.

Also fixed in the same pass, same class: the `+5V_DRV` In2 hop under U201's OUTL
wrap went **0.200 -> 0.400 mm** (0.3 A on 0.5 oz inner needs 0.345 mm).

**FAB NOTE, CARRY TO P9.** The two new `+5V` vias at local (19.250, 30.233) and
(24.232, 35.215) sit inside the bottom-heatsink contact land
(`constraints.placement.keepouts` [11.635, 49.335, 42.635, 109.335]). They join
the four `+5V_DRV` / `/stage/DRIVE` vias already recorded in `route-notes.md`
s10: HS-2 permits vias there but forbids **untented** ones. These are non-GND
nets and MUST stay tented on B.Cu. **Do not enable via-tenting-off at plot time.**

### 1.2 NOT A DEFECT - the /SW return image (`check_return_path`, 1 error)

> `return corridor of /SW (F.Cu) leaves continuous GND copper on In1.Cu:
> 81.29 mm2 deficit, 0.60 mm of trace crossing`

Investigated, measured, and **it is benign**. Not fixed, because the only fix
available is forbidden by the architecture and would buy 0.45 mm.

**Where it is.** /SW has four F.Cu tracks. Three are the 0.25/0.45 mm EPC2019
drain escapes and their rung, and they produce no deficit at all. The fourth is
the **L301 west terminal land: 11.894 mm wide and 1.200 mm long**, at local
(51.4, 17.6) -> (52.6, 17.6). `check_return_path` buffers a centreline by
`k x trace width` = 3 x 11.894 = **35.68 mm**, so a 1.2 mm stub gets a
1.2 x 71.4 mm corridor. **21.70 mm2 of the 81.29 mm2 deficit (27 %) is not even
on the board** - the corridor runs to local y -18.08. The rest is the part of
that rectangle that lies east of local x 51.0, where In1's zone-A plane ends.

**The switching loop itself is fully imaged.** Measured on the actual fills:

- the **/SW zone fill** - the pour that carries the drain node - is
  191.30 mm2, of which **183.90 mm2 (96.13 %) sits over continuous In1 GND**;
- the entire remainder is one 7.41 mm2 lip at local x 51.00..51.50, i.e. a
  0.5 mm strip along the pour's east edge;
- **C203, C204, C205, C206 (the C_shunt bank) and L202.1 are 100 % over In1.**
  The high-dI/dt loop that In1 at 0.2444 mm exists for - drain -> C_shunt ->
  source - is imaged over its whole length.

**Why it cannot be closed.** The land sits where /SW hands off to the tank, at
the edge of zone B, which by decision **D4** carries **no plane on any inner
layer** (a plane under a PCB air-core spiral is a shorted turn). L301's
`copperpour not_allowed` rule area reaches x = **51.45** at y = 17.6 (51.84 at
y = 13.6 / 21.6); In1's plane already reaches x = **51.00**. So the total copper
that could ever be added is **0.45 mm** of the land's 1.2 mm - and
`route/verify_geom.py`'s strict-interior test would then sit 0.05 mm from
failing. There is no fix; there is a design decision.

**Why it is benign, in numbers.** Model the land as a 1.2 mm long, 11.894 mm
wide strip:

```
with an image at h = 0.2444 mm : L = mu0.h.l/w                    = 0.031 nH
without an image (partial self): L = (mu0.l/2pi)[ln(2l/(w+t)) + 0.5
                                    + 0.2235(w+t)/l]              = 0.268 nH
increment                                                          = 0.24 nH
```

- **0.24 nH against the 164 nH inductor it feeds = 0.15 %**, and 0.09 % of the
  274 nH series tank. The C_s bank trims +/-54 pF on 518 pF (+/-10.4 %), i.e.
  ~70x the resonant-frequency error this causes (df/f = -0.07 %).
- The current through it is the **tank** current, not the switching edge:
  6.96 A rms sinusoidal at 20 MHz -> dI/dt max 1.24 A/ns, so
  `L.di/dt = 0.30 V` on a node that swings 143 V pk - **0.21 %**. The
  "~8 A/ns" figure belongs to the drain-current transition, which flows in the
  FET/C_shunt/source loop; the choke and the tank see a smooth sinusoid.
- **The loop still closes**, and it closes the way the architecture designed it:
  past this land the conductor *is* the spiral, whose loop area is the 164 nH
  the design is built on. The tank's return runs on the **B.Cu GND bridge**
  (board-local [49, 30, 94, 48]) from J301's shell back to the FET sources -
  verified still ONE 5999 mm2 island spanning x 0.3..119.7.

Waived below as entry 5.

---

## 2. The 31 residual ERRORS, as sidecar entries

| # | `check` | `net` | `refs` | covers | `reason` |
|---|---|---|---|---|---|
| 1 | `check_creepage` | `/SW` | `["Q201","Q202"]` | **21** | Intra-EPC2019 die geometry, confirmed one by one: **all 21 fall inside the two EPC2019 land patterns** (Q201 x10, Q202 x11) and every spacing is the die's own solder-bar pitch - 0.350 mm (x15), 0.375 (x2), 0.389 (x2), 0.391 (x2). **None is board copper away from the die.** The land pattern is a 0.6 mm solder-bar row, so drain-to-source gaps are 0.350 mm by construction, against IPC-2221's 0.80 mm (A6/B4) and 0.40 mm (B4/B4) at /SW's 143 V peak. IPC-2221 creepage governs BOARD conductors, not the internal terminals of a manufacturer-qualified **200 V** part, and EPC rates the device at 200 V *with that pitch*. No alternative part exists - every eGaN FET in this class has comparable bar pitch. Same class, same evidence and the same verdict as the APPROVED `drc_routed` clearance waiver (48 findings, `route-notes.md` s13 entries 1-4). |
| 2 | `check_current` | `/SW` | - | 3 | The EPC2019 drain escapes (2 x 0.2500 mm) and their rung (0.4500 mm) against an `aiee_pwr_width_SW` floor of 11.8942 mm. Geometrically unmeetable: the widest connectable conductor at a drain bar is 2.63 mm, and a `.kicad_dru` rule beats a zone's local clearance during fill so **no pour of any setting can reach the die**. Pour fan-in per `remediations/track_width.md` step 4 is what is in place - /SW is one 263 mm2 F.Cu island and these are the only /SW tracks on the board besides the L301 land. Identical to the approved `drc_routed` `track_width` waiver (entry 5). |
| 3 | `check_current` | `/tank/RFOUT` | - | 1 | L302's east terminal land, 7.6510 mm against an 8.4123 mm floor. The corridor is 9.106 mm wide and 0.8 mm of HV clearance each side leaves 7.506 mm of legal conductor, so 8.4123 mm cannot exist there. It is also above the architecture's own binding number: `constraints.json` states the AC requirement is ~7.2 mm of poured copper and that the IPC-2152 width "is a floor, not a pass ... wrong above ~1 MHz". Identical to the approved `drc_routed` `track_width` waiver (entry 6). |
| 4 | `check_current` | `+40V` | - | 1 | `+40V pour on F.Cu necks to ~4.43 mm ... needs 5.500 mm`, reported at local (46.79, 7.58) - the **north block**, around L201. It is an artefact of the per-zone erosion test, not a conductor: the block is **10-15 mm** of continuous copper, and the erosion fails only because **3 of the 30** vias in the bridge's north field (local (43.8/44.7/45.6, 12.7)) sit in a 0.8 mm-deep pocket at the fill's south edge, bounded by L201's own `L201_MID` land. Measured on the actual copper with the resistive-sheet solve: the north block's **peak** linear current density at the declared 7.0 A is **1.126 A/mm** (equivalent width **6.22 mm**, dT ~7.6 C) and at the three flagged vias it is **0.473 A/mm** (equivalent width 14.8 mm, dT ~1.1 C). The transition itself has 30 vias against the 14 required. Deliberately **not** "fixed" by deleting those three vias, which would satisfy the metric without changing any current. |
| 5 | `check_return_path` | `/SW` | - | 1 | The L301 west terminal land, s1.2 above. 27 % of the reported deficit is off the board (the k x w corridor of a 1.2 mm stub 11.894 mm wide runs 35.68 mm past its own ends); the rest is zone B, where D4 forbids an inner plane because a plane under a PCB air-core spiral is a shorted turn. The /SW **pour** is 96.13 % imaged on In1 and the C_shunt bank and L202.1 are 100 % imaged, so the switching loop is intact; the unimaged section adds **0.24 nH**, 0.15 % of the 164 nH it feeds and 0.30 V of `L.di/dt` against a 143 V node. In1 could be extended 0.45 mm before entering L301's keepout circle, which changes none of these numbers. |
| 6 | `check_thermal` | `GND` | `["Q201","Q202"]` | 2 | `Q20x dissipates 5.63 W into 645 mm2 of GND copper: ~288 C rise (theta_JA ~51 C/W) > 25 C allowed`. **The check is heatsink-blind and this is confirmed in its source**: `check_thermal.theta_ja()` is `theta_floor + (theta_0 - theta_floor).exp(-A/tau)` with `(140, 45, 235)` for a multilayer board - copper area is its *only* input, there is no heatsink, TIM or airflow term anywhere in the module, and its own docstring calls it "a screen, not a sign-off ... +/-30 %". This board is designed around a **bolt-on bottom-side heatsink with forced air**, and the architecture's own path is `theta_JB 3.75 + theta_BS 1.5 + theta_HS 0.7 = 5.95 C/W` for the pair (D1), giving **Tj ~123 C nominal / ~142 C at the max-datasheet corner** with R205/R206 at 6R8 (`route-notes.md` s14), against the EPC2019's 150 C absolute maximum. **Compensating control, and it is a hard requirement, not a preference: theta_HS <= 0.7 C/W MEASURED, forced air (OPEN-9 / HS-1).** Without it a single FET reaches 175 C nominal and the pair does not close either. HS-2 (no untented vias, no through-hole pins in the land) and HS-3 (THT pads clear of the land) travel with it. |
| 7 | `check_thermal` | `/tank/TANK_A` | `["L301"]` | 1 | `L301 dissipates 10.00 W into 256 mm2 of /tank/TANK_A copper: ~769 C rise`. L301 is an **etched PCB air-core spiral**, not a placed part: its conductor is a custom-shaped SMD pad that `geom` models as its 2.8 x 8.0 mm land rect, so the 256 mm2 the check measures is the tank *pour*, not the winding. `constraints.json` says so in its own `_net_note` ("net added at P8 so check_thermal can run ... the authoritative thermal case for the spirals is `reports/spiral-design.md`, NOT this gate"). The real numbers, from `spiral-design.md` s4: **2.57 W** (not 10.0 W - the 10.0 W entry is the Q=100 planning figure; the drawn part measures Q 388) into **860 mm2** of plan area = **2.99 mW/mm2** against SPIRAL-1's 7 mW/mm2 rule, i.e. **2.3x clear even on the pessimistic proximity derate**. dt_c 70 is design intent; the copper runs 100-140 C and that is why TG155+ high-Tg FR4 is a mandatory order-time option (D5, carried to P10). |
| 8 | `check_thermal` | `/tank/TANK_B` | `["L302"]` | 1 | Same, L302: measured **2.06 W** into 833 mm2 = **2.48 mW/mm2** against 7, and the check sees 1 mm2 of TANK_B pour because the winding is a pad. `spiral-design.md` s4 is the authoritative case. |

**Caveat on entry 1, carried forward from `route-notes.md` s13.** 10 of the 21
creepage findings are track-to-track and carry **empty** `refs`, so the subset
test cannot exclude a future /SW creepage error elsewhere on the board that also
has empty refs. The waiver cannot be made tighter through this matcher; the
compensating control is that **the count is fixed at 21** - if `check_creepage`
ever reports more, the delta must be read, not waived.

---

## 3. The 159 WARNINGS - triage

The verify gate fails on `error` only (`fail_severities: ["error"], max_count: 0`),
so none of these gates the board. Listed for completeness; nothing here needs a
sidecar entry.

| count | source / kind | verdict |
|---|---|---|
| 119 | `check_current` `insufficient_transition_vias`, **all `derived`/`advisory`** | The synthesized GND return-net entry (`check_current.derived_return_entry`: no board declares its return net, so one is synthesized at the largest rail's 7.0 A with plane-fed semantics). Every GND stitch via is a single-via cluster by construction, so all 119 are the documented labelled worst-case screen. The module's own docstring says error severity is not justified for these. |
| 13 | `check_current` `pour_neckdown`, derived GND | Same derived entry, applied to the GND planes. GND is carried by three solid planes (In1 5569 / In2 5734 / B.Cu 5999 mm2) plus a 2003 mm2 F.Cu blanket; the budget (7.0 A, = the largest declared rail) is a heuristic. |
| 8 | `check_current` `undersized_track`, derived GND | The EPC2019 source escapes (0.25 mm, forced by a 0.6 mm bump pitch) and GND signal-return stubs. Same class as entry 2. |
| 5 | `check_current` `undersized_track` on `/SW` `/tank/*` at warning severity | Advisory duplicates of the entry 2/3 class. |
| 4 | `check_decoupling` `decoupler_distance` (C106, C201, C202, C213) | Placement-derived, all inside the P6 approved floorplan: C201/C202 cannot get closer to U201.A1 than the OUTL wrap allows (`route-notes.md` s10 - the wrap encloses U201's ball array and C202), and C106/C213 are bulk parts whose 3.0 mm sidecar limit is tighter than the class default. **These are the D6/SIM-6 loop-inductance items and belong to the P6 backward edge already named in `route-notes.md` s5 item 4** (re-place U201 so OUTL nests inside OUTH), not to P8. |
| 2 | `check_decoupling` `decoupler_loop` (C201 ~6.1 nH, C202 ~3.1 nH vs a 0.3 nH sidecar limit) | Same root cause, same owner. The 0.3 nH figure is the VDD-loop *budget* from `constraints.json`; the estimator is 0.7 nH/mm + 1 nH/via, so it counts the In2 hop's vias. Real mitigation is the re-place, not a P8 edit. |
| 3 | `check_creepage` warnings | Same intra-EPC2019 class as entry 1, already labelled by the check itself: *"land-pattern pitch (same footprint Q20x) - part-selection scope, not layout"*. |
| 2 | `check_thermal` `thermal_vias` (Q201, Q202: "found 3, want >= 10") | **The real count is 9 per FET, not 3** - `check_thermal` counts vias within `max(2.0, sqrt(pad_hull_area/pi) + 1.5)` = **2.27 mm** of the footprint centroid, and an EPC2019's pad hull is 1.84 mm2, so its window is smaller than the array. Measured: **9 GND vias within 4.0 mm of each FET centroid** (Q201 also has a 10th at 4.6 mm). So the router's "9 achievable, the 0.8 mm HV rule caps the landing area" is confirmed, against `min_vias: 10`. **It does not change the thermal answer:** the dominant board-through path is broad-area conduction from the 645 mm2 F.Cu GND island to In1 across the **0.2444 mm** L1-L2 dielectric (~0.8 K/W), and a 9-via array (barrel-only, ~169 K/W each -> ~18.8 K/W) is a parallel helper worth a few percent; 9 vs 10 moves the combined figure by <0.01 K/W, i.e. **<0.1 C of Tj**. The real thermal uncertainty is **OPEN-10** (`theta_BS = 1.5 C/W` for the pair is assumed, not simulated, and carries 17 C of the 85 C junction budget) - that is what should be closed, not the via count. |
| 6 | `check_silk` `silk_misattributed` (R203, R204, R205, C202, C213, U201) | Real and NOT fixed, deliberately. The criterion is: refdes > 1.0 mm from its own pads AND < 1.0 mm from another part's pads. A grid search over every position within 4 mm of each part, requiring <= 1.0 mm to its own pads, >= 1.0 mm to every other part's pads and no overlap with any pad, finds: **R203 - 0 legal positions**, C202 - 3, R204 - 6, C213 - 125, R205 - 857, U201 - 246. The gate-drive cluster is simply too dense for per-part labels (U201 is a 0.4 mm-pitch WCSP with four gate resistors, C202 and the C101 bulk can within 0.22-0.61 mm). Moving five of six would leave R203 unfixable anyway and would risk new `silk_over_copper` / `silk_overlap` on a board whose `drc_routed` residual is a signed-off 55. **Compensating control: JLC PCBA places from the CPL, not from silk** - and the P9 silk pass owns this if the owner wants the five moved. |
| 1 | `check_pdn` `pdn_no_bulk` on `+40V` | `+40V has 1 cap(s) but no bulk reservoir (>= 1 uF)`. False by sidecar scope, true by class: the rail's bulk **is** C101/C102 (2 x 100 uF electrolytic at the input) plus the C207-C212 HF bank; `decoupling.json` only ever carried C105 (the LM5017's own 100 nF VIN bypass) because `schlib.place_ic_with_decoupling` emits IC-pin bypass entries only. Left as-is: adding C101/C102 to the sidecar would need a served IC pin they do not have, and the check is advisory. |
| 1 | `verify_all` `constraints_drift` | `architecture/constraints.json` vs `kicad/constraints.json`. **Every difference is deliberate and documented**, so this is a records question, not a board question: (a) `planes[].region` and `placement` rects are **absolute** in `kicad/` and **board-local** in `architecture/` - the P6 coordinate-trap fix (workspace LEARNINGS 2026-08-08 [constraints][COORDINATE TRAP]); reverting would re-arm the bug. (b) `power` gains `+5V_DRV` (P4-FIX review W4: FB201 splits the rail). (c) `thermal` gains `net` on L301/L302 (P8 needs it for check_thermal to run at all). (d) `placement.groups.switch` gains C213/FB201 and drops R207-R210, which do not exist. **Recommendation for the owner: retire `architecture/constraints.json`** - every script reads `kicad/constraints.json`, and a second copy in a different coordinate frame is exactly how the P6 bug happened. |

---

## 4. One new toolchain gotcha, recorded in the workspace LEARNINGS

The "a via added into an ALREADY-FILLED zone takes the ZONE's net" trap
(workspace LEARNINGS, 2026-08-08 [P7][kicad][swig]) was hit again, and this time
from a case the original entry does not cover: **3 of the 4 layers under the new
vias were +40V** (F.Cu strip fill, B.Cu bridge fill) and only In1/In2 were GND -
and the failure was **non-deterministic**. Batch 1 (8 vias) lost 1; batch 2
(the same 8 shifted one pitch west) lost 4, including three x-positions that had
*succeeded* in batch 1. `route_edit` is atomic and post-verified, so both
attempts rolled back cleanly and cost nothing. The reliable procedure is the P7
one: **strip every `(filled_polygon ...)` block, apply the ops on the bare board,
then `kicad-cli pcb drc --refill-zones --save-board`.**

---

## 5. Reproduce

    .venv/Scripts/python .claude/skills/ai-ee/scripts/gate.py --gate verify \
        boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb --out boards/rf-de-20m/reports/gate-verify.json
    .venv/Scripts/python .claude/skills/ai-ee/scripts/gate.py --gate drc_routed \
        boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb --out boards/rf-de-20m/reports/gate-drc_routed.json
    .venv/Scripts/python boards/rf-de-20m/route/verify_geom.py      # island / keepout acceptance
    .venv/Scripts/python boards/rf-de-20m/route/bus_solve.py        # the +40V resistive-sheet solve
    .venv/Scripts/python boards/rf-de-20m/route/bus_cuts.py         # branch currents per section
