#!/usr/bin/env bash
# Build the flow charts and the showcase PDF.
#
#   ./build_docs.sh            diagrams + PDF
#   ./build_docs.sh diagrams   diagrams only
#   ./build_docs.sh pdf        PDF only
#
# The flow charts are standalone TikZ built with pdflatex, and need pdftoppm for
# the PNGs the README shows. The PDF is set in the pdf-material-builder house
# style and built with that skill's scripts/build.sh (lualatex, three passes);
# point PMB_DIR at the skill if it is not in ~/.claude/skills. The renders come
# from ./render_boards.sh, which is slow and separate on purpose.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTS=(pipeline roles gate lessons)

build_diagrams() {
  cd "$HERE/diagrams"
  for f in "${CHARTS[@]}"; do
    pdflatex -interaction=nonstopmode -halt-on-error "$f.tex" >/dev/null 2>&1 || {
      echo "FAIL $f"; grep -m5 -A3 '^!' "$f.log" || true; return 1; }
    pdftoppm -r 200 -png -singlefile "$f.pdf" "$f"
    echo "ok $f"
  done
  rm -f ./*.aux ./*.log
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
