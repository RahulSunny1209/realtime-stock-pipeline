"""
Real-Time Stock Market Dashboard - Live Updates Enhanced
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import sys
sys.path.append('.')

from src.storage.database import PostgresStorage, RedisCache

# Page config
st.set_page_config(
    page_title="Real-Time Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .price-up { color: #00C805; font-weight: bold; }
    .price-down { color: #FF4136; font-weight: bold; }
    .subtitle { font-size: 1.5rem; color: #555; margin-top: 2rem; }
    .live-indicator {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def normalize_price_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure price column is float to avoid Decimal math issues"""
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
    return df

# Initialize storage in session state
def init_storage():
    """Initialize storage connections once per session"""
    if 'storage_initialized' not in st.session_state:
        try:
            postgres = PostgresStorage()
            redis_cache = RedisCache()
            
            postgres_ok = postgres.connect()
            redis_ok = redis_cache.connect()
            
            if postgres_ok and redis_ok:
                st.session_state.postgres = postgres
                st.session_state.redis = redis_cache
                st.session_state.storage_initialized = True
                st.session_state.storage_error = None
                return True
            else:
                st.session_state.storage_error = "Failed to connect to storage"
                return False
        except Exception as e:
            st.session_state.storage_error = str(e)
            return False
    return st.session_state.storage_initialized

storage_ok = init_storage()

# Dashboard Header
st.markdown('<h1 class="main-header"> Real-Time Stock Market Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Live Data from Finnhub API → Kafka → Spark → PostgreSQL")

if not storage_ok:
    st.error(f"❌ Storage Connection Error: {st.session_state.get('storage_error', 'Unknown error')}")
    st.info("💡 Make sure all services are running:")
    st.code("docker-compose ps")
    st.stop()

# Get storage
postgres = st.session_state.postgres
redis_cache = st.session_state.redis

# Sidebar with FASTER refresh
st.sidebar.header("⚙️ Configuration")
st.sidebar.markdown("🔴 <span class='live-indicator'>LIVE</span>", unsafe_allow_html=True)

auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 3, 30, 5)  # Faster: 3-30s, default 5s

selected_symbols = st.sidebar.multiselect(
    "Select Stocks",
    options=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
    default=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
)

if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

# Show data freshness
try:
    latest = postgres.get_latest_prices(limit=5)
    if latest:
        st.sidebar.success("✅ Data flowing (recent batches detected)")
    else:
        st.sidebar.warning("⚠️ No recent data")
except:
    st.sidebar.info("📊 Checking data flow...")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "📋 Data Table", "📊 Analytics"])

# TAB 1: OVERVIEW
with tab1:
    st.markdown('<p class="subtitle">Latest Stock Prices</p>', unsafe_allow_html=True)
    
    try:
        # Always fetch fresh from PostgreSQL for live data
        latest = postgres.get_latest_prices(limit=10)
        
        if latest and len(latest) > 0:
            df = pd.DataFrame(latest)
            df = normalize_price_column(df)
            
            cols = st.columns(len(selected_symbols))
            
            for idx, symbol in enumerate(selected_symbols):
                with cols[idx]:
                    symbol_data = df[df['symbol'] == symbol]
                    if not symbol_data.empty:
                        row = symbol_data.iloc[0]
                        price = row['price']
                        
                        st.metric(
                            label=f"{symbol}",
                            value=f"${price:.2f}",
                        )
                        volume = row.get('volume', 0)
                        if volume == 0:
                            st.caption("📊 Vol: N/A (API limitation)")
                        else:
                            st.caption(f"📊 Vol: {volume:,}")
                        st.caption(f"📈 High: ${row.get('day_high', 0):.2f}")
                        st.caption(f"📉 Low: ${row.get('day_low', 0):.2f}")
                        
                        # Show timestamp
                        event_time = pd.to_datetime(row['event_time'])
                        st.caption(f"🕐 {event_time.strftime('%H:%M:%S')}")
                    else:
                        st.info(f"No data for {symbol}")
        else:
            st.warning("⏳ Waiting for data...")
            st.info("**Start Spark processor if not running:**")
            st.code("python src/processing/spark_processor_with_storage.py")
    
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.caption(f"🕐 Dashboard Updated: {datetime.now().strftime('%H:%M:%S')}")

