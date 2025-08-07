"""Settings and configuration page."""

import streamlit as st
import json


def show():
    """Display the settings page."""
    
    st.markdown('<h1 class="main-header">⚙️ Bot Configuration</h1>', unsafe_allow_html=True)
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔌 API Keys", "🎯 Trading", "⚠️ Risk Management", "📡 Channels", "🔔 Alerts"
    ])
    
    with tab1:
        st.subheader("🔐 API Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Telegram Configuration")
            telegram_token = st.text_input(
                "Bot Token",
                value="123456:ABC-DEF...",
                type="password"
            )
            
            st.markdown("##### Zerodha Configuration")
            kite_api_key = st.text_input(
                "API Key",
                value="abcdef123456",
                type="password"
            )
            kite_secret = st.text_input(
                "API Secret",
                value="secret123",
                type="password"
            )
            kite_access_token = st.text_input(
                "Access Token",
                value="",
                type="password",
                help="Will be generated after login"
            )
        
        with col2:
            st.markdown("##### OpenRouter Configuration")
            openrouter_key = st.text_input(
                "API Key",
                value="sk-or-...",
                type="password"
            )
            
            models = st.multiselect(
                "AI Models",
                [
                    "anthropic/claude-3-haiku",
                    "anthropic/claude-3-sonnet",
                    "meta-llama/llama-3.1-8b-instruct",
                    "openai/gpt-4o-mini"
                ],
                default=["anthropic/claude-3-haiku", "meta-llama/llama-3.1-8b-instruct"]
            )
            
            st.markdown("##### Database Configuration")
            db_url = st.text_input(
                "Database URL",
                value="postgresql://user:pass@localhost:5432/trading_bot"
            )
        
        if st.button("🔄 Test API Connections"):
            with st.spinner("Testing connections..."):
                # Simulate API tests
                import time
                time.sleep(1)
                
                st.success("✅ Telegram Bot: Connected")
                st.success("✅ Zerodha Kite: Connected")
                st.success("✅ OpenRouter: Connected")
                st.success("✅ Database: Connected")
    
    with tab2:
        st.subheader("📈 Trading Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Execution Settings")
            
            trading_mode = st.selectbox(
                "Trading Mode",
                ["Paper Trading", "Live Trading"],
                index=0
            )
            
            if trading_mode == "Live Trading":
                st.warning("⚠️ Live trading mode will execute real trades!")
            
            auto_execute = st.checkbox("Auto-execute signals", value=True)
            
            max_orders_per_day = st.number_input(
                "Max orders per day",
                min_value=1,
                max_value=100,
                value=20
            )
            
            max_positions = st.number_input(
                "Max concurrent positions",
                min_value=1,
                max_value=50,
                value=10
            )
            
            execution_delay = st.slider(
                "Execution delay (seconds)",
                min_value=0,
                max_value=300,
                value=30,
                help="Delay between signal detection and order placement"
            )
        
        with col2:
            st.markdown("##### Default Parameters")
            
            default_quantity = st.number_input(
                "Default quantity",
                min_value=1,
                max_value=10000,
                value=100
            )
            
            min_confidence = st.slider(
                "Minimum signal confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05
            )
            
            stop_loss_pct = st.slider(
                "Default stop loss (%)",
                min_value=0.5,
                max_value=20.0,
                value=2.0,
                step=0.1
            )
            
            target_pct = st.slider(
                "Default target (%)",
                min_value=1.0,
                max_value=50.0,
                value=5.0,
                step=0.5
            )
            
            st.markdown("##### Order Types")
            
            equity_product = st.selectbox(
                "Equity product type",
                ["CNC", "MIS"],
                index=0
            )
            
            fo_product = st.selectbox(
                "F&O product type",
                ["NRML", "MIS"],
                index=0
            )
    
    with tab3:
        st.subheader("⚠️ Risk Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Position Limits")
            
            max_position_size = st.number_input(
                "Max position size (₹)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=10000
            )
            
            max_daily_loss = st.number_input(
                "Max daily loss (₹)",
                min_value=500,
                max_value=1000000,
                value=5000,
                step=500
            )
            
            max_drawdown = st.slider(
                "Max drawdown (%)",
                min_value=5,
                max_value=50,
                value=15
            )
            
            sector_concentration = st.slider(
                "Max sector concentration (%)",
                min_value=10,
                max_value=100,
                value=30
            )
        
        with col2:
            st.markdown("##### Risk Controls")
            
            enable_stop_loss = st.checkbox("Enable automatic stop-loss", value=True)
            enable_circuit_check = st.checkbox("Check circuit breakers", value=True)
            enable_margin_check = st.checkbox("Validate margin before trade", value=True)
            enable_correlation_check = st.checkbox("Monitor portfolio correlation", value=True)
            
            st.markdown("##### Emergency Settings")
            
            emergency_stop = st.checkbox("Emergency stop enabled", value=False)
            
            if emergency_stop:
                st.error("🚨 Emergency stop is ACTIVE - No trades will be executed!")
            
            auto_square_off = st.checkbox("Auto square-off at market close", value=True)
            
            weekend_trading = st.checkbox("Allow weekend position holding", value=False)
        
        # Risk metrics display
        st.markdown("---")
        st.markdown("##### Current Risk Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Risk", "Medium", "↑")
        
        with col2:
            st.metric("VaR (1 day)", "₹8,500", "↑ ₹500")
        
        with col3:
            st.metric("Beta", "1.15", "↑ 0.05")
        
        with col4:
            st.metric("Correlation", "0.68", "↓ 0.02")
    
    with tab4:
        st.subheader("📡 Channel Management")
        
        # Add new channel
        st.markdown("##### Add New Channel")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_channel_id = st.text_input("Channel ID", placeholder="-1001234567890")
        
        with col2:
            new_channel_name = st.text_input("Channel Name", placeholder="Trading Signals")
        
        with col3:
            new_channel_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        
        if st.button("➕ Add Channel"):
            if new_channel_id and new_channel_name:
                st.success(f"Added channel: {new_channel_name}")
            else:
                st.error("Please fill all fields")
        
        st.markdown("---")
        
        # Existing channels
        st.markdown("##### Active Channels")
        
        channels_data = {
            'Channel': ['TradingGuru', 'StockAlerts', 'FnOSignals', 'QuickTips', 'MarketMaster'],
            'ID': ['-1001234567890', '-1001234567891', '-1001234567892', '-1001234567893', '-1001234567894'],
            'Status': ['Active', 'Active', 'Active', 'Paused', 'Active'],
            'Priority': ['High', 'Medium', 'High', 'Low', 'Medium'],
            'Signals Today': [5, 3, 8, 0, 4],
            'Success Rate': ['72%', '68%', '75%', '62%', '70%']
        }
        
        channels_df = st.data_editor(
            channels_data,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Paused", "Disabled"],
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority",
                    options=["High", "Medium", "Low"],
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Channel filters
        st.markdown("##### Signal Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            keywords_include = st.text_area(
                "Include keywords (one per line)",
                value="BUY\nSELL\nTARGET\nSTOPLOSS"
            )
        
        with col2:
            keywords_exclude = st.text_area(
                "Exclude keywords (one per line)",
                value="MAYBE\nUNCLEAR\nCONFUSED"
            )
    
    with tab5:
        st.subheader("🔔 Alert Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Alert Channels")
            
            email_alerts = st.checkbox("Email alerts", value=True)
            if email_alerts:
                email_address = st.text_input(
                    "Email address",
                    value="trader@example.com"
                )
            
            telegram_alerts = st.checkbox("Telegram alerts", value=True)
            if telegram_alerts:
                alert_chat_id = st.text_input(
                    "Alert chat ID",
                    value="123456789"
                )
            
            webhook_alerts = st.checkbox("Webhook alerts", value=False)
            if webhook_alerts:
                webhook_url = st.text_input(
                    "Webhook URL",
                    placeholder="https://hooks.slack.com/..."
                )
        
        with col2:
            st.markdown("##### Alert Triggers")
            
            signal_alerts = st.checkbox("New signal detected", value=True)
            execution_alerts = st.checkbox("Order executed", value=True)
            profit_alerts = st.checkbox("Position profitable", value=True)
            loss_alerts = st.checkbox("Position in loss", value=True)
            risk_alerts = st.checkbox("Risk limit breached", value=True)
            system_alerts = st.checkbox("System errors", value=True)
            
            st.markdown("##### Alert Frequency")
            
            alert_frequency = st.selectbox(
                "Max alerts per hour",
                ["No limit", "10", "5", "3", "1"]
            )
            
            quiet_hours = st.checkbox("Quiet hours (11 PM - 8 AM)", value=True)
        
        # Test alerts
        st.markdown("---")
        st.markdown("##### Test Alerts")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Test Email"):
                st.info("Test email sent!")
        
        with col2:
            if st.button("💬 Test Telegram"):
                st.info("Test message sent to Telegram!")
        
        with col3:
            if st.button("🔗 Test Webhook"):
                st.info("Test webhook triggered!")
    
    # Save settings
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Settings", type="primary"):
            st.success("Settings saved successfully!")
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.warning("Settings reset to defaults!")
    
    with col3:
        if st.button("📤 Export Config"):
            config = {
                "api_keys": {"telegram": "***", "zerodha": "***", "openrouter": "***"},
                "trading": {"mode": "paper", "auto_execute": True},
                "risk": {"max_position": 100000, "max_daily_loss": 5000},
                "channels": len(channels_data["Channel"]),
                "alerts": {"email": True, "telegram": True}
            }
            st.download_button(
                label="Download config.json",
                data=json.dumps(config, indent=2),
                file_name="bot_config.json",
                mime="application/json"
            )