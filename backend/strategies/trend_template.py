"""Minervini-style trend template."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class TrendTemplateStrategy(BaseStrategy):
    name = "Trend Template (Minervini)"
    slug = "trend_template"
    category = "momentum"
    supports_short = False
    is_premium = False

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        rs_min = float(params.get("rs_threshold", 70))
        out = df.copy()
        scores = []
        sigs = []
        reasons = []

        for _, r in out.iterrows():
            c = float(r.get("close", np.nan))
            s50, s150, s200 = r.get("sma_50"), r.get("sma_150"), r.get("sma_200")
            slope200 = float(r.get("ma200_slope_30", 0))
            hi52 = float(r.get("high_252", np.nan))
            lo52 = float(r.get("low_252", np.nan))
            rs = float(r.get("rs_score", 50))

            checks = [
                not np.isnan(c) and not np.isnan(s150) and not np.isnan(s200) and c > s150 > s200,
                slope200 > 0,
                not np.isnan(s50) and not np.isnan(s150) and s50 > s150 > s200,
                not np.isnan(s50) and c > s50,
                not np.isnan(lo52) and lo52 > 0 and c / lo52 >= 1.25,
                not np.isnan(hi52) and hi52 > 0 and c / hi52 >= 0.75,
                rs >= rs_min,
                c >= 10,
            ]
            score = sum(bool(x) for x in checks) * 12.5
            scores.append(score)
            if all(checks):
                sigs.append("long")
                reasons.append(f"8/8 checks; RS={rs:.0f}")
            elif score >= float(params.get("soft_min_score", 50)):
                sigs.append(None)
                hits = sum(bool(x) for x in checks)
                reasons.append(f"{hits}/8 conditions met for soft tier")
            else:
                sigs.append(None)
                reasons.append("Technical template not aligned")

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = reasons
        return self._ensure_output_cols(out)
