#!/usr/bin/env python3
"""
Test Zerodha KiteConnect integration with paper trading simulation.
"""

import asyncio
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

# Zerodha configuration
KITE_API_KEY = os.getenv("KITE_API_KEY")
KITE_API_SECRET = os.getenv("KITE_API_SECRET") 
KITE_ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN", "dummy_token_for_testing")
KITE_USER_ID = os.getenv("KITE_USER_ID")

# Enable paper trading mode
ENABLE_PAPER_TRADING = True

class PaperTradingClient:
    """Mock Zerodha client for paper trading."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.access_token = None
        self._orders = {}  # Use underscore to avoid method name collision
        self._trades = {}
        self._positions = {}
        self.order_counter = 100000
        self.trade_counter = 200000
        
        # Mock market data
        self.mock_prices = {
            "NSE:NIFTY 50": 25000.0,
            "NSE:BANKNIFTY": 54000.0,
            "NSE:RELIANCE": 2850.0,
            "NSE:SBIN": 420.0,
            "NSE:INFY": 1750.0,
            "NFO:NIFTY25000CE": 50.0,
            "NFO:NIFTY24800PE": 30.0,
            "NFO:BANKNIFTY54000CE": 120.0,
        }
        
        print("📝 Paper Trading Mode Enabled")
        print("💡 All orders will be simulated - no real money involved")
    
    def set_access_token(self, access_token: str):
        """Set access token (simulated)."""
        self.access_token = access_token
        print(f"✅ Access token set (simulated): {access_token[:20]}...")
    
    def place_order(self, variety="regular", exchange=None, tradingsymbol=None, 
                   transaction_type=None, quantity=None, product=None, 
                   order_type=None, price=None, validity=None, 
                   disclosed_quantity=None, trigger_price=None, 
                   squareoff=None, stoploss=None, trailing_stoploss=None, 
                   tag=None):
        """Simulate placing an order."""
        
        if not self.access_token:
            raise Exception("Access token not set")
        
        # Generate order ID
        order_id = str(self.order_counter)
        self.order_counter += 1
        
        # Create order object
        order = {
            "order_id": order_id,
            "variety": variety,
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "product": product,
            "order_type": order_type,
            "price": price,
            "validity": validity,
            "disclosed_quantity": disclosed_quantity or 0,
            "trigger_price": trigger_price or 0,
            "status": "COMPLETE" if order_type == "MARKET" else "OPEN",
            "status_message": None,
            "order_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_order_id": f"EX{order_id}",
            "parent_order_id": None,
            "filled_quantity": quantity if order_type == "MARKET" else 0,
            "pending_quantity": 0 if order_type == "MARKET" else quantity,
            "cancelled_quantity": 0,
            "average_price": self._get_mock_price(f"{exchange}:{tradingsymbol}") if order_type == "MARKET" else 0,
            "tag": tag or "",
            "placed_by": KITE_USER_ID or "PAPER_USER"
        }
        
        self._orders[order_id] = order
        
        # If market order, also create a trade
        if order_type == "MARKET":
            self._create_trade(order)
        
        print(f"📊 Paper Order Placed: {transaction_type} {quantity} {tradingsymbol} @ {order_type}")
        print(f"   Order ID: {order_id}")
        print(f"   Status: {order['status']}")
        
        return order_id
    
    def _create_trade(self, order):
        """Create a simulated trade for executed order."""
        trade_id = str(self.trade_counter)
        self.trade_counter += 1
        
        trade = {
            "trade_id": trade_id,
            "order_id": order["order_id"],
            "exchange": order["exchange"],
            "tradingsymbol": order["tradingsymbol"],
            "instrument_token": hash(order["tradingsymbol"]) % 1000000,  # Mock token
            "product": order["product"],
            "average_price": order["average_price"],
            "quantity": order["quantity"],
            "exchange_order_id": order["exchange_order_id"],
            "transaction_type": order["transaction_type"],
            "fill_timestamp": order["order_timestamp"],
            "order_timestamp": order["order_timestamp"].split()[1],
            "exchange_timestamp": order["exchange_timestamp"]
        }
        
        self._trades[trade_id] = trade
        
        # Update positions
        position_key = f"{order['exchange']}:{order['tradingsymbol']}"
        if position_key not in self._positions:
            self._positions[position_key] = {
                "tradingsymbol": order["tradingsymbol"],
                "exchange": order["exchange"],
                "instrument_token": trade["instrument_token"],
                "product": order["product"],
                "quantity": 0,
                "overnight_quantity": 0,
                "multiplier": 1,
                "average_price": 0,
                "close_price": order["average_price"],
                "last_price": order["average_price"],
                "value": 0,
                "pnl": 0,
                "m2m": 0,
                "unrealised": 0,
                "realised": 0,
                "buy_quantity": 0,
                "buy_price": 0,
                "buy_value": 0,
                "buy_m2m": 0,
                "sell_quantity": 0,
                "sell_price": 0,
                "sell_value": 0,
                "sell_m2m": 0,
                "day_buy_quantity": 0,
                "day_buy_price": 0,
                "day_buy_value": 0,
                "day_sell_quantity": 0,
                "day_sell_price": 0,
                "day_sell_value": 0
            }
        
        # Update position based on transaction type
        position = self._positions[position_key]
        if order["transaction_type"] == "BUY":
            position["buy_quantity"] += order["quantity"]
            position["day_buy_quantity"] += order["quantity"]
            position["quantity"] += order["quantity"]
        else:
            position["sell_quantity"] += order["quantity"]
            position["day_sell_quantity"] += order["quantity"] 
            position["quantity"] -= order["quantity"]
        
        return trade_id
    
    def _get_mock_price(self, symbol: str) -> float:
        """Get mock price for a symbol."""
        return self.mock_prices.get(symbol, 100.0)
    
    def orders(self):
        """Get all orders."""
        return list(self._orders.values())
    
    def get_orders(self):
        """Get all orders (alternative method name)."""
        return list(self._orders.values())
    
    def trades(self):
        """Get all trades.""" 
        return list(self._trades.values())
    
    def get_trades(self):
        """Get all trades (alternative method name)."""
        return list(self._trades.values())
    
    def positions(self):
        """Get positions."""
        net_positions = []
        day_positions = []
        
        for pos in self._positions.values():
            if pos["quantity"] != 0:
                net_positions.append(pos)
            if pos["day_buy_quantity"] > 0 or pos["day_sell_quantity"] > 0:
                day_positions.append(pos)
        
        return {
            "net": net_positions,
            "day": day_positions
        }
    
    def margins(self, segment=None):
        """Get margin information (simulated)."""
        return {
            "equity": {
                "enabled": True,
                "net": 100000.0,  # Mock available margin
                "available": {
                    "adhoc_margin": 0,
                    "cash": 50000.0,
                    "collateral": 0,
                    "intraday_payin": 0,
                    "live_balance": 100000.0,
                    "opening_balance": 100000.0
                },
                "utilised": {
                    "debits": 0,
                    "exposure": 0,
                    "m2m_realised": 0,
                    "m2m_unrealised": 0,
                    "option_premium": 0,
                    "payout": 0,
                    "span": 0,
                    "holding_sales": 0,
                    "turnover": 0,
                    "liquid_collateral": 0,
                    "stock_collateral": 0
                }
            }
        }

class ZerodhaTrader:
    """Enhanced Zerodha trader with paper trading support."""
    
    def __init__(self, api_key: str, paper_trading: bool = True):
        self.api_key = api_key
        self.paper_trading = paper_trading
        
        if paper_trading:
            self.client = PaperTradingClient(api_key)
        else:
            self.client = KiteConnect(api_key=api_key)
        
        self.access_token = None
        
        # Order constants (from KiteConnect)
        self.EXCHANGE_NSE = "NSE"
        self.EXCHANGE_BSE = "BSE" 
        self.EXCHANGE_NFO = "NFO"
        self.EXCHANGE_CDS = "CDS"
        self.EXCHANGE_MCX = "MCX"
        
        self.TRANSACTION_TYPE_BUY = "BUY"
        self.TRANSACTION_TYPE_SELL = "SELL"
        
        self.ORDER_TYPE_MARKET = "MARKET"
        self.ORDER_TYPE_LIMIT = "LIMIT"
        self.ORDER_TYPE_SL = "SL"
        self.ORDER_TYPE_SL_M = "SL-M"
        
        self.PRODUCT_CNC = "CNC"
        self.PRODUCT_MIS = "MIS"
        self.PRODUCT_NRML = "NRML"
        
        self.VALIDITY_DAY = "DAY"
        self.VALIDITY_IOC = "IOC"
    
    def authenticate(self, access_token: str = None):
        """Authenticate with Zerodha."""
        if not access_token:
            access_token = KITE_ACCESS_TOKEN
        
        self.access_token = access_token
        self.client.set_access_token(access_token)
        
        if self.paper_trading:
            print("✅ Paper trading authentication successful")
        else:
            print("✅ Live trading authentication successful")
    
    async def place_order(self, signal: Dict[str, Any]) -> Optional[str]:
        """Place an order based on a trading signal."""
        try:
            # Extract signal information
            symbol = signal.get("symbol", "NIFTY")
            signal_type = signal.get("signal_type", "BUY")
            instrument_type = signal.get("instrument_type", "OPTIONS")
            quantity = signal.get("quantity", 1)
            entry_price = signal.get("entry_price")
            
            # Determine exchange and trading symbol
            if instrument_type == "OPTIONS":
                exchange = self.EXCHANGE_NFO
                strike_price = signal.get("strike_price", 25000)
                option_type = signal.get("option_type", "CE")
                
                # Format options symbol (simplified)
                if symbol == "NIFTY":
                    tradingsymbol = f"NIFTY{strike_price}{option_type}"
                elif symbol == "BANKNIFTY":
                    tradingsymbol = f"BANKNIFTY{strike_price}{option_type}"
                else:
                    tradingsymbol = f"{symbol}{strike_price}{option_type}"
            
            elif instrument_type == "FUTURES":
                exchange = self.EXCHANGE_NFO  
                tradingsymbol = f"{symbol}FUT"
            
            else:  # EQUITY
                exchange = self.EXCHANGE_NSE
                tradingsymbol = symbol
            
            # Determine order type and price
            if entry_price:
                order_type = self.ORDER_TYPE_LIMIT
                price = entry_price
            else:
                order_type = self.ORDER_TYPE_MARKET
                price = None
            
            # Place the order
            order_id = self.client.place_order(
                variety="regular",
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=signal_type,
                quantity=quantity,
                product=self.PRODUCT_MIS,  # Intraday for now
                order_type=order_type,
                price=price,
                validity=self.VALIDITY_DAY,
                tag=f"bot_signal_{signal.get('id', 'unknown')}"
            )
            
            return order_id
            
        except Exception as e:
            print(f"❌ Order placement failed: {e}")
            return None
    
    def get_orders(self):
        """Get all orders."""
        return self.client.orders()
    
    def get_trades(self):
        """Get all trades."""
        return self.client.trades()
    
    def get_positions(self):
        """Get positions."""
        return self.client.positions()
    
    def get_margins(self):
        """Get margin information."""
        return self.client.margins()

async def test_zerodha_authentication():
    """Test Zerodha authentication (simulated)."""
    print("🔍 Testing Zerodha authentication...")
    
    if not KITE_API_KEY:
        print("❌ KITE_API_KEY not found in .env file")
        return False
    
    print(f"🔑 API Key: {KITE_API_KEY}")
    print(f"👤 User ID: {KITE_USER_ID}")
    print(f"📝 Paper Trading: {ENABLE_PAPER_TRADING}")
    
    try:
        trader = ZerodhaTrader(KITE_API_KEY, paper_trading=ENABLE_PAPER_TRADING)
        trader.authenticate()
        
        # Test margin call
        margins = trader.get_margins()
        print(f"✅ Margin info retrieved: ₹{margins['equity']['net']:,.2f} available")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

async def test_order_placement():
    """Test placing sample orders."""
    print("\n🔍 Testing order placement...")
    
    trader = ZerodhaTrader(KITE_API_KEY, paper_trading=ENABLE_PAPER_TRADING)
    trader.authenticate()
    
    # Sample trading signals to test
    test_signals = [
        {
            "id": 1,
            "signal_type": "BUY",
            "instrument_type": "OPTIONS", 
            "symbol": "NIFTY",
            "strike_price": 25000,
            "option_type": "CE",
            "quantity": 50,
            "entry_price": 50.0,
            "confidence_score": 0.85
        },
        {
            "id": 2,
            "signal_type": "SELL",
            "instrument_type": "OPTIONS",
            "symbol": "BANKNIFTY", 
            "strike_price": 54000,
            "option_type": "PE",
            "quantity": 25,
            "entry_price": None,  # Market order
            "confidence_score": 0.90
        },
        {
            "id": 3,
            "signal_type": "BUY",
            "instrument_type": "EQUITY",
            "symbol": "RELIANCE",
            "quantity": 10,
            "entry_price": 2850.0,
            "confidence_score": 0.75
        }
    ]
    
    order_ids = []
    
    for signal in test_signals:
        print(f"\n📊 Testing signal: {signal['signal_type']} {signal.get('quantity')} {signal.get('symbol')}")
        
        order_id = await trader.place_order(signal)
        
        if order_id:
            order_ids.append(order_id)
            print(f"   ✅ Order placed successfully: {order_id}")
        else:
            print(f"   ❌ Order placement failed")
        
        # Small delay between orders
        await asyncio.sleep(0.5)
    
    return order_ids, trader

async def test_order_management():
    """Test order and position management."""
    print("\n🔍 Testing order management...")
    
    # Place some test orders first
    order_ids, trader = await test_order_placement()
    
    # Test getting orders
    print("\n📋 All Orders:")
    orders = trader.get_orders()
    for order in orders:
        print(f"   Order {order['order_id']}: {order['status']} - {order['transaction_type']} {order['quantity']} {order['tradingsymbol']}")
    
    # Test getting trades  
    print("\n📋 All Trades:")
    trades = trader.get_trades()
    for trade in trades:
        print(f"   Trade {trade['trade_id']}: {trade['transaction_type']} {trade['quantity']} {trade['tradingsymbol']} @ ₹{trade['average_price']}")
    
    # Test getting positions
    print("\n📋 Positions:")
    positions = trader.get_positions()
    
    if positions['net']:
        print("   Net Positions:")
        for pos in positions['net']:
            print(f"     {pos['tradingsymbol']}: {pos['quantity']} @ ₹{pos.get('last_price', pos.get('close_price', 0))}")
    else:
        print("   No net positions")
    
    if positions['day']:
        print("   Day Positions:")  
        for pos in positions['day']:
            buy_qty = pos.get('day_buy_quantity', 0)
            sell_qty = pos.get('day_sell_quantity', 0)
            print(f"     {pos['tradingsymbol']}: Buy {buy_qty}, Sell {sell_qty}")
    
    return True

async def test_zerodha_integration():
    """Test integration with actual Zerodha trader module."""
    print("\n🔍 Testing Zerodha trader module integration...")
    
    try:
        from trading.zerodha_client import ZerodhaTrader as ActualTrader
        
        trader = ActualTrader()
        print("✅ Zerodha trader module imported successfully")
        
        # This would require actual access token
        print("💡 Live integration requires valid access token")
        print("💡 Use paper trading mode for now")
        
    except ImportError as e:
        print(f"❌ Could not import Zerodha trader: {e}")
        print("💡 This is expected if there are import issues - we'll fix them")
    except Exception as e:
        print(f"❌ Zerodha trader test failed: {e}")

async def main():
    """Main test function."""
    print("🚀 Testing Zerodha KiteConnect Integration")
    print("=" * 60)
    print(f"📝 Paper Trading Mode: {ENABLE_PAPER_TRADING}")
    print("=" * 60)
    
    # Test authentication
    auth_success = await test_zerodha_authentication()
    
    if auth_success:
        # Test order placement
        await test_order_placement()
        
        # Test order management
        await test_order_management()
        
        # Test integration with actual module
        await test_zerodha_integration()
        
        print("\n" + "=" * 60)
        print("🎉 Zerodha integration tests completed!")
        print("\n💡 Zerodha will be used for:")
        print("   - Placing buy/sell orders")
        print("   - Real-time position tracking")
        print("   - Margin and risk monitoring") 
        print("   - Order status updates")
        print("   - P&L calculation")
        
        if ENABLE_PAPER_TRADING:
            print("\n⚠️  Remember to switch to live trading only after thorough testing!")
    else:
        print("\n❌ Zerodha authentication failed - cannot run other tests")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")