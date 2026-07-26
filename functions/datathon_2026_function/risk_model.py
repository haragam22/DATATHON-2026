"""Phase 15 risk model — local scikit-learn classifier + SHAP, replacing
Zia AutoML. Zia AutoML is CONFIRMED unavailable on this project's data
center (Catalyst docs: "AutoML is currently not available to Catalyst
users accessing from the EU, AU, IN, JP, SA or CA data centers" — this
project is on .in). The predict endpoint 404s with INVALID_URL_PATTERN
for exactly this reason, not a URL typo.

Trains a RandomForestClassifier on features fetched fresh from Data Store
at cold start (module-level cache, same pattern as similar_cases.py's
corpus cache) — same feature set as
data_generation/build_risk_training_set.py's labeled CSV: AgeYear,
GenderID, prior_case_count, arrest_count, primary_role_count,
max_gravity_rank -> risk_label. That CSV's heuristic label construction is
documented there; this module doesn't redefine the label logic, it re-
derives the same features live so the model always trains against current
Data Store state instead of a point-in-time CSV snapshot.

SHAP (real, via shap.TreeExplainer — not fabricated) gives per-prediction
top features. Counterfactual is a simple greedy single-feature search
(decrement each count-type feature by 1, keep the one whose flip actually
changes predicted_class) — a real computed result, but a much simpler
method than a proper counterfactual-generation library like DiCE, which
isn't in this project's dependency set.
ponytail: single-feature greedy counterfactual, not a real DiCE-style
search. Upgrade if the demo needs multi-feature counterfactuals.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier

import zcql_util
from zcql_util import in_clause

_FEATURE_ORDER = ["AgeYear", "GenderID", "prior_case_count", "arrest_count", "primary_role_count", "max_gravity_rank"]
_GRAVITY_RANK = {"Non-Heinous": 0, "Heinous": 1}

_model_cache: dict[str, Any] = {"model": None, "explainer": None}


def _fetch_all(zcql_service: Any, table: str, columns: str) -> list[dict]:
    rows: list[dict] = []
    last_rowid = 0
    while True:
        batch = zcql_util.run(
            zcql_service, f"SELECT ROWID, {columns} FROM {table} WHERE ROWID > {last_rowid} ORDER BY ROWID ASC LIMIT 200",
        )
        if not batch:
            break
        rows.extend(batch)
        last_rowid = int(batch[-1]["ROWID"])
    return rows


def _build_training_data(zcql_service: Any) -> tuple[list[list[float]], list[int]]:
    accused = _fetch_all(zcql_service, "Accused", "AccusedMasterID, AccusedName, AgeYear, GenderID, CaseMasterID_FK")
    arrests = _fetch_all(zcql_service, "ArrestSurrender", "AccusedMasterID_FK")
    arrested_rowids = {int(r["AccusedMasterID_FK"]) for r in arrests}
    links = _fetch_all(zcql_service, "inv_arrestsurrenderaccused", "AccusedMasterID_FK, RoleInEvent")
    primary_by_rowid: dict[int, int] = {}
    for link in links:
        rowid = int(link["AccusedMasterID_FK"])
        primary_by_rowid[rowid] = primary_by_rowid.get(rowid, 0) + (1 if link["RoleInEvent"] == "Primary" else 0)
    cases = _fetch_all(zcql_service, "CaseMaster", "GravityOffenceID")
    case_rowid_to_gravity_fk = {int(c["ROWID"]): int(c["GravityOffenceID"]) for c in cases}
    gravity_lookup = _fetch_all(zcql_service, "GravityOffence", "LookupValue")
    gravity_rowid_to_rank = {int(g["ROWID"]): _GRAVITY_RANK.get(g["LookupValue"], 0) for g in gravity_lookup}

    identity_groups: dict[tuple[str, int, int], list[dict]] = {}
    for a in accused:
        key = (a["AccusedName"], int(a["AgeYear"]), int(a["GenderID"]))
        identity_groups.setdefault(key, []).append(a)

    X: list[list[float]] = []
    y: list[int] = []
    for (_, age, gender), identity_rows in identity_groups.items():
        case_rowids = {int(a["CaseMasterID_FK"]) for a in identity_rows}
        prior_case_count = len(case_rowids)
        arrest_count = sum(1 for a in identity_rows if int(a["ROWID"]) in arrested_rowids)
        primary_role_count = sum(primary_by_rowid.get(int(a["ROWID"]), 0) for a in identity_rows)
        max_gravity_rank = max(
            (gravity_rowid_to_rank.get(case_rowid_to_gravity_fk.get(cr, -1), 0) for cr in case_rowids), default=0,
        )
        label = 1 if (prior_case_count >= 2 or arrest_count >= 2 or max_gravity_rank == 1) else 0
        X.append([age, gender, prior_case_count, arrest_count, primary_role_count, max_gravity_rank])
        y.append(label)
    return X, y


def _get_model(zcql_service: Any) -> tuple[RandomForestClassifier, Any]:
    if _model_cache["model"] is None:
        X, y = _build_training_data(zcql_service)
        model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=43)
        model.fit(X, y)
        _model_cache["model"] = model
        _model_cache["explainer"] = shap.TreeExplainer(model)
    return _model_cache["model"], _model_cache["explainer"]


def predict_with_explanation(features: dict[str, Any], zcql_service: Any) -> dict[str, Any]:
    model, explainer = _get_model(zcql_service)
    x = np.array([[float(features[f]) for f in _FEATURE_ORDER]])

    predicted_class = int(model.predict(x)[0])
    proba = model.predict_proba(x)[0]
    risk_score = round(float(proba[1]), 4)

    shap_values = explainer.shap_values(x)
    # RandomForestClassifier binary case: shap_values is [class0_array, class1_array] or (n, features, 2) depending on shap version.
    class1_shap = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0, :, 1]
    top_features = sorted(
        (
            {"feature": name, "impact": round(float(val), 4)}
            for name, val in zip(_FEATURE_ORDER, class1_shap)
        ),
        key=lambda f: abs(f["impact"]), reverse=True,
    )[:3]

    counterfactual = None
    count_features = ["prior_case_count", "arrest_count", "primary_role_count", "max_gravity_rank"]
    for fname in count_features:
        idx = _FEATURE_ORDER.index(fname)
        if x[0][idx] <= 0:
            continue
        x_perturbed = x.copy()
        x_perturbed[0][idx] -= 1
        if int(model.predict(x_perturbed)[0]) != predicted_class:
            counterfactual = {
                "changed_feature": fname,
                "from_value": float(x[0][idx]),
                "to_value": float(x_perturbed[0][idx]),
                "resulting_predicted_class": int(model.predict(x_perturbed)[0]),
            }
            break

    return {
        "risk_score": risk_score,
        "predicted_class": predicted_class,
        "top_features": top_features,
        "counterfactual": counterfactual,
    }
