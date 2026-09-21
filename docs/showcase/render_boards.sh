#!/usr/bin/env bash
# Remake the hero 3D renders in docs/showcase/renders/.
#
# Why the temp copy: the (model "...") paths inside the .kicad_pcb files are
# absolute paths from the machines the boards were designed on
# (C:/dev/ai-ee3/..., /workspace/boards/..., or repo-relative). The real model
# files are in the repo at boards/<board>/lib/aiee.3dshapes/. So we copy each
# board file, rewrite every prefix that ends in "boards/" to the path where the
# repo's boards dir is mounted in the container, and render the copy. The board
# files themselves are never touched.
#
# Needs: docker (image kicad/kicad:10.0.5-full, which carries KiCad's stock 3D
# model library that some boards reference) and python3 with Pillow.
#
# Usage:
#   ./render_boards.sh                # every board, in parallel
#   ./render_boards.sh g0-sense ...   # only these
#   JOBS=2 ./render_boards.sh         # cap the parallelism (default 3)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
BOARDS="$REPO/boards"
OUT="$HERE/renders"
IMAGE="kicad/kicad:10.0.5-full"
JOBS="${JOBS:-3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
chmod 777 "$WORK"          # the container user is not us and has to write here

# Per-board camera. Fields: rotate | zoom | pan. Empty pan means none.
# Tuned by eye; elongated boards want a shallower tilt so they still fill the
# frame, and dense boards want a little less zoom so nothing clips.
camera() {
  case "$1" in
    lumina-par)     echo "-30,0,22|0.70|" ;;
    lumina-carrier) echo "-32,0,20|0.72|" ;;
    rf-de-20m)      echo "-30,0,18|0.70|" ;;
    rf-term-150w)   echo "-38,0,25|0.75|" ;;
    *)              echo "-35,0,20|0.75|" ;;
  esac
}

# Extra views worth a second render: "<board>:<suffix>:<side>:<rotate>:<zoom>".
# Every board here is single-sided assembly, so a bottom view is bare copper -
# worth one render on the densest board to show the routing, not on all of them.
# rotate "flat" means straight down, orthogonal: no --rotate, no --perspective.
# (--rotate "-90,0,0" is edge-on, not top-down.)
EXTRA_VIEWS=(
  "lumina-par:flat:top:flat:0.95"
  "lumina-carrier:bottom:bottom:-35,0,20:0.75"
)

render_one() {   # board  outname  side  rotate  zoom  pan
  local board="$1" name="$2" side="$3" rot="$4" zoom="$5" pan="$6"
  local pcb="$BOARDS/$board/kicad/$board.kicad_pcb"
  [ -f "$pcb" ] || { echo "skip $board: no .kicad_pcb"; return 0; }

  local tmp="$WORK/$name"
  mkdir -p "$tmp"; chmod 777 "$tmp"
  # Rewrite every model prefix ending in boards/ to the read-only mount.
  # ${KICAD10_3DMODEL_DIR}/... has no "boards/" in it and is left alone.
  sed -E 's#\(model "[^"]*boards/#(model "/workspace/boards/#' "$pcb" > "$tmp/$board.kicad_pcb"
  chmod 666 "$tmp/$board.kicad_pcb"

  local viewargs=()
  if [ "$rot" = "flat" ]; then
    viewargs=()                                   # straight down, orthogonal
  else
    viewargs=(--perspective --rotate "$rot")
  fi
  [ -n "$pan" ] && viewargs+=(--pan "$pan")

  echo "render $name (side=$side rotate=$rot zoom=$zoom)"
  docker run --rm --entrypoint "" \
    -v "$BOARDS:/workspace/boards:ro" -v "$tmp:/out" "$IMAGE" \
    kicad-cli pcb render --side "$side" \
      --zoom "$zoom" --quality high --background transparent \
      -w 2400 -h 1700 "${viewargs[@]}" \
      -o "/out/raw.png" "/out/$board.kicad_pcb" >"$tmp/log" 2>&1 \
    || { echo "FAILED $name"; tail -5 "$tmp/log"; return 1; }

  local finishargs=()
  # Straight down, the drop shadow lands beside the board as grey blocks.
  [ "$rot" = "flat" ] && finishargs=(--opaque-only)
  python3 "$HERE/_finish.py" "${finishargs[@]}" "$tmp/raw.png" "$OUT/$name.png"
}

mkdir -p "$OUT"

all=()
for d in "$BOARDS"/*/; do
  b="$(basename "$d")"
  [ -f "$d/kicad/$b.kicad_pcb" ] && all+=("$b")
done

if [ $# -gt 0 ]; then want=("$@"); else want=("${all[@]}"); fi

pids=()
for b in "${want[@]}"; do
  IFS='|' read -r rot zoom pan <<<"$(camera "$b")"
  render_one "$b" "$b" top "$rot" "$zoom" "$pan" &
  pids+=($!)
  for v in "${EXTRA_VIEWS[@]}"; do
    IFS=':' read -r vb vsuf vside vrot vzoom <<<"$v"
    [ "$vb" = "$b" ] || continue
    render_one "$b" "$b-$vsuf" "$vside" "$vrot" "$vzoom" "" &
    pids+=($!)
  done
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
done

fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
echo "done; renders in $OUT"
exit $fail
