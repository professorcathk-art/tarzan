"""Screening endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

import pandas as pd

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from auth.deps import AnnotatedPrincipal, Principal

from auth.tiers import enforce_screen

from data.frame_builder import build_universe_dataframe

from data.universe import get_universe_tickers

from db.models import BacktestJob, ScreenRun, User

from db.session import SessionLocal, get_db

from engine.backtest import combo_hash as bt_combo_hash

from engine.backtest import run_backtest_job

from engine.waterfall import StageConfig, VotingEngine, WaterfallEngine

from pydantic import BaseModel, Field

from services.price_status import last_trade_date

from sqlalchemy.orm import Session


router = APIRouter(prefix="/screen", tags=["screen"])


def _merged_table_from_snaps(snaps: list) -> list | None:

    for block in reversed(snaps):

        if isinstance(block, dict) and "merged_table" in block:

            return block["merged_table"]

    return None


class ScreenRunPayload(BaseModel):
    pipeline_mode: Literal["waterfall", "voting"] = "waterfall"

    universe: str = "sp500"

    stages: list[StageConfig]

    direction: str = "long"

    max_results: int = Field(50, ge=1, le=500)

    backtest_months: int | None = Field(default=None)

    enqueue_backtest: bool = False


def _principal_user_id(principal: Principal, db: Session) -> uuid.UUID | None:
    if principal.user_id is not None:
        return principal.user_id

    if principal.email == "demo@local":
        demo = db.query(User).filter(User.email == principal.email).one_or_none()

        if demo:

            return demo.id

        u = User(id=uuid.uuid4(), email=principal.email, tier="pro")

        db.add(u)

        db.commit()

        return u.id

    return None


def _launch_backtest_job(job_id: uuid.UUID, tickers: list[str], months: int) -> None:

    sess = SessionLocal()

    try:

        run_backtest_job(sess, job_id, tickers, months)

    finally:

        sess.close()


@router.post("/run")

def run_screen(
    bg: BackgroundTasks,
    payload: ScreenRunPayload,

    db: Annotated[Session, Depends(get_db)],

    principal: AnnotatedPrincipal,
):

    try:

        enforce_screen(payload.stages, payload.universe, principal.tier)

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e)) from e

    tickers = get_universe_tickers(payload.universe)

    frame = build_universe_dataframe(db, tickers)

    if frame.empty:

        raise HTTPException(status_code=400, detail="Unable to assemble universe frame — seed demo data.")

    stages = sorted(payload.stages, key=lambda s: s.order)

    if payload.pipeline_mode == "voting":

        result = VotingEngine().run(stages, frame)

    else:

        result = WaterfallEngine().run(stages, frame)

    merged: list[dict] = []

    for _, row in result.final_df.iterrows():

        tk = str(row["ticker"])

        merged.append(
            {
                "ticker": tk,
                "company": tk,
                "sector": row.get("sector"),

                "price": float(pd.to_numeric(row.get("close"), errors="coerce") or 0),

                "rs": float(pd.to_numeric(row.get("rs_score"), errors="coerce") or 0),

                "sentiment": float(pd.to_numeric(row.get("news_sentiment_score"), errors="coerce") or 0),

                "score": float(pd.to_numeric(row.get("score"), errors="coerce") or 0),

                "reason_summary": result.merged_reasons.get(tk, ""),
            }
        )

    merged.sort(key=lambda r: -r["score"])

    merged = merged[: payload.max_results]

    run_id = uuid.uuid4()

    uid = _principal_user_id(principal, db)

    snaps = [*result.stage_snapshots, {"warnings": result.warnings}, {"merged_table": merged}]

    db.add(
        ScreenRun(
            id=run_id,
            template_id=None,
            user_id=uid,
            stage_snapshots=snaps,
            final_tickers=[m["ticker"] for m in merged],

        )

    )

    db.commit()

    last_dt = last_trade_date(db)

    stale_banner = None

    if last_dt:

        stale_days = (pd.Timestamp.today().normalize() - pd.Timestamp(last_dt)).days

        if stale_days > 4:

            stale_banner = f"Price snapshot may be stale (last DB date {last_dt})."

    warnings = list(result.warnings)

    if stale_banner:

        warnings.append(stale_banner)

    backtest_job_id: str | None = None

    if payload.enqueue_backtest and merged:

        months_raw = payload.backtest_months

        months_used = int(months_raw) if months_raw is not None else (6 if principal.tier == "free" else 36)

        bt_uuid = uuid.uuid4()

        backtest_job_id = str(bt_uuid)

        combo = bt_combo_hash([s.model_dump() for s in stages], payload.universe, months_used)

        db.add(BacktestJob(id=bt_uuid, user_id=uid, combo_hash=combo, status="pending"))

        db.commit()

        tickers_bt = [m["ticker"] for m in merged][: min(48, payload.max_results)]

        bg.add_task(_launch_backtest_job, bt_uuid, tickers_bt, months_used)

    return {
        "run_id": str(run_id),
        "warnings": warnings,

        "data_stale_banner": stale_banner,

        "merged_table": merged,

        "snapshots": result.stage_snapshots,

        "backtest_job_id": backtest_job_id,
    }


@router.get("/{run_id}")

def fetch_run(run_id: uuid.UUID, db: Annotated[Session, Depends(get_db)], principal: AnnotatedPrincipal):

    row = db.get(ScreenRun, run_id)

    if not row:

        raise HTTPException(status_code=404, detail="Run not found")

    snaps = row.stage_snapshots or []

    merged_table = _merged_table_from_snaps(snaps)



    fallback = [{"ticker": t} for t in (row.final_tickers or [])]


    merged_table_final = merged_table if merged_table is not None else fallback


    _ = principal

    return {


        "run_id": str(row.id),



        "snapshots": snaps,



        "final_tickers": row.final_tickers or [],



        "merged_table": merged_table_final,



    }

