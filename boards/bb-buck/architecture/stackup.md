# stackup.md - bb-buck layer count, stackup, outline

## Chosen stackup

**`JLC2313_1.6`** - JLCPCB standard 2-layer, 1.6 mm, **1 oz outer copper**,
HASL. `available: true` in `reference/stackups.yaml` (verified 2026-08-06)
and the `defaults: 2` entry, so `board_init.py` takes it by layer count.

```
F.Cu        0.035 mm   1 oz   signal + power + F.Cu GND thermal island
dielectric  1.530 mm   FR4 core, er 4.5 (ASSUMED, not JLC data)
B.Cu        0.035 mm   1 oz   UNBROKEN GND pour: return + reference + radiator
                              total 1.6 mm
```

**Outline: 40 x 30 mm (1200 mm^2). This is FINAL** - `board_init --outline
40x30` at P5 and there is no shrink step anywhere later in the pipeline.

Do NOT use `JLC04161H-3313` (phantom, never sold) or `JLC04161H-7628G`
(withdrawn 2026-08-06). Both are `available: false` and `board_init` /
`rules_gen` refuse them by name. The 4-layer escalation target is
`JLC04161H-1080B`, JLC's only real 4L/1.6 mm/1 oz-outer/0.5 oz-inner
lamination as of the last live probe.

## Layer-count drivers

| Driver | 2L verdict |
|---|---|
| Controlled impedance | **Not needed.** Nothing on this board is a transmission line. JLC sells no impedance-controlled 2-layer product at all (the API returns zero templates at both copper weights), which is not a constraint here - `controlled_impedance` is an empty list and `constraints.json` carries no `impedance_ohm` anywhere. |
| Reference plane | **One is enough and 2L provides it.** The only node needing a reference is `/SW`, and an unbroken B.Cu GND pour 1.53 mm below F.Cu is that reference. Single-sided assembly (mode default) keeps the whole bottom face clear of SMT, so nothing competes for it. |
| Routing density | **Trivial.** 14 electrical parts, 6 nets, zero layer transitions on `+VIN` / `/SW` / `+5V` by design - all three stay on F.Cu, and GND is plane-fed. |
| Current | **Routable on 1 oz.** IPC-2152 at dT = 10 C: 1.52 mm for the 2.6 A nets, 0.56 mm for `+VIN`. Both fit comfortably on a 1200 mm^2 board. |
| **Thermal** | **The only real question - see below.** |

## 2L vs 4L: the decision, and exactly what flips it

**2 layers, conditionally.** All five conditions from `power.md` s7 hold as
designed:

1. **Synchronous** - chosen. (Async's 1.71 W board and 0.77 W diode do not
   fit on 2 layers at any size.)
2. **`P_U1 <= 0.95 W` at 30 V / 2 A** - the design point is 0.85 W at
   400 kHz. **This is the condition most likely to fail and it is a PART
   property, not a layout one.**
3. **Outline >= ~1000 mm^2 with an unbroken B.Cu GND pour** - 1200 mm^2,
   no split within 14.3 mm of U1.
4. **>= 16 thermal vias under the exposed pad** (target 20-25 counting a ring
   in the surrounding F.Cu GND island), 0.3 mm drill, 1.0-1.2 mm pitch.
5. **Part `Tj_max = 150 C`** - the class norm.

