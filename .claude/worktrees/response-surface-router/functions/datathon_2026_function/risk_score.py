"""Phase 15 — Risk Scoring. GET /api/risk-score/{accused_id}: computes
offender features fresh from current Data Store state (prior_case_count,
arrest_count, primary_role_count, max_gravity_rank, AgeYear, GenderID) and
scores them with the local model in risk_model.py.

Zia AutoML is NOT used — confirmed unavailable on this project's data
center (Catalyst docs: AutoML doesn't serve the EU/AU/IN/JP/SA/CA DCs;
this project is on .in, and the predict endpoint 404s with
INVALID_URL_PATTERN, matching that constraint exactly, not a URL typo).
See risk_model.py's module docstring for the local scikit-learn + SHAP
replacement.
"""

from __future__ import annotations

import datetime
import json
from typing import Any

import zcql_util
from risk_model import predict_with_explanation
from zcql_util import CaseNotFound, in_clause

_GRAVITY_RANK = {"Non-Heinous": 0, "Heinous": 1}


def _compute_features(accused_id: int, zcql_service: Any) -> tuple[dict[str, Any], int]:
    """Returns (feature_dict, this_accused_row's_ROWID)."""
    self_rows = zcql_util.run(
        zcql_service,
        f"SELECT ROWID, AccusedName, AgeYear, GenderID FROM Accused WHERE AccusedMasterID = {int(accused_id)}",
    )
    if not self_rows:
        raise CaseNotFound(f"AccusedMasterID {accused_id} not found")
    self_row = self_rows[0]
    self_rowid = int(self_row["ROWID"])

    identity_rows = zcql_util.run(
        zcql_service,
        "SELECT ROWID, CaseMasterID_FK FROM Accused WHERE "
        f"AccusedName = '{self_row['AccusedName'].replace(chr(39), chr(39) * 2)}' "
        f"AND AgeYear = {int(self_row['AgeYear'])} AND GenderID = {int(self_row['GenderID'])}",
    )
    accused_rowids = [int(r["ROWID"]) for r in identity_rows]
    case_rowids = sorted({int(r["CaseMasterID_FK"]) for r in identity_rows})
    prior_case_count = len(case_rowids)

    arrest_rows = zcql_util.run(
        zcql_service,
        f"SELECT AccusedMasterID_FK FROM ArrestSurrender WHERE AccusedMasterID_FK IN ({in_clause(accused_rowids)})",
    )
    arrest_count = len({int(r["AccusedMasterID_FK"]) for r in arrest_rows})

    link_rows = zcql_util.run(
        zcql_service,
        f"SELECT RoleInEvent FROM inv_arrestsurrenderaccused WHERE AccusedMasterID_FK IN ({in_clause(accused_rowids)})",
    )
    primary_role_count = sum(1 for r in link_rows if r["RoleInEvent"] == "Primary")

    case_meta = zcql_util.run(
        zcql_service, f"SELECT ROWID, GravityOffenceID FROM CaseMaster WHERE ROWID IN ({in_clause(case_rowids)})",
    ) if case_rowids else []
    gravity_fks = {int(c["GravityOffenceID"]) for c in case_meta}
    gravity_lookup = zcql_util.run(
        zcql_service, f"SELECT ROWID, LookupValue FROM GravityOffence WHERE ROWID IN ({in_clause(list(gravity_fks))})",
    ) if gravity_fks else []
    max_gravity_rank = max((_GRAVITY_RANK.get(g["LookupValue"], 0) for g in gravity_lookup), default=0)

    features = {
        "AgeYear": int(self_row["AgeYear"]),
        "GenderID": int(self_row["GenderID"]),
        "prior_case_count": prior_case_count,
        "arrest_count": arrest_count,
        "primary_role_count": primary_role_count,
        "max_gravity_rank": max_gravity_rank,
    }
    return features, self_rowid


def _next_risk_score_id(zcql_service: Any) -> int:
    """RiskScoreID is a mandatory business PK, not Catalyst's auto-assigned
    ROWID — every other table in this project fills it via a local
    id_sequence() during bulk CSV generation; a live INSERT here has to
    compute the next value itself instead."""
    # ponytail: read-then-increment, no lock — two concurrent calls could
    # race onto the same ID. Fine for a demo's call volume; upgrade to a
    # Catalyst-side sequence/lock if this endpoint sees real concurrent load.
    rows = zcql_util.run(zcql_service, "SELECT RiskScoreID FROM RiskScore ORDER BY RiskScoreID DESC LIMIT 1")
    return int(rows[0]["RiskScoreID"]) + 1 if rows else 1


def get_risk_score(accused_id: int, zcql_service: Any) -> dict[str, Any]:
    features, self_rowid = _compute_features(accused_id, zcql_service)
    prediction = predict_with_explanation(features, zcql_service)
    next_id = _next_risk_score_id(zcql_service)

    zcql_util.run(
        zcql_service,
        "INSERT INTO RiskScore (RiskScoreID, AccusedMasterID_FK, RiskScoreValue, ComputedDate, ModelVersion, "
        "TopFeaturesJSON, CounterfactualJSON) VALUES "
        f"({next_id}, {self_rowid}, {prediction['risk_score']}, '{datetime.date.today().isoformat()}', "
        f"'local-rf-shap-v1', '{json.dumps(prediction['top_features'])}', "
        f"'{json.dumps(prediction['counterfactual'])}')",
    )

    return {
        "accused_id": accused_id,
        "risk_score": prediction["risk_score"],
        "predicted_class": prediction["predicted_class"],
        "features_used": features,
        "top_features": prediction["top_features"],
        "counterfactual": prediction["counterfactual"],
        "model_version": "local-rf-shap-v1",
    }
