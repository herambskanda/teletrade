"""Main Streamlit application for the trading bot dashboard."""

import streamlit as st
import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

# Import dashboard pages
from pages import dashboard, positions, signals, backtest, settings

# Configure Streamlit page
st.set_page_config(
    page_title="Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .metric-card {
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .positive {
        color: #00c851;
    }
    .negative {
        color: #ff4444;
    }
    .neutral {
        color: #33b5e5;
    }
    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.title("🤖 Trading Bot")
        st.markdown("---")
        
        # Bot status section
        st.subheader("Bot Status")
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            bot_status = st.selectbox(
                "Status",
                ["Running", "Paused", "Stopped"],
                index=0
            )
        
        with status_col2:
            if bot_status == "Running":
                st.success("🟢 Active")
            elif bot_status == "Paused":
                st.warning("🟡 Paused")
            else:
                st.error("🔴 Stopped")
        
        # Emergency controls
        st.markdown("---")
        st.subheader("Emergency Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            emergency_stop = st.button(
                "🚨 Emergency Stop",
                type="primary",
                help="Stop all trading immediately"
            )
        
        with col2:
            if st.button("⚠️ Pause Bot"):
                st.warning("Bot paused!")
        
        if emergency_stop:
            st.error("🚨 EMERGENCY STOP ACTIVATED!")
            st.balloons()
        
        # Navigation
        st.markdown("---")
        st.subheader("Navigation")
        
        page = st.selectbox(
            "Select Page",
            [
                "📊 Dashboard",
                "📈 Positions",
                "🎯 Signals",
                "📋 Backtest",
                "⚙️ Settings"
            ]
        )
        
        # Quick stats
        st.markdown("---")
        st.subheader("Quick Stats")
        st.metric("Total P&L", "₹12,450", "₹850")
        st.metric("Active Positions", "7", "2")
        st.metric("Win Rate", "68%", "5%")
        st.metric("Signals Today", "15", "3")
        
        # System info
        st.markdown("---")
        st.subheader("System Info")
        st.text("📡 Telegram: Connected")
        st.text("🔗 Zerodha: Connected")
        st.text("🧠 AI Models: Active")
        st.text("💾 Database: Healthy")
        
    # Main content area
    if page == "📊 Dashboard":
        dashboard.show()
    elif page == "📈 Positions":
        positions.show()
    elif page == "🎯 Signals":
        signals.show()
    elif page == "📋 Backtest":
        backtest.show()
    elif page == "⚙️ Settings":
        settings.show()


if __name__ == "__main__":
    main()