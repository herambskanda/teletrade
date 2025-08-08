#!/usr/bin/env python3
"""
Test script for Kite API integration with real APIs.
Tests historical data fetching and order placement functionality.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.trading.zerodha_client import ZerodhaTrader
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_kite_integration():
    """Test complete Kite API integration."""
    
    print("🚀 Testing Kite API Integration")
    print("=" * 60)
    
    # Initialize trader
    trader = ZerodhaTrader()
    settings = get_settings()
    
    if not trader.is_connected:
        print("❌ Failed to connect to Kite API")
        print("Please check your access token in .env file")
        return
    
    print(f"✅ Connected to Kite API")
    print(f"📊 Mode: {'Paper Trading' if settings.enable_paper_trading else 'Live Trading'}")
    print()
    
    # Test 1: Get Margins
    print("💰 Test 1: Account Margins")
    print("-" * 40)
    margins = trader.get_margins()
    if margins:
        equity = margins.get('equity', {})
        available = equity.get('available', {})
        print(f"Available Cash: ₹{available.get('cash', 0):,.2f}")
        print(f"Total Balance: ₹{available.get('live_balance', 0):,.2f}")
    else:
        print("❌ Could not fetch margins")
    print()
    
    # Test 2: Get Instruments
    print("📋 Test 2: Fetching Instruments")
    print("-" * 40)
    instruments = trader.get_instruments("NSE")
    print(f"Total NSE instruments: {len(instruments)}")
    
    # Search for specific stocks
    test_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    print(f"\nSearching for test symbols:")
    for symbol in test_symbols:
        instrument = trader.search_instrument(symbol, "NSE")
        if instrument:
            print(f"✅ {symbol}: Token={instrument['instrument_token']}, "
                  f"Exchange={instrument['exchange']}, Type={instrument['instrument_type']}")
        else:
            print(f"❌ {symbol}: Not found")
    print()
    
    # Test 3: Real-time Quotes
    print("💹 Test 3: Real-time Quotes")
    print("-" * 40)
    quote_symbols = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY"]
    quotes = trader.get_quote(quote_symbols)
    
    for symbol, data in quotes.items():
        print(f"{symbol}:")
        print(f"  Last Price: ₹{data.get('last_price', 0):,.2f}")
        print(f"  Change: {data.get('net_change', 0):+.2f}")
        print(f"  Volume: {data.get('volume', 0):,}")
    print()
    
    # Test 4: Historical Data
    print("📈 Test 4: Historical Data")
    print("-" * 40)
    
    # Get historical data for RELIANCE
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    
    print(f"Fetching 30 days data for RELIANCE...")
    historical_data = trader.get_historical_data_by_symbol(
        symbol="RELIANCE",
        from_date=from_date,
        to_date=to_date,
        interval="day",
        exchange="NSE"
    )
    
    if not historical_data.empty:
        print(f"✅ Fetched {len(historical_data)} days of data")
        print(f"Date Range: {historical_data['date'].min()} to {historical_data['date'].max()}")
        print(f"Price Range: ₹{historical_data['low'].min():,.2f} - ₹{historical_data['high'].max():,.2f}")
        
        # Show last 5 days
        print("\nLast 5 days:")
        for _, row in historical_data.tail(5).iterrows():
            print(f"  {row['date'].date()}: Open={row['open']:,.2f}, "
                  f"High={row['high']:,.2f}, Low={row['low']:,.2f}, "
                  f"Close={row['close']:,.2f}, Volume={row['volume']:,}")
    else:
        print("❌ No historical data received")
    print()
    
    # Test 5: Intraday Data
    print("⏰ Test 5: Intraday Data (5-minute)")
    print("-" * 40)
    
    # Get 5-minute data for today
    intraday_data = trader.get_historical_data_by_symbol(
        symbol="RELIANCE",
        from_date=date.today(),
        to_date=date.today(),
        interval="5minute",
        exchange="NSE"
    )
    
    if not intraday_data.empty:
        print(f"✅ Fetched {len(intraday_data)} 5-minute candles for today")
        print(f"Time Range: {intraday_data['date'].min()} to {intraday_data['date'].max()}")
        
        # Show last 5 candles
        print("\nLast 5 candles:")
        for _, row in intraday_data.tail(5).iterrows():
            print(f"  {row['date'].strftime('%H:%M')}: "
                  f"O={row['open']:.2f}, H={row['high']:.2f}, "
                  f"L={row['low']:.2f}, C={row['close']:.2f}")
    else:
        print("❌ No intraday data received")
    print()
    
    # Test 6: Order Placement (Paper Trading)
    print("📝 Test 6: Order Placement")
    print("-" * 40)
    
    if settings.enable_paper_trading:
        print("Testing paper trading order...")
        
        # Place a test market order
        order_id = await trader.place_order(
            symbol="RELIANCE",
            transaction_type="BUY",
            quantity=1,
            order_type="MARKET",
            product="CNC",
            exchange="NSE",
            tag="test_order"
        )
        
        if order_id:
            print(f"✅ Paper order placed: {order_id}")
        else:
            print("❌ Failed to place paper order")
            
        # Place a limit order
        order_id = await trader.place_order(
            symbol="TCS",
            transaction_type="SELL",
            quantity=1,
            price=3500.0,
            order_type="LIMIT",
            product="CNC",
            exchange="NSE",
            tag="test_limit_order"
        )
        
        if order_id:
            print(f"✅ Paper limit order placed: {order_id}")
        else:
            print("❌ Failed to place paper limit order")
    else:
        print("⚠️  Live trading mode - skipping order placement test")
        print("Set ENABLE_PAPER_TRADING=true in .env to test order placement")
    print()
    
    # Test 7: Get Positions and Orders
    print("📊 Test 7: Positions and Orders")
    print("-" * 40)
    
    positions = trader.get_positions()
    print(f"Net Positions: {len(positions.get('net', []))}")
    print(f"Day Positions: {len(positions.get('day', []))}")
    
    orders = trader.get_orders()
    print(f"Orders Today: {len(orders)}")
    
    if orders:
        print("\nRecent Orders:")
        for order in orders[-3:]:
            print(f"  {order.get('tradingsymbol')}: {order.get('transaction_type')} "
                  f"{order.get('quantity')} @ {order.get('order_type')} - "
                  f"Status: {order.get('status')}")
    print()
    
    # Test 8: Execute Signal (Full Pipeline Test)
    print("🎯 Test 8: Signal Execution Pipeline")
    print("-" * 40)
    
    test_signal = {
        "signal_id": "test_001",
        "symbol": "INFY",
        "signal_type": "BUY",
        "quantity": 1,
        "entry_price": None,  # Market order
        "stop_loss": 1400.0,
        "target_price": 1500.0,
        "instrument_type": "EQUITY"
    }
    
    print(f"Test Signal: BUY {test_signal['symbol']} x{test_signal['quantity']}")
    
    if settings.enable_paper_trading:
        order_id = await trader.execute_signal(test_signal)
        if order_id:
            print(f"✅ Signal executed: Order ID {order_id}")
        else:
            print("❌ Failed to execute signal")
    else:
        print("⚠️  Live trading mode - skipping signal execution")
    
    print("\n" + "=" * 60)
    print("✅ Kite API Integration Test Complete!")
    
    if settings.enable_paper_trading:
        print("📊 Currently in PAPER TRADING mode")
        print("To enable live trading, set ENABLE_LIVE_TRADING=true in .env")
    else:
        print("⚠️  Currently in LIVE TRADING mode")
        print("Be careful - real orders will be placed!")


async def main():
    """Main entry point."""
    print("\n⚠️  KITE API INTEGRATION TEST")
    print("This will test the Kite API integration with your account")
    print()
    
    settings = get_settings()
    
    if settings.enable_live_trading and not settings.enable_paper_trading:
        print("🔴 WARNING: LIVE TRADING IS ENABLED!")
        print("Real orders may be placed if you continue.")
        response = input("Continue with LIVE trading test? (yes/N): ").strip().lower()
        if response != 'yes':
            print("Test cancelled.")
            return
    else:
        print("✅ Paper trading mode is enabled (safe for testing)")
    
    print()
    
    try:
        await test_kite_integration()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    asyncio.run(main())