#!/usr/bin/env python3
"""
Test AI Trading Agent Integration
Tests the complete pipeline with risk management integration.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.ai.agent_integration import TradingAgentIntegration
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_integration():
    """Test the complete integration pipeline."""
    print("🔗 AI TRADING AGENT INTEGRATION TEST")
    print("=" * 60)
    
    integration = TradingAgentIntegration()
    settings = get_settings()
    
    print(f"✅ Integration initialized")
    print(f"📊 Mode: {'LIVE TRADING' if settings.enable_live_trading else 'Paper Trading'}")
    print()
    
    # Test messages with different scenarios
    test_messages = [
        {
            "message": "Can go for PERSISTENT 5100 CE ABOVE 163, TARGET 210++, SL# 120 BELOW",
            "channel_id": "test_channel_options",
            "description": "Options signal with risk management"
        },
        {
            "message": "EXIT RELIANCE IMMEDIATELY - STOP LOSS HIT",
            "channel_id": "test_channel_equity",
            "description": "Emergency exit signal"
        },
        {
            "message": "BUY INFY 10 SHARES AT MARKET",
            "channel_id": "test_channel_equity", 
            "description": "Small equity order"
        },
        {
            "message": "Market looking bullish, good opportunity ahead",
            "channel_id": "test_channel_news",
            "description": "General commentary (no action expected)"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"🧪 Test {i}: {test_case['description']}")
        print("-" * 60)
        print(f"Message: {test_case['message']}")
        print()
        
        try:
            # Process through complete integration
            result = await integration.process_telegram_message(
                message=test_case["message"],
                channel_id=test_case["channel_id"],
                message_id=f"test_msg_{i}_{int(datetime.now().timestamp())}",
                sender_info={"name": "Test User", "id": "test_user_123"},
                metadata={"source": "integration_test"}
            )
            
            print(f"📊 Processing Result:")
            print(f"  Success: {result['success']}")
            print(f"  Processing Time: {result['processing_time']:.2f}s")
            
            if result['success']:
                analysis = result['analysis']
                risk_assessment = result['risk_assessment']
                execution = result['execution']
                
                print(f"  AI Action: {analysis.get('action')}")
                print(f"  AI Confidence: {analysis.get('confidence', 0):.2f}")
                print(f"  Risk Approved: {risk_assessment.get('approved')}")
                print(f"  Risk Level: {risk_assessment.get('risk_level')}")
                
                if risk_assessment.get('approved'):
                    if isinstance(execution, dict):
                        print(f"  Execution Success: {execution.get('success', False)}")
                        print(f"  Execution Message: {execution.get('message', 'N/A')}")
                        if execution.get('order_id'):
                            print(f"  Order ID: {execution['order_id']}")
                    else:
                        print(f"  Execution Success: {execution.success if execution else False}")
                        print(f"  Execution Message: {execution.message if execution else 'N/A'}")
                        if execution and execution.order_id:
                            print(f"  Order ID: {execution.order_id}")
                else:
                    print(f"  Block Reason: {risk_assessment.get('reason')}")
                    if risk_assessment.get('critical_risks'):
                        print(f"  Critical Risks: {len(risk_assessment['critical_risks'])}")
                        for risk in risk_assessment['critical_risks'][:2]:  # Show first 2
                            print(f"    - {risk['message']}")
            else:
                print(f"  Error: {result.get('error')}")
            
            results.append(result)
            print()
            
        except Exception as e:
            logger.error(f"Test {i} failed: {e}")
            print(f"❌ Test Error: {e}")
            print()
            
            results.append({
                "success": False,
                "error": str(e),
                "message": test_case["message"]
            })
    
    # Performance summary
    print("=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    stats = integration.get_performance_stats()
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_time = sum(r.get('processing_time', 0) for r in results)
    avg_time = total_time / len(results) if results else 0
    
    print(f"Tests Completed: {successful_tests}/{len(results)}")
    print(f"Total Processing Time: {total_time:.2f}s")
    print(f"Average Time per Message: {avg_time:.2f}s")
    print()
    
    print("Performance Statistics:")
    print(f"  Messages Processed: {stats['messages_processed']}")
    print(f"  Actions Executed: {stats['actions_executed']}")
    print(f"  Successful Orders: {stats['successful_orders']}")
    print(f"  Risk Blocks: {stats['risk_blocks']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Action Rate: {stats['action_rate']:.2%}")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    print()
    
    return results, stats


async def test_health_check():
    """Test the health check functionality."""
    print("🏥 HEALTH CHECK TEST")
    print("=" * 60)
    
    integration = TradingAgentIntegration()
    
    try:
        health = await integration.health_check()
        
        print(f"Overall Status: {health['overall_status'].upper()}")
        print(f"Timestamp: {health['timestamp']}")
        print()
        
        print("Component Status:")
        for component, status in health['components'].items():
            status_emoji = "✅" if status['status'] == 'healthy' else "❌"
            print(f"  {status_emoji} {component}: {status['status']}")
            
            if 'connected' in status:
                print(f"    Connected: {status['connected']}")
            if 'model' in status:
                print(f"    Model: {status['model']}")
            if 'emergency_stop' in status:
                print(f"    Emergency Stop: {status['emergency_stop']}")
            if 'error' in status:
                print(f"    Error: {status['error']}")
        print()
        
        if 'stats' in health:
            print("Performance Stats:")
            for key, value in health['stats'].items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"❌ Health check error: {e}")
        return None


async def test_with_real_message():
    """Test with the exact message from your Telegram channel."""
    print("🎯 REAL MESSAGE TEST")
    print("=" * 60)
    
    # Your actual Telegram message
    real_message = """Can go for 

