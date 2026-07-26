"""Shared helpers for CSV-based synthetic data generators.

Every generator writes a flat CSV of one table's rows to `csv_out/`.
Named IDs (e.g. StateID) are our own sequential ints — they are NOT
Catalyst's ROWID. FK columns store the parent's ROWID, resolved from
a `{named_id: rowid}` map handed in by pipeline.py after that parent
table has actually been imported. See data_generation/pipeline.py for
the import -> fetch-ROWID-map -> next-table sequencing.
"""

from __future__ import annotations

import csv
import os
from typing import Any

CSV_DIR = os.path.join(os.path.dirname(__file__), "csv_out")


def _catalyst_cell(value: Any) -> Any:
    """Catalyst's ds:import rejects Python's `True`/`False` string casing
    for Boolean columns ("Invalid input value for Active. Please give a
    correct boolean value" — confirmed via a real failed import job on the
    State table). Every generator writes bools through write_csv, so the
    fix lives here once instead of at every call site."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def write_csv(
    rows: list[dict[str, Any]], table_name: str, column_rename: dict[str, str] | None = None,
) -> str:
    """Write rows to csv_out/{table_name}.csv, return the path.

    column_rename: {clean_name: built_as_name} applied ONLY to the CSV
    header/output, never to the in-memory rows returned to callers — Phase
    1's console build introduced spelling drift on several columns
    (CaseMasterID -> CseMasterID, GravityOffenceID -> GravityOffence, etc,
    see schema.md's "Naming drift" table). Downstream Python keeps using
    the clean names; only what actually gets sent to ds:import needs to
    match Catalyst's real (typo'd) column names.

    Column order is taken from the first row's keys. Raises if rows is empty
    (an empty generator run is a bug, not a valid output).
    """
    if not rows:
        raise ValueError(f"{table_name}: generator produced zero rows")
    column_rename = column_rename or {}
    os.makedirs(CSV_DIR, exist_ok=True)
    path = os.path.join(CSV_DIR, f"{table_name}.csv")
    fieldnames = [column_rename.get(k, k) for k in rows[0].keys()]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {column_rename.get(k, k): _catalyst_cell(v) for k, v in row.items()} for row in rows
        )
    return path


def id_sequence(start: int = 1):
    """Infinite sequential-int generator for named ID columns."""
    n = start
    while True:
        yield n
        n += 1
