"""IBD-style RS using SPY-relative momentum ranks."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rs_scores(panel: pd.DataFrame) -> pd.DataFrame:
    """panel rows: ticker, date, adj_close."""

    pivot = panel.pivot(index="date", columns="ticker", values="adj_close").sort_index()
    pivot = pivot.ffill()

    spy = pivot.get("SPY")
    if spy is None or spy.dropna().empty:
        pivot["__bench__"] = pivot.mean(axis=1)
        spy = pivot["__bench__"]

    rets = {}

    for w in (63, 126, 189, 252):

        rr = pivot.pct_change(w)
        bench = spy.pct_change(w)

        rs = rr.sub(bench, axis=0)

        rets[w] = rs.rank(axis=1, pct=True)

    rs_score = (
        0.4 * rets[63].fillna(0.5)
        + 0.2 * rets[126].fillna(0.5)
        + 0.2 * rets[189].fillna(0.5)
        + 0.2 * rets[252].fillna(0.5)
    ) * 99

    out = rs_score.stack().rename("rs_score").reset_index()

    return out
