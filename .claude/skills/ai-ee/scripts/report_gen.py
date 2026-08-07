#!/usr/bin/env python
"""report_gen.py - assemble a board's design document (LaTeX -> PDF) from its run workspace.

Reads state.json (read-only) plus the run's markdown/JSON/render artifacts and
writes reports/design_doc/<board>-design-doc.tex, then compiles it to PDF with
pdflatex (two passes, staged in a system temp dir so no .aux/.log/.toc litter
ever lands in the git-tracked workspace). Sections are conditional on the run's
phase: not-yet-due sections render a one-line "Pending" stub; due-but-absent
CORE artifacts (schematic.pdf, a board render, bom_rows, order.json) are
violations, everything else absent is a warning. All external text goes
through latex_escape (total function; the final .tex is asserted pure ASCII).

Asset paths embedded in run JSON are unreliably backslashed and mixed
repo-/workspace-relative, so every asset is resolved by this script's own
ladder relative to the workspace root and emitted with forward slashes.

Exit 0 "pass"   = requested outputs produced (--tex-only: the .tex alone).
Exit 1 "violations" = degraded: compile failed, pdflatex absent (auto
                  tex-only), or core artifacts missing for the run's phase.
Exit 2 "error"  = unusable workspace / internal error (a bad AIEE_PDFLATEX
                  pin propagates here - loud, never degraded).

CLI:
  report_gen.py --workspace boards/<name> [--out report.json] [--tex-only]
                [--name NAME]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import state as statemod  # noqa: E402  (read-only: PHASES/CHECKPOINTS consts)
from lib import env  # noqa: E402

PHASE_INDEX = {p: i for i, p in enumerate(statemod.PHASES)}

# Section id -> (LaTeX heading, phase whose start makes the section due;
# None = always included). Order = document order = pipeline order.
SECTIONS = [
    ("title", "Board and Run Metadata", None),
    ("overview", "Overview", "P1"),
    ("requirements", "Requirements", "P1"),
    ("architecture", "Architecture", "P2"),
    ("schematic", "Schematic", "P4"),
    ("layout", "Layout", "P6"),
    ("verification", "Verification", "P8"),
    ("dfm_fab", "DFM and Fabrication", "P9"),
    ("run_record", "Run Record (Appendix)", None),
    ("artifact_index", "Artifact Index", None),
]
# Core artifacts: (payload label, owning section, phase that must have PASSED
# for absence to be a violation). Renders are special-cased (ladder).
CORE_SCHEMATIC = ("reports/schematic.pdf", "schematic", "P4")
CORE_RENDER = ("board render (reports render ladder)", "layout", "P6")
CORE_BOM = ("reports/bom_cpl.json bom_rows", "dfm_fab", "P9")
CORE_ORDER = ("fab/order.json", "dfm_fab", "P10")

PDF_TIMEOUT = 300  # seconds per pdflatex pass


class ReportError(RuntimeError):
    """Unusable workspace or internal invariant failure (exit 2)."""


# ---------------------------------------------------------------- escaping

# Per-character total map: every input char maps independently, so ordering
# hazards (escaping the backslashes of \textbackslash{}) cannot occur.
_CHAR_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    # OT1 text mode renders these ASCII chars as inverted punctuation / an
    # em-dash (host-verified: ">3A" printed as an upside-down question mark).
    "<": r"\textless{}", ">": r"\textgreater{}", "|": r"\textbar{}",
    # Context-sensitive after the \\ that joins tt_block/longtable lines and
    # inside \item: a line-initial "[" parses as the optional argument of \\
    # (fatal "Missing number") or as the item label, and "*" as the \\* form.
    # Brace-wrapping renders the literal char in every context.
    "[": "{[}", "]": "{]}", "*": "{*}",
    # Non-ASCII transliteration (the corpus really contains all of these).
    "\u00b1": r"\(\pm\)",          # plus-minus
    "\u03a9": r"\(\Omega\)",       # greek capital omega
    "\u2126": r"\(\Omega\)",       # ohm sign (normalizes to omega)
    "\u00b5": r"\(\mu\)",          # micro sign U+00B5
    "\u03bc": r"\(\mu\)",          # greek small mu U+03BC
    "\u2103": r"\(^{\circ}\)C",    # degree celsius single glyph U+2103
    "\u00b0": r"\(^{\circ}\)",     # degree sign
    "\u2022": r"\textbullet{}",    # bullet
    "\u0394": r"\(\Delta\)",       # greek capital delta
    "\u00d8": "dia. ",             # diameter-ish O-slash
}


def latex_escape(text) -> str:
    """Total function: any value -> LaTeX-safe pure-ASCII text.

    Backslash maps first by construction (single per-char pass over the
    ORIGINAL string). Unknown non-ASCII (CJK vendor names etc.) -> '?'.
    """
    if text is None:
        return ""
    out = []
    for ch in str(text):
        if ch in _CHAR_MAP:
            out.append(_CHAR_MAP[ch])
        elif ch == "\r":
            continue
        elif ch in ("\n", "\t") or 32 <= ord(ch) < 127:
            out.append(ch)
        elif ord(ch) < 32 or ord(ch) == 127:
            out.append(" ")
        else:
            out.append("?")
    return "".join(out)


# ---------------------------------------------------------------- markdown-lite

_INLINE_RE = re.compile(
    r"`([^`]+)`"                                   # `code`
    r"|\*\*([^*]+)\*\*"                            # **bold**
    r"|\*([^*\s][^*]*)\*"                          # *emph*
    r"|(?<!\w)_([^_\s](?:[^_]*[^_\s])?)_(?!\w)"    # _emph_ (word-bounded)
    r"|\[([^\]]+)\]\(([^)]+)\)"                    # [text](url)
)


def _inline(raw: str) -> str:
    """Inline md-lite -> LaTeX: parse markers on RAW text, escape every
    payload fragment."""
    out, pos = [], 0
    for m in _INLINE_RE.finditer(raw):
        out.append(latex_escape(raw[pos:m.start()]))
        code, bold, star, under, ltext, lurl = m.groups()
        if code is not None:
            out.append(r"\texttt{" + latex_escape(code) + "}")
        elif bold is not None:
            out.append(r"\textbf{" + latex_escape(bold) + "}")
        elif star is not None:
            out.append(r"\emph{" + latex_escape(star) + "}")
        elif under is not None:
            out.append(r"\emph{" + latex_escape(under) + "}")
        else:
            out.append(latex_escape(ltext) + r" (\texttt{" + latex_escape(lurl) + "})")
        pos = m.end()
    out.append(latex_escape(raw[pos:]))
    return "".join(out)


def tt_block(text: str) -> str:
    """Verbatim-ish block: escaped lines in a ragged \\ttfamily quote.
    Used for fenced code, md tables (never parsed) and run digests."""
    lines = [latex_escape(ln.rstrip()) for ln in text.splitlines()]
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    body = "\\\\\n".join(ln if ln.strip() else "~" for ln in lines)
    return ("\\begin{quote}\\small\\ttfamily\\raggedright\n"
            + body + "\n\\end{quote}")


_HEAD_CMD = {1: r"\subsection*", 2: r"\subsubsection*", 3: r"\paragraph*"}


def md_to_latex(text: str) -> str:
    """Markdown-lite -> LaTeX (a ceiling, not an engine): #/##/### headings,
    -/* bullets (one nesting level), inline bold/emph/code/link; md table
    lines and fenced blocks pass through as escaped tt blocks; everything
    else becomes escaped paragraphs."""
    out: list[str] = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    depth = 0          # current itemize nesting (0..2)
    para: list[str] = []

    def close_lists(to: int = 0) -> None:
        nonlocal depth
        while depth > to:
            out.append(r"\end{itemize}")
            depth -= 1

    def flush_para() -> None:
        if para:
            out.append(" ".join(para))
            out.append("")
            para.clear()

    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if stripped.startswith("```"):                      # fenced block
            flush_para()
            close_lists()
            j = i + 1
            block = []
            while j < n and not lines[j].strip().startswith("```"):
                block.append(lines[j])
                j += 1
            out.append(tt_block("\n".join(block)))
            i = j + 1
            continue
        if stripped.startswith("|"):                        # md table run
            flush_para()
            close_lists()
            j = i
            block = []
            while j < n and lines[j].strip().startswith("|"):
                block.append(lines[j])
                j += 1
            out.append(tt_block("\n".join(block)))
            i = j
            continue
        mh = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if mh and not raw.startswith(" "):                  # heading
            flush_para()
            close_lists()
            out.append(_HEAD_CMD[len(mh.group(1))] + "{" + _inline(mh.group(2)) + "}")
            i += 1
            continue
        mb = re.match(r"^(\s*)[-*]\s+(.*)$", raw)
        if mb:                                              # bullet
            flush_para()
            want = 2 if len(mb.group(1)) >= 2 else 1
            want = min(want, depth + 1)                     # never skip a level
            if want > depth:
                out.append(r"\begin{itemize}")
                depth += 1
            else:
                close_lists(want)
            out.append(r"\item " + _inline(mb.group(2)))
            i += 1
            continue
        if not stripped:                                    # blank
            flush_para()
            i += 1
            continue
        if depth and raw[:1].isspace():                     # bullet continuation
            out.append(_inline(stripped))
            i += 1
            continue
        close_lists()
        para.append(_inline(stripped))
        i += 1
    flush_para()
    close_lists()
    return "\n".join(out)


# ---------------------------------------------------------------- tex helpers

def longtable(colspec: str, header: list[str], rows: list[list[str]]) -> str:
    """Cells must already be LaTeX-ready (escaped by the caller)."""
    if not rows:
        return r"\emph{(no entries)}"
    out = ["{\\small", r"\begin{longtable}{" + colspec + "}", r"\toprule",
           " & ".join(header) + r" \\", r"\midrule", r"\endhead"]
    for r in rows:
        out.append(" & ".join(r) + r" \\")
    out += [r"\bottomrule", r"\end{longtable}", "}"]
    return "\n".join(out)


def image_block(rel_posix: str, width: str) -> str:
    """Centered non-floating image + its path as a caption line.
    The \\includegraphics argument is the RAW forward-slash path (modern
    LaTeX kernels handle underscores in file names); the caption is escaped."""
    return ("\\begin{center}\n"
            f"\\includegraphics[width={width}\\textwidth]{{{rel_posix}}}\\\\\n"
            "{\\small\\texttt{" + latex_escape(rel_posix) + "}}\n"
            "\\end{center}")


# ---------------------------------------------------------------- data access

def read_text(ws: Path, rel: str) -> str | None:
    p = ws / rel
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def read_json(ws: Path, rel: str) -> dict | None:
    t = read_text(ws, rel)
    if t is None:
        return None
    try:
        d = json.loads(t)
        return d if isinstance(d, dict) else None
    except json.JSONDecodeError:
        return None


def phase_idx(phase: str) -> int:
    return PHASE_INDEX.get(phase, 0)


def find_renders(ws: Path, board: str) -> tuple[list[str], list[str]]:
    """Main render ladder (first convention that hits wins) + extras.
    Returns workspace-relative forward-slash paths."""
    ladders = [
        ["reports/render_final/top.png", "reports/render_final/bottom.png"],
        [f"reports/renders/{board}_top.png", f"reports/renders/{board}_bottom.png",
         f"reports/renders/{board}_iso.png"],
        [f"reports/{board}_top.png", f"reports/{board}_bottom.png"],
    ]
    main: list[str] = []
    for rung in ladders:
        main = [r for r in rung if (ws / r).is_file()]
        if main:
            break
    extras = [r for r in (f"reports/render_labeled/{board}_top.png",
                          f"reports/layers/{board}_layers.png")
              if (ws / r).is_file()]
    return main, extras


# ---------------------------------------------------------------- builder

class DocBuilder:
    def __init__(self, ws: Path, st: dict, name: str):
        self.ws = ws
        self.st = st
        self.board = st.get("board") or ws.name
        self.name = name
        self.cur = phase_idx(str(st.get("phase", "P0")))
        self.sections: list[dict] = []
        self.missing: list[str] = []
        self.warnings: list[str] = []
        self.head: list[str] = []   # title block (before \tableofcontents)
        self.body: list[str] = []

    # -- bookkeeping ------------------------------------------------------
    def due(self, phase: str | None) -> bool:
        return phase is None or self.cur >= phase_idx(phase)

    def passed(self, phase: str) -> bool:
        return self.cur > phase_idx(phase)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def core(self, core: tuple[str, str, str], present: bool) -> bool:
        """Record a core artifact. Returns True if it is HARD-missing
        (due because its phase has passed, and absent)."""
        label, _section, phase = core
        if present or not self.passed(phase):
            if not present and self.due(phase):
                self.warn(f"{label} not present yet (phase {self.st.get('phase')} in progress)")
            return False
        self.missing.append(label)
        return True

    def gate_line(self, gate: str) -> str:
        g = (self.st.get("gates") or {}).get(gate)
        if not g:
            if self.due_gate(gate):
                self.warn(f"gate {gate} has no record in state.json")
            return (r"Gate \texttt{" + latex_escape(gate)
                    + r"}: \emph{not recorded}.")
        last = g.get("last") or {}
        return (r"Gate \texttt{" + latex_escape(gate) + "} (phase "
                + latex_escape(g.get("phase", "?")) + "): \\textbf{"
                + latex_escape(g.get("status", "?")) + "} after "
                + latex_escape(g.get("attempts", "?")) + " attempt(s); last "
                + latex_escape(last.get("ts", "?")) + ", failing "
                + latex_escape(last.get("failing_count", "?")) + " of "
                + latex_escape(last.get("total", "?")) + ".")

    def due_gate(self, gate: str) -> bool:
        for ph, g in statemod.GATE_ORDER:
            if g == gate:
                return self.passed(ph)
        return False

    # -- section plumbing -------------------------------------------------
    def start(self, heading: str) -> None:
        self.body.append("\\section{" + heading + "}")

    def record(self, sid: str, status: str, source: str) -> None:
        self.sections.append({"name": sid, "status": status, "source": source})

    def pending(self, sid: str, heading: str, phase: str) -> None:
        self.start(heading)
        self.body.append(r"\emph{Pending --- produced at " + phase + ".}")
        self.record(sid, "pending", f"due at {phase}")

    # -- sections ---------------------------------------------------------
    def sec_title(self) -> None:
        st = self.st
        gates = st.get("gates") or {}
        n_pass = sum(1 for g in gates.values() if g.get("status") == "pass")
        if not gates:
            overall = "no gates recorded yet"
        elif n_pass == len(gates):
            overall = f"all {len(gates)} recorded gates pass"
        else:
            bad = sorted(k for k, g in gates.items() if g.get("status") != "pass")
            overall = f"{n_pass}/{len(gates)} gates pass (not passing: {', '.join(bad)})"
        self.head.append("\\begin{center}")
        self.head.append("{\\LARGE\\bfseries " + latex_escape(self.name)
                         + " --- Design Document}\\\\[6pt]")
        self.head.append("{\\large ai-ee v1 pipeline}\\\\[2pt]")
        self.head.append("generated " + latex_escape(time.strftime("%Y-%m-%d %H:%M:%S"))
                         + "\n\\end{center}")
        self.start("Board and Run Metadata")
        rows = [
            ["board", latex_escape(self.board)],
            ["workspace", r"\texttt{" + latex_escape(st.get("workspace", "")) + "}"],
            ["phase", latex_escape(st.get("phase", "?"))],
            ["gate status", latex_escape(overall)],
            ["state created", latex_escape(st.get("created", "?"))],
            ["state updated", latex_escape(st.get("updated", "?"))],
        ]
        self.body.append(longtable("lp{11cm}", [r"\textbf{Field}", r"\textbf{Value}"], rows))
        self.record("title", "included", "state.json")

    def sec_overview(self) -> None:
        used = []
        self.start("Overview")
        brief = read_text(self.ws, "brief/brief.md")
        if brief is not None:
            self.body.append(md_to_latex(brief))
            used.append("brief/brief.md")
        else:
            self.warn("brief/brief.md not found")
        order = read_json(self.ws, "fab/order.json") or {}
        snap = order.get("spec_snapshot")
        if isinstance(snap, dict):
            keys = ["layers", "width_mm", "height_mm", "qty", "surface_finish",
                    "solder_mask_color", "assembly"]
            rows = [[latex_escape(k), latex_escape(snap.get(k))] for k in keys
                    if k in snap]
            self.body.append(r"\subsection*{Fabrication spec snapshot}")
            self.body.append(longtable("ll", [r"\textbf{Key}", r"\textbf{Value}"], rows))
            used.append("fab/order.json")
        stack = read_text(self.ws, "architecture/stackup.md")
        if stack is not None:
            chosen = next((ln.split(":", 1)[1].strip() for ln in stack.splitlines()
                           if ln.startswith("## Chosen")), None)
            if chosen:
                self.body.append(r"\subsection*{Stackup}")
                self.body.append("Chosen stackup: " + _inline(chosen))
                used.append("architecture/stackup.md")
        if used:
            self.record("overview", "included", ", ".join(used))
        else:
            self.record("overview", "missing", "brief/brief.md")

    def sec_requirements(self) -> None:
        """Resolution ladder (T6 reportgen-fallback): the state.json artifacts
        registry entry, then the workspace root, then the one live stray
        location (lumina-carrier shipped a 'not found' stub while the file
        sat at architecture/requirements.md). Off-root hits stay a warning so
        the misplacement remains visible - check_requirements.py prevents new
        ones at P0 exit."""
        self.start("Requirements")
        reg = (self.st.get("artifacts") or {}).get("requirements")
        candidates = ([str(reg).replace("\\", "/")] if reg else []) + \
            ["requirements.md", "architecture/requirements.md"]
        req = rel = None
        for cand in candidates:
            req = read_text(self.ws, cand)
            if req is not None:
                rel = cand
                break
        if req is None:
            self.warn("requirements.md not found")
            self.body.append(r"\emph{requirements.md not found.}")
            self.record("requirements", "missing", "requirements.md")
            return
        if rel != "requirements.md":
            self.warn(f"requirements.md found at {rel}, not workspace root")
        self.body.append(md_to_latex(req))
        self.record("requirements", "included", rel)

    def sec_architecture(self) -> None:
        used = []
        self.start("Architecture")
        decisions = self.st.get("decisions") or []
        if decisions:
            self.body.append(r"\subsection*{Decisions of record (state.json)}")
            rows = [[latex_escape(d.get("phase", "?")),
                     latex_escape(d.get("what", "")),
                     latex_escape(d.get("why", ""))] for d in decisions]
            self.body.append(longtable(
                "lp{5.2cm}p{7.2cm}",
                [r"\textbf{Phase}", r"\textbf{What}", r"\textbf{Why}"], rows))
            used.append("state.json decisions")
        sheets = read_text(self.ws, "architecture/sheets.md")
        if sheets is not None:
            self.body.append(r"\subsection*{Sheet plan}")
            self.body.append(md_to_latex(sheets))
            used.append("architecture/sheets.md")
        else:
            self.warn("architecture/sheets.md not found")
        others = [f"architecture/{n}" for n in
                  ("blocks.md", "decisions.md", "power_tree.md", "stackup.md")
                  if (self.ws / "architecture" / n).is_file()]
        if others:
            self.body.append("Full architecture narrative (not inlined; see the "
                             "artifact index): "
                             + ", ".join(r"\texttt{" + latex_escape(o) + "}"
                                         for o in others) + ".")
        if used:
            self.record("architecture", "included", ", ".join(used))
        else:
            self.record("architecture", "missing", "architecture/sheets.md")

    def sec_schematic(self) -> None:
        used = []
        self.start("Schematic")
        self.body.append(self.gate_line("erc"))
        waivers = read_text(self.ws, "reports/erc-waivers.md")
        if waivers is not None:
            self.body.append(r"\subsection*{Review waivers}")
            self.body.append(md_to_latex(waivers))
            used.append("reports/erc-waivers.md")
        pdf_present = (self.ws / "reports" / "schematic.pdf").is_file()
        hard = self.core(CORE_SCHEMATIC, pdf_present)
        if pdf_present:
            self.body.append("The full schematic PDF follows.")
            self.body.append(r"\includepdf[pages=-]{reports/schematic.pdf}")
            used.append("reports/schematic.pdf")
        else:
            self.body.append(r"\emph{reports/schematic.pdf not available.}")
        self.record("schematic", "missing" if hard else "included",
                    ", ".join(used) or "reports/schematic.pdf")

    def sec_layout(self) -> None:
        used = []
        self.start("Layout")
        self.body.append(self.gate_line("place"))
        self.body.append("")
        self.body.append(self.gate_line("drc_routed"))
        main, extras = find_renders(self.ws, self.board)
        hard = self.core(CORE_RENDER, bool(main or extras))
        for rel in main:
            self.body.append(image_block(rel, "0.72"))
            used.append(rel)
        for rel in extras:
            width = "0.95" if rel.endswith("_layers.png") else "0.85"
            self.body.append(image_block(rel, width))
            used.append(rel)
        if not (main or extras):
            self.body.append(r"\emph{No board renders found.}")
        self.record("layout", "missing" if hard else "included",
                    ", ".join(used) or "state.json gates")

    def sec_verification(self) -> None:
        used = []
        self.start("Verification")
        self.body.append(self.gate_line("verify"))
        va = read_json(self.ws, "reports/verify_all.json")
        if va and isinstance(va.get("checks"), dict):
            rows = []
            for cname, c in va["checks"].items():
                status = str(c.get("status", "?"))
                note = ""
                if status == "skipped" and c.get("reason"):
                    note = "skipped - " + str(c["reason"])
                elif c.get("reason"):
                    note = str(c["reason"])
                total = (c.get("counts") or {}).get("total")
                rows.append([r"\texttt{" + latex_escape(cname) + "}",
                             latex_escape(status),
                             latex_escape(total if total is not None else ""),
                             latex_escape(note)])
            self.body.append(r"\subsection*{Verification checks}")
            self.body.append(longtable(
                "llcp{6cm}",
                [r"\textbf{Check}", r"\textbf{Status}", r"\textbf{Findings}",
                 r"\textbf{Note}"], rows))
            used.append("reports/verify_all.json")
        else:
            self.warn("reports/verify_all.json not found or unparseable")
            self.body.append(r"\emph{reports/verify\_all.json not available.}")
        review = read_text(self.ws, "reports/review-board.md")
        if review is not None:
            self.body.append(r"\subsection*{Design review of record}")
            self.body.append(md_to_latex(review))
            used.append("reports/review-board.md")
        else:
            self.warn("reports/review-board.md not found")
        self.record("verification", "included" if used else "missing",
                    ", ".join(used) or "reports/verify_all.json")

    def sec_dfm_fab(self) -> None:
        used = []
        self.start("DFM and Fabrication")
        self.body.append(self.gate_line("dfm"))
        gd = read_json(self.ws, "reports/gate-dfm.json")
        by_sev = ((gd or {}).get("counts") or {}).get("by_severity")
        if isinstance(by_sev, dict):
            line = ", ".join(f"{k}: {v}" for k, v in sorted(by_sev.items())) or "none"
            self.body.append("DFM findings by severity: " + latex_escape(line) + ".")
            used.append("reports/gate-dfm.json")
        fx = read_json(self.ws, "reports/fab_export.json")
        if fx and fx.get("layers_exported"):
            self.body.append(r"\subsection*{Fabrication outputs}")
            self.body.append(
                "Exported layers: "
                + latex_escape(", ".join(map(str, fx["layers_exported"]))) + ".")
            used.append("reports/fab_export.json")
        else:
            self.warn("reports/fab_export.json not found or has no layers_exported")

        bom = read_json(self.ws, "reports/bom_cpl.json")
        rows_ok = bool(bom and isinstance(bom.get("bom_rows"), list)
                       and bom["bom_rows"])
        hard = self.core(CORE_BOM, rows_ok)
        if rows_ok:
            self.body.append(r"\subsection*{Bill of materials}")
            rows = [[latex_escape(r.get("Comment", "")),
                     latex_escape(r.get("Designator", "")),
                     latex_escape(r.get("Footprint", "")),
                     latex_escape(r.get("LCSC", ""))] for r in bom["bom_rows"]]
            self.body.append(longtable(
                "p{4.4cm}p{2.8cm}p{4.6cm}l",
                [r"\textbf{Comment}", r"\textbf{Designator}",
                 r"\textbf{Footprint}", r"\textbf{LCSC}"], rows))
            extras = []
            if bom.get("n_rotation_corrections") is not None:
                extras.append(f"{bom['n_rotation_corrections']} CPL rotation "
                              "correction(s) applied")
            ml = bom.get("missing_lcsc")
            if ml:
                extras.append("missing LCSC for: " + ", ".join(map(str, ml)))
            elif ml == []:
                extras.append("no missing LCSC numbers")
            if extras:
                self.body.append(latex_escape("; ".join(extras) + "."))
            used.append("reports/bom_cpl.json")

        order = read_json(self.ws, "fab/order.json")
        hard = self.core(CORE_ORDER, order is not None) or hard
        if order:
            q = (order.get("quote") or {}).get("selected") or {}
            if q:
                self.body.append(r"\subsection*{Quote}")
                line = (f"Estimated total \\${latex_escape(q.get('total', '?'))} "
                        f"for qty {latex_escape(q.get('qty', '?'))}"
                        f" (unit \\${latex_escape(q.get('unit_cost', '?'))}).")
                if (order.get("quote") or {}).get("estimated"):
                    line += (" This is an estimate from published pricing; the "
                             "JLCPCB cart quote page is authoritative.")
                self.body.append(line)
            steps = order.get("human_steps") or []
            if steps:
                self.body.append(r"\subsection*{Human steps before ordering}")
                self.body.append(r"\begin{enumerate}")
                for s in steps:
                    self.body.append(r"\item " + latex_escape(s))
                self.body.append(r"\end{enumerate}")
            used.append("fab/order.json")
        else:
            self.body.append(r"\emph{fab/order.json not available.}")
        self.record("dfm_fab", "missing" if hard else "included",
                    ", ".join(used) or "reports/bom_cpl.json")

    def sec_run_record(self) -> None:
        used = []
        self.start("Run Record (Appendix)")
        self.body.append(r"\subsection*{Phase digests}")
        top = min(self.cur, phase_idx("P10"))
        for pi in range(0, top + 1):
            phase = statemod.PHASES[pi]
            rel = f"log/{phase}-digest.md"
            txt = read_text(self.ws, rel)
            self.body.append(r"\paragraph*{" + phase + "}")
            if txt is None:
                self.body.append(r"\emph{(no digest recorded)}")
                if pi < self.cur:
                    self.warn(f"{rel} missing for passed phase {phase}")
            else:
                self.body.append(tt_block(txt))
                used.append(rel)

        self.body.append(r"\subsection*{Gate attempt history}")
        hist = []
        for gname, g in sorted((self.st.get("gates") or {}).items()):
            entries = g.get("history") or ([g["last"]] if g.get("last") else [])
            for h in entries:
                hist.append((str(h.get("ts", "")), gname, str(h.get("status", "?")),
                             f"{h.get('failing_count', '?')}/{h.get('total', '?')}"))
        hist.sort(key=lambda t: t[0])
        self.body.append(longtable(
            "llll", [r"\textbf{Timestamp}", r"\textbf{Gate}", r"\textbf{Status}",
                     r"\textbf{Failing/Total}"],
            [[latex_escape(c) for c in row] for row in hist]))

        issues = self.st.get("open_issues") or []
        self.body.append(r"\subsection*{Issues}")
        self.body.append(longtable(
            "llp{5cm}ll",
            [r"\textbf{Id}", r"\textbf{Phase}", r"\textbf{Kinds}",
             r"\textbf{Severity}", r"\textbf{Status}"],
            [[latex_escape(i.get("id")), latex_escape(i.get("phase")),
              latex_escape(", ".join(map(str, i.get("kinds") or []))),
              latex_escape(i.get("severity")), latex_escape(i.get("status"))]
             for i in issues]))

        self.body.append(r"\subsection*{Human checkpoints}")
        human = self.st.get("human") or {}
        rows = []
        for cid in sorted(statemod.CHECKPOINTS):
            h = human.get(cid) or {}
            rows.append([latex_escape(cid),
                         latex_escape(statemod.CHECKPOINTS[cid]),
                         latex_escape(h.get("status", "not reached")),
                         latex_escape(h.get("ts", "")),
                         latex_escape(h.get("note", ""))])
        self.body.append(longtable(
            "lllp{2.6cm}p{6.4cm}",
            [r"\textbf{Id}", r"\textbf{Phase}", r"\textbf{Status}",
             r"\textbf{When}", r"\textbf{Note}"], rows))
        self.record("run_record", "included",
                    ", ".join(used + ["state.json"]))

    def sec_artifact_index(self) -> None:
        self.start("Artifact Index")
        order = read_json(self.ws, "fab/order.json") or {}
        zip_sha = (((order.get("artifacts") or {}).get("gerber_zip") or {})
                   .get("sha256") or "")
        rows: list[list[str]] = []

        def add(rel: str, note: str = "") -> None:
            p = self.ws / rel
            if p.is_file():
                rows.append([r"\texttt{" + latex_escape(rel) + "}",
                             latex_escape(f"{p.stat().st_size:,} B"),
                             latex_escape(note)])

        add("state.json")
        add(f"kicad/{self.board}.kicad_pcb")
        add(f"kicad/{self.board}.kicad_sch")
        add(f"fab/{self.board}_gerbers.zip",
            f"sha256 {zip_sha[:16]}..." if zip_sha else "")
        for rel in ("fab/order.json", "fab/BOM.csv", "fab/CPL.csv",
                    "brief/brief.md", "requirements.md"):
            add(rel)
        arch = self.ws / "architecture"
        if arch.is_dir():
            for p in sorted(arch.iterdir()):
                if p.is_file():
                    add(f"architecture/{p.name}")
        reports = self.ws / "reports"
        if reports.is_dir():
            for p in sorted(reports.iterdir()):
                if p.is_file():
                    add(f"reports/{p.name}")
        self.body.append(longtable(
            "p{9cm}rp{4cm}",
            [r"\textbf{File}", r"\textbf{Size}", r"\textbf{Note}"], rows))
        self.record("artifact_index", "included", "workspace scan")

    # -- assembly ---------------------------------------------------------
    BUILDERS = {
        "title": sec_title, "overview": sec_overview,
        "requirements": sec_requirements, "architecture": sec_architecture,
        "schematic": sec_schematic, "layout": sec_layout,
        "verification": sec_verification, "dfm_fab": sec_dfm_fab,
        "run_record": sec_run_record, "artifact_index": sec_artifact_index,
    }

    def build(self) -> str:
        for sid, heading, phase in SECTIONS:
            if not self.due(phase):
                self.pending(sid, heading, phase)
                continue
            self.BUILDERS[sid](self)
        preamble = "\n".join([
            "% Generated by report_gen.py (ai-ee v1) - do not hand-edit.",
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[margin=2.2cm]{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage{booktabs}",
            r"\usepackage{longtable}",
            r"\usepackage{pdfpages}",
            # Compat shim (host-verified): pdfpages >= 2026 v0.6h passes an
            # `artifact` key to \includegraphics on MULTI-page insertions;
            # graphics stacks <= 2024 lack that key and die with "keyval
            # Error: artifact undefined". Define it as a no-op iff absent.
            r"\makeatletter",
            r"\@ifundefined{KV@Gin@artifact}{\define@key{Gin}{artifact}[]{}}{}",
            r"\makeatother",
            r"\usepackage{xcolor}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\setcounter{tocdepth}{1}",
            r"\begin{document}",
            r"\sloppy",
        ])
        tex = (preamble + "\n" + "\n".join(self.head) + "\n"
               + r"\tableofcontents" + "\n\n"
               + "\n".join(self.body)
               + "\n\\end{document}\n")
        bad = sorted({c for c in tex if ord(c) >= 128})
        if bad:
            raise ReportError(
                "internal: generated .tex is not pure ASCII: "
                + ", ".join(f"U+{ord(c):04X}" for c in bad))
        return tex


# ---------------------------------------------------------------- compile

def pdflatex_is_miktex(pdflatex: Path) -> bool:
    try:
        cp = subprocess.run([str(pdflatex), "--version"], capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=30)
        return "miktex" in ((cp.stdout or "") + (cp.stderr or "")).lower()
    except (OSError, subprocess.TimeoutExpired):
        return False


def compile_pdf(pdflatex: Path, ws: Path, name: str) -> tuple[dict, Path | None]:
    """Two pdflatex passes staged in a system temp dir; only the final PDF is
    moved into the workspace (no .aux/.log/.toc residue - boards/ is
    git-tracked and gate commits sweep the whole tree). Never raises on
    compile failure/timeout: returns a compile dict with latex_log_tail."""
    tex_rel = f"reports/design_doc/{name}.tex"
    comp: dict = {"engine": str(pdflatex).replace("\\", "/"), "rc": None,
                  "passes": 0, "seconds": 0.0}
    extra = ["--enable-installer"] if pdflatex_is_miktex(pdflatex) else []
    # Guard the two files pdflatex can drop in cwd on exotic failures.
    guards = {n: (ws / n).exists() for n in ("missfont.log", "texput.log")}
    t0 = time.time()
    final_pdf: Path | None = None
    with tempfile.TemporaryDirectory(prefix="aiee_report_") as td:
        staging = Path(td)
        argv = [str(pdflatex), "-interaction=nonstopmode", "-halt-on-error",
                "-output-directory", str(staging)] + extra + [tex_rel]
        rc = None
        tail_src = ""
        for _ in range(2):
            try:
                cp = subprocess.run(argv, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace",
                                    timeout=PDF_TIMEOUT, cwd=str(ws))
                rc = cp.returncode
                tail_src = cp.stdout or ""
            except subprocess.TimeoutExpired as exc:
                rc = 124
                comp["timed_out"] = True
                out = exc.stdout
                tail_src = (out.decode("utf-8", "replace")
                            if isinstance(out, bytes) else (out or ""))
                comp["passes"] += 1
                break
            comp["passes"] += 1
            if rc != 0:
                break
        comp["rc"] = rc
        comp["seconds"] = round(time.time() - t0, 1)
        staged = staging / f"{name}.pdf"
        ok = rc == 0 and staged.is_file() and staged.stat().st_size > 0
        if ok:
            final_pdf = ws / "reports" / "design_doc" / f"{name}.pdf"
            final_pdf.unlink(missing_ok=True)
            shutil.move(str(staged), str(final_pdf))
        else:
            log = staging / f"{name}.log"
            if log.is_file():
                tail_src = log.read_text(encoding="utf-8", errors="replace")
            comp["latex_log_tail"] = tail_src[-2000:]
    for n, pre in guards.items():
        if not pre and (ws / n).exists():
            (ws / n).unlink()
    return comp, final_pdf


def count_pages(pdf: Path) -> int | None:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        return None


# ---------------------------------------------------------------- driver

def resolve_workspace(arg: str) -> Path:
    p = Path(arg)
    candidates = [p] if p.is_absolute() else [Path.cwd() / p, env.repo_root() / p]
    for c in candidates:
        if (c / "state.json").is_file():
            return c.resolve()
    raise ReportError(f"workspace has no state.json: {arg}")


def load_state(ws: Path) -> dict:
    try:
        d = json.loads((ws / "state.json").read_text(encoding="utf-8",
                                                     errors="replace"))
    except (OSError, json.JSONDecodeError) as e:
        raise ReportError(f"state.json unreadable: {type(e).__name__}: {e}")
    if not isinstance(d, dict) or "board" not in d or "phase" not in d:
        raise ReportError("state.json lacks the board/phase schema fields")
    return d


def run(workspace: str, name: str | None = None, tex_only: bool = False) -> tuple[dict, int]:
    ws = resolve_workspace(workspace)
    st = load_state(ws)
    doc_name = f"{name or st['board']}-design-doc"

    builder = DocBuilder(ws, st, name or st["board"])
    tex_text = builder.build()

    out_dir = ws / "reports" / "design_doc"
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / f"{doc_name}.tex"
    tex_path.write_text(tex_text, encoding="utf-8")

    pdflatex: Path | None = None
    if not tex_only:
        # Resolved after the tex write: a bad AIEE_PDFLATEX pin still exits 2
        # (EnvError propagates) but must not discard the built document.
        pdflatex = env.find_pdflatex()
        if pdflatex is None:
            builder.warn("pdflatex not installed - degraded to --tex-only "
                         "(no PDF produced)")

    comp = None
    pdf_path: Path | None = None
    pages = None
    if pdflatex is not None:
        comp, pdf_path = compile_pdf(pdflatex, ws, doc_name)
        if pdf_path is None:
            if comp.get("timed_out"):
                builder.warn(f"pdflatex timed out after {PDF_TIMEOUT}s - "
                             "PDF not produced")
            else:
                builder.warn(f"pdflatex failed (rc={comp.get('rc')}) - PDF "
                             "not produced; see compile.latex_log_tail")
        else:
            pages = count_pages(pdf_path)
            if pages is None:
                builder.warn("pypdf could not read the produced PDF")

    degraded = (not tex_only) and pdf_path is None
    violations = bool(builder.missing) or degraded
    payload = {
        "script": "report_gen",
        "status": "violations" if violations else "pass",
        "board": name or st["board"],
        "workspace": str(ws).replace("\\", "/"),
        "tex": f"reports/design_doc/{doc_name}.tex",
        "pdf": f"reports/design_doc/{doc_name}.pdf" if pdf_path else None,
        "pages": pages,
        "sections": builder.sections,
        "missing": builder.missing,
        "warnings": builder.warnings,
        "compile": comp,
    }
    return payload, (1 if violations else 0)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", required=True,
                    help="board workspace dir containing state.json "
                         "(absolute or repo-relative)")
    ap.add_argument("--out", help="write the JSON payload here instead of stdout")
    ap.add_argument("--tex-only", action="store_true",
                    help="write the .tex only; skip the pdflatex compile")
    ap.add_argument("--name", help="override the board name from state.json")
    args = ap.parse_args(argv)

    try:
        payload, code = run(args.workspace, name=args.name,
                            tex_only=args.tex_only)
    except Exception as exc:  # noqa: BLE001 (SPEC: any error -> exit 2)
        err = {"script": "report_gen", "status": "error",
               "error": f"{type(exc).__name__}: {exc}"}
        text = json.dumps(err, indent=1)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            print(text)
        return 2

    text = json.dumps(payload, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
