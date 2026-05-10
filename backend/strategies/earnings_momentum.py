"""Earnings momentum from stub / ingested fundamentals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class EarningsMomentumStrategy(BaseStrategy):
    name = "Earnings Momentum"
    slug = "earnings_momentum"
    category = "alt_data"
    is_premium = True

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        min_beat = float(params.get("min_beat_pct", 5)) / 100.0
        max_days = int(params.get("days_since_earnings", 20))

        out = df.copy()
        scores = []
        sigs = []
        rsns = []

        for _, r in out.iterrows():
            beat_avg = float(r.get("earnings_beat_avg", 0))
            days_e = float(r.get("days_since_earnings", 999))
            score = np.clip((beat_avg / max(min_beat, 1e-6)) * 40 + max(0, 30 - days_e), 0, 100)
            scores.append(float(score))

            ok = beat_avg >= min_beat and days_e <= max_days and beat_avg != 0
            if ok:
                sigs.append("long")
                rsns.append(f"EPS surprise avg {beat_avg*100:.1f}%, days since EPS {days_e:.0f}")
            elif beat_avg > 0:
                sigs.append(None)
                rsns.append(f"Positive drift but gates not met ({days_e:.0f} days)")
            else:
                sigs.append(None)
                rsns.append("Insufficient earnings catalyst data")

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
