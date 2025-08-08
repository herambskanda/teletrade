# Kite Connect API Integration

## Overview
The trading bot is now fully integrated with Zerodha Kite Connect APIs for real-time trading, historical data fetching, and market data streaming.

## Current Implementation Status

### ✅ Completed Features

#### 1. **Authentication & Connection**
- Access token-based authentication
- Connection validation on startup
- User profile fetching

#### 2. **Historical Data API**
- Fetch daily/minute candles for any instrument
- Support for multiple intervals (1min, 3min, 5min, 10min, 15min, 30min, 60min, day)
- Continuous data for F&O contracts
- Open Interest (OI) data support
- Automatic instrument token lookup by symbol

#### 3. **Order Management**
- Place market/limit/SL orders
- Support for all product types (CNC, MIS, NRML)
- Order modification and cancellation
- Order status tracking
- Paper trading mode with simulation

#### 4. **Market Data**
- Real-time quotes via REST API
- Instrument master list with caching
- Symbol search functionality
- Support for all exchanges (NSE, BSE, NFO, MCX, CDS)

#### 5. **Portfolio Management**
- Get positions (net and day)
- Fetch holdings
- Margin/funds information
- P&L calculation

#### 6. **WebSocket Streaming**
- Real-time price streaming setup
- Multiple subscription modes (LTP, Quote, Full)
- Order update postbacks
- Automatic reconnection handling

## Configuration

### Environment Variables (.env)
```bash
# Zerodha Kite Configuration
KITE_API_KEY=p1azabgr32cikm26
KITE_API_SECRET=tpmcx0weg8q7h1mx9s8dwte0ehu9a870
KITE_ACCESS_TOKEN=zUKdwswW160JR0Yo2evv6BLxRrDAgmme
KITE_USER_ID=CD7525

# Trading Mode
ENABLE_LIVE_TRADING=false  # Set to true for real trading
ENABLE_PAPER_TRADING=true   # Set to false to disable paper mode
```

## API Methods Available

### Core Trading Methods

```python
# Initialize trader
trader = ZerodhaTrader()

# Place an order
order_id = await trader.place_order(
    symbol="RELIANCE",
    transaction_type="BUY",
    quantity=10,
    order_type="LIMIT",
    price=2500.0,
    product="CNC",
    exchange="NSE"
)

# Get historical data by symbol
data = trader.get_historical_data_by_symbol(
    symbol="INFY",
    from_date=date(2025, 1, 1),
    to_date=date(2025, 8, 7),
    interval="day",
    exchange="NSE"
)

# Get real-time quotes
quotes = trader.get_quote(["NSE:TCS", "NSE:WIPRO"])

# Get instruments list
instruments = trader.get_instruments("NSE")

# Search for instrument
instrument = trader.search_instrument("HDFC", "NSE")

# Get positions and margins
positions = trader.get_positions()
margins = trader.get_margins()
```

### Historical Data Options

```python
# Get historical data with instrument token
data = trader.get_historical_data(
    instrument_token=738561,  # RELIANCE
    from_date=date(2025, 1, 1),
    to_date=date(2025, 8, 7),
    interval="5minute",
    continuous=False,  # Set True for continuous F&O data
    oi=False          # Set True to include Open Interest
)
```

## Testing

### Run Integration Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run comprehensive test
python test_kite_integration.py

# Run specific live API test
python test_live_kite_api.py
```

### Test Coverage
- ✅ Connection validation
- ✅ Margin/funds retrieval
- ✅ Instrument fetching and search
- ✅ Real-time quotes
- ✅ Historical data (daily & intraday)
- ✅ Order placement (paper mode)
- ✅ Position tracking
- ✅ Signal execution pipeline

## Safety Features

### Paper Trading Mode
- All orders are simulated when `ENABLE_PAPER_TRADING=true`
- Historical data returns simulated data in paper mode
- Margins show virtual balance (₹100,000)
- No real money involved

### Live Trading Safeguards
- Requires both `ENABLE_LIVE_TRADING=true` and `ENABLE_PAPER_TRADING=false`
- Risk manager validates all trades before execution
- Emergency stop endpoint available
- Complete audit trail in database

## Switching to Live Trading

### Prerequisites
1. Valid Kite Connect subscription
2. Fresh access token (expires daily)
3. Sufficient funds in trading account
4. Risk parameters configured

### Steps to Enable
1. Generate fresh access token:
   ```bash
   python get_kite_access_token.py
   ```

2. Update `.env` file:
   ```bash
   KITE_ACCESS_TOKEN=<new_token>
   ENABLE_LIVE_TRADING=true
   ENABLE_PAPER_TRADING=false
   ```

3. Test with small quantities first:
   ```bash
   python test_kite_integration.py
   ```

4. Start the trading bot:
   ```bash
   python src/main.py
   ```

## API Rate Limits

- **Historical Data**: 3 requests per second
- **Order Placement**: 10 requests per second  
- **Market Quotes**: 10 requests per second
- **WebSocket**: 3000 subscriptions per connection

## Error Handling

The integration includes comprehensive error handling:
- Connection failures auto-retry
- Invalid tokens trigger re-authentication
- API errors logged with details
- Graceful degradation in paper mode

## Monitoring

### Logs
- Location: `logs/trading_bot.log`
- Includes all API calls and responses
- Error tracking with stack traces

### Dashboard
- Real-time monitoring via Streamlit
- View positions, orders, and P&L
- Signal tracking and execution status

## Common Issues & Solutions

### Access Token Expired
- Access tokens expire at 3:30 AM daily
- Generate new token using login flow
- Update in `.env` file

### Instrument Not Found
- Ensure correct exchange specified
- Use exact tradingsymbol from NSE/BSE
- Check if instrument is active/not expired

### Historical Data Not Available
- Some instruments have limited history
- Intraday data available for 60 days
- Daily data available for years

### WebSocket Connection Issues
- Check network connectivity
- Verify access token is valid
- Ensure not exceeding subscription limit

## Next Steps

1. **Production Deployment**
   - Set up token refresh automation
   - Configure production database
   - Enable monitoring and alerts

2. **Advanced Features**
   - Implement bracket/cover orders
   - Add options strategies
   - Enable basket orders

3. **Risk Management**
   - Set position limits
   - Configure stop-loss automation
   - Add drawdown controls

## Support

- Kite Connect Docs: https://kite.trade/docs/connect/v3/
- API Forum: https://kite.trade/forum/
- GitHub Issues: Track in project repository

---

**Important**: Always test thoroughly in paper trading mode before enabling live trading. The system handles real money and can execute trades that result in financial losses.