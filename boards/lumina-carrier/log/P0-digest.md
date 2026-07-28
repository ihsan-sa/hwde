# P0 Intake digest - LUMINA carrier (LUM-CAR-A)

- Inputs: 3 briefs (`00` system context v2.0, `01` carrier brief, `05` closed decisions).
  `05` is binding and supersedes `00` section 6 for D-01/D-02/D-03.
- Artifact: `architecture/requirements.md` (requirements-analyst, spawned as subagent).
- Function: universal PoE carrier. One Ethernet cable in; fixture-agnostic expansion
  interface out. PD front end + 48->12->3.3 V + ESP32-S3 + W5500 + RJ45 magjack.
  No LED drivers, no light-engine storage, no audio, no wireless control path.
- Closed on entry: D-01 (at-sized power stage, af classification, resistor-only upgrade),
  D-02 (connector carries 48 V raw + 12 V + 3.3 V), D-03 (no UV board).
  D-04 (strobe colour) is NOT this board's - carrier exposes the full 8-PWM ceiling so
  either answer works.
- Hard ceiling found in the brief and carried forward: ESP32-S3 LEDC = 8 channels,
  4 timers, low-speed only, 14-bit max. Default 13-bit @ 9.77 kHz. The legacy
  "16-bit @ 1.2 kHz" is not achievable and is recorded as dead.
- 16 open questions raised. Two are SAFETY-flagged and will not be guessed past H1:
  Q5 converter isolation + enclosure material, Q6 worst-case per-rail connector current.
- Orchestrator is a background agent with no human channel. Decision D-P0-PROVISIONAL:
  proceed P1/P2 on the analyst's stated defaults, marked PROVISIONAL throughout;
  H1 is the single blocking confirmation point. If the human overrides Q5 or Q6,
  P2 architecture must be revised before P3.
- Blocking for P5 (not yet reached): MECH-02 board outline in mm is permanent at
  `board_init.py --outline WxH`. Must be closed with the human at H1.
