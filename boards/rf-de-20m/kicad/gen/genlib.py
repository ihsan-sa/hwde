"""Shared post-save helpers for the rf-de-20m generators.

Currently one job: hide the AUXILIARY component fields.

`schlib.add_component(fields={...})` writes each extra field as a normal
`(property ...)` node, and kicad-sch-api gives it VISIBLE effects - so every
`LCSC` code and every `Note` string prints on the plot, on top of the part it
belongs to. On this board that is ~70 LCSC codes and ~60 notes, and the
rendered PDF becomes unreadable exactly where a human reviewer needs to read
it (the switch cluster).

The fields must still EXIST: P9's `bom_cpl` takes the LCSC code from the
board's per-footprint field as its primary source, and the notes are the
sheet's own record of why a value is what it is. Hiding is a plot property
only - `(hide yes)` inside the field's `(effects ...)`, exactly the form
KiCad itself writes for `Footprint` and `Datasheet`.

Reference and Value stay visible; so does `Variant`, because `Variant=DNP` is
the ONLY do-not-populate marking reachable from a generator (kicad-sch-api's
writer hard-codes `(dnp no)` - LEARNINGS 2026-08-07) and a human must see it.

Idempotent: a field that already carries `(hide yes)` is left alone.
"""
from __future__ import annotations

from pathlib import Path

VISIBLE = {"Reference", "Value", "Variant"}


def _match(text: str, open_idx: int) -> int:
    """Index just past the paren opened at `open_idx`, quote-aware."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced s-expression at {open_idx}")


def hide_aux_fields(path: Path | str) -> int:
    """Add `(hide yes)` to every non-VISIBLE property. Returns the count."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    out = []
    pos = 0
    hidden = 0
    needle = '(property "'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        j = text.index('"', i + len(needle))
        name = text[i + len(needle):j]
        end = _match(text, i)
        node = text[i:end]
        if name in VISIBLE or "(hide yes)" in node:
            out.append(text[pos:end])
            pos = end
            continue
        e = node.find("(effects")
        if e >= 0:
            e_end = _match(node, e)
            indent = " " * (len(node[:e]) - len(node[:e].rstrip(" \t")) - 1)
            node = (node[:e_end - 1] + f"\t{indent}(hide yes)\n{indent}"
                    + node[e_end - 1:])
        else:
            node = node[:-1] + "(effects (hide yes))"
        hidden += 1
        out.append(text[pos:i] + node)
        pos = end
    out.append(text[pos:])
    new = "".join(out)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return hidden
