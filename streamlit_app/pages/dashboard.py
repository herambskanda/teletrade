"""Main dashboard page for the trading bot."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


def show():
    """Display the main dashboard."""
    
    # Page header
    st.markdown('<h1 class="main-header">📊 Trading Dashboard</h1>', unsafe_allow_html=True)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Portfolio Value",
            "₹2,45,680",
            "₹8,450 (3.6%)",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Today's P&L",
            "₹3,250",
            "₹1,200 (1.5%)",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Active Positions",
            "7",
            "2",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Available Margin",
            "₹1,25,000",
            "₹15,000",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Portfolio Performance")
        
        # Generate sample portfolio data
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        portfolio_values = []
        base_value = 200000
        
        for i, date in enumerate(dates):
            # Simulate portfolio growth with some volatility
            growth = 0.0005 * i  # Slight upward trend
            volatility = np.random.normal(0, 0.02)  # Daily volatility
            value = base_value * (1 + growth + volatility)
            portfolio_values.append(value)
        
        portfolio_df = pd.DataFrame({
            'Date': dates,
            'Portfolio Value': portfolio_values
        })
        
        # Create portfolio chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['Portfolio Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Value Over Time",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            hovermode='x unified',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Asset Allocation")
        
        # Sample allocation data
        allocation_data = {
            'Asset': ['Equity', 'Futures', 'Options', 'Cash'],
            'Percentage': [45, 25, 20, 10],
            'Value': [110520, 61420, 49136, 24604]
        }
        
        allocation_df = pd.DataFrame(allocation_data)
        
        # Create pie chart
        fig = px.pie(
            allocation_df,
            values='Percentage',
            names='Asset',
            title="Current Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent activity and alerts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔔 Recent Alerts")
        
        # Sample alerts
        alerts = [
            {"time": "10:45", "type": "info", "message": "RELIANCE signal detected: BUY at 2850"},
            {"time": "10:30", "type": "success", "message": "HDFC position closed with 2.5% profit"},
            {"time": "10:15", "type": "warning", "message": "High correlation risk in banking sector"},
            {"time": "09:45", "type": "error", "message": "Order failed: Insufficient margin for NIFTY futures"},
            {"time": "09:30", "type": "info", "message": "Market opened - 5 channels active"}
        ]
        
        for alert in alerts:
            icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}[alert["type"]]
            color = {"info": "blue", "success": "green", "warning": "orange", "error": "red"}[alert["type"]]
            
            st.markdown(f"""
            <div style="padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid {color}; background-color: #f8f9fa;">
                <strong>{alert["time"]}</strong> {icon} {alert["message"]}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📋 Recent Trades")
        
        # Sample trades data
        trades_data = {
            'Time': ['10:30', '10:15', '09:45', '09:30', '09:20'],
            'Symbol': ['HDFC', 'RELIANCE', 'TCS', 'INFY', 'ITC'],
            'Action': ['SELL', 'BUY', 'BUY', 'SELL', 'BUY'],
            'Qty': [50, 100, 25, 75, 200],
            'Price': [1654.5, 2851.2, 4123.8, 1567.9, 456.3],
            'P&L': [1250.5, -450.2, 890.1, 2340.7, -123.4]
        }
        
        trades_df = pd.DataFrame(trades_data)
        
        # Style the dataframe
        def color_pnl(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'black'
            return f'color: {color}'
        
        styled_df = trades_df.style.applymap(color_pnl, subset=['P&L'])
        
        st.dataframe(styled_df, use_container_width=True)
    
    st.markdown("---")
    
    # Performance metrics
    st.subheader("📊 Performance Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Win Rate", "68.4%", "2.1%")
    
    with col2:
        st.metric("Profit Factor", "1.85", "0.12")
    
    with col3:
        st.metric("Sharpe Ratio", "1.24", "0.08")
    
    with col4:
        st.metric("Max Drawdown", "8.2%", "-1.5%")
    
    with col5:
        st.metric("Avg Trade", "₹847", "₹23")
    
    # Channel performance
    st.markdown("---")
    st.subheader("📡 Channel Performance")
    
    channel_data = {
        'Channel': ['TradingGuru', 'StockAlerts', 'FnOSignals', 'QuickTips', 'MarketMaster'],
        'Signals': [23, 18, 31, 12, 27],
        'Success Rate': [72.5, 65.8, 78.2, 58.3, 69.1],
        'Avg P&L': [1250, 890, 1680, 450, 1120],
        'Status': ['Active', 'Active', 'Active', 'Paused', 'Active']
    }
    
    channel_df = pd.DataFrame(channel_data)
    
    # Style channel status
    def color_status(val):
        color = 'green' if val == 'Active' else 'orange'
        return f'color: {color}'
    
    styled_channel_df = channel_df.style.applymap(color_status, subset=['Status'])
    
    st.dataframe(styled_channel_df, use_container_width=True)
    
    # Auto-refresh option
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 Dashboard auto-refreshes every 30 seconds when bot is running")
    
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()