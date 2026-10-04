# PCB failure modes, evals and backlog

This is the research for the owner's ask: list every kind of failure a PCB can have, turn the list into tests, implement them, run them on recent boards and fix what they find. This file is phase 1, research and a backlog only. Nothing here changes a script.

Section 1 lists 230 failure modes in 14 categories, each with how it shows, how to catch it before fab, what hwde covers now and at which ladder level (L0 prose, L1 a script reports, L2 a gate fails on it, L3 the generator makes it correct by construction; rubric in design/ladder-triage.md). Section 2 ranks the failures our own boards really had. Section 3 says how to test a check with seeded faults. Section 4 is the backlog, split so no two rows edit one file. Section 5 is a baseline of the existing gates on nine recent boards.

`docs/failure-modes.yaml` is the machine-readable twin: same mode ids, same backlog ids. A planning seat dispatches rows from it. References like `[8]` are external sources (Section 6). `T#70` is a row of design/ladder-triage.md, `L731` a LEARNINGS.md line, `B:` a boards-repo path or commit. In the backlog `S/` means `.claude/skills/hwde/scripts/`. "(hit: board)" in a mode name means we hit it for real.

Limits. Several external thresholds came from search summaries, not the live page; verify them against the fab page before hard-coding (Section 6). Some internal entries were skimmed from commit subjects and review files, so causes may be inferred. No render review was run for the baseline.

## 1. Taxonomy

