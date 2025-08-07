# Trading Bot - Automated Telegram Signal Trading

A comprehensive trading automation bot that monitors Telegram channels for trading signals, uses AI to parse and understand messages, and automatically executes trades through Zerodha Kite Connect API.

## Features

### Core Functionality
- **Multi-channel Telegram monitoring** - Monitor multiple Telegram groups simultaneously
- **AI-powered signal parsing** - Uses OpenRouter API with multiple LLM models for accurate signal extraction
- **Automated trading** - Execute trades through Zerodha Kite Connect API
- **Real-time position monitoring** - Track P&L, positions, and market movements
- **Comprehensive backtesting** - Test strategies with historical data including realistic costs
- **Advanced risk management** - Multiple layers of risk controls and anomaly detection

### Safety Features
- **Paper trading mode** - Test without real money
- **Emergency stop** - Instantly halt all trading
- **Risk limits** - Position size, daily loss, and drawdown controls
- **Anomaly detection** - AI-powered detection of unusual market conditions
- **Multi-layer validation** - Signal confidence, risk checks, margin validation

### Dashboard
- **Real-time monitoring** - Live portfolio tracking and performance metrics
- **Signal analysis** - Historical signal performance by channel
- **Risk metrics** - VaR, beta, correlation analysis
- **Backtesting interface** - Easy-to-use strategy testing
- **Configuration management** - Centralized settings and API management

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Bot System                           │
├─────────────────────────────────────────────────────────────────┤
│  Telegram → AI Parser → Risk Manager → Zerodha → Database      │
│     ↓           ↓           ↓            ↓          ↓          │
│  Messages → Signals → Validation → Orders → Storage           │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Redis server
- Telegram Bot Token
- Zerodha Kite Connect API credentials
- OpenRouter API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd trading-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. **Initialize database**
```bash
# Start PostgreSQL and create database
createdb trading_bot
```

5. **Run the application**
```bash
# Start the main bot
python src/main.py

# In another terminal, start the dashboard
python run_streamlit.py
```

6. **Access the dashboard**
- Open http://localhost:8501 in your browser
- Configure your settings in the Settings tab
- Monitor your bot in the Dashboard tab

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNELS=channel_id_1,channel_id_2

# Zerodha Kite Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
KITE_ACCESS_TOKEN=your_access_token

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading_bot

# Risk Management
MAX_POSITION_SIZE=100000
MAX_DAILY_LOSS=5000
ENABLE_LIVE_TRADING=false  # Set to true only when ready
```

### Getting API Keys

#### Telegram Bot
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to your `.env` file
4. Add the bot to your trading channels as an admin

#### Zerodha Kite Connect
1. Visit https://kite.trade/
2. Go to Console → Apps
3. Create a new app to get API key and secret
4. Generate access token through the login flow

#### OpenRouter
1. Visit https://openrouter.ai/
2. Sign up and go to API Keys
3. Create a new API key
4. Add credits to your account

### Channel Setup
1. Add your Telegram bot to the channels you want to monitor
2. Make the bot an admin with "Read Messages" permission
3. Get the channel IDs (they usually start with -100)
4. Add the channel IDs to your configuration

## Usage

### Starting the Bot

1. **Development Mode**
```bash
# Enable paper trading in .env
ENABLE_PAPER_TRADING=true
ENABLE_LIVE_TRADING=false

python src/main.py
```

2. **Production Mode** (Only after thorough testing)
```bash
# Enable live trading in .env
ENABLE_LIVE_TRADING=true
ENABLE_PAPER_TRADING=false

