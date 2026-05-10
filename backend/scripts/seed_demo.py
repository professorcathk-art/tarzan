"""Seed synthetic OHLCV + fundamentals for local development."""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np

import pandas as pd

from sqlalchemy import text

from data.rs_calculator import compute_rs_scores

from data.universe import DEFAULT_SP500_SAMPLE, record_snapshot

from db.models import Base, Fundamentals, PriceHistory, SentimentScore

from db.session import SessionLocal

from db.session import engine


def _clear(db) -> None:

    for stmt in (
        "TRUNCATE TABLE universe_snapshots CASCADE",
        "TRUNCATE TABLE sentiment_scores CASCADE",
        "TRUNCATE TABLE fundamentals CASCADE",
        "TRUNCATE TABLE price_history CASCADE",
    ):

        db.execute(text(stmt))

    db.commit()


def _generate_prices(tickers: list[str], days: int = 290) -> pd.DataFrame:

    rng = np.random.default_rng(42)

    end = date.today()

    dts = pd.bdate_range(end=end, periods=days)

    rows: list[dict] = []

    spy_returns = rng.normal(0.0004, 0.01, size=len(dts))

    spy_level = 420.0

    for i, d in enumerate(dts):

        spy_level *= 1 + float(spy_returns[i])

        px = float(spy_level)

        vol = int(rng.integers(30_000_000, 120_000_000))

        hi = px * (1 + abs(rng.normal(0, 0.008)))

        lo = px * (1 - abs(rng.normal(0, 0.008)))

        op = float(rng.uniform(lo, hi))

        rows.append(
            {
                "ticker": "SPY",
                "date": d.date(),
                "open": op,
                "high": hi,
                "low": lo,
                "close": px,
                "adj_close": px,
                "volume": vol,
                "rs_score": None,
            }
        )

    for sym in tickers:

        if sym == "SPY":

            continue

        beta = float(rng.uniform(0.85, 1.25))

        lvl = float(rng.uniform(20, 520))

        noise = rng.normal(0.0005, 0.014, size=len(dts))

        for i, d in enumerate(dts):

            shock = beta * spy_returns[i] + float(noise[i])

            lvl *= 1 + shock

            c = float(max(2.0, lvl))

            rng_hl = abs(rng.normal(0, 0.012))

            hi = c * (1 + rng_hl)

            lo = c * (1 - rng_hl)

            op = float(rng.uniform(lo, hi))

            vol = int(rng.integers(200_000, 6_000_000))

            rows.append(
                {
                    "ticker": sym,
                    "date": d.date(),
                    "open": op,
                    "high": hi,
                    "low": lo,
                    "close": c,
                    "adj_close": c,
                    "volume": vol,
                    "rs_score": None,
                }
            )

    return pd.DataFrame(rows)


def seed(db, force: bool) -> None:

    exists = db.query(PriceHistory).first()

    if exists and not force:

        print("Database already has rows. Use --force to truncate and reseed.")

        return

    if force or exists:

        _clear(db)

    tickers = sorted({t.upper() for t in DEFAULT_SP500_SAMPLE if t.upper() != "SPY"})

    df = _generate_prices(["SPY", *tickers])

    for row in df.itertuples(index=False):

        db.add(
            PriceHistory(
                ticker=row.ticker,
                date=row.date,
                open=row.open,

                high=row.high,

                low=row.low,

                close=row.close,

                volume=row.volume,

                adj_close=row.adj_close,

                rs_score=row.rs_score,
            )
        )

    db.commit()

    panel = df[["ticker", "date", "adj_close"]].copy()


    panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()


    rs_long = compute_rs_scores(panel)


    cols = rs_long.columns.tolist()


    if "level_0" in cols:



        rs_long = rs_long.rename(columns={"level_0": "date", "level_1": "ticker"})



    elif len(cols) == 3:


        rs_long.columns = ["date", "ticker", "rs_score"]






    rs_long["date"] = pd.to_datetime(rs_long["date"]).dt.date




    for row in rs_long.itertuples(index=False):

        db.query(PriceHistory).filter(
            PriceHistory.ticker == row.ticker,

            PriceHistory.date == row.date,

        ).update({"rs_score": float(row.rs_score)}, synchronize_session=False)


    db.commit()

    asof = df["date"].max()

    rng = np.random.default_rng(7)

    for sym in tickers:

        mc = int(rng.integers(2_000_000_000, 900_000_000_000))

        ev = int(mc * float(rng.uniform(0.95, 1.2)))

        db.add(
            Fundamentals(
                ticker=sym,

                date=asof,

                pe_ratio=float(rng.uniform(8, 42)),

                eps=float(rng.uniform(0.5, 18)),

                revenue=int(rng.integers(200_000_000, 120_000_000_000)),

                market_cap=mc,

                roe=float(rng.uniform(5, 42)),

                debt_equity=float(rng.uniform(0.05, 1.8)),

                fcf_yield=float(rng.uniform(-1, 9)),

                peg_ratio=float(rng.uniform(0.4, 3.5)),

                roic=float(rng.uniform(4, 38)),

                ev=ev,

                ebit=float(rng.uniform(50_000_000, 40_000_000_000)),

                sector=("Technology" if sym[0] <= "M" else "Industrials"),

            )
        )

        db.add(
            SentimentScore(
                ticker=sym,
                date=asof,
                avg_sentiment=float(rng.uniform(-0.35, 0.65)),
                news_count=int(rng.integers(0, 18)),
                volume_spike=bool(rng.choice([True, False])),

                top_headlines=[
                    {"headline": f"{sym} guidance update", "score": 0.2, "source": "demo"},
                ],
            )
        )

    db.commit()

    record_snapshot(db, "sp500", tickers)

    alt = tickers.copy()

    if alt:

        alt[0] = "DEMO1"

    record_snapshot(db, "sp500", alt)

    print(f"Seeded {len(df)} price rows for {len(set(df.ticker)) - 1} names + SPY.")


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        seed(db, args.force)

    finally:

        db.close()


if __name__ == "__main__":

    main()
