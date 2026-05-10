"""Quality + value composite."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class QualityValueStrategy(BaseStrategy):
    name = "Quality Value"
    slug = "quality_value"
    category = "fundamental"
    is_premium = True

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        w_roe = float(params.get("w_roe", 0.25))
        w_lev = float(params.get("w_leverage", 0.2))
        w_growth = float(params.get("w_growth", 0.25))
        w_val = float(params.get("w_valuation", 0.2))
        w_fcf = float(params.get("w_fcf", 0.1))

        out = df.copy()

        roe_s = pd.to_numeric(out.get("roe"), errors="coerce")
        de = pd.to_numeric(out.get("debt_equity"), errors="coerce")
        pe = pd.to_numeric(out.get("pe_ratio"), errors="coerce")
        fcf_y = pd.to_numeric(out.get("fcf_yield"), errors="coerce")
        eg = pd.to_numeric(out.get("eps_growth_proxy"), errors="coerce")

        scores = []
        rsns = []
        sigs = []

        for i, row in out.iterrows():
            roe_ok = roe_s.loc[i] == roe_s.loc[i] and roe_s.loc[i] >= 15
            lev_ok = de.loc[i] == de.loc[i] and de.loc[i] < 0.5
            val_ok = pe.loc[i] == pe.loc[i] and 0 < pe.loc[i] < 25  # simplified P/E gate
            fcf_ok = fcf_y.loc[i] == fcf_y.loc[i] and fcf_y.loc[i] > 3
            growth_ok = eg.loc[i] == eg.loc[i] and eg.loc[i] > 0.10

            parts = [
                w_roe * 100 if roe_ok else 0,
                w_lev * 100 if lev_ok else 0,
                w_growth * 100 if growth_ok else w_growth * 40,
                w_val * 100 if val_ok else w_val * 30,
                w_fcf * 100 if fcf_ok else w_fcf * 25,
            ]
            score = float(np.sum(parts))
            scores.append(score)

            hits = sum([roe_ok, lev_ok, growth_ok, val_ok, fcf_ok])
            rsns.append(
                f"Quality hits {hits}/5; ROE={row.get('roe','n/a')}, D/E={row.get('debt_equity','n/a')}, "
                f"FCF yield={row.get('fcf_yield','n/a')}"
            )
            sigs.append("long" if score >= 70 else None)

        out["score"] = scores
        out["signal"] = sigs
        out["reason"] = rsns
        return self._ensure_output_cols(out)
