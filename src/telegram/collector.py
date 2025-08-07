"""Telegram message collector for monitoring multiple channels."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)
from telegram.error import TelegramError
import redis.asyncio as redis

from config.settings import get_settings
from src.database.models import RawMessage, TelegramChannel
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramCollector:
    """Multi-channel Telegram message collector with real-time processing."""
    
    def __init__(self):
        """Initialize the Telegram collector."""
        self.settings = settings
        self.redis_client: Optional[redis.Redis] = None
        self.application: Optional[Application] = None
        self.channels: List[str] = self.settings.telegram_channels
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
    async def initialize(self):
        """Initialize connections and setup handlers."""
        try:
            # Initialize Redis connection
            self.redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize Telegram bot application
            self.application = (
                Application.builder()
                .token(self.settings.telegram_bot_token)
                .build()
            )
            
            # Add handlers
            self._setup_handlers()
            
            logger.info("Telegram collector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram collector: {e}")
            raise
    
    def _setup_handlers(self):
        """Set up message handlers for the bot."""
        # Command handlers
        self.application.add_handler(
            CommandHandler("start", self.start_command)
        )
        self.application.add_handler(
            CommandHandler("status", self.status_command)
        )
        self.application.add_handler(
            CommandHandler("stop", self.stop_command)
        )
        
        # Message handler for channel messages
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_channel_message
            )
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        await update.message.reply_text(
            "Trading Bot Message Collector is active!\n"
            f"Monitoring {len(self.channels)} channels.\n"
            "Use /status to check current status."
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command."""
        status_msg = f"Bot Status: {'Running' if self.is_running else 'Stopped'}\n"
        status_msg += f"Channels monitored: {len(self.channels)}\n"
        
        # Get queue size from Redis
        if self.redis_client:
            queue_size = await self.redis_client.llen("message_queue")
            status_msg += f"Messages in queue: {queue_size}\n"
        
        await update.message.reply_text(status_msg)
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stop command."""
        self.is_running = False
        await update.message.reply_text("Bot stopping...")
    
    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from monitored channels."""
        try:
            if not update.message or not update.message.text:
                return
            
            # Check if message is from a monitored channel
            chat_id = str(update.effective_chat.id)
            if chat_id not in self.channels:
                logger.debug(f"Ignoring message from non-monitored channel: {chat_id}")
                return
            
            # Create message data
            message_data = {
                "channel_id": chat_id,
                "message_id": str(update.message.message_id),
                "message_text": update.message.text,
                "message_date": update.message.date.isoformat(),
                "sender_info": {
                    "user_id": update.message.from_user.id if update.message.from_user else None,
                    "username": update.message.from_user.username if update.message.from_user else None,
                    "first_name": update.message.from_user.first_name if update.message.from_user else None,
                },
                "chat_info": {
                    "title": update.effective_chat.title,
                    "type": update.effective_chat.type,
                }
            }
            
            # Store in database
            await self._store_message(message_data)
            
            # Queue for processing
            await self._queue_message(message_data)
            
            logger.info(f"Message collected from channel {chat_id}: {update.message.message_id}")
            
        except Exception as e:
            logger.error(f"Error handling channel message: {e}")
    
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
                    json.dumps(message_data)
                )
                
                # Also add to in-memory queue
                await self.message_queue.put(message_data)
                
                logger.debug(f"Message queued for processing: {message_data['message_id']}")
                
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
    
    async def error_handler(self, update: Update, context: CallbackContext):
        """Handle errors in the bot."""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Try to notify admin
        try:
            if self.settings.alert_telegram_chat_id:
                await context.bot.send_message(
                    chat_id=self.settings.alert_telegram_chat_id,
                    text=f"Error in bot: {context.error}"
                )
        except:
            pass
    
    async def start_monitoring(self):
        """Start monitoring Telegram channels."""
        try:
            self.is_running = True
            logger.info("Starting Telegram monitoring...")
            
            # Initialize if not already done
            if not self.application:
                await self.initialize()
            
            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.info(f"Monitoring {len(self.channels)} channels")
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            raise
        
        finally:
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup."""
        try:
            self.is_running = False
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
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