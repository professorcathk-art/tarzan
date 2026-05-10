"""Latest market data staleness helpers."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func

from sqlalchemy.orm import Session

from db.models import PriceHistory


def last_trade_date(session: Session) -> date | None:

    mn = session.query(func.max(PriceHistory.date)).scalar()

    return mn
