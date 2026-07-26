"""Phase 11 — Network & Graph Analysis. GET /api/network/{case_id}: builds
the co-offender graph around a case, using NetworkX.

Graph model, matched to how the data is actually generated (confirmed by
reading data_generation/generators/case_children.py, not assumed):
inv_arrestsurrenderaccused is 1:1 by construction — one ArrestSurrender
row already targets exactly one Accused, so there is no multi-accused
"arrest event" to read co-occurrence from. The two real signals are:
  1. Same-case co-accused: multiple Accused rows sharing one CaseMasterID
     (gang members charged together, arrested individually).
  2. Recidivism: the same real person recurs as separate Accused rows
     across different cases, identified by (AccusedName, AgeYear,
     GenderID) — Accused has no cross-case person ID in this schema (see
     narratives.py's module docstring).
Edges connect accused who share a case; the graph expands outward through
recidivism to also chain in each repeat offender's OTHER cases' co-accused.

ROWID vs business ID (confirmed live, not assumed): every `_FK` column
stores the parent row's Catalyst ROWID, never the parent's own "named ID"
business column (e.g. Accused.CaseMasterID_FK holds CaseMaster's ROWID,
not CaseMaster.CseMasterID). All internal chaining below happens in ROWID
space; results are translated back to business IDs (CseMasterID,
AccusedMasterID) exactly once, at the end.

All lookups are batched via WHERE ... IN (...) — no per-row round trip
(CLAUDE.md: no N+1 queries against the Data Store).
"""

from __future__ import annotations

from typing import Any

import networkx as nx

import zcql_util
from zcql_util import CaseNotFound, in_clause


def build_case_network(case_id: int, zcql_service: Any) -> dict[str, Any]:
    case_rows = zcql_util.run(zcql_service, f"SELECT ROWID FROM CaseMaster WHERE CseMasterID = {int(case_id)}")
    if not case_rows:
        raise CaseNotFound(f"CaseMasterID {case_id} not found")
    case_rowid = int(case_rows[0]["ROWID"])

    seed_rows = zcql_util.run(zcql_service, f"SELECT ROWID FROM Accused WHERE CaseMasterID_FK = {case_rowid}")
    seed_accused_rowids = [int(r["ROWID"]) for r in seed_rows]
    if not seed_accused_rowids:
        return {"nodes": [], "edges": [], "case_ids": [case_id]}

    result = expand_accused_network(seed_accused_rowids, zcql_service, seed_is_rowid=True)
    result["case_ids"] = sorted(set(result["case_ids"]) | {case_id})
    return result


def expand_accused_network(
    seed_accused_ids: list[int], zcql_service: Any, seed_is_rowid: bool = False,
) -> dict[str, Any]:
    """From a set of seed Accused ROWIDs: expand through recidivism (same
    person's other Accused rows, by name+age+gender) to find every case
    they touch, then pull every co-accused sharing any of those cases, and
    connect co-accused pairwise per shared case.

    Used by build_case_network (seed = a case's own Accused rows) and
    entity_context.py (seed = one person's own Accused row, Phase 14).

    Returns nodes/edges keyed by business AccusedMasterID and case_ids as
    business CseMasterID values — never raw ROWIDs."""
    if not seed_accused_ids:
        return {"nodes": [], "edges": [], "case_ids": []}
    if not seed_is_rowid:
        raise NotImplementedError("expand_accused_network needs Accused ROWIDs, not business AccusedMasterID values")

    seed_rows = zcql_util.run(
        zcql_service,
        f"SELECT ROWID, AccusedName, AgeYear, GenderID, CaseMasterID_FK FROM Accused "
        f"WHERE ROWID IN ({in_clause(seed_accused_ids)})",
    )
    if not seed_rows:
        return {"nodes": [], "edges": [], "case_ids": []}

    identity_tuples = {(r["AccusedName"], int(r["AgeYear"]), int(r["GenderID"])) for r in seed_rows}
    identity_clause = " OR ".join(
        f"(AccusedName = '{name.replace(chr(39), chr(39) * 2)}' AND AgeYear = {age} AND GenderID = {gender})"
        for name, age, gender in identity_tuples
    )
    recidivism_rows = zcql_util.run(
        zcql_service, f"SELECT ROWID, CaseMasterID_FK FROM Accused WHERE {identity_clause}",
    )

    case_rowids = sorted({int(r["CaseMasterID_FK"]) for r in seed_rows} | {int(r["CaseMasterID_FK"]) for r in recidivism_rows})

    all_accused = zcql_util.run(
        zcql_service,
        f"SELECT ROWID, AccusedMasterID, AccusedName, CaseMasterID_FK FROM Accused "
        f"WHERE CaseMasterID_FK IN ({in_clause(case_rowids)})",
    )

    case_meta = zcql_util.run(
        zcql_service, f"SELECT ROWID, CseMasterID FROM CaseMaster WHERE ROWID IN ({in_clause(case_rowids)})",
    )
    case_rowid_to_businessid = {int(r["ROWID"]): int(r["CseMasterID"]) for r in case_meta}

    seed_business_ids = {
        int(a["AccusedMasterID"]) for a in all_accused if int(a["ROWID"]) in set(seed_accused_ids)
    }

    accused_by_case: dict[int, list[dict[str, Any]]] = {}
    for a in all_accused:
        accused_by_case.setdefault(int(a["CaseMasterID_FK"]), []).append(a)

    graph = nx.Graph()
    for a in all_accused:
        business_id = int(a["AccusedMasterID"])
        graph.add_node(business_id, label=a["AccusedName"], is_seed=business_id in seed_business_ids)

    for case_rowid, accused_in_case in accused_by_case.items():
        case_business_id = case_rowid_to_businessid.get(case_rowid)
        ids_in_case = [int(a["AccusedMasterID"]) for a in accused_in_case]
        for i in range(len(ids_in_case)):
            for j in range(i + 1, len(ids_in_case)):
                a, b = ids_in_case[i], ids_in_case[j]
                if graph.has_edge(a, b):
                    graph[a][b]["weight"] += 1
                    if case_business_id is not None:
                        graph[a][b]["shared_case_ids"].add(case_business_id)
                else:
                    graph.add_edge(a, b, weight=1, shared_case_ids={case_business_id} if case_business_id is not None else set())

    nodes = [{"id": n, **graph.nodes[n]} for n in graph.nodes]
    edges = [
        {"source": u, "target": v, "weight": d["weight"], "shared_case_ids": sorted(d["shared_case_ids"])}
        for u, v, d in graph.edges(data=True)
    ]
    case_ids = sorted(case_rowid_to_businessid.values())

    return {"nodes": nodes, "edges": edges, "case_ids": case_ids}
