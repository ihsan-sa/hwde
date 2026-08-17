# bb-mcu - environment facts found during this run

Candidates for the workspace LEARNINGS entry at run close (kept here so
`research.py close`'s own LEARNINGS appends are not raced).

## 2026-08-16 [research][network][fetch] st.com is UNREACHABLE from this host - the allowlisted route to ST primary docs is LCSC's wmsc mirror

Measured, not inferred:

    curl --max-time 20 https://www.st.com/       -> HTTP 000, 0 bytes, timeout
    curl --max-time 20 https://wmsc.lcsc.com/    -> HTTP 301 in 0.93 s

The P1 reference-design agent hit the same wall independently on both curl
and WebFetch, against working control fetches. It is a network-level block on
the host, not a bad URL and not a transient.

Why it matters to the pipeline: `st.com` IS on the `research.py fetch`
allowlist (`reference/knowledge/domains.yaml`), so a researcher will pick it
first and burn depth-cap attempts on a host that cannot answer. The working
route is `wmsc.lcsc.com`, also allowlisted, which serves the manufacturer's
own PDF - e.g. the STM32F030F4P6 datasheet at
`https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf`
and per domains.yaml's own note "(LCSC: use the wmsc form)".

Tier consequence: an ST datasheet fetched through LCSC is still tier
`vendor-layout` for an ST part - domains.yaml says the tier is a fact about
the DOCUMENT vs the SUBJECT part, not about the host.

What it does NOT solve: ST application notes and reference manuals (AN4325,
RM0360) and the errata sheet are not on LCSC. The P1 agent reached them only
through third-party mirrors that are NOT allowlisted, so a sanctioned
`research.py fetch` cannot acquire them. If a P2/P3 record needs one, the
correct move is to name the host in OPEN for the owner to rule on adding -
never to work around the refusal.

Consequence accepted for this run: records will be built from the datasheet
(the best tier available) and the P1 app-note findings ride along as research
context, cited as what they are.

### Update: st.com is not the only allowlisted host that is dark

`analog.com` is unreachable from this host too - HTTP 000 / 0 bytes on both
the site root and a direct PDF, the same class of network block. The P2
swd-debug-port researcher burned two fetch attempts discovering it (attempts
are capped at 3x the depth cap, so this is not free).

So the pattern is: **being on the allowlist says nothing about being
reachable.** Two of the biggest vendor domains on the list are dark from this
host. A researcher that plans its acquisitions around st.com or analog.com
will spend its depth budget on timeouts. Worth a line in the researcher role
prompt or in domains.yaml itself, not just in this workspace.

Hosts confirmed working this run: `wmsc.lcsc.com` (serves manufacturers' own
PDFs), `infineon.com`, `ti.com`, `microchip.com`, `nxp.com`.

## 2026-08-16 [fp_verify][librarian][footprint] fp_verify never checks row_spacing_mm, though land_pattern carries the field - a two-row package can be off by 0.25 mm and pass with one pad_size warning

The P3 librarian diffed the pulled U1 SOP-20 footprint against the datasheet
extraction and got: pad_count 20/20, pitch ok, pin-1 present, ONE warning on
pad_size. It then hand-measured what the tool does not look at:

    pad size     0.35 x 1.494 mm   vs datasheet 0.40 x 1.35 mm  -> warned
    row spacing  6.00 mm           vs datasheet 5.75 mm         -> NOT CHECKED

`land_pattern.row_spacing_mm` is populated by datasheet_extract (the U1
extraction filled it, showing the derivation), so the data is there and only
the comparison is missing. On a two-row leaded package, row spacing is the
dimension that decides whether the pads capture the lead FEET at all - it is
arguably more load-bearing than pad size, because getting it wrong shifts
both rows off the leads while every pad-count and pitch check still passes.

Here the deviation was benign and was accepted on a worked-through argument
(the pulled land still spans 2.253-3.747 mm from the centreline against a
lead foot at ~2.6-3.2 mm, so it captures the foot with more toe and a WIDER
inter-pad gap than ST's own land). But it was found by a human-style manual
measurement, not by the gate - so the next board's librarian may not find it.

Fix worth making: add a `row_spacing_mm` comparison to fp_verify with the
same tolerance treatment as pitch, and treat "datasheet states it but the
footprint cannot be measured for it" as a warning rather than silence.

## 2026-08-16 [windows][process][state] Backticks inside a Bash-tool argument are COMMAND SUBSTITUTION - a state.py decision silently lost a word

Recording a `state.py decision` whose `--why` prose contained a backtick-
quoted term:

    ... with the floor at `proven`, a verified-but-unapproved record ...

Bash ran `proven` as a command (`proven: command not found` on stderr),
substituted its empty output, and state.py stored:

    ... with the floor at , a verified-but-unapproved record ...

The decision was recorded, exit code was 0 for state.py, and the ONLY signal
was one stderr line from a different process than the one being checked. A
caller keying on the script's exit status sees a clean success.

This is the same family as the existing entry about the Bash tool collapsing
`\\` inside a quoted heredoc: prose destined for a file should not travel
through the shell. Long `--why` / `--note` text is exactly that kind of
prose, and it is the audit trail, so a silent deletion there is worse than
in most places.

Rules that follow:
- never put backticks in a Bash-tool argument, even inside single quotes at
  the outer level, if any inner quoting could expose them;
- for multi-sentence decision/note prose, prefer writing a file with the
  Write tool and passing a path, or keep the prose backtick-free;
- after recording a long decision, it is cheap to read it back out of
  state.json once - which is how this was caught.

