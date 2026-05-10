"""TTM Squeeze proxy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class TTMSqueezeStrategy(BaseStrategy):
    name = "TTM Squeeze"
    slug = "ttm_squeeze"
    category = "volatility"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        out = df.copy()
        scores = []
        sigs = []
        dirs = []
        rsns = []

        for _, r in out.iterrows():
            iq = bool(r.get("in_squeeze", False))
            days = int(r.get("squeeze_days", 0))
            mom = float(r.get("mom_hist", 0))

            firing_long = iq and mom > 0 and days >= 5
            score = np.clip(days * 3 + abs(mom) * 600 + (40 if iq else 0), 0, 100)
            scores.append(float(score))

            if firing_long:
                sigs.append("long")
                dirs.append("firing_long")
                rsns.append(f"Squeeze {days} bars, histogram turning up {mom:+.4f}")
            elif iq:
                sigs.append(None)
                dirs.append("in_squeeze")
                rsns.append(f"In squeeze {days}d, waiting momentum flip")
            else:
                sigs.append(None)
                dirs.append("idle")
                rsns.append("No active squeeze")

        out["score"] = scores
        out["signal"] = sigs
        out["squeeze_state"] = dirs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
