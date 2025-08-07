"""Zerodha Kite Connect integration for order management and market data."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum
import asyncio
from threading import Thread
import json

from kiteconnect import KiteConnect, KiteTicker
import pandas as pd

from config.settings import get_settings
from src.database.models import Trade, Position, TradeStatus, InstrumentType
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()


class OrderType(Enum):
    """Kite order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class TransactionType(Enum):
    """Transaction types."""
    BUY = "BUY"
    SELL = "SELL"


class Product(Enum):
    """Kite product types."""
    CNC = "CNC"  # Cash and Carry for equity
    MIS = "MIS"  # Intraday
    NRML = "NRML"  # Normal for F&O


class ZerodhaTrader:
    """Zerodha Kite Connect integration with order management."""
    
    def __init__(self):
        """Initialize Zerodha trader."""
        self.settings = settings
        self.kite = KiteConnect(api_key=self.settings.kite_api_key)
        self.kws = None
        self.access_token = self.settings.kite_access_token
        self.is_connected = False
        self.ticker_thread = None
        self.subscribed_tokens = []
        self.price_data = {}
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)
            self.is_connected = True
    
    def generate_session(self, request_token: str) -> str:
        """Generate access token from request token."""
        try:
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.settings.kite_api_secret
            )
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            self.is_connected = True
            
            logger.info("Zerodha session generated successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            raise
    
    def get_login_url(self) -> str:
        """Get the login URL for Kite Connect."""
        return self.kite.login_url()
    
    async def place_order(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: str = OrderType.MARKET.value,
        product: str = Product.CNC.value,
        exchange: str = "NSE",
        validity: str = "DAY",
        tag: str = "trading_bot"
    ) -> Optional[str]:
        """Place an order on Kite."""
        try:
            if not self.is_connected:
                logger.error("Not connected to Kite")
                return None
            
            if self.settings.enable_paper_trading:
                # Simulate order in paper trading mode
                order_id = f"PAPER_{datetime.now().timestamp()}"
                logger.info(f"Paper trading: Simulated order {order_id} for {symbol}")
                return order_id
            
            if not self.settings.enable_live_trading:
                logger.warning("Live trading is disabled")
                return None
            
            # Place actual order
            order_params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "validity": validity,
                "tag": tag
            }
            
            # Add price parameters based on order type
            if order_type in [OrderType.LIMIT.value, OrderType.SL.value]:
                order_params["price"] = price
            
            if order_type in [OrderType.SL.value, OrderType.SL_M.value]:
                order_params["trigger_price"] = trigger_price
            
            order_id = self.kite.place_order(**order_params)
            
            logger.info(f"Order placed successfully: {order_id} for {symbol}")
            return str(order_id)
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
    
    async def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None,
        trigger_price: Optional[float] = None
    ) -> bool:
        """Modify an existing order."""
        try:
            if not self.is_connected:
                return False
            
            if self.settings.enable_paper_trading:
                logger.info(f"Paper trading: Modified order {order_id}")
                return True
            
            params = {}
            if price is not None:
                params["price"] = price
            if quantity is not None:
                params["quantity"] = quantity
            if trigger_price is not None:
                params["trigger_price"] = trigger_price
            
            self.kite.modify_order(variety="regular", order_id=order_id, **params)
            
            logger.info(f"Order modified successfully: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to modify order: {e}")
            return False
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            if not self.is_connected:
                return False
            
            if self.settings.enable_paper_trading:
                logger.info(f"Paper trading: Cancelled order {order_id}")
                return True
            
            self.kite.cancel_order(variety="regular", order_id=order_id)
            
            logger.info(f"Order cancelled successfully: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders for the day."""
        try:
            if not self.is_connected:
                return []
            
            if self.settings.enable_paper_trading:
                return []  # Return empty list for paper trading
            
            return self.kite.orders()
            
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            return []
    
    def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all positions."""
        try:
            if not self.is_connected:
                return {"net": [], "day": []}
            
            if self.settings.enable_paper_trading:
                # Return paper trading positions from database
                return {"net": [], "day": []}
            
            return self.kite.positions()
            
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return {"net": [], "day": []}
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get holdings."""
        try:
            if not self.is_connected:
                return []
            
            if self.settings.enable_paper_trading:
                return []
            
            return self.kite.holdings()
            
        except Exception as e:
            logger.error(f"Failed to fetch holdings: {e}")
            return []
    
    def get_margins(self) -> Dict[str, Any]:
        """Get account margins."""
        try:
            if not self.is_connected:
                return {}
            
            if self.settings.enable_paper_trading:
                return {
                    "equity": {"available": {"cash": 100000}},
                    "commodity": {"available": {"cash": 0}}
                }
            
            return self.kite.margins()
            
        except Exception as e:
            logger.error(f"Failed to fetch margins: {e}")
            return {}
    
    def get_quote(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Any]:
        """Get real-time quotes for symbols."""
        try:
            if not self.is_connected:
                return {}
            
            # Format symbols with exchange
            formatted_symbols = [f"{exchange}:{symbol}" for symbol in symbols]
            
            return self.kite.quote(formatted_symbols)
            
        except Exception as e:
            logger.error(f"Failed to fetch quotes: {e}")
            return {}
    
    def get_historical_data(
        self,
        instrument_token: str,
        from_date: date,
        to_date: date,
        interval: str = "day"
    ) -> pd.DataFrame:
        """Get historical data for backtesting."""
        try:
            if not self.is_connected:
                return pd.DataFrame()
            
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return pd.DataFrame()
    
    def start_price_streaming(self, tokens: List[int]):
        """Start WebSocket price streaming."""
        try:
            if not self.access_token:
                logger.error("No access token for WebSocket")
                return
            
            self.kws = KiteTicker(
                self.settings.kite_api_key,
                self.access_token
            )
            
            # Set callbacks
            self.kws.on_ticks = self._on_ticks
            self.kws.on_connect = self._on_connect
            self.kws.on_close = self._on_close
            self.kws.on_error = self._on_error
            
            self.subscribed_tokens = tokens
            
            # Start ticker in a separate thread
            self.ticker_thread = Thread(target=self.kws.connect)
            self.ticker_thread.daemon = True
            self.ticker_thread.start()
            
            logger.info("Price streaming started")
            
        except Exception as e:
            logger.error(f"Failed to start price streaming: {e}")
    
    def stop_price_streaming(self):
        """Stop WebSocket price streaming."""
        try:
            if self.kws:
                self.kws.stop()
                logger.info("Price streaming stopped")
        except Exception as e:
            logger.error(f"Failed to stop price streaming: {e}")
    
    def _on_ticks(self, ws, ticks):
        """Handle incoming price ticks."""
        for tick in ticks:
            self.price_data[tick["instrument_token"]] = tick
            logger.debug(f"Tick: {tick['instrument_token']} - {tick.get('last_price')}")
    
    def _on_connect(self, ws, response):
        """Handle WebSocket connection."""
        logger.info("WebSocket connected")
        
        # Subscribe to tokens
        if self.subscribed_tokens:
            ws.subscribe(self.subscribed_tokens)
            ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
    
    def _on_close(self, ws, code, reason):
        """Handle WebSocket close."""
        logger.info(f"WebSocket closed: {code} - {reason}")
    
    def _on_error(self, ws, code, reason):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {code} - {reason}")
    
    async def execute_signal(self, signal: Dict[str, Any]) -> Optional[str]:
        """Execute a trading signal."""
        try:
            # Validate signal
            if not self._validate_signal(signal):
                logger.warning("Invalid signal, skipping execution")
                return None
            
            # Check margins
            if not await self._check_margin_requirements(signal):
                logger.warning("Insufficient margin for trade")
                return None
            
            # Determine order parameters
            order_params = self._prepare_order_params(signal)
            
            # Place order
            order_id = await self.place_order(**order_params)
            
            if order_id:
                # Store trade in database
                await self._store_trade(signal, order_id)
            
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to execute signal: {e}")
            return None
    
    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate trading signal."""
        required_fields = ["symbol", "signal_type", "quantity"]
        return all(field in signal for field in required_fields)
    
    async def _check_margin_requirements(self, signal: Dict[str, Any]) -> bool:
        """Check if sufficient margin is available."""
        margins = self.get_margins()
        
        if not margins:
            return False
        
        available_cash = margins.get("equity", {}).get("available", {}).get("cash", 0)
        
        # Estimate required margin (simplified)
        estimated_margin = signal.get("quantity", 0) * signal.get("entry_price", 0)
        
        return available_cash >= estimated_margin
    
    def _prepare_order_params(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare order parameters from signal."""
        params = {
            "symbol": signal["symbol"],
            "transaction_type": signal["signal_type"],
            "quantity": signal["quantity"],
            "order_type": OrderType.LIMIT.value if signal.get("entry_price") else OrderType.MARKET.value,
            "product": Product.CNC.value if signal.get("instrument_type") == "EQUITY" else Product.NRML.value,
        }
        
        if signal.get("entry_price"):
            params["price"] = signal["entry_price"]
        
        if signal.get("stop_loss"):
            params["trigger_price"] = signal["stop_loss"]
        
        return params
    
    async def _store_trade(self, signal: Dict[str, Any], order_id: str):
        """Store trade in database."""
        try:
            async with get_db_session() as session:
                trade = Trade(
                    signal_id=signal.get("signal_id"),
                    order_id=order_id,
                    symbol=signal["symbol"],
                    instrument_type=InstrumentType[signal.get("instrument_type", "EQUITY")],
                    trade_type=signal["signal_type"],
                    quantity=signal["quantity"],
                    entry_price=signal.get("entry_price"),
                    stop_loss=signal.get("stop_loss"),
                    target_price=signal.get("target_price"),
                    status=TradeStatus.PENDING,
                    entry_time=datetime.now()
                )
                session.add(trade)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store trade: {e}")