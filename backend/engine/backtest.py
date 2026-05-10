"""Simplified vectorized-style backtest using weekly rebalance rules from the spec."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from db.models import BacktestJob, BacktestResult, PriceHistory


def combo_hash(pipeline: list[dict], universe: str, months: int) -> str:
    blob = json.dumps({"p": pipeline, "u": universe, "m": months}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:64]


def _load_prices(db: Session, tickers: list[str]) -> pd.DataFrame:
    rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.ticker.in_(tickers))
        .order_by(PriceHistory.ticker, PriceHistory.date)
        .all()
    )
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "ticker": r.ticker,
                "date": pd.Timestamp(r.date),
                "close": float(r.adj_close or r.close or 0),
            }
            for r in rows
        ]
    )


def _spy_series(db: Session) -> pd.Series:
    rows = db.query(PriceHistory).filter(PriceHistory.ticker == "SPY").order_by(PriceHistory.date).all()
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(r.date): float(r.adj_close or r.close or 0) for r in rows})
    return s.sort_index()


def run_backtest_job(db: Session, job_id: uuid.UUID, tickers: list[str], months: int = 12) -> None:
    job = db.get(BacktestJob, job_id)
    if not job:
        return

    job.status = "running"
    job.progress = 10
    db.commit()

    try:
        px = _load_prices(db, tickers + ["SPY"])
        if px.empty:
            raise RuntimeError("No price history available for backtest.")

        pivot = px.pivot(index="date", columns="ticker", values="close").sort_index().ffill()

        end = pivot.index.max()
        start = end - pd.DateOffset(months=months)
        pivot = pivot[pivot.index >= start]
        spy = _spy_series(db)
        spy = spy.reindex(pivot.index).ffill().pct_change().fillna(0)

        rebal = pivot.resample("W-FRI").last().index
        port_ret = []
        bench_ret = []
        active = [t for t in tickers if t in pivot.columns]

        if not active:
            raise RuntimeError("No overlapping tickers in price matrix.")

        for i in range(1, len(rebal)):
            dt = rebal[i]
            prev = rebal[i - 1]
            window = pivot.loc[prev:dt]
            if len(window) < 2:
                continue
            wret = window[active].pct_change().iloc[1:].mean(axis=1).fillna(0)
            period = float((1 + wret).prod() - 1)
            port_ret.append(period)

            bw = spy.loc[prev:dt]
            period_b = float((1 + bw.iloc[1:]).prod() - 1)
            bench_ret.append(period_b)

        arr = np.array(port_ret, dtype=float)
        arr_b = np.array(bench_ret, dtype=float)

        equity = np.cumprod(1 + arr)
        bench_equity = np.cumprod(1 + arr_b)

        total_return = float(equity[-1] - 1) if len(equity) else 0.0

        rf = float(np.std(arr) * math.sqrt(52)) + 1e-9 if len(arr) else 1e-9
        sharpe = float((np.mean(arr) * 52) / rf) if len(arr) else 0.0

        roll_max = np.maximum.accumulate(equity) if len(equity) else np.array([1.0])
        dd = float(np.min((equity / roll_max) - 1)) if len(equity) else 0.0

        metrics = {
            "total_return_pct": total_return * 100,
            "cagr_pct": ((1 + total_return) ** (12 / max(months, 1)) - 1) * 100 if months else 0,
            "sharpe": sharpe,
            "max_drawdown_pct": dd * 100,
            "win_rate_pct": float(np.mean(arr > 0) * 100) if len(arr) else 0,
            "avg_holding_weeks": 1.0,
            "benchmark_total_return_pct": float(bench_equity[-1] - 1) * 100 if len(bench_equity) else 0,
            "note": "Simplified weekly rebalance on static input list — illustration only.",
        }

        equity_curve = [
            {"week": i, "portfolio": float(equity[i]), "benchmark": float(bench_equity[i])} for i in range(len(equity))
        ]

        db.add(
            BacktestResult(
                id=uuid.uuid4(),
                job_id=job_id,
                combo_hash=job.combo_hash,
                metrics=metrics,
                equity_curve=equity_curve,
                monthly_returns=[{"week": i, "port": float(arr[i]), "bench": float(arr_b[i])} for i in range(len(arr))][
                    :200
                ],
                run_at=datetime.utcnow(),
            )
        )

        job.status = "completed"
        job.progress = 100
        db.commit()
    except Exception as e:  # noqa: BLE001
        job.status = "failed"
        job.error_msg = str(e)
        job.progress = 100
        db.commit()
