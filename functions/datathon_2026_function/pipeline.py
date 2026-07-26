"""POST /api/query orchestrator — Stage 1 (intent extraction) -> Stage 2
(verifier) -> schema-constrained SQL generation -> self-consistency check ->
execute -> post-execution sanity check -> answer generation -> entailment
check -> response envelope. Per technical.md's pipeline diagram and
CLAUDE.md's "these are mandatory pipeline steps, not optional" rule.

follow_up_questions is Phase 10 scope — envelope field exists (per the
agreed wire contract) but this module always returns it empty.
AuditLog writes are Phase 17 scope — not done here yet.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

import language
import quickml_client
import zcql_util
from schema_registry import (
    ADJACENT_TABLES, ALLOWED_SCHEMA, BOOLEAN_COLUMNS, FK_LABEL_TARGETS,
    render_relationships_for_prompt, render_schema_for_prompt,
)

_SCHEMA_TEXT = render_schema_for_prompt()
_RELATIONSHIPS_TEXT = render_relationships_for_prompt()

_MAX_PLAN_STEPS = 6

_FORBIDDEN_SQL_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE",
    "GRANT", "REVOKE", "--", "/*", ";",
)

_MAX_RESULT_ROWS = 500  # post-execution sanity bound, not a hard DB limit


class QueryIntent(BaseModel):
    entities: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    time_range: str | None = None
    aggregation: str | None = None


class QueryStep(BaseModel):
    table: str
    select: str  # a single column, or an aggregate like COUNT(CseMasterID)
    where: str = ""  # may reference {prev} for the previous step's ID list
    group_by: str = ""  # single column, only meaningful on the final step
    having: str = ""  # e.g. "COUNT(CseMasterID) > 5", only on the final step, requires group_by
    order_by: str = ""  # e.g. "COUNT(CseMasterID) DESC", only on the final step
    limit: int | None = None  # e.g. 5 for "top 5", only on the final step
    is_final: bool = False


class QueryEnvelope(BaseModel):
    response_type: Literal["card", "chart", "map", "network", "evidence", "text"]
    data: dict[str, Any]
    cited_case_ids: list[int] = Field(default_factory=list)
    generated_sql: str = ""
    confidence_score: float = 0.0
    follow_up_questions: list[str] = Field(default_factory=list)


class ClarificationNeeded(Exception):
    def __init__(self, question: str):
        self.question = question
        super().__init__(question)


class PipelineError(Exception):
    """Any stage failure that isn't a clarification request — surfaced to
    the caller as a 'text' envelope with confidence 0, never swallowed."""


def _extract_json_object(text: str) -> dict[str, Any]:
    """QuickML sometimes wraps JSON in prose despite instructions — pull
    out the first {...} block rather than trusting json.loads(text) raw."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise PipelineError(f"no JSON object found in QuickML output: {text!r}")
    return json.loads(match.group(0))


# ---------------------------------------------------------------------------
# Stage 1: Intent extraction
# ---------------------------------------------------------------------------

_INTENT_SYSTEM_PROMPT = (
    "Extract structured intent from a police-database natural language "
    "question. Respond with ONLY a JSON object, no prose, matching this "
    "shape exactly: "
    '{"entities": [<strings, e.g. case ids, names, districts, crime types>], '
    '"filters": {<key-value filter conditions>}, '
    '"time_range": <string or null>, '
    '"aggregation": <"count"|"sum"|"avg"|"list"|null>}'
)


