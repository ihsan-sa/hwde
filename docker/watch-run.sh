#!/usr/bin/env bash
# watch-run.sh <ccbox-name> <board> [poll-sec=300] - HOST side. Watches an unattended ai-ee run in a ccbox container and
# posts to the owner (cc-notify -> Slack #<repo> + ntfy) ONLY at milestones: a phase change, a gate result change, the
# loop waiting out a usage limit, or the loop ending. Messages are short (owner rule 2026-08-27: <= 6 lines, shallow
# first); the detail lives in boards/<board>/log/run-journal.md, which every post links.
set -uo pipefail
case ":$PATH:" in *":$HOME/bin:"*) ;; *) PATH="$HOME/bin:$PATH";; esac; export PATH   # systemd --user units lack ~/bin (cc-notify)
NAME="${1:?ccbox name}"; BOARD="${2:?board}"; EVERY="${3:-300}"; C="ccbox-$NAME"; WS="$HOME/dev/$NAME/boards/$BOARD"
J="$WS/log/run-journal.md"; LL="$WS/log/run/loop.log"
snap(){   # the milestone state, one line
  phase=$(jq -r '.phase // "-"' "$WS/state.json" 2>/dev/null)
  gates=$(jq -r '[.gates // {} | to_entries[] | "\(.key)=\(.value.status // .value.last.status // "?")"] | join(" ")' "$WS/state.json" 2>/dev/null)
  st=$(cat "$WS/log/run/STATUS" 2>/dev/null || echo "-")
  lim=$(tail -n 3 "$LL" 2>/dev/null | grep -o 'LIMIT: [a-z]*' | tail -1)
  printf '%s|%s|%s|%s' "$phase" "${gates:--}" "$st" "${lim:-}"
}
post(){   # <= 6 short lines, detail behind one link
  local title="$1" it cost lim
  it=$(grep -c ' end rc=' "$LL" 2>/dev/null); it=${it:-0}; cost=$(grep -o 'total=\$[0-9.]*' "$LL" 2>/dev/null | tail -1)
  lim=$(tail -n 3 "$LL" 2>/dev/null | grep -o 'LIMIT: .*' | tail -1 | cut -c1-80)
  cc-notify ${2:+-p "$2"} -t "$title" "$(printf -- '- phase %s | loop %s, %s iteration(s), %s\n- gates: %s\n%s- detail: %s' \
      "$phase" "$st" "$it" "${cost:-cost n/a}" "${gates:--}" "${lim:+- $lim
}" "$J")"
}
last=$(snap); IFS='|' read -r phase gates st lim <<<"$last"
while :; do
  cur=$(snap); IFS='|' read -r phase gates st lim <<<"$cur"; running=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null || echo false)
  if [ "$st" != RUNNING ] && [ "$st" != "-" ] || [ "$running" != true ]; then post "ai-ee run $BOARD: ${st}${running:+ (container $running)}" high; exit 0; fi
  [ "$cur" != "$last" ] && post "ai-ee run $BOARD: $phase" ; last="$cur"
  sleep "$EVERY"
done
