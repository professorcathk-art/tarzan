"""JWT + optional demo auth."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

from config import get_settings


security = HTTPBearer(auto_error=False)


@dataclass
class Principal:

    user_id: uuid.UUID | None

    email: str | None

    tier: str


def principal_from_credentials(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> Principal:

    settings = get_settings()

    if settings.skip_auth:

        return Principal(user_id=None, email="demo@local", tier="pro")

    if creds is None or creds.scheme.lower() != "bearer":

        raise HTTPException(status_code=401, detail="Missing bearer token")

    secret = settings.supabase_jwt_secret

    if not secret:

        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not configured")

    try:

        payload = jwt.decode(
            creds.credentials,

            secret,

            algorithms=["HS256"],

            audience="authenticated",

            options={"verify_aud": False},
        )

    except JWTError:

        raise HTTPException(status_code=401, detail="Invalid token") from None

    sub = payload.get("sub")

    meta = payload.get("user_metadata") or {}

    app_meta = payload.get("app_metadata") or {}

    tier = meta.get("tier") or app_meta.get("tier") or "free"

    try:

        uid = uuid.UUID(str(sub))

    except Exception:

        raise HTTPException(status_code=401, detail="Malformed subject") from None

    return Principal(user_id=uid, email=payload.get("email"), tier=str(tier))


AnnotatedPrincipal = Annotated[Principal, Depends(principal_from_credentials)]
