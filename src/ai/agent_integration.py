"""
AI Trading Agent Integration
Connects the AI agent with Telegram collector and risk management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from src.ai.trading_agent import TradingAgent
from src.risk.risk_manager import RiskManager
from config.settings import get_settings

logger = logging.getLogger(__name__)


class TradingAgentIntegration:
    """Integration layer for AI Trading Agent with the trading bot system."""
    
    def __init__(self):
        """Initialize the integration layer."""
        self.agent = TradingAgent()
        self.risk_manager = RiskManager()
        self.settings = get_settings()
        
        # Performance metrics
        self.processing_stats = {
            "messages_processed": 0,
            "actions_executed": 0,
            "successful_orders": 0,
            "risk_blocks": 0,
            "errors": 0
        }
        
    async def process_telegram_message(
        self,
        message: str,
        channel_id: str,
        message_id: str,
        sender_info: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a Telegram message through the complete trading pipeline.
        
        Args:
            message: The message text
            channel_id: Telegram channel ID
            message_id: Message ID
            sender_info: Information about the sender
            metadata: Additional metadata
            
        Returns:
            Processing result with all details
        """
        start_time = datetime.now()
        
        try:
            self.processing_stats["messages_processed"] += 1
            
            logger.info(f"Processing message {message_id} from channel {channel_id}")
            logger.debug(f"Message content: {message[:200]}...")
            
            # Step 1: AI Analysis
            logger.info("Step 1: AI message analysis")
            context = {
                "channel_id": channel_id,
                "message_id": message_id,
                "sender": sender_info,
                "metadata": metadata,
                "timestamp": start_time.isoformat()
            }
            
            analysis = await self.agent.analyze_message(message, context)
            
            # Step 2: Risk Assessment
            risk_result = await self._assess_risk(analysis, context)
            
            # Step 3: Execute if approved
            execution_result = None
            if risk_result["approved"] and analysis.get("confidence", 0) >= 0.7:
                logger.info("Step 3: Executing trading action")
                self.processing_stats["actions_executed"] += 1
                execution_result = await self.agent.execute_action(analysis)
                
                if execution_result and execution_result.success:
                    self.processing_stats["successful_orders"] += 1
                    if execution_result.order_id:
                        logger.info(f"Order placed successfully: {execution_result.order_id}")
            else:
                logger.info("Step 3: Action blocked by risk management or low confidence")
                if not risk_result["approved"]:
                    self.processing_stats["risk_blocks"] += 1
                
                execution_result = {
                    "success": False,
                    "message": "Action blocked by risk management or low confidence",
                    "reason": risk_result.get("reason", "low_confidence"),
                    "risk_details": risk_result
                }
            
            # Step 4: Compile result
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message_id": message_id,
                "channel_id": channel_id,
                "original_message": message,
                "context": context,
                "analysis": analysis,
                "risk_assessment": risk_result,
                "execution": execution_result,
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
                "stats": self.processing_stats.copy()
            }
            
            logger.info(f"Message processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.processing_stats["errors"] += 1
            logger.error(f"Message processing error: {e}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "message_id": message_id,
                "channel_id": channel_id,
                "original_message": message,
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
                "stats": self.processing_stats.copy()
            }
    
    async def _assess_risk(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for the proposed trading action.
        
        Args:
            analysis: AI analysis result
            context: Message context
            
        Returns:
            Risk assessment result
        """
        try:
            action = analysis.get("action")
            confidence = analysis.get("confidence", 0)
            parameters = analysis.get("parameters", {})
            
            # Skip risk assessment for no-action or low confidence
            if action == "no_action" or confidence < 0.7:
                return {
                    "approved": False,
                    "reason": "no_action_or_low_confidence",
                    "confidence": confidence,
                    "risk_level": "LOW"
                }
            
            # For order placement, check comprehensive risk
            if action == "place_order":
                return await self._assess_order_risk(parameters, context)
            
            # For position exit, generally lower risk
            elif action == "exit_position":
                return await self._assess_exit_risk(parameters, context)
            
            # For order modification, medium risk
            elif action in ["modify_order", "cancel_order"]:
                return {
                    "approved": True,
                    "reason": "order_management_action",
                    "risk_level": "LOW",
                    "details": "Order management actions have lower risk"
                }
            
            else:
                return {
                    "approved": False,
                    "reason": "unknown_action",
                    "risk_level": "HIGH",
                    "details": f"Unknown action type: {action}"
                }
                
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "approved": False,
                "reason": "risk_assessment_error",
                "risk_level": "HIGH",
                "error": str(e)
            }
    
    async def _assess_order_risk(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for order placement."""
        try:
            # Get current portfolio
            current_portfolio = await self._get_current_portfolio()
            
            # Create signal dict for risk manager
            signal = {
                "symbol": parameters.get("symbol"),
                "signal_type": parameters.get("action"),
                "quantity": parameters.get("quantity"),
                "entry_price": parameters.get("price"),
                "stop_loss": parameters.get("stop_loss"),
                "target_price": parameters.get("target"),
                "instrument_type": "EQUITY" if parameters.get("exchange") in ["NSE", "BSE"] else "DERIVATIVE",
                "confidence_score": context.get("analysis", {}).get("confidence", 0),
                "source": f"telegram_{context.get('channel_id')}",
                "timestamp": datetime.now()
            }
            
            # Run risk validation
            risk_results = await self.risk_manager.validate_trade(signal, current_portfolio)
            
            # Check for critical risks
            critical_risks = [r for r in risk_results if r.severity.value in ["HIGH", "CRITICAL"] and not r.passed]
            
            if critical_risks:
                return {
                    "approved": False,
                    "reason": "critical_risks_detected",
                    "risk_level": "HIGH",
                    "critical_risks": [{"message": r.message, "severity": r.severity.value} for r in critical_risks],
                    "details": f"Blocked by {len(critical_risks)} critical risk(s)"
                }
            
            # Check for medium risks
            medium_risks = [r for r in risk_results if r.severity.value == "MEDIUM" and not r.passed]
            
            risk_level = "MEDIUM" if medium_risks else "LOW"
            
            return {
                "approved": True,
                "reason": "risk_validation_passed",
                "risk_level": risk_level,
                "risk_checks": len(risk_results),
                "passed_checks": len([r for r in risk_results if r.passed]),
                "medium_risks": [{"message": r.message, "severity": r.severity.value} for r in medium_risks] if medium_risks else [],
                "details": f"Passed {len([r for r in risk_results if r.passed])}/{len(risk_results)} risk checks"
            }
            
        except Exception as e:
            logger.error(f"Order risk assessment error: {e}")
            return {
                "approved": False,
                "reason": "order_risk_assessment_error",
                "risk_level": "HIGH",
                "error": str(e)
            }
    
    async def _assess_exit_risk(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for position exit."""
        try:
            symbol = parameters.get("symbol")
            
            # Exiting positions is generally lower risk
            # But we should verify the position exists
            positions_result = self.agent.trading_tools.get_positions()
            
            if positions_result.success:
                position_found = False
                for pos in positions_result.data.get("net_positions", []):
                    if pos.get("tradingsymbol") == symbol and pos.get("quantity", 0) != 0:
                        position_found = True
                        break
                
                if not position_found:
                    return {
                        "approved": False,
                        "reason": "no_position_to_exit",
                        "risk_level": "LOW",
                        "details": f"No position found for {symbol}"
                    }
            
            return {
                "approved": True,
                "reason": "position_exit_approved",
                "risk_level": "LOW",
                "details": "Position exit is generally low risk"
            }
            
        except Exception as e:
            logger.error(f"Exit risk assessment error: {e}")
            return {
                "approved": False,
                "reason": "exit_risk_assessment_error", 
                "risk_level": "MEDIUM",
                "error": str(e)
            }
    
    async def _get_current_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio for risk assessment."""
        try:
            positions_result = self.agent.trading_tools.get_positions()
            margins_result = self.agent.trading_tools.get_margins()
            
            portfolio = {
                "total_value": 0,
                "available_margin": 0,
                "positions": []
            }
            
            if margins_result.success:
                portfolio["available_margin"] = margins_result.data.get("summary", {}).get("available_cash", 0)
            
            if positions_result.success:
                positions = positions_result.data.get("net_positions", [])
                portfolio["positions"] = positions
                
                # Calculate total portfolio value
                total_value = sum(pos.get("value", 0) for pos in positions)
                portfolio["total_value"] = total_value
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Portfolio fetch error: {e}")
            return {
                "total_value": 0,
                "available_margin": 0,
                "positions": []
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.processing_stats.copy()
        
        # Calculate success rates
        if stats["messages_processed"] > 0:
            stats["action_rate"] = stats["actions_executed"] / stats["messages_processed"]
            stats["error_rate"] = stats["errors"] / stats["messages_processed"]
        else:
            stats["action_rate"] = 0
            stats["error_rate"] = 0
        
        if stats["actions_executed"] > 0:
            stats["success_rate"] = stats["successful_orders"] / stats["actions_executed"]
            stats["risk_block_rate"] = stats["risk_blocks"] / stats["actions_executed"]
        else:
            stats["success_rate"] = 0
            stats["risk_block_rate"] = 0
        
        return stats
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.processing_stats = {
            "messages_processed": 0,
            "actions_executed": 0,
            "successful_orders": 0,
            "risk_blocks": 0,
            "errors": 0
        }
        logger.info("Performance statistics reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        try:
            health = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "components": {}
            }
            
            # Check trading tools
            try:
                margins_result = self.agent.trading_tools.get_margins()
                health["components"]["trading_api"] = {
                    "status": "healthy" if margins_result.success else "error",
                    "connected": self.agent.trading_tools.trader.is_connected,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health["components"]["trading_api"] = {
                    "status": "error",
                    "error": str(e),
                    "connected": False
                }
            
            # Check AI model
            try:
                # Quick test analysis
                test_analysis = await self.agent.analyze_message("Market update test message")
                health["components"]["ai_model"] = {
                    "status": "healthy" if "analysis" in test_analysis else "error",
                    "model": self.agent.primary_model,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health["components"]["ai_model"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Check risk manager
            try:
                health["components"]["risk_manager"] = {
                    "status": "healthy",
                    "emergency_stop": await self.risk_manager.is_emergency_stop_active(),
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health["components"]["risk_manager"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Determine overall status
            component_statuses = [comp.get("status") for comp in health["components"].values()]
            if "error" in component_statuses:
                health["overall_status"] = "degraded"
            if all(status == "error" for status in component_statuses):
                health["overall_status"] = "error"
            
            health["stats"] = self.get_performance_stats()
            
            return health
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }


# Global instance
trading_agent_integration = TradingAgentIntegration()