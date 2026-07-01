"""
SQLAlchemy ORM models.
All tables prefixed with `sw_` to avoid collisions if sharing a database.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Stock Universe ────────────────────────────────────────────────────────────

class Stock(Base):
    __tablename__ = "sw_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(80))
    industry: Mapped[Optional[str]] = mapped_column(String(80))
    market_cap_category: Mapped[Optional[str]] = mapped_column(String(20))  # large/mid/small
    isin: Mapped[Optional[str]] = mapped_column(String(12), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    ohlcv_records: Mapped[list["OHLCV"]] = relationship(back_populates="stock", lazy="dynamic")
    signals: Mapped[list["Signal"]] = relationship(back_populates="stock", lazy="dynamic")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="stock", lazy="dynamic"
    )


# ── OHLCV Data ────────────────────────────────────────────────────────────────

class OHLCV(Base):
    __tablename__ = "sw_ohlcv"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", "timeframe", name="uq_ohlcv_stock_date_tf"),
        Index("ix_ohlcv_stock_date", "stock_id", "date"),
        Index("ix_ohlcv_date_tf", "date", "timeframe"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("sw_stocks.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False, default="1d")
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adj_close: Mapped[Optional[float]] = mapped_column(Float)
    is_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)

    stock: Mapped["Stock"] = relationship(back_populates="ohlcv_records")


# ── Signals ───────────────────────────────────────────────────────────────────

class Signal(Base):
    __tablename__ = "sw_signals"
    __table_args__ = (
        Index("ix_signal_symbol_date", "stock_id", "signal_date"),
        Index("ix_signal_strategy", "strategy_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stock_id: Mapped[int] = mapped_column(ForeignKey("sw_stocks.id"), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # LONG/SHORT
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    target_1: Mapped[float] = mapped_column(Float, nullable=False)
    target_2: Mapped[Optional[float]] = mapped_column(Float)
    risk_reward: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[str] = mapped_column(String(10), nullable=False)   # STRONG/MODERATE/WEAK
    holding_days: Mapped[int] = mapped_column(Integer, default=10)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="signals")


# ── Recommendations ───────────────────────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "sw_recommendations"
    __table_args__ = (
        Index("ix_rec_date_score", "scan_date", "confidence_score"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stock_id: Mapped[int] = mapped_column(ForeignKey("sw_stocks.id"), nullable=False)
    signal_id: Mapped[str] = mapped_column(ForeignKey("sw_signals.id"), nullable=False)
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    historical_win_rate: Mapped[Optional[float]] = mapped_column(Float)
    historical_occurrences: Mapped[Optional[int]] = mapped_column(Integer)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="recommendations")
    signal: Mapped["Signal"] = relationship()


# ── Backtest Results ──────────────────────────────────────────────────────────

class BacktestResult(Base):
    __tablename__ = "sw_backtest_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    universe: Mapped[str] = mapped_column(String(80), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    final_capital: Mapped[float] = mapped_column(Float, nullable=False)
    total_return_pct: Mapped[float] = mapped_column(Float)
    cagr: Mapped[float] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Float)
    calmar_ratio: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown_pct: Mapped[float] = mapped_column(Float)
    win_rate: Mapped[float] = mapped_column(Float)
    total_trades: Mapped[int] = mapped_column(Integer)
    winning_trades: Mapped[int] = mapped_column(Integer)
    losing_trades: Mapped[int] = mapped_column(Integer)
    avg_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    avg_loss_pct: Mapped[Optional[float]] = mapped_column(Float)
    expectancy: Mapped[Optional[float]] = mapped_column(Float)
    equity_curve: Mapped[list] = mapped_column(JSON, default=list)
    monthly_returns: Mapped[dict] = mapped_column(JSON, default=dict)
    trade_log: Mapped[list] = mapped_column(JSON, default=list)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── Replay Sessions ───────────────────────────────────────────────────────────

class ReplaySession(Base):
    __tablename__ = "sw_replay_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stock_id: Mapped[int] = mapped_column(ForeignKey("sw_stocks.id"), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    stock: Mapped["Stock"] = relationship()


# ── Scan Jobs ─────────────────────────────────────────────────────────────────

class ScanJob(Base):
    __tablename__ = "sw_scan_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    stocks_scanned: Mapped[int] = mapped_column(Integer, default=0)
    signals_generated: Mapped[int] = mapped_column(Integer, default=0)
    recommendations_created: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
