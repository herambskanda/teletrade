"""OpenRouter AI-powered message parser for extracting trading signals."""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict

import aiohttp
from openai import AsyncOpenAI
import backoff

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class TradingSignal:
    """Structured trading signal extracted from message."""
    signal_type: str  # BUY, SELL, HOLD
    instrument_type: str  # EQUITY, FUTURES, OPTIONS
    symbol: str
    quantity: Optional[int] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    strike_price: Optional[float] = None
    expiry_date: Optional[str] = None
    option_type: Optional[str] = None  # CE or PE
    confidence_score: float = 0.0
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AISignalParser:
    """OpenRouter-powered message analysis with multiple model fallbacks."""
    
    def __init__(self):
        """Initialize the AI parser."""
        self.settings = settings
        self.models = self.settings.openrouter_models
        self.primary_model = self.models[0] if self.models else "anthropic/claude-3-haiku"
        self.confidence_threshold = self.settings.min_signal_confidence
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.settings.openrouter_api_key,
        )
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for signal extraction."""
        return """You are an expert trading signal analyzer. Your task is to extract trading signals from messages.

Analyze the message and extract the following information if present:
1. Signal Type: BUY, SELL, or HOLD
2. Instrument Type: EQUITY, FUTURES, or OPTIONS
3. Symbol/Ticker
4. Quantity (if mentioned)
5. Entry Price
6. Stop Loss
7. Target Price(s)
8. For options: Strike Price, Expiry Date, Option Type (CE/PE)

Return the analysis in the following JSON format:
{
    "signal_type": "BUY/SELL/HOLD",
    "instrument_type": "EQUITY/FUTURES/OPTIONS",
    "symbol": "SYMBOL_NAME",
    "quantity": null or number,
    "entry_price": null or number,
    "stop_loss": null or number,
    "target_price": null or number,
    "strike_price": null or number (for options),
    "expiry_date": null or "YYYY-MM-DD" (for options),
    "option_type": null or "CE/PE" (for options),
    "confidence_score": 0.0 to 1.0,
    "reasoning": "Brief explanation of the signal extraction"
}

If the message doesn't contain a clear trading signal, return:
{
    "signal_type": "HOLD",
    "confidence_score": 0.0,
    "reasoning": "No clear trading signal found"
}

Be conservative with confidence scores:
- 0.9-1.0: Very clear, explicit signal with all key details
- 0.7-0.9: Clear signal with most details present
- 0.5-0.7: Probable signal but missing some details
- Below 0.5: Unclear or ambiguous signal"""
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, Exception),
        max_tries=3,
        max_time=60
    )
    async def parse_message(
        self,
        message_text: str,
        channel_context: Optional[Dict[str, Any]] = None
    ) -> Optional[TradingSignal]:
        """Parse a message to extract trading signal."""
        try:
            # Prepare the user prompt
            user_prompt = f"Extract trading signal from this message:\n\n{message_text}"
            
            if channel_context:
                user_prompt += f"\n\nChannel context: {json.dumps(channel_context)}"
            
            # Try primary model first
            signal = await self._call_model(self.primary_model, user_prompt)
            
            # If primary model fails or low confidence, try fallback models
            if not signal or signal.confidence_score < self.confidence_threshold:
                for fallback_model in self.models[1:]:
                    logger.info(f"Trying fallback model: {fallback_model}")
                    fallback_signal = await self._call_model(fallback_model, user_prompt)
                    
                    if fallback_signal and fallback_signal.confidence_score > (signal.confidence_score if signal else 0):
                        signal = fallback_signal
                        
                    if signal and signal.confidence_score >= self.confidence_threshold:
                        break
            
            return signal if signal and signal.confidence_score >= self.confidence_threshold else None
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    async def _call_model(self, model: str, user_prompt: str) -> Optional[TradingSignal]:
        """Call a specific model to extract signal."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Low temperature for consistent extraction
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            if response.choices and response.choices[0].message.content:
                signal_data = json.loads(response.choices[0].message.content)
                
                # Create TradingSignal object
                signal = TradingSignal(
                    signal_type=signal_data.get("signal_type", "HOLD"),
                    instrument_type=signal_data.get("instrument_type", "EQUITY"),
                    symbol=signal_data.get("symbol", ""),
                    quantity=signal_data.get("quantity"),
                    entry_price=signal_data.get("entry_price"),
                    stop_loss=signal_data.get("stop_loss"),
                    target_price=signal_data.get("target_price"),
                    strike_price=signal_data.get("strike_price"),
                    expiry_date=signal_data.get("expiry_date"),
                    option_type=signal_data.get("option_type"),
                    confidence_score=signal_data.get("confidence_score", 0.0),
                    reasoning=signal_data.get("reasoning", "")
                )
                
                logger.info(f"Model {model} extracted signal with confidence {signal.confidence_score}")
                return signal
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {model}: {e}")
        except Exception as e:
            logger.error(f"Error calling model {model}: {e}")
        
        return None
    
    async def batch_parse_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Optional[TradingSignal]]:
        """Parse multiple messages in batch."""
        tasks = []
        
        for message in messages:
            task = self.parse_message(
                message.get("message_text", ""),
                message.get("channel_context")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        signals = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in batch parsing: {result}")
                signals.append(None)
            else:
                signals.append(result)
        
        return signals
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate if a signal has minimum required information."""
        # Must have a valid signal type
        if signal.signal_type not in ["BUY", "SELL"]:
            return False
        
        # Must have a symbol
        if not signal.symbol or signal.symbol.strip() == "":
            return False
        
        # For BUY/SELL signals, should have at least entry price or current action
        if signal.signal_type in ["BUY", "SELL"]:
            if not signal.entry_price and signal.confidence_score < 0.7:
                return False
        
        # For OPTIONS, must have strike and expiry
        if signal.instrument_type == "OPTIONS":
            if not signal.strike_price or not signal.expiry_date or not signal.option_type:
                return False
        
        return True


async def test_parser():
    """Test the AI parser with sample messages."""
    parser = AISignalParser()
    
    test_messages = [
        "BUY RELIANCE 2850 TARGET 2900 2950 SL 2800",
        "NIFTY 22000 CE BUY ABOVE 150 TGT 180 200 SL 120",
        "Sell HDFC Bank below 1650 for targets of 1620 and 1600 with stop loss at 1680",
        "Market looking weak, stay in cash",
        "Good morning everyone!"
    ]
    
    for message in test_messages:
        print(f"\nParsing: {message}")
        signal = await parser.parse_message(message)
        if signal:
            print(f"Extracted Signal: {signal.to_dict()}")
        else:
            print("No valid signal extracted")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_parser())