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
    MIS = "MIS"  # Margin Intraday Square off
    NRML = "NRML"  # Normal for F&O
    CO = "CO"  # Cover Order
    BO = "BO"  # Bracket Order


class Variety(Enum):
    """Order variety types."""
    REGULAR = "regular"
    AMO = "amo"  # After Market Order
    CO = "co"  # Cover Order
    BO = "bo"  # Bracket Order
    ICEBERG = "iceberg"  # Iceberg Order


class Validity(Enum):
    """Order validity types."""
    DAY = "DAY"
    IOC = "IOC"  # Immediate or Cancel
    TTL = "TTL"  # Time to Live


class Exchange(Enum):
    """Supported exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"  # NSE F&O
    CDS = "CDS"  # Currency
    BFO = "BFO"  # BSE F&O
    MCX = "MCX"  # Commodity


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
        self.instruments_cache = {}
        self.last_instruments_update = None
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)
            self.is_connected = True
            self._validate_connection()
    
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
            self._validate_connection()
            
            logger.info("Zerodha session generated successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to generate session: {e}")
            raise
    
    def _validate_connection(self):
        """Validate Kite connection."""
        try:
            profile = self.kite.profile()
            logger.info(f"Connected to Kite as {profile['user_name']} ({profile['user_id']})")
        except Exception as e:
            logger.error(f"Failed to validate Kite connection: {e}")
            self.is_connected = False
    
    def get_login_url(self) -> str:
        """Get the login URL for Kite Connect."""
        return self.kite.login_url()
    
    def get_instruments(self, exchange: str = "NSE", refresh: bool = False) -> List[Dict[str, Any]]:
        """Get list of instruments for an exchange.
        
        Args:
            exchange: Exchange (NSE, BSE, NFO, CDS, MCX)
            refresh: Force refresh of cached instruments
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to Kite")
                return []
            
            # Check cache
            cache_key = f"{exchange}_instruments"
            if not refresh and cache_key in self.instruments_cache:
                # Cache for 1 hour
                if self.last_instruments_update and \
                   (datetime.now() - self.last_instruments_update).seconds < 3600:
                    return self.instruments_cache[cache_key]
            
            # Fetch fresh instruments
            instruments = self.kite.instruments(exchange)
            self.instruments_cache[cache_key] = instruments
            self.last_instruments_update = datetime.now()
            
            logger.info(f"Fetched {len(instruments)} instruments for {exchange}")
            return instruments
            
        except Exception as e:
            logger.error(f"Failed to fetch instruments: {e}")
            return []
    
    def search_instrument(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        """Search for an instrument by symbol.
        
        Args:
            symbol: Trading symbol to search
            exchange: Exchange to search in
            
        Returns:
            Instrument dict with token, symbol, name etc.
        """
        try:
            instruments = self.get_instruments(exchange)
            
            for inst in instruments:
                if inst['tradingsymbol'] == symbol:
                    return inst
            
            # Try partial match
            for inst in instruments:
                if symbol in inst['tradingsymbol']:
                    logger.info(f"Found partial match: {inst['tradingsymbol']} for {symbol}")
                    return inst
            
            logger.warning(f"Instrument {symbol} not found in {exchange}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to search instrument: {e}")
            return None
    
    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """Get instrument token for a symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange
            
        Returns:
            Instrument token (integer) or None
        """
        instrument = self.search_instrument(symbol, exchange)
        if instrument:
            return instrument['instrument_token']
        return None
    
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
        variety: str = "regular",
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
            
            # Place actual order using Kite Connect API
            order_params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "validity": validity,
                "variety": variety,
                "tag": tag
            }
            
            # Add price parameters based on order type
            if order_type in [OrderType.LIMIT.value, OrderType.SL.value]:
                order_params["price"] = price
            
            if order_type in [OrderType.SL.value, OrderType.SL_M.value]:
                order_params["trigger_price"] = trigger_price
            
            # Remove variety from order_params since it's passed separately
            order_params_copy = order_params.copy()
            order_params_copy.pop('variety', None)
            
            order_id = self.kite.place_order(variety=variety, **order_params_copy)
            
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
        instrument_token: int,
        from_date: date,
        to_date: date,
        interval: str = "day",
        continuous: bool = False,
        oi: bool = False
    ) -> pd.DataFrame:
        """Get historical data for backtesting.
        
        Args:
            instrument_token: Instrument token (integer)
            from_date: Start date  
            to_date: End date
            interval: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute
            continuous: Get continuous data for expired F&O contracts
            oi: Include open interest data
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to Kite")
                return pd.DataFrame()
            
            if self.settings.enable_paper_trading:
                logger.info(f"Paper trading: Simulating historical data for token {instrument_token}")
                # Return simulated data for paper trading
                dates = pd.date_range(start=from_date, end=to_date, freq='D')
                simulated_data = []
                base_price = 100.0
                
                for d in dates:
                    open_price = base_price + (hash(str(d)) % 10 - 5)
                    high = open_price + abs(hash(str(d) + 'h') % 5)
                    low = open_price - abs(hash(str(d) + 'l') % 5)
                    close = (high + low) / 2
                    
                    simulated_data.append({
                        'date': d,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': hash(str(d) + 'v') % 1000000
                    })
                    base_price = close
                
                return pd.DataFrame(simulated_data)
            
            # Fetch real historical data using Kite Connect API
            # API expects format: GET /instruments/historical/:instrument_token/:interval
            # with from, to, continuous, oi as query params
            params = {
                "from_date": from_date,
                "to_date": to_date,
                "interval": interval
            }
            
            if continuous:
                params["continuous"] = 1
            if oi:
                params["oi"] = 1
                
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                **params
            )
            
            if data:
                df = pd.DataFrame(data)
                logger.info(f"Fetched {len(df)} records of historical data for token {instrument_token}")
                
                # Ensure datetime column is properly formatted
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return pd.DataFrame()
    
    def get_historical_data_by_symbol(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        interval: str = "day",
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Get historical data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'INFY')
            from_date: Start date
            to_date: End date
            interval: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute
            exchange: Exchange (NSE, BSE, NFO, etc.)
        """
        try:
            # Get instrument token for the symbol
            token = self.get_instrument_token(symbol, exchange)
            if not token:
                logger.error(f"Could not find instrument token for {symbol} on {exchange}")
                return pd.DataFrame()
            
            # Fetch historical data using token
            return self.get_historical_data(token, from_date, to_date, interval)
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
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
        """Handle incoming price ticks.
        
        Tick structure includes:
        - instrument_token: Instrument identifier
        - last_price: Last traded price
        - ohlc: Open, high, low, close data
        - volume: Volume traded
        - buy_quantity, sell_quantity: Pending buy/sell quantity
        - last_trade_time: Time of last trade
        - oi: Open interest (for F&O)
        - depth: Market depth (bid/ask)
        """
        for tick in ticks:
            self.price_data[tick["instrument_token"]] = tick
            logger.debug(f"Tick: {tick['instrument_token']} - LTP: {tick.get('last_price')}, Volume: {tick.get('volume')}")
    
    def _on_connect(self, ws, response):
        """Handle WebSocket connection.
        
        Once connected, subscribe to required tokens and set data mode:
        - MODE_LTP: Last traded price only
        - MODE_QUOTE: Market depth data  
        - MODE_FULL: Complete market data including OHLC
        """
        logger.info(f"WebSocket connected: {response}")
        
        # Subscribe to tokens
        if self.subscribed_tokens:
            ws.subscribe(self.subscribed_tokens)
            # Set to FULL mode for complete data
            ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
            logger.info(f"Subscribed to {len(self.subscribed_tokens)} tokens in FULL mode")
    
    def _on_close(self, ws, code, reason):
        """Handle WebSocket close."""
        logger.info(f"WebSocket closed: {code} - {reason}")
        self.price_data.clear()
    
    def _on_error(self, ws, code, reason):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {code} - {reason}")
    
    def _on_order_update(self, ws, data):
        """Handle order update via WebSocket postback."""
        logger.info(f"Order update received: {data}")
        # Process order update
        if 'order_id' in data:
            order_id = data['order_id']
            status = data.get('status')
            logger.info(f"Order {order_id} status: {status}")
    
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
        quantity = signal.get("quantity", 1)
        
        # If entry_price is not provided, get current price
        entry_price = signal.get("entry_price")
        if not entry_price:
            # Get current market price
            quotes = self.get_quote([signal["symbol"]], signal.get("exchange", "NSE"))
            if quotes:
                quote_key = f"{signal.get('exchange', 'NSE')}:{signal['symbol']}"
                entry_price = quotes.get(quote_key, {}).get("last_price", 0)
            
            if not entry_price:
                # Assume a default price for paper trading
                entry_price = 1000.0 if self.settings.enable_paper_trading else 0
        
        estimated_margin = quantity * entry_price
        
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
                # Handle signal_id - convert to int if string numeric, otherwise use None
                signal_id = signal.get("signal_id")
                if signal_id and isinstance(signal_id, str):
                    try:
                        signal_id = int(signal_id) if signal_id.isdigit() else None
                    except:
                        signal_id = None
                        
                trade = Trade(
                    signal_id=signal_id,
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
                logger.info(f"Trade stored in database: {order_id}")
                
        except Exception as e:
            logger.error(f"Failed to store trade: {e}")