"""VCP: volatility contraction pattern scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy


class VCPStrategy(BaseStrategy):
    name = "VCP (Volatility Contraction)"
    slug = "vcp"
    category = "momentum"
    supports_short = False
    timeout_seconds = 10
    is_premium = False

    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        contraction_periods = int(params.get("contraction_periods", 3))
        pivot_pct = float(params.get("pivot_proximity_pct", 5)) / 100.0
        rs_thr = float(params.get("rs_threshold", 70))

        out = df.copy()

        tightness = []
        volume_score = []
        ma_score = []
        pivot_bonus = []
        passes = []

        for _, r in out.iterrows():
            c = float(r.get("close", np.nan))
            sma50 = r.get("sma_50", np.nan)
            sma150 = r.get("sma_150", np.nan)
            sma200 = r.get("sma_200", np.nan)
            r20 = r.get("range_20", np.nan)
            r60 = r.get("range_60", np.nan)
            av50 = float(r.get("avg_vol_50", 1)) or 1.0
            vol = float(r.get("volume", 0))
            cycles = int(r.get("contraction_cycles", 0))
            pivot = float(r.get("pivot_high_60", np.nan))
            rs = float(r.get("rs_score", 50))

            h_pre = (
                np.isnan(c)
                or c <= 10
                or vol < 500_000
                or rs < rs_thr
                or cycles < max(2, contraction_periods - 1)
            )
            passes.append(not h_pre)

            if not np.isnan(r20) and not np.isnan(r60) and r60 > 0:
                tight = np.clip((1 - r20 / r60) * 40, 0, 40)
            else:
                tight = 0.0

            vr = np.clip((1 - vol / max(av50 * 1.2, 1)) * 30 + 15, 0, 30) if vol < av50 else max(10, 15 - vol / max(av50 * 5, 1))

            ma = 0.0
            if not np.isnan(sma50) and not np.isnan(sma150) and not np.isnan(sma200):
                if sma50 > sma150 > sma200:
                    ma += 22
                    slope = float(r.get("ma200_slope_30", 0))
                    if slope > 0:
                        ma += 8

            piv = 0.0
            if not np.isnan(pivot) and pivot > 0 and not np.isnan(c):
                prox = abs(c / pivot - 1)
                if prox <= pivot_pct:
                    piv = 5.0 * (1 - prox / max(pivot_pct, 1e-6))

            tightness.append(tight)
            volume_score.append(vr if np.isfinite(vr) else 15.0)
            ma_score.append(ma)
            pivot_bonus.append(piv)

        out["score"] = pd.Series(tightness) + pd.Series(volume_score) + pd.Series(ma_score) + pd.Series(pivot_bonus)
        sig = []
        reasons = []
        for i in range(len(out)):
            ok = passes[i]
            sc = float(out["score"].iloc[i])
            if ok and sc >= 60:
                sig.append("long")
                reasons.append(
                    f"Tightness {tightness[i]:.0f}/40, Volume {volume_score[i]:.0f}/30, MA {ma_score[i]:.0f}/30, "
                    f"pivot bonus {pivot_bonus[i]:.1f}"
                )
            elif ok:
                sig.append(None)
                reasons.append("Preconditions OK but composite score below long threshold.")
            else:
                sig.append(None)
                cc = float(out.iloc[i].get("close", 0))
                vrow = float(out.iloc[i].get("volume", 0))
                reasons.append(
                    f"Filtered: price ${cc:.2f}, vol/day {vrow:,.0f}, RS≥{rs_thr}, "
                    f"contractions {int(out.iloc[i].get('contraction_cycles', 0))}"
                )

        out["signal"] = sig
        out["reason"] = reasons
        return self._ensure_output_cols(out)
