# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated trading bot that monitors Telegram channels for trading signals, uses AI to parse messages, validates trades through comprehensive risk management, and executes orders via Zerodha Kite Connect API. The system includes a Streamlit dashboard and is designed with production-grade safety features.

## Development Commands

### Running the Application
```bash
# Start the main trading bot (FastAPI server on port 8000)
python src/main.py

# Start the Streamlit dashboard (port 8501) 
python run_streamlit.py

# Both can run simultaneously for full functionality
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys

# Initialize PostgreSQL database
createdb trading_bot
```

### Configuration
- Always start in **paper trading mode** (`ENABLE_LIVE_TRADING=false` in .env)
- Set `ENABLE_LIVE_TRADING=true` only after thorough testing
- Required APIs: Telegram Bot, Zerodha Kite Connect, OpenRouter, PostgreSQL, Redis

## Architecture Overview

### Core Processing Pipeline
```
Telegram Channels → Message Collection → AI Parsing → Risk Validation → Order Execution
                                     ↓
                              Database Storage ← Dashboard Monitoring
```

### Key Components
- **`src/main.py`** - FastAPI entry point with async message processing loop
- **`src/telegram/collector.py`** - Multi-channel Telegram monitoring with Redis queuing
- **`src/ai/parser.py`** - OpenRouter AI integration with model fallbacks and confidence scoring
- **`src/trading/zerodha_client.py`** - Zerodha Kite Connect wrapper with paper/live trading modes
- **`src/risk/risk_manager.py`** - Multi-layered risk validation system with ML anomaly detection
- **`src/database/models.py`** - Complete audit trail from messages → signals → trades
- **`streamlit_app/`** - Modular dashboard with real-time monitoring

### Configuration Management
- **Pydantic-based settings** in `config/settings.py`
- Environment variables loaded from `.env`
- Typed configuration with validation
- Production/development mode switching

### Database Schema
Well-structured relational design with complete audit trail:
- `TelegramChannel` → `RawMessage` → `TradingSignal` → `Trade`
- Risk events, positions, backtest results tracked separately
- All operations logged for compliance and debugging

## Safety & Risk Management

### Critical Safety Features
- **Paper trading mode** - test without real money
- **Emergency stop** - `/emergency-stop` API endpoint
- **Multi-layer risk validation**:
  - Position size limits
  - Daily loss limits
  - Drawdown tracking
  - Margin requirements
  - Market hours validation
  - ML-based anomaly detection

### Development Safety
- **Never enable live trading** during development
- **Always test with paper trading first**
- Risk manager has fail-safe approach - prefers missing trades over bad trades
- Comprehensive logging to `logs/trading_bot.log`

## Extension Points

### Adding New Features
- **New signal sources**: Extend `ai/parser.py` or create new parsers
- **New risk checks**: Add validation methods to `RiskManager` class
- **New brokers**: Implement trading interface similar to `ZerodhaTrader`
- **Dashboard features**: Add new pages in `streamlit_app/pages/`

### Common Patterns
- **Async-first**: All I/O operations use async/await
- **Error handling**: Comprehensive logging with graceful degradation
- **State management**: Global application state in `main.py`
- **Configuration**: Environment-based with Pydantic validation
- **Database**: SQLAlchemy ORM with async support

## Key Dependencies

- **FastAPI** - Async web framework and API server
- **python-telegram-bot** - Telegram integration
- **kiteconnect** - Zerodha API client  
- **openai** - AI model access via OpenRouter
- **streamlit** - Dashboard frontend
- **SQLAlchemy** - Database ORM
- **Redis** - Message queuing
- **scikit-learn** - ML anomaly detection

## Important Notes

- This is a **financial trading system** - extreme care required when making changes
- **Test thoroughly in paper trading mode** before any live deployment
- The system processes real financial data and can execute real trades
- Always validate configuration and API connectivity before starting
- Emergency stop functionality must always be accessible and functional
- Maintain complete audit trail - never delete raw messages or trade records