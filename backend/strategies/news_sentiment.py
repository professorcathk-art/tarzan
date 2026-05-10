"""News sentiment using DB fields (VADER applied in ingestion)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class NewsSentimentStrategy(BaseStrategy):
    name = "News Sentiment"
    slug = "news_sentiment"
    category = "alt_data"
    supports_short = True
    is_premium = True

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        min_thr = float(params.get("min_sentiment_threshold", 0.1))
        require_spike = bool(params.get("require_volume_spike", False))
        hard = params.get("filter_mode_hard", True)

        out = df.copy()
        scores = []
        sigs = []
        reasons = []

        for _, r in out.iterrows():
            s = float(r.get("news_sentiment_score", 0))
            spike = bool(r.get("news_volume_spike", False))
            cnt = int(r.get("news_count_7d", 0))
            adj = s * (1 + (0.2 if spike else 0))
            scores.append((adj + 1) * 50)

            ok_long = adj >= min_thr and (not require_spike or spike)
            if ok_long:
                sigs.append("long")
                reasons.append(f"7d weighted sentiment {adj:+.2f}, news count {cnt}, spike={spike}")
            elif adj <= -float(params.get("short_sentiment_threshold", 0.3)):
                sigs.append("short" if params.get("allow_short", False) else None)
                reasons.append(f"Strong negative catalyst proxy {adj:+.2f}")
            elif hard:
                sigs.append(None)
                reasons.append(f"Below sentiment threshold ({adj:+.2f} < {min_thr})")
            else:
                sigs.append(None)
                reasons.append(f"Neutral-ish sentiment {adj:+.2f}")

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = reasons
        return self._ensure_output_cols(out)
