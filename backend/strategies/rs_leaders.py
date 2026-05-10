"""RS Leaders."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class RSLeadersStrategy(BaseStrategy):
    name = "RS Leaders"
    slug = "rs_leaders"
    category = "momentum"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        thr = float(params.get("rs_threshold", 80))
        out = df.copy()
        scores = []
        sigs = []
        rsns = []

        for _, r in out.iterrows():
            rs = float(r.get("rs_score", 50))
            drop = float(r.get("max_1d_drop_4w", 0))
            slope = float(r.get("rs_slope_4w", 0))

            penalty = drop > 0.15 or rs < thr
            score = rs + (10 if slope > 0 else 0)
            scores.append(float(np.clip(score, 0, 100)))

            if rs >= thr and drop <= 0.15:
                sigs.append("long")
                rsns.append(f"RS {rs:.0f}, 4w max drop {drop*100:.1f}%, RS slope {'+' if slope>0 else '-'} ")
            elif rs >= thr * 0.9:
                sigs.append(None)
                rsns.append("Near RS leader but disqualifying drop or RS slope")
            else:
                sigs.append(None)
                rsns.append(f"RS {rs:.0f} below {thr}")

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
