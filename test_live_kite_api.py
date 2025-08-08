#!/usr/bin/env python3
"""
Comprehensive Kite API testing script for live functionality.
Tests all API endpoints we'll need for real trading.
"""

import asyncio
import sys
from datetime import datetime, date, timedelta
from kiteconnect import KiteConnect
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your Kite Connect credentials from .env
API_KEY = "p1azabgr32cikm26"
ACCESS_TOKEN = "zUKdwswW160JR0Yo2evv6BLxRrDAgmme"

class KiteAPITester:
    """Comprehensive Kite API testing class."""
    
    def __init__(self):
        """Initialize Kite API client."""
        self.kite = KiteConnect(api_key=API_KEY)
        self.kite.set_access_token(ACCESS_TOKEN)
        logger.info("Kite API client initialized")
    
    def test_connection(self):
        """Test basic connection and profile."""
        try:
            logger.info("🔌 Testing connection...")
            profile = self.kite.profile()
            
            print(f"✅ Connection successful!")
            print(f"👤 User: {profile['user_name']} ({profile['email']})")
            print(f"🏢 Broker: {profile['broker']}")
            print(f"📱 User ID: {profile['user_id']}")
            print(f"📞 Phone: {profile.get('phone', 'N/A')}")
            print(f"🎯 User Type: {profile['user_type']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def test_margins(self):
        """Test margin/funds information."""
        try:
            logger.info("💰 Testing margins...")
            margins = self.kite.margins()
            
            equity = margins.get('equity', {})
            commodity = margins.get('commodity', {})
            
            print(f"💰 Margins Information:")
            print(f"🏦 Equity:")
            if equity:
                available = equity.get('available', {})
                used = equity.get('utilised', {})
                print(f"  📊 Available: ₹{available.get('live_balance', 0):,.2f}")
                print(f"  📊 Cash: ₹{available.get('cash', 0):,.2f}")
                print(f"  📊 Opening Balance: ₹{available.get('opening_balance', 0):,.2f}")
                print(f"  🔒 Used: ₹{used.get('debits', 0):,.2f}")
            
            print(f"🌾 Commodity:")
            if commodity:
                available = commodity.get('available', {})
                used = commodity.get('utilised', {})
                print(f"  📊 Available: ₹{available.get('live_balance', 0):,.2f}")
                print(f"  📊 Cash: ₹{available.get('cash', 0):,.2f}")
                print(f"  🔒 Used: ₹{used.get('debits', 0):,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Margins test failed: {e}")
            return False
    
    def test_instruments(self):
        """Test instruments download."""
        try:
            logger.info("📋 Testing instruments...")
            
            # Get instruments for NSE
            instruments = self.kite.instruments("NSE")
            print(f"✅ NSE Instruments: {len(instruments)} instruments")
            
            # Show sample instruments
            if instruments:
                print("📝 Sample instruments:")
                for i, inst in enumerate(instruments[:5]):
                    print(f"  {i+1}. {inst['tradingsymbol']} - {inst['name']}")
            
            # Get instruments for NFO (derivatives)
            nfo_instruments = self.kite.instruments("NFO")
            print(f"✅ NFO Instruments: {len(nfo_instruments)} instruments")
            
            # Find NIFTY options
            nifty_options = [inst for inst in nfo_instruments 
                           if 'NIFTY' in inst['name'] and inst['instrument_type'] in ['CE', 'PE']]
            print(f"📊 NIFTY Options available: {len(nifty_options)}")
            
            if nifty_options:
                print("🎯 Sample NIFTY options:")
                for i, opt in enumerate(nifty_options[:3]):
                    print(f"  {i+1}. {opt['tradingsymbol']} - Strike: {opt['strike']}, Expiry: {opt['expiry']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Instruments test failed: {e}")
            return False
    
    def test_quotes(self):
        """Test real-time quotes."""
        try:
            logger.info("📊 Testing quotes...")
            
            # Test equity quotes
            equity_symbols = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY"]
            quotes = self.kite.quote(equity_symbols)
            
            print(f"💹 Equity Quotes:")
            for symbol, data in quotes.items():
                print(f"  {symbol}:")
                print(f"    💰 LTP: ₹{data.get('last_price', 0):,.2f}")
                print(f"    📈 Change: {data.get('net_change', 0):+.2f} ({data.get('oi_day_change', 0):+.2%})")
                print(f"    🔄 Volume: {data.get('volume', 0):,}")
                print(f"    ⏰ Last traded: {data.get('last_trade_time', 'N/A')}")
            
            # Test index quotes
            index_symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK"]
            index_quotes = self.kite.quote(index_symbols)
            
            print(f"📊 Index Quotes:")
            for symbol, data in index_quotes.items():
                print(f"  {symbol}: ₹{data.get('last_price', 0):,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Quotes test failed: {e}")
            return False
    
    def test_historical_data(self):
        """Test historical data fetching."""
        try:
            logger.info("📈 Testing historical data...")
            
            # Get instruments first to find token for NIFTY 50
            instruments = self.kite.instruments("NSE")
            nifty_instrument = None
            
            for inst in instruments:
                if inst['tradingsymbol'] == 'NIFTY 50' and inst['instrument_type'] == 'EQ':
                    nifty_instrument = inst
                    break
            
            if not nifty_instrument:
                print("⚠️ NIFTY 50 instrument not found")
                return False
            
            # Get historical data for last 10 days
            to_date = date.today()
            from_date = to_date - timedelta(days=10)
            
            historical_data = self.kite.historical_data(
                instrument_token=nifty_instrument['instrument_token'],
                from_date=from_date,
                to_date=to_date,
                interval="day"
            )
            
            print(f"📈 Historical Data for NIFTY 50 (last {len(historical_data)} days):")
            if historical_data:
                df = pd.DataFrame(historical_data)
                print(f"📊 Date Range: {df['date'].min()} to {df['date'].max()}")
                print(f"💰 Price Range: ₹{df['low'].min():,.2f} - ₹{df['high'].max():,.2f}")
                print(f"📈 Recent Close: ₹{df['close'].iloc[-1]:,.2f}")
                
                # Show last 3 days
                print("📅 Last 3 days:")
                for _, row in df.tail(3).iterrows():
                    print(f"  {row['date'].date()}: Open={row['open']:,.2f}, High={row['high']:,.2f}, Low={row['low']:,.2f}, Close={row['close']:,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Historical data test failed: {e}")
            return False
    
    def test_options_data(self):
        """Test options data fetching."""
        try:
            logger.info("🎯 Testing options data...")
            
            # Get NFO instruments for options
            nfo_instruments = self.kite.instruments("NFO")
            
            # Find current month NIFTY CE and PE options
            current_expiry_options = []
            for inst in nfo_instruments:
                if ('NIFTY' in inst['name'] and 
                    inst['instrument_type'] in ['CE', 'PE'] and 
                    inst['expiry'] and
                    len(current_expiry_options) < 4):  # Get 4 options for testing
                    current_expiry_options.append(inst)
            
            if current_expiry_options:
                print(f"🎯 Found {len(current_expiry_options)} NIFTY options for testing:")
                
                option_symbols = []
                for opt in current_expiry_options[:4]:
                    symbol = f"NFO:{opt['tradingsymbol']}"
                    option_symbols.append(symbol)
                    print(f"  📋 {opt['tradingsymbol']} - Strike: {opt['strike']}, Type: {opt['instrument_type']}, Expiry: {opt['expiry']}")
                
                # Get quotes for these options
                if option_symbols:
                    option_quotes = self.kite.quote(option_symbols)
                    
                    print(f"💹 Option Quotes:")
                    for symbol, data in option_quotes.items():
                        print(f"  {symbol.split(':')[1]}:")
                        print(f"    💰 LTP: ₹{data.get('last_price', 0):.2f}")
                        print(f"    📊 OI: {data.get('oi', 0):,}")
                        print(f"    🔄 Volume: {data.get('volume', 0):,}")
                        
                        # Get historical data for one option
                        if len(option_symbols) > 0 and symbol == option_symbols[0]:
                            opt_token = None
                            for opt in current_expiry_options:
                                if f"NFO:{opt['tradingsymbol']}" == symbol:
                                    opt_token = opt['instrument_token']
                                    break
                            
                            if opt_token:
                                try:
                                    to_date = date.today()
                                    from_date = to_date - timedelta(days=5)
                                    
                                    opt_historical = self.kite.historical_data(
                                        instrument_token=opt_token,
                                        from_date=from_date,
                                        to_date=to_date,
                                        interval="day"
                                    )
                                    
                                    if opt_historical:
                                        print(f"    📈 Historical: {len(opt_historical)} days available")
                                        latest = opt_historical[-1]
                                        print(f"    📅 Latest: {latest['date'].date()} - Close: ₹{latest['close']:.2f}")
                                except:
                                    print(f"    ⚠️ No historical data available")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Options test failed: {e}")
            return False
    
    def test_orders_and_positions(self):
        """Test orders and positions (read-only)."""
        try:
            logger.info("📋 Testing orders and positions...")
            
            # Get today's orders
            orders = self.kite.orders()
            print(f"📝 Orders today: {len(orders)}")
            
            if orders:
                print("📋 Recent orders:")
                for order in orders[-3:]:  # Show last 3 orders
                    print(f"  🎯 {order.get('tradingsymbol', 'N/A')} - {order.get('transaction_type', 'N/A')} - {order.get('quantity', 0)} @ ₹{order.get('price', 0)} - Status: {order.get('status', 'N/A')}")
            
            # Get positions
            positions = self.kite.positions()
            net_positions = positions.get('net', [])
            day_positions = positions.get('day', [])
            
            print(f"📊 Net Positions: {len(net_positions)}")
            print(f"📊 Day Positions: {len(day_positions)}")
            
            if net_positions:
                print("💼 Net Positions:")
                for pos in net_positions[:5]:  # Show first 5 positions
                    pnl = pos.get('pnl', 0)
                    pnl_symbol = "📈" if pnl >= 0 else "📉"
                    print(f"  {pnl_symbol} {pos.get('tradingsymbol', 'N/A')}: Qty={pos.get('quantity', 0)}, P&L=₹{pnl:.2f}")
            
            # Get holdings
            holdings = self.kite.holdings()
            print(f"🏦 Holdings: {len(holdings)}")
            
            if holdings:
                print("💎 Holdings:")
                for holding in holdings[:5]:  # Show first 5 holdings
                    pnl = holding.get('pnl', 0)
                    pnl_symbol = "📈" if pnl >= 0 else "📉"
                    print(f"  {pnl_symbol} {holding.get('tradingsymbol', 'N/A')}: Qty={holding.get('quantity', 0)}, P&L=₹{pnl:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Orders/Positions test failed: {e}")
            return False
    
    def test_order_simulation(self):
        """Test order placement parameters (simulation only - no actual orders)."""
        try:
            logger.info("🧪 Testing order parameters (simulation)...")
            
            # Test order parameter validation
            test_orders = [
                {
                    "name": "Market Buy Order",
                    "params": {
                        "variety": "regular",
                        "tradingsymbol": "RELIANCE",
                        "exchange": "NSE",
                        "transaction_type": "BUY",
                        "quantity": 1,
                        "order_type": "MARKET",
                        "product": "CNC",
                        "validity": "DAY",
                        "tag": "test_order"
                    }
                },
                {
                    "name": "Limit Sell Order", 
                    "params": {
                        "variety": "regular",
                        "tradingsymbol": "TCS",
                        "exchange": "NSE",
                        "transaction_type": "SELL",
                        "quantity": 1,
                        "order_type": "LIMIT",
                        "price": 3500.0,
                        "product": "CNC",
                        "validity": "DAY",
                        "tag": "test_order"
                    }
                },
                {
                    "name": "Stop Loss Order",
                    "params": {
                        "variety": "regular",
                        "tradingsymbol": "INFY",
                        "exchange": "NSE",
                        "transaction_type": "SELL",
                        "quantity": 1,
                        "order_type": "SL",
                        "price": 1500.0,
                        "trigger_price": 1480.0,
                        "product": "CNC",
                        "validity": "DAY",
                        "tag": "test_order"
                    }
                }
            ]
            
            print("🧪 Order Parameter Validation:")
            for test_order in test_orders:
                print(f"\n📋 {test_order['name']}:")
                params = test_order['params']
                
                # Validate required parameters
                required_params = ['tradingsymbol', 'exchange', 'transaction_type', 'quantity', 'order_type', 'product']
                missing_params = [param for param in required_params if param not in params]
                
                if missing_params:
                    print(f"  ❌ Missing parameters: {missing_params}")
                else:
                    print(f"  ✅ All required parameters present")
                
                # Show order details
                print(f"  🎯 Symbol: {params.get('tradingsymbol')} ({params.get('exchange')})")
                print(f"  📊 {params.get('transaction_type')} {params.get('quantity')} @ {params.get('order_type')}")
                
                if 'price' in params:
                    print(f"  💰 Price: ₹{params['price']}")
                if 'trigger_price' in params:
                    print(f"  🚨 Trigger: ₹{params['trigger_price']}")
                
                print(f"  📦 Product: {params.get('product')}")
                print(f"  ⏰ Validity: {params.get('validity')}")
                
                # NOTE: We're NOT actually placing these orders - just validating parameters
                print(f"  ℹ️  (Parameters validated - no actual order placed)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Order simulation test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Comprehensive Kite API Test Suite")
        print("=" * 60)
        
        tests = [
            ("Connection & Profile", self.test_connection),
            ("Margins & Funds", self.test_margins), 
            ("Instruments List", self.test_instruments),
            ("Real-time Quotes", self.test_quotes),
            ("Historical Data", self.test_historical_data),
            ("Options Data", self.test_options_data),
            ("Orders & Positions", self.test_orders_and_positions),
            ("Order Parameters", self.test_order_simulation)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                success = test_func()
                results[test_name] = success
                
                if success:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:<25} {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Kite API is ready for live trading.")
            print("🔸 You can now update your ZerodhaTrader class to use real API")
            print("🔸 Set ENABLE_LIVE_TRADING=true in .env when ready")
        else:
            print("⚠️ Some tests failed. Please check the errors above.")
            print("🔧 Fix any issues before enabling live trading")

def main():
    """Main function."""
    print("⚠️  IMPORTANT SAFETY NOTICE:")
    print("🔸 This script tests live Kite API with your real account")
    print("🔸 No actual trades will be placed (read-only operations)")
    print("🔸 Your access token is valid until market close today")
    print()
    
    response = input("Continue with API testing? (y/N): ").strip().lower()
    if response != 'y':
        print("👋 Test cancelled.")
        return
    
    # Run tests
    tester = KiteAPITester()
    
    # Use asyncio to run the async test function
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()