"""Saved pipeline templates."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from auth.deps import AnnotatedPrincipal

from auth.tiers import limits_for

from db.models import Template

from db.session import get_db

from engine.waterfall import StageConfig

from pydantic import BaseModel

from sqlalchemy.orm import Session


router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateUpsert(BaseModel):

    name: str

    description: str | None = None

    pipeline_config: list[StageConfig]

    universe: str = "sp500"

    direction: str = "long"

    max_stocks: int = 50


def serialize_template(r: Template) -> dict[str, Any]:

    return {

        "id": str(r.id),

        "name": r.name,

        "description": r.description,

        "universe": r.universe,

        "direction": r.direction,

        "max_stocks": r.max_stocks,

        "pipeline_config": r.pipeline_config,

    }


def _enforce_template_quota(db: Session, principal, creating: bool) -> None:

    lim = limits_for(principal.tier)

    if lim.templates_max is None:

        return

    cnt = db.query(Template).filter(Template.user_id == principal.user_id).count()

    if creating and cnt >= lim.templates_max:

        raise HTTPException(status_code=400, detail="Template quota reached — upgrade or delete")


@router.get("")

def list_templates(db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    if principal.user_id is None:

        return []

    rows = db.query(Template).filter(Template.user_id == principal.user_id).all()

    return [serialize_template(r) for r in rows]


@router.post("")

def create_template(payload: TemplateUpsert, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    if principal.user_id is None:

        raise HTTPException(status_code=400, detail="Authenticate to save templates")

    _enforce_template_quota(db, principal, True)

    row = Template(

        id=uuid.uuid4(),

        user_id=principal.user_id,

        name=payload.name,

        description=payload.description,

        pipeline_config=[s.model_dump() for s in payload.pipeline_config],

        universe=payload.universe,

        direction=payload.direction,

        max_stocks=payload.max_stocks,

    )

    db.add(row)

    db.commit()

    return {"id": str(row.id)}


@router.get("/{tid}")

def get_template(tid: uuid.UUID, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    tpl = db.get(Template, tid)

    if not tpl or tpl.user_id != principal.user_id:

        raise HTTPException(status_code=404)

    return serialize_template(tpl)


@router.put("/{tid}")

def put_template(tid: uuid.UUID, payload: TemplateUpsert, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    tpl = db.get(Template, tid)

    if not tpl or tpl.user_id != principal.user_id:

        raise HTTPException(status_code=404)

    tpl.name = payload.name

    tpl.description = payload.description

    tpl.pipeline_config = [s.model_dump() for s in payload.pipeline_config]

    tpl.universe = payload.universe

    tpl.direction = payload.direction

    tpl.max_stocks = payload.max_stocks

    db.commit()

    return {"ok": True}


@router.delete("/{tid}")

def del_template(tid: uuid.UUID, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    tpl = db.get(Template, tid)

    if not tpl or tpl.user_id != principal.user_id:

        raise HTTPException(status_code=404)

    db.delete(tpl)

    db.commit()

    return {"ok": True}
