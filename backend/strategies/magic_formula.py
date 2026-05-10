"""Greenblatt-style ranking."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class MagicFormulaStrategy(BaseStrategy):
    name = "Magic Formula"
    slug = "magic_formula"
    category = "fundamental"
    is_premium = False

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        out = df.copy()

        excluded = {"Financial Services", "Utilities", "financial", "utilities", "Finance", ""}
        mc_min = float(params.get("min_market_cap_usd", 500_000_000))
        universe_size = int(params.get("universe_size", min(80, len(out))))

        ebit = pd.to_numeric(out["ebit"], errors="coerce") if "ebit" in out.columns else pd.Series(np.nan, index=out.index)

        ev = pd.to_numeric(out["ev"], errors="coerce") if "ev" in out.columns else pd.Series(np.nan, index=out.index)

        ey = ebit / ev.replace({0: np.nan})

        roic = pd.to_numeric(out["roic"], errors="coerce") if "roic" in out.columns else pd.Series(np.nan, index=out.index)

        rp_ey = ey.rank(pct=True, method="average")
        rp_roic = roic.rank(pct=True, method="average")

        mf = rp_ey.fillna(0.5) + rp_roic.fillna(0.5)

        ranks = mf.sort_values(ascending=False)
        thresh = ranks.iloc[min(universe_size, len(ranks)) - 1] if len(ranks) else 0

        mc = pd.to_numeric(out.get("market_cap"), errors="coerce") if "market_cap" in out.columns else pd.Series(np.nan, index=out.index)

        sectors = out.get("sector", pd.Series([""] * len(out)))

        scores = []

        rsns = []

        sigs = []

        for i in range(len(out)):

            sec = str(sectors.iloc[i]).strip()

            filt = (mc.iloc[i] == mc.iloc[i] and mc.iloc[i] >= mc_min and sec not in excluded) if len(mc) else True

            comp = float(mf.iloc[i]) if mf.iloc[i] == mf.iloc[i] else 0.5

            scores.append(float(np.clip(comp * 50, 0, 100)))

            ok = filt and mf.iloc[i] >= thresh

            sigs.append("long" if ok else None)

            rsns.append(
                f"EY rank bucket {rp_ey.iloc[i]:.2f}, ROIC rank bucket {rp_roic.iloc[i]:.2f}, MF comp {mf.iloc[i]:.2f}; "
                f"sector={sec or 'n/a'}; cap_gate={filt}"
            )

        out["score"] = scores

        out["signal"] = sigs

        out["reason"] = rsns

        return self._ensure_output_cols(out)
