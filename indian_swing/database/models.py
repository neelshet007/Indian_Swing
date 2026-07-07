from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
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


class Stock(Base):
    __tablename__ = "sw_stocks"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_stock_exchange_symbol"),
        UniqueConstraint("isin", name="uq_stock_isin"),
        Index("ix_stock_exchange_symbol", "exchange", "symbol"),
    )

    stock_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="DEVELOPMENT")
    exchange: Mapped[str] = mapped_column(String(16), nullable=False, default="NSE")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(120))
    industry: Mapped[Optional[str]] = mapped_column(String(120))
    market_cap_category: Mapped[Optional[str]] = mapped_column(String(24))
    instrument_type: Mapped[str] = mapped_column(String(24), nullable=False, default="EQUITY")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    ohlcv_records: Mapped[list["OHLCV"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    signals: Mapped[list["Signal"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
    )


class OHLCV(Base):
    __tablename__ = "sw_ohlcv"
    __table_args__ = (
        UniqueConstraint("stock_uuid", "date", "timeframe", name="uq_ohlcv_stock_date_tf"),
        Index("ix_ohlcv_stock_date", "stock_uuid", "date"),
        Index("ix_ohlcv_timeframe_date", "timeframe", "date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stock_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_stocks.stock_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False, default="1d")
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    is_adjusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="yfinance")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    stock: Mapped["Stock"] = relationship(back_populates="ohlcv_records")


class ScanJob(Base):
    __tablename__ = "sw_scan_jobs"
    __table_args__ = (
        UniqueConstraint(
            "strategy_name",
            "strategy_version",
            "scan_date",
            name="uq_scan_strategy_version_date",
        ),
        Index("ix_scan_status_created", "status", "created_at"),
    )

    scan_uuid: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="DEVELOPMENT")
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    market_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    total_stocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stocks_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signals_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendations_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_stocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    filter_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    validation_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    signals: Mapped[list["Signal"]] = relationship(
        back_populates="scan_job",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="scan_job",
        cascade="all, delete-orphan",
    )


class Signal(Base):
    __tablename__ = "sw_signals"
    __table_args__ = (
        UniqueConstraint(
            "scan_uuid",
            "stock_uuid",
            "strategy_name",
            name="uq_signal_scan_stock_strategy",
        ),
        Index("ix_signal_scan_stock", "scan_uuid", "stock_uuid"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_scan_jobs.scan_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    stock_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_stocks.stock_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    target_1: Mapped[float] = mapped_column(Float, nullable=False)
    target_2: Mapped[Optional[float]] = mapped_column(Float)
    risk_reward: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    holding_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    indicator_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    scan_job: Mapped["ScanJob"] = relationship(back_populates="signals")
    stock: Mapped["Stock"] = relationship(back_populates="signals")
    recommendation: Mapped[Optional["Recommendation"]] = relationship(
        back_populates="signal",
        uselist=False,
    )


class Recommendation(Base):
    __tablename__ = "sw_recommendations"
    __table_args__ = (
        UniqueConstraint("scan_uuid", "stock_uuid", name="uq_recommendation_scan_stock"),
        Index("ix_recommendation_scan_rank", "scan_uuid", "rank"),
        Index("ix_recommendation_scan_date", "scan_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_scan_jobs.scan_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    signal_id: Mapped[str] = mapped_column(
        ForeignKey("sw_signals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    stock_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_stocks.stock_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_uuid: Mapped[str] = mapped_column(String(36), nullable=False, default=_uuid)
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    indicator_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    scanner_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    yahoo_version: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    download_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    history_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indicator_warmup: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calculation_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False, default="BUY")
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    risk_per_share: Mapped[float] = mapped_column(Float, nullable=False)
    risk_pct: Mapped[float] = mapped_column(Float, nullable=False)
    position_size: Mapped[Optional[int]] = mapped_column(Integer)
    portfolio_weight_pct: Mapped[Optional[float]] = mapped_column(Float)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    scan_job: Mapped["ScanJob"] = relationship(back_populates="recommendations")
    stock: Mapped["Stock"] = relationship(back_populates="recommendations")
    signal: Mapped["Signal"] = relationship(back_populates="recommendation")


class BacktestResult(Base):
    __tablename__ = "sw_backtest_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    universe: Mapped[str] = mapped_column(String(80), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    final_capital: Mapped[float] = mapped_column(Float, nullable=False)
    total_return_pct: Mapped[Optional[float]] = mapped_column(Float)
    cagr: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Float)
    calmar_ratio: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown_pct: Mapped[Optional[float]] = mapped_column(Float)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    total_trades: Mapped[Optional[int]] = mapped_column(Integer)
    winning_trades: Mapped[Optional[int]] = mapped_column(Integer)
    losing_trades: Mapped[Optional[int]] = mapped_column(Integer)
    avg_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    avg_loss_pct: Mapped[Optional[float]] = mapped_column(Float)
    expectancy: Mapped[Optional[float]] = mapped_column(Float)
    equity_curve: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    monthly_returns: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    trade_log: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ReplaySession(Base):
    __tablename__ = "sw_replay_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stock_uuid: Mapped[str] = mapped_column(
        ForeignKey("sw_stocks.stock_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_name: Mapped[str] = mapped_column(String(80), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    stock: Mapped["Stock"] = relationship()