PERSISTENT 5100 CE ABOVE 163

TARGET 210++

SL# 120 BELOW

Wait for level to cross 

Disclaimer : This is my personal view, sharing only for educational Purposes. Consider it as a Paper trade. Option trading is risky, consult your financial analyst before taking any trade"""
    
    integration = TradingAgentIntegration()
    
    print("Processing your actual Telegram message...")
    print(f"Message: {real_message[:100]}...")
    print()
    
    try:
        result = await integration.process_telegram_message(
            message=real_message,
            channel_id="persistent_signals_123",
            message_id=f"real_msg_{int(datetime.now().timestamp())}",
            sender_info={"name": "Signal Provider", "id": "provider_123"},
            metadata={
                "source": "telegram_channel",
                "disclaimer": True,
                "educational": True
            }
        )
        
        print("🔍 Detailed Analysis:")
        print(f"  Overall Success: {result['success']}")
        print(f"  Processing Time: {result['processing_time']:.2f}s")
        
        if result['success']:
            analysis = result['analysis']
            risk_assessment = result['risk_assessment'] 
            execution = result['execution']
            
            print(f"\n🤖 AI Analysis:")
            print(f"  Action: {analysis.get('action')}")
            print(f"  Confidence: {analysis.get('confidence', 0):.2f}")
            print(f"  Reasoning: {analysis.get('reasoning')}")
            
            if analysis.get('parameters'):
                print(f"  Parameters:")
                for key, value in analysis['parameters'].items():
                    print(f"    {key}: {value}")
            
            print(f"\n⚠️  Risk Assessment:")
            print(f"  Approved: {risk_assessment.get('approved')}")
            print(f"  Risk Level: {risk_assessment.get('risk_level')}")
            print(f"  Reason: {risk_assessment.get('reason')}")
            
            if risk_assessment.get('details'):
                print(f"  Details: {risk_assessment['details']}")
            
            print(f"\n🎯 Execution Result:")
            if isinstance(execution, dict):
                print(f"  Success: {execution.get('success', False)}")
                print(f"  Message: {execution.get('message', 'N/A')}")
                if execution.get('order_id'):
                    print(f"  Order ID: {execution['order_id']}")
                elif execution.get('reason'):
                    print(f"  Block Reason: {execution['reason']}")
        else:
            print(f"❌ Processing Error: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Real message test failed: {e}")
        print(f"❌ Error: {e}")
        return None


async def main():
    """Main test function."""
    print("\n🔗 AI TRADING AGENT INTEGRATION - COMPREHENSIVE TEST")
    print("=" * 60)
    
    settings = get_settings()
    print(f"Environment: {settings.environment}")
    print(f"Live Trading: {settings.enable_live_trading}")
    print()
    
    try:
        # Test 1: Health Check
        print("Step 1: Health Check")
        await test_health_check()
        print()
        
        # Test 2: Integration Pipeline
        print("Step 2: Integration Pipeline")
        results, stats = await test_integration()
        print()
        
        # Test 3: Real Message
        print("Step 3: Real Message Test")
        real_result = await test_with_real_message()
        print()
        
        print("🎉 All integration tests completed!")
        
        if real_result and real_result.get('success'):
            execution = real_result.get('execution')
            if isinstance(execution, dict) and execution.get('order_id'):
                print(f"🚀 LIVE ORDER PLACED: {execution['order_id']}")
            elif hasattr(execution, 'order_id') and execution.order_id:
                print(f"🚀 LIVE ORDER PLACED: {execution.order_id}")
        
    except Exception as e:
        logger.error(f"Integration test suite failed: {e}")
        print(f"\n❌ Test suite error: {e}")


if __name__ == "__main__":
    asyncio.run(main())