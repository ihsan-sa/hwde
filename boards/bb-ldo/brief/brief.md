# bb-ldo brief (owner, verbatim)

learning block-basics: a linear regulator. Input 5 V DC on a screw terminal;
output 3.3 V at up to 500 mA on a screw terminal. Must hold regulation at full
load with no airflow. Workspace boards/bb-ldo.

## Resolved mode (state.py mode, P0)

- token: `learning block-basics:`
- target: block-basics
- scope tier: block-only (excludes protection, filtering, indicators,
  test-points, config, second-rail, mechanical, enclosure-fit)
- binding: canonical -> geometry is an OUTPUT (board_init --outline auto,
  place, then `board_edit --outline fit`)
- stage under study: none
