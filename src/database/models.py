"""Database models for the trading bot."""

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Date, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class SignalType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class InstrumentType(enum.Enum):
    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


class TradeStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


class SeverityLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TelegramChannel(Base):
    """Telegram channel configuration."""
    __tablename__ = "telegram_channels"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(100), unique=True, nullable=False)
    channel_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    signal_patterns = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("RawMessage", back_populates="channel")


class RawMessage(Base):
    """Raw messages from Telegram."""
    __tablename__ = "raw_messages"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(100), ForeignKey("telegram_channels.channel_id"), nullable=False)
    message_id = Column(String(100), nullable=False)
    message_text = Column(String, nullable=False)
    message_date = Column(DateTime, nullable=False)
    sender_info = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    channel = relationship("TelegramChannel", back_populates="messages")
    signals = relationship("TradingSignal", back_populates="message")


class TradingSignal(Base):
    """Parsed trading signals from messages."""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("raw_messages.id"), nullable=False)
    channel_id = Column(String(100), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)
    instrument_type = Column(Enum(InstrumentType), nullable=False)
    symbol = Column(String(100), nullable=False)
    strike_price = Column(Float)
    expiry_date = Column(Date)
    option_type = Column(String(10))  # CE or PE
    quantity = Column(Integer)
    entry_price = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)
    confidence_score = Column(Float)
    ai_model_used = Column(String(100))
    parsing_metadata = Column(JSON)
    signal_timestamp = Column(DateTime, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    message = relationship("RawMessage", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")


class Trade(Base):
    """Executed trades."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("trading_signals.id"))
    trade_id = Column(String(100), unique=True)
    order_id = Column(String(100))
    symbol = Column(String(100), nullable=False)
    instrument_type = Column(Enum(InstrumentType), nullable=False)
    trade_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    pnl = Column(Float)
    brokerage = Column(Float)
    taxes = Column(Float)
    net_pnl = Column(Float)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    signal = relationship("TradingSignal", back_populates="trades")


class Position(Base):
    """Current positions."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(100), nullable=False)
    instrument_type = Column(Enum(InstrumentType), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class RiskEvent(Base):
    """Risk management events."""
    __tablename__ = "risk_events"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    description = Column(String, nullable=False)
    affected_trades = Column(JSON)
    action_taken = Column(String(255))
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class BacktestResult(Base):
    """Backtesting results."""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True)
    backtest_name = Column(String(255), nullable=False)
    channel_id = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_signals = Column(Integer)
    executed_signals = Column(Integer)
    win_rate = Column(Float)
    total_pnl = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    parameters = Column(JSON)
    results_detail = Column(JSON)
    created_at = Column(DateTime, default=func.now())


class PerformanceMetric(Base):
    """System performance metrics."""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_date = Column(Date, nullable=False)
    metric_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=func.now())


class AnomalyLog(Base):
    """Anomaly detection logs."""
    __tablename__ = "anomaly_logs"
    
    id = Column(Integer, primary_key=True)
    anomaly_type = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    data_snapshot = Column(JSON)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())