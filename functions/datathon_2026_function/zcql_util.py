"""Shared ZCQL row-normalization helper. Row shape returned by
zcql_service.execute_query() is UNCONFIRMED against a live table in this
project (docs describe "a row object or array of row objects" without
showing the exact dict shape) — this handles both a flat dict per row and
the {table_name: {...}} nesting other Catalyst SDKs use, and raises
explicitly if neither shape matches rather than guessing further.
"""

from __future__ import annotations

from typing import Any


class ZcqlError(Exception):
    pass


class CaseNotFound(Exception):
    """Shared across network.py and similar_cases.py — both look up a
    CaseMasterID first; a single shared type keeps main.py's except clause
    correct regardless of which module raised it."""


def run(zcql_service: Any, sql: str) -> list[dict[str, Any]]:
    raw_rows = zcql_service.execute_query(sql)
    if raw_rows is None:
        return []
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ZcqlError(f"unexpected ZCQL row type {type(raw)}: {raw!r}")
        if len(raw) == 1 and isinstance(next(iter(raw.values())), dict):
            rows.append(next(iter(raw.values())))
        else:
            rows.append(raw)
    return rows


def in_clause(values: list[int]) -> str:
    """Safe to build directly (no string interpolation of untrusted input)
    only because callers pass ints already round-tripped through a prior
    ZCQL result, never raw user input."""
    return ", ".join(str(int(v)) for v in values)
