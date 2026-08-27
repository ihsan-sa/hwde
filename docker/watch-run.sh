#!/usr/bin/env bash
# watch-run.sh <ccbox-name> <board> [interval-sec=3600] - HOST side. Polls an unattended ai-ee run in a ccbox
# container and posts progress to the owner (cc-notify -> Slack #<repo> + ntfy): hourly digest + one final report.
set -uo pipefail
NAME="${1:?ccbox name}"; BOARD="${2:?board}"; EVERY="${3:-3600}"; C="ccbox-$NAME"; WS="$HOME/dev/$NAME/boards/$BOARD"
last=""
digest(){
  phase=$(jq -r '.phase // "-"' "$WS/state.json" 2>/dev/null); gates=$(jq -r '[.gates // {} | to_entries[] | "\(.key)=\(.value.status // .value.last.status // "?")"] | join(" ")' "$WS/state.json" 2>/dev/null)
  st=$(cat "$WS/log/run/STATUS" 2>/dev/null || echo "-"); it=$(grep -c ' end rc=' "$WS/log/run/loop.log" 2>/dev/null || echo 0)
  running=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null || echo no)
  cost=$(grep -o 'total=\$[0-9.]*' "$WS/log/run/loop.log" 2>/dev/null | tail -1)
  jt=$(tail -n 12 "$WS/log/run-journal.md" 2>/dev/null | sed 's/^/    /')
  printf 'board %s: phase %s | loop %s, %s iteration(s) done, %s | container running=%s\ngates: %s\njournal tail:\n%s\n' "$BOARD" "$phase" "$st" "$it" "${cost:-cost n/a}" "$running" "${gates:--}" "$jt"
}
while :; do
  d=$(digest); st=$(cat "$WS/log/run/STATUS" 2>/dev/null || echo RUNNING); running=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null || echo false)
  if [ "$st" != RUNNING ] || [ "$running" != true ]; then
    cc-notify -p high -t "ai-ee run $BOARD: $st" "$d"; exit 0
  fi
  [ "$d" != "$last" ] && cc-notify -t "ai-ee run $BOARD progress" "$d"; last="$d"
  sleep "$EVERY"
done
