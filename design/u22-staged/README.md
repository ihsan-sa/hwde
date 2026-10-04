# U22 staged output for the boards repo

The hwde side of U22 landed in the library; this directory holds what the
boards repo still has to apply (this track could not write it).

- `queues/<board>/queue.yaml` - the resolved queue, zero pending. Copy over
  `~/dev/boards/<board>/learnings/queue.yaml`.
- `rulings/<board>.yaml` - who ruled what; copy beside the queue as
  `learnings/rulings-2026-10-04.yaml`. Do not re-run `resolve --batch`: the root
  LEARNINGS rows already exist and the tool refuses them.
- bb-amp: set `status: superseded` on research records
  `in-bias-current-return-path` and `in-bias-return-path-required` (merged).
- Then `learnings.py validate --workspace <board>` for each of the five.
- `second-reads.md` - the six bb-amp second reads (Q3).
- `records/` - the prep-mode staged merge (the approved copy is in the library).
