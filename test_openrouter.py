#!/usr/bin/env python3
"""
Test OpenRouter AI parser integration.
"""

import asyncio
import os
import sys
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODELS = os.getenv("OPENROUTER_MODELS", "qwen/qwen3-coder").split(",")

# Sample trading messages to test parsing
SAMPLE_MESSAGES = [
    {
        "text": "BUY NIFTY 25000 CE @ 50 TARGET 100 SL 30",
        "expected_signal": "BUY",
        "expected_symbol": "NIFTY",
        "expected_type": "OPTIONS"
    },
    {
        "text": "SELL BANKNIFTY 54000 PE @ 120 TGT 60 STOPLOSS 180",
        "expected_signal": "SELL", 
        "expected_symbol": "BANKNIFTY",
        "expected_type": "OPTIONS"
    },
    {
        "text": "EXIT ALL POSITIONS - BOOK PROFIT",
        "expected_signal": "SELL",
        "expected_symbol": None,
        "expected_type": None
    },
    {
        "text": "Good morning! Market looks bullish today",
        "expected_signal": None,  # No trading signal
        "expected_symbol": None,
        "expected_type": None
    },
    {
        "text": "BUY RELIANCE FUTURE JAN25 @ 2850 QTY 50 TGT 2900 SL 2800",
        "expected_signal": "BUY",
        "expected_symbol": "RELIANCE",
        "expected_type": "FUTURES"
    }
]

class OpenRouterAIParser:
    """Test implementation of OpenRouter AI parser."""
    
    def __init__(self, api_key: str, models: list):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.models = models
        self.system_prompt = """You are a trading signal parser. Extract structured trading information from messages.

Return a JSON object with these fields:
- signal_type: "BUY", "SELL", "HOLD", or null if no signal
- instrument_type: "EQUITY", "FUTURES", "OPTIONS", or null
- symbol: stock/index symbol (e.g., "NIFTY", "BANKNIFTY", "RELIANCE")
- strike_price: number for options (e.g., 25000)
- expiry_date: expiry date if mentioned
- option_type: "CE" or "PE" for options
- quantity: number of shares/contracts
- entry_price: entry price
- target_price: target price
- stop_loss: stop loss price
- confidence_score: 0.0-1.0 confidence in parsing

Return null for non-trading messages. Be conservative - if unsure, return null."""

    async def parse_message(self, message_text: str, model: str = None) -> dict:
        """Parse a message using OpenRouter AI."""
        
        if not model:
            model = self.models[0]
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Parse this trading message: {message_text}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                parsed_data = json.loads(content)
                return parsed_data
            except json.JSONDecodeError:
                # If not JSON, try to extract JSON from text
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_str = content[start:end]
                    return json.loads(json_str)
                return None
                
        except Exception as e:
            print(f"❌ Error parsing with {model}: {e}")
            return None

async def test_openrouter_connection():
    """Test basic OpenRouter connection."""
    print("🔍 Testing OpenRouter API connection...")
    
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found in .env file")
        return False
    
    print(f"🔑 API Key: {OPENROUTER_API_KEY[:20]}...")
    print(f"🤖 Models: {OPENROUTER_MODELS}")
    
    try:
        client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Simple test call
        response = await client.chat.completions.create(
            model=OPENROUTER_MODELS[0],
            messages=[
                {"role": "user", "content": "Hello! Can you help me parse trading messages?"}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"✅ Connection successful!")
        print(f"   Model response: {content[:100]}...")
        
        # Check usage
        if hasattr(response, 'usage') and response.usage:
            print(f"   Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter connection failed: {e}")
        return False

async def test_message_parsing():
    """Test parsing of sample trading messages."""
    print("\n🔍 Testing message parsing...")
    
    parser = OpenRouterAIParser(OPENROUTER_API_KEY, OPENROUTER_MODELS)
    
    for i, sample in enumerate(SAMPLE_MESSAGES, 1):
        print(f"\n📝 Test {i}: {sample['text']}")
        print(f"   Expected: {sample['expected_signal']} signal")
        
        try:
            result = await parser.parse_message(sample['text'])
            
            if result is None:
                if sample['expected_signal'] is None:
                    print("   ✅ Correctly identified as non-trading message")
                else:
                    print("   ⚠️ Failed to parse valid trading message")
            else:
                print(f"   📊 Parsed result:")
                print(f"      Signal: {result.get('signal_type')}")
                print(f"      Symbol: {result.get('symbol')}")
                print(f"      Type: {result.get('instrument_type')}")
                print(f"      Price: {result.get('entry_price')}")
                print(f"      Confidence: {result.get('confidence_score', 0):.2f}")
                
                # Check if parsing matches expectations
                if result.get('signal_type') == sample['expected_signal']:
                    print("   ✅ Signal type matches expected")
                else:
                    print(f"   ⚠️ Signal mismatch - got {result.get('signal_type')}, expected {sample['expected_signal']}")
        
        except Exception as e:
            print(f"   ❌ Parsing failed: {e}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

async def test_model_fallback():
    """Test model fallback functionality."""
    print("\n🔍 Testing model fallback...")
    
    parser = OpenRouterAIParser(OPENROUTER_API_KEY, OPENROUTER_MODELS)
    test_message = "BUY NIFTY 25000 CE @ 50"
    
    for model in OPENROUTER_MODELS:
        print(f"\n🤖 Testing model: {model}")
        try:
            result = await parser.parse_message(test_message, model)
            if result:
                print(f"   ✅ Model {model} parsed successfully")
                print(f"   📊 Signal: {result.get('signal_type')}, Confidence: {result.get('confidence_score', 0):.2f}")
            else:
                print(f"   ⚠️ Model {model} returned null")
        except Exception as e:
            print(f"   ❌ Model {model} failed: {e}")
        
        await asyncio.sleep(1)

async def test_ai_parser_integration():
    """Test integration with actual AI parser module."""
    print("\n🔍 Testing AI parser module integration...")
    
    try:
        from ai.parser import AISignalParser
        
        parser = AISignalParser()
        test_message = "BUY NIFTY 25000 CE @ 50 TARGET 100 SL 30"
        
        result = await parser.parse_message(test_message)
        
        if result:
            print("✅ AI parser module working")
            print(f"   📊 Parsed: {result}")
        else:
            print("❌ AI parser module returned None")
            
    except ImportError as e:
        print(f"❌ Could not import AI parser: {e}")
        print("💡 This is expected if there are import issues - we'll fix them")
    except Exception as e:
        print(f"❌ AI parser test failed: {e}")

async def main():
    """Main test function."""
    print("🚀 Testing OpenRouter AI Integration")
    print("=" * 60)
    
    # Test basic connection
    connection_success = await test_openrouter_connection()
    
    if connection_success:
        # Test message parsing
        await test_message_parsing()
        
        # Test model fallback
        if len(OPENROUTER_MODELS) > 1:
            await test_model_fallback()
        
        # Test integration with actual module
        await test_ai_parser_integration()
        
        print("\n" + "=" * 60)
        print("🎉 OpenRouter AI tests completed!")
        print("\n💡 AI parser will be used for:")
        print("   - Extracting trading signals from messages")
        print("   - Confidence scoring")
        print("   - Multiple model fallback")
        print("   - Structured data extraction")
    else:
        print("\n❌ OpenRouter connection failed - cannot run other tests")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")