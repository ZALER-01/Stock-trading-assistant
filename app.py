import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="AlgoTrader Pro", layout="wide", page_icon="📈")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_index=True)

st.title("📈 AlgoTrader Pro: EMA Crossover Strategy")
st.sidebar.header("🕹️ Strategy Controls")

# --- USER INPUTS ---
ticker = st.sidebar.text_input("Stock Ticker (e.g., RELIANCE.NS, TSLA, BTC-USD)", "RELIANCE.NS")
start_capital = st.sidebar.number_input("Starting Capital ($)", value=10000)
rr_ratio = st.sidebar.slider("Risk/Reward Ratio (Target)", 1.0, 5.0, 2.0)
ema_short_val = st.sidebar.number_input("Short EMA Period", value=50)
ema_long_val = st.sidebar.number_input("Long EMA Period", value=200)

@st.cache_data
def get_data(symbol):
    try:
        data = yf.download(symbol, period="5y", interval="1d", progress=False)
        if data.empty: return None
        # Indicators
        data['EMA_S'] = ta.ema(data['Close'], length=ema_short_val)
        data['EMA_L'] = ta.ema(data['Close'], length=ema_long_val)
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)
        return data.dropna()
    except:
        return None

def run_backtest(df):
    balance = start_capital
    position = 0 
    entry_price = 0
    stop_loss = 0
    take_profit = 0
    history = []

    for i in range(1, len(df)):
        price = float(df['Close'].iloc[i])
        atr = float(df['ATR'].iloc[i])
        
        if position == 0:
            if (df['EMA_S'].iloc[i-1] <= df['EMA_L'].iloc[i-1] and 
                df['EMA_S'].iloc[i] > df['EMA_L'].iloc[i] and 
                df['RSI'].iloc[i] < 70):
                position = 1
                entry_price = price
                stop_loss = entry_price - (2 * atr)
                take_profit = entry_price + ((entry_price - stop_loss) * rr_ratio)
                history.append({'Date': df.index[i], 'Event': 'BUY', 'Price': price, 'Balance': balance})
        
        elif position == 1:
            if price >= take_profit:
                balance *= (1 + (take_profit - entry_price) / entry_price)
                position = 0
                history.append({'Date': df.index[i], 'Event': 'TP HIT', 'Price': take_profit, 'Balance': balance})
            elif price <= stop_loss:
                balance *= (1 - (entry_price - stop_loss) / entry_price)
                position = 0
                history.append({'Date': df.index[i], 'Event': 'SL HIT', 'Price': stop_loss, 'Balance': balance})
    
    return pd.DataFrame(history), balance

# --- MAIN ENGINE ---
df = get_data(ticker)

if df is not None:
    # LIVE SIGNAL HEADER
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Price", f"{latest['Close']:.2f}")
    c2.metric("RSI (14)", f"{latest['RSI']:.1f}")
    
    signal = "NEUTRAL"
    if prev['EMA_S'] <= prev['EMA_L'] and latest['EMA_S'] > latest['EMA_L']:
        signal = "BUY"
        st.success(f"🔥 Signal: {signal} (Golden Cross) | SL: {latest['Close']-(2*latest['ATR']):.2f}")
    elif prev['EMA_S'] >= prev['EMA_L'] and latest['EMA_S'] < latest['EMA_L']:
        signal = "SELL"
        st.error(f"💀 Signal: {signal} (Death Cross)")
    else:
        st.info("No fresh crossover signal today.")

    st.divider()

    # BACKTEST RESULTS
    history_df, final_bal = run_backtest(df)
    
    if not history_df.empty:
        roi = ((final_bal - start_capital) / start_capital) * 100
        st.header(f"Strategy Performance: {roi:.2f}% ROI")
        
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(history_df['Date'], history_df['Balance'], color="#00FFAA")
        ax.fill_between(history_df['Date'], history_df['Balance'], start_capital, alpha=0.1, color="#00FFAA")
        st.pyplot(fig)
        
        st.subheader("Historical Trade Log")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.warning("No trades found for these parameters in the 5-year window.")
else:
    st.error("Ticker not found. Please check the symbol (e.g., AAPL, TSLA, RELIANCE.NS).")
