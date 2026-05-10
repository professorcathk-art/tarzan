"""Universe diff snapshot endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from data.universe import latest_diff

from db.session import get_db

from sqlalchemy.orm import Session


router = APIRouter(prefix="/universe", tags=["universe"])


@router.get("/diff")

def universe_diff(universe_key: Annotated[str, Query(alias="key")], db: Annotated[Session, Depends(get_db)]):

    return latest_diff(db, universe_key)
