import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Real-Time Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

st.markdown('<h1 style="text-align: center; color: #1f77b4;">📈 Real-Time Stock Market Dashboard</h1>', unsafe_allow_html=True)

st.info("""
🎯 **Demo Version** - Simplified for Streamlit Cloud  
📦 **Full Stack**: Kafka + Spark + PostgreSQL + Docker  
💼 **Portfolio Project** | [GitHub Repository](https://github.com/YOUR_USERNAME/realtime-stock-pipeline)
""")

def generate_mock_data():
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    base_prices = {
        'AAPL': 273.76,
        'GOOGL': 313.56,
        'MSFT': 487.10,
        'AMZN': 232.07,
        'TSLA': 459.64
    }
    
    data = []
    now = datetime.now()
    
    for symbol in stocks:
        base = base_prices[symbol]
        for i in range(20):
            time = now - timedelta(minutes=i*5)
            price = base + random.uniform(-5, 5)
            data.append({
                'symbol': symbol,
                'price': round(price, 2),
                'timestamp': time,
                'high': round(price + random.uniform(0, 3), 2),
                'low': round(price - random.uniform(0, 3), 2)
            })
    
    return pd.DataFrame(data)

st.sidebar.header("⚙️ Configuration")
selected_stocks = st.sidebar.multiselect(
    "Select Stocks",
    ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
    default=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
)

df = generate_mock_data()

tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Charts", "📋 Data"])

with tab1:
    st.markdown("### 💰 Latest Stock Prices")
    
    cols = st.columns(len(selected_stocks))
    
    for idx, symbol in enumerate(selected_stocks):
        with cols[idx]:
            symbol_data = df[df['symbol'] == symbol].iloc[0]
            price = symbol_data['price']
            change = random.uniform(-2, 2)
            
            st.metric(
                label=symbol,
                value=f"${price:.2f}",
                delta=f"{change:.2f}"
            )
            st.caption(f"📈 High: ${symbol_data['high']:.2f}")
            st.caption(f"📉 Low: ${symbol_data['low']:.2f}")

with tab2:
    st.markdown("### 📈 Price History")
    
    fig = go.Figure()
    
    for symbol in selected_stocks:
        symbol_data = df[df['symbol'] == symbol].sort_values('timestamp')
        fig.add_trace(go.Scatter(
            x=symbol_data['timestamp'],
            y=symbol_data['price'],
            mode='lines+markers',
            name=symbol,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        height=500,
        xaxis_title="Time",
        yaxis_title="Price ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### 📋 Historical Data")
    
    display_df = df[df['symbol'].isin(selected_stocks)].copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"stock_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("### 🛠️ Technology Stack")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📡 Streaming", "Apache Kafka")
with col2:
    st.metric("⚡ Processing", "Apache Spark")
with col3:
    st.metric("💾 Storage", "PostgreSQL")
with col4:
    st.metric("🐳 Deployment", "Docker")

st.caption("Built with Python, Streamlit, Plotly | Portfolio Project")
st.caption("⭐ [View Full Code on GitHub](https://github.com/RahulSunny1209/realtime-stock-pipeline)")