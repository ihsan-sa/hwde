# Build modes - scope envelopes a brief can declare

A brief may open with a MODE token. A mode is a SCOPE contract: it answers the
"how much board is this" questions up front so the brief does not have to, and
it binds every stage that would otherwise pad the design out. It never changes
what correct means.

Record the declared mode with `state.py decision` at P0 and name it in
`requirements.md` section 1 so later stages and reviewers can see it. A brief
with no token has no mode - design normally.

## ultra-bare-bones

Token: a brief opening `ultra bare bones design:` or `ultra-bare-bones:`.

Purpose: ONE functional block, built to be studied. These boards exercise the
pipeline and seed the knowledge library one domain at a time, so every part
that is not that block is noise.

**Include, and nothing else**
- The block's active part(s) plus exactly the support components its datasheet
  requires for correct operation at the stated operating point.
- One input and one output interface, each the simplest part that carries the
  power or signal involved - unless the block under study IS an interface, in
  which case that interface is whatever its standard requires.
- What the fab needs to build the board and the bench needs to hold it.

**Exclude, unless the block under study IS that thing**
- Protection of every kind: TVS/ESD, reverse polarity, fusing, OVP/OCP/UVLO
  beyond what lives inside the IC.
- Filtering, sequencing or conditioning the datasheet does not require.
- Indicators, displays, buttons, jumpers, config straps, DNP/alternate
  footprints, and test points beyond the block's own measurement need.
- Any second rail, second IC or MCU the block does not need in order to work.
- Mechanical and enclosure features beyond mounting the bare board.

**Defaults - apply them, do not ask**
- The fewest layers the block honestly needs; JLC PCBA, single-sided assembly.
- Quantity 5, cost minimal, no enclosure, bench environment (indoor, 0-50 C).
- Size: the smallest outline that keeps the layout HONEST - never so tight the
  layout stops being representative of the block, never padded for features
  that do not exist.
- Stop at P9 (fab package + DFM). Ordering is a separate owner decision.

**What the mode does NOT relax.** Everything that makes the board true: every
gate, the P2/P3 coverage checks and the research they trigger, DFM, the
datasheet's own requirements, and every safety question in the
requirements-analyst's section 8. A minimal board is minimal in SCOPE, never in
rigor. If the stated operating point implies a hazard (mains, >30 V, >3 A,
battery), ask - the mode grants no silence there.

**Reviewers.** A feature this mode excludes is NOT a finding: do not report
absent ESD, protection, indicators or spare rails. Everything else you hunt is
unchanged - report anything that makes the block itself wrong, unsafe at its
stated operating point, or unbuildable.

**Knowledge guardrail.** These exclusions are SCOPE decisions, not engineering
judgments. Never write a knowledge record, or promote a learning, that says a
protection or conditioning feature is unnecessary in general - a learning from
one of these boards is valid only where it concerns the block's own topology,
layout or manufacture. Workspace learnings from a mode board carry the mode
token so promotion review can see the provenance.
