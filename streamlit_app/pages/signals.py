"""Signals monitoring and analysis page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime, timedelta
import json


def fetch_telegram_messages(days_back=7, limit=100):
    """Fetch historical messages from FastAPI backend."""
    try:
        response = requests.get(
            f"http://localhost:8000/telegram/messages/historical",
            params={"days_back": days_back, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("messages", [])
        else:
            st.error(f"API Error: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []


def fetch_recent_signals(limit=50):
    """Fetch recent signals from database."""
    try:
        response = requests.get(
            f"http://localhost:8000/signals/recent",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("signals", [])
        else:
            st.error(f"API Error: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []


def fetch_channel_info():
    """Fetch channel information."""
    try:
        response = requests.get("http://localhost:8000/telegram/channels/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("channels", {})
        else:
            return {}
    except:
        return {}


def backfill_messages(days_back=7):
    """Trigger historical message backfill."""
    try:
        response = requests.post(
            f"http://localhost:8000/telegram/messages/backfill",
            params={"days_back": days_back},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                st.success(f"✅ {data.get('message', 'Backfill completed')}")
                return True
        st.error(f"Backfill failed: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Backfill error: {e}")
        return False


def analyze_signal_text(text):
    """Simple analysis of signal text to extract trading info."""
    text_upper = text.upper()
    
    # Detect signal type
    signal_type = "UNKNOWN"
    if any(word in text_upper for word in ["BUY", "LONG", "CALL"]):
        signal_type = "BUY"
    elif any(word in text_upper for word in ["SELL", "SHORT", "PUT"]):
        signal_type = "SELL"
    elif any(word in text_upper for word in ["CE", "CALL OPTION"]):
        signal_type = "CALL"
    elif any(word in text_upper for word in ["PE", "PUT OPTION"]):
        signal_type = "PUT"
    
    # Detect instruments
    instrument = "UNKNOWN"
    if "NIFTY" in text_upper:
        instrument = "NIFTY"
    elif "BANKNIFTY" in text_upper:
        instrument = "BANKNIFTY"
    elif "SENSEX" in text_upper:
        instrument = "SENSEX"
    
    # Simple confidence based on text patterns
    confidence = 0.5
    if any(word in text_upper for word in ["TARGET", "SL", "STOP LOSS"]):
        confidence += 0.2
    if any(word in text_upper for word in ["BUY", "SELL"]):
        confidence += 0.2
    if len(text) > 50:
        confidence += 0.1
        
    return {
        "signal_type": signal_type,
        "instrument": instrument,
        "confidence": min(confidence, 1.0)
    }


def show():
    """Display the signals page."""
    
    st.markdown('<h1 class="main-header">🎯 Signal Analysis</h1>', unsafe_allow_html=True)
    
    # Add refresh controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    with col2:
        days_back = st.selectbox("Historical Days", [1, 3, 7, 15, 30], index=2)
    
    with col3:
        if st.button("📥 Backfill"):
            with st.spinner("Fetching historical messages..."):
                backfill_messages(days_back)
    
    # Fetch channel information
    channel_info = fetch_channel_info()
    
    # Fetch real messages and signals
    messages = fetch_telegram_messages(days_back=days_back, limit=200)
    db_signals = fetch_recent_signals(limit=100)
    
    if not messages and not db_signals:
        st.warning("⚠️ No data available. Try clicking 'Backfill' to fetch historical messages.")
        return
    
    # Analyze messages for signal patterns
    analyzed_signals = []
    for msg in messages:
        analysis = analyze_signal_text(msg.get("message_text", ""))
        analyzed_signals.append({
            "timestamp": msg.get("message_date", ""),
            "text": msg.get("message_text", ""),
            "channel_id": msg.get("channel_id", ""),
            "signal_type": analysis["signal_type"],
            "instrument": analysis["instrument"],
            "confidence": analysis["confidence"]
        })
    
    # Create metrics
    if analyzed_signals or db_signals:
        # Calculate metrics
        total_signals = len(analyzed_signals) + len(db_signals)
        signal_types = [s["signal_type"] for s in analyzed_signals]
        avg_confidence = sum(s["confidence"] for s in analyzed_signals) / len(analyzed_signals) if analyzed_signals else 0.5
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Signals", total_signals)
        
        with col2:
            buy_signals = signal_types.count("BUY") + signal_types.count("CALL")
            st.metric("Buy/Call Signals", buy_signals)
        
        with col3:
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        with col4:
            channels_count = len(set(msg.get("channel_id", "") for msg in messages))
            st.metric("Active Channels", channels_count)
    
    st.markdown("---")
    
    # Display channel information
    if channel_info:
        st.subheader("📺 Monitored Channels")
        
        cols = st.columns(len(channel_info))
        for i, (channel_id, info) in enumerate(channel_info.items()):
            with cols[i % len(cols)]:
                st.metric(
                    label=info.get("title", "Unknown Channel"),
                    value=f"ID: {channel_id}",
                    delta=f"{info.get('type', 'Unknown')}"
                )
    
    # Filters and controls
    st.subheader("🔧 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_filter = st.date_input("From Date", datetime.now() - timedelta(days=days_back))
    
    with col2:
        channel_ids = list(channel_info.keys()) if channel_info else ["All"]
        channel_filter = st.multiselect("Channels", channel_ids, default=channel_ids[:1] if channel_ids != ["All"] else [])
    
    with col3:
        confidence_filter = st.slider("Min Confidence", 0.0, 1.0, 0.3, 0.1)
    
    with col4:
        signal_type_filter = st.selectbox("Signal Type", ["All", "BUY", "SELL", "CALL", "PUT"])
    
    # Filter signals based on criteria
    filtered_signals = analyzed_signals
    if channel_filter and "All" not in channel_filter:
        filtered_signals = [s for s in filtered_signals if s["channel_id"] in channel_filter]
    if confidence_filter:
        filtered_signals = [s for s in filtered_signals if s["confidence"] >= confidence_filter]
    if signal_type_filter != "All":
        filtered_signals = [s for s in filtered_signals if s["signal_type"] == signal_type_filter]
    
    # Create visualizations
    if filtered_signals:
        st.subheader("📊 Signal Analysis Charts")
        
        # Create DataFrame for plotting
        df = pd.DataFrame(filtered_signals)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Signal type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Signal Types")
            signal_counts = df['signal_type'].value_counts()
            fig = px.pie(values=signal_counts.values, names=signal_counts.index, 
                        title="Distribution of Signal Types")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Instruments")
            instrument_counts = df['instrument'].value_counts()
            fig = px.bar(x=instrument_counts.index, y=instrument_counts.values,
                        title="Signals by Instrument")
            st.plotly_chart(fig, use_container_width=True)
        
        # Timeline of signals
        st.subheader("📈 Signal Timeline")
        df_daily = df.groupby([df['timestamp'].dt.date, 'signal_type']).size().reset_index(name='count')
        fig = px.bar(df_daily, x='timestamp', y='count', color='signal_type',
                    title="Daily Signal Count by Type")
        st.plotly_chart(fig, use_container_width=True)
    
    # Display raw signals table
    st.subheader("📋 Recent Signals")
    
    if filtered_signals:
        # Convert to DataFrame and display
        df_display = pd.DataFrame(filtered_signals)
        df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Format the dataframe
        df_display = df_display[['timestamp', 'signal_type', 'instrument', 'confidence', 'text']].copy()
        df_display.columns = ['Time', 'Type', 'Instrument', 'Confidence', 'Message']
        df_display['Message'] = df_display['Message'].str[:100] + "..."  # Truncate long messages
        
        # Apply styling
        styled_df = df_display.style.applymap(
            lambda x: 'background-color: #d4edda; color: #155724' if x == 'BUY' or x == 'CALL' else
                     'background-color: #f8d7da; color: #721c24' if x == 'SELL' or x == 'PUT' else
                     '', subset=['Type']
        ).format({'Confidence': '{:.2f}'})
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    else:
        st.info("No signals match the current filters. Try adjusting the criteria.")
    
    # Raw message explorer
    with st.expander("🔍 Raw Message Explorer", expanded=False):
        st.subheader("Recent Telegram Messages")
        
        if messages:
            for i, msg in enumerate(messages[:10], 1):  # Show last 10 messages
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"Message {i}: {msg.get('message_text', '')[:200]}...")
                    with col2:
                        st.caption(f"📅 {msg.get('message_date', 'Unknown')}")
                        st.caption(f"📺 {msg.get('channel_id', 'Unknown')}")
                    st.markdown("---")
        else:
            st.info("No raw messages available.")
    
    # Footer info
    st.markdown("---")
    st.markdown(
        """
        **📝 Notes:**
        - Signals are automatically analyzed from Telegram messages
        - Confidence scores are based on message patterns and keywords
        - Historical data is fetched directly from Telegram API
        - Click 'Backfill' to get more historical messages
        """
    )


if __name__ == "__main__":
    show()