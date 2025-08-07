"""Positions management page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def show():
    """Display the positions page."""
    
    st.markdown('<h1 class="main-header">📈 Positions Management</h1>', unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Open Positions", "7", "2")
    
    with col2:
        st.metric("Total Value", "₹1,85,420", "₹12,340")
    
    with col3:
        st.metric("Unrealized P&L", "₹8,450", "₹2,100")
    
    with col4:
        st.metric("Day Change", "+3.2%", "+0.8%")
    
    st.markdown("---")
    
    # Position filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        position_filter = st.selectbox(
            "Filter by Status",
            ["All Positions", "Open Positions", "Closed Today", "Profitable", "Loss Making"]
        )
    
    with col2:
        instrument_filter = st.selectbox(
            "Instrument Type",
            ["All", "Equity", "Futures", "Options"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Symbol", "P&L", "Value", "Percentage Change"]
        )
    
    # Current positions table
    st.subheader("💼 Current Positions")
    
    # Sample positions data
    positions_data = {
        'Symbol': ['RELIANCE', 'HDFC', 'TCS', 'INFY', 'ITC', 'SBIN', 'KOTAKBANK'],
        'Type': ['Equity', 'Equity', 'Equity', 'Equity', 'Equity', 'Equity', 'Equity'],
        'Quantity': [100, 50, 25, 75, 200, 150, 40],
        'Avg Price': [2851.2, 1654.5, 4123.8, 1567.9, 456.3, 789.1, 1876.5],
        'Current Price': [2865.4, 1642.3, 4156.7, 1589.2, 461.7, 792.6, 1888.9],
        'Market Value': [286540, 82115, 103918, 119190, 92340, 118890, 75556],
        'P&L': [1420, -610, 823, 1598, 1080, 525, 496],
        'Change %': [0.50, -0.74, 0.80, 1.36, 1.18, 0.44, 0.66],
        'Day Change': ['+0.8%', '-1.2%', '+1.1%', '+2.1%', '+0.9%', '+0.3%', '+1.3%']
    }
    
    positions_df = pd.DataFrame(positions_data)
    
    # Apply filters
    if instrument_filter != "All":
        positions_df = positions_df[positions_df['Type'] == instrument_filter]
    
    if position_filter == "Profitable":
        positions_df = positions_df[positions_df['P&L'] > 0]
    elif position_filter == "Loss Making":
        positions_df = positions_df[positions_df['P&L'] < 0]
    
    # Style the dataframe
    def style_pnl(val):
        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {color}; font-weight: bold'
    
    def style_change(val):
        color = 'green' if '+' in str(val) else 'red' if '-' in str(val) else 'black'
        return f'color: {color}'
    
    styled_positions = positions_df.style.applymap(style_pnl, subset=['P&L']) \
                                      .applymap(style_change, subset=['Day Change']) \
                                      .format({
                                          'Avg Price': '₹{:.1f}',
                                          'Current Price': '₹{:.1f}',
                                          'Market Value': '₹{:,.0f}',
                                          'P&L': '₹{:,.0f}',
                                          'Change %': '{:.2f}%'
                                      })
    
    st.dataframe(styled_positions, use_container_width=True)
    
    # Position actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Square Off All", type="primary"):
            st.warning("Square off all positions? This action cannot be undone!")
    
    with col2:
        if st.button("🛡️ Set Stop Loss"):
            st.info("Stop loss orders will be placed for all positions")
    
    with col3:
        if st.button("🎯 Book Profits"):
            st.info("Profit booking orders will be placed")
    
    with col4:
        if st.button("🔄 Refresh Positions"):
            st.rerun()
    
    # Charts section
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 P&L Distribution")
        
        # Create P&L pie chart
        profit_count = len(positions_df[positions_df['P&L'] > 0])
        loss_count = len(positions_df[positions_df['P&L'] < 0])
        
        pnl_dist = pd.DataFrame({
            'Status': ['Profitable', 'Loss Making'],
            'Count': [profit_count, loss_count]
        })
        
        fig_pnl = px.pie(pnl_dist, values='Count', names='Status', 
                        title="Positions by P&L Status",
                        color_discrete_map={'Profitable': 'green', 'Loss Making': 'red'})
        
        st.plotly_chart(fig_pnl, use_container_width=True)
    
    with col2:
        st.subheader("📊 Top Positions by Value")
        
        # Bar chart of positions by market value
        top_positions = positions_df.nlargest(5, 'Market Value')
        
        fig_bar = px.bar(top_positions, x='Symbol', y='Market Value',
                        title="Top 5 Positions by Market Value",
                        color='P&L',
                        color_continuous_scale=['red', 'white', 'green'])
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Position details
    st.markdown("---")
    st.subheader("🔍 Position Details")
    
    selected_symbol = st.selectbox("Select a position to view details:", 
                                  positions_df['Symbol'].tolist())
    
    if selected_symbol:
        position_detail = positions_df[positions_df['Symbol'] == selected_symbol].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"""
            **Symbol:** {position_detail['Symbol']}
            
            **Type:** {position_detail['Type']}
            
            **Quantity:** {position_detail['Quantity']}
            """)
        
        with col2:
            st.success(f"""
            **Avg Price:** ₹{position_detail['Avg Price']:.2f}
            
            **Current Price:** ₹{position_detail['Current Price']:.2f}
            
            **Market Value:** ₹{position_detail['Market Value']:,.0f}
            """)
        
        with col3:
            pnl_color = "🟢" if position_detail['P&L'] > 0 else "🔴"
            st.metric(
                f"{pnl_color} P&L",
                f"₹{position_detail['P&L']:,.0f}",
                f"{position_detail['Change %']:.2f}%"
            )
    
    # Risk metrics
    st.markdown("---")
    st.subheader("⚠️ Risk Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Beta", "1.15", "+0.05")
    
    with col2:
        st.metric("Concentration Risk", "18.2%", "-2.1%")
    
    with col3:
        st.metric("Sector Exposure", "Banking 35%", "IT 25%")
    
    with col4:
        st.metric("VaR (95%)", "₹12,450", "₹890")
    
    # Order management
    st.markdown("---")
    st.subheader("📋 Pending Orders")
    
    # Sample pending orders
    orders_data = {
        'Order ID': ['ORD001', 'ORD002', 'ORD003'],
        'Symbol': ['RELIANCE', 'TCS', 'HDFC'],
        'Type': ['SELL', 'BUY', 'SELL'],
        'Quantity': [50, 25, 30],
        'Price': [2900, 4200, 1620],
        'Status': ['Pending', 'Pending', 'Triggered'],
        'Time': ['10:45', '11:20', '11:35']
    }
    
    orders_df = pd.DataFrame(orders_data)
    st.dataframe(orders_df, use_container_width=True)
    
    # Export options
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💾 Export positions data in CSV, Excel, or PDF format")
    
    with col2:
        export_format = st.selectbox("Export as:", ["CSV", "Excel", "PDF"])
        if st.button("📤 Export"):
            st.success(f"Positions exported as {export_format}!")