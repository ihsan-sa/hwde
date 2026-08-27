#!/usr/bin/env bash
# watch-run.sh <ccbox-name> <board> [poll-sec=600] - HOST side. Polls an unattended ai-ee run in a ccbox container and
# posts to the owner (cc-notify -> Slack #<repo> + ntfy) ONLY at milestones: a phase change, a gate newly PASSING, a
# usage-limit wait starting, plus one final report (gate fails and other churn stay silent; the title names the milestone). Posts are short and link the journal (owner rule 2026-08-27: <= 6 bullets,
# long reports in a file). The last milestone key is persisted, so a watcher restart does not re-post an unchanged state.
set -uo pipefail
case ":$PATH:" in *":$HOME/bin:"*) ;; *) PATH="$HOME/bin:$PATH";; esac; export PATH   # systemd --user units lack ~/bin (cc-notify)
NAME="${1:?ccbox name}"; BOARD="${2:?board}"; EVERY="${3:-600}"; C="ccbox-$NAME"; WS="$HOME/dev/$NAME/boards/$BOARD"
LASTF="$HOME/.cc/state/$NAME/watch-$BOARD.last"; mkdir -p "$(dirname "$LASTF")"
key(){ # sets k (the milestone key) and phase/gates/st/running/limstate for digest(); called directly, never in $(...)
  phase=$(jq -r '.phase // "-"' "$WS/state.json" 2>/dev/null); gates=$(jq -r '[.gates // {} | to_entries[] | "\(.key)=\(.value.status // .value.last.status // "?")"] | join(" ")' "$WS/state.json" 2>/dev/null)
  st=$(cat "$WS/log/run/STATUS" 2>/dev/null || echo "-"); running=$(docker inspect -f '{{.State.Running}}' "$C" 2>/dev/null || echo no)
  limstate=""; tail -n 3 "$WS/log/run/loop.log" 2>/dev/null | grep -qE 'LIMIT: (usage limit hit|still limited)' && limstate="limit-wait"
  k="$phase|${gates:--}|$st|$running|$limstate"
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
  key; d=$(digest); IFS='|' read -r pphase pgates pst prun plim <<<"$last"
  if [ "$st" != RUNNING ] || [ "$running" != true ]; then cc-notify -p high -t "ai-ee run $BOARD: $st" "$d"; printf '%s' "$k" > "$LASTF"; exit 0; fi
  ev=""   # milestones only: a phase change, a gate newly PASSING, a usage-limit wait starting. Gate fails, limit clearing and other churn stay silent.
  [ "$phase" != "$pphase" ] && ev="phase $phase"
  for g in $gates; do case "$g" in *=pass) grep -qw -- "$g" <<<"$pgates" || ev="${ev:+$ev, }gate ${g%=pass} PASS";; esac; done
  [ "$limstate" = limit-wait ] && [ "$plim" != limit-wait ] && ev="${ev:+$ev, }usage-limit wait"
  [ -n "$ev" ] && [ -n "$last" ] && cc-notify -t "ai-ee run $BOARD: $ev" "$d"   # an empty $last = first start: record, do not post
  [ "$k" != "$last" ] && { printf '%s' "$k" > "$LASTF"; last="$k"; }
  sleep "$EVERY"
done
