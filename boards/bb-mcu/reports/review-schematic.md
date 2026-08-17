# Schematic review - bb-mcu (adversarial, P4)

Reviewer: schematic-reviewer subagent, fresh context. Reviewed from the rendered
PDF (`reports/schematic.pdf`, 1 page, read at 500 dpi in five crops), the
netlist (`reports/top.net`), `parts/C89040.json`, the source datasheet PDF
(ST DocID024849 Rev 3) read directly, `parts/C8465.json`, `parts/C32713271.json`,
`kicad/decoupling.json`, `architecture/constraints.json`, `requirements.md`,
`reference/build-modes.md`, and the mcu / connector / power checklists.
`reports/gate-erc.json` is clean (0 violations) and was taken as given.

**Gate: 0 errors / 3 warnings.**

The block is electrically correct. Every "must" in the part's datasheet is on the
page, the boot strap points the right way, and the two decisions most likely to be
wrong (VDDA tied hard to VDD; no series resistors on SWD) are right for reasons the
datasheet actually supports. All three warnings are about what happens at the
bench, on connectors that have no keying.

## Scope tier applied

Build mode `learning block-basics:` -> scope tier `block-only`, binding
`canonical`. Per `reference/build-modes.md` this tier EXCLUDES protection,
filtering, indicators, test-points, config, second-rail, mechanical and
enclosure-fit. Nothing below is a report of an absent TVS, an absent
reverse-polarity part, an absent LED, an absent reset button or an absent test
point, and no missing board dimension is reported - geometry is an output earned
at P6. Rigor is not relaxed, and the findings below are all things that make the
block itself risky at its stated operating point.

---

## Findings, worst first

### W1 (warning) - NRST carries no capacitor on the one board that pushes it onto a flying lead

`kind: nrst-missing-datasheet-cap` | net `/NRST` | refs U1, J2

`/NRST` has exactly two nodes: U1 pin 4 and J2 pin 5. Nothing else. The node is
held only by the die's own weak pull-up (Table 49: RPU 25 / 40 / 55 kOhm,
typ 40k), and it is deliberately extended off-board onto an unshielded flying
lead in a bench environment.

What the part's own datasheet says, read directly from the source PDF:

- Figure 21 (p66) is titled **"Recommended NRST pin protection"**. Note 1:
  *"The external capacitor protects the device against parasitic resets."*
  The figure draws the external reset circuit and the capacitor as two separate
  elements - the note attaches the protection claim to the **capacitor**, and it
  is not conditioned on a button existing.
- Table 49 (p65) bounds the die's own filter exactly: `VF(NRST)` (input pulse
  that IS filtered) max **100 ns**; `VNF(NRST)` (pulse guaranteed NOT filtered)
  min **300 ns** at 2.7-3.6 V. So the silicon rejects glitches below 100 ns and
  is guaranteed to reset on anything at or above 300 ns.
- `parts/C89040.json` - this run's own ground-truth extraction - lists
  `{"pins": ["NRST"], "value": "0.1 uF to GND (recommended)"}` inside its
  `decoupling[]` array, alongside the VDD and VDDA entries that WERE built.
- `research/records/swd-debug-port-nrst-on-the-header.yaml` - this run's own
  verified research record - carries `datasheet_recommended_cap_uf: 0.1` and
  quotes note 1 verbatim.