def extract_intent(question: str) -> QueryIntent:
    raw = quickml_client.chat(
        [
            {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=400, temperature=0.2,
    )
    try:
        return QueryIntent.model_validate(_extract_json_object(raw))
    except (ValidationError, json.JSONDecodeError, PipelineError) as e:
        raise PipelineError(f"Stage 1 intent extraction failed: {e}") from e


# ---------------------------------------------------------------------------
# Stage 2: Verifier
# ---------------------------------------------------------------------------

_VERIFIER_SYSTEM_PROMPT = (
    "You check whether an extracted intent JSON actually matches the "
    "original question. If it matches well enough to answer confidently, "
    'respond with exactly: {"match": true}. '
    "If the question is ambiguous or the intent misses/misreads something "
    "important, respond with exactly: "
    '{"match": false, "clarifying_question": "<one short question to ask '
    'the user>"}. Respond with ONLY the JSON object, no prose.\n\n'
    "Examples:\n"
    'Question: "How many murder cases were registered in Ballari district '
    'in 2024?"\n'
    'Extracted intent: {"entities": ["Ballari", "Murder"], "filters": '
    '{"district": "Ballari", "crime_type": "Murder"}, "time_range": '
    '"2024", "aggregation": "count"}\n'
    'Response: {"match": true}\n'
    "(clear: every clause in the question — district, crime type, year, "
    "count — is captured, nothing left to guess)\n\n"
    'Question: "What happened with that case?"\n'
    'Extracted intent: {"entities": [], "filters": {}, "time_range": '
    'null, "aggregation": null}\n'
    'Response: {"match": false, "clarifying_question": "Which case are '
    'you asking about — do you have a Case ID or FIR number?"}\n'
    "(genuinely ambiguous: \"that case\" has no antecedent and the intent "
    "correctly extracted nothing to act on)\n"
)


def verify_intent(question: str, intent: QueryIntent) -> None:
    """Raises ClarificationNeeded if the intent doesn't match well enough —
    CLAUDE.md: ambiguous intent must trigger a clarifying question, never a
    silent best-guess pick."""
    raw = quickml_client.chat(
        [
            {"role": "system", "content": _VERIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Question: {question}\nExtracted intent: {intent.model_dump_json()}"
            )},
        ],
        max_tokens=200, temperature=0.0,
    )
    try:
        result = _extract_json_object(raw)
    except (json.JSONDecodeError, PipelineError) as e:
        raise PipelineError(f"Stage 2 verifier failed: {e}") from e
    if not result.get("match", False):
        raise ClarificationNeeded(
            result.get("clarifying_question", "Could you clarify your question?")
        )


# ---------------------------------------------------------------------------
# Schema-constrained query PLAN generation + guard
#
# ZCQL's JOIN requires a declared relationship between the FK column and the
# parent table's PK (docs/zcql.md's JOIN section) — confirmed live: EVERY
# tested _FK-named column (including textbook ones like
# Accused.CaseMasterID_FK -> CaseMaster) fails with "No relationship between
# tables X and Y", because this schema's _FK columns are plain integers from
# CSV import, never declared as a real relationship/Lookup-type column. ZCQL
# JOIN is therefore unusable on THIS schema, not on ZCQL in general — if a
# future schema fix ever adds real relationship-typed FK columns (see
# docs/schema.md's already-fixed CaseStatusID_FK bug), this ban must be
# re-verified live before trusting it's still true, not assumed permanent.
# Cross-table filtering instead happens as a chain of single-table SELECTs
# in Python — same batched, no-N+1 pattern already used in network.py —
# with each step's WHERE clause referencing the previous step's result IDs
# via a literal {prev} substitution, never a nested SELECT: confirmed live
# as 'Nested Sub query is not supported' on this project's ZCQL version.
# docs/zcql.md DOES document WHERE-clause subqueries as a ZCQL V2 feature —
# so this project is most likely pinned to ZCQL V1, and the ban is a
# version limitation, not a permanent ZCQL restriction; re-verify if the
# project ever migrates to V2, since validate_plan's blanket "no SELECT
# inside a step" check would then be wrongly rejecting legal V2 syntax.
# ---------------------------------------------------------------------------

_PLAN_SYSTEM_PROMPT = (
    "Generate a JSON query PLAN that answers the question, using ONLY "
    "these tables and columns, no others:\n\n"
    f"{_SCHEMA_TEXT}\n\n"
    "The plan is a JSON object: "
    '{"steps": [{"table": <name>, "select": <single column, or an '
    'aggregate like COUNT(CseMasterID)>, "where": <condition string, or '
    '"">, "group_by": <single column, or "", only meaningful on the final '
    'step>, "having": <aggregate condition on the group, e.g. '
    '"COUNT(CseMasterID) > 5", or "" -- only on the final step, and only '
    'when group_by is also set>, "order_by": <e.g. "COUNT(CseMasterID) '
    'DESC", or "", only on the final step>, "limit": <int or null, only on '
    'the final step>, "is_final": <bool>}, ...]}\n\n'
    "Use having for questions filtering ON the aggregate itself (e.g. "
    "\"districts with more than 5 cases\"), never in where -- where can "
    "only filter raw rows before grouping. Example for \"police stations "
    "with more than 10 cases\": "
    '{"steps": [{"table": "CaseMaster", "select": '
    '"PoliceStationID_FK, COUNT(CseMasterID)", "where": "", "group_by": '
    '"PoliceStationID_FK", "having": "COUNT(CseMasterID) > 10", '
    '"is_final": true}]}\n\n'
    "For 'top N' / 'most common' / 'hotspot' questions that need a count "
    "per group, use group_by on the grouping column, order_by the "
    "aggregate descending, and limit N — all on the final step only. "
    "Example for \"top 3 police stations by number of cases\": "
    '{"steps": [{"table": "CaseMaster", "select": '
    '"PoliceStationID_FK, COUNT(CseMasterID)", "where": "", "group_by": '
    '"PoliceStationID_FK", "order_by": "COUNT(CseMasterID) DESC", "limit": '
    '3, "is_final": true}]}\n\n'
    "Rules, all confirmed against real API behavior, not hypothetical:\n"
    "- NO JOIN keyword anywhere — this database's foreign-key columns are "
    "plain integers, not real relationships, so JOIN always fails.\n"
    "- NO nested SELECT anywhere in a where clause — always fails.\n"
    "- NO '*' inside an aggregate function — write COUNT(CseMasterID), "
    "never COUNT(*).\n"
    "- To filter across tables, write ONE step per table, in dependency "
    "order (the table with the literal filter value first). Every step "
    "after the first should reference the placeholder {prev} in its where "
    "clause to mean 'the ROWID values returned by the immediately preceding "
    "step', e.g. \"DistrictID_FK IN ({prev})\". The step selecting {prev}'s "
    "source should select ROWID.\n"
    "- If the final step must combine filters from TWO SEPARATE, unrelated "
    "chains (e.g. filter by district AND by a specific offence name), do "
    "NOT try to fit both into one {prev} — write each chain as its own "
    "steps, then reference each chain's last step by its 0-based index: "
    "{prev0} means step 0's results, {prev1} means step 1's results, etc. "
    "{prev} alone always means the step directly above. Worked example for "
    "\"murder cases in Ballari district\":\n"
    '{"steps": ['
    '{"table": "District", "select": "ROWID", '
    '"where": "DistrictName = \'Ballari\'", "is_final": false}, '
    '{"table": "Unit", "select": "ROWID", '
    '"where": "DistrictID_FK IN ({prev})", "is_final": false}, '
    '{"table": "CrimeSubHead", "select": "ROWID", '
    '"where": "CrimeHeadName = \'Murder\'", "is_final": false}, '
    '{"table": "CaseMaster", "select": "COUNT(CseMasterID)", '
    '"where": "PoliceStationID_FK IN ({prev1}) AND CrimeMinorHeadID_FK IN ({prev2})", "is_final": true}'
    "]}\n"
    "- Only these table pairs may be chained this way (the FK actually "
    "points from the first to the second):\n\n"
    f"{_RELATIONSHIPS_TEXT}\n\n"
    "- Exactly one step must have is_final=true — it must be a query "
    "against the table that actually answers the question (usually "
    "CaseMaster), and comes last.\n"
    "- Keep the plan to as few steps as the question actually needs — "
    "most questions need only 1-3 steps.\n"
    "- CaseMaster has NO DistrictID_FK column. To filter cases by "
    "district, you MUST go through Unit (CaseMaster.PoliceStationID_FK is "
    "a Unit ROWID, and Unit.DistrictID_FK is a District ROWID) — never "
    "join District straight to CaseMaster, that FK doesn't exist. Worked "
    "example for \"cases in Ballari district\":\n"
    '{"steps": ['
    '{"table": "District", "select": "ROWID", '
    '"where": "DistrictName LIKE \'%Ballari%\'", "is_final": false}, '
    '{"table": "Unit", "select": "ROWID", '
    '"where": "DistrictID_FK IN ({prev})", "is_final": false}, '
    '{"table": "CaseMaster", "select": "CseMasterID", '
    '"where": "PoliceStationID_FK IN ({prev})", "is_final": true}'
    "]}\n"
    "- CRITICAL FK TYPE RULE: All columns ending in _FK or ID (e.g. "
    "DistrictID_FK, PoliceStationID_FK, StateID_FK, CrimeMinorHeadID_FK, ROWID) "
    "are BIGINT INTEGERS. NEVER compare an _FK or ID column to a string literal "
    "(e.g. NEVER write DistrictID_FK = 'Bengaluru' or DistrictID_FK LIKE '%bengaluru%'). "
    "String filters must ONLY target string columns (e.g. District.DistrictName, "
    "CrimeSubHead.CrimeHeadName, Unit.UnitName).\n"
    "- ZCQL LIKE wildcards are '*' (zero or more chars) and '?' (exactly one "
    "char) — NOT SQL's '%' or '_'. '%' is a literal character in ZCQL, so "
    "'%bengaluru%' matches nothing. For district/city queries (e.g. "
    "'Bengaluru', 'Mysuru'), filter District table using DistrictName LIKE "
    "'*Bengaluru*' in step 0, then filter Unit on DistrictID_FK IN ({prev}) "
    "in step 1.\n"
    "Specific offence names (Murder, Robbery, Theft, NDPS, Dacoity, etc.) "
    "are in CrimeSubHead.CrimeHeadName — NOT CrimeHead.CrimeGroupName, "
    "which only holds broad categories like 'Crimes Against Body'. A "
    "question naming a specific offence must filter CrimeSubHead."
    "CrimeHeadName, joining to CaseMaster via CrimeMinorHeadID_FK.\n"
    "- DATE/DATETIME literals must be quoted strings in 'YYYY-MM-DD' form "
    "(e.g. CrimeRegisteredDate >= '2024-01-01' AND CrimeRegisteredDate <= "
    "'2024-12-31'). Never use a bare year number or a function call. "
    "Worked example for \"murder cases registered in 2024\":\n"
    '{"steps": ['
    '{"table": "CrimeSubHead", "select": "ROWID", '
    '"where": "CrimeHeadName = \'Murder\'", "is_final": false}, '
    '{"table": "CaseMaster", "select": "CseMasterID", '
    '"where": "CrimeMinorHeadID_FK IN ({prev}) AND CrimeRegisteredDate >= '
    '\'2024-01-01\' AND CrimeRegisteredDate <= \'2024-12-31\'", '
    '"is_final": true}'
    "]}\n"
    "- BOOLEAN columns (e.g. IsOutdoor, IsAccused, IsComplainantAccused, "
    "Active) only support = and != — never LIKE, BETWEEN, IN, <, >, <=, "
    ">= on a boolean column. Compare to bare unquoted TRUE or FALSE, never "
    "a quoted string or 1/0, e.g. \"IsOutdoor = TRUE\".\n"
    "- If a string literal itself contains an apostrophe (e.g. a name "
    "like O'Brien), double it inside the literal: 'O''Brien', never a "
    "single unescaped quote — a lone apostrophe breaks the literal.\n"
    "Respond with ONLY the JSON object, no prose, no markdown fences."
)


class QueryPlan(BaseModel):
    steps: list[QueryStep]


def _generate_plan_once(question: str, intent: QueryIntent, feedback: str | None = None) -> QueryPlan:
    user_content = f"Question: {question}\nIntent: {intent.model_dump_json()}"
    if feedback:
        user_content += f"\n\nYour previous plan was rejected: {feedback}\nFix it and try again."
    raw = quickml_client.chat(
        [
            {"role": "system", "content": _PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=500, temperature=0.1,
    )
    try:
        plan = QueryPlan.model_validate(_extract_json_object(raw))
    except (ValidationError, json.JSONDecodeError, PipelineError) as e:
        raise PipelineError(f"plan generation produced invalid JSON: {e}") from e
    if not plan.steps:
        raise PipelineError("generated plan has zero steps")
    return plan


def _generate_valid_plan(question: str, intent: QueryIntent) -> QueryPlan:
    """One generation attempt, plus one repair retry with the validation
    error fed back to the model — LLMs reliably produce a structurally
    valid plan that still skips a required intermediate JOIN hop on the
    first try (confirmed live), so a single blind retry recovers most of
    those without a human in the loop."""
    plan = _generate_plan_once(question, intent)
    try:
        validate_plan(plan)
        return plan
    except PipelineError as first_error:
        plan = _generate_plan_once(question, intent, feedback=str(first_error))
        validate_plan(plan)  # let this raise straight through if still invalid
        return plan


def _normalize_plan(plan: QueryPlan) -> str:
    return json.dumps([s.model_dump() for s in plan.steps], sort_keys=True)


def _render_step_sql(step: QueryStep, where: str) -> str:
    sql = f"SELECT {step.select} FROM {step.table}"
    if where:
        sql += f" WHERE {where}"
    if step.group_by:
        sql += f" GROUP BY {step.group_by}"
    if step.having:
        sql += f" HAVING {step.having}"
    if step.order_by:
        sql += f" ORDER BY {step.order_by}"
    if step.limit is not None:
        sql += f" LIMIT {step.limit}"
    return sql


def render_plan_as_sql(plan: QueryPlan) -> str:
    """Debug-friendly rendering for the envelope's generated_sql field —
    not itself executable as one statement, just a readable trace."""
    return "; ".join(_render_step_sql(s, s.where) for s in plan.steps)


def validate_plan(plan: QueryPlan) -> None:
    """Schema-constrained guard over the plan, not a raw SQL string.
    Column-level checking is best-effort (aggregate-wrapped select isn't
    unwrapped and checked) since a real SQL parser isn't in this project's
    dependency set yet.
    ponytail: best-effort column check, upgrade to sqlparse/sqlglot-based
    parsing if adversarial-input testing (Phase 22) finds a bypass."""
    if len(plan.steps) > _MAX_PLAN_STEPS:
        raise PipelineError(f"plan has {len(plan.steps)} steps, exceeds max {_MAX_PLAN_STEPS}")

    final_count = sum(1 for s in plan.steps if s.is_final)
    if final_count != 1 or not plan.steps[-1].is_final:
        raise PipelineError(f"plan must have exactly one is_final step, as the last step: {plan.steps!r}")

    # A step is either a fresh anchor (a literal-value filter, no {prev} —
    # legal at ANY position, since the final step may fan in several
    # independent chains that each start fresh) or a continuation (must
    # name which specific prior non-final step it continues via {prev} or
    # {prevN}, and must be FK-adjacent to THAT step's table specifically —
    # not just "any table seen so far", which would let unrelated chains
    # falsely validate each other).
    for i, step in enumerate(plan.steps):
        if step.table not in ALLOWED_SCHEMA:
            raise PipelineError(f"plan step {i} references unknown table {step.table!r}")
        if not step.is_final and (step.group_by or step.having or step.order_by or step.limit is not None):
            raise PipelineError(
                f"plan step {i} sets group_by/having/order_by/limit but isn't the final step: {step!r}"
            )
        if step.having and not step.group_by:
            raise PipelineError(f"plan step {i} sets having without group_by — HAVING requires GROUP BY: {step!r}")
        combined = f"{step.select} {step.where} {step.having}".upper()
        for kw in _FORBIDDEN_SQL_KEYWORDS:
            if kw in combined:
                raise PipelineError(f"plan step {i} contains forbidden token {kw!r}: {step!r}")
        if "SELECT" in combined:
            raise PipelineError(f"plan step {i} contains a nested SELECT, unsupported by ZCQL: {step!r}")
        if re.search(r"\w+\(\s*\*\s*\)", combined):
            raise PipelineError(f"plan step {i} uses '*' inside an aggregate function: {step!r}")

        # Guard: Check for invalid comparisons between ID/FK columns and string literals.
        # Foreign key & ID columns in ZCQL schema are BIGINT integers.
        # Comparing an ID/FK column (e.g. DistrictID_FK, PoliceStationID_FK) to a quoted string
        # (e.g. DistrictID_FK = 'Bengaluru') causes ZCQL status 400 error.
        fk_match = re.search(r"\b(\w*(?:ID|_FK))\s*(?:=|LIKE|IN|\!=|<|>)\s*['\"]([^'\"]*)['\"]", step.where, re.IGNORECASE)
        if fk_match:
            col_name, str_val = fk_match.group(1), fk_match.group(2)
            if not str_val.isdigit():
                raise PipelineError(
                    f"plan step {i} ({step.table}) compares integer ID/FK column {col_name!r} to string literal {str_val!r}. "
                    f"Foreign key and ID columns are numeric BIGINTs. String filters must target string text columns "
                    f"(e.g. District.DistrictName, CrimeSubHead.CrimeHeadName, Unit.UnitName), never ID or _FK columns."
                )

        # Guard: BOOLEAN columns only support = and != in ZCQL, compared to
        # bare TRUE/FALSE (docs/zcql.md's boolean exceptions table) — the
        # prompt states this but nothing else enforced it, so a slip here
        # previously only surfaced as an unexplained live 400 with no
        # repair retry (execute_plan has none for post-validation failures).
        for bool_col in BOOLEAN_COLUMNS.get(step.table, set()):
            op_match = re.search(
                rf"\b{re.escape(bool_col)}\b\s*(!=|=|<=|>=|<|>|LIKE|IN|BETWEEN)",
                step.where, re.IGNORECASE,
            )
            if not op_match:
                continue
            op = op_match.group(1).upper()
            if op not in ("=", "!="):
                raise PipelineError(
                    f"plan step {i} ({step.table}) uses operator {op!r} on BOOLEAN column {bool_col!r} — "
                    f"ZCQL only supports = and != for BOOLEAN columns, never LIKE/BETWEEN/IN/</>/<=/>=."
                )
            rest = step.where[op_match.end():].strip()
            value_token = rest.split()[0].rstrip(",)") if rest else ""
            if value_token.upper() not in ("TRUE", "FALSE"):
                raise PipelineError(
                    f"plan step {i} ({step.table}) compares BOOLEAN column {bool_col!r} to {value_token!r} — "
                    f"must be bare unquoted TRUE or FALSE, never a quoted string or 1/0."
                )

        # Guard: an odd number of single quotes outside recognized
        # 'literal' spans means an unescaped apostrophe broke a string
        # literal mid-value (e.g. a name like O'Brien) — ZCQL's own docs
        # don't document an escape convention, so this is caught here
        # rather than reaching ZCQL as a malformed-query 400.
        if "'" in re.sub(r"'[^']*'", "", step.where):
            raise PipelineError(
                f"plan step {i} ({step.table}) has an unmatched/unescaped single quote in a string literal: "
                f"{step.where!r}. Double any apostrophe inside a literal (e.g. O'Brien -> O''Brien)."
            )

        refs = re.findall(r"\{PREV(\d*)\}", combined)
        if not refs:
            continue  # fresh anchor step — no prior-step dependency to check
        for raw_ref in refs:
            ref_i = i - 1 if raw_ref == "" else int(raw_ref)
            if ref_i < 0 or ref_i >= i or plan.steps[ref_i].is_final:
                raise PipelineError(f"plan step {i} references invalid prior step {{prev{raw_ref}}}: {step!r}")
            ref_table = plan.steps[ref_i].table
            if ref_table not in ADJACENT_TABLES.get(step.table, set()):
                raise PipelineError(
                    f"plan step {i} ({step.table!r}) has no direct FK path from step {ref_i} ({ref_table!r}): {step!r}"
                )


def generate_plan_with_self_consistency(question: str, intent: QueryIntent) -> tuple[QueryPlan, bool]:
    """Generates the plan twice (each with its own repair retry, see
    _generate_valid_plan) and diffs (CLAUDE.md: self-consistency check is
    mandatory, not optional). Returns (plan_to_use, consistent)."""
    candidates: list[QueryPlan | None] = []
    errors: list[PipelineError | None] = []
    for _ in range(2):
        try:
            candidates.append(_generate_valid_plan(question, intent))
            errors.append(None)
        except PipelineError as e:
            candidates.append(None)
            errors.append(e)
    first, second = candidates

    if first is None and second is None:
        raise PipelineError(f"both self-consistency plan candidates failed validation: {errors[0]} / {errors[1]}")
    if first is None:
        return second, False
    if second is None:
        return first, False

    consistent = _normalize_plan(first) == _normalize_plan(second)
    return first, consistent


# ---------------------------------------------------------------------------
# Execute + post-execution sanity check
# ---------------------------------------------------------------------------

def _resolve_fk_labels(zcql_service: Any, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replaces raw FK integer values in final rows with the target table's
    display label (e.g. CaseStatusID_FK 53418... -> "Under Investigation"),
    via one batched single-table lookup per FK column present in the rows —
    no JOIN needed, same zcql_util.run pattern used everywhere else."""
    if not rows:
        return rows
    for col in list(rows[0].keys()):
        target = FK_LABEL_TARGETS.get((table, col))
        if not target:
            continue
        target_table, target_pk, label_col = target
        ids = sorted({str(r[col]) for r in rows if r.get(col) is not None})
        if not ids:
            continue
        lookup_sql = f"SELECT {target_pk}, {label_col} FROM {target_table} WHERE {target_pk} IN ({', '.join(ids)})"
        try:
            lookup_rows = zcql_util.run(zcql_service, lookup_sql)
        except zcql_util.ZcqlError:
            continue  # label resolution is best-effort — keep raw ID rather than fail the whole answer
        labels = {str(lr[target_pk]): lr[label_col] for lr in lookup_rows if target_pk in lr and label_col in lr}
        for r in rows:
            if col in r and str(r[col]) in labels:
                r[col] = labels[str(r[col])]
    return rows


def execute_plan(zcql_service: Any, plan: QueryPlan) -> list[dict[str, Any]]:
    # step_ids[i] holds step i's resolved ID list once it runs (only
    # populated for non-final steps). {prev} means "the immediately
    # preceding step"; {prevN} references step N by index directly — needed
    # when the final step must combine results from two independent chains
    # (e.g. a district->unit chain and an unrelated offence-name chain) that
    # a single overwritten {prev} variable can't hold at once.
    step_ids: dict[int, list[int]] = {}
    final_rows: list[dict[str, Any]] = []
    last_non_final: list[int] = []
    for i, step in enumerate(plan.steps):
        where = re.sub(
            r"\{prev(\d*)\}",
            lambda m: zcql_util.in_clause(
                (step_ids.get(int(m.group(1)), last_non_final) if m.group(1) else last_non_final) or [0]
            ),
            step.where,
        )
        sql = _render_step_sql(step, where)
        try:
            rows = zcql_util.run(zcql_service, sql)
        except zcql_util.ZcqlError as e:
            raise PipelineError(f"plan step against {step.table!r} failed: {e} (sql={sql!r})") from e
        if step.is_final:
            final_rows = _resolve_fk_labels(zcql_service, step.table, rows)
        else:
            select_col = step.select.strip()
            ids = [int(r[select_col]) for r in rows if select_col in r]
            # If an intermediate step (e.g. District filter) matches 0 records,
            # downstream dependent steps cannot match anything — short-circuit early.
            if not ids:
                return []
            step_ids[i] = ids
            last_non_final = ids
    return final_rows


def sanity_check_results(rows: list[dict[str, Any]], intent: QueryIntent) -> float:
    """Post-execution sanity check (mandatory per CLAUDE.md): validates
    result shape against expected bounds. Returns a confidence contribution
    in [0, 1] rather than a bool — an aggregation returning many rows or a
    plain listing returning zero rows are suspicious, not automatically
    fatal, so they lower confidence instead of hard-failing the pipeline."""
    if intent.aggregation in ("count", "sum", "avg") and len(rows) > 1:
        return 0.5
    if len(rows) > _MAX_RESULT_ROWS:
        return 0.5
    if len(rows) == 0:
        return 0.7
    return 1.0


# ---------------------------------------------------------------------------
# Answer generation + entailment check
# ---------------------------------------------------------------------------

_ANSWER_SYSTEM_PROMPT = (
    "Answer the user's question in one or two sentences, using ONLY the "
    "facts present in the provided result rows (JSON). Do not state "
    "anything not directly supported by the rows. If the rows are empty, "
    "say no matching records were found."
)

_ENTAILMENT_SYSTEM_PROMPT = (
    "Check whether every factual claim in the given answer is directly "
    "supported by the given result rows (JSON). Respond with ONLY a JSON "
    'object: {"entailed": true} if every claim is supported, or '
    '{"entailed": false, "reason": "<short reason>"} otherwise.'
)


def generate_answer(question: str, rows: list[dict[str, Any]]) -> str:
    rows_json = json.dumps(rows[:50])  # cap prompt size, not a result-count limit
    return quickml_client.chat(
        [
            {"role": "system", "content": _ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\nRows: {rows_json}"},
        ],
        max_tokens=300, temperature=0.3,
    ).strip()


def entailment_check(answer: str, rows: list[dict[str, Any]]) -> bool:
    rows_json = json.dumps(rows[:50])
    raw = quickml_client.chat(
        [
            {"role": "system", "content": _ENTAILMENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Answer: {answer}\nRows: {rows_json}"},
        ],
        max_tokens=150, temperature=0.0,
    )
    try:
        return bool(_extract_json_object(raw).get("entailed", False))
    except (json.JSONDecodeError, PipelineError):
        return False  # can't confirm entailment -> treat as failed, not passed


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_query_pipeline(raw_question: str, zcql_service: Any) -> QueryEnvelope:
    """raw_question is whatever the user typed — English, Kannada, or
    code-switched. Phase 18: detected+translated to English once here,
    ahead of Stage 1, per backend_ultraplan.md ("a preprocessing addition
    in front of /api/query, not a new pipeline") — every stage below still
    operates in English; only the final answer (and a clarifying question,
    if one is needed) gets translated back for a Kannada/mixed-language
    caller, since the user asked for Kannada-in/Kannada-out symmetry."""
    question, detected_language = language.preprocess_question(raw_question)

    intent = extract_intent(question)

    try:
        verify_intent(question, intent)
    except ClarificationNeeded as c:
        clarifying_question = language.postprocess_answer(c.question, detected_language)
        return QueryEnvelope(
            response_type="text",
            data={"clarifying_question": clarifying_question, "language": detected_language},
            confidence_score=0.0,
        )

    plan, consistent = generate_plan_with_self_consistency(question, intent)
    validate_plan(plan)  # re-validate the chosen candidate, not just both branches above

    rows = execute_plan(zcql_service, plan)
    sanity_confidence = sanity_check_results(rows, intent)

    answer = generate_answer(question, rows)
    entailed = entailment_check(answer, rows)
    if not entailed:
        # One retry with an explicit "stick to the rows" nudge, per
        # CLAUDE.md's entailment-must-pass-before-reaching-user rule.
        answer = generate_answer(
            question + " (Answer using ONLY the exact values in the rows, nothing else.)", rows,
        )
        entailed = entailment_check(answer, rows)

    answer = language.postprocess_answer(answer, detected_language)

    confidence = sanity_confidence * (1.0 if consistent else 0.6) * (1.0 if entailed else 0.4)

    cited_case_ids = sorted({
        int(r["CseMasterID"]) for r in rows if "CseMasterID" in r and str(r["CseMasterID"]).isdigit()
    })

    return QueryEnvelope(
        response_type="card" if rows else "text",
        data={"answer": answer, "rows": rows[:_MAX_RESULT_ROWS], "language": detected_language},
        cited_case_ids=cited_case_ids,
        generated_sql=render_plan_as_sql(plan),
        confidence_score=round(confidence, 3),
    )
