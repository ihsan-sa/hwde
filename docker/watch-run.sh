#!/usr/bin/env bash
# watch-run.sh <ccbox-name> <board> [poll-sec=600] - HOST side. Polls an unattended ai-ee run in a ccbox container and
# posts to the owner (cc-notify -> Slack #<repo> + ntfy) ONLY at milestones: phase / gate / STATUS / container /
# usage-limit changes, plus one final report. Posts are short and link the journal (owner rule 2026-08-27: <= 6 bullets,
# long reports in a file). The last milestone key is persisted, so a watcher restart does not re-post an unchanged state.
set -uo pipefail
case ":$PATH:" in *":$HOME/bin:"*) ;; *) PATH="$HOME/bin:$PATH";; esac; export PATH   # systemd --user units lack ~/bin (cc-notify)
NAME="${1:?ccbox name}"; BOARD="${2:?board}"; EVERY="${3:-600}"; C="ccbox-$NAME"; WS="$HOME/dev/$NAME/boards/$BOARD"
LASTF="$HOME/.cc/state/$NAME/watch-$BOARD.last"; mkdir -p "$(dirname "$LASTF")"
key(){ # milestone key; also sets phase/gates/st/running/limstate for digest()
  phase=$(jq -r '.phase // "-"' "$WS/state.json" 2>/dev/null); gates=$(jq -r '[.gates // {} | to_entries[] | "\(.key)=\(.value.status // .value.last.status // "?")"] | join(" ")' "$WS/state.json" 2>/dev/null)
  st=$(cat "$WS/log/run/STATUS" 2>/dev/null || echo "-"); running=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null || echo no)
  limstate=""; tail -n 3 "$WS/log/run/loop.log" 2>/dev/null | grep -qE 'LIMIT: (usage limit hit|still limited)' && limstate="limit-wait"
  printf '%s|%s|%s|%s|%s' "$phase" "${gates:--}" "$st" "$running" "$limstate"
}
digest(){ # <= 4 short bullets; the journal is linked, not pasted
  it=$(grep -c ' end rc=' "$WS/log/run/loop.log" 2>/dev/null); it=${it:-0}; cost=$(grep -o 'total=\$[0-9.]*' "$WS/log/run/loop.log" 2>/dev/null | tail -1)
  limline=$(tail -n 3 "$WS/log/run/loop.log" 2>/dev/null | grep -o 'LIMIT: .*' | tail -1)
  printf '• %s: phase %s, gates %s\n• loop %s, %s iteration(s), %s, container %s\n%s• journal: %s\n' \
    "$BOARD" "$phase" "${gates:--}" "$st" "$it" "${cost:-cost n/a}" "$running" "${limline:+• $limline
}" "$WS/log/run-journal.md"
}
last=$(cat "$LASTF" 2>/dev/null || true)
while :; do
  k=$(key); d=$(digest)
  if [ "$st" != RUNNING ] || [ "$running" != true ]; then cc-notify -p high -t "ai-ee run $BOARD: $st" "$d"; printf '%s' "$k" > "$LASTF"; exit 0; fi
  if [ "$k" != "$last" ]; then cc-notify -t "ai-ee run $BOARD: $phase${limstate:+ (usage-limit wait)}" "$d"; printf '%s' "$k" > "$LASTF"; last="$k"; fi
  sleep "$EVERY"
done
