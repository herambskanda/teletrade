#!/usr/bin/env python3
"""
Test script to verify Telegram bot setup and channel access.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_chat_access(bot: Bot, chat_identifier: str):
    """Test access to a specific chat by ID or username."""
    try:
        # Try to get chat info
        chat = await bot.get_chat(chat_id=chat_identifier)
        print(f"✅ Chat access successful!")
        print(f"   Chat type: {chat.type}")
        print(f"   Chat title: {chat.title if hasattr(chat, 'title') else 'N/A'}")
        print(f"   Chat username: @{chat.username}" if hasattr(chat, 'username') and chat.username else "   No username")
        print(f"   Chat ID: {chat.id}")
        print()
        
        # Try to get member count if it's a group/channel
        try:
            member_count = await bot.get_chat_member_count(chat_id=chat_identifier)
            print(f"   Members: {member_count}")
        except TelegramError:
            print("   Member count: Not available")
        
        # Try to get recent messages (this might fail if not enough permissions)
        print("🔍 Attempting to get chat history...")
        try:
            # Note: This requires the bot to be an admin or have message history access
            updates = await bot.get_updates(limit=10)
            print(f"✅ Got {len(updates)} recent updates from bot")
            
            # Filter updates for this chat
            chat_updates = [u for u in updates if u.message and str(u.message.chat.id) == str(chat.id)]
            print(f"   Found {len(chat_updates)} messages from this chat")
            
            if chat_updates:
                for update in chat_updates[-3:]:  # Show last 3 messages
                    msg = update.message
                    text = msg.text or msg.caption or "[Media/Non-text message]"
                    print(f"   📝 Message: {text[:100]}...")
                    print(f"      From: {msg.from_user.first_name if msg.from_user else 'Unknown'}")
                    print(f"      Date: {msg.date}")
            else:
                print("   ℹ️ No recent messages found for this chat in bot updates")
                
        except TelegramError as e:
            print(f"⚠️ Cannot access message history: {e}")
            print("   This is normal if bot doesn't have admin access or message history permissions")
        
        return True
        
    except TelegramError as e:
        print(f"❌ Cannot access chat {chat_identifier}: {e}")
        
        # Common issues and suggestions
        if "chat not found" in str(e).lower():
            print("   💡 Suggestions:")
            print("      - Check if the chat ID/username is correct")
            print("      - For channels, ID should start with -100 (e.g., -1001234567890)")
            print("      - For usernames, try with/without @ symbol")
            print("      - Channel might be private or not exist")
        elif "forbidden" in str(e).lower():
            print("   💡 Suggestions:")
            print("      - Bot needs to be added to the channel/group")
            print("      - Bot might need admin permissions")
            print("      - For private channels, bot must be invited")
        
        return False

async def test_telegram_bot():
    """Test Telegram bot configuration and access."""
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_ids = os.getenv("TELEGRAM_CHANNELS", "").split(",")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return False
    
    if not channel_ids or channel_ids == [""]:
        print("❌ TELEGRAM_CHANNELS not found in .env file")
        return False
    
    print(f"🤖 Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
    print(f"📱 Channel IDs: {channel_ids}")
    print()
    
    # Test the actual channel name and variations
    test_usernames = [
        "Only option CE PE",
        "@Only option CE PE",
        "OnlyoptionCEPE",
        "@OnlyoptionCEPE", 
        "only_option_ce_pe",
        "@only_option_ce_pe",
        "onlyoptioncepe",
        "@onlyoptioncepe"
    ]
    print(f"🔍 Will also test common channel usernames: {test_usernames}")
    print()
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Test bot connection
        print("🔍 Testing bot connection...")
        me = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"   Bot name: {me.first_name}")
        print(f"   Bot username: @{me.username}")
        print(f"   Bot ID: {me.id}")
        print()
        
        # Test each channel ID first
        for i, channel_id in enumerate(channel_ids):
            channel_id = channel_id.strip()
            print(f"🔍 Testing channel {i+1}: {channel_id}")
            await test_chat_access(bot, channel_id)
            print("-" * 50)
        
        # Test common channel usernames
        print("🔍 Testing common channel username patterns...")
        for username in test_usernames:
            print(f"🔍 Testing username: {username}")
            await test_chat_access(bot, username)
            print("-" * 30)
        
        return True
        
    except TelegramError as e:
        print(f"❌ Bot connection failed: {e}")
        print("💡 Check if your TELEGRAM_BOT_TOKEN is correct")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_bot_commands():
    """Test if bot responds to basic commands."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = Bot(token=bot_token)
    
    print("🔍 Testing bot commands...")
    
    try:
        # Get bot commands
        commands = await bot.get_my_commands()
        print(f"✅ Bot has {len(commands)} registered commands:")
        for cmd in commands:
            print(f"   /{cmd.command} - {cmd.description}")
    
    except Exception as e:
        print(f"⚠️ Could not get bot commands: {e}")

async def find_personal_chat():
    """Help find your personal chat ID for testing."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = Bot(token=bot_token)
    
    print("🔍 Looking for recent personal chats...")
    print("💡 Send a message to @kite777_bot now if you want to find your chat ID")
    
    try:
        updates = await bot.get_updates(limit=50)
        print(f"✅ Found {len(updates)} recent updates")
        
        personal_chats = {}
        for update in updates:
            if update.message:
                chat = update.message.chat
                if chat.type == "private":
                    user = update.message.from_user
                    personal_chats[chat.id] = {
                        "name": f"{user.first_name} {user.last_name or ''}".strip(),
                        "username": f"@{user.username}" if user.username else "No username",
                        "last_message": update.message.text or "[Media]"
                    }
        
        if personal_chats:
            print(f"📱 Found {len(personal_chats)} personal chat(s):")
            for chat_id, info in personal_chats.items():
                print(f"   Chat ID: {chat_id}")
                print(f"   User: {info['name']} ({info['username']})")
                print(f"   Last message: {info['last_message'][:50]}...")
                print()
        else:
            print("❌ No personal chats found. Send '/start' to @kite777_bot first!")
            
    except Exception as e:
        print(f"❌ Error getting updates: {e}")

if __name__ == "__main__":
    print("🚀 Testing Telegram Bot Integration")
    print("=" * 50)
    
    try:
        # Run the tests
        success = asyncio.run(test_telegram_bot())
        
        if success:
            asyncio.run(test_bot_commands())
            print("\n" + "=" * 50)
            asyncio.run(find_personal_chat())
            print("\n✅ Telegram bot test completed!")
        else:
            print("\n❌ Telegram bot test failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")