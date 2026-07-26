"""Phase 14 — Entity Auto-Context Fetch. GET /api/entity-context/{accused_id}:
pulls a profile for an accused — past cases, risk score, network position —
for the sidecar card Person A's frontend renders alongside a main answer.

"Past cases" uses the same cross-case identity resolution documented in
data_generation/generators/narratives.py: Accused has no cross-case person
ID in this schema, so the same real person recurs as separate AccusedMasterID
rows in each case, matched by (AccusedName, AgeYear, GenderID).

ROWID vs business ID (see network.py's module docstring for the confirmed
FK convention): Accused.CaseMasterID_FK and RiskScore.AccusedMasterID_FK
both store the parent's ROWID, never CseMasterID/AccusedMasterID directly
— every lookup below resolves through ROWID, translating back to business
IDs only in the returned dict.

risk_score is null until Phase 15 (RiskScore table) is populated for this
accused — never fabricated, per CLAUDE.md's anti-hallucination rule.
"""

from __future__ import annotations

from typing import Any

import zcql_util
from network import expand_accused_network
from zcql_util import CaseNotFound, in_clause


def get_entity_context(accused_id: int, zcql_service: Any) -> dict[str, Any]:
    self_rows = zcql_util.run(
        zcql_service,
        f"SELECT AccusedName, AgeYear, GenderID FROM Accused WHERE AccusedMasterID = {int(accused_id)}",
    )
    if not self_rows:
        raise CaseNotFound(f"AccusedMasterID {accused_id} not found")
    self_row = self_rows[0]

    # Recidivism match: same name+age+gender across cases (see narratives.py).
    identity_rows = zcql_util.run(
        zcql_service,
        "SELECT ROWID, CaseMasterID_FK FROM Accused WHERE "
        f"AccusedName = '{self_row['AccusedName'].replace(chr(39), chr(39) * 2)}' "
        f"AND AgeYear = {int(self_row['AgeYear'])} AND GenderID = {int(self_row['GenderID'])}",
    )
    identity_accused_rowids = sorted({int(r["ROWID"]) for r in identity_rows})
    case_rowids = sorted({int(r["CaseMasterID_FK"]) for r in identity_rows})

    case_meta = zcql_util.run(
        zcql_service,
        f"SELECT ROWID, CseMasterID FROM CaseMaster WHERE ROWID IN ({in_clause(case_rowids)})",
    ) if case_rowids else []
    past_case_ids = sorted({int(r["CseMasterID"]) for r in case_meta})

    risk_rows = zcql_util.run(
        zcql_service,
        f"SELECT RiskScoreValue, TopFeaturesJSON, CounterfactualJSON, ModelVersion "
        f"FROM RiskScore WHERE AccusedMasterID_FK IN ({in_clause(identity_accused_rowids)}) LIMIT 1",
    ) if identity_accused_rowids else []
    risk_score = risk_rows[0] if risk_rows else None

    network = expand_accused_network(identity_accused_rowids, zcql_service, seed_is_rowid=True)
    # is_seed nodes are this same person's own recidivism-matched entries
    # (one per case they appear in) — exclude them to count OTHER people.
    other_accused_count = sum(1 for n in network["nodes"] if not n["is_seed"])

    return {
        "accused_id": accused_id,
        "name": self_row["AccusedName"],
        "past_case_ids": past_case_ids,
        "risk_score": risk_score,
        "network_position": {
            "connected_accused_count": other_accused_count,
            "connected_case_count": len(set(network["case_ids"]) - set(past_case_ids)),
        },
    }
