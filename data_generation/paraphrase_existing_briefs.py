"""One-off UPDATE-in-place pass: paraphrases BriefFacts for the 2000
CaseMaster rows that were generated (and imported) before Phase 4's
QuickML paraphrase call existed. Does NOT insert new rows — reads existing
ROWIDs, paraphrases, UPDATEs. Uses raw REST (requests) for both OAuth and
ZCQL, not zcatalyst_sdk — the SDK's RefreshTokenCredential token exchange
fails to parse the accounts.zoho.in response in this environment even
though the identical raw request works; not worth debugging further for a
one-off local script (production Functions use a different, unaffected
internal auth path via zcatalyst_sdk.initialize()).

Resumable: persists the last completed ROWID to a cursor file after every
batch, so a crash/interrupt (confirmed twice — Zoho's token endpoint threw
transient 400/401s under this session's heavy testing load) picks back up
instead of re-paraphrasing rows already done.

Run: python -m data_generation.paraphrase_existing_briefs
"""

from __future__ import annotations

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "streamlit_harness", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_generation.generators import narratives  # noqa: E402

ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/token"
QUERY_URL = f"https://api.catalyst.zoho.in/baas/v1/project/{os.environ['CATALYST_PROJECT_ID']}/query"
CURSOR_PATH = os.path.join(os.path.dirname(__file__), ".paraphrase_cursor")

_token_cache = {"access_token": "", "expires_at": 0.0}


def _with_retry(fn, attempts: int = 5, base_delay: float = 5.0):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (requests.exceptions.RequestException, RuntimeError) as e:
            last_error = e
            if attempt < attempts:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"[paraphrase_existing] transient error (attempt {attempt}/{attempts}): {e} — retrying in {delay:.0f}s", flush=True)
                time.sleep(delay)
    raise last_error


def _access_token() -> str:
    if time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    def _do_refresh():
        resp = requests.post(ACCOUNTS_URL, data={
            "refresh_token": os.environ["CATALYST_REFRESH_TOKEN"],
            "client_id": os.environ["CATALYST_CLIENT_ID"],
            "client_secret": os.environ["CATALYST_CLIENT_SECRET"],
            "grant_type": "refresh_token",
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()

    body = _with_retry(_do_refresh)
    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = time.time() + body.get("expires_in", 3600) - 60
    return body["access_token"]


def zcql(query: str) -> list[dict]:
    def _do_query():
        resp = requests.post(
            QUERY_URL,
            json={"query": query},
            headers={
                "Authorization": f"Zoho-oauthtoken {_access_token()}",
                "CATALYST-ORG": os.environ["CATALYST_ORG_ID"],
                "Environment": os.environ["CATALYST_ENVIRONMENT"],
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        body = resp.json()
        if body.get("status") != "success":
            raise RuntimeError(f"ZCQL failed: {body}")
        return body["data"]

    data = _with_retry(_do_query)
    return [next(iter(row.values())) for row in data]


def _escape(text: str) -> str:
    return text.replace("'", "''")


def _load_cursor() -> int:
    if os.path.exists(CURSOR_PATH):
        with open(CURSOR_PATH) as f:
            return int(f.read().strip() or 0)
    return 0


def _save_cursor(rowid: int) -> None:
    with open(CURSOR_PATH, "w") as f:
        f.write(str(rowid))


def main() -> None:
    updated = 0
    failed = 0
    last_rowid = _load_cursor()
    if last_rowid:
        print(f"[paraphrase_existing] resuming from cursor ROWID {last_rowid}", flush=True)
    while True:
        rows = zcql(
            f"SELECT ROWID, BriefFacts FROM CaseMaster WHERE ROWID > {last_rowid} "
            f"ORDER BY ROWID ASC LIMIT 200"
        )
        if not rows:
            break
        for row in rows:
            rowid = int(row["ROWID"])
            original = row["BriefFacts"]
            try:
                paraphrased = narratives.paraphrase_brief_facts(original)
                if paraphrased != original:
                    zcql(f"UPDATE CaseMaster SET BriefFacts = '{_escape(paraphrased)}' WHERE ROWID = {rowid}")
                updated += 1
            except Exception as e:  # noqa: BLE001 — logged explicitly, loop continues
                failed += 1
                print(f"[paraphrase_existing] ROWID {rowid} failed: {e}", flush=True)
            last_rowid = rowid
            _save_cursor(last_rowid)
            if updated % 25 == 0:
                print(f"[paraphrase_existing] progress: {updated} updated, {failed} failed, last_rowid={last_rowid}", flush=True)

    print(f"[paraphrase_existing] DONE: {updated} updated, {failed} failed", flush=True)
    os.remove(CURSOR_PATH)


if __name__ == "__main__":
    main()
