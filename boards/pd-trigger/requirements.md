# Requirements: pd-trigger

Source: `brief/brief.md` (S14 run c - novel brief). No other attachments.
Unstated low-risk items are marked `ASSUMED:` inline. Section 9 holds every
design-changing or safety-relevant unknown - all six items there trace back
to the >3A flag (section 8) or a part-selection conflict found while
writing this document; none are guessed.

## 1. Function

A USB-C Power Delivery trigger/breakout board for bench use. A CH224-class
(or equivalent) PD sink controller negotiates as a SINK with a connected
USB-C PD charger/source, and the user selects one of five PD profiles
(5/9/12/15/20V) via an onboard selector (DIP switch, jumper, or button -
architect's choice, stated). The negotiated voltage is delivered on a screw
terminal (primary output) plus an auxiliary 2.54mm header, sized for 5A
continuous (up to 100W at 20V). Status LEDs show at minimum power-present;
per-profile indication is optional ("welcome" but not required). No
regulation/conversion circuitry beyond the PD negotiation itself - this is
a pass-through trigger board, not a DC-DC converter. Bench tool: no
enclosure, no battery. Prototype qty 10.

NOTE: delivering 5A continuous through a compact ~40x25mm 2-layer board is
a real copper-sizing constraint (trace/pour width, copper weight, thermal
relief) - carried forward as a directive for the architecture stage: verify
against a current-capacity calculation, do not assume default 1oz copper
is sufficient without checking.

## 2. Interfaces

- USB-C receptacle (input): PD SINK only, stated. Negotiates with the
  source; no USB data function (no D+/D-, no USB 2.0/3.x data role) implied
  or needed - power-only use of the connector. ASSUMED: CC1/CC2 wired per
  the chosen PD controller's application circuit (architect's part choice
  drives the exact pinout).
- Output voltage selector: onboard, type left to architect (DIP switch /
  jumper / button) - stated explicitly as the architect's choice.
- Output connector: 2-pole screw terminal (V+/GND), primary output,
  stated. Pitch/current rating: see open question 3.
- Auxiliary output: 2.54mm pin header, stated. Its purpose and current
  rating relative to the screw terminal are unstated and matter for part
  selection - see open question 4.
- Status indication: at least 1x power-present LED, stated (mandatory).
  Per-profile indication: stated as "welcome," i.e. optional. ASSUMED:
  architect adds it only if cheap/simple (e.g. one extra LED or a color
  change), omits otherwise - no user decision needed here.

## 3. Power

- Source: USB-C VBUS, PD-negotiated as SINK only. No battery, no mains, no
  other input (stated: "no battery").
- Negotiated profiles: 5V / 9V / 12V / 15V / 20V, user-selected (stated) -
  the profile set CH224-class trigger controllers natively support
  (matches the brief exactly).
- Design current: 5A continuous per the brief, stated as sizing "the power
  path" generally (copper, terminal, connector). Whether that means a
  uniform 5A at EVERY profile (25W at 5V up to 100W at 20V) or a
  per-profile-varying cap is the single most consequential unknown in this
  document - see open question 1.
- 100W at 20V (5A x 20V) is within normal USB PD range but only reachable
  if the source advertises a 20V/5A PDO AND the cable is electronically
  marked (e-marked) for 5A - both outside this board's control. Noted here
  as a fact, not a question: the board must be built to handle 5A when
  offered, not guaranteed to receive it from every source/cable pairing.
- USB-C receptacle current rating: the connector itself is spec'd for up
  to 5A (with an e-marked cable) by the USB-C standard - no separate
  rating decision needed for the input connector.
- Rail budget for the controller/logic/LEDs (GUESS): low tens of mA,
  negligible next to the 5A main path. No separate regulator is implied by
  the brief (pass-through trigger board, not a DC-DC converter). ASSUMED:
  the PD controller supplies its own housekeeping rail internally (typical
  for CH224-class parts) or the selector/LEDs draw directly off VOUT;
  architect confirms against the chosen part.
- Fusing / input protection: TVS is stated (add it). Fusing is explicitly
  conditional in the brief ("if warranted") - for a >3A path this is
  safety-relevant and not guessable - see open question 2.

## 4. Environment

Not stated beyond "bench use, no enclosure" (stated). ASSUMED: indoor
lab/bench ambient (roughly 0-40C), no ingress protection, no
vibration/shock requirement. Low risk - qty-10 prototype, easy to revisit.

## 5. Size & mounting

- Outline: brief says "compact (~40x25mm target)" - a target, not stated
  as a hard max. Fitting a USB-C receptacle, a 5A-rated screw terminal, PD
  controller, selector, and LEDs is workable at this size but tight, and
  the tolerance if the layout runs slightly over is unstated - see open
  question 5.
- Mounting holes: not stated. ASSUMED: none (bench use, no enclosure).
- Height limit: not stated. ASSUMED: none (open board, no enclosure); the
  screw terminal and USB-C receptacle heights are the practical limits.

## 6. Quantity & budget

- Build quantity: prototype qty 10 (stated).
- Target unit cost: not stated. ASSUMED: no hard cap; minimized via the
  JLC Basic parts preference + economy PCBA (stated strategy).

## 7. Assembly

- JLCPCB, 2-layer, economy PCBA "where possible" (stated). ASSUMED
  interpretation: JLC assembles everything it can from its catalog; any
  part that isn't JLC-catalog-assemblable (e.g. the screw terminal,
  possibly the USB-C receptacle depending on footprint/stock) is
  hand-soldered post-PCBA; architect decides per actual part availability.
