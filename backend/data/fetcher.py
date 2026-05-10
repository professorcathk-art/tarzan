"""Market data ingestion (EODHD / yfinance) — stubs with optional live calls."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd
import yfinance as yf

from config import get_settings


def pd_ts_to_date(ts) -> date:
    return pd.Timestamp(ts).date()


def fetch_daily_yfinance(symbol: str, days: int = 400) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days)

    tk = yf.Ticker(symbol)
    hist = tk.history(start=start.isoformat(), end=end.isoformat(), auto_adjust=True)
    rows: list[dict[str, Any]] = []

    for idx, r in hist.iterrows():
        rows.append(
            {
                "ticker": symbol.upper(),
                "date": pd_ts_to_date(idx),
                "open": float(r["Open"]),
                "high": float(r["High"]),
                "low": float(r["Low"]),
                "close": float(r["Close"]),
                "volume": int(r["Volume"]),
                "adj_close": float(r["Close"]),
            }
        )

    return rows


async def fetch_finnhub_news(symbol: str) -> list[dict[str, Any]]:
    s = get_settings()
    if not s.finnhub_api_key:
        return []

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            "https://finnhub.io/api/v1/company-news",
            params={
                "symbol": symbol.upper(),
                "from": (date.today() - timedelta(days=30)).isoformat(),
                "to": date.today().isoformat(),
                "token": s.finnhub_api_key,
            },
        )
        if r.status_code != 200:
            return []

        rows: list[dict[str, Any]] = []

        for it in r.json()[:120]:
            rows.append(
                {
                    "title": str(it.get("headline") or ""),
                    "published": str(it.get("datetime") or ""),
                    "source": str(it.get("source") or ""),
                }
            )

        return rows
