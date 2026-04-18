import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from twelvedata import TDClient
from smc_logic import find_swings, get_smc_signals
import time

# --- Setup ---
st.set_page_config(page_title="SMC Pro Dashboard", layout="wide")

# REPLACE THIS WITH YOUR ACTUAL TWELVEDATA API KEY
API_KEY = "c890e28c661647c6bbbeec32c0d805e7" 
td = TDClient(apikey=API_KEY)

st.title("🎯 SMC Real-Time Strategy Hub")

# --- Sidebar Controls ---
st.sidebar.header("Trading Style")

# Re-adding Scalp/Swing Options
trade_style = st.sidebar.radio("Select Style", ["Scalp (Fast)", "Swing (Trend)"])

if trade_style == "Scalp (Fast)":
    tf_choice = st.sidebar.selectbox("Scalp Timeframe", ["5min", "15min"])
    output_size = 100 # Smaller sample for speed
else:
    tf_choice = st.sidebar.selectbox("Swing Timeframe", ["1h", "4h", "1week"])
    output_size = 300 # Larger sample to see major structure

st.sidebar.divider()
symbol = st.sidebar.text_input("Symbol (e.g., EUR/USD, BTC/USD)", "GBP/USD")
balance = st.sidebar.number_input("Account Balance ($)", value=10000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.1, 5.0, 1.0)
auto_refresh = st.sidebar.toggle("Real-Time Mode (15s)", value=True)

# --- Analysis Function ---
def run_live_analysis():
    try:
        # Fetching data
        ts = td.time_series(
            symbol=symbol,
            interval=tf_choice,
            outputsize=output_size,
            timezone="Africa/Lagos"
        )
        df = ts.as_pandas()
        
        # Format for logic
        df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'})
        df = df.sort_index(ascending=True)

        if not df.empty:
            # Show Live Price in Sidebar
            current_price = df['Close'].iloc[-1]
            st.sidebar.metric("Live Price", f"{current_price:.5f}")
            
            df = find_swings(df)
            signal, entry, sl, tp = get_smc_signals(df)
            
            # --- Results Display ---
            st.subheader(f"{trade_style} Analysis: {symbol} ({tf_choice})")
            
            if "BOS" in signal:
                st.success(f"🔥 {signal}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Entry", f"{entry:.5f}")
                m2.metric("Stop Loss", f"{sl:.5f}")
                m3.metric("Take Profit", f"{tp:.5f}")
                
                # Lot Size Calc
                risk_cash = balance * (risk_pct / 100)
                pips = abs(entry - sl)
                lots = risk_cash / pips if pips != 0 else 0
                st.info(f"💰 **Risk Guide:** Risking ${risk_cash:.2f}. Recommended Position: {lots:.2f}")
            else:
                st.warning(f"⚖️ {signal}")
                st.write("Waiting for price to break the orange dashed lines for a signal.")

            # --- Candlestick Chart ---
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
            )])

            # Draw Structure Lines
            last_h = float(df[df['high_swing'] == 1]['High'].iloc[-1])
            last_l = float(df[df['low_swing'] == 1]['Low'].iloc[-1])
            fig.add_hline(y=last_h, line_dash="dash", line_color="#ffa726", annotation_text="BOS High")
            fig.add_hline(y=last_l, line_dash="dash", line_color="#ffa726", annotation_text="BOS Low")

            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Waiting for valid data... (Check API Key and Symbol format)")

# Run Logic
if st.sidebar.button("Manual Analyze") or auto_refresh:
    run_live_analysis()

# Auto-refresh loop
if auto_refresh:
    time.sleep(15)
    st.rerun()