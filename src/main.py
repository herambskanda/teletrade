"""Main application entry point for the trading bot."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import signal
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import get_settings
from src.database.connection import init_database_sync
from src.telegram.collector import TelegramCollector
from src.ai.parser import AISignalParser
from src.trading.zerodha_client import ZerodhaTrader
from src.risk.risk_manager import RiskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Global application state
app_state = {
    "telegram_collector": None,
    "ai_parser": None,
    "zerodha_trader": None,
    "risk_manager": None,
    "running": False
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Startup
    logger.info("Starting Trading Bot application...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database_sync()
        
        # Initialize components
        app_state["ai_parser"] = AISignalParser()
        app_state["zerodha_trader"] = ZerodhaTrader()
        app_state["risk_manager"] = RiskManager()
        app_state["telegram_collector"] = TelegramCollector()
        
        # Initialize telegram collector
        await app_state["telegram_collector"].initialize()
        
        logger.info("All components initialized successfully")
        app_state["running"] = True
        
        # Start background tasks
        asyncio.create_task(message_processing_loop())
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Trading Bot application...")
        app_state["running"] = False
        
        if app_state["telegram_collector"]:
            await app_state["telegram_collector"].stop_monitoring()
        
        if app_state["zerodha_trader"]:
            app_state["zerodha_trader"].stop_price_streaming()
        
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="Automated trading bot with Telegram signal processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def message_processing_loop():
    """Main message processing loop."""
    logger.info("Starting message processing loop...")
    
    while app_state["running"]:
        try:
            # Get pending messages from Telegram collector
            if app_state["telegram_collector"]:
                messages = await app_state["telegram_collector"].get_pending_messages(limit=10)
                
                for message in messages:
                    await process_message(message)
            
            # Sleep for a short interval
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in message processing loop: {e}")
            await asyncio.sleep(10)


async def process_message(message: dict):
    """Process a single message through the trading pipeline."""
    try:
        logger.info(f"Processing message: {message['message_id']}")
        
        # Parse message with AI
        signal = await app_state["ai_parser"].parse_message(
            message["message_text"],
            {"channel_id": message["channel_id"]}
        )
        
        if not signal:
            logger.debug("No valid signal extracted from message")
            return
        
        logger.info(f"Signal extracted: {signal.signal_type} {signal.symbol} (confidence: {signal.confidence_score:.2f})")
        
        # Validate signal with risk manager
        portfolio = await get_current_portfolio()
        risk_results = await app_state["risk_manager"].validate_trade(
            signal.to_dict(),
            portfolio
        )
        
        # Check if any critical risks
        critical_risks = [r for r in risk_results if r.severity.value in ["HIGH", "CRITICAL"] and not r.passed]
        
        if critical_risks:
            logger.warning(f"Trade rejected due to risk checks: {[r.message for r in critical_risks]}")
            return
        
        # Execute trade if all checks pass
        if app_state["zerodha_trader"]:
            order_id = await app_state["zerodha_trader"].execute_signal(signal.to_dict())
            
            if order_id:
                logger.info(f"Trade executed successfully: Order ID {order_id}")
            else:
                logger.error("Failed to execute trade")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")


async def get_current_portfolio() -> dict:
    """Get current portfolio status."""
    try:
        if app_state["zerodha_trader"]:
            positions = app_state["zerodha_trader"].get_positions()
            margins = app_state["zerodha_trader"].get_margins()
            
            total_value = 0
            for position in positions.get("net", []):
                total_value += position.get("value", 0)
            
            return {
                "total_value": total_value,
                "available_margin": margins.get("equity", {}).get("available", {}).get("cash", 0),
                "positions": positions.get("net", [])
            }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
    
    return {
        "total_value": 0,
        "available_margin": 0,
        "positions": []
    }


# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Trading Bot API", "status": "running" if app_state["running"] else "stopped"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "telegram": app_state["telegram_collector"] is not None,
            "ai_parser": app_state["ai_parser"] is not None,
            "zerodha": app_state["zerodha_trader"] is not None,
            "risk_manager": app_state["risk_manager"] is not None
        }
    }


@app.get("/status")
async def get_status():
    """Get current bot status."""
    return {
        "running": app_state["running"],
        "components_initialized": all([
            app_state["telegram_collector"],
            app_state["ai_parser"],
            app_state["zerodha_trader"],
            app_state["risk_manager"]
        ])
    }


@app.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop all trading."""
    try:
        if app_state["risk_manager"]:
            await app_state["risk_manager"].emergency_stop()
        
        logger.critical("EMERGENCY STOP ACTIVATED via API")
        return {"status": "emergency_stop_activated"}
        
    except Exception as e:
        logger.error(f"Failed to activate emergency stop: {e}")
        return {"error": str(e)}


@app.get("/portfolio")
async def get_portfolio():
    """Get current portfolio status."""
    return await get_current_portfolio()


@app.get("/signals/recent")
async def get_recent_signals(limit: int = 50):
    """Get recent signals from database."""
    try:
        from src.database.connection import get_db_session
        from src.database.models import RawMessage
        from sqlalchemy import select, desc
        
        async with get_db_session() as session:
            # Get recent raw messages
            result = await session.execute(
                select(RawMessage)
                .order_by(desc(RawMessage.message_date))
                .limit(limit)
            )
            messages = result.scalars().all()
            
            # Convert to API format
            signals = []
            for msg in messages:
                signals.append({
                    "id": msg.id,
                    "channel_id": msg.channel_id,
                    "message_id": msg.message_id,
                    "timestamp": msg.message_date.isoformat(),
                    "text": msg.message_text,
                    "sender_info": msg.sender_info,
                    "processed": msg.processed
                })
            
            return {"signals": signals}
            
    except Exception as e:
        logger.error(f"Error fetching recent signals: {e}")
        return {"error": str(e)}


@app.get("/telegram/messages/historical")
async def get_historical_messages(channel_id: str = None, days_back: int = 7, limit: int = 100):
    """Fetch historical messages from Telegram channels."""
    try:
        collector = app_state["telegram_collector"]
        
        if channel_id:
            # Fetch from specific channel
            messages = await collector.fetch_historical_messages(
                channel_id=channel_id,
                limit=limit,
                days_back=days_back
            )
        else:
            # Fetch from all channels
            messages = []
            for cid in collector.channels:
                channel_messages = await collector.fetch_historical_messages(
                    channel_id=cid,
                    limit=limit // len(collector.channels),
                    days_back=days_back
                )
                messages.extend(channel_messages)
        
        return {
            "messages": messages,
            "count": len(messages),
            "channels": collector.channels
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical messages: {e}")
        return {"error": str(e)}


@app.post("/telegram/messages/backfill")
async def backfill_historical_messages(days_back: int = 7):
    """Backfill historical messages and store in database."""
    try:
        collector = app_state["telegram_collector"]
        
        # Run backfill process
        await collector.backfill_historical_messages(days_back=days_back)
        
        return {
            "success": True,
            "message": f"Backfill completed for last {days_back} days"
        }
        
    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        return {"error": str(e)}


@app.get("/telegram/channels/info")
async def get_channel_info():
    """Get information about monitored Telegram channels."""
    try:
        collector = app_state["telegram_collector"]
        channel_info = await collector.get_channel_info()
        
        return {
            "channels": channel_info,
            "count": len(channel_info)
        }
        
    except Exception as e:
        logger.error(f"Error fetching channel info: {e}")
        return {"error": str(e)}


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    app_state["running"] = False


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("Starting Trading Bot...")
    
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()