"""Insider buying from ingested stubs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class InsiderBuyingStrategy(BaseStrategy):
    name = "Insider Buying"
    slug = "insider_buying"
    category = "alt_data"
    is_premium = True

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        min_amt = float(params.get("min_amount_usd", 50_000))
        min_ins = int(params.get("min_insiders", 2))
        ratio_min = float(params.get("buy_sell_ratio", 2))

        out = df.copy()
        scores = []
        sigs = []
        rsns = []

        for _, r in out.iterrows():
            amt = float(r.get("insider_buy_usd", 0))
            ic = int(r.get("insider_count", 0))
            rt = float(r.get("insider_buy_sell_ratio", 0))

            score = np.clip(np.log10(amt + 1) * 20 + ic * 5 + rt * 5, 0, 100)
            scores.append(float(score))

            ok = amt >= min_amt and ic >= min_ins and rt >= ratio_min
            sigs.append("long" if ok else None)
            rsns.append(f"Cluster buys ${amt:,.0f} by {ic} insiders; buy/sell {rt:.2f}")

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
