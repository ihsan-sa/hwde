#!/usr/bin/env bash
# Build the flow charts and the showcase PDF.
#
#   ./build_docs.sh            diagrams + PDF
#   ./build_docs.sh diagrams   diagrams only
#
# Needs pdflatex and pdftoppm. The renders come from ./render_boards.sh, which
# is slow and separate on purpose.
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
  cd "$HERE"
  for _ in 1 2; do
    pdflatex -interaction=nonstopmode hwde-showcase.tex >/dev/null 2>&1 || {
      echo "FAIL hwde-showcase"; grep -m8 -A3 '^!' hwde-showcase.log || true; return 1; }
  done
  echo "over-/underfull boxes: $(grep -c 'Overfull\|Underfull' hwde-showcase.log || true)"
  echo "ok hwde-showcase.pdf ($(du -h hwde-showcase.pdf | cut -f1))"
  rm -f hwde-showcase.aux hwde-showcase.out hwde-showcase.toc hwde-showcase.log
}

case "${1:-all}" in
  diagrams) build_diagrams ;;
  pdf)      build_pdf ;;
  all)      build_diagrams && build_pdf ;;
  *) echo "usage: $0 [diagrams|pdf|all]"; exit 2 ;;
esac
