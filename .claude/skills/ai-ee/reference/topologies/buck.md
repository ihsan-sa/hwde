# Topology reference: buck (GENERATED VIEW - do not hand-edit)

Source of truth: reference/knowledge/records/ (U4). Regenerate with
`scripts/knowledge.py --render-topology buck --out reference/topologies/buck.md`; a test pins this file to the
records, so hand-edits fail the suite - edit the record, re-render.

HOW TO USE (research-reference-design agents): read this FIRST, then
research only the part-specific delta (exact external-component
table, errata, the family's FB flavor). Cite deltas against the
record ids. Retrieval into P6/P7 spawn prompts is automatic
(knowledge.py --select) once constraints.json declares the block.
Each heading carries the record's level/maturity tag (U13 coverage
contract): draft = unreviewed; only approved/proven satisfy coverage.

## buck-bst-fb-output-caps [feedback, decoupling] (level?/draft)

BST: integrated-FET parts need the 100 nF BST-SW cap - it is required, not optional (DS41326 s13); confirm value/rating in the family datasheet. FB TRAP (cost a near-miss once): FIXED-output family members tie FB straight to the output sense point - do NOT copy the ADJUSTABLE variant's divider from the shared datasheet figure (AP63203 vs AP63200/1, DS41326 fig 20/21). Adjustable parts: divider AT the FB pin, short FB trace routed away from SW and L, sense point AFTER the output caps. OUTPUT CAPS: ceramic, inside the datasheet's stated C/ESR window - internal compensation assumes it (DS41326 s12); count DC-bias derating (a "22 uF" X5R at bias is ~12-15 uF). When the part has EXTERNAL compensation, the vendor's table values are quoted for a specific C_OUT - a different bank means re-deriving the network, not copying the row (sbuck D-item: 5x 22 uF vs the table's 2x 22 uF moved the crossover by 2.5x).

Rule: bst_cap_nf=100 fb_divider_at=FB pin, sense point AFTER the output caps

Sources: boards/usb-buck/parts/C5248536.pdf DS41326 s12-13, fig 20/21; boards/sbuck-5v3a/architecture/blocks.md s3 (compensation re-derive)

## buck-cin-co-ground-separation [power-loop, emi] (level?/draft)

Two ROHM measurements the generic hot-loop rule does not carry: (1) shortening the CBYPASS wiring EVEN BY 1 mm is worth it - the HF bypass supplies the steepest edge of the switch current, and its loop inductance sets the VIN-pin voltage noise directly; (2) even with CBYPASS tight to the IC, several hundred MHz rides on the INPUT capacitor's ground, so the grounds of C_IN and C_OUT must sit 1-2 cm APART - placed close together the input HF noise couples straight into the output through C_OUT. C_IN placed on the bottom layer through vias is explicitly unsuitable (via inductance); input cap and (for async) the free-wheel diode go on the SAME surface layer as the IC terminals. This refines, not replaces, the shortest-loop rule in buck-input-hot-loop.

Rule: bypass_same_surface_as_ic=True cin_co_gnd_separation_cm=1 to 2

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.3 s3, fig 3-a..3-d; reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.7 s6 (output cap)

## buck-constraints-emission [constraints-emission] (level?/draft)

What a buck block must emit into constraints.json for the pipeline: (1) power entries with current_a from the RAIL BUDGET (consumer sum + ~30% headroom, rounded to a design ceiling) and dt_c from ambient; (2) a thermal entry when regulator dissipation > ~0.5 W - for async parts add the Schottky's Vf * I * (1-D), the diode often out-heats the IC; (3) layout_notes for P6/P7: hot-loop grouping, SW containment/separation, FB routing - these become placement groups and route_critical facts; (4) a blocks entry ({topology: buck}) so knowledge retrieval keys on it.

Rule: thermal_entry_above_w=0.5

Sources: boards/usb-buck/research/power.md s7-9 (emitted constraints); .claude/skills/ai-ee/reference/constraints_schema.md power / thermal / blocks

## buck-en-softstart-sequencing [sequencing] (level?/draft)

