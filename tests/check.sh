#!/usr/bin/env bash
# The full pytest suite on a Linux host, detachable with `cc-green start -- tests/check.sh`
# (cc-green only detaches a committed tests/check*.sh). Same as `make check` minus check_env.
# Sources the no-container toolchain (~/.local/kicad10/hwde-env.sh) when present, and gives
# the SWIG workers a private Xvfb display when none is set (CLAUDE.md, Linux host section).
# cc-land runs it as a landing gate from a checkout with no .venv, so it falls back to the
# host venv ~/.local/hwde-venv.
set -u
cd "$(dirname "$0")/.."
[ -f "$HOME/.local/kicad10/hwde-env.sh" ] && . "$HOME/.local/kicad10/hwde-env.sh"
xpid=""
if [ -z "${DISPLAY:-}" ] && command -v Xvfb >/dev/null; then
  n=$(( 200 + $$ % 700 ))
  Xvfb ":$n" -nolisten tcp >/dev/null 2>&1 &
  xpid=$!
  export DISPLAY=":$n"
  sleep 1
fi
py=.venv/bin/python
[ -x "$py" ] || py="$HOME/.local/hwde-venv/bin/python"
nice "$py" -m pytest -q -rfE "$@"
rc=$?
[ -n "$xpid" ] && kill "$xpid" 2>/dev/null
exit $rc
