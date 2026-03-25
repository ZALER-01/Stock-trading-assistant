import streamlit as st
import pandas as pd
@st.cache
def get_data(ticker, ema_short_val, ema_long_val):
    # Function to fetch data based on ticker
    pass

def main():
    st.title('Stock Trading Assistant')
    ticker = st.text_input('Enter ticker symbol')
    # Use the new EMA parameters
    ema_short_val = st.number_input('EMA Short Value', value=9)
    ema_long_val = st.number_input('EMA Long Value', value=21)
    data = get_data(ticker, ema_short_val, ema_long_val)
    st.write(data)

if __name__ == '__main__':
    main()