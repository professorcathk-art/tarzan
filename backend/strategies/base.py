from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    name: str = ""
    slug: str = ""
    category: str = ""
    supports_short: bool = False
    timeout_seconds: int = 10
    is_premium: bool = False

    @abstractmethod
    def run(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Input: cross-section DataFrame per ticker with OHLCV aggregates and features.
        Output: same rows with columns score (float), signal ('long'|'short'|None), reason (str).
        """

    def _ensure_output_cols(self, out: pd.DataFrame) -> pd.DataFrame:
        if "score" not in out.columns:
            out["score"] = 0.0
        if "signal" not in out.columns:
            out["signal"] = None
        if "reason" not in out.columns:
            out["reason"] = ""
        return out