# TAB 2: CHARTS
with tab2:
    st.markdown('<p class="subtitle">Price History Charts</p>', unsafe_allow_html=True)
    
    time_range = st.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours"],
            index=0
        )

    hours_map = {
        "Last Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24
    }

    hours = hours_map.get(str(time_range), 1)
        
    try:
        fig = make_subplots(
            rows=len(selected_symbols), 
            cols=1,
            subplot_titles=[f"{symbol} Price History" for symbol in selected_symbols],
            vertical_spacing=0.1
        )
        
        has_data = False
        for idx, symbol in enumerate(selected_symbols, 1):
            history = postgres.get_symbol_history(symbol, hours=hours)
            
            if history and len(history) > 0:
                has_data = True
                df = pd.DataFrame(history)
                df = normalize_price_column(df)
                df['event_time'] = pd.to_datetime(df['event_time'])
                df = df.tail(20)
                df = df.sort_values('event_time')
                
                
                fig.add_trace(
                    go.Scatter(
                        x=df['event_time'],
                        y=df['price'],
                        mode='lines+markers',
                        name=symbol,
                        line=dict(width=2),
                        marker=dict(size=6)
                    ),
                    row=idx, col=1
                )
        
        if has_data:
            fig.update_layout(
                height=300 * len(selected_symbols),
                showlegend=True,
                hovermode='x unified'
            )
            fig.update_yaxes(
                rangemode="normal",
                fixedrange=False
            )
            fig.update_yaxes(autorange=True)
            
            fig.update_xaxes(title_text="Time", row=len(selected_symbols), col=1)
            fig.update_yaxes(title_text="Price ($)")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No data for selected time range")
    
    except Exception as e:
        st.error(f"Chart error: {e}")
    st.caption(f"Last chart refresh: {datetime.now().strftime('%H:%M:%S')}")


# TAB 3: DATA TABLE
with tab3:
    st.markdown('<p class="subtitle">Historical Data</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol_filter = st.selectbox("Filter by Symbol", ["All"] + selected_symbols)
    with col2:
        limit = st.slider("Number of Records", 10, 100, 20)
    
    try:
        if symbol_filter == "All":
            latest = postgres.get_latest_prices(limit=limit)
            df = pd.DataFrame(latest)
            df = normalize_price_column(df)
        else:
            history = postgres.get_symbol_history(symbol_filter, hours=24)
            df = pd.DataFrame(history)
            df = df.head(limit)
        
        if not df.empty:
            if 'event_time' in df.columns:
                df['event_time'] = pd.to_datetime(df['event_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Highlight latest row
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available")
    
    except Exception as e:
        st.error(f"Data error: {e}")

# TAB 4: ANALYTICS
with tab4:
    st.markdown('<p class="subtitle">Analytics & Statistics</p>', unsafe_allow_html=True)
    
    try:
        st.subheader("📊 Summary Statistics")
        
        stats_data = []
        for symbol in selected_symbols:
            history = postgres.get_symbol_history(symbol, hours=24)
            if history:
                df = pd.DataFrame(history)
                df = normalize_price_column(df)
                df['event_time'] = pd.to_datetime(df['event_time'])
                df = df.tail(20)
                stats_data.append({
                    'Symbol': symbol,
                    'Records': len(df),
                    'Avg Price': f"${df['price'].mean():.2f}",
                    'Max Price': f"${df['price'].max():.2f}",
                    'Min Price': f"${df['price'].min():.2f}",
                    'Std Dev': f"${df['price'].std():.2f}"
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        st.subheader("📈 Price Comparison")
        
        comparison_fig = go.Figure()
        for symbol in selected_symbols:
            history = postgres.get_symbol_history(symbol, hours=hours)
            if history:
                df = pd.DataFrame(history)
                df = normalize_price_column(df)
                df['event_time'] = pd.to_datetime(df['event_time'])
                df = df.sort_values('event_time').tail(20)
                
                comparison_fig.add_trace(go.Scatter(
                    x=df['event_time'],
                    y=df['price'],
                    mode='lines',
                    name=symbol,
                    line=dict(width=2)
                ))
        
        comparison_fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Price ($)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(comparison_fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Analytics error: {e}")

# Footer
st.markdown("---")
st.markdown("### 🔧 System Status")

# Check system health
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📡 Kafka", "Running")
with col2:
    st.metric("⚡ Spark", "Check logs")
with col3:
    st.metric("🗄️ PostgreSQL", "Connected")
with col4:
    # Count records
    try:
        st.metric("📊 Records", len(latest) if latest else 0)
    except:
        st.metric("📊 Records", "?")


# Auto-refresh at END
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
