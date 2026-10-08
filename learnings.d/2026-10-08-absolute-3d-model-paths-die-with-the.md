## 2026-10-08 [easyeda2kicad][parts][verify] Absolute 3D model paths die with the worktree that pulled them
The fix for relative --out-dir (LEARNINGS 2026-07-28) made lib_pull resolve
the dir before handing it to easyeda2kicad, which copies it verbatim into
every footprint's (model ...). So every pull since baked the absolute path of
the checkout that ran it, and the board took the path from the footprint on
update. Eleven boards in the boards repo named models inside
.cc/worktrees/boards/<track>/...; once a track's worktree was removed the
models were gone (PCB-0020-A's USB-C rendered wrong in a doc). Older boards
carry C:/dev/... and /workspace/... paths the same way. Render never showed
it, because kc.render_png relinks a dead path by name to the workspace lib.
The board's project dir is <ws>/kicad and the lib is <ws>/lib, so the
portable form is ${KIPRJMOD}/../lib/aiee.3dshapes/<name>, not
${KIPRJMOD}/lib/... . lib_pull now rewrites each pulled footprint to that
form (relative to --project, else <out_dir>/../kicad), check_model_paths
fails a board on any model path that is neither ${KICAD*_3DMODEL_DIR}/ nor
${KIPRJMOD}/ inside the workspace, and its --fix rewrites the board and the
lib footprints by name. Fix the lib footprints too, or the next footprint
update brings the old path back.

Triage: now L2 | target L3 | owner scripts/check_model_paths.py | status open | note lib_pull writes portable paths (L3) for new pulls; the 11 boards still need check_model_paths --fix; tests/test_model_paths.py pins both.
