"""
AI Trading Agent using Qwen 3 Coder
Analyzes Telegram messages and executes trading actions.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio

import openai
from config.settings import get_settings
from src.ai.trading_tools import TradingTools, TradingResult

logger = logging.getLogger(__name__)


class TradingAgent:
    """AI Trading Agent for analyzing Telegram messages and executing trades."""
    
    def __init__(self):
        """Initialize the trading agent."""
        self.settings = get_settings()
        self.trading_tools = TradingTools()
        
        # Initialize OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.settings.openrouter_api_key
        )
        
        # Primary model for analysis
        self.primary_model = "qwen/qwen-2.5-coder-32b-instruct"
        
        # System prompt for the trading agent
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the trading agent."""
        return """You are an expert Telegram Trading Agent. Your job is to analyze trading messages from Telegram channels and execute appropriate trading actions.

**YOUR CAPABILITIES:**
- place_order: Place buy/sell orders
- modify_order: Modify existing orders
- cancel_order: Cancel orders
- exit_position: Exit existing positions
- get_positions: Check current positions
- get_orders: Check current orders
- get_margins: Check account balance
- search_instrument: Find trading instruments
- get_quote: Get real-time prices

**TRADING MESSAGE ANALYSIS:**
You need to analyze messages and identify:
1. **INSTRUMENT**: Stock/Option symbol (e.g., RELIANCE, PERSISTENT25AUG5100CE)
2. **ACTION**: BUY, SELL, MODIFY, EXIT, CANCEL
3. **QUANTITY**: Number of shares/lots
4. **ENTRY PRICE**: Price to enter (if specified)
5. **TARGET PRICE**: Profit target (if specified) 
6. **STOP LOSS**: Risk management level (if specified)
7. **ORDER TYPE**: MARKET, LIMIT, SL, SL-M

**MESSAGE PATTERNS TO UNDERSTAND:**
- "BUY XYZ ABOVE 100" → Place BUY order with entry condition
- "SELL XYZ BELOW 90" → Place SELL order or exit position
- "EXIT XYZ" → Close existing position
- "MODIFY ORDER 123 PRICE 105" → Modify existing order
- "CANCEL ORDER 123" → Cancel order
- "TARGET REACHED - BOOK PROFITS" → Exit profitable positions
- "SL HIT - STOP LOSS" → Exit loss-making positions
- Options format: "NIFTY25AUG24000CE", "BANKNIFTY25AUG50000PE"

**RESPONSE FORMAT:**
Always respond with a JSON object containing:
```json
{
    "analysis": "Brief analysis of the message",
    "action": "place_order|modify_order|cancel_order|exit_position|get_status|no_action",
    "confidence": 0.8,
    "reasoning": "Why you chose this action",
    "parameters": {
        "symbol": "RELIANCE",
        "action": "BUY",
        "quantity": 10,
        "price": 2500.0,
        "order_type": "LIMIT",
        "exchange": "NSE",
        "product": "CNC",
        "stop_loss": 2400.0,
        "target": 2600.0
    }
}
```

**IMPORTANT RULES:**
1. **BE CONSERVATIVE**: Only act on clear, unambiguous messages
2. **SAFETY FIRST**: Always include stop-loss when possible
3. **VERIFY INSTRUMENTS**: Use search_instrument to verify symbols exist
4. **CHECK POSITIONS**: Use get_positions before exit orders
5. **HANDLE OPTIONS**: Properly format option symbols
6. **RISK MANAGEMENT**: Consider position size and account balance
7. **MARKET HOURS**: Consider AMO vs regular orders
8. **CONFIDENCE THRESHOLD**: Only execute if confidence > 0.7

**EXAMPLES:**

Input: "Can go for PERSISTENT 5100 CE ABOVE 163, TARGET 210++, SL# 120 BELOW"
Output: {
    "analysis": "Options call buying signal for PERSISTENT 5100 CE with clear entry, target, and stop-loss levels",
    "action": "place_order", 
    "confidence": 0.9,
    "reasoning": "Clear buy signal with entry condition, target and stop-loss specified",
    "parameters": {
        "symbol": "PERSISTENT25AUG5100CE",
        "action": "BUY",
        "quantity": 100,
        "price": 163.0,
        "order_type": "LIMIT",
        "exchange": "NFO",
        "product": "NRML",
        "stop_loss": 120.0,
        "target": 210.0
    }
}

Input: "Exit all positions in RELIANCE"
Output: {
    "analysis": "Clear instruction to exit all RELIANCE positions",
    "action": "exit_position",
    "confidence": 0.95,
    "reasoning": "Unambiguous exit instruction for specific stock",
    "parameters": {
        "symbol": "RELIANCE",
        "order_type": "MARKET",
        "exchange": "NSE"
    }
}

Input: "Market looking bullish today"
Output: {
    "analysis": "General market commentary without specific trading instruction",
    "action": "no_action",
    "confidence": 0.1,
    "reasoning": "No specific trading signal or actionable instruction",
    "parameters": {}
}

**CURRENT SESSION INFO:**
- Trading Mode: LIVE (real orders will be placed)
- Account: Connected to Zerodha Kite
- Available Tools: All trading functions active
- Risk Management: Active

Analyze the following message and provide your trading decision:"""

    async def analyze_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a Telegram message and determine trading action.
        
        Args:
            message: The Telegram message to analyze
            context: Optional context (channel info, sender, etc.)
        
        Returns:
            Dict containing analysis and action decision
        """
        try:
            # Add context to the message if provided
            full_prompt = f"MESSAGE: {message}"
            if context:
                full_prompt += f"\nCONTEXT: {json.dumps(context, indent=2)}"
            
            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse the AI response
            ai_response = response.choices[0].message.content
            analysis = json.loads(ai_response)
            
            # Validate the analysis
            if not self._validate_analysis(analysis):
                return {
                    "analysis": "Invalid AI response format",
                    "action": "no_action",
                    "confidence": 0.0,
                    "reasoning": "AI response validation failed",
                    "error": "Invalid analysis format"
                }
            
            logger.info(f"AI Analysis: {analysis['action']} with confidence {analysis['confidence']}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "analysis": "Failed to parse AI response",
                "action": "no_action",
                "confidence": 0.0,
                "reasoning": "JSON parsing error",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Message analysis error: {e}")
            return {
                "analysis": "Analysis failed",
                "action": "no_action", 
                "confidence": 0.0,
                "reasoning": "System error during analysis",
                "error": str(e)
            }
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Validate the AI analysis response format."""
        required_fields = ["analysis", "action", "confidence", "reasoning", "parameters"]
        
        for field in required_fields:
            if field not in analysis:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate action type
        valid_actions = ["place_order", "modify_order", "cancel_order", "exit_position", "get_status", "no_action"]
        if analysis["action"] not in valid_actions:
            logger.error(f"Invalid action: {analysis['action']}")
            return False
        
        # Validate confidence
        confidence = analysis.get("confidence", 0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            logger.error(f"Invalid confidence: {confidence}")
            return False
        
        return True
    
    async def execute_action(self, analysis: Dict[str, Any]) -> TradingResult:
        """
        Execute the trading action based on AI analysis.
        
        Args:
            analysis: The AI analysis result
            
        Returns:
            TradingResult with execution details
        """
        try:
            action = analysis.get("action")
            parameters = analysis.get("parameters", {})
            confidence = analysis.get("confidence", 0)
            
            # Check confidence threshold
            if confidence < 0.7:
                return TradingResult(
                    success=False,
                    message=f"⚠️ Action skipped - confidence {confidence:.2f} below threshold (0.7)",
                    data={"analysis": analysis}
                )
            
            # Execute the appropriate action
            if action == "place_order":
                return await self._execute_place_order(parameters)
            elif action == "modify_order":
                return await self._execute_modify_order(parameters)
            elif action == "cancel_order":
                return await self._execute_cancel_order(parameters)
            elif action == "exit_position":
                return await self._execute_exit_position(parameters)
            elif action == "get_status":
                return await self._execute_get_status(parameters)
            elif action == "no_action":
                return TradingResult(
                    success=True,
                    message="📝 No action required",
                    data={"analysis": analysis}
                )
            else:
                return TradingResult(
                    success=False,
                    message=f"❌ Unknown action: {action}",
                    error="Invalid action"
                )
                
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            return TradingResult(
                success=False,
                message=f"Action execution failed: {str(e)}",
                error=str(e)
            )
    
    async def _execute_place_order(self, params: Dict[str, Any]) -> TradingResult:
        """Execute place order action."""
        # First verify the instrument exists
        symbol = params.get("symbol")
        exchange = params.get("exchange", "NSE")
        
        if symbol:
            search_result = self.trading_tools.search_instrument(symbol, exchange)
            if not search_result.success:
                return TradingResult(
                    success=False,
                    message=f"❌ Instrument {symbol} not found on {exchange}",
                    error="Instrument not found"
                )
        
        return await self.trading_tools.place_order(
            symbol=params.get("symbol"),
            action=params.get("action"),
            quantity=params.get("quantity"),
            price=params.get("price"),
            order_type=params.get("order_type", "MARKET"),
            exchange=params.get("exchange", "NSE"),
            product=params.get("product", "CNC"),
            stop_loss=params.get("stop_loss"),
            target=params.get("target"),
            tag="ai_agent_order"
        )
    
    async def _execute_modify_order(self, params: Dict[str, Any]) -> TradingResult:
        """Execute modify order action."""
        return await self.trading_tools.modify_order(
            order_id=params.get("order_id"),
            price=params.get("price"),
            quantity=params.get("quantity"),
            trigger_price=params.get("trigger_price")
        )
    
    async def _execute_cancel_order(self, params: Dict[str, Any]) -> TradingResult:
        """Execute cancel order action."""
        return await self.trading_tools.cancel_order(
            order_id=params.get("order_id")
        )
    
    async def _execute_exit_position(self, params: Dict[str, Any]) -> TradingResult:
        """Execute exit position action."""
        return await self.trading_tools.exit_position(
            symbol=params.get("symbol"),
            quantity=params.get("quantity"),
            price=params.get("price"),
            order_type=params.get("order_type", "MARKET"),
            exchange=params.get("exchange", "NSE"),
            product=params.get("product", "CNC")
        )
    
    async def _execute_get_status(self, params: Dict[str, Any]) -> TradingResult:
        """Execute get status action."""
        # Get comprehensive status
        positions = self.trading_tools.get_positions()
        orders = self.trading_tools.get_orders()
        margins = self.trading_tools.get_margins()
        
        status_info = {
            "positions": positions.data if positions.success else {},
            "orders": orders.data if orders.success else {},
            "margins": margins.data if margins.success else {}
        }
        
        status_message = f"📊 Account Status:\n"
        if positions.success:
            status_message += f"Positions: {len(positions.data.get('position_summary', []))}\n"
        if orders.success:
            status_message += f"Orders: {orders.data.get('summary', {}).get('total', 0)}\n"
        if margins.success:
            status_message += f"Available: ₹{margins.data.get('summary', {}).get('available_cash', 0):,.2f}"
        
        return TradingResult(
            success=True,
            message=status_message,
            data=status_info
        )
    
    async def process_telegram_message(
        self,
        message: str,
        channel_id: Optional[str] = None,
        sender_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline to process a Telegram message.
        
        Args:
            message: The message text
            channel_id: Telegram channel ID
            sender_info: Information about the sender
            
        Returns:
            Complete processing result
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing Telegram message: {message[:100]}...")
            
            # Build context
            context = {}
            if channel_id:
                context["channel_id"] = channel_id
            if sender_info:
                context["sender"] = sender_info
            context["timestamp"] = start_time.isoformat()
            
            # Step 1: Analyze the message
            logger.info("Step 1: Analyzing message with AI...")
            analysis = await self.analyze_message(message, context)
            
            # Step 2: Execute the action if confidence is high enough
            if analysis.get("confidence", 0) >= 0.7 and analysis.get("action") != "no_action":
                logger.info(f"Step 2: Executing action: {analysis['action']}")
                execution_result = await self.execute_action(analysis)
            else:
                logger.info("Step 2: Skipping execution (low confidence or no action)")
                execution_result = TradingResult(
                    success=True,
                    message="No action taken",
                    data={"reason": "low_confidence_or_no_action"}
                )
            
            # Compile final result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": message,
                "context": context,
                "analysis": analysis,
                "execution": {
                    "success": execution_result.success,
                    "message": execution_result.message,
                    "data": execution_result.data,
                    "order_id": execution_result.order_id,
                    "error": execution_result.error
                },
                "processing_time": processing_time,
                "timestamp": start_time.isoformat()
            }
            
            logger.info(f"Message processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": start_time.isoformat()
            }


# Helper function for testing
def create_test_messages() -> List[Dict[str, str]]:
    """Create test messages for validation."""
    return [
        {
            "message": "Can go for PERSISTENT 5100 CE ABOVE 163, TARGET 210++, SL# 120 BELOW",
            "expected_action": "place_order",
            "description": "Options buying signal with entry, target, and stop-loss"
        },
        {
            "message": "EXIT RELIANCE IMMEDIATELY",
            "expected_action": "exit_position",
            "description": "Clear exit instruction"
        },
        {
            "message": "BUY TCS 100 SHARES AT 3500 LIMIT",
            "expected_action": "place_order",
            "description": "Equity limit buy order"
        },
        {
            "message": "Market looking bullish today, good opportunity ahead",
            "expected_action": "no_action",
            "description": "General commentary without specific instruction"
        },
        {
            "message": "MODIFY ORDER 123456 PRICE TO 2550",
            "expected_action": "modify_order",
            "description": "Order modification instruction"
        },
        {
            "message": "CANCEL ORDER 789012",
            "expected_action": "cancel_order",
            "description": "Order cancellation instruction"
        }
    ]