### MECH - Mechanical, enclosure, connector, mounting (17)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| MECH-01 | Connector mouth faces into the board (hit: PCB-0021-A, PCB-0018-A, pd-trigger, bb-adc, usb-111FD) | board cannot be plugged in; passes place/DRC/verify/DFM | mating direction table per family; check mouth vs nearest edge | check_mating:mating_faces_inward | L2>L3 | placement does not pick orientation from the family table (T#70); still per-board fixes | T#70; L677; L731; B:PCB-0021-A |
| MECH-02 | Connector mouth recessed behind board edge (hit: pd-trigger, usb-buck, bb-mcu) | plug does not seat (0.4-0.5 mm inset) | inset limit per family | check_mating:mating_mouth_inset | L2>L2 | none after cd6ca77; keep a mutant | B reviews; cd6ca77 |
| MECH-03 | Plug insertion zone blocked by a part or wires | plug or cable hits a tall part | keepout in front of the mouth | check_mating:mating_zone_blocked | L2>L2 | only declared families | cd6ca77 |
| MECH-04 | Mouth direction unreadable from footprint (hit: usb-111FD) | check cannot decide, only warns | family table entry or explicit direction | check_mating:mating_direction_unknown | L1>L2 | warning only; unknown families pass | L677; cd6ca77 |
| MECH-05 | Mated pair pinout mirrored or rows swapped (hit: lumina-par, g0-sense) | supply shorts to GND when daughter board reverse-mounts | map pin names across the pair; flip for B.Cu mount; pin-1 per 3 sources | none | L0>L2 | no mated-pair net check; fp_verify has no pin-1 rule (T#323) | B:commit 2026-08-07; T#323; L4739 |
| MECH-06 | Identical unkeyed connectors with different rails (hit: bb-mcu) | one-position slip puts a push-pull output on +3V3 | pin-compatibility review of same-family pairs; key or distinct families | none | L0>L2 | none | B:PCB-0011-A |
| MECH-07 | Terminal block or JST entry side misjudged (hit: bb-adc, bb-mcu, bb-amp) | wire entry faces into board; side-entry land mirrored | entry face from datasheet; family table | check_mating (when family listed) | L1>L3 | entry side not in table for all families (T#70, T#189) | L2418; B:PCB-0014-A |
| MECH-08 | 3D model offset flips apparent orientation (hit: pd-trigger) | render and WRL bbox mislead review | compare model origin to footprint origin | none | L0>L1 | T#124 open | L731; L1359; T#124 |
| MECH-09 | Mounting pattern differs from ICD or enclosure (hit: lumina-carrier, rp2040-mini, bb-buck) | board does not fit; holes 94x74 vs 90x70 | compare holes and outline to requirements/ICD | none | L0>L2 | no brief-vs-board check | B:PCB-0004-A; B:PCB-0019-A |
| MECH-10 | Mounting hole keepout violated or hole cut by notch (hit: lumina-par, usbbuck4) | screw head hits part; hole open to notch | no SMD or track within ~2-3 mm of hole; pad vs head dia | place_metrics:keepout_violation (declared only) | L1>L2 | keepouts only if declared; schematic holes trip own keepouts (T#220) | L927; L2884; B:PCB-0005-A |
| MECH-11 | MLCC or BGA in a board-flex zone | cap cracks after depanel or screw-down | MLCC >=5 mm from edge, V-score, mount hole; axis parallel to flex | none | L0>L2 | none | [8][28] |
| MECH-12 | Mounting holes cannot be placed or leave no standoff (hit: rf-term-150w, pd-trigger) | no hole at wire-tug corner; 3 holes on a 26 mm edge | hole pad dia (not drill) sets width; corner standoffs | none | L0>L1 | none | L2325 |
| MECH-13 | Hole size or plating wrong (PTH vs NPTH, under-drilled library part, plated pegs) (hit: bb-buck, bb-mcu, pd-trigger) | screw or pin does not fit; zero-annulus pegs | drill = pin + 0.2-0.3 mm; NPTH explicit | fp_verify:drill_mismatch; dfm_check:dfm_hole_size | L1>L2 | fp_verify has no drill handling for imports (T#8) | L712; L1256; [1] |
| MECH-14 | Part height or protrusion vs enclosure, shim or heatsink (hit: rf-term-150w) | trimmer 4.75 mm below board vs 1.00 mm shim | 3D envelope vs mechanical limits in requirements | none | L0>L1 | no height budget check | B:commit 2026-08-09 |
| MECH-15 | Heatsink land, clamp or mask opening missing (hit: rf-de-20m) | power part has no thermal path to sink | requirement-driven keepout and mask opening | none | L0>L1 | none | B:PCB-0007-A |
| MECH-16 | Castellated or half-hole edge not buildable (hit: rp2040-mini) | fab cannot make it; plain PTH pads shipped instead | flag at requirements; hwde cannot build it | castellated_fp.py (generator) | L1>L2 | requirements not checked against flow capability | B:PCB-0019-A; [26] |
| MECH-17 | Outline closed, valid and consistent (hit: pd-trigger) | interior rect read as outline; edit drops cutouts; board grown without pour resize | closed Edge.Cuts, radii >= 0.5 mm, zone outline follows edge | dfm_check:dfm_open_outline | L2>L2 | grown-board zone check is L0 (T#308, T#96) | 2026-08-16; L964; T#308 |

### THERM - Thermal (13)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| THERM-01 | Regulator or LDO dissipation exceeds copper (hit: g0-sense, sbuck-5v3a, lipo-boost) | thermal shutdown, hot board | P = dV*I vs copper area and layers | check_thermal:thermal_area | L2>L2 | model ignores back-side pour (T#331); score is area only | L2788; L4891; [16] |
| THERM-02 | Tj above abs max from optimistic theta (hit: rf-de-20m, lumina-carrier) | part over 150 C (EPC2019 theta_BS, 1 A bridge 176 C) | size on RthJA at real copper, not headline | check_thermal (partial) | L1>L2 | no Tj vs abs-max compare (T#112) | L1210; B:PCB-0007-A |
| THERM-03 | Thermal vias under EP below datasheet minimum (hit: bb-buck, bb-ldo, rf-de-20m) | 9 vs 12 vias; high theta_JA | via count and pitch per datasheet | check_thermal:thermal_vias | L1>L2 | min_vias documentary; window too small (T#214, T#276) | L2788; L3863; B:PCB-0010-A |
| THERM-04 | Exposed pad missing or mis-sized from package name (hit: buck-5v3a) | no EP land (DFN3020 has none); unsolderable | read land pattern from datasheet; pad count | fp_verify:pad_count (partial) | L1>L2 | T#211 open | L2736 |
| THERM-05 | EP paste aperture or via wicking (hit: bb-ldo, rf-de-20m) | void or open joint under QFN | window-pane paste 50-80%; tent or fill vias | dfm_check:dfm_pad_tented (partial) | L1>L2 | no paste-aperture check (T#285) | L4106; [6] |
| THERM-06 | Trace or plane heating at current (hit: PCB-0017-A, PCB-0018-A) | discolored trace, V drop | IPC-2152 width at declared dT | check_current:undersized_track | L2>L2 | noise on plane-fed rails (see backlog noise row) | [12] |
| THERM-07 | Inductor saturation or Irms heating | efficiency collapse, EMI | Isat >= 1.2-1.3 x Ipeak; Irms vs dT | check_ratings (not for inductors) | L0>L2 | no inductor rating rule | [16] |
| THERM-08 | Hot part near heat-sensitive part | reference, NTC, crystal, battery drift | placement distance rule from thermal map | none | L0>L1 | none | [27] |
| THERM-09 | Electrolytic life at board temperature | ESR rise, dry-out | life halves per +10 C; 105 C part; away from heat | none | L0>L1 | none | [14] |
| THERM-10 | Switching and conduction loss in FET or driver (hit: rf-de-20m) | BLDC or class-D FET hot | Qg*f*V, Rds(on) at hot Tj, dead-time diode loss | none | L0>L1 | no loss calc | [21][22] |
| THERM-11 | Charger or battery thermal path missing (hit: lipo-boost) | cell overheats | NTC wired, charge current <= C-rate | none | L0>L1 | none | [27] |
| THERM-12 | 2L board rise far above declared (hit: sbuck-5v3a, lipo-boost) | BQ24074 rise ~81 C vs 40 C declared | thermal model with real layers | check_thermal | L2>L2 | calibration only | B:commit 2026-08-09 |
| THERM-13 | Hot surface or hand-touch hazard not marked (hit: rf-term-150w, lumina-par) | burn on 48 V bench board | hazard silk when Tsurface > limit | none | L0>L1 | none | B:reviews |

### RATE - Electrical ratings and part values (25)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| RATE-01 | Capacitor voltage rating below worst case | cap shorts or vents | rated V >= 1.5-2x incl. spikes | check_ratings:rating_over_voltage | L2>L2 | needs datasheet extraction | [14] |
| RATE-02 | Pin absolute-maximum exceeded (V or I) (hit: rf-de-20m) | damaged part | extracted ratings vs net voltage and current | check_ratings:rating_over_voltage,rating_over_current | L2>L2 | only parts with extraction | [26] |
| RATE-03 | Reverse polarity or input above supply | part damaged when mis-wired | ratings check and ideal-diode review | check_ratings:rating_reverse_polarity | L2>L2 | none | [10][27] |
| RATE-04 | Part has no ratings on file (hit: all) | check silently covers nothing | extract every part's ratings | check_ratings:rating_unrated | L1>L2 | warning only; 3-18 per board | baseline.md |
| RATE-05 | Outside recommended operating range | part out of spec but not destroyed | recommended range vs operating point | check_ratings:rating_outside_recommended | L2>L2 | none | [10] |
| RATE-06 | Polarized part reversed (electrolytic, tantalum, diode, LED) (hit: sbuck-5v3a, rf-de-20m, g0-sense) | pop, vent, dead FET (Zener marker on anode pad) | silk and footprint polarity vs datasheet; chamfer meaning | dfm_check:cpl_polarity (diodes) | L2>L2 | caps and tantalum not covered; marker-on-wrong-pad not checked | B:commit 2026-08-09; L3387; L4721 |
| RATE-07 | Feedback divider gives wrong Vout (hit: buck-5v3a) | 0.8 V instead of rail; overvoltage | recompute Vout from Vfb and resistor values | sim_run (bench only) | L1>L2 | no static recompute from netlist | L2648; [10] |
| RATE-08 | Fixed vs adjustable regulator mislabeled (hit: buck-5v3a) | FB tied to Vout gives 0.8 V | datasheet variant vs vendor type field | none | L0>L2 | T#205 open | L2648 |
| RATE-09 | Logic level or 5 V tolerance mismatch | misread input, back-power | Vol/Voh vs Vil/Vih across rails | none | L0>L2 | none | [10] |
| RATE-10 | Pull-up or pull-down missing or wrong value (hit: lumina-par) | I2C stuck; enable latched | pull-ups present, value for Cbus; bias current in pull-down sizing | none | L0>L2 | T#194 open: gates see topology, not value | L2493; [10] |
| RATE-11 | Unconnected pin or floating input | erratic behaviour | ERC pin_not_connected; tie unused inputs | kc.py (ERC) | L2>L2 | no ERC mutant corpus | [10][11] |
| RATE-12 | Two outputs drive one net | heat, damage | ERC pin conflict | kc.py (ERC) | L2>L2 | no ERC mutant corpus | [11] |
| RATE-13 | Power sequencing or enable pin undefined at power-up (hit: lumina-par) | drivers latched ON when +12V arrives before +3V3 | enable pull-downs, sequencing review | none | L0>L2 | T#194 open | L2493; [11] |
| RATE-14 | Gate voltage beyond Vgs max (hit: rf-de-20m) | eGaN +6 V max with 5 V drive; destroyed on first pulse | Vgs max vs worst-case drive rail | check_ratings (only if pin extracted) | L1>L2 | gate-network rule missing (T#254) | L3360 |
| RATE-15 | Gate resistance below driver floor or FETs paralleled on one pin (hit: rf-de-20m) | 0.975 ohm vs 2 ohm floor | network total R vs datasheet | none | L0>L2 | T#254 open | L3360; B:PCB-0007-A |
| RATE-16 | Bootstrap cap undersized (hit: rf-de-20m) | 2.2 nF vs 10 nF needed; driver undervoltage | Cboot >= 10x total Cgs | none | L0>L2 | none | B:PCB-0007-A; [21] |
| RATE-17 | Dead time, shoot-through, gate pull-down missing (hit: bldc-motor-driver) | FET destroyed | dead time > turn-off delay; pull-down on each gate | none | L0>L2 | none | [21] |
| RATE-18 | Driver UVLO margin at minimum supply | partial enhancement, heat | VCC >= UVLO + margin | none | L0>L2 | none | [21] |
| RATE-19 | Inrush or hot-plug current | USB source collapses; fuse trips | soft-start, bulk C limit | none | L0>L1 | none | [17] |
| RATE-20 | Crystal load capacitance wrong | no start or ppm error | CL = C1*C2/(C1+C2)+Cstray; drive; ESR | none | L0>L2 | none | [15] |
| RATE-21 | Set-resistor pin wrong (ILIM, ISET, UVLO, charger) | wrong current or threshold | recompute from datasheet equation | none | L0>L2 | none | [10][27] |
| RATE-22 | Charger configuration wrong (hit: lipo-boost) | LiPo overcharged | float 4.2 V, termination, precharge, NTC | none | L0>L1 | none | [27] |
| RATE-23 | Invented or misread datasheet values drive the design (hit: rf-de-20m) | Coss and Rds(on) wrong; frozen operating point false | second reader on extracted values; cite page | none | L0>L2 | T#251 open | L3295 |
| RATE-24 | Part derating ignored (fuse voltage, DC bias, tolerance) (hit: CH224 boards) | 1206 PPTC cannot hold 1 A at 30 V | derating tables in parts check | none | L0>L1 | none | 2026-08-15 [parts] |
| RATE-25 | Control loop unstable or ripple injection missing (hit: bb-buck) | COT buck has 1-2 mV at FB vs 20 mV | compensation and ripple-injection calc; SPICE | sim_run (bench only) | L1>L2 | no static check | B:PCB-0010-A |

### PI - Power integrity (20)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| PI-01 | Missing HF decoupling on an IC supply pin (hit: lumina-carrier, rp2040-mini) | resets, ADC noise; 100 nF absent on buck VIN | cap per pin within 2-5 mm | check_decoupling:reg_input_no_hf; check_pdn:pdn_undecoupled | L2>L2 | checker classed by value, cannot see absence (L1980); per-pin count none | L1980; [15][19] |
| PI-02 | Decoupler far from pin or high loop inductance (hit: lumina-carrier, bb-adc) | ringing, droop | distance and loop nH limit | check_decoupling:decoupler_distance,decoupler_loop; place_metrics:decoupler_distance | L2>L2 | centre-to-centre rules; locked refs skipped (T#197, T#219) | B:PCB-0004-A; 2026-08-19 |
| PI-03 | Decoupling cap with long GND stub (hit: PCB-0017-A, lipo-boost) | HF bypass lost | stub <= 5 mm to GND via | check_decoupling:gnd_stub_long | L2>L2 | warning only | baseline.md |
| PI-04 | Rail without bulk cap | brown-out on load step | bulk cap per rail | check_pdn:pdn_no_bulk | L1>L2 | warning only | [16] |
| PI-05 | Buck hot loop or switch-node copper too large (hit: lumina-par, sbuck-5v3a) | EMI, ringing | loop area from input cap + switch + GND; SW copper min | none | L0>L2 | annealer ignores loops (T#219) | L2872; [16] |
| PI-06 | Feedback trace near switch node | jitter, wrong regulation | FB over ground, away from SW | none | L0>L2 | none | [16] |
| PI-07 | Track too narrow for current (hit: PCB-0017-A, PCB-0018-A, PCB-0019-A) | heating, V drop | IPC-2152 width | check_current:undersized_track | L2>L2 | noisy on plane-fed rails; per-segment current unattributed | [12] |
| PI-08 | Pour neck or too few vias at layer transition (hit: PCB-0021-A, PCB-0018-A, g0-sense) | IR hotspot | neck width and via count | check_current:pour_neckdown,insufficient_transition_vias | L2>L2 | seam in tiled pours read as neck (T#330); 277 errors on one board | L4868 |
| PI-09 | DC IR drop to far loads | rail low at load | 2.5D resistive solve | check_irdrop | L1>L2 | not in verify (recipe only) | [26] |
| PI-10 | Plane-pair impedance or antiresonance (hit: usbbuck4) | rail resonance | cavity Z(f) vs target | check_pdn_z | L1>L2 | not in verify; band-edge model | L991 |
| PI-11 | Single thin track severs a poured power bus (hit: rf-de-20m) | 10.4 mohm, 369 mW hot spot, DRC clean | net connectivity through copper, not tracks | check_current (partial) | L1>L2 | T#274 open | 2026-08-08 [P8] |
| PI-12 | Via swallowed by track or takes the zone's net (hit: rf-de-20m) | stitch via lost; GND island open | via net vs intended net; dangling via | none | L0>L2 | T#263, T#270 open | L3565; L3732 |
| PI-13 | Pad starved of pour by neighbouring track (hit: rf-de-20m) | WCSP GND ball unconnected, no DRC | pad connectivity count | none | L0>L2 | T#271 open | L3747 |
| PI-14 | Thermal relief starves a high-current pad (hit: pd-trigger) | 2.5-5 A pad on thin spokes | connect_pads yes on power pads | planes_gen (generator) | L3>L3 | no check on hand-edited boards | L782; L832 |
| PI-15 | Pour missing, not resized, or constraint rect offset (hit: rf-de-20m, bb-buck, sbuck-5v3a) | no pour under buck; plane over spiral; keepouts unenforced | constraint coords vs outline origin; zone covers declared area | check_current:plane_missing (partial) | L1>L2 | T#221, T#260, T#200 open | L2892; L2586 |
| PI-16 | No return plane under magnetics (hit: rf-de-20m) | 23-30 nH instead of 4 nH; ZVS lost, 121 W -> 53 W | loop L estimate with plane present | check_return_path:no_reference_plane (partial) | L1>L2 | checked signals, not power loops (T#280) | L4007 |
| PI-17 | Net-class widths unmeetable at fine pitch or one class for all power (hit: pd-trigger) | 20 mA nets at 1.75 mm; USB-C pads unroutable | per-net width with pad-limited neck | rules_gen (generator) | L2>L3 | T#224 open | L782; L798 |
| PI-18 | Motor back-EMF or regen pumps the bus (hit: bldc-motor-driver) | bus overvoltage on decel | bus cap and TVS sized for regen | none | L0>L1 | none | [21] |
| PI-19 | Class-D supply bounce or ground return (hit: stereo-class-d-amp) | hum, THD | PVDD decoupling at IC, solid ground | none | L0>L1 | none | [22] |
| PI-20 | Regenerating the schematic wipes netclasses or decoupling data (hit: rf-de-20m) | decoupling.json lost, +5V rule gone | round-trip test of sidecars | none | L0>L3 | T#265, T#282 open | L3614; L4048 |

### PROT - Protection (12)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| PROT-01 | No ESD protection on a user-touch connector | latent or total failure | TVS or ESD array at each external port | none | L0>L2 | not observed on our boards yet, but nothing checks | [11][20] |
| PROT-02 | TVS standoff or clamp wrong for the rail | conducts at VBUS or clamps too high | VRWM > Vmax; Vclamp < downstream abs-max | none | L0>L2 | none | [17] |
| PROT-03 | ESD return path long | clamp ineffective | TVS ground via adjacent, short path | none | L0>L2 | none | [20] |
| PROT-04 | No overvoltage or reverse protection on input | regulator burned by bad supply | OVP, Zener plus fuse, PD 20-28 V vs rail | none | L0>L2 | none | [17] |
| PROT-05 | No overcurrent protection on VBUS or battery | runaway, fire | fuse, PTC or e-fuse | none | L0>L2 | none | [27] |
| PROT-06 | LiPo protection absent (hit: lipo-boost) | overdischarge or short fire | protection IC, UVLO ~3.0 V | none | L0>L2 | none | [27] |
| PROT-07 | Hot-plug transient exceeds ratings | VBUS spike | TVS and damping | none | L0>L1 | none | [17] |
| PROT-08 | Shield or chassis bonded wrongly | ground loop, ESD through logic | single bridge R parallel C | none | L0>L1 | none | [20] |
| PROT-09 | Unprotected inputs on harness (hit: lumina-par, lumina-carrier) | comparator inputs see 6.8-24 V | series R and clamp on cable-fed inputs | none | L0>L2 | none | B:commit 2026-08-07 |
| PROT-10 | Unfiltered or unclamped long I/O traces (hit: lumina-carrier, bb-mcu) | LED lines 55-73 mm into PHY; NRST on flying lead | RC or ferrite at entry | none | L0>L1 | none | B:PCB-0004-A; B:PCB-0011-A |
| PROT-11 | Overtemperature path unused | cell not shut down | NTC to charger TS or ADC | none | L0>L1 | none | [27] |
| PROT-12 | RF input lacks ESD or matching pads | LNA damaged | low-C diode, Pi pads | none | L0>L0 | rare | [24] |

### EMC - ESD and EMC (13)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| EMC-01 | Signal crosses a plane gap or loses its return corridor (hit: esp32c3-node, usbbuck4) | radiation, ESD upset | corridor of continuous ground under fast nets | check_return_path:corridor_void | L2>L2 | 2L coplanar FP; short fan-in land misread (T#235) | L194; L3058 |
| EMC-02 | Layer change without return via (hit: rf4) | return path breaks | stitch via within 1-2 mm | check_return_path:missing_return_via,missing_stitch_cap | L2>L2 | none | [18][24] |
| EMC-03 | No reference plane under a fast net (hit: lumina-carrier) | impedance and EMI | ground plane adjacent layer | check_return_path:no_reference_plane | L2>L2 | nearest plane may be a power plane (fixed) | L1774 |
| EMC-04 | Fast net near plane edge | edge radiation | keep >= 20H from plane edge | none | L0>L2 | none | [19][20] |
| EMC-05 | Long clock or fast edge on outer layer (hit: lumina-carrier) | radiated emissions | short, damped, referenced; length cap | none | L0>L2 | none | B:commit 2026-07-30; [19] |
| EMC-06 | Large switching loops (class-D, motor, buck) | fails EMC | loop area budget | none | L0>L2 | see PI-05 | [16][22] |
| EMC-07 | Unfiltered I/O at connector entry (hit: lumina-carrier) | emissions couple in/out | RC or ferrite at entry | none | L0>L1 | none | [19][20] |
| EMC-08 | Stitching vias too sparse or tied to THT drills (hit: rf-term-150w, pd-trigger) | resonant gaps; vias 0.12 mm from drill | pitch ~lambda/20; keep clear of drills | stitch_vias.py (generator) | L3>L3 | generator ignores THT drills (T#227) | L819; L2954 |
| EMC-09 | Common-mode on cable | emissions | choke, shield termination | none | L0>L1 | none | [18][20] |
| EMC-10 | Phase or motor traces form an antenna (hit: bldc-motor-driver) | emissions | short wide phase traces | none | L0>L1 | none | [21] |
| EMC-11 | MCU resets on ESD | upset | RC on reset and boot, watchdog | none | L0>L1 | none | [15] |
| EMC-12 | Routing style: arcs, off-45 segments, needless jogs (hit: PCB-0018-A, rp2040-mini) | owner preference; stress | 45-degree grid | check_route_style:route_style | L1>L1 | warning only by design | memory routing-style |
| EMC-13 | Antenna keepout wrong or module pads inside it (hit: lumina-carrier) | six pins unconnectable | keepout from module datasheet | place_metrics:keepout_violation | L2>L3 | T#123 open; false positives (T#125) | L1345; L1373 |

### SI - Signal integrity (13)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| SI-01 | Diff-pair impedance off (hit: lumina-carrier) | enumeration errors | 90 ohm +/-15% from stackup | check_diffpair:diffpair_impedance | L2>L2 | table, not solver (V12/V18) | [18][1] |
| SI-02 | Diff-pair skew over limit (hit: lumina-carrier) | eye closure | < 0.15 mm FS/HS | check_diffpair:diffpair_skew | L2>L2 | FP on LF pairs | L1564; [18] |
| SI-03 | Uncoupled length or meander adds length (hit: usb-buck) | skew traded for loss | uncoupled length cap | check_diffpair:diffpair_uncoupled | L2>L2 | none | L311 |
| SI-04 | Via asymmetry in a pair | common-mode conversion | matched vias | check_diffpair:diffpair_via_asymmetry | L2>L2 | none | [18] |
| SI-05 | Open trunk or mesh route on a 3-pad pair (hit: lumina-carrier) | only first leg closes | connectivity of trunk | check_diffpair:diffpair_open_trunk | L2>L3 | router creates it (T#119) | L1302 |
| SI-06 | Pair not recognised (naming) | check does not run | netlist_audit diffpair_naming | check_diffpair:diffpair_missing_net; netlist_audit | L1>L2 | auto-discovery by name only | netlist_audit |
| SI-07 | Skew gate blind to pad and via ends (hit: lumina-carrier) | 35 mm vs 6 mm true; magjack 2.84 mm apart | measure end to end incl. vias | check_diffpair | L2>L2 | fixed; keep a mutant | L1564 |
| SI-08 | CPW vs microstrip, pour near controlled trace (hit: rf-term-150w) | Z0 75 vs 88 ohm | solver or coplanar formula | check_diffpair (table) | L1>L2 | T#234 open | L3046 |
| SI-09 | Order stackup or impedance template differs from design (hit: lumina-carrier) | nonexistent template; 1 oz vs 0.5 oz inner | compare order stackup to design | order_submit (partial) | L1>L3 | T#141, T#208 open | L1654; B:commit 2026-07-30 |
| SI-10 | Crosstalk spacing | corrupted data | >= 3x width or guard | none | L0>L1 | none | [19] |
| SI-11 | USB D+/D- swapped or CC wiring wrong | no detect, no 5 V | separate 5.1k Rd per CC; D+ pull-up | none | L0>L2 | none | [17][18] |
| SI-12 | Stubs and termination on fast nets | reflections | stub length cap | none | L0>L1 | none | [19] |
| SI-13 | Clock or crystal routed near sensitive input | spurs | guard, short, nothing beneath | none | L0>L1 | none | [15] |

### ANA - Analog and grounding (10)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| ANA-01 | ADC reference or analog supply noisy | jittery codes | ferrite or RC to VDDA; VREF cap | none | L0>L1 | none | [15] |
| ANA-02 | Analog and digital returns mixed | offsets | partition by placement, single crossing | none | L0>L1 | none | [20] |
| ANA-03 | Class-D output couples into inputs (hit: stereo-class-d-amp) | hum, whine | route inputs away, differential | none | L0>L1 | none | [22] |
| ANA-04 | PLL or VCO supply noise | phase noise | LC filter, own LDO | none | L0>L0 | rare | [24] |
| ANA-05 | Kelvin sense tied on global GND (hit: bldc-motor-driver) | current sense error | Kelvin net ties | none | L0>L1 | none | B:PCB-0018-A |
| ANA-06 | Sense RC too slow or wrong range (hit: bldc-motor-driver) | phase sense ~170 Hz too slow for BEMF | RC corner vs signal band | sim_run (bench only) | L1>L2 | none | B:PCB-0018-A |
| ANA-07 | Return of PWM or sense off GND plane (hit: lumina-par) | noise, shared return | reference plane under signal | check_return_path | L2>L2 | fixed | B:commit 2026-08-08 |
| ANA-08 | Anti-alias cap far from ADC (hit: bb-adc) | aliasing, noise | satellite distance rule | place_metrics (declared separations only) | L1>L2 | annealer re-derives slots (2026-08-19) | 2026-08-19 [placement] |
| ANA-09 | NTC or divider range off | wrong temperature | divider range vs ADC | none | L0>L1 | none | [27] |
| ANA-10 | Crystal layout parasitics | start failure | guard, short, no signals under | none | L0>L1 | none | [15] |

### FAB - Fab DFM (26)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| FAB-01 | Track width or spacing below fab minimum (hit: lumina-carrier) | opens or shorts | JLC 0.127 mm 2L / 0.09 mm 4L | dfm_check:dfm_trace_width,dfm_clearance | L2>L2 | held by PR #63 | [1] |
| FAB-02 | Annular ring too small | breakout | >= 0.125 mm | dfm_check:dfm_annular_ring | L2>L2 | none | [1][29] |
| FAB-03 | Hole size outside fab range | not buildable | drill table | dfm_check:dfm_hole_size | L2>L2 | none | [1] |
| FAB-04 | Hole-to-hole too close (hit: lumina-carrier) | merged drills; 0.31 mm vs 0.5 mm | JLC hole-to-hole | dfm_check:dfm_hole_to_hole | L2>L2 | generator adds vias on top of vias (T#232) | L1705; L1327 |
| FAB-05 | Hole or copper too close to board edge (hit: lumina-carrier) | exposed copper | >= 0.3 mm | dfm_check:dfm_hole_to_edge,dfm_copper_to_edge | L2>L2 | edge no-op'd when outline empty (fixed) | L2178; [2] |
| FAB-06 | Mask dam or sliver too narrow (hit: rf-de-20m) | bridging | dam >= 0.1 mm | dfm_check:dfm_mask_dam | L2>L2 | none | L3763 |
| FAB-07 | Via in pad not filled or not tented (hit: bb-ldo, rf-de-20m) | solder wicks | fill or offset | dfm_check:dfm_pad_tented (partial) | L1>L2 | T#285 open | L4106 |
| FAB-08 | Silk stroke too thin (hit: PCB-0018-A, rp2040-mini, esp32c3-node, nfc-card) | unprintable | >= 0.15 mm | dfm_check:dfm_silk_width | L1>L2 | warnings on 4 boards, likely logo graphics | baseline.md |
| FAB-09 | Silk over pad or mask opening (hit: usb-buck, pd-trigger) | solder issue | clip at openings | check_silk:silk_over_pad; dfm_check:dfm_silk_over_pad | L2>L2 | slivers are noise | L615; L687 |
| FAB-10 | Refdes attributed to the wrong part (hit: sbuck-5v3a, rp2040-mini, lumina-carrier) | reads as another part's label | nearest-pad rule | check_silk:silk_misattributed | L2>L3 | silk_place only sometimes fixes (T#238); 26 on one board | L3103 |
| FAB-11 | Silk text illegible or has no legal spot (hit: g0-sense) | unreadable | text height, legal spot | check_silk:silk_thin,silk_illegible | L2>L2 | 0.1 in header labels need 1.70 mm run | 2026-08-27 |
| FAB-12 | Outline open, layer missing, drill file missing | fab rejects | zip contents check | dfm_check:dfm_open_outline,dfm_missing_layer,dfm_no_drill | L2>L2 | none | [3] |
| FAB-13 | Project rules below fab floor (hit: lumina-carrier, bb-ldo) | DRC 0/0 but unfabricable; min_track 0.1 mm | rules floor = fab floor | rules_gen (generator) | L3>L3 | no check of .kicad_pro / .kicad_dru | L2011; L2178 |
| FAB-14 | Gerber export wrong (arcs flattened, empty outline, NPTH marked plated) (hit: lumina-carrier, rf-de-20m) | phantom edge errors; checks no-op | round-trip against board | gerblib / dfm_check | L1>L3 | T#286 open | L2510; L2178; L4140 |
| FAB-15 | Gerber vs netlist mismatch | shorts or opens in fab | IPC-356 compare | dfm_check:pad_net_mismatch | L2>L2 | none | [2] |
| FAB-16 | Slivers, acid traps, thin thermal-relief spokes | etch defects | angle and spoke checks | none | L0>L2 | none | [2][3] |
| FAB-17 | Order copper, layers or stackup differ from design (hit: buck-5v3a, lumina-carrier) | wrong 1 oz vs 0.5 oz; wrong quote | compare order payload to design | order_submit (partial) | L1>L3 | T#208, T#141 | L1654; L2678 |
| FAB-18 | Order creation fails ambiguously (hit: lumina-carrier) | HTTP 200 code 2; unknown if placed | idempotency; check order list | order_submit | L2>L3 | T#162 open | L1635; L2033 |
| FAB-19 | Imported footprint geometry self-violating (hit: pd-trigger, g0-sense, lumina-par) | EP no net; courtyard excludes pads; pad stroke inflates copper | fp_verify vs datasheet | fp_verify | L1>L2 | T#8, T#218, T#327 | L1167; L4807 |
| FAB-20 | Imported footprint metadata breaks tools (hit: rf-term-150w) | through_hole on SMD; User.Drawings layer crashes kicad-cli | sanitise on import | fpfix.py (generator) | L3>L3 | T#212 open | L2752; L55 |
| FAB-21 | Land dimension taken from envelope, not pitch (hit: rf-de-20m) | GaN gate pad 0.11 mm off | datasheet land vs envelope | fp_verify | L1>L2 | T#252 open | L3324 |
| FAB-22 | Etched-copper part (spiral) carries no net (hit: rf-de-20m) | unconnected and shorting DRC | net on fp_poly | none | L0>L2 | T#256 open | L3406 |
| FAB-23 | Per-net clearance rules pad-blind (hit: bldc-motor-driver, rf-de-20m) | 406 hv errors; Freerouting ignores DRU | pad-aware HV escape check | none | L0>L2 | T#117, T#269 open | L1280; L3715 |
| FAB-24 | Rules file silently matches nothing (hit: poe_tap) | DRU token A.Net ignored; copy outside project changes rules | lint DRU against netlist | none | L0>L3 | T#75 open | L222; L754 |
| FAB-25 | Moving a part on a routed board (hit: lumina-carrier) | pad onto live trace; orphan stubs | post-move DRC and stub check | place_edit.py (tool) | L2>L3 | T#129, T#145 | L1455 |
| FAB-26 | Mask or copper-weight capability exceeded | 2 oz needs wider spacing | capability table by weight | dfm_check (partial) | L1>L2 | none | [1] |

### DFA - Assembly, CPL, BOM, sourcing (26)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| DFA-01 | Polarized part rotated or marker on wrong pad (hit: sbuck-5v3a, nfc-card) | dead part, destroyed FET | per-pad net compare vs CPL | dfm_check:cpl_polarity | L2>L2 | per-pad compare only for diodes; marker-on-wrong-pad open | L495; B:commit 2026-08-09 |
| DFA-02 | CPL rotation depends on JLC library origin (hit: PCB-0022-A) | U1/U2 rotated = dead card | pin-1 or centroid check against fab origin | dfm_check:cpl_polarity (partial) | L1>L2 | unverifiable offline | B:PCB-0022-A |
| DFA-03 | Pad nets swapped between schematic and board | wrong connection | schematic parity | kc.py (parity); dfm_check:pad_net_mismatch | L2>L2 | none | L141 |
| DFA-04 | Part missing from BOM or CPL (hit: rf-term-150w) | whole-board function absent (250 W load) | BOM and CPL vs board refs | dfm_check:dfm_bom_incomplete | L2>L2 | exclude_from_pos_files not checked | B:PCB-0009-A |
| DFA-05 | BOM part not an LCSC part | cannot assemble | LCSC lookup | dfm_check:dfm_bom_off_lcsc | L2>L2 | none | [1] |
| DFA-06 | Footprint does not match the package | wrong part fit | footprint vs package | dfm_check:dfm_unplaced_in_package | L2>L2 | none | [10] |
| DFA-07 | DNP not machine-readable (hit: lumina-par, rf-de-20m) | 9 DNP parts populated in BOM and CPL | DNP attribute vs BOM, CPL and fields | none | L0>L2 | U3 assembly classes fixed boards; no check | L2405; B:commit 2026-08-14 |
| DFA-08 | parts.json missing, BOM leg silently skipped (hit: rf-de-20m, g0-sense) | dfm gate PASS with half the checks off | skip is a failure at release | dfm_check (strict) | L1>L2 | T#284, T#335 open | L4083; L4950 |
| DFA-09 | Part out of stock, extended-part cost, no alternate (hit: pd-trigger-lite) | order blocked | stock and basic/extended count | order_quote; distributor_bom | L1>L2 | stock at BOM review only | 2026-09 [jlc] |
| DFA-10 | Schematic and board fields out of sync (hit: rf-de-20m) | 15 footprint_symbol_field_mismatch | ERC parity | kc.py (parity) | L2>L2 | stale copies (T#283) | L4066 |
| DFA-11 | Tombstoning risk | 0402 stands up | symmetric pads and copper | none | L0>L2 | none | [4][5] |
| DFA-12 | Fine-pitch bridging or decouplers on pin tips (hit: stm32-blinky) | 9 shorts and 9 mask bridges | mask dams; courtyard from pads | kc.py (DRC); place_metrics:courtyard_overlap | L2>L2 | imported courtyards enclose body only (T#218) | L561; L1167 |
| DFA-13 | Land pattern wrong | skewed part | datasheet land vs footprint | fp_verify | L1>L2 | T#8 open | [12] |
| DFA-14 | Fiducials missing | misplacement | >= 2 board fiducials; local pair for fine pitch | none | L0>L2 | none | [7] |
| DFA-15 | Panel rails and tooling | breakage | 5 mm rails, V-score vs tab | none | L0>L1 | none | [5][7] |
| DFA-16 | Courtyard overlap or part spacing | collision, no rework | courtyard overlap; 0.2-0.3 mm gap | place_metrics:courtyard_overlap,courtyard_missing | L2>L2 | none | [5][12] |
| DFA-17 | Part near board edge | dropped on conveyor | 5 mm clear if railless | place_metrics:edge_violation (declared only) | L1>L2 | none | [5][7] |
| DFA-18 | Assembly sides, THT on SMT line, 0201 | assembly refused or low yield | economic assembly: top SMD only | none | L0>L2 | none | [1] |
| DFA-19 | Polarity cue hidden or silk misplaced (hit: rf-de-20m, g0-sense) | chamfer hidden under part; "+" on pad 1 | polarity cue vs pad function | none | L0>L2 | T#255, T#258, T#322 open | L3387; L3463; L4721 |
| DFA-20 | EP paste voiding and BGA joint risk | intermittent joint | window paste pattern | none | L0>L1 | none | [6] |
| DFA-21 | Stencil aperture area ratio | opens | ratio >= 0.66 | none | L0>L1 | none | [12] |
| DFA-22 | Passive tolerance or dielectric | drift | C0G for RF/timing; 1% for dividers | none | L0>L1 | none | [10] |
| DFA-23 | Sourcing: single source, no US distributor, price tiers wrong (hit: CH224 boards) | cannot buy | two-source check | none | L0>L1 | T#299, T#300 | L4327; L4342 |
| DFA-24 | Half-pitch or odd package pulled as through-hole (hit: pd-trigger-lite-dip) | CPL would drop it | attr vs pad types | fp_verify (partial) | L1>L2 | none | 2026-09-24 |
| DFA-25 | Tin whiskers, finish, flux residue | shorts under fine leads | finish choice; clean | none | L0>L0 | rare | [25][9] |
| DFA-26 | Assembly drawing missing | wrong orientation or DNP | assembly PDF with polarity, pin 1, DNP | none | L0>L1 | none | [10] |

### TEST - Test and bring-up access (12)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| TEST-01 | No test points on rails | cannot debug | TP per rail and GND | none | L0>L2 | none | [10][11] |
| TEST-02 | No SWD or JTAG access | cannot flash | header or pads | none | L0>L2 | none | [15] |
| TEST-03 | Bootloader entry impossible | bricked board | BOOT0 button or jumper | none | L0>L2 | none | [15] |
| TEST-04 | No power or status LED | unclear state | LED per rail | none | L0>L1 | none | [10] |
| TEST-05 | No probe labels or legal silk spot (hit: g0-sense) | misprobe | TP labels, pin 1 | check_silk (partial) | L1>L1 | none | 2026-08-27 |
| TEST-06 | Debug UART not exposed | no logs | header or TPs | none | L0>L1 | none | [10] |
| TEST-07 | Reset not reachable | cannot reset | button or TP | none | L0>L1 | none | [15] |
| TEST-08 | No board name, revision and date on silk | spin confusion | silk text | none | L0>L1 | none | [10] |
| TEST-09 | Antenna tuning or test connector missing | RF off | Pi pads, u.FL | none | L0>L0 | rare | [24] |
| TEST-10 | Gate results not recorded; ERC pass absent from state (hit: bb-buck, rf-de-20m) | six gates passed, none recorded | state.json records each gate | gate.py | L2>L2 | fixed; waiver sidecar path wrong (T#281) | B:commit 2026-08-16; L4029 |
| TEST-11 | Bench baselines pinned to one KiCad version (hit: pd-trigger) | fail on 10.0.5 | re-pin baselines on upgrade | bench.py | L2>L2 | T#317, T#338 | L4668 |
| TEST-12 | Eval corpus too thin | one mutant per check; no ERC or DRC mutants | see Section 3 | score_checks.py | L1>L2 | backlog rows multi-mutant, erc-drc-mutants | checks.md |

### FW - Firmware-hardware interface (16)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| FW-01 | Boot strap pins floating or wrong (hit: g0-sense) | wrong boot mode | BOOT0 pull-down; ESP32 strapping valid at reset | none | L0>L2 | none | 2026-08-27 |
| FW-02 | NRST handling (hit: bb-mcu) | spurious reset | 100 nF, pull-up, supervisor | none | L0>L2 | none | B:PCB-0011-A |
| FW-03 | SWD pins repurposed | cannot reprogram | keep PA13/PA14 | none | L0>L2 | none | [15] |
| FW-04 | Pin mux conflict or function absent on pin | peripheral missing | AF table per pin | none | L0>L2 | none | [15] |
| FW-05 | ADC or timer channel not on pin (hit: bldc-motor-driver) | PWM or ADC unavailable | pin table check | none | L0>L2 | none | [15][21] |
| FW-06 | Peripheral pin clash | one disables another | per-peripheral allocation | none | L0>L2 | none | [15] |
| FW-07 | USB clock accuracy or HSE failure | enumeration fails | CRS, tolerance, CL | none | L0>L1 | none | [15] |
| FW-08 | GPIO default state drives FETs at reset (hit: bldc-motor-driver) | shoot-through, motor spin | external pull-down; tri-state at reset | none | L0>L2 | none | [21] |
| FW-09 | Driver enable polarity or missing enable (hit: bldc-motor-driver) | outputs live at reset; arming only via TIM1 MOE | pull-down on EN | none | L0>L1 | design constraint | B:PCB-0018-A |
| FW-10 | GPIO current limits | LED overcurrent | per-pin and port limits | none | L0>L1 | none | [15] |
| FW-11 | Interrupt or wake pin floating; sleep leakage | spurious wake, drain | pull states, Iq | none | L0>L1 | none | [27] |
| FW-12 | Programmer level mismatch | no VTref | VTref on header | none | L0>L1 | none | [10] |
| FW-13 | LSE or HSE expected but absent | RTC off | config vs hardware | none | L0>L1 | none | [15] |
| FW-14 | Firmware pin map out of date vs layout | works only with wiring hacks | pin map regenerated from netlist, diff each spin | fwe pinmap (outside hwde gates) | L1>L2 | not a hwde gate | [10] |
| FW-15 | Strap table inverted (hit: pd-trigger) | would select 5 V not 9 V | strap logic vs ON=GND | none | L0>L1 | fixed by hand | L843 |
| FW-16 | Complementary timer pins not on one timer | BLDC drive impossible | timer pin table | none | L0>L2 | none | [21] |

### SAFE - Safety and compliance (11)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| SAFE-01 | Spacing too small for working voltage (hit: lumina-carrier, PCB-0018-A) | arc or tracking | IPC-2221 / creepage table | check_creepage:creepage | L2>L2 | 36 FPs on golden; pairs counted as one (T#196) | L1600; L1889 |
| SAFE-02 | High-voltage nets not declared (hit: lumina-par) | 3 of 7 >= 30 V nets covered; inherits 0.1 mm floor | every >= 30 V net in voltages and DRU | none | L0>L2 | T#147, T#198 open | L1785; L2559 |
| SAFE-03 | Isolation barrier collapsed by a replacement footprint (hit: lumina-carrier) | 3.58 -> 1.05 mm vs vendor 1.40 mm | declared barrier checked vs footprint | check_creepage (partial) | L1>L2 | barrier not declared | L1110; L1226 |
| SAFE-04 | Creepage modelled on wrong pad shape or signed voltage (hit: lumina-carrier) | 0.3-0.5 mm answer shift; 8 invented errors | pad shape, coating, abs voltage | check_creepage | L1>L2 | T#196 open | L1401; L1889 |
| SAFE-05 | Net-tie or on-die pitch below rule (hit: rf-de-20m) | 0.35 mm pitch on 200 V die; 0.014 mm turn gap | waivable intra-die only | none | L0>L2 | T#259 open; DRC blind in net-tie | L3470 |
| SAFE-06 | Hazard marking absent (hit: lumina-par) | 48 V bench board unmarked | silk for > 50 V and hot surfaces | none | L0>L1 | none | B:commit 2026-08-08 |
| SAFE-07 | Exposed high-voltage test points | shock | no exposed > 50 V TPs | none | L0>L1 | none | [13] |
| SAFE-08 | Battery cell certification and shipping | fire, UN38.3 | process rule | none | L0>L0 | out of scope for eda | [27] |
| SAFE-09 | USB-C PD sink non-compliance | source damaged; draws > 0.5 A early | Rd on each CC; negotiation | none | L0>L2 | none | [17] |
| SAFE-10 | RF regulatory and RoHS | FCC, CE fail | module vs intentional radiator | none | L0>L0 | out of scope | [24][25] |
| SAFE-11 | CTI and pollution-degree assumption | surface tracking | FR4 CTI 175-250 V; PD2 | none | L0>L1 | none | [13] |

### CONC - Conceptual and requirements (16)

| id | mode | how it shows | how to catch before fab | hwde coverage now | level now>target | gap | sources |
|---|---|---|---|---|---|---|---|
| CONC-01 | Brief number has no calc or sim behind it (hit: PCB-0022-A) | board powers but misses spec | requirement-to-design trace table | none | L0>L2 | no brief trace check | [26] |
| CONC-02 | Requirements amended elsewhere, not in requirements.md (hit: PCB-0019-A, lumina-par) | castellated; ICD table authoritative but wrong | requirements.md is the one source | check_requirements.py (schema only) | L1>L2 | checks structure, not content | B:PCB-0019-A |
| CONC-03 | Built to the wrong format or spec (hit: PCB-0022-A) | NFC card rev A: wrong outline, thickness, layers, coil | brief fields mapped to board facts | none | L0>L2 | none | B:commit 2026-10-01 #17 |
| CONC-04 | Outline, mounting or connector drift vs ICD (hit: bb-buck, rp2040-mini, lumina-par) | 48x30 over ceiling; holes 13.05 vs 11.4 mm; owner CLI size lost | brief facts vs board facts | none | L0>L2 | T#312 open | 2026-08-16; L4603 |
| CONC-05 | Threshold chosen against wrong operating point (hit: PCB-0022-A) | PY32 BOR 1.8-2.0 V on a 2 V harvester | operating point vs part thresholds | none | L0>L1 | none | B:commit 2026-10-01 |
| CONC-06 | Sim bench stale or invalid (hit: rf-term-150w, usbbuck4) | parasitic 1.3 vs 4.7 pF; .step last point only; empty bounds pass | invalidate sims when routed values change | sim_run (bounds only) | L1>L2 | T#233, T#236, T#279 open | L3032; L3939; L991 |
| CONC-07 | Power budget unrealistic | batteries die fast | sum worst-case loads, efficiency | none | L0>L1 | none | [10] |
| CONC-08 | Wrong part for the use | temperature grade or supply range mismatch | parametric check vs requirements | none | L0>L2 | none | [10] |
| CONC-09 | Missing function | no charge path, debug or connector | block checklist vs brief | none | L0>L1 | none | [10][26] |
| CONC-10 | Interface or cable compatibility | PD profile, host pinout | pinout vs mating device | none | L0>L1 | none | [17] |
| CONC-11 | Cost target exceeded | BOM over budget | BOM cost vs target | order_quote (partial) | L1>L2 | none | [26][1] |
| CONC-12 | Datasheet pinout read wrong (hit: g0-sense) | pins or footprint off | second reader, pin-count cross-check | none | L0>L2 | T#211, T#105 | L1091; [26] |
| CONC-13 | Reference-layout deviation unexplained | subtle layout bug | compare to datasheet layout | none | L0>L1 | none | [16] |
| CONC-14 | Assumptions and waivers undocumented | later contradictory changes | durable waivers with reason | verify waivers (reason+approved) | L2>L2 | none | [26] |
| CONC-15 | Environment omitted (temp, humidity, vibration) | field failure | temp grade, coating, CAF spacing | none | L0>L0 | rare | [9] |
| CONC-16 | Lifetime or update path unspecified | field aging; no DFU/OTA | plan with hardware support | none | L0>L0 | rare | [14][15] |

Coverage note. check_mating (added in cd6ca77, PR #64) now catches a mouth facing inward, inset from the edge, or blocked. It does not catch a mirrored pinout on a mated pair, pin-1 errors or unkeyed lookalike connectors, so MECH-05, MECH-06 and the pin-1 part of MECH-07 stay open. check_mating is not yet a row of the scorecard.

Count by level now: L0 124, L1 46, L2 56, L3 4. Modes with no script at all: 123.

## 2. Real failures on our boards

Ranked by consequence. "Gate today" says whether any gate would fail it now, as far as I could check from the code and the notes.

| # | failure | mode ids | gate today? |
|---|---|---|---|
| 1 | Connectors facing into the board; unpluggable (PCB-0021-A J4, PCB-0018-A J701/J702, pd-trigger J2, bb-adc J1) | MECH-01, MECH-07 | Yes for inward, inset and blocked mouths since cd6ca77; placement still does not choose orientation (T#70) |
| 2 | rf-de-20m did not reach ZVS: no return plane under magnetics, 23-30 nH, 121 W -> 53 W; DRC and verify clean | PI-16 | No; check_return_path covers signals, not power loops (T#280) |
| 3 | Mated connector pair shorts 48 V to GND (lumina-par J3/J4 reverse-mounted, ICD pin table crossed) | MECH-05 | No |
| 4 | Polarity and rotation: Zener marker on the anode pad kills Q1 (sbuck-5v3a); NFC card U1/U2 CPL rotation gives a dead card | RATE-06, DFA-01, DFA-02 | Partly; cpl_polarity compares diode pads, not marker position or QFN origin |
| 5 | R1, the 250 W load and the board's whole function, missing from BOM and CPL (rf-term-150w) | DFA-04 | Partly; dfm_bom_incomplete covers the BOM, I did not verify the exclude_from_pos flag |
| 6 | DNP parts shipped populated: 9 parts in BOM and CPL, would undo the ZVS fix (lumina-par, rf-de-20m) | DFA-07 | No |
| 7 | Isolation barrier collapsed from 3.58 to 1.05 mm; 217 pairs at 0.2031 mm counted as one (lumina-carrier) | SAFE-03, SAFE-01 | No for the barrier; creepage fixed per case, T#196 open |
| 8 | EPC2019 over 150 C abs max; thermal screen scores the same with zero vias (rf-de-20m) | THERM-02, THERM-03 | Partly; area screen only |
| 9 | GaN gate drive 0.975 ohm vs 2 ohm floor, VGS max 6 V at 5 V drive, invented datasheet values (rf-de-20m) | RATE-14, RATE-15, RATE-23 | No |
| 10 | Missing 100 nF HF cap on buck VIN passed every check; rework on a shipped batch (lumina-carrier) | PI-01 | Yes for regulator inputs now (reg_input_no_hf); not for other supply pins |
| 11 | DRC 0/0 yet unfabricable: min_track 0.1 mm, hole_to_hole 0.25 vs 0.5 mm, 188 tracks under the floor (lumina-carrier) | FAB-13, FAB-04 | Yes at gerber level (dfm_check); the project rules themselves are unchecked |
| 12 | JLC order create failed ambiguously; wrong stackup and copper in the order; nonexistent impedance template (lumina-carrier) | FAB-17, FAB-18, SI-09 | No |
| 13 | Constraint rects read as absolute while the outline had an offset: pour missing under buck, plane over spiral (rf-de-20m, bb-buck) | PI-15 | No (T#221, T#260) |
| 14 | Floating or dead copper: via swallowed by a track, via takes the zone net, 0.2 mm track starves a WCSP ball (rf-de-20m) | PI-11, PI-12, PI-13 | No (T#263, T#270, T#271) |
| 15 | Requirements failures: NFC card rev A to the wrong spec, castellation required but unbuildable (rp2040-mini), outline and ICD drift (bb-buck, lumina) | CONC-02, CONC-03, CONC-04, MECH-16 | No |

Of the fifteen, nine have no gate that fails them today and four are only partly caught. All fifteen are in the backlog.

## 3. Eval design

### 3.1 What exists

- Golden boards: blinky2 (2L), usbbuck4 (4L), rf4 (4L), built by tests/golden/generators/gen.py. They have ERC, DRC and parity at 0.
- Mutants: tests/golden/manifest.yaml lists 13, each {board, script, check, defect, expect}. A script in tests/golden/mutations/ (using mutlib.py) edits the golden .kicad_pcb as text, or only a sidecar (constraints.json, decoupling.json, parts/). Output is committed in tests/golden/mutants/<name>/.
- Scoring: S/score_checks.py runs every check in verify_all.CHECKS on the golden boards (every finding there is a false alarm unless triage.yaml says real), on the mutants (a catch is one finding matching all keys of `expect`) and on the finished boards. It writes docs/check-scorecard.md. tests/test_check_scorecard.py and tests/test_golden.py fail when false alarms or misses rise.
- Stage fixtures: S/bench.py runs one pipeline stage on a frozen fixture and compares with `known_answer` {expected: [{check, kind, net, ref}], forbid_errors}. Useful for pinning a regression with a composite score; P8 and P9 only; no position match.

### 3.2 Rules for the new evals

1. Every mode id in scope gets at least one mutant: one known-good golden board plus one injected defect. A mode with no mutant is "not covered" in the coverage table.
2. Name the mutant after the mode: the manifest key is `<mode-id-lowercase>-<short-defect>`, for example `mech-05-pinout-mirror`. The mutation script is tests/golden/mutations/<same name with underscores>.py. The manifest entry has a `modes:` list naming the id so the coverage table can be built.
3. A catch means the check under test emits an error-severity finding with the expected rule code. Where the fault has a place, `expect` carries `pos` and the finding must be within POS_TOL_MM. A warning does not count as a catch.
4. A false alarm is any error from that check on a clean golden board, and any error that triage marks as not real on the finished-boards corpus (phase P9 and later). Warnings are counted but not scored.
5. Sidecar-only faults are fine where the defect lives in constraints, parts or requirements. Board-text faults must keep ERC and DRC otherwise clean, so the check under test is the only thing that can fail.
6. A new check row adds its mutant in the same PR: script, test, mutation script, committed output and a manifest fragment. Under the wire-registry row these are drop-in files (`checks.d/<name>.yaml`, `manifest.d/<name>.yaml`), so two rows never edit verify_all.py or the shared manifest. The scorecard is re-recorded once by the scorecard-record row, never by individual rows.

### 3.3 Scores and thresholds

- Per check: recall = caught mutants / mutants. False-alarm rate = clean boards flagged / clean boards, taken over the three golden boards and separately over the finished-boards corpus.
- Per mode: covered when at least one mutant for the mode is caught by the check named in the yaml. Coverage = covered modes / modes in scope. Modes with target level L0 or out of scope (SAFE-08, SAFE-10, DFA-25 and similar) are left out of the denominator and listed.
- L1 -> L2 promotion (a check may fail a gate) needs: recall 1.0 on at least two mutants for each rule code, in different places or on different boards; 0 errors on the three golden boards; 0 untriaged errors on the finished-boards corpus, or each remaining error triaged as real with a board-fix row; every error code has a remediation line. A check that cannot meet this stays a warning.
- L2 -> L3 (generator makes it right) needs: the generator output passes the check on every golden board and every generated corpus board, and the old mutant still fails when the generator is bypassed.
- Regression: tests keep the existing rule that recall and false alarms may not get worse than the last recorded line.

### 3.4 CONC evals (requirements against board)

A conceptual failure passes every geometric check, so the eval seeds a mismatch between the brief and the board. The brief-trace row reads requirements.md (the nine-section file check_requirements.py already lints), pulls facts it can compare (outline, hole pattern, layer count, thickness, connector list, rail voltages, BOM cost cap, castellation) and compares them with the board. The mutant is a copy of a golden workspace with one requirement edited, for example outline 40x30 changed to 44x34, or "castellated edges" added. Expected codes: `brief_outline_mismatch`, `brief_feature_unbuildable`. A second mutant removes the calc reference behind a numeric requirement and expects `brief_untraced`. The clean case is the unedited workspace and must produce no errors. Judgement items (wrong part for the use, power budget) stay at L0/L1 as a checklist the reviewer subagent fills in; they are not scored.

### 3.5 Known gaps in the harness

- Single mutant per check: recall of 1.0 is weak evidence. The multi-mutant row adds a second one.
- No ERC or DRC mutants: kc.py faults have no corpus. The erc-drc-mutants row adds some.
- dfm_check is not in verify_all.CHECKS, so it is scored in tests/test_fab.py, not on the scorecard. check_mating, check_irdrop, check_pdn_z, netlist_audit and fp_verify are not scorecard rows either.
- bench.py known_answer cannot match a position and handles one fault per board.
- Most false alarms come from the finished-boards corpus, which needs the boards repo; tests skip when it is absent.
- Golden boards lack gate drivers, mated connector pairs, TVS parts and MCU strap networks. Some evals therefore need a small golden fixture added first, or a sidecar-only fault. The row says which.

## 4. Ranked implementation backlog

Rank is (consequence of the failure x how often we hit it) / size. Rows are split so no two own the same file. Rules for the planning seat:

- **Registration is one row.** Row `wire-registry` is the only row that edits verify_all.py, score_checks.py, tests/test_golden.py, tests/test_check_scorecard.py and gates.yaml. After it lands, checks register by dropping `S/checks.d/<name>.yaml` and `tests/golden/manifest.d/<name>.yaml`. A check row can be built and unit-tested before wire-registry lands but merges after it.
- A row adds its own new test file; it does not edit tests/test_checks.py or other shared tests.
- Rows must not edit bom_cpl.py, dfm_check.py, gate.py, lib/easyeda.py, cpl_render.py or cpl_verify.py now (held by PR #63). Those gaps are in group D.
- Evals name a golden board and mutation as a proposal; the builder confirms the board has the part the mutation needs, and adds a small fixture if not (Section 3.5).
- Row sizes: S under a day, M a day or two, L several days.

| rank | id | title | modes | size | after | grp |
|---|---|---|---|---|---|---|
| 1 | wire-registry | Load checks and mutants from drop-in fragment files | TEST-12 | M | - | A |
| 2 | mate-pins | Check mated connector pairs for mirrored pins and shorts | MECH-05, MECH-06 | M | wire-registry | B |
| 3 | bom-board-sync | Check DNP, BOM, CPL and board attributes agree | DFA-07, DFA-04, DFA-08 | S | wire-registry | B |
| 4 | polarity-marker | Check polarity marks sit on the right pad | RATE-06, DFA-19 | M | wire-registry | B |
| 5 | creepage-v2 | Count every HV pair; declare every 30 V net | SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05 | M | wire-registry | B |
| 6 | thermal-v2 | Fix thermal model: back pour, EP vias, Tj vs abs max | THERM-01, THERM-02, THERM-03, THERM-12 | M | wire-registry | B |
| 7 | check-noise | Cut false alarms in current, ratings, route and silk checks | PI-07, PI-08, RATE-04, FAB-10, EMC-12, THERM-06 | M | wire-registry | B |
| 8 | decoupling-absence | Detect absent decoupling per supply pin, not by value | PI-01, PI-03, PI-04, PI-02 | S | wire-registry | B |
| 9 | rules-integrity | Check project rules, zones and constraint coordinates | FAB-13, FAB-24, PI-15, PI-20, MECH-17 | M | wire-registry | B |
| 10 | route-integrity | Find swallowed vias, starved pads and dead copper | PI-11, PI-12, PI-13, FAB-22 | M | wire-registry | B |
| 11 | driver-network | Check gate-drive network values against datasheet floors | RATE-14, RATE-15, RATE-16, RATE-17, RATE-18 | M | wire-registry | B |
| 12 | regulator-values | Recompute Vout, set-resistors and pull-ups from the netlist | RATE-07, RATE-08, RATE-10, RATE-13, RATE-21, RATE-22 | M | wire-registry | B |
| 13 | mech-keepouts | Check mounting keepouts, flex zones and height budget | MECH-10, MECH-11, MECH-12, MECH-14, MECH-15 | M | wire-registry | B |
| 14 | esd-protection | Check ESD, OVP and fuse parts on every external port | PROT-01, PROT-02, PROT-03, PROT-04, PROT-05, PROT-06, PROT-09, PROT-10 | M | wire-registry | B |
| 15 | mcu-hardware | Check boot, reset, SWD, crystal and reset-time pin states | FW-01, FW-02, FW-03, FW-12, FW-13, FW-15, RATE-20, TEST-02, TEST-03, TEST-07 | M | wire-registry | B |
| 16 | pinmux | Check pin functions against the MCU datasheet pin table | FW-04, FW-05, FW-06, FW-08, FW-09, FW-14, FW-16 | M | wire-registry | B |
| 17 | testpoints | Check test points, status LED and revision silk | TEST-01, TEST-04, TEST-05, TEST-06, TEST-08 | S | wire-registry | B |
| 18 | brief-trace | Check requirements.md facts and numbers against the board | CONC-01, CONC-02, CONC-03, CONC-04, CONC-05, MECH-09, MECH-16 | L | wire-registry | B |
| 19 | fp-trust | Verify pulled footprints: drill, pin 1, courtyard, EP | MECH-13, MECH-08, THERM-04, FAB-19, FAB-21, DFA-13, DFA-24 | M | wire-registry | B |
| 20 | emc-layout | Check hot-loop area, fast nets at plane edges, entry filters | EMC-04, EMC-05, EMC-07, EMC-09, EMC-10, PI-05, PI-06, SI-10, SI-12 | L | wire-registry | B |
| 21 | dfa-physical | Check fiducials, tombstone symmetry, paste ratio, sides | DFA-11, DFA-14, DFA-15, DFA-17, DFA-18, DFA-20, DFA-21, FAB-16, FAB-26 | M | wire-registry | B |
| 22 | place-metrics-fixes | Measure placement rules edge to edge; honour locked refs | PI-02, ANA-08, EMC-13 | S | wire-registry | B |
| 23 | irdrop-pdnz-promote | Promote IR-drop and plane-impedance checks into verify | PI-09, PI-10 | S | wire-registry | B |
| 24 | sim-trust | Reject stale or empty SPICE benches | CONC-06, RATE-25, ANA-06 | S | wire-registry | B |
| 25 | order-safety | Block orders with doubtful stackup, copper or create call | FAB-17, FAB-18, SI-09, DFA-09 | M | wire-registry | B |
| 26 | multi-mutant | Add a second mutant for each existing check | TEST-12 | M | wire-registry | C |
| 27 | erc-drc-mutants | Seed ERC and DRC faults into the golden boards | RATE-11, RATE-12, DFA-03, DFA-10, DFA-12 | M | wire-registry | C |
| 28 | scorecard-record | Re-record the scorecard and coverage table | TEST-12 | S | all group B and C rows | C |
| 29 | dfm-extended | Add wicking, plated-NPTH and skip-is-fail rules to dfm | THERM-05, FAB-07, FAB-08, FAB-14, DFA-08 | M | PR 63 | D |
| 30 | cpl-origin | Check CPL rotation and exclude flags against the JLC origin | DFA-01, DFA-02 | M | PR 63 | D |
| 31 | gate-hardening | Make a skipped input fail the gate; fix waiver path | TEST-10, DFA-08 | S | PR 63 | D |
| 32 | import-checks | Reject bad pulled parts at import (pegs, attrs, offsets) | FAB-20, FAB-19, MECH-08, DFA-24 | M | PR 63 | D |
| 33 | bf-0018-power | Re-check BLDC power tracks, VM_IN neck, creepage, silk | SAFE-01, PI-07, PI-08, FAB-10 | M | - | E |
| 34 | bf-0017-12v | Widen the +12V track for 4 A; fix 7 silk labels | PI-07, FAB-10 | S | - | E |
| 35 | bf-0021-sys | Repair the +SYS pour neck, add vias, fix silk | PI-08, FAB-10 | S | - | E |
| 36 | bf-0019-hfcap | Add HF cap on VSYS and widen SW_L1 | PI-01, PI-07 | S | - | E |
| 37 | bf-0020-usb | Close the USB return gap; fix 20 silk labels | EMC-01, FAB-10 | S | - | E |
| 38 | bf-0016b-silk | Move the misattributed J2 refdes silk | FAB-10 | S | - | E |
| 39 | bf-0022-cpl | Verify U1/U2 CPL rotation by pin 1 on the NFC cards | DFA-02 | S | - | E |
| 40 | bf-0019-castle | Amend requirements or rebuild castellated edge | MECH-16, CONC-02 | S | - | E |

Groups: A. foundation; B. new checks and fixes to checks; C. eval corpus and scorecard; D. after PR 63 lands; E. board fixes.

### Row details (files owned and seeded-fault eval)

**1. wire-registry** - files: `S/verify_all.py`, `S/score_checks.py`, `tests/test_golden.py`, `tests/test_check_scorecard.py`, `.claude/skills/hwde/reference/gates.yaml`, `S/checks.d/README.md`. Eval: blinky2; add a dummy fragment under checks.d and manifest.d; expect `fragment_loaded (test_every_check_has_recall passes for a drop-in check)`.

**2. mate-pins** - files: standard set for check_mate_pins (script, test, mutation, mutants dir, two fragments), `.claude/skills/hwde/reference/connector_pinmap.yaml`. Eval: usbbuck4; add a second same-family connector and swap two pad nets across the pair; expect `mate_pin_mismatch`.

**3. bom-board-sync** - files: standard set for check_bom_sync (script, test, mutation, mutants dir, two fragments). Eval: blinky2; mark a part DNP in the schematic but leave it in the BOM sidecar; expect `bom_dnp_populated`.

**4. polarity-marker** - files: standard set for check_polarity (script, test, mutation, mutants dir, two fragments). Eval: usbbuck4; move a diode silk marker to the anode pad; expect `polarity_marker_wrong_pad`.

**5. creepage-v2** - files: standard set for check_hv_coverage (script, test, mutation, mutants dir, two fragments), `S/check_creepage.py`, `tests/test_creepage_v2.py`, `tests/golden/mutations/hv_undeclared.py`, `tests/golden/mutants/hv_undeclared/**`. Eval: blinky2; add a 48 V net to constraints.voltages but not to the DRU netclass; expect `hv_net_undeclared`.

**6. thermal-v2** - files: `S/check_thermal.py`, `tests/test_thermal_v2.py`, `tests/golden/mutations/ep_vias_removed.py`, `tests/golden/mutants/ep_vias_removed/**`, `tests/golden/manifest.d/thermal_v2.yaml`. Eval: blinky2; delete the thermal vias under the LDO exposed pad; expect `thermal_vias`.

**7. check-noise** - files: `S/check_current.py`, `S/check_ratings.py`, `S/check_route_style.py`, `S/check_silk.py`, `tests/test_check_noise.py`, `tests/golden/scorecard/triage.yaml`. Eval: PCB-0017-A to PCB-0021-A (finished boards corpus); none; goal is fewer warnings on the baseline with the 5 existing mutants still caught; expect `undersized_track (still caught); advisory GND findings drop`.

**8. decoupling-absence** - files: `S/check_decoupling.py`, `S/check_pdn.py`, `tests/test_decoupling_absence.py`, `tests/golden/mutations/pin_cap_removed.py`, `tests/golden/mutants/pin_cap_removed/**`, `tests/golden/manifest.d/decoupling_absence.yaml`. Eval: usbbuck4; delete the only 100 nF cap on an IC supply pin; expect `decoupler_missing`.

**9. rules-integrity** - files: standard set for check_board_rules (script, test, mutation, mutants dir, two fragments), `S/constraints_lint.py`. Eval: blinky2; set min_track to 0.1 mm in the project file; expect `rules_below_fab_floor`.

**10. route-integrity** - files: standard set for check_route_integrity (script, test, mutation, mutants dir, two fragments). Eval: rf4; remove the track that ties a stitch via to its pour; expect `via_dangling`.

**11. driver-network** - files: standard set for check_driver (script, test, mutation, mutants dir, two fragments). Eval: rf4; set gate resistor sidecar to 0.975 ohm vs 2 ohm floor; expect `gate_r_below_floor`.

**12. regulator-values** - files: standard set for check_regulators (script, test, mutation, mutants dir, two fragments). Eval: usbbuck4; change a feedback divider resistor so Vout is 12 percent high; expect `vout_mismatch`.

**13. mech-keepouts** - files: standard set for check_mechanical (script, test, mutation, mutants dir, two fragments). Eval: blinky2; place an MLCC 1.5 mm from a mounting hole; expect `mlcc_flex_zone`.

**14. esd-protection** - files: standard set for check_protection (script, test, mutation, mutants dir, two fragments). Eval: usbbuck4; delete the TVS on the USB connector nets; expect `esd_missing_on_connector`.

**15. mcu-hardware** - files: standard set for check_mcu_hw (script, test, mutation, mutants dir, two fragments). Eval: blinky2; remove the BOOT0 pull-down; expect `boot0_floating`.

**16. pinmux** - files: standard set for check_pinmux (script, test, mutation, mutants dir, two fragments). Eval: blinky2; move the LED net to a pin with no timer channel; expect `pinmux_no_function`.

**17. testpoints** - files: standard set for check_testpoints (script, test, mutation, mutants dir, two fragments). Eval: blinky2; delete the +3V3 test point; expect `rail_no_testpoint`.

**18. brief-trace** - files: standard set for check_brief_trace (script, test, mutation, mutants dir, two fragments), `tests/golden/brief/**`. Eval: blinky2; change the outline in requirements.md from 40x30 to 44x34; expect `brief_outline_mismatch`.

**19. fp-trust** - files: `S/fp_verify.py`, `tests/test_fp_trust.py`, `tests/golden/mutations/fp_drill_short.py`, `tests/golden/mutants/fp_drill_short/**`, `tests/golden/manifest.d/fp_trust.yaml`. Eval: blinky2; shrink a THT footprint drill by 0.2 mm; expect `drill_mismatch`.

**20. emc-layout** - files: standard set for check_emc (script, test, mutation, mutants dir, two fragments). Eval: usbbuck4; move the buck input cap 12 mm from the switch; expect `hotloop_area`.

**21. dfa-physical** - files: standard set for check_dfa (script, test, mutation, mutants dir, two fragments). Eval: blinky2; delete the board fiducials; expect `fiducials_missing`.

**22. place-metrics-fixes** - files: `S/place_metrics.py`, `tests/test_place_metrics_fixes.py`, `tests/golden/mutations/decoupler_locked.py`, `tests/golden/mutants/decoupler_locked/**`, `tests/golden/manifest.d/place_metrics_fixes.yaml`. Eval: blinky2; move a decoupler beyond the limit with its reference locked; expect `decoupler_distance`.

**23. irdrop-pdnz-promote** - files: `S/check_irdrop.py`, `S/check_pdn_z.py`, `tests/test_irdrop_pdnz.py`, `tests/golden/mutations/narrow_neck_irdrop.py`, `tests/golden/mutants/narrow_neck_irdrop/**`, `tests/golden/manifest.d/irdrop_pdnz.yaml`. Eval: blinky2; narrow the supply path to 0.15 mm; expect `irdrop_excess`.

**24. sim-trust** - files: `S/sim_run.py`, `tests/test_sim_trust.py`, `tests/fixtures/sim_trust/**`. Eval: tests/fixtures/sim (sim fixture); stale parasitic in the sidecar; empty bounds file; expect `sim_stale_parasitic`.

**25. order-safety** - files: `S/order_submit.py`, `S/order_quote.py`, `tests/test_order_safety.py`, `tests/fixtures/order_safety/**`. Eval: tests/fixtures/jlc_impedance (payload fixture); order payload with 1 oz inner vs 0.5 oz design; create reply code 2; expect `order_stackup_mismatch`.

**26. multi-mutant** - files: `tests/golden/mutations/*_b.py`, `tests/golden/mutants/*_b/**`, `tests/golden/manifest.d/second_mutants.yaml`. Eval: rf4, usbbuck4, blinky2; one second mutant per check in verify_all.CHECKS (different board or location); expect `same codes as the first mutants`.

**27. erc-drc-mutants** - files: `tests/golden/mutations/erc_*.py`, `tests/golden/mutations/drc_*.py`, `tests/golden/mutants/erc_*/**`, `tests/golden/mutants/drc_*/**`, `tests/test_erc_drc_eval.py`, `tests/golden/manifest.d/erc_drc.yaml`. Eval: blinky2; delete a wire to leave a pin unconnected; move a pad onto a track; expect `pin_not_connected (ERC); clearance (DRC)`.

**28. scorecard-record** - files: `docs/check-scorecard.md`, `docs/check-scorecard.jsonl`, `docs/failure-coverage.md`. Eval: all golden boards; run score_checks --record after all rows land; coverage table from this yaml; expect `n/a`.

**29. dfm-extended** - files: `S/dfm_check.py`, `tests/test_dfm_extended.py`, `tests/golden/mutations/via_in_pad_open.py`, `tests/golden/mutants/via_in_pad_open/**`. Eval: blinky2; put an open via inside an SMD pad; expect `dfm_via_in_pad`.

**30. cpl-origin** - files: `S/bom_cpl.py`, `S/cpl_verify.py`, `S/cpl_render.py`, `tests/test_cpl_origin.py`. Eval: blinky2 (cpl-rotation mutant plus a QFN rotation); rotate a QFN 90 degrees in CPL; expect `cpl_polarity`.

**31. gate-hardening** - files: `S/gate.py`, `tests/test_gate_hardening.py`. Eval: blinky2; delete parts.json then run the dfm gate; expect `gate_input_skipped`.

**32. import-checks** - files: `S/lib/easyeda.py`, `tests/test_import_checks.py`, `tests/fixtures/import_checks/**`. Eval: tests/fixtures/lib (pristine pulls); pull fixture with copper dia equal to drill on a peg; expect `import_zero_annulus`.

**33. bf-0018-power** - files: `~/dev/boards/PCB-0018-A*/kicad/**`. Eval: PCB-0018-A; fix the board; no mutation; expect `creepage; undersized_track; pour_neckdown; silk_misattributed gone from verify_all`.

**34. bf-0017-12v** - files: `~/dev/boards/PCB-0017-A*/kicad/**`. Eval: PCB-0017-A; fix the board; no mutation; expect `undersized_track; silk_misattributed gone from verify_all`.

**35. bf-0021-sys** - files: `~/dev/boards/PCB-0021-A*/kicad/**`. Eval: PCB-0021-A; fix the board; no mutation; expect `pour_neckdown; insufficient_transition_vias; silk_misattributed gone from verify_all`.

**36. bf-0019-hfcap** - files: `~/dev/boards/PCB-0019-A*/kicad/**`. Eval: PCB-0019-A; fix the board; no mutation; expect `reg_input_no_hf; undersized_track gone from verify_all`.

**37. bf-0020-usb** - files: `~/dev/boards/PCB-0020-A*/kicad/**`. Eval: PCB-0020-A; fix the board; no mutation; expect `corridor_void; silk_misattributed gone from verify_all`.

**38. bf-0016b-silk** - files: `~/dev/boards/PCB-0016-B*/kicad/**`. Eval: PCB-0016-B; fix the board; no mutation; expect `silk_misattributed gone from verify_all`.

**39. bf-0022-cpl** - files: `~/dev/boards/PCB-0022-A*/kicad/**`, `~/dev/boards/PCB-0022-B*/kicad/**`. Eval: PCB-0022-A, PCB-0022-B; fix the board; no mutation; expect `cpl rotation (manual pin-1 check) gone from verify_all`.

**40. bf-0019-castle** - files: `~/dev/boards/PCB-0019-A*/requirements.md`. Eval: PCB-0019-A; fix the board; no mutation; expect `requirements vs board gone from verify_all`.

Notes on specific rows.

- `check-noise` is the baseline-noise row: it demotes or dedupes the plane-fed GND advisories (one issue per transition), tiled-pour seams, route jogs and rating_unrated coverage notices so that an error means a real defect. It must keep all five existing mutants for these checks caught. It alone owns tests/golden/scorecard/triage.yaml.
- `brief-trace` is L because the requirements format has to gain machine-readable facts; a smaller first cut is outline, holes and layers only.
- `emc-layout` is L because loop area needs a loop finder; start with the buck hot loop.
- `scorecard-record` also writes a coverage table from the yaml (mode id -> passing mutant), the metric in Section 3.3.
- Group D rows touch held files; start them after PR #63 lands. Their evals reuse the same golden mutants.

### Board fixes (candidates for the fix-until-clean phase)

These come from the baseline in Section 5. They own board directories, not scripts, so they do not conflict with check rows. Each needs a human look first because some findings may be false alarms of the checks (run check-noise first).

| id | board | finding that looks real | codes | size |
|---|---|---|---|---|
| bf-0018-power | PCB-0018-A | Re-check BLDC power tracks, VM_IN neck, creepage, silk | creepage; undersized_track; pour_neckdown; silk_misattributed | M |
| bf-0017-12v | PCB-0017-A | Widen the +12V track for 4 A; fix 7 silk labels | undersized_track; silk_misattributed | S |
| bf-0021-sys | PCB-0021-A | Repair the +SYS pour neck, add vias, fix silk | pour_neckdown; insufficient_transition_vias; silk_misattributed | S |
| bf-0019-hfcap | PCB-0019-A | Add HF cap on VSYS and widen SW_L1 | reg_input_no_hf; undersized_track | S |
| bf-0020-usb | PCB-0020-A | Close the USB return gap; fix 20 silk labels | corridor_void; silk_misattributed | S |
| bf-0016b-silk | PCB-0016-B | Move the misattributed J2 refdes silk | silk_misattributed | S |
| bf-0022-cpl | PCB-0022-A, PCB-0022-B | Verify U1/U2 CPL rotation by pin 1 on the NFC cards | cpl rotation (manual pin-1 check) | S |
| bf-0019-castle | PCB-0019-A | Amend requirements or rebuild castellated edge | requirements vs board | S |

## 5. Baseline

Run on 2026-10-04 from this worktree's scripts with KiCad 10.0.6 in user space, against the boards repo at ~/dev/boards. Command per board: verify_all.py with the board's constraints, decoupling and parts, plus --strict; dfm_check.py with schematic, netlist and parts. Nothing was written to either repo.

Boards: the nine created on or after 2026-09-04 that have fab outputs (phase P7-P10), so they are the newest and most representative: PCB-0016-A, 0016-B, 0017-A, 0018-A, 0019-A, 0020-A, 0021-A, 0022-A, 0022-B. Left out: PCB-0015 (last updated 08-27); PCB-0001/0002/0010 (state touched 09-27 but they look like a bulk migration, not verified); PCB-0017-A_astra-amp (empty stub). The render review was not run.

| board | verify_all errors | verify_all warnings | dfm errors | dfm warnings | notes |
|---|---|---|---|---|---|
| PCB-0016-A pd-trigger-lite | 0 | 22 | 0 | 0 | P8; GND track and via advisories, J1 unrated |
| PCB-0016-B pd-trigger-lite-dip | 0 | 17 | 0 | 0 | P9; one silk_misattributed |
| PCB-0017-A stereo-class-d-amp | 8 | 43 | 0 | 0 | P7; +12V track 0.343 mm for 4 A (real); GND stub 17.9 mm on C5 |
| PCB-0018-A bldc-motor-driver | 383 | 131 | 0 | 4 | P9; 277 transition-via, 57 undersized, 23 creepage (45 V, 0.13 mm), 20 pour necks; count inflated per transition |
| PCB-0019-A rp2040-mini | 6 | 60 | 0 | 1 | P9; reg_input_no_hf on U3 VSYS; SW_L1 0.30 mm for 1 A |
| PCB-0020-A esp32c3-node | 21 | 96 | 0 | 1 | P8; 18 corridor_void errors on USB_DP; 45 GND via advisories |
| PCB-0021-A lipo-boost | 6 | 14 | 0 | 0 | P9; +SYS pour neck ~0 mm and 2 vias vs 5 |
| PCB-0022-A nfc-card | 0 | 13 | 0 | 0 | P10; only unrated parts; dfm rerun with kicad/parts.json |
| PCB-0022-B nfc-card | 0 | 26 | 0 | 1 | P9; route jogs, silk width |

--strict gave the same counts as the default on every board. dfm_check passed all nine (exit 0) and only emits silk warnings. The first dfm run on PCB-0022-A/B crashed because I passed the wrong parts.json path; the table is from the rerun. Counts are per segment or per transition, so they do not compare across boards.

Likely real (judged from messages only, boards not opened):

- PCB-0018-A: /PHASE_A track 0.25 mm for 10 A (57 errors), VM_IN neck at 13 A (20), 45 V creepage of 0.13 mm to GATE_HA (23). Need to check whether pours back the tracks.
- PCB-0017-A: +12V track 0.343 mm for 4 A (6 errors).
- PCB-0021-A: +SYS pour necks to ~0 mm, 2 vias vs 5 needed.
- PCB-0019-A: no HF ceramic on U3 VSYS (nearest cap is 10 uF); SW_L1 0.30 mm for 1 A.
- PCB-0020-A: USB_DP return corridor leaves GND copper (0.53 mm2 deficit, 18 errors).
- Silk: refdes sits nearer another part on five boards (26 on PCB-0018-A, 20 on PCB-0020-A). Real but cosmetic.

Noise (false alarms to fix in check-noise):

- check_current on GND with "advisory: plane-fed rail" (bulk of PCB-0020-A and PCB-0016); one issue per via transition inflates counts.
- check_ratings rating_unrated, 3-18 per board: a coverage notice, not a defect.
- check_route_style needless jogs (68 on PCB-0018-A, 51 on PCB-0019-A).
- dfm_silk_width (0.10-0.12 mm strokes, likely logo graphics) and dfm_silk_over_pad slivers. These are in dfm_check, so the fix waits for PR #63 (dfm-extended).
- check_decoupling gnd_stub_long at 6.6 mm is marginal; 17.9 mm on PCB-0017-A C5 is worth a look.

What the gates missed that we know failed (Section 2): everything marked "No" or "Partly" there. The baseline cannot show misses, because it only counts what the checks said. PCB-0022-A shows nothing beyond unrated parts, though its CPL rotation is the known risk (DFA-02). Side effect of the run: KiCad left untracked .kicad_prl files in ~/dev/boards (PCB-0016-A, 0016-B) and an Xvfb :57 may still run.

## 6. Sources

Some external thresholds came from search summaries, not full pages. Verify them against the live fab or standard page before hard-coding. Source [26] is a local file. Items tagged [g] in the research notes (standard practice, no page fetched) are defaults to confirm against the part datasheet.

### External

1. JLCPCB, Annular Rings in PCB Design (and capability figures from search summary) - https://jlcpcb.com/blog/annular-rings-pcb-design
2. Sierra Circuits / Proto Express, DFM for PCB - https://www.protoexpress.com/pcb/dfm-for-pcb/ ; Via guide https://www.protoexpress.com/pcb-design-guides/via/
3. Altium, Preventing Top DFM Errors in Your PCB Design - https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design
4. PCBCart, Common SMT defects - https://www.pcbcart.com/article/content/common-smt-defects
5. PCBCart, DFA errors and fix in PCB assembly - https://www.pcbcart.com/article/content/dfa-errors-and-fix-in-pcb-assembly
6. AllPCB, Troubleshooting solder-related SMT assembly problems - https://www.allpcb.com/allelectrohub/troubleshooting-solder-related-smt-assembly-problems
7. BestPCBs, PCB fiducial markers - https://www.bestpcbs.com/blog/2026/01/pcb-fiducial-markers/
8. TDK, MLCC flex-crack solution guide - https://product.tdk.com/en/products/solutionguide/mlcc_flex-crack.html
9. IPC technical resource on CAF (E24&S00007) - https://www.electronics.org/system/files/technical_resource/E24%2600007.pdf
10. Altium, Schematic Design Review Checklist - https://resources.altium.com/p/schematic-review-checklist
11. PCBSync schematic review checklist - https://pcbsync.com/schematic-review-checklist/
12. Proto Express, IPC standards help PCB designers build prototypes - https://www.protoexpress.com/blog/ipc-standards-help-pcb-designers-build-prototypes/
13. Siemens, PCB high voltage spacing - https://blogs.sw.siemens.com/electronic-systems-design/2025/04/29/pcb-high-voltage-spacing-what-every-engineer-should-know/
14. Analog Devices, Electrolytic capacitor lifetimes (LED bulb case study) - https://www.analog.com/en/resources/technical-articles/ensure-long-lifetimes-from-electrolytic-capacitors-a-case-study-in-led-light-bulbs.html
15. ST Community, STM32G431 schematic review - https://community.st.com/stm32-mcus-boards-and-hardware-tools-26/stm32g431-schematic-review-162840 (plus other STM32 hardware-guideline snippets from the same search)
16. TI, LM61495 datasheet layout guidelines - https://ti.com/document-viewer/LM61495/datasheet/GUID-72D0C9F1-92AA-4080-A349-82027E96E79B
17. kernel.org, How to design a proper USB-C power sink - https://people.kernel.org/bleung/how-to-design-a-proper-usb-c-power-sink-hint-not-the-way-raspberry-pi-4
18. Embedded Hardware Design, USB2.0 PCB layout guidelines - https://embeddedhardwaredesign.com/usb2-0-pcb-layout-guidelines/
19. Flux, EMI/EMC PCB design guide - https://www.flux.ai/p/blog/emi-emc-pcb-design-guide
20. EMC design rule checking slides - https://emcfastpass.com/wp-content/uploads/2017/04/EMCDesignRuleChecking-PPandF.pdf
21. Diodes Inc., DN1156 Gate drivers in BLDC motors - https://www.Diodes.com/assets/App-Note-Files/DN1156_Gate_Drivers_in_BLDC_motors.pdf
22. TI, SPVA061 class-D layout - https://www.ti.com/lit/pdf/SPVA061
23. Nordic, general PCB design guidelines for nRF52 - https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series
24. Predictable Designs, 8 PCB design mistakes that kill wireless performance - https://predictabledesigns.com/8-pcb-design-mistakes-that-kill-wireless-performance/
25. NASA NEPP, Tin whiskers attributes and mitigation - https://nepp.nasa.gov/Whisker/reference/tech_papers/brusse2002-slides-tin-whiskers-attributes-mitigation-CARTS-US.pdf
26. Local: /home/ihsan/.cc/worktrees/ai-ee/pcb-failure-research/docs/competitive-research.md
27. Printables, Safe 18650 LiPo charger with boost - https://www.printables.com/model/1235604-a-safe-18650-lipo-charger-with-a-5-12v-boost-conve
28. NASA NEPP 2008 ceramic capacitors - https://xdevs.com/doc/NASA/nepp%202008%20ceramic%20capacitors.pdf
29. Altium, PCB manufacturing rule: minimum annular ring - https://altium.com/jp/documentation/altium-designer/pcb-manufacturing-rule-minimum-annular-ring?version=18

### Internal

- I1. LEARNINGS.md (L<n> = line number), repo root. Lines 1-560 partly skimmed.
- I2. design/ladder-triage.md (T#<n> = row number; owner and level per row).
- I3. Boards repo ~/dev/boards (ihsan-sa/boards): reports/review-board.md and review-schematic.md per board, commit subjects (B: refs).
- I4. tests/golden/manifest.yaml, tests/golden/mutations/, S/score_checks.py, docs/check-scorecard.md.
- I5. S/bench.py and tests/fixtures/stages/manifest.yaml.
- I6. reference/gates.yaml, S/verify_all.py, S/check_mating.py (cd6ca77).
- I7. Research notes: ~/.cc/state/ai-ee/pcb-failure-research/notes/{internal,external,checks,baseline}.md.
