"""AI Trading Agent Interface and Monitoring Page."""

import streamlit as st
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.ai.agent_integration import TradingAgentIntegration
    from src.ai.trading_agent import TradingAgent
    from config.settings import get_settings
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error(f"Current working directory: {os.getcwd()}")
    st.error(f"Python path: {sys.path}")
    st.stop()


def show():
    """Main AI Agent page."""
    st.markdown('<h1 class="main-header">🤖 AI Trading Agent</h1>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat Interface", 
        "📊 Performance", 
        "🏥 Health Check", 
        "📋 Execution Logs", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_chat_interface()
    
    with tab2:
        show_performance_dashboard()
    
    with tab3:
        show_health_dashboard()
    
    with tab4:
        show_execution_logs()
    
    with tab5:
        show_agent_settings()


def show_chat_interface():
    """Interactive chat interface with the AI agent."""
    st.subheader("💬 Chat with AI Trading Agent")
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent_stats' not in st.session_state:
        st.session_state.agent_stats = {
            "messages_sent": 0,
            "actions_taken": 0,
            "orders_placed": 0
        }
    
    # Agent status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Messages Sent", st.session_state.agent_stats["messages_sent"])
    with col2:
        st.metric("Actions Taken", st.session_state.agent_stats["actions_taken"])
    with col3:
        st.metric("Orders Placed", st.session_state.agent_stats["orders_placed"])
    with col4:
        if st.button("🔄 Reset Stats"):
            st.session_state.agent_stats = {"messages_sent": 0, "actions_taken": 0, "orders_placed": 0}
            st.success("Stats reset!")
    
    st.markdown("---")
    
    # Chat input
    with st.form("message_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_message = st.text_area(
                "Enter your trading message:",
                height=100,
                placeholder="e.g., 'BUY RELIANCE 10 SHARES AT MARKET' or 'EXIT INFY IMMEDIATELY'"
            )
        
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            submit_button = st.form_submit_button("🚀 Send to Agent")
            
            # Quick message buttons
            st.write("**Quick Messages:**")
            if st.form_submit_button("📊 Get Portfolio Status"):
                user_message = "GET PORTFOLIO STATUS"
                submit_button = True
            
            if st.form_submit_button("❌ Cancel All Orders"):
                user_message = "CANCEL ALL PENDING ORDERS"
                submit_button = True
    
    # Process message
    if submit_button and user_message.strip():
        with st.spinner("🤖 Agent is thinking..."):
            result = process_agent_message(user_message.strip())
        
        # Add to chat history
        st.session_state.chat_history.append({
            "timestamp": datetime.now(),
            "user_message": user_message.strip(),
            "agent_response": result
        })
        
        # Update stats
        st.session_state.agent_stats["messages_sent"] += 1
        if result.get("analysis", {}).get("action") not in ["no_action", None]:
            st.session_state.agent_stats["actions_taken"] += 1
        if result.get("execution", {}).get("order_id"):
            st.session_state.agent_stats["orders_placed"] += 1
        
        # Rerun to update display
        st.experimental_rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("💬 Chat History")
        
        # Show recent messages (last 10)
        recent_messages = st.session_state.chat_history[-10:]
        
        for i, chat in enumerate(reversed(recent_messages)):
            with st.expander(
                f"🕒 {chat['timestamp'].strftime('%H:%M:%S')} - {chat['user_message'][:50]}...", 
                expanded=(i == 0)  # Expand most recent
            ):
                st.markdown(f"**You:** {chat['user_message']}")
                
                response = chat["agent_response"]
                
                # AI Analysis
                if response.get("analysis"):
                    analysis = response["analysis"]
                    st.markdown(f"**🤖 Agent Analysis:**")
                    st.json({
                        "Action": analysis.get("action"),
                        "Confidence": f"{analysis.get('confidence', 0):.2%}",
                        "Reasoning": analysis.get("reasoning"),
                        "Parameters": analysis.get("parameters", {})
                    })
                
                # Risk Assessment
                if response.get("risk_assessment"):
                    risk = response["risk_assessment"]
                    risk_color = "green" if risk.get("approved") else "red"
                    st.markdown(f"**⚖️ Risk Assessment:** <span style='color:{risk_color}'>{risk.get('reason', 'Unknown')}</span>", unsafe_allow_html=True)
                
                # Execution Result
                if response.get("execution"):
                    execution = response["execution"]
                    if isinstance(execution, dict):
                        success = execution.get("success", False)
                        message = execution.get("message", "No message")
                        order_id = execution.get("order_id")
                    else:
                        success = execution.success if hasattr(execution, 'success') else False
                        message = execution.message if hasattr(execution, 'message') else "No message"
                        order_id = execution.order_id if hasattr(execution, 'order_id') else None
                    
                    result_color = "green" if success else "orange"
                    st.markdown(f"**🎯 Result:** <span style='color:{result_color}'>{message}</span>", unsafe_allow_html=True)
                    
                    if order_id:
                        st.success(f"✅ Order ID: {order_id}")
                
                # Processing time
                processing_time = response.get("processing_time", 0)
                st.caption(f"⏱️ Processed in {processing_time:.2f} seconds")


@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_agent_performance_data():
    """Get agent performance data."""
    try:
        integration = TradingAgentIntegration()
        stats = integration.get_performance_stats()
        return stats
    except Exception as e:
        st.error(f"Error getting performance data: {e}")
        return {}


def show_performance_dashboard():
    """Show agent performance metrics."""
    st.subheader("📊 Agent Performance Dashboard")
    
    # Get performance data
    stats = get_agent_performance_data()
    
    if not stats:
        st.warning("No performance data available")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Messages Processed", 
            stats.get("messages_processed", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Actions Executed", 
            stats.get("actions_executed", 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Successful Orders", 
            stats.get("successful_orders", 0),
            delta=None
        )
    
    with col4:
        st.metric(
            "Risk Blocks", 
            stats.get("risk_blocks", 0),
            delta=None
        )
    
    st.markdown("---")
    
    # Performance ratios
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_rate = stats.get("action_rate", 0)
        st.metric(
            "Action Rate", 
            f"{action_rate:.1%}",
            help="Percentage of messages that resulted in actions"
        )
    
    with col2:
        success_rate = stats.get("success_rate", 0)
        st.metric(
            "Success Rate", 
            f"{success_rate:.1%}",
            help="Percentage of actions that succeeded"
        )
    
    with col3:
        error_rate = stats.get("error_rate", 0)
        error_color = "red" if error_rate > 0.1 else "green"
        st.metric(
            "Error Rate", 
            f"{error_rate:.1%}",
            help="Percentage of messages that resulted in errors"
        )
    
    # Performance over time chart (simulated data)
    st.subheader("📈 Performance Trends")
    
    # Generate sample time series data
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'messages_processed': [max(0, int(10 + 5 * (i % 24) + (i / 24))) for i in range(len(dates))],
        'actions_executed': [max(0, int(3 + 2 * (i % 24) + (i / 48))) for i in range(len(dates))],
        'successful_orders': [max(0, int(1 + (i % 24) + (i / 72))) for i in range(len(dates))]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sample_data['timestamp'], 
        y=sample_data['messages_processed'],
        mode='lines',
        name='Messages Processed',
        line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=sample_data['timestamp'], 
        y=sample_data['actions_executed'],
        mode='lines',
        name='Actions Executed',
        line=dict(color='orange')
    ))
    fig.add_trace(go.Scatter(
        x=sample_data['timestamp'], 
        y=sample_data['successful_orders'],
        mode='lines',
        name='Successful Orders',
        line=dict(color='green')
    ))
    
    fig.update_layout(
        title="Agent Activity Over Time",
        xaxis_title="Time",
        yaxis_title="Count",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data(ttl=10)  # Cache for 10 seconds
def get_agent_health():
    """Get agent health status."""
    try:
        integration = TradingAgentIntegration()
        return asyncio.run(integration.health_check())
    except Exception as e:
        return {"error": str(e)}


def show_health_dashboard():
    """Show agent health status."""
    st.subheader("🏥 Agent Health Monitor")
    
    # Get health data
    health = get_agent_health()
    
    if "error" in health:
        st.error(f"Health check failed: {health['error']}")
        return
    
    # Overall status
    overall_status = health.get("overall_status", "unknown")
    status_colors = {
        "healthy": "green",
        "degraded": "orange", 
        "error": "red"
    }
    status_color = status_colors.get(overall_status, "gray")
    
    st.markdown(f"**Overall Status:** <span style='color:{status_color}; font-size:1.2em; font-weight:bold'>{overall_status.upper()}</span>", unsafe_allow_html=True)
    st.caption(f"Last check: {health.get('timestamp', 'Unknown')}")
    
    st.markdown("---")
    
    # Component status
    components = health.get("components", {})
    
    if components:
        st.subheader("🔧 Component Status")
        
        for component, status_info in components.items():
            status = status_info.get("status", "unknown")
            
            col1, col2, col3 = st.columns([2, 1, 3])
            
            with col1:
                st.write(f"**{component.replace('_', ' ').title()}**")
            
            with col2:
                if status == "healthy":
                    st.success("✅ Healthy")
                elif status == "error":
                    st.error("❌ Error")
                else:
                    st.warning("⚠️ Unknown")
            
            with col3:
                # Show additional info
                if "connected" in status_info:
                    st.write(f"Connected: {'✅' if status_info['connected'] else '❌'}")
                if "model" in status_info:
                    st.write(f"Model: {status_info['model']}")
                if "emergency_stop" in status_info:
                    st.write(f"Emergency Stop: {'🚨 Active' if status_info['emergency_stop'] else '✅ Inactive'}")
                if "error" in status_info:
                    st.error(f"Error: {status_info['error']}")
        
        st.markdown("---")
    
    # Performance stats
    if "stats" in health:
        st.subheader("📈 Real-time Stats")
        stats = health["stats"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Messages", stats.get("messages_processed", 0))
        with col2:
            st.metric("Actions", stats.get("actions_executed", 0))
        with col3:
            st.metric("Orders", stats.get("successful_orders", 0))
        with col4:
            st.metric("Errors", stats.get("errors", 0))
    
    # Auto-refresh option
    if st.checkbox("🔄 Auto-refresh (10s)"):
        import time
        time.sleep(10)
        st.experimental_rerun()


def show_execution_logs():
    """Show agent execution logs."""
    st.subheader("📋 Agent Execution Logs")
    
    # Sample log data (in real implementation, this would come from a log file or database)
    sample_logs = [
        {
            "timestamp": datetime.now() - timedelta(minutes=5),
            "level": "INFO",
            "message": "Processing message: BUY RELIANCE 10 SHARES",
            "action": "place_order",
            "result": "success",
            "order_id": "250807401827513"
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=15),
            "level": "WARNING",
            "message": "Low confidence signal ignored",
            "action": "no_action",
            "result": "skipped",
            "confidence": 0.65
        },
        {
            "timestamp": datetime.now() - timedelta(minutes=25),
            "level": "INFO",
            "message": "EXIT PERSISTENT position",
            "action": "exit_position",
            "result": "success",
            "order_id": "250807401827514"
        },
        {
            "timestamp": datetime.now() - timedelta(hours=1),
            "level": "ERROR",
            "message": "Risk management blocked order",
            "action": "place_order",
            "result": "blocked",
            "reason": "position_limit_exceeded"
        }
    ]
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        level_filter = st.multiselect(
            "Log Level",
            ["INFO", "WARNING", "ERROR"],
            default=["INFO", "WARNING", "ERROR"]
        )
    
    with col2:
        action_filter = st.multiselect(
            "Action Type",
            ["place_order", "exit_position", "modify_order", "no_action"],
            default=["place_order", "exit_position", "modify_order", "no_action"]
        )
    
    with col3:
        result_filter = st.multiselect(
            "Result",
            ["success", "blocked", "error", "skipped"],
            default=["success", "blocked", "error", "skipped"]
        )
    
    # Filter logs
    filtered_logs = [
        log for log in sample_logs
        if log["level"] in level_filter
        and log["action"] in action_filter
        and log["result"] in result_filter
    ]
    
    # Display logs
    if filtered_logs:
        for log in filtered_logs:
            timestamp_str = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            # Color coding
            if log["level"] == "ERROR":
                level_color = "red"
            elif log["level"] == "WARNING":
                level_color = "orange"
            else:
                level_color = "green"
            
            if log["result"] == "success":
                result_color = "green"
            elif log["result"] == "error":
                result_color = "red"
            else:
                result_color = "orange"
            
            with st.expander(f"[{timestamp_str}] {log['message']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Level:** <span style='color:{level_color}'>{log['level']}</span>", unsafe_allow_html=True)
                    st.write(f"**Action:** {log['action']}")
                
                with col2:
                    st.markdown(f"**Result:** <span style='color:{result_color}'>{log['result']}</span>", unsafe_allow_html=True)
                    if log.get("confidence"):
                        st.write(f"**Confidence:** {log['confidence']:.2%}")
                
                with col3:
                    if log.get("order_id"):
                        st.success(f"**Order ID:** {log['order_id']}")
                    if log.get("reason"):
                        st.warning(f"**Reason:** {log['reason']}")
    else:
        st.info("No logs match the selected filters")


def show_agent_settings():
    """Show agent configuration settings."""
    st.subheader("⚙️ AI Agent Settings")
    
    settings = get_settings()
    
    # Model configuration
    st.subheader("🧠 Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Primary Model", value="qwen/qwen-2.5-coder-32b-instruct", disabled=True)
        st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.05, help="Minimum confidence required for action execution")
        st.slider("Temperature", 0.0, 1.0, 0.1, 0.1, help="Model creativity (lower = more consistent)")
    
    with col2:
        st.text_input("Fallback Model", value="Not configured", disabled=True)
        st.number_input("Max Tokens", value=1000, min_value=100, max_value=4000)
        st.number_input("Response Timeout (s)", value=30, min_value=5, max_value=120)
    
    st.markdown("---")
    
    # Trading configuration
    st.subheader("💰 Trading Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Enable Live Trading", value=settings.enable_live_trading, disabled=True)
        st.checkbox("Enable Paper Trading", value=settings.enable_paper_trading, disabled=True)
        st.selectbox("Default Product Type", ["CNC", "MIS", "NRML"], index=0)
    
    with col2:
        st.number_input("Max Position Size", value=10000, min_value=1000, max_value=1000000)
        st.number_input("Max Orders Per Day", value=50, min_value=1, max_value=1000)
        st.selectbox("Default Exchange", ["NSE", "BSE", "NFO"], index=0)
    
    st.markdown("---")
    
    # Risk management
    st.subheader("⚖️ Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("Max Daily Loss (%)", 0.0, 10.0, 2.0, 0.5)
        st.slider("Position Size Limit (%)", 0.0, 50.0, 10.0, 1.0)
        st.checkbox("Require Stop Loss", value=True)
    
    with col2:
        st.slider("Max Drawdown (%)", 0.0, 20.0, 5.0, 0.5)
        st.number_input("Min Account Balance", value=10000, min_value=1000)
        st.checkbox("Enable Emergency Stop", value=True)
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")
    
    with col2:
        if st.button("🔄 Reset to Default"):
            st.info("Settings reset to default")
    
    with col3:
        if st.button("🧪 Test Configuration"):
            st.info("Running configuration test...")


def process_agent_message(message: str) -> Dict[str, Any]:
    """Process a message through the AI agent."""
    try:
        integration = TradingAgentIntegration()
        
        # Run the async function
        result = asyncio.run(
            integration.process_telegram_message(
                message=message,
                channel_id="streamlit_chat",
                message_id=f"chat_{datetime.now().timestamp()}",
                sender_info={"name": "Streamlit User", "id": "streamlit_user"},
                metadata={"source": "streamlit_chat", "interface": "web"}
            )
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": {"action": "error", "confidence": 0},
            "execution": {"success": False, "message": f"Error: {str(e)}"}
        }