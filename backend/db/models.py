from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import List, Optional

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    tier: Mapped[str] = mapped_column(String(20), default="free")
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    templates = relationship("Template", back_populates="user")
    schedules = relationship("EmailSchedule", back_populates="user")


class StrategyMeta(Base):
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    category: Mapped[str] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_short: Mapped[bool] = mapped_column(Boolean, default=False)
    sharpe_preview: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pipeline_config: Mapped[list] = mapped_column(JSONB)
    universe: Mapped[str] = mapped_column(String(64), default="sp500")
    direction: Mapped[str] = mapped_column(String(32), default="long")
    max_stocks: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="templates")


class ScreenRun(Base):
    __tablename__ = "screen_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    stage_snapshots: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    final_tickers: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    backtest_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    combo_hash: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("backtest_jobs.id"))
    combo_hash: Mapped[str] = mapped_column(String(128))
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    equity_curve: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    monthly_returns: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"

    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    adj_close: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    rs_score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    pe_ratio: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    eps: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    revenue: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    market_cap: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    debt_equity: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    fcf_yield: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    peg_ratio: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    roic: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    ev: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ebit: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    avg_sentiment: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    news_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    volume_spike: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    top_headlines: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)


class EmailSchedule(Base):
    __tablename__ = "email_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.id"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    frequency: Mapped[str] = mapped_column(String(32))
    time_et: Mapped[str] = mapped_column(String(8))
    days_of_week: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="schedules")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("email_schedules.id"))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PaperPortfolio(Base):
    __tablename__ = "paper_portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("paper_portfolios.id"))
    ticker: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    entry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    entry_price: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    return_pct: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)


class UniverseSnapshot(Base):
    __tablename__ = "universe_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe: Mapped[str] = mapped_column(String(64))
    tickers: Mapped[List[str]] = mapped_column(ARRAY(Text))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
