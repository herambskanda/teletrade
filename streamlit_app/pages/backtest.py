"""Backtesting page for strategy analysis."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, date, timedelta


def show():
    """Display the backtesting page."""
    
    st.markdown('<h1 class="main-header">📋 Strategy Backtesting</h1>', unsafe_allow_html=True)
    
    # Backtest configuration
    st.subheader("⚙️ Backtest Configuration")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=365),
            max_value=date.today() - timedelta(days=1)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=date.today() - timedelta(days=1),
            max_value=date.today()
        )
    
    with col3:
        initial_capital = st.number_input(
            "Initial Capital (₹)",
            min_value=10000,
            max_value=10000000,
            value=100000,
            step=10000
        )
    
    with col4:
        commission = st.slider(
            "Commission (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01
        )
    
    # Strategy selection
    col1, col2 = st.columns(2)
    
    with col1:
        channels = st.multiselect(
            "Select Channels",
            ["TradingGuru", "StockAlerts", "FnOSignals", "QuickTips", "MarketMaster"],
            default=["TradingGuru", "StockAlerts"]
        )
    
    with col2:
        instruments = st.multiselect(
            "Instrument Types",
            ["Equity", "Futures", "Options"],
            default=["Equity"]
        )
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_confidence = st.slider("Min Signal Confidence", 0.0, 1.0, 0.7, 0.05)
            max_position_size = st.slider("Max Position Size (%)", 1, 50, 10)
            
        with col2:
            stop_loss = st.slider("Stop Loss (%)", 1, 20, 5)
            take_profit = st.slider("Take Profit (%)", 1, 50, 15)
            
        with col3:
            slippage = st.slider("Slippage (bps)", 0, 50, 5)
            delay = st.slider("Execution Delay (seconds)", 0, 300, 30)
    
    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary"):
        with st.spinner("Running backtest... This may take a few minutes."):
            # Simulate backtest execution
            import time
            time.sleep(2)
            
            st.success("Backtest completed successfully!")
            
            # Store results in session state for display
            st.session_state.backtest_completed = True
    
    # Display results if backtest has been run
    if getattr(st.session_state, 'backtest_completed', False):
        
        st.markdown("---")
        st.subheader("📊 Backtest Results")
        
        # Generate sample backtest data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Simulate portfolio performance
        returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
        portfolio_values = [initial_capital]
        
        for r in returns[1:]:
            new_value = portfolio_values[-1] * (1 + r)
            portfolio_values.append(new_value)
        
        results_df = pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values[:len(dates)]
        })
        
        # Performance metrics
        final_value = portfolio_values[-1]
        total_return = (final_value - initial_capital) / initial_capital
        trading_days = len(dates)
        annual_return = (final_value / initial_capital) ** (252 / trading_days) - 1
        
        # Calculate additional metrics
        daily_returns = results_df['Portfolio_Value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Max drawdown calculation
        peak = results_df['Portfolio_Value'].expanding(min_periods=1).max()
        drawdown = (results_df['Portfolio_Value'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Return",
                f"{total_return:.1%}",
                f"₹{final_value - initial_capital:,.0f}"
            )
        
        with col2:
            st.metric(
                "Annual Return",
                f"{annual_return:.1%}",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                "Sharpe Ratio",
                f"{sharpe_ratio:.2f}",
                delta_color="normal"
            )
        
        with col4:
            st.metric(
                "Max Drawdown",
                f"{max_drawdown:.1%}",
                delta_color="inverse"
            )
        
        # Portfolio performance chart
        st.subheader("📈 Portfolio Performance")
        
        fig_performance = go.Figure()
        
        fig_performance.add_trace(go.Scatter(
            x=results_df['Date'],
            y=results_df['Portfolio_Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue', width=2)
        ))
        
        # Add benchmark (assuming market return of 12% annually)
        benchmark_values = [initial_capital * (1.12 ** ((i) / 252)) for i in range(len(dates))]
        
        fig_performance.add_trace(go.Scatter(
            x=results_df['Date'],
            y=benchmark_values,
            mode='lines',
            name='Benchmark (12% p.a.)',
            line=dict(color='orange', width=1, dash='dash')
        ))
        
        fig_performance.update_layout(
            title="Portfolio vs Benchmark Performance",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_performance, use_container_width=True)
        
        # Trade analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Trade Analysis")
            
            # Generate sample trade data
            num_trades = np.random.randint(50, 200)
            trade_pnls = np.random.normal(500, 1000, num_trades)
            winning_trades = len(trade_pnls[trade_pnls > 0])
            losing_trades = len(trade_pnls[trade_pnls <= 0])
            
            trade_metrics = {
                "Total Trades": [num_trades],
                "Winning Trades": [winning_trades],
                "Losing Trades": [losing_trades],
                "Win Rate": [f"{winning_trades/num_trades*100:.1f}%"],
                "Avg Win": [f"₹{trade_pnls[trade_pnls > 0].mean():.0f}"],
                "Avg Loss": [f"₹{trade_pnls[trade_pnls <= 0].mean():.0f}"],
                "Profit Factor": [f"{abs(trade_pnls[trade_pnls > 0].sum() / trade_pnls[trade_pnls <= 0].sum()):.2f}"],
                "Best Trade": [f"₹{trade_pnls.max():.0f}"],
                "Worst Trade": [f"₹{trade_pnls.min():.0f}"]
            }
            
            trade_df = pd.DataFrame(trade_metrics).T
            trade_df.columns = ["Value"]
            
            st.dataframe(trade_df, use_container_width=True)
        
        with col2:
            st.subheader("📈 Monthly Returns")
            
            # Generate monthly returns heatmap data
            monthly_returns = []
            months = []
            years = []
            
            for year in range(start_date.year, end_date.year + 1):
                for month in range(1, 13):
                    if (year == start_date.year and month >= start_date.month) or \
                       (year == end_date.year and month <= end_date.month) or \
                       (start_date.year < year < end_date.year):
                        monthly_returns.append(np.random.normal(0.01, 0.05))
                        months.append(month)
                        years.append(year)
            
            # Create monthly returns chart
            fig_monthly = px.bar(
                x=[f"{y}-{m:02d}" for y, m in zip(years, months)],
                y=monthly_returns,
                title="Monthly Returns",
                color=monthly_returns,
                color_continuous_scale=['red', 'white', 'green']
            )
            
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Drawdown analysis
        st.subheader("📉 Drawdown Analysis")
        
        fig_drawdown = go.Figure()
        
        fig_drawdown.add_trace(go.Scatter(
            x=results_df['Date'],
            y=drawdown * 100,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='red'),
            fillcolor='rgba(255, 0, 0, 0.3)'
        ))
        
        fig_drawdown.update_layout(
            title="Portfolio Drawdown Over Time",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_drawdown, use_container_width=True)
        
        # Signal performance by channel
        st.subheader("🎯 Channel Performance")
        
        channel_performance = {
            'Channel': channels if channels else ['TradingGuru', 'StockAlerts'],
            'Signals': [45, 38] if len(channels) <= 2 else [45, 38, 52, 23, 67][:len(channels)],
            'Win Rate': [72.5, 65.8] if len(channels) <= 2 else [72.5, 65.8, 78.2, 58.3, 69.1][:len(channels)],
            'Avg P&L': [1250, 890] if len(channels) <= 2 else [1250, 890, 1680, 450, 1120][:len(channels)],
            'Total P&L': [56250, 33820] if len(channels) <= 2 else [56250, 33820, 87360, 10350, 74800][:len(channels)]
        }
        
        channel_df = pd.DataFrame(channel_performance)
        
        # Channel performance chart
        fig_channel = px.bar(
            channel_df,
            x='Channel',
            y='Total P&L',
            color='Win Rate',
            title="Channel Performance - Total P&L vs Win Rate",
            color_continuous_scale=['red', 'yellow', 'green']
        )
        
        st.plotly_chart(fig_channel, use_container_width=True)
        
        # Display channel table
        st.dataframe(channel_df, use_container_width=True)
        
        # Risk metrics
        st.subheader("⚠️ Risk Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Value at Risk (95%)", f"₹{initial_capital * 0.05:,.0f}")
        
        with col2:
            st.metric("Beta", f"{np.random.uniform(0.8, 1.3):.2f}")
        
        with col3:
            st.metric("Calmar Ratio", f"{annual_return / abs(max_drawdown):.2f}")
        
        with col4:
            st.metric("Sortino Ratio", f"{sharpe_ratio * 1.2:.2f}")
        
        # Export results
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("💾 Export detailed backtest results and analysis")
        
        with col2:
            export_format = st.selectbox("Format:", ["PDF", "Excel", "CSV"])
            if st.button("📤 Export Report"):
                st.success(f"Backtest report exported as {export_format}!")
    
    # Saved backtests
    st.markdown("---")
    st.subheader("💾 Saved Backtests")
    
    saved_backtests = {
        'Name': ['Conservative Strategy', 'Aggressive Options', 'Multi-Channel Equity', 'High Frequency'],
        'Date': ['2024-01-15', '2024-01-10', '2024-01-05', '2023-12-28'],
        'Return': ['18.5%', '45.2%', '22.1%', '12.8%'],
        'Sharpe': [1.24, 1.67, 1.15, 0.89],
        'Max DD': ['-8.2%', '-15.6%', '-12.4%', '-6.7%']
    }
    
    saved_df = pd.DataFrame(saved_backtests)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.dataframe(saved_df, use_container_width=True)
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("📊 Load"):
            st.info("Loading saved backtest...")
        if st.button("🗑️ Delete"):
            st.error("Backtest deleted!")
    
    # Tips and help
    st.markdown("---")
    
    with st.expander("💡 Backtesting Tips"):
        st.markdown("""
        **Best Practices for Backtesting:**
        
        1. **Use sufficient historical data** - At least 1 year of data for reliable results
        2. **Include transaction costs** - Don't forget brokerage, taxes, and slippage
        3. **Account for execution delays** - Real-world execution isn't instantaneous
        4. **Be realistic about position sizing** - Consider market liquidity constraints
        5. **Test multiple scenarios** - Try different market conditions and time periods
        6. **Validate with out-of-sample data** - Reserve some data for final validation
        7. **Consider survivorship bias** - Include delisted stocks in your analysis
        8. **Monitor for overfitting** - Avoid over-optimizing based on historical data
        
        **Key Metrics to Watch:**
        - **Sharpe Ratio**: Risk-adjusted returns (>1.0 is good)
        - **Maximum Drawdown**: Worst peak-to-trough decline (<20% preferred)
        - **Win Rate**: Percentage of profitable trades
        - **Profit Factor**: Gross profit / Gross loss (>1.5 is good)
        """)