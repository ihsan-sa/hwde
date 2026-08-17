# bb-ldo - stackup (P2)

## Chosen: `JLC2313_1.6` - 2 layers, 1.6 mm, 1 oz outer copper, HASL

By NAME from `reference/stackups.yaml` (`available: true`, and the file's own
`defaults[2]`). Provenance there is `vendor_page`, verified 2026-08-06;
`live_verified: false` is expected and harmless - JLC's impedance-template API
returns ZERO templates for 2-layer at any copper weight because JLC sells no
impedance-controlled 2-layer product, so there is nothing to read back and
nothing this board needs from it.

```
F.Cu          0.035 mm   1 oz    <- +3V3 pour = THE HEATSINK, plus all routing
dielectric 1  1.530 mm   FR-4 core
B.Cu          0.035 mm   1 oz    <- GND pour + a +3V3 island under the tab
                                    total 1.6 mm
```

## Why 2 layers - the four things that normally drive layer count

1. **Impedance control: not needed, and not purchasable.** There is no
   high-speed net on this board - no signal net at all. Had one existed, note
   that a 2-layer board has no adjacent reference plane and JLC offers no
   controlled-impedance 2-layer stackup, so an impedance requirement is itself
   a reason to go to 4 layers. This board has none.
2. **Plane count: exactly two pour surfaces are needed** - `+3V3` on F.Cu (the
   tab net / heatsink) and GND on B.Cu (the 515 mA return). A 2-layer board
   supplies exactly that. There is no third net that wants a plane.
3. **Density: three nets, six parts.** Routing is `+5V` from J1 to VIN, `+3V3`
   from VOUT into the pour and out to J2, and GND on the bottom pour. Nothing
   here needs an escape layer.
4. **Thermal: more layers do NOT buy tab area.** This is the one that looks
   like it should force 4 layers and does not. The lever is copper AREA on the
   TAB net, and the tab is on TOP:
   - inner copper in JLC's 4-layer 1.6 mm stack is **0.5 oz**, half the
     spreading conductance of an outer layer, and it is buried - it has no
     convection surface of its own;
   - reaching it costs vias, and the measured penalty for via-fed copper is
     **~20% worse per unit area than the same copper on top** (79 vs 66 C/W at
     645 mm2, TI SOT-223 1 oz sweep), with a 50/50 top/bottom split (70 C/W)
     losing to putting it all on top (66 C/W);
   - the inner layers would also have to be `+3V3` islands, not planes, since
     the tab net is the OUTPUT - so they buy no return-path or shielding
     benefit either.
   Growing the F.Cu pour is strictly better per dollar and per mm2 than adding
   layers. **Class: 2L, and it is an engineering answer, not a cost answer.**

**Thickness 1.6 mm is a real choice, not a default.** Both copper-area sweeps
this design is sized against were measured on **1/16 inch (1.59 mm) FR-4**.
Keeping 1.6 mm keeps the board in the same physical class as the data; a 0.8 mm
board would be cheaper to bend and a different thermal experiment.

## Rejected

- **`JLC04161H-1080B` (4 layers, 1.6 mm, 1 oz/0.5 oz)** - see driver 4 above.
  ~2.5x the bare-board price (headline $5.00 vs $2.00 at qty 5) for copper that
  is worse per mm2 for this package. Rejected on physics first, price second.
- **`JLC2313_1.6_2oz` (2 layers, 2 oz)** - tempting and unsupported: no source
  in the research quantifies 2 oz for SOT-223 (TI's 2 oz sweep is for TO-252,
  which confounds package with copper weight), and `check_thermal`'s model keys
  on layer count only, so 2 oz changes the gate's answer by exactly nothing.
  Area is the earned lever. **Held as the cheapest fallback** if the P8 thermal
  waiver ever needs strengthening.
- No ENIG, no thick copper, no non-standard thickness, no impedance template.
  Surface finish stays the DFM default (HASL / lead-free HASL); the two THT
  screw terminals are hand soldered, which HASL suits.

## Pours (this is where the stackup does its work)

`constraints.json["planes"]` overrides the 2-layer default (which is a single
B.Cu GND pour and would leave the thermal design with no copper at all):

| layer | net | region | connect |
|---|---|---|---|
| F.Cu | `+3V3` | full board (inset) | **solid** |
| B.Cu | `GND` | full board (inset) | thermal (default) |
| B.Cu | `+3V3` island under the tab | **P6/P7 - needs board coordinates** | solid, priority auto-raised over the GND pour |

**`connect: solid` on the F.Cu pour** is deliberate: KiCad's default thermal
relief would connect the tab pad to its own heatsink through four ~0.5 mm
spokes, necking the ONLY heat path this design has. Cost: every `+3V3` pad on
that pour (notably J2's) is solid-connected and needs a hotter iron to hand
solder - recorded for P9's assembly note.

**Known lint noise:** `constraints_lint` warns
`planes[0]: key 'connect' is not in constraints_schema.md - consumers will
ignore it`. The warning is wrong and the key is right: `planes_gen.py` owns the
planes schema and accepts `net/layer/region/priority/min_island_mm2/clearance/
min_width/connect` (`_PLANE_KEYS`, with `connect` in `{solid, thermal}`);
`constraints_schema.md` and the lint's own table list only `region`. Do not
delete the key on the strength of the warning - fix the doc/lint instead
(candidate LEARNINGS entry, and note that `planes[]` entries are also the ONE
place where an `_`-prefixed comment key is REJECTED: `planes_gen` errors on any
unknown key, exit 2).

## Fab class and cost picture for the checkpoint

Standard JLC 2-layer process, 1.6 mm, 1 oz, HASL, green mask, no controlled
impedance, no special finish - the cheapest tier JLC sells, and comfortably
inside the promo size envelope (100 x 100 mm) at an expected ~40 x 40 mm.
Lead time 2 days fab + 4 days assembly, standard.

Rough, from `reference/jlc_pricing.yaml` (headline price points, qty 5) and the
one researched part price. **`order_quote` does real numbers at P10; that file
warns its own estimates run 1.9-3.1x LOW, so treat these as a lower bound.**

| item | estimate (qty 5) | basis |
|---|---|---|
| bare PCB, 2L, in the promo envelope | $2.00 headline (~$4-6 realistic) | pricing table 2L/qty5 + its measured bias |
| PCBA setup + stencil | $16.00 | fixed fees, independent of part count |
| extended-part feeders | ~$6.00 | the two tantalums are probably Extended; the regulator is Basic (free) |
| solder joints | ~$0.07 | ~8 SMT joints x 5 boards |
| parts | ~$4-7 total | regulator $0.20/pc (researched); caps + terminals ESTIMATED $0.15-0.40/pc, P3 confirms |
| **order total, 5 boards** | **~$28-35** | **~$6-7 per board** |

**The honest observation for the checkpoint:** this board has THREE SMT parts,
so ~$22 of the ~$30 is fixed JLC assembly overhead - PCBA costs more than five
bare boards plus a soldering iron. The mode default (JLC PCBA, single-sided) is
taken as written and P2 does not change it; the owner may want to at H1. The
two through-hole screw terminals are outside economy SMT assembly either way
and are hand soldered after PCBA.
