"""52-week breakout."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class Strategy52WBreakout(BaseStrategy):
    name = "52-Week Breakout"
    slug = "breakout_52w"
    category = "momentum"

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        prox_pct = float(params.get("proximity_pct", 2)) / 100.0
        vol_mult = float(params.get("volume_multiplier", 1.5))

        out = df.copy()
        scores = []
        sigs = []
        rsns = []

        for _, r in out.iterrows():
            c = float(r.get("close", np.nan))
            hi = float(r.get("high_252", np.nan))
            vol_ratio = float(r.get("volume_ratio_vs_50d", 1))
            consol = float(r.get("consolidation_vol_ratio", 1))

            near_hi = hi > 0 and c >= hi * (1 - prox_pct)
            vol_ok = vol_ratio >= vol_mult
            consol_ok = consol <= 0.95

            stren = max(0, (vol_ratio - 1)) * max(0, (1 - abs(c / hi - 1) / max(prox_pct, 1e-6)))
            score = np.clip(stren * 35 + (30 if near_hi else 0) + (20 if vol_ok else 5) + (15 if consol_ok else 0), 0, 100)

            scores.append(float(score))

            ok = near_hi and vol_ok and consol_ok and not np.isnan(c)
            sigs.append("long" if ok else None)
            rsns.append(
                f"Near 52w high {near_hi}, vol x {vol_ratio:.2f}, consolidation ratio {consol:.2f}, strength {stren:.2f}"
            )

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
