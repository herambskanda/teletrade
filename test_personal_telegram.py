#!/usr/bin/env python3
"""
Test script to access Telegram messages using your personal account.
This can access any channel/group you're a member of.
"""

import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Your API credentials from https://my.telegram.org
API_ID = 26179321  # Your API ID
API_HASH = 'f63dd545353b8b8308d6e17f756fecca'  # Your API Hash
PHONE_NUMBER = '+917692020359'  # Your phone number with country code

async def test_personal_access():
    """Test accessing Telegram with your personal account."""
    
    print("🔍 Testing personal Telegram account access...")
    print("📱 This method can access ANY channel/group you're a member of!")
    print()
    
    phone_number = PHONE_NUMBER
    print(f"📱 Using phone number: {phone_number}")
    
    try:
        # Create client
        client = TelegramClient('session_name', API_ID, API_HASH)
        
        # Connect and authenticate
        await client.start(phone=phone_number)
        print("✅ Successfully connected to Telegram!")
        
        # Get your dialogs (chats/channels you're in)
        dialogs = await client.get_dialogs(limit=50)
        
        print(f"📋 Found {len(dialogs)} chats/channels you're in:")
        target_channel = None
        
        for dialog in dialogs:
            entity = dialog.entity
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Unknown')
            
            print(f"   ID: {entity.id}")
            print(f"   Name: {name}")
            print(f"   Type: {type(entity).__name__}")
            
            # Look for our target channel
            if "only option" in name.lower():
                print(f"   🎯 FOUND TARGET CHANNEL!")
                target_channel = entity
            print()
        
        # If we found the channel, get recent messages
        if target_channel:
            print(f"📨 Getting recent messages from '{target_channel.title}'...")
            
            messages = await client.get_messages(target_channel, limit=10)
            print(f"✅ Found {len(messages)} recent messages:")
            
            for i, message in enumerate(messages, 1):
                print(f"   Message {i}:")
                print(f"     Date: {message.date}")
                print(f"     Text: {message.text or '[Media/No text]'}")
                print(f"     From: {message.sender_id}")
                print()
        else:
            print("❌ Could not find 'Only option CE PE' channel in your dialogs")
            print("💡 Make sure you're actually a member of this channel")
        
        await client.disconnect()
        
    except SessionPasswordNeededError:
        print("❌ Two-factor authentication enabled. Please enter your password.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Personal Telegram Access")
    print("=" * 50)
    print("⚠️  You need API credentials from https://my.telegram.org")
    print("=" * 50)
    
    # Check if telethon is installed
    try:
        import telethon
        asyncio.run(test_personal_access())
    except ImportError:
        print("❌ Telethon not installed. Run: pip install telethon")