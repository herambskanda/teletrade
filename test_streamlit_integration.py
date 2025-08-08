#!/usr/bin/env python3
"""
Test script to verify Streamlit AI Agent integration.
Tests the AI agent page components without running the full Streamlit app.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_ai_agent_import():
    """Test that the AI agent page can be imported."""
    try:
        from streamlit_app.pages import ai_agent
        print("✅ AI Agent page imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import AI agent page: {e}")
        return False

def test_agent_integration():
    """Test the agent integration directly."""
    try:
        from src.ai.agent_integration import TradingAgentIntegration
        
        integration = TradingAgentIntegration()
        print("✅ TradingAgentIntegration initialized successfully")
        
        # Test performance stats
        stats = integration.get_performance_stats()
        print(f"✅ Performance stats retrieved: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

async def test_agent_message_processing():
    """Test processing a message through the agent."""
    try:
        from src.ai.agent_integration import TradingAgentIntegration
        
        integration = TradingAgentIntegration()
        
        # Test message processing
        result = await integration.process_telegram_message(
            message="Get portfolio status",
            channel_id="test_streamlit",
            message_id="test_001",
            sender_info={"name": "Test User", "id": "test_user"},
            metadata={"source": "streamlit_test"}
        )
        
        print("✅ Message processing test completed")
        print(f"   Success: {result['success']}")
        print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        
        if result['success']:
            analysis = result.get('analysis', {})
            print(f"   AI Action: {analysis.get('action', 'unknown')}")
            print(f"   AI Confidence: {analysis.get('confidence', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message processing test failed: {e}")
        return False

async def test_health_check():
    """Test the health check functionality."""
    try:
        from src.ai.agent_integration import TradingAgentIntegration
        
        integration = TradingAgentIntegration()
        
        # Test health check
        health = await integration.health_check()
        
        print("✅ Health check test completed")
        print(f"   Overall status: {health.get('overall_status', 'unknown')}")
        
        components = health.get('components', {})
        for component, status in components.items():
            print(f"   {component}: {status.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

def test_streamlit_dependencies():
    """Test that all required packages are available."""
    missing_deps = []
    
    try:
        import streamlit
        print("✅ streamlit available")
    except ImportError:
        missing_deps.append("streamlit")
    
    try:
        import plotly
        print("✅ plotly available")  
    except ImportError:
        missing_deps.append("plotly")
    
    try:
        import pandas
        print("✅ pandas available")
    except ImportError:
        missing_deps.append("pandas")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        return False
    else:
        print("✅ All required dependencies available")
        return True

async def main():
    """Main test function."""
    print("🧪 STREAMLIT AI AGENT INTEGRATION TEST")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Dependencies
    print("\n📦 Test 1: Dependencies")
    if test_streamlit_dependencies():
        tests_passed += 1
    
    # Test 2: AI Agent Import
    print("\n📥 Test 2: AI Agent Page Import")
    if test_ai_agent_import():
        tests_passed += 1
    
    # Test 3: Agent Integration
    print("\n🔗 Test 3: Agent Integration")
    if test_agent_integration():
        tests_passed += 1
    
    # Test 4: Message Processing
    print("\n💬 Test 4: Message Processing")
    if await test_agent_message_processing():
        tests_passed += 1
    
    # Test 5: Health Check
    print("\n🏥 Test 5: Health Check")
    if await test_health_check():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Streamlit integration is ready.")
        print("\n🚀 To start the Streamlit app:")
        print("   source venv/bin/activate")
        print("   python run_streamlit.py")
        print("   Open http://localhost:8501 and navigate to '🤖 AI Agent' page")
    else:
        print(f"⚠️  {total_tests - tests_passed} test(s) failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())