"""Email schedules (Pro)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from auth.deps import AnnotatedPrincipal

from auth.tiers import limits_for

from db.models import EmailLog, EmailSchedule

from db.session import get_db

from pydantic import BaseModel

from sqlalchemy.orm import Session


router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleBody(BaseModel):

    template_id: uuid.UUID

    frequency: str

    time_et: str

    days_of_week: list[int] | None = None


class SchedulePutBody(BaseModel):

    template_id: uuid.UUID | None = None

    frequency: str

    time_et: str

    days_of_week: list[int] | None = None


@router.post("")

def create_schedule(body: ScheduleBody, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    if principal.user_id is None:

        raise HTTPException(status_code=400, detail="Auth required")

    if not limits_for(principal.tier).schedules_ok:

        raise HTTPException(status_code=403, detail="Email schedules require Pro")

    row = EmailSchedule(

        id=uuid.uuid4(),

        template_id=body.template_id,

        user_id=principal.user_id,

        frequency=body.frequency,

        time_et=body.time_et,

        days_of_week=body.days_of_week,

    )

    db.add(row)

    db.commit()

    return {"id": str(row.id)}


@router.put("/{sid}")

def update_schedule(sid: uuid.UUID, body: SchedulePutBody, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    sch = db.get(EmailSchedule, sid)

    if not sch or sch.user_id != principal.user_id:

        raise HTTPException(status_code=404)

    if body.template_id is not None:

        sch.template_id = body.template_id

    sch.frequency = body.frequency

    sch.time_et = body.time_et

    sch.days_of_week = body.days_of_week

    db.commit()

    return {"ok": True}


@router.delete("/{sid}")

def delete_schedule(sid: uuid.UUID, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    sch = db.get(EmailSchedule, sid)

    if not sch or sch.user_id != principal.user_id:

        raise HTTPException(status_code=404)

    db.delete(sch)

    db.commit()

    return {"ok": True}


@router.get("/logs")

def logs(principal: AnnotatedPrincipal, db: Annotated[Session, Depends(get_db)], limit: int = 50) -> list[dict[str, Any]]:

    if principal.user_id is None:

        return []

    schedules = db.query(EmailSchedule).filter(EmailSchedule.user_id == principal.user_id).all()

    ids = [s.id for s in schedules]

    if not ids:

        return []

    items = db.query(EmailLog).filter(EmailLog.schedule_id.in_(ids)).limit(limit).all()

    return [

        {

            "id": str(it.id),

            "schedule_id": str(it.schedule_id) if it.schedule_id else None,

            "sent_at": str(it.sent_at) if it.sent_at else None,

            "status": it.status,

            "error_msg": it.error_msg,

        }

        for it in items

    ]
