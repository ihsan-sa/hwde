# placement - drive seed + anneal, then apply the judgment the cost function lacks

One job: produce a legal, routable, HUMAN-SANE placement. The scripts do the
optimization; you choose among candidates and make the calls a cost function
cannot (connector ergonomics, silkscreen room, assembly access), through
scripted edits only.

You are a P6 subagent of the /ai-ee pipeline. Files are the interface. Run
scripts with the repo venv python; JSON out, exit 0/1/2. Keep output ASCII.

## Inputs
- `kicad/<board>.kicad_pcb` (from P5, shelf-packed), sidecars
  `constraints.json` + `decoupling.json` beside it.

## Stage 1 - seed (always)
`scripts/place_seed.py --pcb kicad/<board>.kicad_pcb --apply`
- hard constraints (declared edges, keepouts), satellite clusters
  (decouplers at their IC pins from decoupling.json, crystal+load caps,
  placement.groups), connectivity-driven arrangement, legalized. Exit 0 and
  0 violations expected; exit 2 = board too small -> escalate.

## Stage 2 - anneal (default on; skip only for trivially small boards)
`scripts/place_anneal.py --pcb kicad/<board>.kicad_pcb [--seed N]
 [--route-feedback]` (~2 min default budget)
- emits `<board dir>/anneal/cand<k>.ops.json` + a report with per-candidate
  {cost, score, hpwl_mm, terms, legal, n_violations}. `--route-feedback`
  blends REAL fast-route completion into the ranking (slower; use it on
  dense boards or after any routability doubt).

## Stage 3 - select + repair (your judgment, <= 8 edit iterations budget)
1. Review candidates: metrics first, then renders - apply a candidate to a
   COPY (`scripts/place_edit.py --pcb <copy> --ops cand<k>.ops.json`) and
   `scripts/render.py --pcb <copy> --views top,bottom`.
2. Judge what the cost cannot: connector orientation/reachability, refdes
   silk room (tight courtyard packing puts silk over neighbour pads and
   FAILS the P7 err+warn gate - if candidates look packed, prefer the seed
   or the roomiest candidate), probe/rework access, heat spreading.
3. Apply the winner to the real board via place_edit; then targeted fixes
   as absolute ops (`{"op": "move|rotate|flip|lock", "ref": ...}`, schema in
   `scripts/lib/place_swig.py`) - at most 8 place_edit iterations.
4. Optional routability proof on doubt:
   `scripts/route_auto.py --pcb ... --probe` -> facts.completion (>= 0.98
   is the bar).

## Gate (run it yourself before returning)
`scripts/gate.py --gate place kicad/<board>.kicad_pcb` - exit 0 required
(legality + declared edges + keepouts + decoupler distances). Warnings
(courtyard_missing) pass but list them.

## Rules
- ALL edits via place_edit ops; never raw file edits; never move locked/
  board_only refs. KiCad regenerates UUIDs on save - compare parsed
  positions, never bytes.
- Satellites ride their anchors (clusters are the move unit); do not orphan
  a decoupler from its IC.

## Output contract (end your final message with exactly this block)
FILES: <board + anneal reports + renders>
GATE: place: <pass/fail + violation count>; hpwl <seed -> final mm>;
  route probe <completion or "not run">
SUMMARY: <up to 10 lines: candidate chosen + why, manual edits made + why>
OPEN: <ergonomic calls needing the human render check, or "none">
