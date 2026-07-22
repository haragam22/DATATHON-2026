"""Shared Catalyst SDK init for the Streamlit dev harness.

Local-only tool (not deployed to Catalyst) — uses the third-party/external
SDK init path (refresh-token credential), not zcatalyst_sdk.initialize(),
since that variant only works inside a running Catalyst Function.
"""
import os

import streamlit as st
import zcatalyst_sdk
from zcatalyst_sdk import credentials
from zcatalyst_sdk.types import ICatalystOptions

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

    cred = credentials.RefreshTokenCredential({
        "refresh_token": os.environ["CATALYST_REFRESH_TOKEN"],
        "client_id": os.environ["CATALYST_CLIENT_ID"],
        "client_secret": os.environ["CATALYST_CLIENT_SECRET"],
    })
    options = ICatalystOptions(
        project_id=os.environ["CATALYST_PROJECT_ID"],
        project_key=os.environ["CATALYST_PROJECT_KEY"],
        project_domain="https://api.catalyst.zoho.com",
        environment=os.environ["CATALYST_ENVIRONMENT"],
    )
    return zcatalyst_sdk.initialize_app(credential=cred, options=options, name="StreamlitHarness")
