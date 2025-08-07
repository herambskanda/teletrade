#!/usr/bin/env python3
"""
Interactive Telegram channel access - you can enter verification codes when prompted.
"""

import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import sys
import os

# Your credentials
API_ID = 26179321
API_HASH = 'f63dd545353b8b8308d6e17f756fecca'
PHONE_NUMBER = '+917692020359'

def get_verification_code():
    """Interactive function to get verification code."""
    print("\n📱 A verification code has been sent to your Telegram app.")
    code = input("🔢 Please enter the verification code: ")
    return code.strip()

def get_2fa_password():
    """Interactive function to get 2FA password if needed."""
    print("\n🔒 Two-factor authentication is enabled on your account.")
    password = input("🔑 Please enter your 2FA password: ")
    return password.strip()

async def interactive_telegram_access():
    """Interactive Telegram access with proper input handling."""
    
    print("🚀 Interactive Telegram Channel Access")
    print("=" * 50)
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"🔧 API ID: {API_ID}")
    print("=" * 50)
    
    # Create client session
    client = TelegramClient('interactive_session', API_ID, API_HASH)
    
    try:
        print("\n🔗 Connecting to Telegram...")
        
        # Start with interactive authentication
        await client.start(
            phone=PHONE_NUMBER,
            code_callback=get_verification_code
        )
        
        print("✅ Successfully authenticated with Telegram!")
        
        # Get user info
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''} (@{me.username})")
        
        # Get all dialogs (chats/channels/groups)
        print("\n🔍 Scanning your chats and channels...")
        dialogs = await client.get_dialogs()
        
        print(f"📋 Found {len(dialogs)} chats/channels/groups")
        
        # Look for target channel
        target_channel = None
        all_channels = []
        
        for dialog in dialogs:
            entity = dialog.entity
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', 'Unknown')
            
            # Store all channels for display
            if hasattr(entity, 'title'):  # Groups and channels have titles
                all_channels.append({
                    'name': name,
                    'id': entity.id,
                    'type': type(entity).__name__
                })
            
            # Look for our target
            if "only option" in name.lower() or "ce pe" in name.lower():
                print(f"🎯 FOUND POTENTIAL TARGET: '{name}' (ID: {entity.id})")
                target_channel = entity
        
        # Display all channels for reference
        print(f"\n📺 Your channels and groups:")
        for i, ch in enumerate(all_channels[:15], 1):  # Show first 15
            marker = "🎯" if target_channel and ch['id'] == target_channel.id else "  "
            print(f"{marker} {i:2d}. {ch['name']} (ID: {ch['id']}) [{ch['type']}]")
        
        if len(all_channels) > 15:
            print(f"     ... and {len(all_channels) - 15} more")
        
        # If no automatic match, let user choose
        if not target_channel and all_channels:
            print(f"\n❓ Could not automatically find 'Only option CE PE' channel.")
            print("💡 Please check the list above and identify your channel.")
            try:
                choice = input("\n🔢 Enter the number of your target channel (or 0 to skip): ")
                if choice.strip() and choice.strip() != '0':
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(all_channels):
                        # Find the dialog entity by ID
                        target_id = all_channels[idx]['id']
                        for dialog in dialogs:
                            if dialog.entity.id == target_id:
                                target_channel = dialog.entity
                                break
            except (ValueError, IndexError):
                print("❌ Invalid selection")
        
        # Access the target channel
        if target_channel:
            print(f"\n📨 Accessing channel: '{target_channel.title}'")
            print(f"🆔 Channel ID: {target_channel.id}")
            
            # Get recent messages
            try:
                messages = await client.get_messages(target_channel, limit=5)
                print(f"\n✅ Retrieved {len(messages)} recent messages:")
                print("=" * 60)
                
                for i, message in enumerate(messages, 1):
                    print(f"Message {i}:")
                    print(f"  📅 Date: {message.date}")
                    print(f"  👤 Sender ID: {message.sender_id}")
                    if message.text:
                        # Show first 200 characters of text
                        text = message.text[:200] + "..." if len(message.text) > 200 else message.text
                        print(f"  💬 Text: {text}")
                    else:
                        print(f"  📎 Media: {type(message.media).__name__ if message.media else 'No content'}")
                    print("-" * 40)
                
                # Show the channel ID for .env configuration
                print(f"\n🔧 CONFIGURATION FOR YOUR .env FILE:")
                print(f"TELEGRAM_CHANNELS={target_channel.id}")
                print("\n💡 Copy this line to your .env file to use with the trading bot!")
                
            except Exception as e:
                print(f"❌ Could not retrieve messages: {e}")
                print("💡 You might need to have message history enabled or be an admin")
        
        else:
            print("\n❌ No target channel selected or found")
            print("💡 Make sure you're a member of 'Only option CE PE' channel")
        
        # Disconnect
        await client.disconnect()
        print("\n✅ Disconnected from Telegram")
        
    except SessionPasswordNeededError:
        print("❌ Two-factor authentication required but password callback failed")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the interactive test."""
    print("🚀 Starting Interactive Telegram Test...")
    print("💡 You'll be prompted to enter verification codes as needed")
    print()
    
    try:
        asyncio.run(interactive_telegram_access())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")

if __name__ == "__main__":
    main()