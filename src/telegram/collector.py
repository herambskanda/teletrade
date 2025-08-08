"""Telegram message collector using Telethon API for full channel access."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import Channel, Chat, User
import redis.asyncio as redis

from config.settings import get_settings
from src.database.models import RawMessage, TelegramChannel
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramCollector:
    """Telethon-based Telegram message collector with full API access."""
    
    def __init__(self):
        """Initialize the Telegram collector."""
        self.settings = settings
        self.redis_client: Optional[redis.Redis] = None
        self.client: Optional[TelegramClient] = None
        self.channels: List[str] = self.settings.telegram_channels_list
        self.channel_entities: Dict[str, Any] = {}
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Telethon API credentials (from your working setup)
        self.api_id = 26179321
        self.api_hash = 'f63dd545353b8b8308d6e17f756fecca'
        self.phone_number = '+917692020359'
        self.session_file = 'trading_session'
        
    async def initialize(self):
        """Initialize connections and setup handlers."""
        try:
            # Initialize Redis connection
            self.redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize Telethon client with existing session
            self.client = TelegramClient(
                self.session_file, 
                self.api_id, 
                self.api_hash
            )
            
            # Connect to Telegram
            await self.client.connect()
            
            # Check if we're authorized (should be from previous session)
            if not await self.client.is_user_authorized():
                logger.error("Telegram session expired - need to re-authenticate")
                raise Exception("Telegram session expired. Run interactive_telegram_test.py to re-authenticate.")
            
            # Get user info
            me = await self.client.get_me()
            logger.info(f"Connected to Telegram as: {me.first_name} {me.last_name or ''} (@{me.username})")
            
            # Resolve channel entities
            await self._resolve_channel_entities()
            
            # Set up event handlers for real-time messages
            self._setup_event_handlers()
            
            logger.info("Telegram collector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram collector: {e}")
            raise
    
    async def _resolve_channel_entities(self):
        """Resolve channel IDs to entities."""
        try:
            dialogs = await self.client.get_dialogs()
            
            for channel_id in self.channels:
                try:
                    # Try to convert channel_id to int if it's a string
                    if isinstance(channel_id, str):
                        channel_id = int(channel_id)
                    
                    # Find the entity by ID
                    entity = None
                    for dialog in dialogs:
                        if dialog.entity.id == channel_id:
                            entity = dialog.entity
                            break
                    
                    if entity:
                        self.channel_entities[str(channel_id)] = entity
                        logger.info(f"Resolved channel: {getattr(entity, 'title', 'Unknown')} (ID: {channel_id})")
                    else:
                        logger.warning(f"Could not find channel with ID: {channel_id}")
                        
                except Exception as e:
                    logger.error(f"Error resolving channel {channel_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error resolving channel entities: {e}")
    
    def _setup_event_handlers(self):
        """Set up event handlers for real-time messages."""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                # Check if message is from monitored channels
                chat_id = str(event.chat_id)
                if chat_id not in self.channels:
                    return
                
                # Extract message data
                message_data = await self._extract_message_data(event.message)
                if message_data:
                    # Store in database
                    await self._store_message(message_data)
                    
                    # Queue for processing
                    await self._queue_message(message_data)
                    
                    logger.info(f"Real-time message collected from channel {chat_id}: {event.message.id}")
                    
            except Exception as e:
                logger.error(f"Error handling new message: {e}")
    
    async def _extract_message_data(self, message) -> Optional[Dict[str, Any]]:
        """Extract structured data from a Telegram message."""
        try:
            # Skip messages without text
            if not message.text:
                return None
            
            # Get sender info
            sender_info = {}
            if message.sender:
                sender_info = {
                    "user_id": message.sender.id,
                    "username": getattr(message.sender, 'username', None),
                    "first_name": getattr(message.sender, 'first_name', None),
                    "last_name": getattr(message.sender, 'last_name', None),
                }
            
            # Get chat info
            chat_info = {}
            if message.chat:
                chat_info = {
                    "title": getattr(message.chat, 'title', None),
                    "type": type(message.chat).__name__,
                }
            
            return {
                "channel_id": str(message.chat_id),
                "message_id": str(message.id),
                "message_text": message.text,
                "message_date": message.date.isoformat(),
                "sender_info": sender_info,
                "chat_info": chat_info,
                "raw_message": {
                    "id": message.id,
                    "date": message.date.isoformat(),
                    "text": message.text,
                    "sender_id": message.sender_id,
                    "chat_id": message.chat_id,
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting message data: {e}")
            return None
    
    async def _store_message(self, message_data: Dict[str, Any]):
        """Store message in database."""
        try:
            async with get_db_session() as session:
                raw_message = RawMessage(
                    channel_id=message_data["channel_id"],
                    message_id=message_data["message_id"],
                    message_text=message_data["message_text"],
                    message_date=datetime.fromisoformat(message_data["message_date"]),
                    sender_info=message_data["sender_info"],
                    processed=False
                )
                session.add(raw_message)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store message in database: {e}")
    
    async def _queue_message(self, message_data: Dict[str, Any]):
        """Queue message for processing."""
        try:
            if self.redis_client:
                # Add to Redis queue
                await self.redis_client.lpush(
                    "message_queue",
                    json.dumps(message_data, default=str)
                )
                
                # Also add to in-memory queue
                await self.message_queue.put(message_data)
                
                logger.debug(f"Message queued for processing: {message_data['message_id']}")
                
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
    
    async def fetch_historical_messages(self, channel_id: str, limit: int = 1000, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch historical messages from a channel."""
        try:
            entity = self.channel_entities.get(channel_id)
            if not entity:
                logger.error(f"Channel entity not found for ID: {channel_id}")
                return []
            
            # Calculate the date to fetch from
            offset_date = datetime.now() - timedelta(days=days_back)
            
            logger.info(f"Fetching {limit} historical messages from {getattr(entity, 'title', channel_id)} since {offset_date.date()}")
            
            messages = []
            async for message in self.client.iter_messages(
                entity, 
                limit=limit,
                offset_date=offset_date
            ):
                message_data = await self._extract_message_data(message)
                if message_data:
                    messages.append(message_data)
            
            logger.info(f"Fetched {len(messages)} historical messages from channel {channel_id}")
            return messages
            
        except FloodWaitError as e:
            logger.warning(f"Rate limited, waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return []
        except Exception as e:
            logger.error(f"Error fetching historical messages from channel {channel_id}: {e}")
            return []
    
    async def backfill_historical_messages(self, days_back: int = 30, batch_size: int = 100):
        """Backfill historical messages for all channels."""
        logger.info(f"Starting historical message backfill for {days_back} days")
        
        for channel_id in self.channels:
            try:
                # Check what's the latest message we have in database
                async with get_db_session() as session:
                    from sqlalchemy import select, desc
                    result = await session.execute(
                        select(RawMessage.message_date)
                        .where(RawMessage.channel_id == channel_id)
                        .order_by(desc(RawMessage.message_date))
                        .limit(1)
                    )
                    latest_date = result.scalar_one_or_none()
                
                if latest_date:
                    logger.info(f"Latest message in DB for channel {channel_id}: {latest_date}")
                    # Fetch messages since the latest we have
                    since_date = latest_date
                else:
                    # Fetch messages from specified days back
                    since_date = datetime.now() - timedelta(days=days_back)
                    
                logger.info(f"Fetching messages since {since_date} for channel {channel_id}")
                
                # Fetch historical messages
                messages = await self.fetch_historical_messages(channel_id, limit=1000, days_back=days_back)
                
                # Store in batches
                stored_count = 0
                for i in range(0, len(messages), batch_size):
                    batch = messages[i:i + batch_size]
                    for message_data in batch:
                        try:
                            await self._store_message(message_data)
                            stored_count += 1
                        except Exception as e:
                            logger.error(f"Error storing message {message_data['message_id']}: {e}")
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
                
                logger.info(f"Stored {stored_count} historical messages for channel {channel_id}")
                
            except Exception as e:
                logger.error(f"Error backfilling channel {channel_id}: {e}")
    
    async def start_monitoring(self):
        """Start monitoring Telegram channels."""
        try:
            self.is_running = True
            logger.info("Starting Telegram monitoring...")
            
            # Initialize if not already done
            if not self.client:
                await self.initialize()
            
            # Perform initial backfill
            logger.info("Performing historical message backfill...")
            await self.backfill_historical_messages(days_back=7)  # Last 7 days
            
            # Start real-time monitoring
            logger.info(f"Starting real-time monitoring of {len(self.channels)} channels")
            
            # Keep the client running for real-time events
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            raise
        
        finally:
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        try:
            self.is_running = False
            
            if self.client:
                await self.client.disconnect()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Telegram monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    async def get_pending_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending messages from the queue."""
        messages = []
        
        if self.redis_client:
            for _ in range(min(limit, await self.redis_client.llen("message_queue"))):
                message_json = await self.redis_client.rpop("message_queue")
                if message_json:
                    messages.append(json.loads(message_json))
        
        return messages

    async def get_channel_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about monitored channels."""
        channel_info = {}
        
        for channel_id, entity in self.channel_entities.items():
            try:
                # Get basic info
                info = {
                    "id": entity.id,
                    "title": getattr(entity, 'title', 'Unknown'),
                    "type": type(entity).__name__,
                    "username": getattr(entity, 'username', None),
                }
                
                # Get participant count if available
                try:
                    full_entity = await self.client.get_entity(entity)
                    if hasattr(full_entity, 'participants_count'):
                        info["participants_count"] = full_entity.participants_count
                except:
                    pass
                
                channel_info[channel_id] = info
                
            except Exception as e:
                logger.error(f"Error getting info for channel {channel_id}: {e}")
                channel_info[channel_id] = {"error": str(e)}
        
        return channel_info


async def main():
    """Main function for testing the collector."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = TelegramCollector()
    
    try:
        await collector.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await collector.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())