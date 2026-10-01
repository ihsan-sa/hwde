#!/usr/bin/env python3
"""Bring the hwde showcase up to date with the boards repo, in one command.

    sync.py [--boards-root DIR] [--no-file] [--note TEXT]

1. gallery.py --pictures: makes the picture of any new board, then rewrites
   gallery.tex and the gallery part of the top-level README.md.
2. When anything the PDF is built from changed since the last filing (the
   hash of hwde-showcase.tex, gallery.tex and every picture and figure, kept in
   filed.json), builds the PDF with build_docs.sh pdf and files it in the
   library: cc-docs file --project 003 --title 'hwde showcase' --source
   SHOWCASE_SOURCE (default ~/dev/ai-ee/docs/showcase/hwde-showcase.tex, the
   name the document is filed under wherever this runs). Nothing changed
   means nothing is built and nothing filed. cc-docs files nothing either
   when the content matches the current revision.
3. Commits nothing. The README, gallery.tex, the PDF, any new picture and
   filed.json are left in the working tree, ready to commit.

--no-file builds but does not file (and leaves filed.json alone).

JSON to stdout; exit 0 done, 1 a board has no picture or the build or the
filing failed, 2 error (no boards repo, bad gallery.yaml).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gallery  # noqa: E402

MAIN = HERE / "hwde-showcase.tex"
FILED = HERE / "filed.json"
SOURCE = Path(os.environ.get(
    "SHOWCASE_SOURCE", Path.home() / "dev/ai-ee/docs/showcase/hwde-showcase.tex"))


def inputs_hash() -> str:
    """One hash over everything the PDF is built from."""
    h = hashlib.sha256()
    files = [MAIN, gallery.TEX_OUT]
    files += sorted(gallery.RENDERS.glob("*.png")) + sorted(gallery.RENDERS.glob("*.jpg"))
    files += sorted((HERE / "diagrams").glob("*.pdf"))
    for f in files:
        h.update(f.relative_to(HERE).as_posix().encode() + b"\0")
        h.update(f.read_bytes())
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--boards-root", type=Path, default=None)
    ap.add_argument("--no-file", action="store_true", help="build, but do not file")
    ap.add_argument("--note", default=None,
                    help="what changed, for the library (default: names the boards added)")
    a = ap.parse_args(argv)
    root = (a.boards_root or gallery.env.boards_root()).expanduser()
    out: dict = {"boards_root": str(root)}
    if not (root / "register.yaml").is_file():
        out["error"] = f"no register.yaml under {root}"
        print(json.dumps(out))
        return 2
    try:
        res = gallery.generate(root, write=True, pictures=True)
    except (OSError, ValueError, KeyError, gallery.yaml.YAMLError) as e:
        out["error"] = f"gallery: {type(e).__name__}: {e}"
        print(json.dumps(out))
        return 2
    out["gallery"] = {k: res[k] for k in ("count", "added", "missing_pictures",
                                           "tex_changed", "readme_changed")}
    out["pictures_made"] = [p["board"] for p in res["pictures_made"] if p["ok"]]
    bad = res["missing_pictures"] + [p["board"] for p in res["pictures_made"] if not p["ok"]]
    if bad:
        out["error"] = f"no picture for {', '.join(sorted(set(bad)))}"
        print(json.dumps(out, indent=1))
        return 1

    digest = inputs_hash()
    last = json.loads(FILED.read_text()) if FILED.is_file() else {}
    pdf = HERE / "hwde-showcase.pdf"
    if last.get("inputs") == digest and pdf.is_file():
        out.update(built=False, filed=None, reason="nothing the PDF is built from changed")
        print(json.dumps(out, indent=1))
        return 0

    b = subprocess.run(["bash", str(HERE / "build_docs.sh"), "pdf"],
                       capture_output=True, text=True)
    out["built"] = b.returncode == 0
    if b.returncode:
        out["error"] = "build failed: " + (b.stdout + b.stderr).strip()[-600:]
        print(json.dumps(out, indent=1))
        return 1
    if a.no_file:
        out["filed"] = None
        print(json.dumps(out, indent=1))
        return 0

    note = a.note or (
        f"The board gallery now shows {', '.join(res['added'])}, regenerated from "
        f"the boards repo." if res["added"] else
        "The board gallery was regenerated from the boards repo.")
    f = subprocess.run(["cc-docs", "file", str(pdf), "--project", "003",
                        "--title", "hwde showcase", "--source", str(SOURCE),
                        "--latex", str(MAIN), "--note", note],
                       capture_output=True, text=True)
    text = (f.stdout + f.stderr).strip()
    out["cc_docs"] = text[-600:]
    if f.returncode:
        out["error"] = "cc-docs file failed"
        print(json.dumps(out, indent=1))
        return 1
    m = re.search(r"\b(\d{3}-\d{4}-[A-Z]+)\b", text)
    out["filed"] = m.group(1) if m else None
    FILED.write_text(json.dumps({"inputs": digest, "number": out["filed"]},
                                indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
