/**
 * KSP Crime Intelligence — API Client
 *
 * Base URL: http://localhost:3000/server/datathon_2026_function
 * Auth: Catalyst auth token injected via request header once RBAC milestone
 *       is wired (Milestone 12). During dev with ALLOW_UNAUTHENTICATED=true
 *       on the function, the header is omitted and auth is skipped.
 *
 * Every JSON response (except PDF export, / and /cache) uses the envelope:
 *   { response_type, data, cited_case_ids, generated_sql,
 *     confidence_score, follow_up_questions }
 *
 * NOTE: POST /api/query returns HTTP 200 even on pipeline failure —
 *       always check data.error in the body, not just status code.
 *
 * Errors elsewhere: { error: "<message>" } with real HTTP status.
 * Handle 400/401/403/404/405/500 distinctly — do not collapse them.
 */

import axios from 'axios';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// In dev: Vite proxies /server/... → http://localhost:3000/server/...
// In prod: on Catalyst Slate, the SPA and function share the same origin.
// Override via VITE_API_BASE_URL env var only if you need absolute addressing.
export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  '/server/datathon_2026_function';

// ---------------------------------------------------------------------------
// Auth token store (set by auth layer once logged in)
// ---------------------------------------------------------------------------

let _authToken = null;

export function setAuthToken(token) {
  _authToken = token;
}

export function clearAuthToken() {
  _authToken = null;
}

export function getAuthToken() {
  return _authToken;
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000, // pipeline can be slow — 60s
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach auth token when available
client.interceptors.request.use((config) => {
  if (_authToken) {
    config.headers['Authorization'] = `Bearer ${_authToken}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — normalize errors
// ---------------------------------------------------------------------------

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      const message = data?.error || 'An unexpected error occurred';

      // Attach a typed error descriptor for consumers to branch on
      const typed = new ApiError(message, status, data);
      return Promise.reject(typed);
    }

    if (error.request) {
      // Network error — backend unreachable
      return Promise.reject(
        new ApiError('Backend unreachable — is catalyst serve running?', 0, null)
      );
    }

    return Promise.reject(new ApiError(error.message, -1, null));
  }
);

// ---------------------------------------------------------------------------
// ApiError — typed error class
// Consumers can switch on .status: 401 → prompt login, 403 → show RBAC lock,
// 404 → not found, 400 → bad input, 500 → server error, 0 → network down.
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(message, status, rawData) {
    super(message);
    this.name = 'ApiError';
    this.status = status;      // HTTP status code (0 = network unreachable)
    this.rawData = rawData;    // full response body if available
  }

  /** true if the user needs to log in */
  get isUnauthorized() { return this.status === 401; }

  /** true if the user's role lacks scope for this endpoint */
  get isForbidden() { return this.status === 403; }

  /** true if the requested resource doesn't exist */
  get isNotFound() { return this.status === 404; }

  /** true if the backend is completely unreachable */
  get isNetworkError() { return this.status === 0; }
}

// ---------------------------------------------------------------------------
// Endpoint helpers
// ---------------------------------------------------------------------------

/**
 * POST /api/query
 * Runs NL→SQL pipeline. Creates/continues a conversation session.
 * IMPORTANT: Returns HTTP 200 even on pipeline failure — check data.error.
 *
 * @param {string} question
 * @param {number|null} sessionId — pass on subsequent turns to continue thread
 * @returns {Promise<EnvelopeResponse>}
 */
export async function postQuery(question, sessionId = null) {
  const body = { question };
  if (sessionId != null) body.session_id = sessionId;

  const { data } = await client.post('/api/query', body);
  return data;
}

/**
 * GET /api/network/<case_id>
 * Returns response_type: "network" with graph data for the case.
 *
 * @param {number} caseId — must be a digit (backend 400s otherwise)
 */
export async function getNetwork(caseId) {
  assertDigit(caseId, 'caseId');
  const { data } = await client.get(`/api/network/${caseId}`);
  return data;
}

/**
 * GET /api/similar-cases/<case_id>
 * Returns response_type: "card", data.similar_cases: [{case_id, ...}]
 *
 * @param {number} caseId
 */
export async function getSimilarCases(caseId) {
  assertDigit(caseId, 'caseId');
  const { data } = await client.get(`/api/similar-cases/${caseId}`);
  return data;
}

/**
 * GET /api/entity-context/<accused_id>
 * Supervisor+ only. data.past_case_ids.
 *
 * @param {number} accusedId
 */
export async function getEntityContext(accusedId) {
  assertDigit(accusedId, 'accusedId');
  const { data } = await client.get(`/api/entity-context/${accusedId}`);
  return data;
}

/**
 * GET /api/risk-score/<accused_id>
 * Supervisor+ only. data.risk_score (mirrored into confidence_score).
 *
 * @param {number} accusedId
 */
export async function getRiskScore(accusedId) {
  assertDigit(accusedId, 'accusedId');
  const { data } = await client.get(`/api/risk-score/${accusedId}`);
  return data;
}

/**
 * GET /api/aggregates?type=<type>&date_from=&date_to=&crime_type=
 * Returns response_type: "chart". Invalid type → 400.
 *
 * @param {object} params — { type, date_from?, date_to?, crime_type? }
 */
export async function getAggregates(params = {}) {
  const { data } = await client.get('/api/aggregates', { params });
  return data;
}

/**
 * GET /api/hotspots?date_from=&date_to=&crime_type=
 * Returns response_type: "map", data.clusters: [{case_ids, ...}]
 *
 * @param {object} params — { date_from?, date_to?, crime_type? }
 */
export async function getHotspots(params = {}) {
  const { data } = await client.get('/api/hotspots', { params });
  return data;
}

/**
 * GET /api/financial-trail/<case_id>
 * Supervisor+ only.
 *
 * @param {number} caseId
 */
export async function getFinancialTrail(caseId) {
  assertDigit(caseId, 'caseId');
  const { data } = await client.get(`/api/financial-trail/${caseId}`);
  return data;
}

/**
 * GET /api/evidence/<case_id>
 * Returns response_type: "evidence", data.items.
 *
 * @param {number} caseId
 */
export async function getEvidence(caseId) {
  assertDigit(caseId, 'caseId');
  const { data } = await client.get(`/api/evidence/${caseId}`);
  return data;
}

/**
 * GET /api/conversation/<session_id>/export
 * Returns raw application/pdf bytes — NOT JSON.
 * Caller is responsible for creating a blob URL.
 *
 * @param {number} sessionId
 * @returns {Promise<Blob>}
 */
export async function exportConversation(sessionId) {
  assertDigit(sessionId, 'sessionId');
  const response = await client.get(
    `/api/conversation/${sessionId}/export`,
    { responseType: 'blob' }
  );
  return response.data; // Blob
}

/**
 * GET /
 * Health check — returns { status: "success" }
 */
export async function healthCheck() {
  const { data } = await client.get('/');
  return data;
}

// ---------------------------------------------------------------------------
// Internal guards
// ---------------------------------------------------------------------------

/**
 * Asserts that id is a digit (or digit string) to avoid the backend
 * 400-ing before auth is even checked.
 */
function assertDigit(id, name) {
  if (!/^\d+$/.test(String(id))) {
    throw new ApiError(
      `${name} must be a digit — received: ${id}`,
      400,
      null
    );
  }
}

// Export the raw client for any ad-hoc calls
export { client as apiClient };
