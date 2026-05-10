"""Tier limits from product spec."""

from __future__ import annotations

from dataclasses import dataclass

from engine.waterfall import StageConfig


FREE_SLUGS = {"vcp", "trend_template", "magic_formula"}


@dataclass
class Limits:

    max_stages: int

    premium_ok: bool

    universe_wide: bool

    schedules_ok: bool

    templates_max: int | None


def limits_for(tier: str) -> Limits:
    tier_l = tier.lower()

    if tier_l == "pro":
        return Limits(max_stages=99, premium_ok=True, universe_wide=True, schedules_ok=True, templates_max=None)

    return Limits(max_stages=2, premium_ok=False, universe_wide=False, schedules_ok=False, templates_max=2)


def enforce_screen(stages: list[StageConfig], universe: str, tier: str) -> None:

    lim = limits_for(tier)

    if len(stages) > lim.max_stages:

        raise ValueError(f"{tier} plan allows up to {lim.max_stages} stages")

    if not lim.premium_ok:

        bad = [s.slug for s in stages if s.slug not in FREE_SLUGS]

        if bad:

            raise ValueError(f"Upgrade to Pro for strategies: {', '.join(sorted(set(bad)))}")

    if not lim.universe_wide and universe not in {"", "sp500", "free"}:

        raise ValueError("Broad universes require Pro")
