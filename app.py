import streamlit as st
from brokers.ccxt_brokers import BinanceBroker
import tradier  # We'll add Tradier setup later
import os
from dotenv import load_dotenv
import paypalrestsdk
import datetime

# Load environment variables (secret keys)
load_dotenv()
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET_KEY")
TRADIER_KEY = os.getenv("TRADIER_API_KEY")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_EMAIL = "mbuniversal.money@hotmail.com"

# Set up PayPal (for $19.99 one-time payment)
paypalrestsdk.configure({
    "mode": "sandbox",  # Use "live" later for real money
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

# Free access for you and kids (check email)
FREE_USERS = ["markbarnett0123456789@gmail.com", "kid1@example.com", "kid2@example.com"]  # Add your kids' emails

# Simple trading function (Tradier for stocks, Binance for crypto)
def trade(asset_type, symbol, side, qty):
    if asset_type == "stocks":
        # Tradier setup (placeholder, we'll expand)
        account_id = "your_tradier_account_id"  # Get from Tradier dashboard
        tradier_api = tradier.Tradier(TRADIER_KEY)
        if side == "buy":
            tradier_api.place_order(account_id, symbol, qty, "buy", "market")
        else:
            tradier_api.place_order(account_id, symbol, qty, "sell", "market")
    else:  # crypto
        binance = BinanceBroker(BINANCE_KEY, BINANCE_SECRET)
        if side == "buy":
            binance.place_market_order(symbol, "buy", qty)
        else:
            binance.place_market_order(symbol, "sell", qty)

# Streamlit dashboard (easy buttons)
st.title("MBU Trading Bot")
st.write("One-time payment: $19.99 for lifetime access. Free for me and my kids!")

# Check if user is free
user_email = st.text_input("Enter your email for access")
if user_email in FREE_USERS or user_email == PAYPAL_EMAIL:
    st.success("Free lifetime access granted!")
    is_free = True
else:
    is_free = False

# Payment button
if not is_free:
    if st.button("Pay $19.99 for Lifetime Access"):
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": "19.99", "currency": "USD"},
                "description": "Lifetime MBU Trading Bot Access"
            }],
            "redirect_urls": {"return_url": "https://yourdomain.com/success", "cancel_url": "https://yourdomain.com/cancel"}
        })
        if payment.create():
            st.write("Please complete payment at: " + payment.links[1].href)
        else:
            st.error("Payment failed. Try again.")

# Trading section (if paid or free)
if is_free or st.session_state.get("paid", False):
    asset_type = st.selectbox("Stocks or Crypto?", ["stocks", "crypto"])
    symbol = st.text_input("Symbol (e.g., AAPL for stocks, BTC/USDT for crypto)", "AAPL")
    side = st.selectbox("Buy or Sell?", ["buy", "sell"])
    qty = st.number_input("Quantity", min_value=1, value=1)
    if st.button("Place Trade"):
        trade(asset_type, symbol, side, qty)
        st.success(f"Placed {side} order for {qty} {symbol}!")

# Note: Tradier library (tradier) isn't standard; we'll add a placeholder. Install via pip later.
