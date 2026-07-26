"""SOS / 112 alert simulation — feeds the frontend's global notification
banner. Stateless by design (confirmed with the user): every call
independently fabricates 0-2 fresh alerts, no persistence, no schema.md
changes. There is no real 112 telephony integration here or ever — this is
a synthetic demo of "how fast can the system surface an emergency," same
spirit as CLAUDE.md's synthetic-data-only rule. Caller name/phone are
obviously-synthetic placeholders, never a real-looking dialable number.

No new dependency added for name generation — technical.md lists `faker`
but it isn't actually installed anywhere in this repo (checked); a small
hardcoded name pool is enough for this and keeps the deploy light.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

_FIRST_NAMES = ("Arjun", "Priya", "Ravi", "Lakshmi", "Suresh", "Kavya", "Manoj", "Deepa", "Vinay", "Anitha")
_LAST_NAMES = ("Gowda", "Rao", "Shetty", "Reddy", "Hegde", "Naik", "Kumar", "Patil")

_EMERGENCY_TYPES = (
    "Assault in progress", "Domestic violence", "Robbery in progress",
    "Road accident", "Medical emergency", "Fire reported", "Stalking / harassment",
    "Suspicious activity",
)

# Karnataka land bounds, same box aggregates.py::get_hotspots filters
# incident coordinates to — keeps fabricated alerts plausibly on-map.
_LAT_RANGE = (11.5, 18.55)
_LON_RANGE = (74.05, 78.55)

_MAX_ALERTS_PER_CALL = 2
_ALERT_PROBABILITY = 0.6  # per potential alert slot, not per call


def _synthetic_caller() -> tuple[str, str]:
    name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
    # Obviously-synthetic placeholder shape (never a real Indian mobile
    # prefix pattern) — flagged per CLAUDE.md, same spirit as "no
    # real-looking fake photos": don't present fabricated PII as real.
    phone = f"SIM-{random.randint(100000, 999999)}"
    return name, phone


def get_active_sos_alerts() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    alerts = []
    for _ in range(_MAX_ALERTS_PER_CALL):
        if random.random() > _ALERT_PROBABILITY:
            continue
        name, phone = _synthetic_caller()
        alerts.append({
            "emergency_type": random.choice(_EMERGENCY_TYPES),
            "caller_name": name,
            "caller_phone": phone,
            "lat": round(random.uniform(*_LAT_RANGE), 6),
            "lon": round(random.uniform(*_LON_RANGE), 6),
            "received_at": now.replace(microsecond=0).isoformat(),
        })
    return alerts


def _demo() -> None:
    """ponytail self-check: shape + bounds + count cap, deterministic seed."""
    random.seed(42)
    alerts = get_active_sos_alerts()
    assert len(alerts) <= _MAX_ALERTS_PER_CALL, alerts
    for a in alerts:
        assert a["emergency_type"] in _EMERGENCY_TYPES, a
        assert a["caller_phone"].startswith("SIM-"), a
        assert _LAT_RANGE[0] <= a["lat"] <= _LAT_RANGE[1], a
        assert _LON_RANGE[0] <= a["lon"] <= _LON_RANGE[1], a
        assert set(a.keys()) == {"emergency_type", "caller_name", "caller_phone", "lat", "lon", "received_at"}, a

    print("sos_alerts._demo: all assertions passed")


if __name__ == "__main__":
    _demo()
