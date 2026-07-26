import logging
import os

# Load functions/datathon_2026_function/.env (gitignored — QuickML/OAuth
# secrets, kept out of catalyst-config.json since that file is tracked and
# this repo is about to go public). Must run before `import zcatalyst_sdk`:
# the SDK reads CATALYST_ACCOUNTS_URL from the environment at import time.
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _value = _line.partition("=")
                os.environ.setdefault(_key.strip(), _value.strip())

from flask import Request, make_response, jsonify
import zcatalyst_sdk

from pipeline import run_query_pipeline
from network import build_case_network
from pcr_dispatch import get_active_dispatches
from sos_alerts import get_active_sos_alerts
from voice import VoiceError, transcribe
from similar_cases import find_similar_cases
from entity_context import get_entity_context
from risk_score import get_risk_score
from aggregates import InvalidAggregateType, get_aggregates, get_hotspots
from financial_trail import get_financial_trail
from evidence import backfill_evidence_stratus, get_evidence
from conversation import ConversationForbidden, SessionNotFound, export_conversation_pdf, get_or_create_session, log_message
from auth import AuthenticationRequired, ForbiddenScope, check_scope, resolve_app_user, write_audit_log
from zcql_util import CaseNotFound
'''
Execute below command to install SDK in global for enabling code suggestions
-> python3 -m pip install zcatalyst-sdk
'''

# (ExceptionType, HTTP status) pairs checked, in order, on top of the
# AuthenticationRequired/ForbiddenScope/CaseNotFound mapping every scoped
# route shares — lets one _run_scoped implementation serve every endpoint
# whose only per-route difference is which extra exception maps to 400.
_STANDARD_EXTRA_STATUS = ()


def _envelope(response_type, data, cited_case_ids=(), generated_sql="", confidence_score=1.0):
    return {
        "response_type": response_type,
        "data": data,
        "cited_case_ids": list(cited_case_ids),
        "generated_sql": generated_sql,
        "confidence_score": confidence_score,
        "follow_up_questions": [],
    }


def _run_scoped(app, logger, label, scope, work, extra_status=_STANDARD_EXTRA_STATUS):
    """Runs `work(zcql_service)` behind the auth+scope check every endpoint
    needs, and maps its result/exceptions to (status, json_body). `work`
    returns the JSON-able response body directly (already enveloped, or a
    raw dict for endpoints — like admin backfill — that don't use the
    envelope shape)."""
    try:
        zcql_service = app.zcql()
        check_scope(resolve_app_user(app, zcql_service), scope)
        return 200, work(zcql_service)
    except AuthenticationRequired as e:
        return 401, {"error": str(e)}
    except ForbiddenScope as e:
        return 403, {"error": str(e)}
    except CaseNotFound as e:
        return 404, {"error": str(e)}
    except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
        for exc_type, status in extra_status:
            if isinstance(e, exc_type):
                return status, {"error": str(e)}
        logger.error(f"{label} error: {e}")
        return 500, {"error": str(e)}


