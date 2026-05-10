"""Waterfall and optional voting engines."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field

from strategies.registry import get_strategy


class StageConfig(BaseModel):
    slug: str
    order: int = 1
    filter_mode: Literal["hard", "soft"] = "hard"
    keep_pct: float = Field(0.3, ge=0.02, le=1.0)
    params: dict = Field(default_factory=dict)


def _reason_col(slug: str) -> str:
    return f"__reason__{slug}"


def run_strategy_with_timeout(strategy_cls, df: pd.DataFrame, params: dict):
    holder: dict[str, pd.DataFrame | str | None] = {"out": None, "err": None}

    def worker():
        try:
            strat = strategy_cls()
            holder["out"] = strat.run(df.copy(), params)
        except Exception as e:  # noqa: BLE001
            holder["err"] = str(e)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    timeout = float(getattr(strategy_cls, "timeout_seconds", 10) or 10)
    t.join(timeout=timeout)

    if t.is_alive():
        nm = getattr(strategy_cls, "name", "Strategy")

        return df.copy(), f"{nm} timed out after {timeout:.0f}s — stage skipped."

    if holder["err"]:
        return df.copy(), str(holder["err"])

    return holder["out"], None


@dataclass
class PipelineResult:
    final_df: pd.DataFrame
    final_tickers: list[str]
    stage_snapshots: list[dict]
    merged_reasons: dict[str, str]
    warnings: list[str]


class WaterfallEngine:
    def run(self, stages: list[StageConfig], universe_df: pd.DataFrame) -> PipelineResult:
        stages_sorted = sorted(stages, key=lambda s: s.order)
        cur = universe_df.copy()
        warnings: list[str] = []
        snapshots: list[dict] = []

        if "ticker" not in cur.columns:
            raise ValueError("Universe dataframe must contain column 'ticker'")

        accumulated_reasons: dict[str, list[str]] = {}

        for st in stages_sorted:
            cls = get_strategy(st.slug)

            inp_count = len(cur)
            result_df, warn = run_strategy_with_timeout(cls, cur, st.params)

            if warn:
                warnings.append(warn)

            rc = _reason_col(st.slug)
            result_df[rc] = result_df.get("reason", "")

            if st.filter_mode == "hard":
                sig = result_df["signal"].astype(object)
                passed = result_df[sig.notna() & sig.ne("")].copy()

            else:
                if result_df.empty:
                    passed = result_df
                else:
                    pct = float(st.keep_pct)
                    thr = result_df["score"].quantile(max(1e-6, 1 - pct))
                    passed = result_df[result_df["score"] >= thr].copy()

            after = len(passed)

            dropped = sorted(set(result_df["ticker"].tolist()) - set(passed["ticker"].tolist()))

            snapshots.append(
                {
                    "stage_slug": st.slug,
                    "stage_name": getattr(cls, "name", st.slug),
                    "input_count": inp_count,
                    "output_count": after,
                    "dropped_sample": dropped[:25],
                }
            )

            if passed.empty:
                cur = passed
                break

            for _, row in passed.iterrows():
                tk = str(row["ticker"])
                chunk = str(row.get(rc, "") or "")
                accumulated_reasons.setdefault(tk, []).append(
                    f"[{getattr(cls, 'name', st.slug)}] {chunk}" if chunk else f"[{getattr(cls, 'name', st.slug)}]"
                )

            keep_cols = [c for c in passed.columns if not str(c).startswith("__reason__")]
            cur = passed[keep_cols].copy()

        merged = {tk: " | ".join(parts) for tk, parts in accumulated_reasons.items()}
        final_tickers = cur["ticker"].astype(str).tolist()

        return PipelineResult(
            final_df=cur,
            final_tickers=final_tickers,
            stage_snapshots=snapshots,
            merged_reasons=merged,
            warnings=warnings,
        )


class VotingEngine:
    """Optional parallel scoring: sum normalized scores across strategies."""

    def run(self, stages: list[StageConfig], universe_df: pd.DataFrame) -> PipelineResult:
        from collections import defaultdict

        base = universe_df.copy()
        score_acc = pd.Series(0.0, index=base.index)
        reasons: dict[str, list[str]] = defaultdict(list)
        warnings: list[str] = []

        for st in sorted(stages, key=lambda s: s.order):
            cls = get_strategy(st.slug)
            tagged, warn = run_strategy_with_timeout(cls, base, st.params)
            if warn:
                warnings.append(warn)

            s = pd.to_numeric(tagged["score"], errors="coerce").fillna(0)
            n = (s - s.min()) / (s.max() - s.min() + 1e-9)
            score_acc = score_acc + n.fillna(0)

            for _, row in tagged.iterrows():
                tk = str(row["ticker"])
                reasons[tk].append(f"[{getattr(cls,'name','strategy')}] {row.get('reason','')}")

        base = base.copy()
        base["score"] = score_acc.values
        base["signal"] = ["long" if v >= float(len(stages)) * 0.55 else None for v in score_acc]
        base["reason"] = [(" | ".join(reasons[str(t)])).strip() for t in base["ticker"].tolist()]
        merged = {str(t): r for t, r in zip(base["ticker"].tolist(), base["reason"].tolist(), strict=False)}

        return PipelineResult(
            final_df=base.sort_values("score", ascending=False),
            final_tickers=base.sort_values("score", ascending=False)["ticker"].astype(str).tolist(),
            stage_snapshots=[{"mode": "voting", "stages": [s.slug for s in stages]}],
            merged_reasons=merged,
            warnings=warnings,
        )