- Parts: JLC Basic parts preferred (stated), not exclusive - Extended or
  hand-solder parts allowed where Basic doesn't cover the need (e.g. a
  5A-rated screw terminal, the PD controller itself).
- Sidedness: not stated. ASSUMED: single-sided (top) SMT preferred for the
  economy tier and small part count; architect may go double-sided if
  placement on ~40x25mm requires it.

## 8. Compliance/safety flags

- Mains voltage: no - USB-C PD input only, max 20V.
- Batteries: no (stated).
- Motors: no - output is a generic power tap, load-agnostic.
- >30V: no - max 20V from PD negotiation.
- High current (>3A): YES - power path is stated to be sized for 5A
  continuous, up to 100W at 20V. This is the primary safety driver for
  this board and the source of open questions 1-4 below: nothing about the
  current path is being guessed.
- RF transmit: no - no radio/wireless function.

## 9. Open questions

All six items below stem from the >3A safety flag (section 8) or from a
part-selection conflict found while writing this document. The pipeline
will not proceed on assumptions here.

1. Max current commitment: does 5A continuous apply UNIFORMLY to every
   selectable profile (copper, terminal, and connector all handle 5A even
   at 5V/9V/12V/15V, not just at 20V), or does the design current vary by
   profile (lower at lower voltages)?
   DEFAULT: uniform 5A at every profile - simplest, safest, matches the
   brief's unconditional wording ("power path sized for 5A continuous"),
   and gives headroom since a typical PD source will offer less than 5A at
   the lower voltages anyway.

2. Fusing: add a fuse/current-limiting element on the input, and if so what
   type? The brief leaves this conditional ("fusing if warranted") but a
   5A/100W path is exactly the case where it usually is.
   Options: (a) none - rely on the PD source's own protections plus the
   TVS only; (b) resettable PTC/polyfuse (survives a downstream/output
   short without replacement); (c) one-time fast-blow fuse.
   DEFAULT: (b) resettable PTC, sized to hold at the committed current
   (question 1) with headroom and trip well above it - cheap, JLC-Basic-
   friendly, and self-resetting after a bench-tool short-circuit mistake.

3. Screw terminal sizing: what wire gauge should the output terminal
   accept, and what minimum current rating (component nameplate rating,
   not just the 5A operating point) should it carry? These two drive the
   same part choice (pitch/size), so they're answered together.
   Options: (a) 20AWG / rated >=5A (smallest footprint, least margin);
   (b) 18AWG / rated >=8A (comfortable margin); (c) 16AWG / rated >=10A
   (most margin, largest footprint - pressures the size target in
   question 5).
   DEFAULT: (b) 18AWG, terminal rated >=8A - standard mid-size terminal
   block class, reasonable margin above 5A without oversizing the board.

4. Auxiliary 2.54mm header purpose: standard 2.54mm pin headers are
   typically only rated ~1-3A PER PIN - well under the 5A design current -
   unless multiple pins are paralleled per net. The brief lists this
   header alongside the screw terminal without saying which duty it
   carries.
   Options: (a) full-power tap, same 5A as the screw terminal - requires
   paralleling 3+ pins per net (VOUT, GND), extra part count/footprint;
   (b) low-current/sense tap only (e.g. probing VOUT, driving small
   accessory logic) - NOT rated for the full 5A; (c) full-power tap via a
   beefier high-current 2.54mm-pitch connector instead of a plain header.
   DEFAULT: (b) - auxiliary header is a low-current tap only; the screw
   terminal is the sole full-current output. Simplest and smallest, and
   avoids silently under-rating a 5A path onto what looks like a generic
   0.1in header.

5. Size target tolerance: "~40x25mm target" - is this a hard ceiling
   (redesign if exceeded) or a soft target (get as close as practical,
   given a 5A-rated screw terminal, USB-C receptacle, and selector all
   need physical room)?
   DEFAULT: soft target - architect minimizes toward ~40x25mm but may run
   modestly over (roughly up to 15-20%) if needed to fit the current-rated
   connector/terminal safely rather than undersizing them to hit the
   number.

6. PD negotiation fallback behavior: CH224-class controllers commonly fall
   back to 5V (rather than holding or erroring) when the source can't
   deliver the user-selected profile (e.g. a weak/cheaper charger, or a
   non-PD source). Is a silent 5V fallback on the output terminal
   acceptable to whatever load the user connects, or must the board react
   differently?
   Options: (a) yes, silent fallback is fine - board just outputs whatever
   gets negotiated; (b) no - actively block/disconnect the output (e.g.
   via a load switch) unless the SELECTED profile is confirmed, rather
   than ever presenting an unrequested voltage; (c) fallback is fine but
   must be visibly indicated (status LED distinguishes "selected profile
   achieved" from "fallback/mismatch").
   DEFAULT: (c) - keeps the design simple (no added load switch) while
   making a wrong-voltage condition visible, which matters for a bench
   tool where the user picks a profile expecting the load to see that
   voltage.

## Answers (P0, decided by orchestrator as user's delegate per directive)
1. Uniform 5A at every profile. 2. Resettable PTC fuse. 3. Screw terminal
18AWG-capable, >=8A rated. 4. Aux header LOW-CURRENT tap only (silk-marked).
5. Size soft target (up to ~20% over allowed for current-rated parts).
6. 5V fallback ACCEPTABLE but must be VISIBLY indicated (profile LED scheme).