def handler(request: Request):
    app = zcatalyst_sdk.initialize(req=request)
    logger = logging.getLogger()
    path = request.path

    if path == "/":
        return make_response(jsonify({'status': 'success', 'message': 'Hello from main.py'}), 200)

    elif path == "/api/query":
        if request.method != "POST":
            return make_response(jsonify({"error": "POST only"}), 405)
        body = request.get_json(silent=True) or {}
        question = body.get("question", "").strip()
        if not question:
            return make_response(jsonify({"error": "missing 'question'"}), 400)
        try:
            zcql_service = app.zcql()
            app_user = resolve_app_user(app, zcql_service)
            check_scope(app_user, "query")
            session_id = get_or_create_session(app, zcql_service, app_user, body.get("session_id"))
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except ConversationForbidden as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except SessionNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        try:
            log_message(app, zcql_service, session_id, "user", question)
        except Exception as log_e:  # noqa: BLE001 — logged, never swallowed silently
            logger.error(f"/api/query conversation log write failed: {log_e}")
        try:
            envelope = run_query_pipeline(question, zcql_service)
        except Exception as e:  # noqa: BLE001 — api.js promises 200-always for this route, never an uncaught 500
            logger.error(f"/api/query pipeline error: {e}")
            try:
                write_audit_log(app, app_user, question, "", 0)
            except Exception as audit_e:  # noqa: BLE001 — logged, never swallowed silently
                logger.error(f"/api/query audit log write failed: {audit_e}")
            body = _envelope("text", {"error": str(e), "session_id": session_id}, confidence_score=0.0)
            return make_response(jsonify(body), 200)
        try:
            result_row_count = len(envelope.data.get("rows", []))
            write_audit_log(app, app_user, question, envelope.generated_sql, result_row_count)
        except Exception as audit_e:  # noqa: BLE001 — logged, never swallowed silently
            logger.error(f"/api/query audit log write failed: {audit_e}")
        try:
            log_message(
                app, zcql_service, session_id, "assistant", envelope.data.get("answer", ""),
                generated_sql=envelope.generated_sql, confidence_score=envelope.confidence_score,
                cited_case_ids=envelope.cited_case_ids,
            )
        except Exception as log_e:  # noqa: BLE001 — logged, never swallowed silently
            logger.error(f"/api/query conversation log write failed: {log_e}")
        envelope_dict = envelope.model_dump()
        envelope_dict["data"]["session_id"] = session_id
        return make_response(jsonify(envelope_dict), 200)

    elif path.startswith("/api/network/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)

        def work(zcql_service):
            graph_data = build_case_network(int(case_id_str), zcql_service)
            return _envelope("network", graph_data, graph_data["case_ids"])

        status, payload = _run_scoped(app, logger, "/api/network", "network", work)
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/similar-cases/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)

        def work(zcql_service):
            matches = find_similar_cases(int(case_id_str), zcql_service)
            return _envelope("card", {"similar_cases": matches}, [m["case_id"] for m in matches])

        status, payload = _run_scoped(app, logger, "/api/similar-cases", "similar-cases", work)
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/entity-context/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        accused_id_str = path.rsplit("/", 1)[-1]
        if not accused_id_str.isdigit():
            return make_response(jsonify({"error": "accused_id must be an integer"}), 400)

        def work(zcql_service):
            context = get_entity_context(int(accused_id_str), zcql_service)
            return _envelope("card", context, context["past_case_ids"])

        status, payload = _run_scoped(app, logger, "/api/entity-context", "entity-context", work)
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/risk-score/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        accused_id_str = path.rsplit("/", 1)[-1]
        if not accused_id_str.isdigit():
            return make_response(jsonify({"error": "accused_id must be an integer"}), 400)

        def work(zcql_service):
            result = get_risk_score(int(accused_id_str), zcql_service)
            return _envelope("card", result, confidence_score=result["risk_score"])

        status, payload = _run_scoped(app, logger, "/api/risk-score", "risk-score", work)
        return make_response(jsonify(payload), status)

    elif path == "/api/aggregates":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        agg_type = request.args.get("type")

        def work(zcql_service):
            data = get_aggregates(
                zcql_service, agg_type,
                request.args.get("date_from"), request.args.get("date_to"), request.args.get("crime_type"),
            )
            return _envelope("chart", data)

        status, payload = _run_scoped(
            app, logger, "/api/aggregates", "aggregates", work,
            extra_status=((InvalidAggregateType, 400),),
        )
        return make_response(jsonify(payload), status)

    elif path == "/api/hotspots":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)

        def work(zcql_service):
            data = get_hotspots(
                zcql_service,
                request.args.get("date_from"), request.args.get("date_to"), request.args.get("crime_type"),
            )
            cited = sorted({int(cid) for c in data.get("clusters", []) for cid in c.get("case_ids", [])})
            return _envelope("map", data, cited)

        status, payload = _run_scoped(app, logger, "/api/hotspots", "hotspots", work)
        return make_response(jsonify(payload), status)

    elif path == "/api/pcr-dispatch":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)

        def work(zcql_service):
            dispatches = get_active_dispatches(zcql_service)
            return _envelope("map", {"dispatches": dispatches}, [d["case_id"] for d in dispatches])

        status, payload = _run_scoped(app, logger, "/api/pcr-dispatch", "pcr-dispatch", work)
        return make_response(jsonify(payload), status)

    elif path == "/api/sos-alerts":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)

        def work(zcql_service):
            return _envelope("text", {"alerts": get_active_sos_alerts()})

        status, payload = _run_scoped(app, logger, "/api/sos-alerts", "sos-alerts", work)
        return make_response(jsonify(payload), status)

    elif path == "/api/voice/transcribe":
        if request.method != "POST":
            return make_response(jsonify({"error": "POST only"}), 405)
        audio_bytes = request.get_data()
        if not audio_bytes:
            return make_response(jsonify({"error": "missing audio body"}), 400)
        hint_language = request.args.get("language")  # optional "en" | "kn"

        def work(zcql_service):
            result = transcribe(audio_bytes, hint_language=hint_language)
            return _envelope("text", result)

        status, payload = _run_scoped(
            app, logger, "/api/voice/transcribe", "voice", work,
            extra_status=((VoiceError, 400),),
        )
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/financial-trail/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)

        def work(zcql_service):
            trail = get_financial_trail(int(case_id_str), zcql_service)
            return _envelope("card", trail, [int(case_id_str)])

        status, payload = _run_scoped(app, logger, "/api/financial-trail", "financial-trail", work)
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/evidence/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)

        def work(zcql_service):
            items = get_evidence(int(case_id_str), zcql_service)
            return _envelope("evidence", {"items": items}, [int(case_id_str)])

        status, payload = _run_scoped(app, logger, "/api/evidence", "evidence", work)
        return make_response(jsonify(payload), status)

    elif path == "/api/admin/backfill-evidence-stratus":
        if request.method != "POST":
            return make_response(jsonify({"error": "POST only"}), 405)

        def work(zcql_service):
            return backfill_evidence_stratus(app, zcql_service)

        status, payload = _run_scoped(app, logger, "/api/admin/backfill-evidence-stratus", "admin-backfill-evidence", work)
        return make_response(jsonify(payload), status)

    elif path.startswith("/api/conversation/") and path.endswith("/export"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        path_parts = path.split("/")
        session_id_str = path_parts[3] if len(path_parts) > 3 else ""
        if not session_id_str.isdigit():
            return make_response(jsonify({"error": "session_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            app_user = resolve_app_user(app, zcql_service)
            check_scope(app_user, "conversation-export")
            pdf_bytes = export_conversation_pdf(app, int(session_id_str), zcql_service, app_user)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except ConversationForbidden as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except SessionNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/conversation/export error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        response = make_response(pdf_bytes, 200)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=conversation_{session_id_str}.pdf"
        return response

    else:
        response = make_response('Unknown path')
        response.status_code = 400
        return response