python src/main.py
```

### Dashboard Features

#### Main Dashboard
- Portfolio overview and performance metrics
- Recent trades and alerts
- Real-time P&L tracking
- Asset allocation charts

#### Positions
- Current positions with real-time P&L
- Position management tools
- Risk metrics and exposure analysis

#### Signals
- Live signal feed from Telegram channels
- Historical signal performance
- AI model accuracy tracking
- Channel-wise success rates

#### Backtesting
- Strategy testing with historical data
- Performance analysis and metrics
- Risk-adjusted returns calculation
- Export detailed reports

#### Settings
- API configuration and testing
- Trading parameters and limits
- Risk management rules
- Channel management
- Alert configuration

## Risk Management

The bot includes multiple layers of risk management:

### Pre-Trade Checks
- Position size limits
- Available margin validation
- Market hours verification
- Circuit breaker detection
- Portfolio correlation analysis

### Real-Time Monitoring
- Daily loss limits
- Maximum drawdown tracking
- Anomaly detection
- Emergency stop functionality

### Post-Trade Controls
- Automatic stop-loss orders
- Position monitoring and alerts
- Performance tracking

## Backtesting

The backtesting engine includes:
- **Realistic simulation** - Transaction costs, slippage, execution delays
- **Historical accuracy** - Uses actual market data
- **Performance metrics** - Sharpe ratio, max drawdown, win rate, profit factor
- **Risk analysis** - VaR, beta, correlation metrics
- **Channel analysis** - Performance by signal source

## API Endpoints

The bot exposes a REST API for monitoring and control:

- `GET /health` - System health check
- `GET /status` - Bot running status
- `GET /portfolio` - Current portfolio state
- `GET /signals/recent` - Recent signals
- `POST /emergency-stop` - Emergency stop trading

## Development

### Project Structure
```
trading-bot/
├── src/                    # Main application code
│   ├── telegram/          # Telegram integration
│   ├── ai/                # AI signal parsing
│   ├── trading/           # Zerodha integration
│   ├── risk/              # Risk management
│   ├── database/          # Database models
│   └── monitoring/        # System monitoring
├── streamlit_app/         # Dashboard application
│   └── pages/            # Dashboard pages
├── config/               # Configuration files
├── tests/                # Test suite
└── logs/                 # Application logs
```

### Adding New Features

1. **New signal sources** - Add parsers in `src/ai/`
2. **New risk checks** - Extend `RiskManager` class
3. **New brokers** - Implement trading interface
4. **Dashboard features** - Add pages in `streamlit_app/pages/`

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src
```

## Monitoring and Alerts

The bot provides multiple alert channels:
- **Telegram notifications** - Real-time trade alerts
- **Email alerts** - Daily summaries and critical events
- **Dashboard alerts** - Visual notifications
- **Webhook integration** - Custom alert endpoints

## Performance Optimization

- **Message queuing** - Redis-based async processing
- **Database optimization** - Indexed queries and connection pooling
- **Caching** - Frequently accessed data caching
- **Rate limiting** - API call optimization

## Security

- **API key management** - Secure credential storage
- **Input validation** - All user inputs validated
- **Audit logging** - Complete trade and action logs
- **Access control** - Dashboard authentication
- **Rate limiting** - Protection against abuse

## Troubleshooting

### Common Issues

1. **Telegram connection fails**
   - Check bot token validity
   - Verify bot permissions in channels
   - Ensure network connectivity

2. **Zerodha API errors**
   - Verify API credentials
   - Check if access token is valid
   - Ensure market hours for live data

3. **Database connection issues**
   - Check PostgreSQL server status
   - Verify database URL format
   - Ensure database exists

4. **AI parsing errors**
   - Check OpenRouter API key
   - Verify model availability
   - Monitor API usage limits

### Logs

Check application logs in:
- `logs/trading_bot.log` - Main application logs
- Console output for real-time monitoring

### Support

For issues and questions:
1. Check the logs for error details
2. Review the configuration settings
3. Test API connections individually
4. Start in paper trading mode first

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

**Important**: This software is for educational purposes only. Trading involves significant risk and can result in financial losses. The authors are not responsible for any trading losses incurred while using this software. Always test thoroughly in paper trading mode before using with real money.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.