Check the EN pin's OWN behavior before adding parts: many parts auto-start (AP63203: internal 1.5 uA pull-up - tie to VIN or float; adding a divider is wasted parts). When EN is used as a UVLO divider, mind the two traps the sbuck run hit: a narrow hysteresis gap can force a divider into the mA-burn regime via the part's own equations, and hysteresis smaller than the input CABLE DROP at full load motorboats (start -> sag -> stop -> recover). Soft-start time sets the output-cap inrush as seen by the source. Single-rail boards rarely need sequencing; multi-rail: state the order requirement or "none" explicitly in power.md.

Sources: boards/usb-buck/research/power.md s6 (EN/soft-start); boards/sbuck-5v3a/architecture/blocks.md s4 (UVLO divider pathology)

## buck-fb-route-rules [feedback] (level?/draft)

The feedback route needs the most attention of any signal wire - noise here becomes output-voltage error and instability. ROHM's four rules (fig 7-a): (a) the FB pin is high impedance - connect the divider network with a SHORT wire at the pin; (b) sense AFTER the output capacitor or at its terminals; (c) wire the two divider resistors adjacent and parallel for noise tolerance; (d) route far from the switching node, never directly under the inductor or diode, and never parallel to a power line - on multilayer boards the same rules apply layer-to-layer, and the worked example drops the FB route to the bottom layer through a via to get away from the SW region. A feedback trace laid parallel beside the inductor picks up its magnetic field (fig 7-d). Matches and extends the FB half of buck-bst-fb-output-caps.

Rule: divider_at_fb_pin=short wire, resistors adjacent and parallel keep_away_from=SW node, inductor, diode; never under L or D; not parallel to power lines sense_point=after or at both ends of the output capacitor

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.7 s7, fig 7-a/7-b; reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.8 fig 7-c/7-d

## buck-freewheel-diode-snubber-placement [power-loop, emi] (level?/draft)

Async buck (free-wheel diode) placement rules: the diode must sit CLOSE and on the SAME surface as the IC terminals, wired short and wide, connected directly to the IC's GND and SW terminals - distance adds wiring inductance whose spike noise piles onto the output, and dropping the diode to the bottom layer through vias makes it worse (via inductance). If spike noise still needs an RC snubber, place it CLOSE TO THE IC's SW and GND terminals; a snubber across the diode's own ends does NOT absorb the spike generated by the wiring inductance (ROHM fig 3-g vs 3-h). Sync bucks lose the diode but keep the rule's core: the LS-FET return corner of the hot loop stays tight to the IC.

Rule: diode_surface=same layer as IC terminals, never via-dropped to bottom snubber_at=IC SW + GND terminals, NOT across the diode ends

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.3 s3, fig 3-e..3-h; reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.5 fig 3-g/3-h placement

## buck-inductor-copper-and-gnd-void [emi] (level?/draft)

Inductor region rules (ROHM s5): place L close to the IC but NOT as close as the input cap; do NOT expand the SW/inductor copper beyond what current needs - enlarged copper works as an antenna (EMI), even though instinct says more copper = cooler. Practical width floors with margin: 1 mm per A at 1 oz, 0.7 mm per A at 2 oz. Do not put a ground plane DIRECTLY UNDER the inductor: eddy currents derate the inductance and Q, and any signal line under it picks up switching noise - keep wiring out from under L, or use a closed-magnetic-circuit (shielded) inductor when routing there is unavoidable. Keep the two inductor terminals' wiring apart: close spacing couples the SW edge to the output through stray capacitance (fig 6-d).

Rule: gnd_plane_under_inductor=avoid (eddy current derates L, couples noise) width_per_amp_1oz_mm=1.0 width_per_amp_2oz_mm=0.7

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.5 s5; reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.6 fig 6-a..6-d

## buck-inductor-selection [selection] (level?/draft)

The three inductor rules every run re-derived from scratch. L VALUE: start from the vendor's recommended-components table row for your Vout; the next STANDARD value up is usually right - light-load efficiency improves with larger L (DS41326 s10 says so explicitly; usb-buck: table said 3.9 uH, chosen 4.7 uH). ISAT: must beat the part's PEAK CURRENT LIMIT / PFM clamp, not the load current (usb-buck: 450 mA clamp meant a 1 A-rated part was ample at a 57 mA load). DCR: budget it as real dissipation - target < 30 mohm for A-class rails (usb-buck P3 rule, waived at 60 mohm with math); ~0.1 ohm cost 0.29 W at 2 A on the carrier. DCR losses scale I^2 - cheap inductors tax high-current rails hard. Derate Isat/Irms/DCR to the real ambient before comparing (sbuck: 18.5 mohm at 20 C -> 24 mohm hot).

