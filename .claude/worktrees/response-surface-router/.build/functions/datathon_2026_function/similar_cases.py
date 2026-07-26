"""Phase 13 — Similar-Case Retrieval. GET /api/similar-cases/{case_id}:
ranks other cases by similarity to the given one, using BriefFacts text +
a couple of structured MO features (crime sub-head, gravity) blended in as
extra tokens.

Embedding approach: TF-IDF + cosine similarity (scikit-learn), computed
IN-MEMORY over the full CaseMaster corpus per request — not the NoSQL
CaseEmbedding cache table schema.md describes. At this dataset's scale
(2000 cases, short text) a full TF-IDF fit is comfortably sub-second, so
the cache table's rationale (avoid expensive recompute, CLAUDE.md) doesn't
bite yet.
ponytail: in-memory recompute + a module-level warm-instance cache
(_corpus_cache), no NoSQL. Upgrade to real CaseEmbedding NoSQL rows (per
schema.md Part 3) if the corpus grows past what a single Function
invocation can comfortably fetch+vectorize per request, or once QuickML
gets a confirmed embeddings endpoint worth swapping in.
"""

from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import zcql_util
from zcql_util import CaseNotFound

_corpus_cache: dict[str, Any] = {"case_ids": [], "texts": [], "matrix": None}


def _fetch_all_cases(zcql_service: Any) -> tuple[list[int], list[str]]:
    case_ids: list[int] = []
    texts: list[str] = []
    last_rowid = 0
    while True:
        rows = zcql_util.run(
            zcql_service,
            f"SELECT ROWID, CseMasterID, BriefFacts, CrimeMinorHeadID_FK, GravityOffenceID "
            f"FROM CaseMaster WHERE ROWID > {last_rowid} ORDER BY ROWID ASC LIMIT 200",
        )
        if not rows:
            break
        for r in rows:
            case_ids.append(int(r["CseMasterID"]))
            mo_tokens = f" crimehead_{r.get('CrimeMinorHeadID_FK', '')} gravity_{r.get('GravityOffenceID', '')}"
            texts.append((r.get("BriefFacts") or "") + mo_tokens)
            last_rowid = int(r["ROWID"])
    return case_ids, texts


def _get_corpus(zcql_service: Any) -> tuple[list[int], Any]:
    if _corpus_cache["matrix"] is None:
        case_ids, texts = _fetch_all_cases(zcql_service)
        vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        matrix = vectorizer.fit_transform(texts)
        _corpus_cache["case_ids"] = case_ids
        _corpus_cache["matrix"] = matrix
    return _corpus_cache["case_ids"], _corpus_cache["matrix"]


def find_similar_cases(case_id: int, zcql_service: Any, top_n: int = 5) -> list[dict[str, Any]]:
    case_check = zcql_util.run(zcql_service, f"SELECT CseMasterID FROM CaseMaster WHERE CseMasterID = {int(case_id)}")
    if not case_check:
        raise CaseNotFound(f"CaseMasterID {case_id} not found")

    case_ids, matrix = _get_corpus(zcql_service)
    if case_id not in case_ids:
        # Corpus cache is stale (case created after this Function instance
        # warmed up) — rebuild once rather than silently miss it.
        _corpus_cache["matrix"] = None
        case_ids, matrix = _get_corpus(zcql_service)
    if case_id not in case_ids:
        raise CaseNotFound(f"CaseMasterID {case_id} not found in corpus")

    idx = case_ids.index(case_id)
    similarities = cosine_similarity(matrix[idx], matrix).flatten()

    ranked = sorted(
        ((cid, float(score)) for cid, score in zip(case_ids, similarities) if cid != case_id),
        key=lambda x: x[1], reverse=True,
    )[:top_n]

    return [{"case_id": cid, "similarity": round(score, 4)} for cid, score in ranked]
