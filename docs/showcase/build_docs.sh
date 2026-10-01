#!/usr/bin/env bash
# Build the figures and the showcase PDF.
#
#   ./build_docs.sh            figures + PDF
#   ./build_docs.sh diagrams   figures only
#   ./build_docs.sh pdf        PDF only
#
# The figures are diagram-maker specs (diagrams/*.json), exported by that
# skill's scripts/export.sh to the PDF this document places and the PNG the
# README shows; point DM_DIR at the skill if it is not in ~/.claude/skills.
# The PDF is set in the pdf-material-builder house style and built with that
# skill's scripts/build.sh (lualatex, three passes); point PMB_DIR at the
# skill if it is not in ~/.claude/skills. The board renders are made
# separately, as README.md in this folder says.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTS=(pipeline gate after)

build_diagrams() {
  local dm="${DM_DIR:-$HOME/.claude/skills/diagram-maker}"
  local fonts="${PMB_DIR:-$HOME/.claude/skills/pdf-material-builder}/assets/fonts"
  [ -f "$dm/scripts/export.sh" ] || {
    echo "FAIL diagrams: no diagram-maker at $dm (set DM_DIR)"; return 1; }
  cd "$HERE/diagrams"
  for f in "${CHARTS[@]}"; do
    bash "$dm/scripts/export.sh" "$f.json" "$fonts" >/dev/null || { echo "FAIL $f"; return 1; }
    echo "ok $f"
  done
}

build_pdf() {
  local pmb="${PMB_DIR:-$HOME/.claude/skills/pdf-material-builder}"
  [ -x "$pmb/scripts/build.sh" ] || {
    echo "FAIL hwde-showcase: no pdf-material-builder at $pmb (set PMB_DIR)"; return 1; }
  "$pmb/scripts/build.sh" "$HERE/hwde-showcase.tex"
  echo "ok hwde-showcase.pdf ($(du -h "$HERE/hwde-showcase.pdf" | cut -f1))"
}

case "${1:-all}" in
  diagrams) build_diagrams ;;
  pdf)      build_pdf ;;
  all)      build_diagrams && build_pdf ;;
  *) echo "usage: $0 [diagrams|pdf|all]"; exit 2 ;;
esac
