#!/usr/bin/env python3
"""
Test script for the AI Trading Agent.
Tests message analysis and action execution with various Telegram message formats.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.ai.trading_agent import TradingAgent, create_test_messages
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_message_analysis():
    """Test the AI agent's message analysis capabilities."""
    print("🤖 AI TRADING AGENT TEST")
    print("=" * 60)
    
    # Initialize the trading agent
    agent = TradingAgent()
    settings = get_settings()
    
    print(f"✅ Trading Agent initialized")
    print(f"📊 Mode: {'LIVE TRADING' if settings.enable_live_trading else 'Paper Trading'}")
    print(f"🔗 Model: qwen-2.5-coder-32b-instruct")
    print()
    
    # Test messages
    test_cases = [
        {
            "message": "Can go for PERSISTENT 5100 CE ABOVE 163, TARGET 210++, SL# 120 BELOW, Wait for level to cross",
            "description": "Real options trading signal (used earlier)"
        },
        {
            "message": "EXIT RELIANCE IMMEDIATELY - MARKET TURNING BEARISH",
            "description": "Emergency exit instruction"
        },
        {
            "message": "BUY INFY 50 SHARES AT MARKET PRICE",
            "description": "Simple equity market order"
        },
        {
            "message": "TCS LOOKING GOOD FOR LONG TERM INVESTMENT",
            "description": "General commentary (should be no action)"
        },
        {
            "message": "NIFTY25AUG24000CE - BUY ABOVE 250, TARGET 350, SL 200",
            "description": "Index options signal"
        },
        {
            "message": "MODIFY ORDER 250807401827513 PRICE TO 165",
            "description": "Order modification (using real order ID)"
        },
        {
            "message": "CANCEL ALL PENDING ORDERS",
            "description": "Mass cancellation instruction"
        },
        {
            "message": "HDFC BANK - SELL 25 SHARES BELOW 1600",
            "description": "Conditional sell order"
        },
        {
            "message": "📈 MARKET UPDATE: Nifty at 19500, Bank Nifty strong",
            "description": "Market update with emojis (should be no action)"
        },
        {
            "message": "STOP LOSS HIT ON WIPRO - BOOK LOSS",
            "description": "Stop loss trigger message"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['description']}")
        print("-" * 60)
        print(f"Message: {test_case['message']}")
        print()
        
        try:
            # Analyze the message
            start_time = datetime.now()
            analysis = await agent.analyze_message(test_case['message'])
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            print(f"📊 AI Analysis ({analysis_time:.2f}s):")
            print(f"  Action: {analysis.get('action', 'unknown')}")
            print(f"  Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"  Analysis: {analysis.get('analysis', 'N/A')}")
            print(f"  Reasoning: {analysis.get('reasoning', 'N/A')}")
            
            if analysis.get('parameters'):
                print(f"  Parameters:")
                for key, value in analysis['parameters'].items():
                    print(f"    {key}: {value}")
            
            # Store result for summary
            results.append({
                "test": i,
                "message": test_case['message'],
                "description": test_case['description'],
                "action": analysis.get('action'),
                "confidence": analysis.get('confidence', 0),
                "analysis_time": analysis_time,
                "success": "error" not in analysis
            })
            
            print()
            
        except Exception as e:
            logger.error(f"Test {i} failed: {e}")
            print(f"❌ Error: {e}")
            print()
            
            results.append({
                "test": i,
                "message": test_case['message'],
                "description": test_case['description'],
                "action": "error",
                "confidence": 0,
                "analysis_time": 0,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_time = sum(r['analysis_time'] for r in results)
    avg_time = total_time / len(results) if results else 0
    
    print(f"Tests Passed: {successful_tests}/{len(results)}")
    print(f"Total Analysis Time: {total_time:.2f}s")
    print(f"Average Time per Message: {avg_time:.2f}s")
    print()
    
    # Action breakdown
    actions = {}
    for r in results:
        if r['success']:
            action = r['action']
            actions[action] = actions.get(action, 0) + 1
    
    print("Action Distribution:")
    for action, count in actions.items():
        print(f"  {action}: {count}")
    print()
    
    # High confidence predictions
    high_conf = [r for r in results if r['success'] and r['confidence'] > 0.7]
    print(f"High Confidence Predictions (>0.7): {len(high_conf)}")
    for r in high_conf:
        print(f"  Test {r['test']}: {r['action']} ({r['confidence']:.2f})")
    print()
    
    return results


async def test_full_pipeline():
    """Test the complete message processing pipeline."""
    print("🔄 FULL PIPELINE TEST")
    print("=" * 60)
    
    agent = TradingAgent()
    
    # Test with a real message
    test_message = "Can go for PERSISTENT 5100 CE ABOVE 163, TARGET 210++, SL# 120 BELOW"
    
    print(f"Testing complete pipeline with:")
    print(f"Message: {test_message}")
    print()
    
    try:
        # Process the message through the complete pipeline
        result = await agent.process_telegram_message(
            message=test_message,
            channel_id="test_channel_123",
            sender_info={"name": "Test User", "id": "user_123"}
        )
        
        print("📊 Pipeline Results:")
        print(f"  Success: {result['success']}")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        
        if result['success']:
            analysis = result['analysis']
            execution = result['execution']
            
            print(f"  Analysis Action: {analysis.get('action')}")
            print(f"  Analysis Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"  Execution Success: {execution['success']}")
            print(f"  Execution Message: {execution['message']}")
            
            if execution.get('order_id'):
                print(f"  Order ID: {execution['order_id']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        print(f"❌ Pipeline Error: {e}")
        return None


async def test_trading_tools():
    """Test the trading tools directly."""
    print("🛠️  TRADING TOOLS TEST")
    print("=" * 60)
    
    from src.ai.trading_tools import TradingTools
    
    tools = TradingTools()
    
    # Test 1: Check connection
    print("Test 1: Connection Status")
    if tools.trader.is_connected:
        print("✅ Connected to Kite API")
    else:
        print("❌ Not connected to Kite API")
    print()
    
    # Test 2: Get account status
    print("Test 2: Account Status")
    margins_result = tools.get_margins()
    print(f"  Margins: {margins_result.message}")
    
    positions_result = tools.get_positions()
    print(f"  Positions: {positions_result.message}")
    
    orders_result = tools.get_orders()
    print(f"  Orders: {orders_result.message}")
    print()
    
    # Test 3: Instrument search
    print("Test 3: Instrument Search")
    
    test_symbols = ["RELIANCE", "PERSISTENT25AUG5100CE", "TCS"]
    for symbol in test_symbols:
        if "25AUG" in symbol:  # Options
            result = tools.search_instrument(symbol, "NFO")
        else:  # Equity
            result = tools.search_instrument(symbol, "NSE")
        print(f"  {symbol}: {result.message}")
    print()
    
    # Test 4: Get quotes
    print("Test 4: Real-time Quotes")
    quote_symbols = ["RELIANCE", "TCS", "INFY"]
    for symbol in quote_symbols:
        quote_result = tools.get_quote(symbol, "NSE")
        print(f"  {symbol}: {quote_result.message}")
    print()


async def main():
    """Main test function."""
    print("\n🤖 AI TRADING AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    settings = get_settings()
    print(f"Environment: {settings.environment}")
    print(f"Live Trading: {settings.enable_live_trading}")
    print(f"Paper Trading: {settings.enable_paper_trading}")
    print()
    
    try:
        # Test 1: Trading Tools
        await test_trading_tools()
        print()
        
        # Test 2: Message Analysis
        await test_message_analysis()
        print()
        
        # Test 3: Full Pipeline (uncomment to test execution)
        # print("⚠️  Note: Full pipeline test will attempt to place actual orders!")
        # response = input("Run full pipeline test? (y/N): ").strip().lower()
        # if response == 'y':
        #     await test_full_pipeline()
        
        print("🎉 All tests completed!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\n❌ Test suite error: {e}")


if __name__ == "__main__":
    asyncio.run(main())