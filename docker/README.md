# ai-ee in a container (Linux)

The S0 environment was verified on Windows (`CLAUDE.md`). This directory is the
Linux/Docker port: one image with the whole toolchain, used both for interactive
ccbox sessions and for unattended board runs.

| Piece | Where | Note |
|---|---|---|
| `Dockerfile` | image `ccbox-<name>:latest` | FROM `kicad/kicad:10.0.5` (Debian 13, kicad-cli 10.0.5, python 3.13.5 + SWIG pcbnew, symbol/footprint libs, libngspice) + Node + Claude Code + venv (`requirements.lock` minus pywin32) + Temurin 25 JRE + Freerouting 2.2.4 + KiCadRoutingTools 0.19.0 + TeX Live + xvfb. ccbox's entrypoint/firewall are copied from the `ccbox:latest` base image (iiks1). |
| `ccbox-project-init` | runs at container start | links `/workspace/.venv -> /opt/venv`, marks `tools/` as unused, git safe.directory |
| `ai-ee-loop` | `/usr/local/bin/ai-ee-loop <board>` | unattended run: `claude -p "/ai-ee ..."` per iteration, fresh context, resumes from `state.json`; journal `boards/<b>/log/run-journal.md`; transcripts `boards/<b>/log/run/` |
| `run-contract.md` | read by the loop every iteration | the delegation rules + Done criteria for an unattended run |
| `watch-run.sh` | host side | polls the container, posts progress to Slack via `cc-notify`, final report |

Toolchain pins in the container are env vars read by `scripts/lib/env.py`:
`AIEE_KICAD_CLI AIEE_JAVA AIEE_FREEROUTING_JAR AIEE_KRT_DIR AIEE_NGSPICE_DLL`
(+ `KICAD10_*_DIR`). KiCad 10.0.3 (the Windows pin) has no published image;
10.0.5 shares the 10.0 file format - never mix with 9.x.

## Use

    # on the box (iiks1 ccbox): build the project image, then a normal or headless session
    git clone <repo> ~/dev/ai-ee-run && ccbox build ai-ee-run
    ccbox ai-ee-run --open-egress                                   # interactive claude in the container
    ccbox ai-ee-run --open-egress --cmd "ai-ee-loop g0-sense"        # unattended full run of boards/g0-sense
    ccbox shell ai-ee-run   # poke around;  docker/watch-run.sh ai-ee-run g0-sense   # host-side progress to Slack

    # verify the environment inside the container
    make check          # pytest + check_env --quiet
    make env            # check_env --full (SWIG round-trip probe)

Runs need open egress (datasheets come from arbitrary vendor hosts); the
research allowlist (`reference/knowledge/domains.yaml`) still governs what a
researcher may cite. No credentials are mounted: the run commits locally and
stops at the order-ready package; pushing and ordering stay with the owner.
