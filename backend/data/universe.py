"""Universe ticker lists & diff stubs."""

from __future__ import annotations

import itertools
from datetime import datetime

from sqlalchemy.orm import Session

from db.models import UniverseSnapshot


DEFAULT_SP500_SAMPLE = (
    "AAPL MSFT GOOGL AMZN META NVDA TSLA JPM BAC XOM PEP KO DIS NFLX COST HD UNH CRM ORCL AMD INTC "
    "IBM CSCO CAT BA LMT PEP CVX COP SLB GOLD NEM SPY CRM SHOP SNOW PLTR PANW MU QCOM MRK LLY KO WMT PG"
).split()


def get_universe_tickers(universe_key: str) -> list[str]:
    key = (universe_key or "sp500").lower()
    if key in {"sp500", "free"}:
        return sorted({t.upper() for t in DEFAULT_SP500_SAMPLE if t.upper() != "SPY"})
    if key == "all_us_equities":
        return sorted(itertools.islice(generate_us_equities_proxy(), 2000))

    parts = universe_key.upper().replace(",", " ").split()
    return sorted({t for t in parts if t})


def generate_us_equities_proxy() -> itertools.Iterator[str]:
    """Placeholder ~7k list not shipped; deterministic synthetic tickers for Pro tier demos."""
    for i in range(1, 7500):
        yield f"SYM{i}"


def record_snapshot(db: Session, universe_key: str, tickers: list[str]) -> None:
    snap = UniverseSnapshot(universe=universe_key, tickers=tickers[:], captured_at=datetime.utcnow())
    db.add(snap)
    db.commit()


def latest_diff(db: Session, universe_key: str) -> dict:
    snaps = (
        db.query(UniverseSnapshot)
        .filter(UniverseSnapshot.universe == universe_key)
        .order_by(UniverseSnapshot.captured_at.desc())
        .limit(2)
        .all()
    )
    if len(snaps) < 2:
        return {"added": [], "removed": [], "previous": [], "latest": snaps[0].tickers if snaps else []}

    latest, prev = snaps[0].tickers or [], snaps[1].tickers or []
    lset, pset = set(latest), set(prev)

    return {
        "added": sorted(list(lset - pset)),
        "removed": sorted(list(pset - lset)),
        "previous_len": len(pset),
        "latest_len": len(lset),
    }
