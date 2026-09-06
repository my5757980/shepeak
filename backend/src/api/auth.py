"""Authentication — verified claims only.

Prototype JWT: signed with a shared secret, carrying role + subject. The important property
is not the algorithm but the direction of trust: identity reaches the database ONLY from a
verified claim in this module. A client-supplied header or body field must never reach
`SET LOCAL`, or RLS is filtering on whatever the caller chose to say about themselves.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Header, HTTPException

SECRET = os.environ.get("SHEPEAK_JWT_SECRET", "dev-only-not-for-production").encode()
TTL_SECONDS = 12 * 3600


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue(role: str, subject_id: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"role": role, "sub": subject_id, "exp": int(time.time()) + TTL_SECONDS}
    signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(payload).encode())}"
    signature = hmac.new(SECRET, signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}"


def verify(token: str) -> dict[str, Any]:
    try:
        head_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise HTTPException(401, "Malformed token")

    expected = hmac.new(
        SECRET, f"{head_b64}.{payload_b64}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(expected, _unb64(sig_b64)):
        raise HTTPException(401, "Bad signature")

    claims = json.loads(_unb64(payload_b64))
    if claims.get("exp", 0) < time.time():
        raise HTTPException(401, "Token expired")
    return claims


def current_identity(authorization: str = Header(default="")):
    """FastAPI dependency. Returns the Identity that will be bound to the transaction."""
    from api.db import Identity

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    claims = verify(authorization.split(" ", 1)[1].strip())
    role, subject = claims.get("role"), claims.get("sub")
    if role == "athlete":
        return Identity(role="athlete", athlete_id=subject)
    if role == "coach":
        return Identity(role="coach", coach_id=subject)
    raise HTTPException(401, "Unknown role in token")
