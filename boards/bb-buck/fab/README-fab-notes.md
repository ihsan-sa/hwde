# bb-buck - fabrication and assembly notes

24 V (18-30 V) to 5 V / 2 A synchronous buck, bench study article.
2 layers, 35 x 25 mm, JLC2313_1.6, 1 oz outer copper. Build quantity 5.

---

## 1. STENCIL REQUEST - window the exposed-pad aperture (owner-approved)

**Please window U1's exposed-pad paste aperture instead of using the single
full-size opening the gerbers currently carry.**

- U1 is an LMR33630ADDAR in a SOIC-8-EP (TI DDA). Its exposed pad is
  2.5 x 3.5 mm and the F.Paste layer currently has ONE 100 % aperture over
  the whole 8.75 mm2 pad.
- **Twelve 0.30 mm thermal vias sit inside that pad**, open on the top side
  (tented on the bottom only). Barrel sink volume is ~1.36 mm3 against
  ~0.53 mm3 of solder metal from a 0.12 mm stencil - a 2.6:1 sink-to-source
  ratio. Left as-is, solder wicks into the barrels and starves the pad joint.
- Requested: **60-80 % paste coverage, split into sub-apertures that avoid
  the via barrels** (typically 4-9 windows). Standard practice for
  via-in-pad thermal pads.
- Why it matters more than usual here: this pad is not only the sole heat
  path of a 2-layer thermal design, it is also **AGND** - the datasheet
  (Table 6-1) states every electrical parameter is measured with respect to
  it. A starved joint degrades cooling AND the voltage reference.

If windowing is not available, please advise before building rather than
proceeding with the full aperture.

## 2. Assembly sequence

1. **SMT reflow, TOP SIDE ONLY** - 14 placements (CPL.csv). The bottom side
   carries no components by design: it is one unbroken ground pour that acts
   as the return path, the switch-node reference plane and the board's
   radiator. Do not place anything on it.
2. **Hand-solder the two THT screw terminals AFTER reflow** - J1 and J2
   (KF128-5.08-2P-AA, C474952). They are deliberately excluded from BOM.csv
   and CPL.csv and appear only in BOM-full.csv, marked `hand_install`.

**Iron/preheat note for J1 and J2:** the GND pin of each terminal is flooded
**solid** into the ground pour on both layers, with no thermal relief. That
is deliberate - the pour carries the 2.6 A return and thermal-relief spokes
would throttle it - but it makes those two pins a large heat sink. Use a
60-80 W iron with a chisel tip, or preheat the board, and verify a full
fillet. A cold joint there is a 2.6 A return path.

## 3. Polarity - there is no reverse-polarity protection on this board

By design (the board is a deliberately minimal study article), so **the silk
is the only defense**:

- **J1 = INPUT.** Silk reads `VIN`, with `+` marking pin 1. Pin 2 is ground.
- **J2 = OUTPUT.** Silk reads `5V OUT`, with `-` marking pin 2. Pin 1 is +5 V.

J1 and J2 are the same physical part. Connecting the 24 V supply backwards
to J1 destroys U1.

## 4. Bench operating notes (for whoever brings this up)

- Input 18-30 V DC. **30 V is a hard maximum** - the converter is rated
  38 V absolute max and there is no input clamp.
- **Do not hot-plug the input.** Land the wires first, then bring the supply
  up from zero. Connecting live through lead inductance rings the input to
  roughly 1.5-1.6x the supply voltage; from 30 V that is 45-49 V, past the
  part's 38 V rating.
- Output 5 V, 0-2 A into a resistive load.
- **TP1 is the switch node, TP2 is its ground.** Scope them as a pair with a
  short ground spring - that is what the pad pair exists for.
- Regulation holds +/-3 % and <= 50 mV ripple from ~200 mA to 2 A. Below
  ~200 mA the converter enters PFM/burst mode: ripple and output voltage
  both rise, and that is expected, not a fault.

## 5. What this board deliberately does NOT have

Recorded so a reviewer does not read them as omissions: no input TVS or ESD
protection, no reverse-polarity protection, no fuse, no EMI input filter, no
OVP/OCP/UVLO beyond what lives inside the IC, no indicators, no second rail,
and no test points other than the one switch-node probe pair. All are scope
decisions for a single-block study article, not oversights.
