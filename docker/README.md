# hwde in a container (Linux)

The S0 environment was verified on Windows (`CLAUDE.md`). This directory is the
Linux/Docker port: one image with the whole toolchain, used both for interactive
sessions and for unattended board runs.

| Piece | Where | Note |
|---|---|---|
| `Dockerfile` | image `hwde-run:latest` (any name works) | FROM `kicad/kicad:10.0.5` (Debian 13, kicad-cli 10.0.5, python 3.13.5 + SWIG pcbnew, symbol/footprint libs, libngspice) + Node + Claude Code + venv (`requirements.lock` minus pywin32) + Temurin 25 JRE + Freerouting 2.2.4 + KiCadRoutingTools 0.19.0 + TeX Live + xvfb |
| `project-init` | the image's entrypoint | links `/workspace/.venv -> /opt/venv`, marks `tools/` as unused, git safe.directory, starts Xvfb `:99`, then execs the command |
| `hwde-loop` | `/usr/local/bin/hwde-loop <board>` | unattended run: `claude -p "/hwde ..."` per iteration, fresh context, resumes from `state.json`; journal `boards/<b>/log/run-journal.md`; per-iteration records `boards/<b>/log/run/` (reduced - no session ids or token counts) |
| `run-contract.md` | read by the loop every iteration | the delegation rules + Done criteria for an unattended run |

Toolchain pins in the container are env vars read by `scripts/lib/env.py`:
`HWDE_KICAD_CLI HWDE_JAVA HWDE_FREEROUTING_JAR HWDE_KRT_DIR HWDE_NGSPICE_DLL`
(+ `KICAD10_*_DIR`). KiCad 10.0.3 (the Windows pin) has no published image;
10.0.5 shares the 10.0 file format - never mix with 9.x.

## Use

    docker build -t hwde-run:latest -f docker/Dockerfile .

    # interactive session in the container (repo bind-mounted at /workspace)
    docker run --rm -it -v "$PWD:/workspace" hwde-run:latest bash

    # unattended full run of boards/g0-sense
    docker run --rm -v "$PWD:/workspace" hwde-run:latest hwde-loop g0-sense

    # verify the environment inside the container
    make check          # pytest + check_env --quiet
    make env            # check_env --full (SWIG round-trip probe)

`hwde-loop` reads `HWDE_REPO_DIR` (the repo checkout, default `/workspace`) and
`HWDE_RUN_CONTRACT` (default `docker/run-contract.md`), so it does not care how
the container was started. Claude Code needs its login state: mount a directory
at `/home/node/.claude` (or pass an API key) before an unattended run.

Watching a run from the host - polling the container, posting progress to a chat
or notification service - is out of scope here and left to whatever tooling you
already use; everything the loop knows is in `boards/<b>/log/run/loop.log`,
`boards/<b>/log/run/STATUS` and the journal.

Runs need open network egress (datasheets come from arbitrary vendor hosts); the
research allowlist (`reference/knowledge/domains.yaml`) still governs what a
researcher may cite. No credentials are mounted: the run commits locally and
stops at the order-ready package; pushing and ordering stay with the owner.
