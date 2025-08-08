"""
Trading Tools for AI Agent
Specialized tools for the AI agent to interact with the trading system.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time
from dataclasses import dataclass
import asyncio

from src.trading.zerodha_client import ZerodhaTrader, OrderType, TransactionType, Product, Variety
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TradingResult:
    """Result of a trading operation."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    order_id: Optional[str] = None
    error: Optional[str] = None


class TradingTools:
    """Trading tools for AI agent to execute orders."""
    
    def __init__(self):
        """Initialize trading tools."""
        self.trader = ZerodhaTrader()
        self.settings = get_settings()
        
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        current_time = datetime.now().time()
        market_start = time(9, 15)  # 9:15 AM
        market_end = time(15, 30)   # 3:30 PM
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        weekday = datetime.now().weekday()
        is_weekday = weekday < 5  # Monday to Friday
        
        return is_weekday and market_start <= current_time <= market_end
    
    async def place_order(
        self,
        symbol: str,
        action: str,  # BUY or SELL
        quantity: int,
        price: Optional[float] = None,
        order_type: str = "MARKET",
        exchange: str = "NSE",
        product: str = "CNC",
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
        tag: str = "ai_agent"
    ) -> TradingResult:
        """
        Place a trading order.
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'PERSISTENT25AUG5100CE')
            action: 'BUY' or 'SELL'
            quantity: Number of shares/lots
            price: Limit price (for LIMIT orders)
            order_type: 'MARKET', 'LIMIT', 'SL', 'SL-M'
            exchange: 'NSE', 'BSE', 'NFO', 'CDS', 'MCX'
            product: 'CNC', 'MIS', 'NRML'
            stop_loss: Stop loss price
            target: Target price
            tag: Order tag for identification
        """
        try:
            if not self.trader.is_connected:
                return TradingResult(
                    success=False,
                    message="Not connected to trading API",
                    error="Connection failed"
                )
            
            # Determine variety based on market status
            if self.is_market_open():
                variety = "regular"
                variety_msg = "regular order (market open)"
            else:
                variety = "amo"
                variety_msg = "AMO order (market closed)"
            
            # For market orders during closed hours, set a reasonable limit price
            if order_type == "MARKET" and not self.is_market_open():
                # Get last traded price if available
                quotes = self.trader.get_quote([f"{exchange}:{symbol}"])
                quote_key = f"{exchange}:{symbol}"
                
                if quotes and quote_key in quotes:
                    last_price = quotes[quote_key].get('last_price', 0)
                    if last_price > 0:
                        # Set limit price with 2% buffer for AMO
                        buffer = 0.02 if action == "BUY" else -0.02
                        price = last_price * (1 + buffer)
                        order_type = "LIMIT"
                        logger.info(f"Converted MARKET order to LIMIT at ₹{price} for AMO")
            
            # Place the order
            order_id = await self.trader.place_order(
                symbol=symbol,
                transaction_type=action,
                quantity=quantity,
                price=price,
                order_type=order_type,
                product=product,
                exchange=exchange,
                validity="DAY",
                variety=variety,
                tag=tag
            )
            
            if order_id:
                result_data = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "order_type": order_type,
                    "variety": variety
                }
                
                message = f"✅ Order placed successfully! {action} {quantity} {symbol} at {order_type}"
                if price:
                    message += f" ₹{price}"
                message += f" ({variety_msg})"
                
                return TradingResult(
                    success=True,
                    message=message,
                    data=result_data,
                    order_id=order_id
                )
            else:
                return TradingResult(
                    success=False,
                    message="Failed to place order",
                    error="Order placement returned no ID"
                )
                
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return TradingResult(
                success=False,
                message=f"Order placement failed: {str(e)}",
                error=str(e)
            )
    
    async def modify_order(
        self,
        order_id: str,
        price: Optional[float] = None,
        quantity: Optional[int] = None,
        trigger_price: Optional[float] = None
    ) -> TradingResult:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            price: New limit price
            quantity: New quantity
            trigger_price: New trigger price (for SL orders)
        """
        try:
            if not self.trader.is_connected:
                return TradingResult(
                    success=False,
                    message="Not connected to trading API"
                )
            
            success = await self.trader.modify_order(
                order_id=order_id,
                price=price,
                quantity=quantity,
                trigger_price=trigger_price
            )
            
            if success:
                modifications = []
                if price:
                    modifications.append(f"price=₹{price}")
                if quantity:
                    modifications.append(f"qty={quantity}")
                if trigger_price:
                    modifications.append(f"trigger=₹{trigger_price}")
                
                return TradingResult(
                    success=True,
                    message=f"✅ Order {order_id} modified: {', '.join(modifications)}",
                    data={"order_id": order_id, "modifications": modifications}
                )
            else:
                return TradingResult(
                    success=False,
                    message=f"Failed to modify order {order_id}",
                    error="Modification failed"
                )
                
        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return TradingResult(
                success=False,
                message=f"Order modification failed: {str(e)}",
                error=str(e)
            )
    
    async def cancel_order(self, order_id: str) -> TradingResult:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
        """
        try:
            if not self.trader.is_connected:
                return TradingResult(
                    success=False,
                    message="Not connected to trading API"
                )
            
            success = await self.trader.cancel_order(order_id)
            
            if success:
                return TradingResult(
                    success=True,
                    message=f"✅ Order {order_id} cancelled successfully",
                    data={"order_id": order_id, "action": "cancelled"}
                )
            else:
                return TradingResult(
                    success=False,
                    message=f"Failed to cancel order {order_id}",
                    error="Cancellation failed"
                )
                
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return TradingResult(
                success=False,
                message=f"Order cancellation failed: {str(e)}",
                error=str(e)
            )
    
    def get_positions(self) -> TradingResult:
        """Get current positions."""
        try:
            positions = self.trader.get_positions()
            
            net_positions = positions.get("net", [])
            day_positions = positions.get("day", [])
            
            # Filter out zero quantity positions
            active_net = [pos for pos in net_positions if pos.get("quantity", 0) != 0]
            active_day = [pos for pos in day_positions if pos.get("quantity", 0) != 0]
            
            position_summary = []
            for pos in active_net:
                pnl = pos.get("pnl", 0)
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                position_summary.append({
                    "symbol": pos.get("tradingsymbol"),
                    "quantity": pos.get("quantity"),
                    "average_price": pos.get("average_price"),
                    "last_price": pos.get("last_price"),
                    "pnl": pnl,
                    "pnl_formatted": f"{pnl_emoji} ₹{pnl:,.2f}"
                })
            
            return TradingResult(
                success=True,
                message=f"📊 Positions: {len(active_net)} net, {len(active_day)} day",
                data={
                    "net_positions": active_net,
                    "day_positions": active_day,
                    "position_summary": position_summary
                }
            )
            
        except Exception as e:
            logger.error(f"Get positions error: {e}")
            return TradingResult(
                success=False,
                message=f"Failed to get positions: {str(e)}",
                error=str(e)
            )
    
    def get_orders(self) -> TradingResult:
        """Get today's orders."""
        try:
            orders = self.trader.get_orders()
            
            if not orders:
                return TradingResult(
                    success=True,
                    message="📝 No orders today",
                    data={"orders": []}
                )
            
            # Categorize orders by status
            open_orders = [o for o in orders if o.get("status") in ["OPEN", "TRIGGER PENDING"]]
            completed_orders = [o for o in orders if o.get("status") == "COMPLETE"]
            cancelled_orders = [o for o in orders if o.get("status") == "CANCELLED"]
            rejected_orders = [o for o in orders if o.get("status") == "REJECTED"]
            
            order_summary = {
                "total": len(orders),
                "open": len(open_orders),
                "completed": len(completed_orders),
                "cancelled": len(cancelled_orders),
                "rejected": len(rejected_orders)
            }
            
            return TradingResult(
                success=True,
                message=f"📝 Orders: {order_summary['total']} total, {order_summary['open']} open",
                data={
                    "orders": orders,
                    "open_orders": open_orders,
                    "completed_orders": completed_orders,
                    "cancelled_orders": cancelled_orders,
                    "rejected_orders": rejected_orders,
                    "summary": order_summary
                }
            )
            
        except Exception as e:
            logger.error(f"Get orders error: {e}")
            return TradingResult(
                success=False,
                message=f"Failed to get orders: {str(e)}",
                error=str(e)
            )
    
    def get_margins(self) -> TradingResult:
        """Get account margins."""
        try:
            margins = self.trader.get_margins()
            
            if not margins:
                return TradingResult(
                    success=False,
                    message="Failed to get margins data"
                )
            
            equity = margins.get("equity", {})
            available = equity.get("available", {})
            
            margin_info = {
                "available_cash": available.get("cash", 0),
                "total_balance": available.get("live_balance", 0),
                "opening_balance": available.get("opening_balance", 0),
                "intraday_payin": available.get("intraday_payin", 0)
            }
            
            return TradingResult(
                success=True,
                message=f"💰 Available: ₹{margin_info['available_cash']:,.2f}",
                data={"margins": margins, "summary": margin_info}
            )
            
        except Exception as e:
            logger.error(f"Get margins error: {e}")
            return TradingResult(
                success=False,
                message=f"Failed to get margins: {str(e)}",
                error=str(e)
            )
    
    def search_instrument(self, symbol: str, exchange: str = "NSE") -> TradingResult:
        """
        Search for an instrument.
        
        Args:
            symbol: Symbol to search for
            exchange: Exchange to search in
        """
        try:
            instrument = self.trader.search_instrument(symbol, exchange)
            
            if instrument:
                return TradingResult(
                    success=True,
                    message=f"✅ Found {symbol} on {exchange}",
                    data={
                        "instrument": instrument,
                        "symbol": instrument["tradingsymbol"],
                        "token": instrument["instrument_token"],
                        "exchange": instrument["exchange"],
                        "type": instrument.get("instrument_type"),
                        "lot_size": instrument.get("lot_size", 1)
                    }
                )
            else:
                return TradingResult(
                    success=False,
                    message=f"❌ Instrument {symbol} not found on {exchange}",
                    error="Instrument not found"
                )
                
        except Exception as e:
            logger.error(f"Instrument search error: {e}")
            return TradingResult(
                success=False,
                message=f"Search failed: {str(e)}",
                error=str(e)
            )
    
    def get_quote(self, symbol: str, exchange: str = "NSE") -> TradingResult:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange
        """
        try:
            quote_key = f"{exchange}:{symbol}"
            quotes = self.trader.get_quote([quote_key])
            
            if quotes and quote_key in quotes:
                quote_data = quotes[quote_key]
                
                price_info = {
                    "last_price": quote_data.get("last_price", 0),
                    "change": quote_data.get("net_change", 0),
                    "change_percent": quote_data.get("change", 0),
                    "volume": quote_data.get("volume", 0),
                    "ohlc": quote_data.get("ohlc", {})
                }
                
                change_emoji = "📈" if price_info["change"] >= 0 else "📉"
                
                return TradingResult(
                    success=True,
                    message=f"💹 {symbol}: ₹{price_info['last_price']} {change_emoji} {price_info['change']:+.2f}",
                    data={"quote": quote_data, "summary": price_info}
                )
            else:
                return TradingResult(
                    success=False,
                    message=f"❌ No quote data for {symbol}",
                    error="Quote not available"
                )
                
        except Exception as e:
            logger.error(f"Get quote error: {e}")
            return TradingResult(
                success=False,
                message=f"Failed to get quote: {str(e)}",
                error=str(e)
            )
    
    async def exit_position(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: str = "MARKET",
        exchange: str = "NSE",
        product: str = "CNC"
    ) -> TradingResult:
        """
        Exit a position (sell if long, buy if short).
        
        Args:
            symbol: Symbol to exit
            quantity: Quantity to exit (if None, exits full position)
            price: Exit price (for LIMIT orders)
            order_type: 'MARKET' or 'LIMIT'
            exchange: Exchange
            product: Product type
        """
        try:
            # Get current position
            positions_result = self.get_positions()
            if not positions_result.success:
                return TradingResult(
                    success=False,
                    message="Failed to get positions for exit"
                )
            
            # Find the position for this symbol
            position = None
            for pos in positions_result.data["net_positions"]:
                if pos.get("tradingsymbol") == symbol:
                    position = pos
                    break
            
            if not position:
                return TradingResult(
                    success=False,
                    message=f"❌ No position found for {symbol}",
                    error="Position not found"
                )
            
            current_qty = position.get("quantity", 0)
            if current_qty == 0:
                return TradingResult(
                    success=False,
                    message=f"❌ No quantity to exit for {symbol}",
                    error="Zero quantity"
                )
            
            # Determine exit parameters
            exit_qty = abs(quantity) if quantity else abs(current_qty)
            
            # Determine transaction type (opposite of current position)
            if current_qty > 0:
                action = "SELL"  # Exit long position
            else:
                action = "BUY"   # Exit short position
            
            # Place exit order
            result = await self.place_order(
                symbol=symbol,
                action=action,
                quantity=exit_qty,
                price=price,
                order_type=order_type,
                exchange=exchange,
                product=product,
                tag="exit_position"
            )
            
            if result.success:
                result.message = f"🚪 Exit order placed: {action} {exit_qty} {symbol} " + \
                               result.message.split("Order placed successfully!")[-1]
            
            return result
            
        except Exception as e:
            logger.error(f"Exit position error: {e}")
            return TradingResult(
                success=False,
                message=f"Failed to exit position: {str(e)}",
                error=str(e)
            )