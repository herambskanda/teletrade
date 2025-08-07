"""Comprehensive risk management system for the trading bot."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config.settings import get_settings
from src.database.models import Trade, RiskEvent, SeverityLevel, Position
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()


class RiskEventType(Enum):
    """Types of risk events."""
    POSITION_SIZE_LIMIT = "POSITION_SIZE_LIMIT"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    DRAWDOWN_LIMIT = "DRAWDOWN_LIMIT"
    MARGIN_REQUIREMENT = "MARGIN_REQUIREMENT"
    MARKET_HOURS = "MARKET_HOURS"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    CORRELATION_RISK = "CORRELATION_RISK"
    PRICE_ANOMALY = "PRICE_ANOMALY"
    SIGNAL_ANOMALY = "SIGNAL_ANOMALY"
    ORDER_FAILURE = "ORDER_FAILURE"


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    passed: bool
    risk_type: RiskEventType
    message: str
    severity: SeverityLevel
    action_required: bool = False


class RiskManager:
    """Comprehensive risk management system."""
    
    def __init__(self):
        """Initialize risk manager."""
        self.settings = settings
        self.emergency_stop_active = False
        self.daily_pnl = 0.0
        self.max_drawdown_current = 0.0
        self.portfolio_peak = 0.0
        
        # Risk limits from settings
        self.max_position_size = settings.max_position_size
        self.max_daily_loss = settings.max_daily_loss
        self.max_drawdown = settings.max_drawdown
        
        # Anomaly detection models
        self.price_anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_price_model_trained = False
        
        # Market hours (Indian market)
        self.market_open_time = (9, 15)  # 9:15 AM
        self.market_close_time = (15, 30)  # 3:30 PM
    
    async def validate_trade(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> List[RiskCheckResult]:
        """Comprehensive trade validation with risk checks."""
        risk_results = []
        
        # Run all risk checks
        checks = [
            self.check_position_size(signal),
            self.check_daily_loss_limit(),
            self.check_drawdown_limit(portfolio),
            self.check_margin_requirements(signal, portfolio),
            self.check_market_hours(),
            await self.check_circuit_breakers(signal["symbol"]),
            await self.check_correlation_risk(signal, portfolio),
            await self.check_price_anomalies(signal)
        ]
        
        # Execute all checks concurrently
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Risk check failed with exception: {result}")
                risk_results.append(RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.ORDER_FAILURE,
                    message=f"Risk check error: {str(result)}",
                    severity=SeverityLevel.HIGH,
                    action_required=True
                ))
            elif isinstance(result, RiskCheckResult):
                risk_results.append(result)
        
        # Log failed checks
        failed_checks = [r for r in risk_results if not r.passed]
        if failed_checks:
            await self._log_risk_events(failed_checks, signal)
        
        return risk_results
    
    async def check_position_size(self, signal: Dict[str, Any]) -> RiskCheckResult:
        """Check if position size is within limits."""
        try:
            position_value = signal.get("quantity", 0) * signal.get("entry_price", 0)
            
            if position_value > self.max_position_size:
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.POSITION_SIZE_LIMIT,
                    message=f"Position size {position_value} exceeds limit {self.max_position_size}",
                    severity=SeverityLevel.HIGH,
                    action_required=True
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.POSITION_SIZE_LIMIT,
                message="Position size within limits",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Position size check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.POSITION_SIZE_LIMIT,
                message=f"Position size check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_daily_loss_limit(self) -> RiskCheckResult:
        """Check daily loss limits."""
        try:
            today = date.today()
            
            # Calculate today's PnL from database
            async with get_db_session() as session:
                # Query today's trades
                from sqlalchemy import func, and_
                
                result = await session.execute(
                    f"""
                    SELECT COALESCE(SUM(net_pnl), 0) as daily_pnl
                    FROM trades 
                    WHERE DATE(created_at) = '{today}' AND net_pnl IS NOT NULL
                    """
                )
                
                daily_pnl = result.scalar() or 0.0
                self.daily_pnl = daily_pnl
            
            if abs(daily_pnl) > self.max_daily_loss and daily_pnl < 0:
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.DAILY_LOSS_LIMIT,
                    message=f"Daily loss {daily_pnl} exceeds limit {self.max_daily_loss}",
                    severity=SeverityLevel.CRITICAL,
                    action_required=True
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.DAILY_LOSS_LIMIT,
                message=f"Daily PnL {daily_pnl} within limits",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Daily loss check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.DAILY_LOSS_LIMIT,
                message=f"Daily loss check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_drawdown_limit(self, portfolio: Dict[str, Any]) -> RiskCheckResult:
        """Check maximum drawdown limits."""
        try:
            current_portfolio_value = portfolio.get("total_value", 0)
            
            # Update portfolio peak
            if current_portfolio_value > self.portfolio_peak:
                self.portfolio_peak = current_portfolio_value
            
            # Calculate current drawdown
            if self.portfolio_peak > 0:
                current_drawdown = (self.portfolio_peak - current_portfolio_value) / self.portfolio_peak
                self.max_drawdown_current = current_drawdown
            else:
                current_drawdown = 0.0
            
            if current_drawdown > self.max_drawdown:
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.DRAWDOWN_LIMIT,
                    message=f"Drawdown {current_drawdown:.2%} exceeds limit {self.max_drawdown:.2%}",
                    severity=SeverityLevel.CRITICAL,
                    action_required=True
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.DRAWDOWN_LIMIT,
                message=f"Drawdown {current_drawdown:.2%} within limits",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Drawdown check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.DRAWDOWN_LIMIT,
                message=f"Drawdown check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_margin_requirements(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> RiskCheckResult:
        """Check margin requirements."""
        try:
            available_margin = portfolio.get("available_margin", 0)
            required_margin = self._calculate_required_margin(signal)
            
            if required_margin > available_margin:
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.MARGIN_REQUIREMENT,
                    message=f"Required margin {required_margin} exceeds available {available_margin}",
                    severity=SeverityLevel.HIGH,
                    action_required=True
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.MARGIN_REQUIREMENT,
                message="Sufficient margin available",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Margin check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.MARGIN_REQUIREMENT,
                message=f"Margin check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_market_hours(self) -> RiskCheckResult:
        """Check if market is open."""
        try:
            now = datetime.now()
            current_time = (now.hour, now.minute)
            
            # Check if it's a weekend
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.MARKET_HOURS,
                    message="Market closed - Weekend",
                    severity=SeverityLevel.MEDIUM
                )
            
            # Check market hours
            if not (self.market_open_time <= current_time <= self.market_close_time):
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.MARKET_HOURS,
                    message=f"Market closed - Current time {now.strftime('%H:%M')}",
                    severity=SeverityLevel.MEDIUM
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.MARKET_HOURS,
                message="Market is open",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Market hours check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.MARKET_HOURS,
                message=f"Market hours check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_circuit_breakers(self, symbol: str) -> RiskCheckResult:
        """Check if stock has hit circuit breakers."""
        try:
            # This would typically involve checking real-time data
            # For now, we'll implement a simple check
            
            # In a real implementation, you would:
            # 1. Get current price and previous close
            # 2. Calculate percentage change
            # 3. Check against circuit limits (usually ±5%, ±10%, ±20%)
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.CIRCUIT_BREAKER,
                message=f"No circuit breaker hit for {symbol}",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Circuit breaker check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.CIRCUIT_BREAKER,
                message=f"Circuit breaker check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_correlation_risk(self, signal: Dict[str, Any], portfolio: Dict[str, Any]) -> RiskCheckResult:
        """Check for correlation risk in portfolio."""
        try:
            # Get current positions
            current_positions = portfolio.get("positions", [])
            
            # Check sector concentration
            symbol = signal["symbol"]
            sector = self._get_sector(symbol)
            
            sector_exposure = sum(
                pos.get("value", 0) for pos in current_positions
                if self._get_sector(pos.get("symbol", "")) == sector
            )
            
            total_portfolio_value = portfolio.get("total_value", 1)
            sector_concentration = sector_exposure / total_portfolio_value if total_portfolio_value > 0 else 0
            
            # Check if sector concentration exceeds 30%
            if sector_concentration > 0.3:
                return RiskCheckResult(
                    passed=False,
                    risk_type=RiskEventType.CORRELATION_RISK,
                    message=f"High sector concentration {sector_concentration:.2%} in {sector}",
                    severity=SeverityLevel.MEDIUM,
                    action_required=True
                )
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.CORRELATION_RISK,
                message="Portfolio correlation within limits",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Correlation check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.CORRELATION_RISK,
                message=f"Correlation check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    async def check_price_anomalies(self, signal: Dict[str, Any]) -> RiskCheckResult:
        """Check for price anomalies using machine learning."""
        try:
            symbol = signal["symbol"]
            entry_price = signal.get("entry_price", 0)
            
            if not entry_price:
                return RiskCheckResult(
                    passed=True,
                    risk_type=RiskEventType.PRICE_ANOMALY,
                    message="No entry price to check",
                    severity=SeverityLevel.LOW
                )
            
            # Get historical prices for anomaly detection
            # This would typically fetch real historical data
            # For now, we'll use a simple volatility-based check
            
            # Simple implementation: check if price is within 3 standard deviations
            # of recent average (you would implement proper historical data fetching)
            
            return RiskCheckResult(
                passed=True,
                risk_type=RiskEventType.PRICE_ANOMALY,
                message=f"Price {entry_price} appears normal for {symbol}",
                severity=SeverityLevel.LOW
            )
            
        except Exception as e:
            logger.error(f"Price anomaly check failed: {e}")
            return RiskCheckResult(
                passed=False,
                risk_type=RiskEventType.PRICE_ANOMALY,
                message=f"Price anomaly check error: {e}",
                severity=SeverityLevel.MEDIUM
            )
    
    def _calculate_required_margin(self, signal: Dict[str, Any]) -> float:
        """Calculate required margin for a trade."""
        # Simplified margin calculation
        # In reality, this would depend on instrument type, volatility, etc.
        
        quantity = signal.get("quantity", 0)
        price = signal.get("entry_price", 0)
        instrument_type = signal.get("instrument_type", "EQUITY")
        
        if instrument_type == "EQUITY":
            # For cash segment, full amount is required
            return quantity * price
        elif instrument_type == "FUTURES":
            # For futures, typically 10-20% margin
            return quantity * price * 0.15
        elif instrument_type == "OPTIONS":
            # For options buying, premium amount
            return quantity * price
        
        return quantity * price
    
    def _get_sector(self, symbol: str) -> str:
        """Get sector for a symbol."""
        # This would typically lookup from a database or API
        # For now, simple mapping
        sector_mapping = {
            "RELIANCE": "Energy",
            "TCS": "IT",
            "HDFCBANK": "Banking",
            "INFY": "IT",
            "HDFC": "Financial Services",
            "ICICIBANK": "Banking",
            "KOTAKBANK": "Banking",
            "SBIN": "Banking",
            "BHARTIARTL": "Telecom",
            "ITC": "FMCG"
        }
        
        return sector_mapping.get(symbol.upper(), "Others")
    
    async def _log_risk_events(self, failed_checks: List[RiskCheckResult], signal: Dict[str, Any]):
        """Log risk events to database."""
        try:
            async with get_db_session() as session:
                for check in failed_checks:
                    risk_event = RiskEvent(
                        event_type=check.risk_type.value,
                        severity=check.severity,
                        description=check.message,
                        affected_trades={"signal": signal},
                        resolved=False
                    )
                    session.add(risk_event)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to log risk events: {e}")
    
    async def emergency_stop(self):
        """Emergency stop all trading activities."""
        try:
            self.emergency_stop_active = True
            logger.critical("EMERGENCY STOP ACTIVATED")
            
            # Log emergency stop event
            async with get_db_session() as session:
                risk_event = RiskEvent(
                    event_type="EMERGENCY_STOP",
                    severity=SeverityLevel.CRITICAL,
                    description="Emergency stop activated",
                    action_taken="All trading stopped",
                    resolved=False
                )
                session.add(risk_event)
                await session.commit()
            
            # Here you would also:
            # 1. Cancel all pending orders
            # 2. Close all positions (if configured)
            # 3. Send alerts to administrators
            # 4. Disable automated trading
            
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
    
    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        return self.emergency_stop_active
    
    async def reset_emergency_stop(self):
        """Reset emergency stop (manual intervention required)."""
        self.emergency_stop_active = False
        logger.info("Emergency stop reset")


class AnomalyDetector:
    """Machine learning-based anomaly detection for trading patterns."""
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.price_detector = IsolationForest(contamination=0.1, random_state=42)
        self.signal_detector = IsolationForest(contamination=0.05, random_state=42)
        self.volume_detector = IsolationForest(contamination=0.1, random_state=42)
        
        self.scaler = StandardScaler()
        self.is_trained = False
    
    async def detect_price_anomalies(
        self,
        symbol: str,
        current_price: float,
        historical_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detect price anomalies using isolation forest."""
        try:
            if historical_data.empty:
                return {"is_anomaly": False, "score": 0.0, "message": "No historical data"}
            
            # Prepare features
            features = self._prepare_price_features(historical_data)
            
            if len(features) < 10:  # Need minimum data
                return {"is_anomaly": False, "score": 0.0, "message": "Insufficient data"}
            
            # Fit model if not trained
            if not self.is_trained:
                self.price_detector.fit(features)
                self.is_trained = True
            
            # Check current price
            current_features = self._prepare_current_price_features(current_price, historical_data)
            anomaly_score = self.price_detector.decision_function([current_features])[0]
            is_anomaly = self.price_detector.predict([current_features])[0] == -1
            
            return {
                "is_anomaly": is_anomaly,
                "score": anomaly_score,
                "message": f"Price anomaly detected for {symbol}" if is_anomaly else "Normal price"
            }
            
        except Exception as e:
            logger.error(f"Price anomaly detection failed: {e}")
            return {"is_anomaly": False, "score": 0.0, "message": f"Error: {e}"}
    
    def _prepare_price_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare price features for anomaly detection."""
        # Calculate technical indicators
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=10).std()
        df['rsi'] = self._calculate_rsi(df['close'])
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
        
        # Select features
        features = df[['returns', 'volatility', 'rsi', 'volume_ratio']].dropna()
        
        return features.values
    
    def _prepare_current_price_features(self, current_price: float, df: pd.DataFrame) -> List[float]:
        """Prepare current price features."""
        if df.empty:
            return [0, 0, 0, 0]
        
        last_price = df['close'].iloc[-1]
        current_return = (current_price - last_price) / last_price
        
        # Calculate other features based on recent data
        recent_returns = df['close'].pct_change().tail(10)
        current_volatility = recent_returns.std()
        current_rsi = 50  # Simplified
        current_volume_ratio = 1  # Simplified
        
        return [current_return, current_volatility, current_rsi, current_volume_ratio]
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi