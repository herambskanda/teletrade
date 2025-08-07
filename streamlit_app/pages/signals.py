"""Signals monitoring and analysis page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


def show():
    """Display the signals page."""
    
    st.markdown('<h1 class="main-header">🎯 Signal Analysis</h1>', unsafe_allow_html=True)
    
    # Signal metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Signals Today", "23", "+8")
    
    with col2:
        st.metric("Success Rate", "72.5%", "+3.2%")
    
    with col3:
        st.metric("Avg Confidence", "0.78", "+0.05")
    
    with col4:
        st.metric("Auto Executed", "18", "+5")
    
    st.markdown("---")
    
    # Filters and controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_filter = st.date_input("From Date", datetime.now() - timedelta(days=7))
    
    with col2:
        channel_filter = st.multiselect(
            "Channels",
            ["TradingGuru", "StockAlerts", "FnOSignals", "QuickTips", "MarketMaster"],
            default=["TradingGuru", "StockAlerts"]
        )
    
    with col3:
        confidence_filter = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.1)
    
    with col4:
        signal_type = st.selectbox("Signal Type", ["All", "BUY", "SELL"])
    
    # Real-time signals feed
    st.subheader("🔴 Live Signal Feed")
    
    # Container for live updates
    signal_container = st.container()
    
    with signal_container:
        # Sample live signals
        live_signals = [
            {
                "time": "11:45:32",
                "channel": "TradingGuru",
                "symbol": "RELIANCE",
                "signal": "BUY",
                "price": "2865",
                "target": "2900",
                "sl": "2840",
                "confidence": 0.85,
                "status": "New"
            },
            {
                "time": "11:44:15",
                "channel": "FnOSignals",
                "symbol": "NIFTY 22000 CE",
                "signal": "BUY",
                "price": "145",
                "target": "165",
                "sl": "130",
                "confidence": 0.79,
                "status": "Processing"
            },
            {
                "time": "11:43:28",
                "channel": "StockAlerts",
                "symbol": "TCS",
                "signal": "SELL",
                "price": "4156",
                "target": "4120",
                "sl": "4180",
                "confidence": 0.72,
                "status": "Executed"
            }
        ]
        
        for signal in live_signals:
            status_color = {
                "New": "🟡",
                "Processing": "🔵", 
                "Executed": "🟢",
                "Rejected": "🔴"
            }[signal["status"]]
            
            signal_color = "green" if signal["signal"] == "BUY" else "red"
            
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0; 
                        background: linear-gradient(90deg, #f8f9fa, #ffffff);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: {signal_color};">{signal["signal"]} {signal["symbol"]}</strong> 
                        @ ₹{signal["price"]} | TGT: ₹{signal["target"]} | SL: ₹{signal["sl"]}
                    </div>
                    <div>
                        {status_color} {signal["status"]} | 
                        Confidence: {signal["confidence"]:.0%} | 
                        {signal["time"]}
                    </div>
                </div>
                <small style="color: #666;">Source: {signal["channel"]}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Historical signals analysis
    st.markdown("---")
    st.subheader("📊 Historical Signals")
    
    # Sample historical signals data
    signals_data = {
        'Date': pd.date_range('2024-01-01', periods=50, freq='D'),
        'Channel': ['TradingGuru', 'StockAlerts', 'FnOSignals'] * 16 + ['QuickTips', 'MarketMaster'],
        'Symbol': ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ITC'] * 10,
        'Signal': ['BUY', 'SELL'] * 25,
        'Entry_Price': [2800 + i*10 + (i%5)*100 for i in range(50)],
        'Exit_Price': [2800 + i*10 + (i%5)*100 + (-1)**(i%2) * 50 for i in range(50)],
        'Confidence': [0.5 + (i%5)*0.1 for i in range(50)],
        'P&L': [(-1)**(i%2) * (50 + i*10) for i in range(50)],
        'Status': ['Executed'] * 40 + ['Rejected'] * 10
    }
    
    signals_df = pd.DataFrame(signals_data)
    
    # Filter data
    if channel_filter:
        signals_df = signals_df[signals_df['Channel'].isin(channel_filter)]
    
    signals_df = signals_df[signals_df['Confidence'] >= confidence_filter]
    
    if signal_type != "All":
        signals_df = signals_df[signals_df['Signal'] == signal_type]
    
    # Display filtered signals
    display_columns = ['Date', 'Channel', 'Symbol', 'Signal', 'Entry_Price', 'Exit_Price', 'P&L', 'Confidence', 'Status']
    
    def style_signals(val):
        if val == 'BUY':
            return 'color: green; font-weight: bold'
        elif val == 'SELL':
            return 'color: red; font-weight: bold'
        elif isinstance(val, (int, float)) and val > 0:
            return 'color: green'
        elif isinstance(val, (int, float)) and val < 0:
            return 'color: red'
        return ''
    
    styled_signals = signals_df[display_columns].style.applymap(style_signals)
    
    st.dataframe(styled_signals, use_container_width=True)
    
    # Signal analytics
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Signal Performance by Channel")
        
        # Channel performance metrics
        channel_perf = signals_df.groupby('Channel').agg({
            'P&L': 'mean',
            'Confidence': 'mean',
            'Status': lambda x: (x == 'Executed').mean() * 100
        }).round(2)
        
        channel_perf.columns = ['Avg P&L', 'Avg Confidence', 'Execution Rate (%)']
        
        # Create bar chart
        fig_channel = px.bar(
            channel_perf.reset_index(),
            x='Channel',
            y='Avg P&L',
            title="Average P&L by Channel",
            color='Avg P&L',
            color_continuous_scale=['red', 'white', 'green']
        )
        
        st.plotly_chart(fig_channel, use_container_width=True)
        
        # Display channel performance table
        st.dataframe(channel_perf, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Confidence vs Performance")
        
        # Scatter plot of confidence vs P&L
        fig_scatter = px.scatter(
            signals_df,
            x='Confidence',
            y='P&L',
            color='Signal',
            title="Signal Confidence vs P&L",
            hover_data=['Symbol', 'Channel'],
            color_discrete_map={'BUY': 'green', 'SELL': 'red'}
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Confidence bins analysis
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        signals_df['Confidence_Bin'] = pd.cut(signals_df['Confidence'], bins=bins, right=False)
        
        bin_analysis = signals_df.groupby('Confidence_Bin').agg({
            'P&L': ['mean', 'count'],
            'Status': lambda x: (x == 'Executed').mean() * 100
        }).round(2)
        
        bin_analysis.columns = ['Avg P&L', 'Count', 'Success Rate (%)']
        st.dataframe(bin_analysis, use_container_width=True)
    
    # Signal quality metrics
    st.markdown("---")
    st.subheader("🔍 Signal Quality Analysis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_signals = len(signals_df)
        st.metric("Total Signals", total_signals)
    
    with col2:
        executed_signals = len(signals_df[signals_df['Status'] == 'Executed'])
        execution_rate = (executed_signals / total_signals * 100) if total_signals > 0 else 0
        st.metric("Execution Rate", f"{execution_rate:.1f}%")
    
    with col3:
        profitable_signals = len(signals_df[(signals_df['Status'] == 'Executed') & (signals_df['P&L'] > 0)])
        win_rate = (profitable_signals / executed_signals * 100) if executed_signals > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col4:
        avg_pnl = signals_df[signals_df['Status'] == 'Executed']['P&L'].mean()
        st.metric("Avg P&L per Signal", f"₹{avg_pnl:.0f}")
    
    # AI Model Performance
    st.markdown("---")
    st.subheader("🧠 AI Model Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Model accuracy over time
        model_perf_data = {
            'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
            'Accuracy': [0.65 + 0.01*i + 0.05*((i%7)-3)/10 for i in range(30)]
        }
        
        model_df = pd.DataFrame(model_perf_data)
        
        fig_model = go.Figure()
        fig_model.add_trace(go.Scatter(
            x=model_df['Date'],
            y=model_df['Accuracy'],
            mode='lines+markers',
            name='Model Accuracy',
            line=dict(color='purple')
        ))
        
        fig_model.update_layout(
            title="AI Model Accuracy Over Time",
            yaxis_title="Accuracy",
            yaxis=dict(range=[0.5, 1.0])
        )
        
        st.plotly_chart(fig_model, use_container_width=True)
    
    with col2:
        # Model comparison
        model_comparison = {
            'Model': ['Claude-3-Haiku', 'Llama-3.1-8B', 'GPT-4-Mini'],
            'Accuracy': [0.78, 0.72, 0.75],
            'Speed (ms)': [150, 200, 180],
            'Cost per 1K': [0.25, 0.15, 0.30],
            'Usage (%)': [60, 25, 15]
        }
        
        model_comp_df = pd.DataFrame(model_comparison)
        
        st.subheader("Model Comparison")
        st.dataframe(model_comp_df, use_container_width=True)
        
        # Usage pie chart
        fig_usage = px.pie(
            model_comp_df,
            values='Usage (%)',
            names='Model',
            title="Model Usage Distribution"
        )
        
        st.plotly_chart(fig_usage, use_container_width=True)
    
    # Signal configuration
    st.markdown("---")
    st.subheader("⚙️ Signal Configuration")
    
    with st.expander("🔧 Advanced Signal Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.7, 0.05)
            st.slider("Maximum Position Size", 10000, 100000, 50000, 5000)
            st.checkbox("Auto-execute high confidence signals", True)
            st.checkbox("Enable signal filtering by sector", False)
        
        with col2:
            st.multiselect("Blacklisted symbols", ["YESBANK", "SUZLON"], [])
            st.selectbox("Risk level", ["Conservative", "Moderate", "Aggressive"])
            st.number_input("Max signals per hour", 1, 20, 5)
            st.checkbox("Send Telegram alerts for new signals", True)
    
    # Export and refresh
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("🔄 Signal feed updates automatically every 5 seconds")
    
    with col2:
        if st.button("📊 Export Signal Data"):
            st.success("Signal data exported successfully!")
        
        if st.button("🔄 Manual Refresh"):
            st.rerun()