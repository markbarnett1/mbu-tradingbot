# app.py - Version 4.3 with Secure Login, Signup, Password Change, Forgot Password, and SMS 2FA

import streamlit as st
import ccxt
import pandas as pd
import datetime
import time
import numpy as np
import os
from dotenv import load_dotenv
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
import ssl
import uuid
import random

# Load environment variables
load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

# Initialize Twilio client
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (email TEXT PRIMARY KEY, password_hash TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reset_tokens 
             (email TEXT, token TEXT, expiry DATETIME)''')
conn.commit()

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
.disclaimer-box { background-color: #280808; padding: 20px; border-left: 5px solid #ff4d4d; margin-bottom: 20px; border-radius: 8px; font-size: 0.9em; }
.disclaimer-box h1 { color: #ff4d4d; margin-top: 0; }
.disclaimer-box p { color: #ffcccc; }
.login-box { background-color: #1a1a1a; padding: 20px; border-radius: 8px; border: 1px solid #32CD32; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if '2fa_code' not in st.session_state:
    st.session_state.2fa_code = None
if 'reset_token' not in st.session_state:
    st.session_state.reset_token = None
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False
if 'show_forgot' not in st.session_state:
    st.session_state.show_forgot = False
if 'show_change_pw' not in st.session_state:
    st.session_state.show_change_pw = False

# Functions for auth
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())

def send_sms(to_phone, body):
    twilio_client.messages.create(body=body, from_=TWILIO_PHONE, to=to_phone)

# Login, Signup, Forgot, Change PW Logic
if not st.session_state.authenticated:
    st.markdown("<h1 class='main-header'>MBU Trading Bot</h1>", unsafe_allow_html=True)
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    if st.session_state.show_signup:
        st.markdown("<h3 style='color: #FFD700;'>Sign Up</h3>", unsafe_allow_html=True)
        email = st.text_input("Email", "")
        phone = st.text_input("Phone (e.g., +1234567890)", "")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Sign Up"):
            if not email or not password or not confirm_password or not phone:
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                c.execute("SELECT * FROM users WHERE email = ?", (email,))
                if c.fetchone():
                    st.error("Email already exists.")
                else:
                    hashed_pw = hash_password(password)
                    c.execute("INSERT INTO users (email, password_hash, phone) VALUES (?, ?, ?)", (email, hashed_pw, phone))
                    conn.commit()
                    st.success("Account created! Please log in.")
                    st.session_state.show_signup = False
        if st.button("Back to Login"):
            st.session_state.show_signup = False
    elif st.session_state.show_forgot:
        st.markdown("<h3 style='color: #FFD700;'>Forgot Password</h3>", unsafe_allow_html=True)
        email = st.text_input("Email", "")
        token_input = st.text_input("Reset Token (if received)", "")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        if st.button("Reset Password"):
            if not token_input or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                c.execute("SELECT * FROM reset_tokens WHERE email = ? AND token = ? AND expiry > ?", (email, token_input, datetime.datetime.now()))
                if c.fetchone():
                    hashed_pw = hash_password(new_password)
                    c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed_pw, email))
                    c.execute("DELETE FROM reset_tokens WHERE email = ?", (email,))
                    conn.commit()
                    st.success("Password reset! Please log in.")
                    st.session_state.show_forgot = False
                else:
                    st.error("Invalid token or expired.")
        if st.button("Send Reset Token"):
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            if c.fetchone():
                token = secrets.token_hex(16)
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                c.execute("INSERT INTO reset_tokens (email, token, expiry) VALUES (?, ?, ?)", (email, token, expiry))
                conn.commit()
                body = f"Your password reset token is: {token}. Expires in 1 hour."
                send_email(email, "Password Reset Token", body)
                st.success("Reset token sent to your email.")
            else:
                st.error("Email not found.")
        if st.button("Back to Login"):
            st.session_state.show_forgot = False
    elif st.session_state.show_change_pw:
        st.markdown("<h3 style='color: #FFD700;'>Change Password</h3>", unsafe_allow_html=True)
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        if st.button("Change Password"):
            if not old_password or not new_password or not confirm_password:
                st.error("All fields are required.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                email = st.session_state.current_user
                c.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
                stored_hash = c.fetchone()[0]
                if hash_password(old_password) == stored_hash:
                    hashed_pw = hash_password(new_password)
                    c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed_pw, email))
                    conn.commit()
                    st.success("Password changed successfully.")
                    st.session_state.show_change_pw = False
                else:
                    st.error("Old password is incorrect.")
        if st.button("Back"):
            st.session_state.show_change_pw = False
    else:
        st.markdown("<h3 style='color: #FFD700;'>Login</h3>", unsafe_allow_html=True)
        email = st.text_input("Email", "")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT password_hash, phone FROM users WHERE email = ?", (email,))
            result = c.fetchone()
            if result and hash_password(password) == result[0]:
                st.session_state.current_user = email
                phone = result[1]
                if phone:
                    code = str(random.randint(100000, 999999))
                    st.session_state.2fa_code = code
                    send_sms(phone, f"Your 2FA code is {code}")
                    st.success("2FA code sent to your phone.")
                else:
                    st.session_state.authenticated = True
                    st.success("Welcome!")
            else:
                st.error("Invalid email or password.")
        if st.session_state.2fa_code:
            code_input = st.text_input("Enter 2FA Code", "")
            if st.button("Verify 2FA"):
                if code_input == st.session_state.2fa_code:
                    st.session_state.authenticated = True
                    st.session_state.2fa_code = None
                    st.success("Welcome!")
                else:
                    st.error("Invalid 2FA code.")
        if st.button("Sign Up"):
            st.session_state.show_signup = True
        if st.button("Forgot Password"):
            st.session_state.show_forgot = True
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='disclaimer-box'>{DISCLAIMER_TEXT}</div>", unsafe_allow_html=True)
    st.stop()

# Display after authentication
st.markdown("<div class='login-box'>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #FFD700;'>Trading Dashboard</h3>", unsafe_allow_html=True)
if st.button("Change Password"):
    st.session_state.show_change_pw = True
st.markdown("</div>", unsafe_allow_html=True)

# Trading UI and logic
col1, col2 = st.columns(2)

with col1:
    st.markdown("<h3 style='color: #FFD700;'>Choose a Trading Strategy</h3>", unsafe_allow_html=True)
    strategy = st.radio("Which strategy should the bot use?", ["Momentum", "Breakout", "Mean Reversion"], index=0)
    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Trading Timeframe</h3>", unsafe_allow_html=True)
    timeframe = st.radio("How long should the bot run?", ["1 hour", "1 day", "Trade until canceled"], index=1)
    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Profit Targets</h3>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        min_profit = st.number_input("Min Profit %", min_value=0.1, max_value=5.0, value=MIN_PROFIT_TARGET, step=0.1)
    with col4:
        max_loss = st.number_input("Max Loss %", min_value=0.1, max_value=5.0, value=MAX_LOSS_LIMIT, step=0.1)

with col2:
    st.markdown("<h3 style='color: #FFD700;'>Bot Controls</h3>", unsafe_allow_html=True)
    if st.session_state.bot_running:
        if st.button("🔴 Stop Bot"):
            st.session_state.bot_running = False
            st.success("Bot has been stopped.")
    else:
        if st.button("🟢 Start Bot"):
            st.session_state.bot_running = True
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.open_positions = {}
            st.session_state.trades_executed = []
            st.success(f"Bot started with {strategy} strategy for real money trading.")
            run_trading_bot()

if st.session_state.bot_running:
    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Live Dashboard</h3>", unsafe_allow_html=True)
    placeholder = st.empty()
    end_time = st.session_state.start_time + (datetime.timedelta(hours=1) if timeframe == "1 hour" else datetime.timedelta(days=1) if timeframe == "1 day" else None)
    while st.session_state.bot_running:
        if end_time and datetime.datetime.now() > end_time:
            st.session_state.bot_running = False
            st.warning("Trading period ended. Bot stopped.")
            break
        with placeholder.container():
            metrics = calculate_metrics(st.session_state.trades_executed)
            colA, colB, colC = st.columns(3)
            colA.metric("Total P/L", f"${st.session_state.total_profit:.2f}")
            colB.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
            colC.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
            st.dataframe(pd.DataFrame(st.session_state.trades_executed).iloc[::-1])
        time.sleep(10)

# Trading functions
def get_live_price(symbol):
    try:
        ticker = binance.fetch_ticker(symbol)
        return float(ticker['last'])
    except Exception as e:
        st.error(f"Error fetching price for {symbol}: {e}")
        return None

def get_trading_signal(strategy_name, current_price, history_prices):
    signal = "HOLD"
    if strategy_name == "Momentum":
        if len(history_prices) > 10:
            price_change = current_price - history_prices.iloc[-10]
            if price_change > current_price * 0.01 and np.random.random() > 0.5:
                signal = "BUY"
            elif price_change < -current_price * 0.01 and np.random.random() < 0.5:
                signal = "SELL"
    elif strategy_name == "Breakout":
        if len(history_prices) > 20:
            if current_price > history_prices.max() * 1.02 and np.random.random() > 0.6:
                signal = "BUY"
            elif current_price < history_prices.min() * 0.98 and np.random.random() < 0.4:
                signal = "SELL"
    elif strategy_name == "Mean Reversion":
        if len(history_prices) > 15:
            mean = history_prices.mean()
            if current_price < mean * 0.98 and np.random.random() < 0.45:
                signal = "BUY"
            elif current_price > mean * 1.02 and np.random.random() > 0.55:
                signal = "SELL"
    return signal

def calculate_metrics(trades):
    if not trades:
        return {"Total P/L": 0, "Sharpe Ratio": 0, "Max Drawdown": 0, "Win Ratio": 0}
    df = pd.DataFrame(trades)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Cumulative P/L'] = df['P/L'].cumsum()
    returns = df['P/L']
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(365) if returns.std() != 0 else 0
    cumulative_returns = df['Cumulative P/L']
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() if not drawdown.empty else 0
    win_ratio = len(df[df['P/L'] > 0]) / len(df) if len(df) > 0 else 0
    return {"Total P/L": df['Cumulative P/L'].iloc[-1], "Sharpe Ratio": sharpe_ratio, "Max Drawdown": max_drawdown, "Win Ratio": win_ratio}

def execute_trade(symbol, side, quantity, price):
    try:
        if side == "BUY":
            order = binance.create_market_buy_order(symbol, quantity)
        else:
            order = binance.create_market_sell_order(symbol, quantity)
        trade_info = {
            "Date": datetime.datetime.now(),
            "Symbol": symbol,
            "Side": side,
            "Quantity": quantity,
            "Entry_Price": price,
            "P/L": 0,
            "Status": "OPEN"
        }
        st.session_state.open_positions[symbol] = trade_info
        st.success(f"OPENED real trade: {side} {quantity} {symbol.split('/')[0]} at ${price:.2f}")
        return order
    except Exception as e:
        st.error(f"Trade failed: {e}")
        return None

def close_trade(symbol, current_price):
    position = st.session_state.open_positions[symbol]
    entry_price = position['Entry_Price']
    side = position['Side']
    quantity = position['Quantity']
    if side == "BUY":
        gross_profit = (current_price - entry_price) * quantity
        fee = (entry_price * quantity * TRADE_FEE_RATE) + (current_price * quantity * TRADE_FEE_RATE)
        profit = gross_profit - fee
    else:
        gross_profit = (entry_price - current_price) * quantity
        fee = (entry_price * quantity * TRADE_FEE_RATE) + (current_price * quantity * TRADE_FEE_RATE)
        profit = gross_profit - fee
    st.session_state.total_profit += profit
    trade_log = {
        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": symbol,
        "Side": side,
        "Quantity": quantity,
        "P/L": profit,
        "Cumulative P/L": st.session_state.total_profit,
        "Reason": "Bot Close"
    }
    st.session_state.trades_executed.append(trade_log)
    st.success(f"CLOSED real trade: {side} {quantity} {symbol.split('/')[0]} at ${current_price:.2f} | P/L: ${profit:.2f} (After fees)")
    del st.session_state.open_positions[symbol]

def run_trading_bot():
    while st.session_state.bot_running:
        for symbol in CRYPTO_TO_TRADE:
            if symbol not in st.session_state.open_positions:
                current_price = get_live_price(symbol)
                if current_price:
                    history_prices = pd.Series([get_live_price(symbol) for _ in range(20)] or [current_price] * 20)
                    signal = get_trading_signal(strategy, current_price, history_prices)
                    if signal in ["BUY", "SELL"]:
                        quantity = min(0.001, binance.fetch_balance()['USDT']['free'] / current_price / 10)
                        if quantity > 0:
                            execute_trade(symbol, signal, quantity, current_price)
            else:
                current_price = get_live_price(symbol)
                if current_price:
                    entry_price = st.session_state.open_positions[symbol]['Entry_Price']
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    loss_pct = (entry_price - current_price) / entry_price * 100
                    if profit_pct >= min_profit or loss_pct >= max_loss:
                        close_trade(symbol, current_price)
        time.sleep(60)
