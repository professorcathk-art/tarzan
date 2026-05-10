from __future__ import annotations

from strategies.base import BaseStrategy
from strategies.breakout_52w import Strategy52WBreakout
from strategies.earnings_momentum import EarningsMomentumStrategy
from strategies.insider_buying import InsiderBuyingStrategy
from strategies.magic_formula import MagicFormulaStrategy
from strategies.news_sentiment import NewsSentimentStrategy
from strategies.quality_value import QualityValueStrategy
from strategies.rs_leaders import RSLeadersStrategy
from strategies.trend_template import TrendTemplateStrategy
from strategies.ttm_squeeze import TTMSqueezeStrategy
from strategies.vcp import VCPStrategy


def _all() -> list[type[BaseStrategy]]:
    return [
        VCPStrategy,
        TrendTemplateStrategy,
        NewsSentimentStrategy,
        EarningsMomentumStrategy,
        MagicFormulaStrategy,
        RSLeadersStrategy,
        Strategy52WBreakout,
        TTMSqueezeStrategy,
        InsiderBuyingStrategy,
        QualityValueStrategy,
    ]


STRATEGY_CLASSES: list[type[BaseStrategy]] = _all()
STRATEGY_BY_SLUG: dict[str, type[BaseStrategy]] = {c.slug: c for c in STRATEGY_CLASSES}


def get_strategy(slug: str) -> type[BaseStrategy]:
    if slug not in STRATEGY_BY_SLUG:
        raise KeyError(f"Unknown strategy slug: {slug}")
    return STRATEGY_BY_SLUG[slug]


def list_metadata() -> list[dict]:
    out: list[dict] = []
    previews = {"vcp": 0.82, "trend_template": 0.71, "news_sentiment": 0.61, "earnings_momentum": 0.69, "magic_formula": 0.58,
                "rs_leaders": 0.88, "breakout_52w": 0.75, "ttm_squeeze": 0.64, "insider_buying": 0.59, "quality_value": 0.66}

    for cls in STRATEGY_CLASSES:
        preview = previews.get(cls.slug, 0.55)
        out.append(
            {
                "name": cls.name,
                "slug": cls.slug,
                "category": cls.category,
                "supports_short": cls.supports_short,
                "is_premium": getattr(cls, "is_premium", False),
                "timeout_seconds": getattr(cls, "timeout_seconds", 10),
                "sharpe_preview": preview,
                "description_short": "",
            }

        )

    return out
