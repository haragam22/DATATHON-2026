import logging
from flask import Request, make_response, jsonify
import zcatalyst_sdk

from pipeline import PipelineError, run_query_pipeline
from network import build_case_network
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

def handler(request: Request):
    app = zcatalyst_sdk.initialize(req=request)
    logger = logging.getLogger()
    if request.path == "/":
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Hello from main.py'
        }), 200)
        return response
    elif request.path == "/api/query":
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
        except PipelineError as e:
            logger.error(f"/api/query pipeline error: {e}")
            try:
                write_audit_log(app, app_user, question, "", 0)
            except Exception as audit_e:  # noqa: BLE001 — logged, never swallowed silently
                logger.error(f"/api/query audit log write failed: {audit_e}")
            return make_response(jsonify({
                "response_type": "text",
                "data": {"error": str(e), "session_id": session_id},
                "cited_case_ids": [],
                "generated_sql": "",
                "confidence_score": 0.0,
                "follow_up_questions": [],
            }), 200)
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
    elif request.path.startswith("/api/network/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = request.path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "network")
            graph_data = build_case_network(int(case_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/network error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "network",
            "data": graph_data,
            "cited_case_ids": graph_data["case_ids"],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path.startswith("/api/similar-cases/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = request.path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "similar-cases")
            matches = find_similar_cases(int(case_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/similar-cases error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "card",
            "data": {"similar_cases": matches},
            "cited_case_ids": [m["case_id"] for m in matches],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path.startswith("/api/entity-context/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        accused_id_str = request.path.rsplit("/", 1)[-1]
        if not accused_id_str.isdigit():
            return make_response(jsonify({"error": "accused_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "entity-context")
            context = get_entity_context(int(accused_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/entity-context error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "card",
            "data": context,
            "cited_case_ids": context["past_case_ids"],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path.startswith("/api/risk-score/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        accused_id_str = request.path.rsplit("/", 1)[-1]
        if not accused_id_str.isdigit():
            return make_response(jsonify({"error": "accused_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "risk-score")
            result = get_risk_score(int(accused_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/risk-score error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "card",
            "data": result,
            "cited_case_ids": [],
            "generated_sql": "",
            "confidence_score": result["risk_score"],
            "follow_up_questions": [],
        }), 200)
    elif request.path == "/api/aggregates":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        agg_type = request.args.get("type")
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "aggregates")
            data = get_aggregates(
                zcql_service, agg_type,
                request.args.get("date_from"), request.args.get("date_to"), request.args.get("crime_type"),
            )
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except InvalidAggregateType as e:
            return make_response(jsonify({"error": str(e)}), 400)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/aggregates error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "chart",
            "data": data,
            "cited_case_ids": [],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path == "/api/hotspots":
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "hotspots")
            data = get_hotspots(
                zcql_service,
                request.args.get("date_from"), request.args.get("date_to"), request.args.get("crime_type"),
            )
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/hotspots error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "map",
            "data": data,
            "cited_case_ids": sorted({cid for c in data["clusters"] for cid in c["case_ids"]}),
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path.startswith("/api/financial-trail/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = request.path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "financial-trail")
            trail = get_financial_trail(int(case_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/financial-trail error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "card",
            "data": trail,
            "cited_case_ids": [int(case_id_str)],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path.startswith("/api/evidence/"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        case_id_str = request.path.rsplit("/", 1)[-1]
        if not case_id_str.isdigit():
            return make_response(jsonify({"error": "case_id must be an integer"}), 400)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "evidence")
            items = get_evidence(int(case_id_str), zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except CaseNotFound as e:
            return make_response(jsonify({"error": str(e)}), 404)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/evidence error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify({
            "response_type": "evidence",
            "data": {"items": items},
            "cited_case_ids": [int(case_id_str)],
            "generated_sql": "",
            "confidence_score": 1.0,
            "follow_up_questions": [],
        }), 200)
    elif request.path == "/api/admin/backfill-evidence-stratus":
        if request.method != "POST":
            return make_response(jsonify({"error": "POST only"}), 405)
        try:
            zcql_service = app.zcql()
            check_scope(resolve_app_user(app, zcql_service), "admin-backfill-evidence")
            result = backfill_evidence_stratus(app, zcql_service)
        except AuthenticationRequired as e:
            return make_response(jsonify({"error": str(e)}), 401)
        except ForbiddenScope as e:
            return make_response(jsonify({"error": str(e)}), 403)
        except Exception as e:  # noqa: BLE001 — surfaced to the caller, not swallowed
            logger.error(f"/api/admin/backfill-evidence-stratus error: {e}")
            return make_response(jsonify({"error": str(e)}), 500)
        return make_response(jsonify(result), 200)
    elif request.path.startswith("/api/conversation/") and request.path.endswith("/export"):
        if request.method != "GET":
            return make_response(jsonify({"error": "GET only"}), 405)
        session_id_str = request.path.split("/")[3] if len(request.path.split("/")) > 3 else ""
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
    elif request.path == "/cache":
        default_segment = app.cache().segment()

        insert_resp = default_segment.put('Name', 'DefaultName')
        logger.info('Inserted cache : ' + str(insert_resp))
        get_resp = default_segment.get('Name')

        return jsonify(get_resp), 200
    else:
        response = make_response('Unknown path')
        response.status_code = 400
        return response
