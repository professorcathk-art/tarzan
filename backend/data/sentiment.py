"""VADER-backed sentiment ingestion helper."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import get_settings


def compute_headline_sentiments(headlines: list[str]) -> list[float]:
    sia = SentimentIntensityAnalyzer()

    weights = [(0.85**i) for i in range(len(headlines))]
    scores = []
    for i, line in enumerate(headlines):
        c = sia.polarity_scores(line or "")["compound"]
        scores.append(c * weights[i])
    denom = sum(weights) or 1.0

    weighted = sum(scores) / denom
    return [weighted]


def aggregate_ticker_news(news_rows: list[dict], lookback_days: int = 7) -> dict:
    cutoff = date.today() - timedelta(days=lookback_days)
    headlines = []

    for r in sorted(news_rows, key=lambda x: x.get("published", ""), reverse=True):
        try:
            d = pd.Timestamp(r["published"]).date()
        except Exception:  # noqa: BLE001
            continue

        if d >= cutoff:
            headlines.append(str(r.get("title", "") or ""))

    if not headlines:
        return {"avg_sentiment": 0.0, "news_count": 0, "volume_spike": False}

    sia = SentimentIntensityAnalyzer()

    compounded = []

    weights = [(0.85**i) for i in range(len(headlines))]
    for i, h in enumerate(headlines):
        compounded.append(sia.polarity_scores(h)["compound"] * weights[i])

    denom = sum(weights) or 1.0
    avg = sum(compounded) / denom

    hist_avg = len(headlines) / max(len(news_rows), 1)

    spike = len(headlines) > 2 * max(hist_avg, 1)

    adj = avg * (1 + (0.2 if spike else 0))

    return {"avg_sentiment": float(max(-1.0, min(1.0, adj))), "news_count": len(headlines), "volume_spike": spike}
