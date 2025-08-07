#!/usr/bin/env python3
"""
Direct Telegram channel access script using personal account.
"""

import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import sys

# Your credentials
API_ID = 26179321
API_HASH = 'f63dd545353b8b8308d6e17f756fecca'
PHONE_NUMBER = '+917692020359'
VERIFICATION_CODE = '66691'  # The code you received

async def access_channel():
    """Access the 'Only option CE PE' channel and get messages."""
    
    print("🚀 Accessing Telegram channel with personal account...")
    
    try:
        # Create client
        client = TelegramClient('trading_session', API_ID, API_HASH)
        
        # Start client with authentication
        await client.start(
            phone=PHONE_NUMBER,
            code_callback=lambda: VERIFICATION_CODE
        )
        
        print("✅ Successfully authenticated!")
        
        # Get all your chats/channels
        dialogs = await client.get_dialogs()
        
        print(f"📋 Scanning {len(dialogs)} chats/channels...")
        
        target_channel = None
        for dialog in dialogs:
            entity = dialog.entity
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Unknown')
            
            if "only option" in name.lower():
                print(f"🎯 FOUND TARGET CHANNEL: '{name}'")
                print(f"   Channel ID: {entity.id}")
                print(f"   Type: {type(entity).__name__}")
                target_channel = entity
                break
        
        if not target_channel:
            print("❌ Could not find 'Only option CE PE' channel")
            print("📋 Available channels/groups:")
            for dialog in dialogs[:10]:  # Show first 10
                entity = dialog.entity
                name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Unknown')
                print(f"   - {name} (ID: {entity.id})")
            return None
        
        # Get recent messages from the target channel
        print(f"\n📨 Getting recent messages from '{target_channel.title}'...")
        
        messages = await client.get_messages(target_channel, limit=5)
        
        print(f"✅ Retrieved {len(messages)} recent messages:")
        print("=" * 60)
        
        for i, message in enumerate(messages, 1):
            print(f"Message {i}:")
            print(f"  📅 Date: {message.date}")
            print(f"  👤 From: {message.sender_id}")
            if message.text:
                print(f"  💬 Text: {message.text}")
            else:
                print(f"  📎 Media: {type(message.media).__name__ if message.media else 'No media'}")
            print("-" * 40)
        
        # Return the channel ID for use in our bot
        print(f"\n🔧 IMPORTANT: Use this channel ID in your .env file:")
        print(f"TELEGRAM_CHANNELS={target_channel.id}")
        
        await client.disconnect()
        return target_channel.id
        
    except SessionPasswordNeededError:
        print("❌ Two-factor authentication detected. Please disable 2FA temporarily or provide password.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    try:
        channel_id = asyncio.run(access_channel())
        if channel_id:
            print(f"\n✅ Successfully accessed channel! ID: {channel_id}")
        else:
            print("\n❌ Failed to access channel")
    except Exception as e:
        print(f"❌ Script failed: {e}")