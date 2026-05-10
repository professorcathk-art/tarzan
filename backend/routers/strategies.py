"""Strategy catalogue endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from strategies.registry import list_metadata


router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def catalogue():

    return list_metadata()
