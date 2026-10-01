#!/usr/bin/env bash
# Render a board's 3D picture into docs/showcase/renders/<name>.png.
#
# sync.py calls this only for a board whose workspace has no render of its
# own (most boards have one in reports/, which sync.py finishes instead).
#
# Why the temp copy: the (model "...") paths inside the .kicad_pcb files are
# absolute paths from the machines the boards were designed on
# (C:/dev/ai-ee3/..., /workspace/boards/..., or repo-relative). The real model
# files are in the boards repo at <board>/lib/aiee.3dshapes/. So we copy each
# board file, rewrite every prefix that ends in "boards/" to the boards root,
# and render the copy. The board files themselves are never touched.
#
# Needs: KiCad 10's kicad-cli on the host (HWDE_KICAD_CLI, else
# ~/.local/kicad10/bin/kicad-cli, else kicad-cli on PATH; no Docker) and
# python3 with Pillow. A part whose model is in KiCad's stock 3D library
# (${KICAD10_3DMODEL_DIR}) is drawn only when that library is installed.
# kicad-cli loads its 3D model plugins only from /usr/lib/<arch>/kicad/plugins/3d,
# so the user-space KiCad under ~/.local/kicad10 draws the bare board with no
# parts on it (2026-10-01): use a system KiCad, or the board's own render.
#
# Usage:
#   ./render_boards.sh                       # every board, in parallel
#   ./render_boards.sh g0-sense PCB-0020-A_esp32c3-node ...
#                                            # only these (name or folder)
#   JOBS=2 ./render_boards.sh                # cap the parallelism (default 3)
#   HWDE_BOARDS_ROOT=... ./render_boards.sh  # boards root, default ~/dev/boards
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOARDS="$(cd "${HWDE_BOARDS_ROOT:-$HOME/dev/boards}" && pwd)"
OUT="$HERE/renders"
JOBS="${JOBS:-3}"
CLI="${HWDE_KICAD_CLI:-}"
[ -n "$CLI" ] || { [ -x "$HOME/.local/kicad10/bin/kicad-cli" ] && CLI="$HOME/.local/kicad10/bin/kicad-cli"; } || true
[ -n "$CLI" ] || CLI="$(command -v kicad-cli || true)"
[ -n "$CLI" ] || { echo "FAIL: no kicad-cli (set HWDE_KICAD_CLI)"; exit 2; }
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

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

render_one() {   # folder  outname  side  rotate  zoom  pan
  local dir="$1" name="$2" side="$3" rot="$4" zoom="$5" pan="$6"
  local pcb="$BOARDS/$dir/kicad/$dir.kicad_pcb"
  [ -f "$pcb" ] || { echo "skip $dir: no .kicad_pcb"; return 0; }

  local tmp="$WORK/$name"
  mkdir -p "$tmp"
  # Point every model path of the form .../boards/<old folder>/ at this
  # board's folder: boards were renamed to PCB-NNNN-R_<name> after their
  # files were written. ${KICAD10_3DMODEL_DIR}/... has no "boards/" in it and
  # is left alone.
  sed -E "s#\\(model \"[^\"]*boards/[^/\"]+/#(model \"$BOARDS/$dir/#" "$pcb" > "$tmp/$dir.kicad_pcb"

  local viewargs=()
  if [ "$rot" = "flat" ]; then
    viewargs=()                                   # straight down, orthogonal
  else
    viewargs=(--perspective --rotate "$rot")
  fi
  [ -n "$pan" ] && viewargs+=(--pan "$pan")

  echo "render $name (side=$side rotate=$rot zoom=$zoom)"
  "$CLI" pcb render --side "$side" \
      --zoom "$zoom" --quality high --background transparent \
      -w 2400 -h 1700 "${viewargs[@]}" \
      -o "$tmp/raw.png" "$tmp/$dir.kicad_pcb" >"$tmp/log" 2>&1 \
    || { echo "FAILED $name"; tail -5 "$tmp/log"; return 1; }

  local finishargs=()
  # Straight down, the drop shadow lands beside the board as grey blocks.
  [ "$rot" = "flat" ] && finishargs=(--opaque-only)
  python3 "$HERE/_finish.py" "${finishargs[@]}" "$tmp/raw.png" "$OUT/$name.png"
}

mkdir -p "$OUT"

# A board is named by its folder (PCB-0015-A_g0-sense) or its name (g0-sense);
# the picture is always renders/<name>.png.
folder() {
  local d
  for d in "$BOARDS/$1" "$BOARDS"/PCB-*_"$1"; do
    [ -f "$d/kicad/$(basename "$d").kicad_pcb" ] && { basename "$d"; return; }
  done
  echo "skip $1: no such board in $BOARDS" >&2
}

all=()
for d in "$BOARDS"/*/; do
  b="$(basename "$d")"
  [ -f "$d/kicad/$b.kicad_pcb" ] && all+=("$b")
done

if [ $# -gt 0 ]; then want=("$@"); else want=("${all[@]}"); fi

pids=()
for w in "${want[@]}"; do
  dir="$(folder "$w")"; [ -n "$dir" ] || continue
  b="${dir#PCB-*_}"
  IFS='|' read -r rot zoom pan <<<"$(camera "$b")"
  render_one "$dir" "$b" top "$rot" "$zoom" "$pan" &
  pids+=($!)
  for v in "${EXTRA_VIEWS[@]}"; do
    IFS=':' read -r vb vsuf vside vrot vzoom <<<"$v"
    [ "$vb" = "$b" ] || continue
    render_one "$dir" "$b-$vsuf" "$vside" "$vrot" "$vzoom" "" &
    pids+=($!)
  done
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
done

fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
echo "done; renders in $OUT"
exit $fail
