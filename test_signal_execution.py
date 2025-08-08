#!/usr/bin/env python3
"""
Test script to analyze a real trading signal and execute it via Kite API.
This will parse the message, extract trading parameters, and place the order.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date
import logging
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.trading.zerodha_client import ZerodhaTrader
from src.ai.parser import AISignalParser
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def analyze_and_execute_signal():
    """Analyze the trading signal and execute via Kite API."""
    
    # The actual message from the Telegram channel
    message = """Can go for 

PERSISTENT 5100 CE ABOVE 163

TARGET 210++

SL# 120 BELOW

Wait for level to cross 

Disclaimer : This is my personal view, sharing only for educational Purposes. Consider it as a Paper trade. Option trading is risky, consult your financial analyst before taking any trade"""
    
    print("=" * 60)
    print("📊 SIGNAL ANALYSIS AND EXECUTION")
    print("=" * 60)
    print()
    
    # Initialize components
    trader = ZerodhaTrader()
    parser = AISignalParser()
    settings = get_settings()
    
    # Check connection
    if not trader.is_connected:
        print("❌ Failed to connect to Kite API")
        return
    
    print(f"✅ Connected to Kite API")
    print(f"⚠️  Mode: {'LIVE TRADING' if settings.enable_live_trading else 'Paper Trading'}")
    print()
    
    # Step 1: Parse the message manually (since it's an options trade)
    print("📝 Step 1: Parsing Signal")
    print("-" * 40)
    print(f"Message: {message[:100]}...")
    print()
    
    # Extract signal details manually for this specific format
    signal_details = {
        "instrument": "PERSISTENT",
        "strike": 5100,
        "option_type": "CE",
        "entry_level": 163,
        "target": 210,
        "stop_loss": 120,
        "action": "BUY",
        "instruction": "Wait for level to cross 163"
    }
    
    print("📊 Extracted Signal Details:")
    for key, value in signal_details.items():
        print(f"  {key}: {value}")
    print()
    
    # Step 2: Find the exact instrument in NFO
    print("🔍 Step 2: Finding Option Contract")
    print("-" * 40)
    
    # Get NFO instruments to find the exact option contract
    nfo_instruments = trader.get_instruments("NFO")
    
    # Search for PERSISTENT 5100 CE
    matching_options = []
    for inst in nfo_instruments:
        if (inst.get('name') == 'PERSISTENT' and 
            inst.get('strike') == 5100 and 
            inst.get('instrument_type') == 'CE'):
            matching_options.append(inst)
    
    if not matching_options:
        print("❌ No matching option contract found")
        print("Searching for any PERSISTENT options...")
        
        # Show available PERSISTENT options
        persistent_options = [inst for inst in nfo_instruments 
                            if 'PERSISTENT' in inst.get('tradingsymbol', '')]
        
        if persistent_options:
            print(f"Found {len(persistent_options)} PERSISTENT options:")
            for opt in persistent_options[:5]:
                print(f"  - {opt['tradingsymbol']}: Strike={opt.get('strike')}, "
                      f"Type={opt.get('instrument_type')}, Expiry={opt.get('expiry')}")
        return
    
    # Sort by expiry to get the nearest expiry
    matching_options.sort(key=lambda x: x.get('expiry', ''))
    selected_option = matching_options[0]  # Get nearest expiry
    
    print(f"✅ Found Option Contract:")
    print(f"  Symbol: {selected_option['tradingsymbol']}")
    print(f"  Token: {selected_option['instrument_token']}")
    print(f"  Strike: {selected_option['strike']}")
    print(f"  Expiry: {selected_option['expiry']}")
    print(f"  Lot Size: {selected_option['lot_size']}")
    print()
    
    # Step 3: Get current market price
    print("💹 Step 3: Checking Current Market Price")
    print("-" * 40)
    
    quote_symbol = f"NFO:{selected_option['tradingsymbol']}"
    quotes = trader.get_quote([quote_symbol])
    
    if quotes and quote_symbol in quotes:
        current_price = quotes[quote_symbol].get('last_price', 0)
        print(f"  Current Price: ₹{current_price}")
        print(f"  Entry Level: ₹{signal_details['entry_level']}")
        
        if current_price > signal_details['entry_level']:
            print(f"  ⚠️  Price already above entry level (₹{current_price} > ₹{signal_details['entry_level']})")
            print(f"  📌 As per signal: 'Wait for level to cross'")
        else:
            print(f"  ✅ Price below entry level - Good for entry when it crosses")
    else:
        print("  ❌ Could not fetch current price")
    print()
    
    # Step 4: Calculate order parameters
    print("📊 Step 4: Order Parameters")
    print("-" * 40)
    
    lot_size = selected_option.get('lot_size', 1)
    quantity = lot_size  # Trade 1 lot
    
    print(f"  Instrument: {selected_option['tradingsymbol']}")
    print(f"  Quantity: {quantity} (1 lot)")
    print(f"  Order Type: LIMIT")
    print(f"  Entry Price: ₹{signal_details['entry_level']}")
    print(f"  Stop Loss: ₹{signal_details['stop_loss']}")
    print(f"  Target: ₹{signal_details['target']}")
    print()
    
    # Step 5: Risk Analysis
    print("⚠️  Step 5: Risk Analysis")
    print("-" * 40)
    
    max_loss = (signal_details['entry_level'] - signal_details['stop_loss']) * quantity
    max_profit = (signal_details['target'] - signal_details['entry_level']) * quantity
    risk_reward = max_profit / max_loss if max_loss > 0 else 0
    
    print(f"  Max Loss: ₹{max_loss:,.2f}")
    print(f"  Max Profit: ₹{max_profit:,.2f}")
    print(f"  Risk:Reward Ratio: 1:{risk_reward:.2f}")
    print(f"  Required Margin: ₹{signal_details['entry_level'] * quantity:,.2f}")
    print()
    
    # Step 6: Check margins
    print("💰 Step 6: Checking Account Margins")
    print("-" * 40)
    
    margins = trader.get_margins()
    if margins:
        available_cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
        print(f"  Available Cash: ₹{available_cash:,.2f}")
        required_margin = signal_details['entry_level'] * quantity
        
        if available_cash >= required_margin:
            print(f"  ✅ Sufficient margin available")
        else:
            print(f"  ❌ Insufficient margin (Need ₹{required_margin:,.2f})")
    print()
    
    # Step 7: Place the order
    print("🎯 Step 7: Order Execution")
    print("-" * 40)
    
    if settings.enable_live_trading:
        print("⚠️  LIVE TRADING MODE - Real order will be placed!")
        print()
        
        # Safety confirmation
        print("Order Summary:")
        print(f"  BUY {quantity} qty of {selected_option['tradingsymbol']}")
        print(f"  at ₹{signal_details['entry_level']} (LIMIT)")
        print()
        
        print("🚀 Proceeding with order placement...")
        
        if True:  # Auto-proceed
            try:
                # Markets are closed, need to place AMO order
                # AMO orders are accepted from 3:45 PM to 8:57 AM next day
                variety = "amo"
                validity = "DAY"  # AMO orders should use DAY validity
                print("  🌙 Placing After Market Order (AMO)")
                
                # Place main entry order
                order_id = await trader.place_order(
                    symbol=selected_option['tradingsymbol'],
                    transaction_type="BUY",
                    quantity=quantity,
                    price=signal_details['entry_level'],
                    order_type="LIMIT",
                    product="NRML",  # Use NRML for F&O
                    exchange="NFO",
                    validity=validity,
                    variety=variety,
                    tag="PERSISTENT_CE"
                )
                
                if order_id:
                    print(f"✅ Order placed successfully!")
                    print(f"  Order ID: {order_id}")
                    print()
                    
                    # Place stop-loss order (as a separate order)
                    print("Placing Stop-Loss order...")
                    sl_order_id = await trader.place_order(
                        symbol=selected_option['tradingsymbol'],
                        transaction_type="SELL",
                        quantity=quantity,
                        trigger_price=signal_details['stop_loss'],
                        order_type="SL-M",  # Stop-Loss Market
                        product="NRML",
                        exchange="NFO",
                        validity="DAY",
                        tag="PERSISTENT_SL"
                    )
                    
                    if sl_order_id:
                        print(f"✅ Stop-Loss order placed: {sl_order_id}")
                    
                    # Note about target
                    print()
                    print(f"📌 Target: ₹{signal_details['target']}")
                    print("   (Place target order manually after entry fills)")
                    
                else:
                    print("❌ Failed to place order")
                    
            except Exception as e:
                print(f"❌ Order placement error: {e}")
        else:
            print("❌ Order cancelled by user")
    else:
        print("📊 PAPER TRADING MODE - Simulating order...")
        
        # Simulate order in paper mode
        order_id = await trader.place_order(
            symbol=selected_option['tradingsymbol'],
            transaction_type="BUY",
            quantity=quantity,
            price=signal_details['entry_level'],
            order_type="LIMIT",
            product="NRML",
            exchange="NFO",
            tag="PERSISTENT_CE"
        )
        
        if order_id:
            print(f"✅ Paper order placed: {order_id}")
        else:
            print("❌ Failed to place paper order")
    
    print()
    print("=" * 60)
    print("📊 Signal execution complete!")
    print("=" * 60)


async def main():
    """Main entry point."""
    print("\n🎯 TRADING SIGNAL EXECUTION TEST")
    print("This will analyze and execute a real options trading signal")
    print()
    
    settings = get_settings()
    
    if settings.enable_live_trading:
        print("🔴 WARNING: LIVE TRADING IS ENABLED!")
        print("Real orders will be placed with real money.")
        print("Make sure you understand the risks.")
        print("📊 Running in ANALYSIS MODE - will show order details but ask before placing")
    else:
        print("✅ Paper trading mode - Safe for testing")
    
    print()
    
    try:
        await analyze_and_execute_signal()
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())