The recorded reason for omitting it (P1 decision, and repeated in
`constraints.json` notes) is: *"AN4325 files it under OPTIONAL components,
'for RESET button', and this board has no reset button."* That is a true
statement about AN4325 and a wrong conclusion about this board. The datasheet -
the higher authority, and the one `requirements.md` s1 binds to ("exactly the
support components its datasheet requires") - recommends the capacitor
unconditionally, as protection, not as button debounce. Section 1 also names
NRST explicitly as in scope: "whatever the part needs on NRST / boot-mode /
supply pins to run and to be debugged".

Why it matters at bring-up, quantified. Without the cap the node's only
capacitance is trace plus probe lead, order tens of pF; against 40 kOhm that is
a ~1 us time constant, so a capacitively coupled transient on a hand-routed
flying lead can hold NRST below `VIL(NRST)` (0.3*VDD + 0.07 = ~1.06 V at 3.3 V)
for far longer than the 300 ns that is guaranteed to reset the part. With
100 nF the time constant is 4 ms and the same injected charge moves the node by
millivolts. The failure mode is a spurious reset mid-SWD-session, which drops
the debug connection and presents exactly as "bring-up does not work".

The counter-argument in the run's own research record - the cap "also loads
whatever the probe drives" - does not hold up: a probe asserting reset through
its driver into 100 nF settles in microseconds against assertions that last
milliseconds, and release through the 40 kOhm pull-up takes ~4 ms into a
Schmitt input with 200 mV hysteresis. That is ST's own reference circuit.

Not raised as an error because it is probabilistic, not deterministic, and the
run recorded it as an accepted risk. It is raised as a warning because the
reason recorded for accepting it misreads the source, and because this board
maximises the exposure the source is about.

### W2 (warning) - a one-position slip on J2 lands a probe push-pull output directly on +3V3

`kind: j2-offset-lands-probe-driver-on-rail` | net `+3V3` | refs J2

J2 is `GND / SWCLK / +3V3 / SWDIO / NRST` on positions 1-5, on an
`HX PZ2.54-1x5P ZZ` header whose own extraction states "No polarization/keying
feature is depicted anywhere on the drawing sheet".

The recorded P1 ruling analysed the **180 degree reversal** and got it right: on
a 5-way shell position 3 is the fixed point of the reversal map i -> 6-i, so
+3V3 at the centre is the only arrangement in which a reversed plug puts the
probe's high-Z VTref on the board rail. I re-derived it and agree; I also agree
that GND and NRST at the ends means a reversed probe ground clamps reset rather
than a data line, which is benign and self-announcing at the bench.

What the ruling never considered is the **one-position offset**, and the same
centre placement makes that case worse, not better. +3V3 at position 3 is
flanked by SWCLK (2) and SWDIO (4), which are the two probe **push-pull
drivers**. Slip one position either way and one of them lands on the rail:

- offset up: probe SWCLK -> board +3V3, probe GND -> board SWCLK,
  probe VTref -> SWDIO, probe SWDIO -> NRST.
- offset down: probe SWDIO -> board +3V3, probe SWCLK -> board GND,
  probe VTref -> SWCLK, probe NRST -> SWDIO.

In both directions a probe output driver is tied to the 3.3 V rail with no
series element (correctly - the "no series resistors on SWD" ruling is sound,
see below - and no protection, correctly excluded by mode). Every time that
driver goes low it sinks the bench supply's full current limit, ~0.5 A per the
owner's answer 1, plus the discharge of 5.8 uF of on-board bulk, into a driver
rated for tens of milliamps. The board survives; the probe may not, and the
rail collapses while it happens.

This is not a request for a part. No ordering of an unkeyed 5-way removes the
offset hazard, so the only mitigation is the per-pin silk that
`constraints.json` notes already declare load-bearing - and that note itself
records that `stm32-blinky` promised silk-labelled pins and shipped without
them, with its pin-1 marker hidden under the header body. Reported so that P6/P8
treat the J2 silk and its pin-1 marker as a hard deliverable rather than a
nicety, and so the reversal ruling's rationale is not read as covering
mis-plugging in general.

### W3 (warning) - J2 and J3 are the identical unkeyed part and their centre pins are +3V3 and GND

`kind: j2-j3-interchangeable-headers` | net `+3V3` | refs J2, J3

Both connectors are LCSC `C32713271`, both use footprint
`aiee:HDR-TH_5P-P2.54-V-M`, both are 1x5 0.1 inch, both unkeyed, and they sit on
adjacent edges of a board that is a few centimetres across. Nothing on the board
distinguishes them mechanically.

J2 position 3 is `+3V3`. J3 position 3 is `GND`. The J3 pin-order decision says
GND-at-centre "reuses J2's reversal geometry" - it reuses the geometry and
inverts the electrical meaning of the position, which is precisely the collision.

Consequence: plug the GPIO bench cable (whose centre wire is the return clip)
into J2 and the 3.3 V rail is shorted to ground through that cable. There is no
fuse, no current limit and no polarity feature anywhere in the path - all
correctly excluded by the block-only tier, so the board cannot catch it. At the
owner's stated ~0.5 A limited bench supply this is a nuisance; fed from another
board's 3.3 V pin behind a regulator that will happily deliver an amp, it is a
wire-and-terminal heating event. The reverse mis-plug (SWD probe into J3) is
benign and self-announcing: VTref lands on GND, reads 0 V, and the probe refuses
to talk.

Same mitigation as W2 and same reason for reporting it: the silk on both headers
plus a distinguishing pin-1 marker is the whole defence, so it has to survive to
P8. If a cheap ordering change is wanted, moving J3's GND off position 3 breaks
the collision without adding a part - but it costs J3 the signal-to-return
distance the J3 decision bought, so this is a trade for the orchestrator, not a
defect to fix blind.

---

## Checked and cleared (this is where the review spent most of its effort)

**BOOT0 strap polarity - VERIFIED CORRECT, and the run's open question is now
closed.** R1 is 10k from `/BOOT0` (U1 pin 1) to GND: a pull-DOWN, confirmed in
the netlist and read off the rendered page. The P2 decision correctly recorded
that the polarity could not be sourced from any allowlisted host, because the
mapping is in RM0360 and the datasheet's own section 3.3 (p12) names the three
boot options without giving the table. I sourced it: ST's STM32F0 Series
application note, Boot Configuration section, gives

| Boot mode | BOOT0 | BOOT1 |
|---|---|---|
| Main Flash memory | 0 | x |
| System memory | 1 | 0 |
| Embedded SRAM | 1 | 1 |

with "The values of both BOOT0 pin and nBOOT1 bit are latched on the 4th rising
edge of SYSCLK after a reset". Corroborated twice: the ST community thread on
the F0 nBOOT1 bit ("BOOT0 High to get to System Loader mode, and Low to get to
FLASH"), and the STM32F030-specific statement that nBOOT1 defaults to 1 because
the User and Read Protection Register ships as 0x00FF55AA, "so if BOOT0 is set
to 0, then the program in the main Flash memory is executed at startup".
**BOOT0 low = boot from main Flash = what this board wants.** The pull-down is
right. Sourcing caveat: reached through a third-party rendering of the ST
application note plus two secondary sources, not from st.com directly (every
st.com PDF fetch timed out), so this is good enough to retire the design risk
and probably not good enough for a knowledge record without an st.com read.

Level margins check out too: BOOT0 has no internal pull (Table 11 Notes cell is
empty, and Table 10 structure "B"), so the strap is genuinely required support,
not an excluded config strap. `VIL(BOOT0)` max = 0.3*VDD - 0.3 = 0.69 V at
3.3 V; 10 kOhm against BOOT0's leakage puts the node in the low tens of
millivolts. 300 mV of hysteresis on top. No issue.

**VDDA tied hard to +3V3 with no series element - CORRECT, and a ferrite here
would be a fault.** I checked this against the datasheet rather than the
decision text. Figure 12 (p41, "Power supply scheme") shows the VDDA domain
feeding "ADC" **and "Analog: RCs, PLL..."** - so on a board running from the
internal 8 MHz HSI with no crystal, VDDA is the clock supply, not an unused
analog rail. Table 21 requires VDDA >= VDD, and the abs-max table bounds
|VDD - VDDA| at 0.4 V when VDD > VDDA. A series bead or resistor can only ever
drive VDDA below VDD under load and transients, i.e. can only violate both. The
direct tie makes the difference identically zero. The P2 decision that replaced
the weaker scope-based reason with this positive one was right to do so, and it
survives a reviewer who does not accept scope arguments. TSSOP20 bonds no VSSA
(confirmed absent from Table 11's TSSOP20 column), so a separate analog return
is not even available; VSS is the correct return for C3/C4.

**Decoupling per power pin - EXACT match to the datasheet, no gaps.** TSSOP20
bonds exactly three supply pins: VDDA (5), VSS (15), VDD (16). Figure 12's
caution is "must", not "should": each supply pair must be decoupled.
- VDD pin 16: C1 100 nF + C2 4.7 uF. Figure 12 shows 2x100nF + 1x4.7uF for the
  packages with two VDD/VSS pairs; scaling to the single pair on TSSOP20 gives
  1x100nF + 4.7uF. Correct.
- VDDA pin 5: C3 10 nF + C4 1 uF. Figure 12 verbatim. Correct.
- `kicad/decoupling.json` associates all four to the right pins and classes
  (hf/bulk), and none carries role `reg_input` - right, there is no regulator.
This is the item the prompt asked me to attack hardest and it is clean.

**abs_max vs applied rails on U1 (all 29 entries swept).**
- VDD-VSS abs max -0.3 to 4.0 V; applied 3.135-3.465 V (3.3 V +/-5 %). Pass.
  Operating max is the binding number at 3.6 V, 0.135 V of headroom. A bench
  supply mis-set above 3.6 V destroys the part and nothing on the board stops
  it - that is the mode's excluded protection class, stated as a bench fact and
  NOT reported as a finding.
- VDDA-VSS abs max -0.3 to 4.0 V; same net, same numbers. Pass.
- |VDD - VDDA| abs max 0.4 V; applied exactly 0 V. Pass, best possible.
- VIN on BOOT0 abs max 0 to VDDIOx+4.0; applied 0 V. Pass.
- VIN on TTa (PA0-PA3) abs max VSS-0.3 to 4.0 V; nothing on the board drives
  them. Pass on-board.
- VIN on FT pins: PF0, PF1, PA9, PA10 are all NC; PA13/PA14 see only a probe at
  3.3 V logic. Pass.
- Sum IVDD abs max 120 mA. The requirements' 100 mA is a marked sizing GUESS,
  and it is worth noting it sits at 83 % of the part's own abs-max total - but
  an F030 on internal RC at 48 MHz draws ~13 mA, so the guess is
  over-conservative for copper sizing, not unsafe. Pass.
- Per-I/O output current abs max +/-25 mA, total +/-80 mA. Four GPIO, no
  on-board load. Pass.
- Thermal: theta-JA 76 C/W, TJ max 150 C. At the 0.33 W worst-case ceiling and
  50 C ambient, TJ = ~75 C; at realistic draw, ~53 C. Enormous margin. Pass.

**Unused pins floating - safe on this part, not a finding.** PF0, PF1, PA4-PA7,
PA9, PA10, PB1 are all NC-flagged (verified on the rendered page: X markers on
pins 2, 3, 10, 11, 12, 13, 14, 17, 18). Datasheet Table 10, blanket Notes row:
*"Unless otherwise specified by a note, all I/Os are set as floating inputs
during and after reset."* Floating is therefore the die's own default state, not
a board-created condition, and at 3.3 V it costs input-buffer crowbar current,
not damage. I checked each for reset-time behaviour: PF0/PF1 are OSC_IN/OSC_OUT
but HSE is off by default and the part boots on the internal RC; PA9/PA10 are
the USART bootloader pins, reachable only from system-memory boot, which
BOOT0=0 prevents; PA4-PA7 and PB1 are plain GPIO with no reset-time role. The
standard remedy (configure unused pins as analog input) is a firmware line, and
`requirements.md` s1 states firmware is not a deliverable of this pipeline.

**The four GPIO taken straight out - nothing wrong with it.** PA0-PA3 -> J3
positions 1, 2, 4, 5, no series elements, no pulls. At reset they are floating
inputs so an unmated header is the correct idle state. They are TTa
(3.3 V tolerant, ADC-connected), NOT 5 V tolerant, abs max VIN 4.0 V - and I
looked hard at whether the four unused FT pins (PF0, PF1, PA9, PA10 - exactly
four were available) would have been the better bench choice. They would not
obviously: owner answer 3 explicitly waives 5 V tolerance, so this is not drift,
and Table 45 (I/O current injection susceptibility, p60) actually favours the
TTa choice for an over-voltage event - TTa/TC/RST pins are rated -5 / +5 mA
injection while FT pins are rated -5 / **NA** positive, and PF1 specifically is
rated **-0 / NA**, i.e. no injection at all. The recorded layout rationale (four
consecutive pins on one port, diagonally opposite the debug end, maximum
distance from SWCLK) is sound and I am not overturning it.

**SWD port - correct and complete, zero parts.** PA13/PA14 go straight to J2
pins 4 and 2. Table 11 note 7 configures them as SWDIO/SWCLK immediately after
reset with internal pull-up on SWDIO and pull-down on SWCLK already active, so
the port is live at reset with no external resistors - confirmed in the
extraction and in the datasheet pin table. The "no series resistors" ruling
knowingly overrules Raspberry Pi / Lauterbach / SEGGER and grounds itself on
AN4325 4.3.3 plus a 5 ns edge against a 125 ns half-bit; I checked the arithmetic
and it holds at any honest board size. NRST on J2 pin 5 is what makes
connect-under-reset possible, which is the only recovery path if firmware ever
claims PA13/PA14 as GPIO - and it is also the reason W1 matters more here than
on a board that keeps reset local.

**A blank part is programmable.** BOOT0=0 boots main Flash, which on a factory
part is erased; the core faults immediately, but the DAP is independent of the
core and NRST is on the header, so connect-under-reset works. No finding.

**J3 under reversal - genuinely safe.** GND at the centre is the fixed point of
i -> 6-i, so a reversed 5-way maps GND to GND and only swaps IO1<->IO4 and
IO2<->IO3: a silent identity swap with no damage path, since J3 carries no rail.
Under a one-position offset the cable's GND lands on an MCU GPIO; with no
firmware that pin is an input and nothing happens, and even driven push-pull the
short is bounded by the +/-25 mA per-pin abs max. Not reported.

**J1 - nothing to report inside scope.** Pin 1 = +3V3, pin 2 = GND. The screw
terminal is rated 300 V / 10 A (UL) against 3.3 V / <0.1 A. Its own extraction
states "No polarity/keying marked on the drawing - both poles are mechanically
and electrically symmetric", so the silk +/- legend is the entire defence
against a swapped supply - which `requirements.md` s2 states and
`constraints.json` notes already carry as a hard P6/P8 item. Reverse-polarity
protection is excluded by the tier and is not reported.

**Style items deliberately NOT reported as findings:** C3 is drawn mirrored
relative to C1/C2/C4 (pin 2 on the GND side); it is a non-polarised ceramic, so
this is a drawing inconsistency with no electrical meaning. The U1 library
symbol types every I/O as `passive` rather than `bidirectional`, which weakens
what ERC could ever catch on this sheet - noted, not filed.

## Open / could not verify

1. The exact capacitor value in datasheet Figure 21 could not be read from the
   PDF text layer (the figure's labels are in an obfuscated embedded font).
   The 0.1 uF comes from `parts/C89040.json`'s extraction of that figure and
   from the run's own research record, both of which agree; the figure's
   *existence*, its title and note 1's wording were read directly.
2. BOOT0 polarity is sourced (see above) but not from st.com - every st.com PDF
   fetch (RM0360, AN4080) timed out at up to 240 s. Fine for retiring the design
   risk; a knowledge record should wait for a first-party read.
3. The probe-side premise behind the J2 ordering - that a flying-lead probe's
   rail pin is a high-Z VTref sense input and not a driver - is still unsourced
   from any first-party host, exactly as the run's own P2 decision records. My
   W2 finding does not depend on it: SWCLK and SWDIO are drivers under any
   premise.
4. Silk content and pin-1 markers are P6/P8 artifacts and could not be checked
   here. W2 and W3 both reduce to "the silk must actually be there", and
   `constraints.json` already carries the requirement plus the stm32-blinky
   precedent of it being dropped.
5. Not reviewed, out of this role: footprints, land patterns, placement,
   routing, DFM. The J1 drill defect found and fixed at P3 is noted only as
   evidence that the connector work was done carefully.
