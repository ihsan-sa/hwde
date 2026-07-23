#!/usr/bin/env python
"""parts_search.py - LCSC/JLCPCB parametric part search (SPEC.md P3, 6.1).

Returns a ranked JSON candidate list (Basic-first, then stock, then price) for a
keyword query, with parametric filters. Primary source is the anonymous JLCPCB
parts search (no credential); a cached jlcparts SQLite DB is an offline fallback
(--db); web search is the agent's last resort (signalled by exit 2 when the live
endpoint is unreachable and no --db is given).

Contract (SPEC section 6): argparse, JSON to stdout or --out, exit 0/1/2.
  0 = query ran (results present OR a genuine no-match against a reachable API)
  2 = error (endpoint unreachable with no usable cache, bad db, internal error)
(There is no exit-1 "violations" notion for a search.)

Examples:
  parts_search.py --query "STM32F103C8T6"
  parts_search.py --query "100nF 0603 X7R" --basic-only --min-stock 5000 --limit 5
  parts_search.py --query "10k 0603" --filters package=0603 type=basic --db cache.sqlite3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import partslib  # noqa: E402

_FILTER_KEYS = {"package", "type", "min_stock", "max_price", "brand", "contains"}


def _parse_filters(pairs: list[str]) -> dict:
    """`--filters package=0603 type=basic` -> dict, validated against known keys."""
    out: dict = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise partslib.PartsError(f"bad --filters item '{pair}' (want key=value)")
        key, val = pair.split("=", 1)
        key = key.strip()
        if key not in _FILTER_KEYS:
            raise partslib.PartsError(
                f"unknown filter '{key}'; known: {sorted(_FILTER_KEYS)}")
        out[key] = val.strip()
    return out


def _merge_filter_args(args, extra: dict) -> dict:
    """Combine explicit flags with --filters items (flags win when both set)."""
    f = dict(extra)
    if args.package is not None:
        f["package"] = args.package
    if args.basic_only:
        f["type"] = "basic"
    if args.min_stock is not None:
        f["min_stock"] = str(args.min_stock)
    if args.max_price is not None:
        f["max_price"] = str(args.max_price)
    if args.brand is not None:
        f["brand"] = args.brand
    if args.contains is not None:
        f["contains"] = args.contains
    return f


def search(args) -> dict:
    filters = _merge_filter_args(args, _parse_filters(args.filters))
    ftype = (filters.get("type") or "").lower()
    basic_only = ftype == "basic"
    part_type = {"basic": "base", "extended": "expand"}.get(ftype)
    min_stock = int(filters["min_stock"]) if "min_stock" in filters else 0
    max_price = float(filters["max_price"]) if "max_price" in filters else None

    # Fetch a generous window so filters + ranking have material to work on.
    window = max(args.limit * 4, 25)
    source = "live"
    total = 0
    raw: list[dict] = []
    try:
        raw, total = partslib.live_search(
            args.query, page=args.page, page_size=window, part_type=part_type)
    except Exception as exc:  # noqa: BLE001 - network layer is fragile; fall through
        raw = []

    if not raw:
        # Empty live result: cached DB > web-search hint. Disambiguate offline.
        if args.db:
            source = "db"
            raw_norm = partslib.db_search(args.db, args.query, limit=window)
            parts = raw_norm  # already normalized
        elif not partslib.endpoint_reachable():
            raise partslib.PartsError(
                "JLCPCB search endpoint unreachable and no --db cache given. "
                "Fix: run with network, pass --db <jlcparts cache.sqlite3>, or "
                "fall back to web search for the MPN.")
        else:
            # Reachable but genuinely no matches - not an error.
            return {
                "script": "parts_search", "status": "empty", "source": source,
                "query": args.query, "total": 0, "count": 0, "results": [],
                "filters": filters,
            }
    else:
        parts = [partslib.normalize(it) for it in raw]

    parts = partslib.apply_filters(
        parts, basic_only=basic_only, package=filters.get("package"),
        min_stock=min_stock, max_price=max_price, brand=filters.get("brand"),
        contains=filters.get("contains"))
    parts.sort(key=partslib.rank_key)
    top = parts[: args.limit]
    for i, p in enumerate(top):
        p["rank"] = i
    return {
        "script": "parts_search",
        "status": "pass" if top else "empty",
        "source": source,
        "query": args.query,
        "total": total,
        "count": len(top),
        "results": top,
        "filters": filters,
    }


def main(argv: list[str] | None = None) -> int:
    partslib.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--query", required=True, help="keyword search (MPN, value, package, ...)")
    ap.add_argument("--limit", type=int, default=10, help="max ranked results (default 10)")
    ap.add_argument("--page", type=int, default=1, help="live-search page (default 1)")
    ap.add_argument("--basic-only", action="store_true", help="JLC Basic parts only")
    ap.add_argument("--package", help="require this package substring (e.g. 0603)")
    ap.add_argument("--min-stock", type=int, help="require stock >= N")
    ap.add_argument("--max-price", type=float, help="require unit price <= N")
    ap.add_argument("--brand", help="require this brand substring")
    ap.add_argument("--contains", help="require this substring in description/MPN")
    ap.add_argument("--filters", nargs="*", default=[],
                    help="key=value filters: " + " ".join(sorted(_FILTER_KEYS)))
    ap.add_argument("--db", help="jlcparts SQLite cache for offline fallback")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)
    try:
        payload = search(args)
    except partslib.PartsError as exc:
        payload = {"script": "parts_search", "status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - contract: any error -> exit 2
        payload = {"script": "parts_search", "status": "error",
                   "error": f"{type(exc).__name__}: {exc}"}
    return partslib.emit(payload, args.out)


if __name__ == "__main__":
    sys.exit(main())
