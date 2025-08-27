# app.py - Version 4.0 with Real Money Trading, Enhanced Profitability, and Lifetime Access

import streamlit as st
import ccxt
import pandas as pd
import datetime
import time
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# Initialize Binance exchange
binance = ccxt.binance({
    "apiKey": BINANCE_API_KEY,
    "secret": BINANCE_SECRET_KEY,
    "enableRateLimit": True
})

# Disclaimer for real-money trading
DISCLAIMER_TEXT = """
**⚠️ Important Risk Disclaimer**

This trading bot enables real-money trading on Binance. Automated trading involves **significant financial risk**, and you may lose more than your initial investment. There is **no guarantee of profit**, despite our profitability enhancements, as markets are unpredictable.

By using this bot, you acknowledge full responsibility for your financial decisions and outcomes. Use with caution, start with small amounts, and consult a financial advisor. The creators are not liable for losses.

"""

# Tradeable assets (focus on high-liquidity, profitable options)
CRYPTO_TO_TRADE = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"]  # Using USDT pairs for stability

# Trading parameters for profitability
TRADE_FEE_RATE = 0.001  # 0.1% fee (Binance's typical maker/taker fee)
LEVERAGE = 1  # No leverage for safety; adjustable later
MIN_PROFIT_TARGET = 0.5  # Aim for at least 0.5% profit per trade
MAX_LOSS_LIMIT = 1.0  # Max 1% loss per trade

# Website design with enhanced UI
st.set_page_config(
    page_title="MBU Trading Bot",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp { background-color: #0E1117; color: white; }
.main-header { color: #FFD700; text-align: center; font-family: 'Arial', sans-serif; font-size: 3em; padding: 20px 0; }
.subheader { color: #32CD32; text-align: center; font-family: 'Arial', sans-serif; font-size: 1.5em; margin-bottom: 20px; }
.stButton>button { background-color: #FFD700; color: black; border: none; padding: 10px 20px; border-radius: 12px; font-size: 1.2em; font-weight: bold; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); width: 100%; }
.stButton>button:hover { background-color: #DAA520; color: white; transform: scale(1.05); }
.stButton>button:active { background-color: #B8860B; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }
.stRadio > div { background-color: #1a1a1a; padding: 10px; border-radius: 8px; border: 1px solid #32CD32; margin-bottom: 10px; }
.stRadio > label { font-weight: bold; color: #32CD32; }
.stRadio > div > label > div > div:first-child { color: #FFD700; }
.stRadio > div > label > div > div:first-child:hover { color: #32CD32; }
.stRadio > div > label > div > div > div > span:last-child { color: #FFD700; font-weight: bold; }
.stRadio [data-baseweb="radio"] > div { color: #32CD32; }
.stMarkdown p { color: #e0e0e0; text-align: justify; }
.disclaimer-box { background-color: #280808; padding: 20
