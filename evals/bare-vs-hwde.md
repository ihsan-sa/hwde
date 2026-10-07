# Bare Claude Code vs /hwde: LDO, stereo amp, GaN RF inverter

Each run got the same brief in the e2e sandbox (`evals/e2e_run.py`), with
claude-opus-5-5 at medium effort. The bare arm has no skill. "bare" runs
predate the tool-parity change, so they had no Agent tool and no hint about
the egress allowlist; "bare+tools" runs have both, so they get the hwde arm's
tools minus the Skill. The score is the electrical composite from
`evals/e2e_electrical.py --rescore` (0-100, checked against a hidden known
answer). Run records: `bare-vs-hwde.jsonl` (LDO) and `bare-amp.jsonl` (amp, RF).

| Brief | Run | Score | Cost | Wall | Main faults |
|---|---|---|---|---|---|
| USB-C LDO | bare s1 | 94.19 | $2.25 | 12 min | none electrical |
| USB-C LDO | bare s2 | 97.67 | $2.49 | 10 min | none electrical |
| USB-C LDO | hwde s1 | 86.34 | $34.96 | 71 min | 1 DRC error (zones_intersect) |
| USB-C LDO | hwde s2 | 97.42 | $30.14 | 61 min | Cout 6.7 mm from the LDO |
| Stereo amp | bare s1 | 47.50 | $8.05 | 28 min | no thermal pad vias (fatal); +12V and OUTPR traces too thin; PVCC caps 3.1-3.8 mm out |
| Stereo amp | bare+tools s1 | 63.5 | unknown | unknown | no thermal pad vias (fatal); +12V and output traces too thin. Session died after the board was done; scored from the work dir |
| Stereo amp | bare+tools s2 | 50.0 | $12.33 | 51 min | no thermal pad vias (fatal); +12V at 0.30 mm for 2 A; PVCC, GVDD and bootstrap caps 3.4-4.4 mm out |
| Stereo amp | hwde PCB-0017-A | 89.40 | - | - | output traces 0.30 mm for 1.5 A; PVCC and bootstrap caps 3.1-4.9 mm out |
| GaN RF inverter | bare+tools s1 | no known answer yet | $14.36 | 60 min | see below |

The amp's hwde row is the board hwde built for PCB-0017-A outside the eval,
scored against the same known answer, so it has no eval cost or wall time.

**RF inverter (PCB-0023-A's brief).** The bare+tools run finished a 152x90 mm
4-layer board with 89 parts, clean on DRC and ERC. It used EPC2019 where the
brief suggested EPC2307 or 2304, and two single-channel NSi8210 isolators where the brief
asked for one part carrying both PWM channels. hwde's PCB-0023-A is 100x80 mm
with 159 parts: EPC2307 with LMG1020 drivers and dual NSi8220 isolators. There
is no known answer for this brief yet, so neither board has an electrical score.

**Conclusion:** on the simple LDO, bare matches hwde at about 1/14 the cost ($4.74 vs $65.10 for two runs each);
on the amp, hwde leads clearly.
