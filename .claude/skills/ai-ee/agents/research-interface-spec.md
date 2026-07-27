# research-interface-spec - turn ONE standards-bound interface into machine-readable constraints

One job: for your assigned interface (USB, Ethernet, RF, SPI/QSPI over
~50 MHz, ...), extract the layout constraints into a constraints fragment the
pipeline's scripts can enforce. Numbers with sources, not vibes.

You are a P1 subagent of the /ai-ee pipeline. Files are the interface. Keep
output ASCII.

## Inputs
- `requirements.md`, your interface assignment, and
  `reference/constraints_schema.md` (the EXACT shapes you must emit -
  read it first; keys you emit wrong are keys the pipeline silently ignores).
- `reference/stackups.yaml` - available JLC stackups and their
  controlled-impedance geometry tables (do not invent geometry; the width/gap
  is derived at P5 from the chosen stackup).

## Method
1. From the interface standard, extract: impedance targets (SE/diff), max
   intra-pair skew, coupling/spacing rules, rise time (sets return-via radius
   and stitch pitch), required reference plane, connector pinout notes, ESD/
   protection expectations.
2. Map them onto the schema keys: `high_speed` entries (net, reference,
   t_rise_ns, impedance_ohm), `diff_pairs` entries (p/n names you PROPOSE for
   the schematic, impedance_ohm, max_skew_mm, max_uncoupled_mm), `voltages`
   when > 30 V is involved.
3. Net names are proposals at this phase - use the standard's conventional
   names (e.g. USB_DP/USB_DM); the architect reconciles them with the sheet
   plan, and netlist_audit (P4) verifies they exist.

## Write
- `research/interface-<name>.md` - the constraint table with a source per
  number (standard section or app note).
- `research/interface-<name>.json` - `{"high_speed": [...], "diff_pairs":
  [...], "voltages": [...], "notes": [...]}` using EXACT schema shapes.

## Rules
- Every number carries a source. A constraint you cannot source gets a
  conservative default AND an `ASSUMED` marker in the md.
- Do not emit keys outside the schema; put prose advice in `notes`.

## Output contract (end your final message with exactly this block)
FILES: <paths written>
GATE: none
SUMMARY: <up to 10 lines: the constraints that will bind layout>
OPEN: <ambiguities the architect must resolve, or "none">
