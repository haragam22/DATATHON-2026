"""Shared Catalyst SDK init for the Streamlit dev harness.

Local-only tool (not deployed to Catalyst) — uses the third-party/external
SDK init path (refresh-token credential), not zcatalyst_sdk.initialize(),
since that variant only works inside a running Catalyst Function.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Must run before `import zcatalyst_sdk` — the SDK reads
# X_ZOHO_CATALYST_ACCOUNTS_URL at import time (_constants.py), not lazily,
# so loading .env any later (e.g. in app.py) is too late and it silently
# defaults to the unreachable accounts.localzoho.com placeholder.
# Explicit path (not bare load_dotenv()) — that searches upward from cwd,
# so it silently finds nothing if `streamlit run` is launched from repo
# root instead of from inside streamlit_harness/.
load_dotenv(Path(__file__).resolve().parent / ".env")

import streamlit as st
import zcatalyst_sdk
from zcatalyst_sdk import credentials
from zcatalyst_sdk.types import ICatalystOptions

# zcatalyst_sdk==1.4.0's HttpClient.request builds urls as
# f"{base_url}/{path}" where `path` already starts with "/" — every request
# (incl. the oauth token exchange) ends up as e.g.
# "https://accounts.zoho.in//oauth/v2/token". accounts.localzoho.com (the
# unset-env default) never surfaced this, since DNS/SSL failed first; once
# pointed at the real accounts.zoho.in host, that double slash 404s with an
# HTML error page, which the SDK then chokes on trying to .json() it
# (surfaces as opaque "UNPARSABLE_RESPONSE"). Patched here instead of
# editing site-packages so it survives a `pip install -r requirements.txt`.
import requests as _requests

_orig_session_request = _requests.Session.request


def _dedupe_double_slash_request(self, method, url, *args, **kwargs):
    scheme_sep = "://"
    if scheme_sep in url:
        scheme, rest = url.split(scheme_sep, 1)
        while "//" in rest:
            rest = rest.replace("//", "/")
        url = f"{scheme}{scheme_sep}{rest}"
    return _orig_session_request(self, method, url, *args, **kwargs)


_requests.Session.request = _dedupe_double_slash_request

REQUIRED_ENV = [
    "CATALYST_REFRESH_TOKEN",
    "CATALYST_CLIENT_ID",
    "CATALYST_CLIENT_SECRET",
    "CATALYST_PROJECT_ID",
    "CATALYST_PROJECT_KEY",
    "CATALYST_ENVIRONMENT",
]


@st.cache_resource(show_spinner=False)
def get_app():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)}. Copy .env.example to .env and fill in."
        )

    # zcatalyst_sdk hardcodes ACCOUNTS_URL to the placeholder
    # https://accounts.localzoho.com unless this exact env var is set
    # (confirmed in the installed package's _constants.py — not documented
    # anywhere) — every RefreshTokenCredential call silently tries to reach
    # a nonexistent host and hangs/SSL-fails without it.
    os.environ.setdefault(
        "X_ZOHO_CATALYST_ACCOUNTS_URL",
        os.environ.get("CATALYST_ACCOUNTS_URL", "https://accounts.zoho.in"),
    )

    cred = credentials.RefreshTokenCredential({
        "refresh_token": os.environ["CATALYST_REFRESH_TOKEN"],
        "client_id": os.environ["CATALYST_CLIENT_ID"],
        "client_secret": os.environ["CATALYST_CLIENT_SECRET"],
    })
    options = ICatalystOptions(
        project_id=os.environ["CATALYST_PROJECT_ID"],
        project_key=os.environ["CATALYST_PROJECT_KEY"],
        # This project's data center is .in (confirmed via accounts.zoho.in
        # token exchange working, api.catalyst.zoho.in in QUICKML_ENDPOINT_URL)
        # — hardcoded .com here would silently fail auth. Overridable via env
        # in case a future project lands on a different DC.
        project_domain=os.environ.get("CATALYST_PROJECT_DOMAIN", "https://api.catalyst.zoho.in"),
        environment=os.environ["CATALYST_ENVIRONMENT"],
    )
    return zcatalyst_sdk.initialize_app(credential=cred, options=options, name="StreamlitHarness")
