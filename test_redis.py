#!/usr/bin/env python3
"""
Test Redis connectivity and basic operations.
"""

import redis
import asyncio
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def test_redis_sync():
    """Test synchronous Redis operations."""
    print("🔍 Testing Redis synchronous connection...")
    
    try:
        # Connect to Redis
        r = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Test ping
        response = r.ping()
        print(f"✅ Redis ping successful: {response}")
        
        # Test basic operations
        r.set("test_key", "test_value")
        value = r.get("test_key")
        print(f"✅ Set/Get test: {value}")
        
        # Test expiring keys
        r.setex("temp_key", 5, "temporary_value")
        ttl = r.ttl("temp_key")
        print(f"✅ Expiring key TTL: {ttl} seconds")
        
        # Test hash operations (useful for message queuing)
        r.hset("test_hash", "field1", "value1")
        r.hset("test_hash", "field2", "value2")
        hash_data = r.hgetall("test_hash")
        print(f"✅ Hash operations: {hash_data}")
        
        # Test list operations (message queue)
        r.lpush("test_queue", "message1", "message2", "message3")
        queue_length = r.llen("test_queue")
        print(f"✅ Queue length: {queue_length}")
        
        # Pop messages from queue
        messages = []
        for _ in range(3):
            msg = r.rpop("test_queue")
            if msg:
                messages.append(msg)
        print(f"✅ Popped messages: {messages}")
        
        # Test JSON storage (for complex message data)
        message_data = {
            "id": 123,
            "channel": "Only option CE PE", 
            "text": "BUY NIFTY 25000 CE @ 50",
            "timestamp": "2025-08-07T18:00:00Z"
        }
        r.set("message:123", json.dumps(message_data))
        stored_data = json.loads(r.get("message:123"))
        print(f"✅ JSON storage test: {stored_data['text']}")
        
        # Cleanup test data
        r.delete("test_key", "temp_key", "test_hash", "message:123")
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis sync test failed: {e}")
        return False

async def test_redis_async():
    """Test asynchronous Redis operations (if needed)."""
    print("\n🔍 Testing Redis for async operations...")
    
    try:
        # For async operations, we'd use aioredis, but let's test
        # how our sync Redis would work in async contexts
        
        r = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Simulate message processing pipeline
        messages = [
            {"id": 1, "text": "BUY NIFTY 25000 CE"},
            {"id": 2, "text": "SELL NIFTY 24800 PE"},
            {"id": 3, "text": "TARGET HIT - EXIT ALL"}
        ]
        
        # Push messages to processing queue
        for msg in messages:
            r.lpush("message_queue", json.dumps(msg))
        
        print(f"✅ Queued {len(messages)} messages")
        
        # Process messages (simulate async processing)
        processed_count = 0
        while r.llen("message_queue") > 0:
            message_json = r.rpop("message_queue")
            if message_json:
                message = json.loads(message_json)
                print(f"   📨 Processing: {message['text']}")
                # Simulate processing time
                await asyncio.sleep(0.1)
                processed_count += 1
        
        print(f"✅ Processed {processed_count} messages")
        return True
        
    except Exception as e:
        print(f"❌ Redis async test failed: {e}")
        return False

def test_redis_info():
    """Test Redis server information."""
    print("\n🔍 Getting Redis server information...")
    
    try:
        r = redis.from_url(REDIS_URL)
        info = r.info()
        
        print(f"✅ Redis version: {info['redis_version']}")
        print(f"✅ Connected clients: {info['connected_clients']}")
        print(f"✅ Used memory: {info['used_memory_human']}")
        print(f"✅ Uptime: {info['uptime_in_seconds']} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis info test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Testing Redis Setup")
    print("=" * 50)
    print(f"📊 Redis URL: {REDIS_URL}")
    print()
    
    # Test sync operations
    sync_success = test_redis_sync()
    
    # Test server info
    info_success = test_redis_info()
    
    # Test async-style operations
    async_success = await test_redis_async()
    
    print("\n" + "=" * 50)
    if sync_success and info_success and async_success:
        print("🎉 All Redis tests passed!")
        print("✅ Redis is ready for message queuing")
    else:
        print("❌ Some Redis tests failed")
    
    print("\n💡 Redis will be used for:")
    print("   - Message queuing from Telegram")
    print("   - Temporary storage during processing")
    print("   - Caching AI responses")
    print("   - Rate limiting and throttling")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")