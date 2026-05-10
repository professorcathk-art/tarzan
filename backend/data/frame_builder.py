"""Cross-section loader: builds per-ticker features from panel OHLCV in DB."""

from __future__ import annotations

from datetime import date
from typing import Sequence

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from db.models import Fundamentals, PriceHistory, SentimentScore


def _sma(series: pd.Series, n: int) -> float:
    s = series.dropna().tail(n)
    if len(s) < max(5, n // 4):
        return float(np.nan)
    return float(s.mean())


def _slope(series: pd.Series, n: int) -> float:
    s = series.dropna().tail(n)
    if len(s) < 5:
        return 0.0
    y = np.arange(len(s))
    x = np.arange(len(s))
    coef = np.polyfit(x, s.values.astype(float), 1)
    return float(coef[0])


def _max_1d_drop(high: pd.Series, low: pd.Series, window: int) -> float:
    if len(high) < 2:
        return 0.0
    h = high.tail(window)
    l = low.tail(window)
    prev = h.shift(1)
    dd = (l - prev) / prev
    return float(dd.min()) if dd.notna().any() else 0.0


def build_universe_dataframe(
    db: Session,
    tickers: Sequence[str],
    asof: date | None = None,
) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()

    tlist = list({t.upper() for t in tickers})
    px = (
        db.query(PriceHistory)
        .filter(PriceHistory.ticker.in_(tlist))
        .order_by(PriceHistory.ticker, PriceHistory.date)
        .all()
    )
    if not px:
        return pd.DataFrame({"ticker": tlist})

    pdf = pd.DataFrame(
        [
            {
                "ticker": p.ticker,
                "date": p.date,
                "open": float(p.open or 0) or np.nan,
                "high": float(p.high or 0) or np.nan,
                "low": float(p.low or 0) or np.nan,
                "close": float(p.close or p.adj_close or 0) or np.nan,
                "volume": int(p.volume or 0),
                "adj_close": float(p.adj_close or p.close or 0) or np.nan,
                "rs_score": float(p.rs_score) if p.rs_score is not None else np.nan,
            }
            for p in px
        ]
    )

    pdf["date"] = pd.to_datetime(pdf["date"]).dt.normalize()
    if asof is not None:
        pdf = pdf[pdf["date"] <= pd.Timestamp(asof)]

    rows: list[dict] = []
    for tic, g in pdf.groupby("ticker"):
        g = g.sort_values("date").reset_index(drop=True)
        row: dict[str, float | str | bool | int | None] = {"ticker": tic}

        pc = pd.to_numeric(g["close"], errors="coerce")
        pv = pd.to_numeric(g["volume"], errors="coerce")
        ph = pd.to_numeric(g["high"], errors="coerce")
        pl = pd.to_numeric(g["low"], errors="coerce")

        if pc.isna().all() or len(pc) == 0:
            rows.append(row)
            continue

        row["close"] = float(pc.iloc[-1])
        row["volume"] = float(pv.iloc[-1])
        row["open"] = float(pd.to_numeric(g["open"], errors="coerce").iloc[-1])
        row["high"] = float(ph.iloc[-1])
        row["low"] = float(pl.iloc[-1])

        row["sma_50"] = _sma(pc, 50)
        row["sma_150"] = _sma(pc, 150)
        row["sma_200"] = _sma(pc, 200)
        row["ma200_slope_30"] = _slope(pc.rolling(200).mean().dropna(), 30)

        win252 = min(252, len(pc))
        row["high_252"] = float(ph.tail(win252).max())
        row["low_252"] = float(pl.tail(win252).min())

        for w in (20, 30, 40, 60):
            span = ph.tail(w) - pl.tail(w)
            row[f"range_{w}"] = float(span.mean()) if len(span) else np.nan

        row["avg_vol_50"] = float(pv.tail(50).mean()) if len(pv) else np.nan
        row["avg_vol_20"] = float(pv.tail(20).mean()) if len(pv) else np.nan

        row["max_1d_drop_4w"] = abs(_max_1d_drop(ph, pl, 20))

        rs = pd.to_numeric(g["rs_score"], errors="coerce").dropna()
        row["rs_score"] = float(rs.iloc[-1]) if len(rs) else np.nan
        if len(rs) >= 20:
            row["rs_slope_4w"] = float(rs.tail(20).iloc[-1] - rs.tail(20).iloc[0])
        else:
            row["rs_slope_4w"] = 0.0

        # Contraction count: count local minima in 20d range series
        r20 = (ph - pl).tail(120)
        if len(r20) >= 40:
            diff = r20.diff()
            sign = np.sign(diff)
            sign[sign == 0] = np.nan
            sign = sign.ffill().bfill()
            turns = ((sign.shift(1) > 0) & (sign < 0)).fillna(False).sum()
            row["contraction_cycles"] = int(min(turns, 10))
        else:
            row["contraction_cycles"] = 0

        pivot = float(ph.tail(60).max())
        row["pivot_high_60"] = pivot

        # Bollinger / Keltner for TTM
        close20 = pc.tail(20)
        if len(close20) >= 20:
            mid = close20.mean()
            std = close20.std(ddof=0)
            row["bb_mid"] = float(mid)
            row["bb_upper"] = float(mid + 2 * std)
            row["bb_lower"] = float(mid - 2 * std)
            tr = pd.concat(
                [
                    ph.tail(20) - pl.tail(20),
                    (ph.tail(20) - pc.shift(1).tail(20)).abs(),
                    (pl.tail(20) - pc.shift(1).tail(20)).abs(),
                ],
                axis=1,
            ).max(axis=1)
            atr = float(tr.mean()) if len(tr) else np.nan
            row["atr_20"] = atr
            row["kc_upper"] = float(mid + 1.5 * atr) if atr == atr else np.nan
            row["kc_lower"] = float(mid - 1.5 * atr) if atr == atr else np.nan
            row["in_squeeze"] = bool(
                row["bb_upper"] == row["bb_upper"]
                and row["kc_upper"] == row["kc_upper"]
                and row["bb_upper"] < row["kc_upper"]
                and row["bb_lower"] > row["kc_lower"]
            )
        else:
            row["bb_mid"] = row["bb_upper"] = row["bb_lower"] = np.nan
            row["atr_20"] = row["kc_upper"] = row["kc_lower"] = np.nan
            row["in_squeeze"] = False

        # Momentum histogram proxy: last 10d return vs prior 10d
        if len(pc) >= 21:
            r10 = pc.iloc[-1] / pc.iloc[-11] - 1
            r10p = pc.iloc[-11] / pc.iloc[-21] - 1
            row["mom_hist"] = float(r10 - r10p)
        else:
            row["mom_hist"] = 0.0

        # Squeeze days (simple)
        if len(g) >= 5:
            sq = []
            for i in range(len(g) - 19):
                sub = g.iloc[i : i + 20]
                c = pd.to_numeric(sub["close"], errors="coerce")
                h = pd.to_numeric(sub["high"], errors="coerce")
                l = pd.to_numeric(sub["low"], errors="coerce")
                mid = c.mean()
                std = c.std(ddof=0)
                bu, bl = mid + 2 * std, mid - 2 * std
                tr = (h - l).mean()
                ku, kl = mid + 1.5 * tr, mid - 1.5 * tr
                sq.append(bu < ku and bl > kl)
            row["squeeze_days"] = int(sum(sq[-60:]))
        else:
            row["squeeze_days"] = 0

        # Breakout consolidation weeks: approximate low vol before high
        if len(pv) >= 30:
            vol_ratio = pv.iloc[-1] / (pv.iloc[-50:-10].mean() + 1e-9)
            consolidation = pv.iloc[-15:-5].mean() / (pv.iloc[-50:-15].mean() + 1e-9)
            row["volume_ratio_vs_50d"] = float(vol_ratio)
            row["consolidation_vol_ratio"] = float(consolidation)
        else:
            row["volume_ratio_vs_50d"] = 1.0
            row["consolidation_vol_ratio"] = 1.0

        rows.append(row)

    out = pd.DataFrame(rows)

    # Fundamentals snapshot (latest row per ticker)
    fun_rows = []
    for tic in out["ticker"].astype(str):
        f = (
            db.query(Fundamentals)
            .filter(Fundamentals.ticker == tic)
            .order_by(Fundamentals.date.desc())
            .first()
        )
        if f:
            fun_rows.append(
                {
                    "ticker": tic,
                    "pe_ratio": float(f.pe_ratio) if f.pe_ratio is not None else np.nan,
                    "eps_growth_proxy": np.nan,
                    "revenue": int(f.revenue or 0) if f.revenue else 0,
                    "market_cap": int(f.market_cap or 0) if f.market_cap else 0,
                    "roe": float(f.roe) if f.roe is not None else np.nan,
                    "debt_equity": float(f.debt_equity) if f.debt_equity is not None else np.nan,
                    "fcf_yield": float(f.fcf_yield) if f.fcf_yield is not None else np.nan,
                    "peg_ratio": float(f.peg_ratio) if f.peg_ratio is not None else np.nan,
                    "roic": float(f.roic) if f.roic is not None else np.nan,
                    "ev": int(f.ev or 0) if f.ev else np.nan,
                    "ebit": float(f.ebit) if f.ebit is not None else np.nan,
                    "sector": f.sector or "",
                }
            )
        else:
            fun_rows.append(
                {
                    "ticker": tic,
                    "pe_ratio": np.nan,
                    "eps_growth_proxy": np.nan,
                    "market_cap": np.nan,
                    "roe": np.nan,
                    "debt_equity": np.nan,
                    "fcf_yield": np.nan,
                    "peg_ratio": np.nan,
                    "roic": np.nan,
                    "ev": np.nan,
                    "ebit": np.nan,
                    "sector": "",
                }
            )
    ff = pd.DataFrame(fun_rows)
    if not ff.empty:
        out = out.merge(ff, on="ticker", how="left")

    # Sentiment
    sent_rows = []
    for tic in out["ticker"].astype(str):
        s = (
            db.query(SentimentScore)
            .filter(SentimentScore.ticker == tic)
            .order_by(SentimentScore.date.desc())
            .first()
        )
        if s:
            sent_rows.append(
                {
                    "ticker": tic,
                    "news_sentiment_score": float(s.avg_sentiment or 0),
                    "news_count_7d": int(s.news_count or 0),
                    "news_volume_spike": bool(s.volume_spike),
                }
            )
        else:
            sent_rows.append(
                {
                    "ticker": tic,
                    "news_sentiment_score": 0.0,
                    "news_count_7d": 0,
                    "news_volume_spike": False,
                }
            )
    ss = pd.DataFrame(sent_rows)
    out = out.merge(ss, on="ticker", how="left")

    # Alt-data stubs (filled by ingestion or seed)
    for col in (
        "earnings_beat_avg",
        "days_since_earnings",
        "insider_buy_usd",
        "insider_count",
        "insider_buy_sell_ratio",
    ):
        if col not in out.columns:
            out[col] = np.nan
    out["earnings_beat_avg"] = out["earnings_beat_avg"].fillna(0.0)
    out["days_since_earnings"] = out["days_since_earnings"].fillna(999)
    out["insider_buy_usd"] = out["insider_buy_usd"].fillna(0.0)
    out["insider_count"] = out["insider_count"].fillna(0).astype(int)
    out["insider_buy_sell_ratio"] = out["insider_buy_sell_ratio"].fillna(0.0)

    return out.fillna({"rs_score": 50.0})
