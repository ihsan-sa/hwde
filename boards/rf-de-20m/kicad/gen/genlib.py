"""Shared helpers for the rf-de-20m generators.

Two jobs: stamp the LCSC field on components a helper placed without it, and
hide the AUXILIARY component fields after save.

WHY stamp_lcsc EXISTS (P4 review E5, 2026-08-08)
------------------------------------------------
Each sheet's local `_add` wrapper attaches `fields={"LCSC": ...}` to every
purchased part - but `schlib.place_ic_with_decoupling` calls
`Sheet.add_component` DIRECTLY and takes no `fields` argument, so the IC and
its decoupling caps came out of the generator with NO `LCSC` instance
property. That hit U101, U201, C105, C106, C201, C202 and C213, and it is
invisible until P9: `bom_cpl.board_lcsc_map` matches on
`pname.upper() == "LCSC"` only, so the symbol's inherited `LCSC Part`
property does not satisfy it and the board-file fallback misses exactly those
refs. (KiCad 10 DRC also raises `footprint_symbol_field_mismatch` for a
missing symbol field at P5/P6.) `stamp_lcsc` closes it after the fact rather
than by forking the shared schlib helper.

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


def stamp_lcsc(sh, lcsc: dict, refs) -> list[str]:
    """Set the `LCSC` instance property on `refs` from the `lcsc` map.

    For components placed by `schlib.place_ic_with_decoupling`, which has no
    `fields` parameter. Idempotent; raises on an unknown ref or a ref with no
    code, because a silently skipped stamp is the exact defect this closes.
    """
    done = []
    for ref in refs:
        code = lcsc.get(ref)
        if not code:
            raise KeyError(f"stamp_lcsc: no LCSC code for {ref}")
        comp = sh.sch.components.get(ref)
        if comp is None:
            raise KeyError(f"stamp_lcsc: {ref} not placed on sheet {sh.name}")
        comp.set_property("LCSC", code)
        done.append(ref)
    return done


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