Rule: dcr_mohm_max_a_class_rail=30 isat_must_beat=peak current limit / PFM clamp, not load current

Sources: boards/usb-buck/parts/C5248536.pdf DS41326 s10 (inductor selection); boards/usb-buck/research/power.md s5 (L/Isat/DCR derivation); boards/lumina-carrier/research/poe-power.md DCR dissipation at 2 A

## buck-input-hot-loop [power-loop, emi] (level?/draft)

Layout rule #1 for every buck: the input cap carries the DISCONTINUOUS switch current. C_IN plus a 100 nF HF bypass AT the VIN pin, on the SAME layer as the IC; the C_IN -> VIN -> GND -> C_IN loop must be the shortest loop on the board; SW-node copper minimal. At ~1 MHz switching this matters more than copper weight (usb-buck power.md s7-9; every vendor layout section says the same). Solid GND pour + vias under the IC. At P6 this is a placement GROUP (constraints placement.groups) anchored on the IC with the input ceramics + HF bypass as members, placed and locked BEFORE the annealer runs - the cost function does not know the loop exists.

Rule: hf_bypass_at=VIN pin, same layer as the IC hf_bypass_nf=100 loop=C_IN -> VIN -> GND -> C_IN shortest on the board

Sources: boards/usb-buck/research/power.md s7-9 (hot loop); boards/usb-buck/parts/C5248536.pdf DS41326 layout section

## buck-power-ground-isolation [return-path, power-loop] (level?/draft)

Ground strategy (ROHM s8): analog small-signal ground and power ground must be ISOLATED, and power ground laid on the TOP layer without splitting is the ideal - dropping an isolated power ground to the bottom layer through vias adds via R and L and worsens noise. Inner/bottom ground planes are SUPPLEMENTARY (DC loss, shielding, heat), not the return path design. Multilayer recipe (fig 9): power-ground plane on L2 stitched to top with MANY vias; common ground L3, signal ground L4; connect the ground families together ONLY at the output capacitor's power ground (the low-HF-noise point) - NEVER at the free-wheel diode or input-capacitor ground, which carry the highest switching noise. This is the class-level reason the pipeline's In1-GND-under-the-IC default works, and where to join AGND islands when a board has them.

Rule: never_join_at=free-wheel diode / input capacitor ground (highest HF noise) pgnd_agnd=isolate; join only at the LOW-noise point (output cap ground)

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.8 s8, fig 8/9

## buck-selection-ladder [selection] (level?/draft)

Regulator-type ladder, one line of tradeoff each; if the brief names a part the named part stands (record the alternative as an override option). (1) Integrated synchronous buck is the DEFAULT at <= ~60 V input and <= ~3 A: no catch diode, best efficiency/heat (usb-buck AP63203). (2) Asynchronous + Schottky when the V/I corner has no stocked sync part (lumina-carrier: the only 100 V-rated 2 A part was async COT); the Schottky must be rated >= Vin (SS510 class). (3) Controller + external FETs is the efficiency/current escape hatch (~2-3 pts over async, any current) at the cost of 2 FETs + gate/sense network + layout area (carrier LM5146 fallback). (4) An LDO is the honest option at light load - 3 parts vs 6 and no switch node near analog/RF, at the cost of (Vin-Vout)*I heat; do the comparison table before assuming the buck.

Sources: boards/usb-buck/research/power.md s4 (LDO-vs-buck table); boards/lumina-carrier/research/poe-power.md s4 (async choice, LM5146 fallback)

## buck-switch-node-containment [emi] (level?/draft)

Keep SW copper as small as electrically possible and treat SW + L as an AGGRESSOR: lumina-par's 2.4 GHz antenna 11 mm from a switch node drove a 4-layer stackup + containment plan; usb-buck keeps the USB pair away from SW/L per ST AN4879 3.3. Hand P6 a separation/keepout entry (constraints placement.separation / placement.keepouts) whenever any antenna, high-Z analog node, or diff pair shares the board; the switch node is also why high_speed references demand an UNBROKEN plane under victims (check_return_path enforces the plane; the separation entry is what keeps the aggressor out of the corridor in the first place). A /SW test-point tap must be a short stub that does not extend the SW pour - it counts against the SW copper budget.

