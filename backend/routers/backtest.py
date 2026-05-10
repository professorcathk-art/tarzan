"""Backtest job APIs."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from auth.deps import AnnotatedPrincipal

from db.models import BacktestJob, BacktestResult

from db.session import SessionLocal, get_db

from engine.backtest import combo_hash, run_backtest_job

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session


router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRunBody(BaseModel):

    tickers: list[str] = Field(min_length=1, max_length=120)

    months: int = Field(12, ge=3, le=120)

    pipeline_stub: dict | None = None

    universe: str = "sp500"


def _run_job(job_id: uuid.UUID, tickers: list[str], months: int) -> None:

    sess = SessionLocal()

    try:

        run_backtest_job(sess, job_id, tickers, months)

    finally:

        sess.close()


@router.post("/run")

def enqueue_backtest(
    body: BacktestRunBody,
    principal: AnnotatedPrincipal,
    bg: BackgroundTasks,

    db: Annotated[Session, Depends(get_db)],
):

    job_id = uuid.uuid4()

    combo = combo_hash(body.pipeline_stub or [], body.universe, body.months)

    uid = getattr(principal, "user_id", None)

    db.add(BacktestJob(id=job_id, user_id=uid, combo_hash=combo, status="pending"))

    db.commit()

    bg.add_task(_run_job, job_id, [t.upper() for t in body.tickers], body.months)

    return {"job_id": str(job_id)}


@router.get("/{job_id}")

def get_backtest(job_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]):

    job = db.get(BacktestJob, job_id)

    if not job:

        raise HTTPException(status_code=404, detail="Job not found")

    res = db.query(BacktestResult).filter(BacktestResult.job_id == job_id).one_or_none()

    return {

        "status": job.status,

        "progress": job.progress,

        "error": job.error_msg,

        "metrics": None if res is None else res.metrics,

        "equity_curve": None if res is None else res.equity_curve,

    }