**ESCALATION TRIGGER (explicit, for P3 - re-run this arithmetic against the
chosen part's real datasheet numbers BEFORE P5 freezes the stackup):**

> Switch to **4 layers, `JLC04161H-1080B`**, if ANY of:
> - `P_U1 > 0.95 W` at 30 V / 2 A. At 400 kHz that is `Rds_LS > ~110 mOhm`
>   at 25 C (at 500 kHz it would be 85 mOhm). A 2 A-class part at 130 mOhm
>   lands at 1.19 W and trips this.
> - the part is `Tj_max 125 C` (`dt_c` drops to 55 and neither the P8 screen
>   nor the physical ladder passes).
> - the part is asynchronous (re-run the whole budget: +0.42 W board, plus a
>   `thermal` entry for the diode at ~0.77 W).
> - P8 `check_thermal` errors at `dt_c = 70`.
>
> **The screen passes by a real but small margin** - `0.92 W x 73.85 C/W =
> 67.9 C` against `dt_c 70`: **2.1 C** at P1's conservative power and **6.9 C**
> at the 400 kHz design power of 0.854 W. The ceiling is 0.948 W - 0.95 W
> already gives 70.2 C and errors, and a 2 A-class part at 1.19 W gives 87.9 C.
> (Verified by calling `check_thermal.theta_ja` directly: 73.85 C/W on 2L and
> 51.11 C/W on 4L at the 645 mm^2 saturation area.) A live trigger, not a
> formality.
>
> **The outline does NOT change on escalation.** 40 x 30 mm is already at the
> area knee; 4 layers buys a lower LOCAL junction-to-board path (~11 K/W,
> 0.2444 mm prepreg to In1 instead of 1.6 mm to B.Cu), worth ~11 C of Tj. It
> does NOT lower R_ba - board-to-ambient is set by AREA and h, and the board
> is already near-isothermal at 2 layers.

## Why 40 x 30 mm, and why the outline is an electrical decision here

The mode says "the smallest outline that keeps the layout HONEST". On this
board honest has a **numeric floor of ~1000 mm^2, because the outline IS the
radiator**: R_ba is 39 C/W at 875 mm^2, 34 at 1064 and 31 at 1200, so
875 -> 1200 mm^2 is worth ~10 C of junction at the same power - more than
4 layers buys, and it is free at the fab.

40 x 30 is 20 % above that floor, and the increment is bought by three
physical facts, not by padding:

1. **The inductor is big because the part is good.** `Isat >= 1.3 x the
   part's MAX HS current limit` (not 1.3 x the 2.35 A peak) means ~6.6 A for
   a 3 A-class part, which at 15 uH and <= 40 mOhm is a **10 x 10 to
   12.5 x 12.5 mm** component - 100-156 mm^2 of the interior.
2. **Two 5.08 mm screw terminals eat ~10 mm of edge depth each.** With J1 on
   the left edge and J2 on the bottom edge, the clear interior is ~30 x 20 mm
   plus the corner regions - enough for a tight hot loop AND for the FB node
   to stay away from `/SW` and L1. At 38 x 28 with terminals on opposite
   edges the interior drops below 500 mm^2 and one of those two has to give.
3. **4 x M3 with 6.5 mm washer keepouts** costs ~196 mm^2 at the corners.

Cross-check on the ladder: 40 x 30 is a row P1 actually computed (Tj 107 C at
0.92 W with 25 vias), so this is not an interpolation.

**Area is free here and the fab class is unchanged**: JLC's headline price
tier runs to 100 x 100 mm, so 1200 mm^2 and 1064 mm^2 cost the same. The
outline was therefore decided on thermal and layout grounds only. **There is
no outline-shrink step later in this pipeline** - if P3's inductor turns out
to be a 7 x 7 part, the board stays 40 x 30 and simply runs cooler.

## Copper weight: 1 oz, not 2 oz

`JLC2313_1.6_2oz` exists and is available, and is rejected: the widest
IPC-2152 requirement on this board is 1.52 mm at 2.6 A / dT 10 on 1 oz, which
routes easily on a 1200 mm^2 outline. 2 oz was added to the library for a 5 A
path (`pd-trigger`) that could not be routed otherwise; this board has no
such path. Thermally 2 oz would lengthen the spreading length from 26 to
37 mm, which buys nothing on a board that is already near-isothermal.

## Verification status of this choice

- `JLC2313_1.6` provenance is `vendor_page`, **not** a live API read - and
  that is correct rather than weak: JLC returns ZERO impedance templates for
  `stencilLayer=2` at both copper weights (live 2026-08-06), because it sells
  no impedance-controlled 2-layer product, so there is nothing to read back.
  The physical stack (1.6 mm, 1 oz, HASL) is the standard catalogue product.
- `epsilon_r 4.5` is an ASSUMED FR4 value, not JLC data. Nothing on this board
  depends on it (no controlled impedance, no length matching).
- The offering churns - `JLC04161H-7628G` was real on 2026-07-30 and gone by
  2026-08-06. **If the layer count escalates to 4L, re-run the live template
  probe before P5** rather than trusting the yaml entry.