Rule: sw_copper=smallest electrically possible victims=antenna, high-Z analog, diff pairs -> separation/keepout entry

Sources: boards/usb-buck/research/interface-usb.md AN4879 3.3 (USB vs switcher); boards/sbuck-5v3a/architecture/blocks.md s8 (/SW tap stub rule)

## buck-thermal-via-and-via-current [thermal-via] (level?/draft)

Thermal vias under an exposed-pad regulator (ROHM s4, HTSOP-J8 numbers generalize to EP packages): small drill - 0.3 mm inner diameter - so the via can FILL with solder; larger drills suck solder away from the joint at reflow (solder-wicking). Pitch ~1.2 mm, directly below the reverse- side thermal pad; add a ring of extra vias around the IC when the pad area alone is not enough. Copper area helps but the base material is the real radiator - vias carry the heat to the far layers. For CURRENT via sizing (s10-3): a via's equivalent conductor width is pi x diameter but its wall is only ~18 um plating, so use 2 mm of equivalent width per amp - about double the 1 oz surface-trace rule; measured table: 0.3 mm via 0.4 A, 0.6 mm 0.9 A, 1.0 mm 1.5 A. Count vias against that, not against the drill area.

Rule: thermal_via_drill_mm=0.3 thermal_via_pitch_mm=1.2 via_width_per_amp_mm=2.0

Sources: reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.3 s4 (thermal via); reference/knowledge/sources/rohm-buck-pcb-layout-an.pdf p.10 s10-3 (via current)

## buck-upstream-inrush-limit [inrush, selection] (level?/draft)

Upstream bulk limit trap: a buck's input capacitance is bounded by the SOURCE, not by the buck. USB 2.0 allows 10 uF || 44 ohm at attach (spec s7.2.4.1); a USB-PD sink is allowed 100 uF under contract (cSnkBulkPd); PoE has its own inrush envelope. Check the source's rule BEFORE sizing C_IN. Soft-start makes OUTPUT caps invisible to the source's inrush test (usb-buck power.md s6) - so the output bank is sized by load step, not by the source rule.

Rule: usb2_attach_limit=10 uF or 44 ohm-limited at attach (s7.2.4.1) usbpd_sink_bulk_uf_max=100

Sources: boards/usb-buck/research/power.md s6-7 (inrush vs source rules); boards/usb-buck/research/interface-usb.md attach capacitance

## cot-ripple-injection-raises-vout [feedback] (level?/draft)

A constant-on-time regulator ends its off-time when FB falls back through VREF, so it regulates the VALLEY of FB, not its average. With Type 3 injection the ramp is AC-coupled into FB and its mean is genuinely zero, so FB_dc = VREF + Vramp/2 and VOUT = (1 + R_top/R_bot) x (VREF + Vramp_pkpk/2) - NOT VREF times the divider ratio. On an LM5017 at 78.6 mV of injected ripple that is +3.2 %: 5.06 V where a valley calculation says 4.90 V, which is enough to put a 5 V rail over a downstream driver's recommended VDD max. A P4 reviewer computed the rail min/nom/max without the term and concluded the nominal was 100 mV low. Both readings matter in practice because Vramp carries Rr, Cr and K tolerance, so solve the divider against the UNION - effective reference in [VREF_min, VREF_max + Vramp_max/2] - and check both corners rather than picking one model. Also check the FB overvoltage comparator against FB's PEAK (VREF + full Vramp): the LM5017 trips at 1.62 V and terminates the on-time pulse.

Rule: applies_when=constant-on-time regulator with Type 3 (AC-coupled) ripple injection fb_overvoltage=compare against FB PEAK (VREF + full Vramp), not its average solve_against=union of [VREF_min, VREF_max + Vramp_max/2] - check both corners vout=(1 + R_top/R_bot) * (VREF + Vramp_pkpk/2)

Sources: boards/rf-de-20m/LEARNINGS.md 2026-08-08 Type 3 ripple injection RAISES the DC output; boards/rf-de-20m/parts/C34355.pdf LM5017 (the part this was measured on)
