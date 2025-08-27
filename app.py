import streamlit as st
import datetime
import pandas as pd
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
import random
import urllib.parse # Used for encoding SVG for URL
import time # For simulated delays

# --- Load environment variables ---
load_dotenv()
# Note: BINANCE_API_KEY and BINANCE_SECRET_KEY are not used in this simplified demo logic,
# but included for completeness if you re-introduce actual trading logic.
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465)) # Default to 465 for SSL
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

# --- Initialize Twilio client (only if credentials are provided) ---
twilio_client = None
if TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE:
    try:
        twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        # st.sidebar.success("Twilio client initialized.") # For debugging, remove in production
    except Exception as e:
        st.sidebar.error(f"Error initializing Twilio: {e}")
else:
    st.sidebar.warning("Twilio environment variables not fully set. SMS 2FA will not function.")

# --- Database setup ---
# Using check_same_thread=False for Streamlit's multi-threading environment
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (email TEXT PRIMARY KEY, password_hash TEXT, phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reset_tokens
             (email TEXT, token TEXT, expiry DATETIME)''')
conn.commit()

# --- Custom CSS for Professional Green and Gold Theme & Responsiveness ---
def apply_custom_css():
    """Applies custom CSS for the green and gold theme with responsive adjustments."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
            
            body {
                font-family: 'Inter', sans-serif;
            }

            .stApp {
                background-color: #f0f2f6; /* Light gray background */
                color: #2c3e50; /* Dark gray text */
                font-family: 'Inter', sans-serif;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50;
            }
            .stHeader {
                background-color: transparent;
                border: none;
            }
            .stSidebar {
                background-color: #2c3e50; /* Darker sidebar for contrast */
                color: #ecf0f1;
                padding-top: 2rem;
            }
            .stSidebar .stButton>button {
                background-color: #f1c40f; /* Gold button */
                color: #2c3e50 !important; /* Ensure text is visible */
                font-weight: bold;
                border: none;
                border-radius: 8px;
                width: 100%;
                margin-bottom: 0.5rem;
            }
            .stSidebar .stButton>button:hover {
                background-color: #e6b100;
            }

            .stTextInput>div>div>input {
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
                color: #2c3e50; /* Ensure input text is visible */
                padding: 0.6rem 1rem;
            }
            .stTextInput>label {
                font-weight: 600;
                color: #2c3e50;
            }

            .stSubheader {
                color: #27ae60; /* Green subheaders */
                font-weight: bold;
                border-bottom: 1px solid #ecf0f1;
                padding-bottom: 0.5rem;
                margin-top: 2rem;
            }
            .metric-card > div {
                background-color: #ffffff;
                border-radius: 12px;
                border-left: 5px solid #27ae60; /* Green highlight */
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 1rem;
                margin-bottom: 1rem; /* Spacing between metric cards */
            }
            .stDataFrame {
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow-x: auto; /* Ensure tables are scrollable on small screens */
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .main-content {
                max-width: 1200px;
                margin: auto;
            }
            /* Landing page styling */
            .landing-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                padding: 4rem 2rem;
                background-color: #f0f2f6;
            }
            .landing-header {
                font-size: 3rem;
                font-weight: 800;
                color: #2c3e50;
                margin-bottom: 0.5rem;
            }
            .landing-subheader {
                font-size: 1.5rem;
                color: #7f8c8d;
                margin-top: -0.5rem; /* Adjust spacing */
                margin-bottom: 2rem;
            }
            .hero-image {
                margin: 2rem 0;
            }
            .stButton>button.cta-button {
                background-color: #f1c40f;
                color: #2c3e50 !important; /* Ensure text is visible */
                font-weight: bold;
                padding: 0.75rem 2rem;
                font-size: 1.2rem;
                border-radius: 50px;
                border: none;
                transition: transform 0.2s;
            }
            .stButton>button.cta-button:hover {
                transform: scale(1.05);
            }
            /* Styling for the login/signup container */
            .auth-card {
                max-width: 500px;
                margin: 3rem auto; /* Adjusted margin for better centering */
                padding: 2rem;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
                border-top: 5px solid #27ae60;
            }
            .switch-button-container {
                display: flex;
                justify-content: center;
                margin-top: 1rem;
            }
            .switch-button {
                background-color: transparent !important;
                border: none !important;
                color: #27ae60 !important; /* Green for link text */
                text-decoration: underline;
                cursor: pointer;
                font-size: 0.9em; /* Slightly smaller for switch text */
                padding: 0.25rem 0.5rem; /* Add padding for better clickability */
            }
            .switch-button:hover {
                color: #1a7a42 !important; /* Darker green on hover */
            }
            /* Dashboard layout */
            .dashboard-section {
                background-color: #ffffff;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            /* General button styling for all Streamlit buttons */
            .stButton>button {
                background-color: #f1c40f; /* Gold button */
                color: #2c3e50 !important; /* Ensure text is visible */
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                transition: all 0.3s ease;
                width: auto; /* Default to auto width unless specified */
            }
            .stButton>button:hover {
                background-color: #e6b100;
            }
            
            /* Responsive adjustments for smaller screens */
            @media (max-width: 768px) {
                .landing-header {
                    font-size: 2.5rem;
                }
                .landing-subheader {
                    font-size: 1.2rem;
                }
                .auth-card {
                    margin: 2rem auto;
                    padding: 1.5rem;
                }
                .stButton>button.cta-button {
                    font-size: 1rem;
                    padding: 0.6rem 1.5rem;
                }
                .stSidebar {
                    padding: 1rem;
                }
                .stSidebar .stButton>button {
                    padding: 0.4rem 0.8rem;
                    font-size: 0.9em;
                }
            }
            @media (max-width: 480px) {
                .landing-header {
                    font-size: 2rem;
                }
                .landing-subheader {
                    font-size: 1rem;
                }
                .auth-card {
                    margin: 1rem auto;
                    padding: 1rem;
                }
            }
        </style>
        """, unsafe_allow_html=True)

# --- Utility Functions for Auth ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_email(to_email, subject, body):
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
        st.error("Email server configuration missing. Cannot send email.")
        return False
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

def send_sms(to_phone, body):
    if not twilio_client:
        st.error("Twilio client not initialized. Cannot send SMS.")
        return False
    
    try:
        twilio_client.messages.create(body=body, from_=TWILIO_PHONE, to=to_phone)
        return True
    except Exception as e:
        st.error(f"Error sending SMS: {e}")
        return False

# --- Streamlit Session State Management ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "two_fa_passed" not in st.session_state:
    st.session_state.two_fa_passed = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False
if "show_auth_forms" not in st.session_state:
    st.session_state.show_auth_forms = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "two_fa_code" not in st.session_state: # Corrected variable name
    st.session_state.two_fa_code = None
if 'reset_token_sent' not in st.session_state:
    st.session_state.reset_token_sent = False
if 'show_forgot_password' not in st.session_state:
    st.session_state.show_forgot_password = False
if 'show_change_password' not in st.session_state:
    st.session_state.show_change_password = False
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'open_positions' not in st.session_state:
    st.session_state.open_positions = {}
if 'trades_executed' not in st.session_state:
    st.session_state.trades_executed = []
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

# --- Authentication Forms ---
def login_form():
    """Displays the login form."""
    with st.container():
        st.subheader("Login to Your Account")
        email = st.text_input("Email", placeholder="Enter your email", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.button("Login", key="login_button")
        with col2:
            st.markdown('<div class="switch-button-container">', unsafe_allow_html=True)
            st.button("Forgot Password?", key="forgot_password_button", on_click=lambda: st.session_state.update(show_forgot_password=True, login_error=""), help="Reset your password if you've forgotten it.", class_name="switch-button")
            st.markdown('</div>', unsafe_allow_html=True)


        st.markdown("---")
        st.markdown('<div class="switch-button-container">', unsafe_allow_html=True)
        st.button("Don't have an account? Sign Up", key="switch_to_signup", on_click=lambda: st.session_state.update(show_signup=True, login_error=""), help="Create a new account.", class_name="switch-button")
        st.markdown('</div>', unsafe_allow_html=True)

    if submit_button:
        if email:
            c.execute("SELECT password_hash, phone FROM users WHERE email = ?", (email,))
            result = c.fetchone()
            if result and hash_password(password) == result[0]:
                st.session_state.login_error = ""
                st.session_state.user_email = email
                phone = result[1]
                if phone and twilio_client: # Only attempt 2FA if phone is registered and Twilio is active
                    code = str(random.randint(100000, 999999))
                    st.session_state.two_fa_code = code
                    if send_sms(phone, f"Your MBU Trading Bot 2FA code is {code}"):
                        st.success("2FA code sent to your phone.")
                        st.session_state.authenticated = True # Temporarily authenticate for 2FA screen
                        st.session_state.two_fa_passed = False # Indicate 2FA is pending
                    else:
                        st.error("Failed to send 2FA code. Please check Twilio setup and phone number format (e.g., +1XXXXXXXXXX).")
                        st.session_state.authenticated = False # Revert authentication if 2FA fails to send
                else:
                    st.session_state.authenticated = True
                    st.session_state.two_fa_passed = True # No 2FA needed if no phone or Twilio inactive
                    st.success("Welcome!")
                st.rerun()
            else:
                st.session_state.login_error = "Invalid email or password."
        else:
            st.session_state.login_error = "Please enter an email address."


def signup_form():
    """Displays the sign-up form."""
    with st.container():
        st.subheader("Create a New Account")
        email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
        phone = st.text_input("Phone (e.g., +1234567890 for 2FA)", placeholder="Optional for 2FA", key="signup_phone")
        password = st.text_input("Password", type="password", placeholder="Create a password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm_password")
        
        signup_button = st.button("Sign Up", key="signup_button")

        st.markdown("---")
        st.markdown('<div class="switch-button-container">', unsafe_allow_html=True)
        st.button("Already have an account? Login", key="switch_to_login", on_click=lambda: st.session_state.update(show_signup=False, login_error="", signup_success=False), help="Go back to the login screen.", class_name="switch-button")
        st.markdown('</div>', unsafe_allow_html=True)

    if signup_button:
        if not email or not password or not confirm_password:
            st.session_state.login_error = "Email, Password, and Confirm Password are required."
        elif password != confirm_password:
            st.session_state.login_error = "Passwords do not match."
        else:
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            if c.fetchone():
                st.session_state.login_error = "Email already registered."
            else:
                hashed_pw = hash_password(password)
                try:
                    c.execute("INSERT INTO users (email, password_hash, phone) VALUES (?, ?, ?)", (email, hashed_pw, phone if phone else None))
                    conn.commit()
                    st.session_state.signup_success = True
                    st.session_state.show_signup = False # Switch back to login after success
                    st.session_state.login_error = "" # Clear any previous error
                    st.rerun()
                except Exception as e:
                    st.session_state.login_error = f"Account creation failed: {e}"

def two_fa_form():
    """Displays the 2FA form."""
    with st.container():
        st.subheader("Two-Factor Authentication")
        st.write(f"A 6-digit code has been sent to your registered phone for {st.session_state.user_email}.")
        two_fa_input = st.text_input("Enter 6-digit code", max_chars=6, key="2fa_input")

        submit_button = st.button("Verify 2FA", key="2fa_verify_button")

    if submit_button:
        if two_fa_input == st.session_state.two_fa_code:
            st.session_state.two_fa_passed = True
            st.session_state.login_error = ""
            st.success("2FA successful! Welcome.")
            st.rerun()
        else:
            st.session_state.login_error = "Incorrect 2FA code."

def forgot_password_form():
    """Displays the forgot password form."""
    with st.container():
        st.subheader("Forgot Password")
        email = st.text_input("Enter your registered email", key="forgot_email")

        if st.button("Send Reset Link/Token", key="send_reset_token_button"):
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            if c.fetchone():
                token = secrets.token_urlsafe(32) # More secure than hex
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                c.execute("INSERT OR REPLACE INTO reset_tokens (email, token, expiry) VALUES (?, ?, ?)", (email, token, expiry))
                conn.commit()
                
                reset_link = f"https://mbutradingbot.com/reset_password?token={token}&email={email}" # Placeholder URL
                email_body = f"Hello,\n\nYou requested a password reset for your MBU Trading Bot account.\n\nPlease click on the following link to reset your password: {reset_link}\n\nThis link is valid for 1 hour. If you did not request a password reset, please ignore this email.\n\nThank you,\nMBU Trading Bot Team"
                
                if send_email(email, "MBU Trading Bot Password Reset", email_body):
                    st.session_state.reset_token_sent = True
                    st.success("A password reset link has been sent to your email address.")
                    st.session_state.login_error = "" # Clear error
                else:
                    st.error("Failed to send reset email. Please check server settings.")
            else:
                st.session_state.login_error = "Email not found."
        
        if st.session_state.reset_token_sent:
            st.info("Check your email for the reset link. If you didn't receive it, check your spam folder.")
            
        st.markdown("---")
        st.button("Back to Login", key="back_to_login_from_forgot", on_click=lambda: st.session_state.update(show_forgot_password=False, login_error="", reset_token_sent=False))

# (Placeholder for actual reset password page logic - this would typically be a separate page or a more complex interaction)
def reset_password_page_placeholder():
    st.subheader("Reset Your Password")
    st.warning("This is a placeholder for the actual password reset page. In a full application, this would handle the token verification from the email link and might be a separate route.")
    st.info("For this demo, imagine you've clicked a link from your email and are now entering a new password.")

    # Simplified input for demo purposes
    new_password = st.text_input("New Password", type="password", key="new_reset_password")
    confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_reset_password")
    token = st.text_input("Reset Token (for demo, copied from email)", key="token_for_reset")
    email_for_reset = st.text_input("Email (for demo)", key="email_for_reset")

    if st.button("Set New Password"):
        if not new_password or not confirm_new_password or not token or not email_for_reset:
            st.error("All fields are required.")
        elif new_password != confirm_new_password:
            st.error("Passwords do not match.")
        else:
            c.execute("SELECT * FROM reset_tokens WHERE email = ? AND token = ? AND expiry > ?", (email_for_reset, token, datetime.datetime.now()))
            if c.fetchone():
                hashed_pw = hash_password(new_password)
                c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed_pw, email_for_reset))
                c.execute("DELETE FROM reset_tokens WHERE email = ?", (email_for_reset,))
                conn.commit()
                st.success("Password has been reset successfully. You can now log in.")
                st.session_state.show_forgot_password = False # Exit reset flow
                st.session_state.show_auth_forms = True # Go to login form
                st.session_state.show_signup = False # Ensure login form is shown
                st.rerun()
            else:
                st.error("Invalid or expired reset token.")


def change_password_form():
    """Allows authenticated users to change their password."""
    st.subheader("Change Password")
    email = st.session_state.user_email
    
    old_password = st.text_input("Old Password", type="password", key="old_password_change")
    new_password = st.text_input("New Password", type="password", key="new_password_change")
    confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password_change")

    if st.button("Update Password", key="update_password_button"):
        if not old_password or not new_password or not confirm_new_password:
            st.error("All fields are required.")
        elif new_password != confirm_new_password:
            st.error("New passwords do not match.")
        else:
            c.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
            result = c.fetchone()
            if result and hash_password(old_password) == result[0]:
                hashed_pw = hash_password(new_password)
                c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed_pw, email))
                conn.commit()
                st.success("Password changed successfully!")
                st.session_state.show_change_password = False # Go back to dashboard
                st.rerun()
            else:
                st.error("Incorrect old password.")

    st.button("Back to Dashboard", key="back_from_change_pw", on_click=lambda: st.session_state.update(show_change_password=False))


# --- Main Application Pages ---

def landing_page():
    """Displays the main landing page with marketing content."""
    st.markdown("<div class='landing-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='landing-header'>MBU TRADING BOT</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='landing-subheader'>Intelligent, Automated Trading for Your Success</h2>", unsafe_allow_html=True)
    
    # Using the new image provided by the user
    st.image("fotor_creation_2025-08-27.jpg", use_container_width=True)

    st.markdown("<p style='text-align: center; max-width: 600px; margin: auto; font-size: 1.1rem;'>Our intelligent bot analyzes market trends in real-time, executing trades with precision and speed to maximize your returns. We take the emotion out of trading so you can focus on your goals.</p>", unsafe_allow_html=True)
    
    # CTA button to initiate login/signup flow
    st.button("Get Started", key="start_button", type="primary", on_click=lambda: st.session_state.update(show_auth_forms=True), help="Click to login or sign up.")

    st.markdown("</div>", unsafe_allow_html=True)

# Placeholder for actual trading logic (e.g., Binance integration, strategy execution)
# These functions would interact with external APIs (like CCXT) if fully implemented.
def get_live_price(symbol):
    # Dummy function for now, to simulate price fluctuations
    # More realistic: fetch from a real exchange API (e.g., CCXT)
    prices = {
        "BTC/USDT": random.uniform(25000, 30000),
        "ETH/USDT": random.uniform(1500, 2000),
        "SOL/USDT": random.uniform(100, 150),
        "ADA/USDT": random.uniform(0.3, 0.5),
    }
    return prices.get(symbol, random.uniform(1, 10))


def get_trading_signal(strategy_name, current_price, history_prices):
    # Simplified dummy signal generation for demo
    if strategy_name == "Momentum":
        if len(history_prices) > 5:
            if current_price > history_prices.iloc[-1] * 1.005: # Price increased recently
                return "BUY"
            elif current_price < history_prices.iloc[-1] * 0.995: # Price decreased recently
                return "SELL"
    elif strategy_name == "Breakout":
        if len(history_prices) > 10:
            if current_price > history_prices.max() * 1.01: # Broke above recent high
                return "BUY"
            elif current_price < history_prices.min() * 0.99: # Broke below recent low
                return "SELL"
    elif strategy_name == "Mean Reversion":
        if len(history_prices) > 10:
            mean_price = history_prices.mean()
            if current_price < mean_price * 0.99: # Price below mean
                return "BUY"
            elif current_price > mean_price * 1.01: # Price above mean
                return "SELL"
    return "HOLD" # Default

def execute_trade_demo(symbol, side, quantity, price):
    """Simulates executing a trade and updates session state."""
    st.sidebar.info(f"DEMO: Executing trade: {side} {quantity} of {symbol} at {price:.2f}")
    trade_info = {
        "Date": datetime.datetime.now(),
        "Symbol": symbol,
        "Side": side,
        "Quantity": quantity,
        "Entry_Price": price,
        "P/L": 0, # P/L is calculated on close
        "Status": "OPEN"
    }
    st.session_state.open_positions[symbol] = trade_info
    st.success(f"DEMO: OPENED trade: {side} {quantity} {symbol.split('/')[0]} at ${price:.2f}")

def close_trade_demo(symbol, current_price):
    """Simulates closing a trade and updates session state."""
    position = st.session_state.open_positions.pop(symbol) # Remove from open positions
    entry_price = position['Entry_Price']
    side = position['Side']
    quantity = position['Quantity']
    
    # Calculate dummy profit/loss (simplified for demo, no real fees)
    if side == "BUY":
        profit_loss = (current_price - entry_price) * quantity
    else: # SELL
        profit_loss = (entry_price - current_price) * quantity
    
    st.session_state.total_profit += profit_loss
    
    trade_log = {
        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": symbol,
        "Side": side,
        "Quantity": quantity,
        "P/L": profit_loss,
        "Cumulative P/L": st.session_state.total_profit,
        "Reason": "Bot Close"
    }
    st.session_state.trades_executed.append(trade_log)
    st.success(f"DEMO: CLOSED trade: {side} {quantity} {symbol.split('/')[0]} at ${current_price:.2f} | P/L: ${profit_loss:.2f}")

def calculate_metrics_demo(trades):
    """Calculates demo trading metrics."""
    if not trades:
        return {"Sharpe Ratio": 0, "Max Drawdown": 0, "Win Ratio": 0}
    df = pd.DataFrame(trades)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Cumulative P/L'] = df['P/L'].cumsum()
    
    # Simplified metrics for demo
    returns = df['P/L']
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(365) if returns.std() != 0 else 0
    
    cumulative_returns = df['Cumulative P/L']
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() if not drawdown.empty else 0
    
    win_ratio = len(df[df['P/L'] > 0]) / len(df) if len(df) > 0 else 0
    
    return {"Sharpe Ratio": sharpe_ratio, "Max Drawdown": max_drawdown, "Win Ratio": win_ratio}

def run_trading_bot_logic(strategy_name, min_profit, max_loss, crypto_to_trade):
    """Simulates the core trading bot logic for demonstration."""
    for symbol in crypto_to_trade:
        current_price = get_live_price(symbol)
        if not current_price:
            continue

        # Keep a short history for signal generation
        if symbol not in st.session_state:
            st.session_state[f'{symbol}_history'] = pd.Series([])
        
        current_history = st.session_state[f'{symbol}_history']
        current_history = pd.concat([current_history, pd.Series([current_price])]).tail(20)
        st.session_state[f'{symbol}_history'] = current_history

        # Check for open positions first
        if symbol in st.session_state.open_positions:
            position = st.session_state.open_positions[symbol]
            entry_price = position['Entry_Price']
            
            # Simple profit/loss check
            if position['Side'] == "BUY":
                profit_pct = (current_price - entry_price) / entry_price * 100
                if profit_pct >= min_profit or profit_pct <= -max_loss: # Trigger close on profit or loss
                    close_trade_demo(symbol, current_price)
            else: # SELL position
                profit_pct = (entry_price - current_price) / entry_price * 100
                if profit_pct >= min_profit or profit_pct <= -max_loss: # Trigger close on profit or loss
                    close_trade_demo(symbol, current_price)
        else:
            # If no open position, look for new signals
            signal = get_trading_signal(strategy_name, current_price, current_history)
            
            if signal in ["BUY", "SELL"]:
                # Use a small, dummy quantity for demo purposes
                quantity = 0.01 # Example small quantity
                execute_trade_demo(symbol, signal, quantity, current_price)
    

def dashboard_main_content():
    """Content for the main dashboard page after login."""
    st.title(f"Welcome to your MBU Trading Bot Dashboard, {st.session_state.user_email.split('@')[0].capitalize()}!")
    st.write("Monitor your automated trading activity and manage bot settings here.")

    # Bot Controls in Sidebar
    st.sidebar.header("Bot Controls")
    
    # Bot Status Toggle
    if st.session_state.bot_running:
        if st.sidebar.button("🔴 Stop Bot", key="stop_bot"):
            st.session_state.bot_running = False
            st.sidebar.success("Bot has been stopped.")
            st.rerun() # Refresh the page to update UI
    else:
        if st.sidebar.button("🟢 Start Bot", key="start_bot"):
            st.session_state.bot_running = True
            st.session_state.start_time = datetime.datetime.now()
            # Reset trades and profit when starting (for fresh demo)
            st.session_state.open_positions = {}
            st.session_state.trades_executed = []
            st.session_state.total_profit = 0.0
            st.sidebar.success("Bot started! Monitoring markets...")
            st.rerun() # Refresh the page to update UI
    
    # Trading Parameters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Trading Parameters")
    
    # Ensure keys are unique across widgets
    strategy = st.sidebar.radio("Strategy", ["Momentum", "Breakout", "Mean Reversion"], index=0, key="strategy_select")
    timeframe = st.sidebar.radio("Run Duration", ["Continuous", "1 hour", "1 day"], index=0, key="timeframe_select")
    min_profit = st.sidebar.slider("Min Profit %", 0.1, 5.0, 0.5, 0.1, key="min_profit_slider")
    max_loss = st.sidebar.slider("Max Loss %", 0.1, 5.0, 1.0, 0.1, key="max_loss_slider")
    crypto_to_trade = st.sidebar.multiselect("Tradeable Assets", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"], default=["BTC/USDT", "ETH/USDT"], key="crypto_select")

    # --- Live Dashboard Section ---
    st.markdown("<div class='dashboard-section'>", unsafe_allow_html=True)
    st.subheader("Live Trading Dashboard")
    
    if st.session_state.bot_running:
        st.info("Bot is running! Live data will update every 10 seconds (demo rate).")
        placeholder = st.empty()
        
        end_time = None
        if timeframe == "1 hour":
            end_time = st.session_state.start_time + datetime.timedelta(hours=1)
        elif timeframe == "1 day":
            end_time = st.session_state.start_time + datetime.timedelta(days=1)
        
        # Loop for live updates (in a real app, this would be a background process)
        # Using a simple loop and rerun for demonstration.
        
        if 'last_run_time' not in st.session_state:
            st.session_state.last_run_time = datetime.datetime.now()
        
        # Check if 10 seconds have passed since last update or if it's the very first run
        if (datetime.datetime.now() - st.session_state.last_run_time).total_seconds() >= 10:
            run_trading_bot_logic(strategy, min_profit, max_loss, crypto_to_trade)
            st.session_state.last_run_time = datetime.datetime.now()
            st.rerun() # Trigger a rerun to update the display

        with placeholder.container():
            st.write(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            current_metrics = calculate_metrics_demo(st.session_state.trades_executed)
            
            colA, colB, colC, colD = st.columns(4)
            with colA:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Total P/L", f"${st.session_state.total_profit:.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
            with colB:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Sharpe Ratio", f"{current_metrics['Sharpe Ratio']:.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
            with colC:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Max Drawdown", f"{current_metrics['Max Drawdown']:.2%}")
                st.markdown("</div>", unsafe_allow_html=True)
            with colD:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Win Ratio", f"{current_metrics['Win Ratio']:.2%}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("Open Positions")
            if st.session_state.open_positions:
                st.dataframe(pd.DataFrame(list(st.session_state.open_positions.values())), use_container_width=True)
            else:
                st.info("No open positions.")
            
            st.markdown("---")
            st.subheader("Trades Executed")
            if st.session_state.trades_executed:
                st.dataframe(pd.DataFrame(st.session_state.trades_executed).iloc[::-1], use_container_width=True) # Reverse for most recent first
            else:
                st.info("No trades executed yet.")
        
        # Check if trading duration has ended
        if end_time and datetime.datetime.now() > end_time:
            st.session_state.bot_running = False
            st.warning(f"Trading period of {timeframe} ended. Bot stopped.")
            st.rerun()

    else:
        st.warning("Bot is currently stopped. Click 'Start Bot' in the sidebar to begin simulated trading.")
        st.markdown("---")
        st.subheader("Last Session Summary")
        if st.session_state.trades_executed:
            last_metrics = calculate_metrics_demo(st.session_state.trades_executed)
            st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total P/L", f"${st.session_state.total_profit:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            colA, colB, colC = st.columns(3)
            with colA:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Sharpe Ratio", f"{last_metrics['Sharpe Ratio']:.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
            with colB:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Max Drawdown", f"{last_metrics['Max Drawdown']:.2%}")
                st.markdown("</div>", unsafe_allow_html=True)
            with colC:
                st.markdown(f"<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Win Ratio", f"{last_metrics['Win Ratio']:.2%}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.subheader("Previous Trades")
            st.dataframe(pd.DataFrame(st.session_state.trades_executed).iloc[::-1], use_container_width=True)
        else:
            st.info("No previous simulated trading data available.")
    st.markdown("</div>", unsafe_allow_html=True) # End dashboard-section


# --- Main App Logic ---
st.set_page_config(
    page_title="MBU Trading Bot",
    layout="wide",
    initial_sidebar_state="expanded", # Set to expanded for easy access to bot controls
)
apply_custom_css()

# Use your uploaded image as the logo. Ensure 'fotor_creation_2025-08-27.jpg' is in the root directory.
st.logo("fotor_creation_2025-08-27.jpg", link="https://www.mbutradingbot.com")

# Main conditional rendering for different states of the application
if st.session_state.authenticated and st.session_state.two_fa_passed:
    if st.session_state.show_change_password:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        change_password_form()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        dashboard_main_content()
elif st.session_state.show_forgot_password:
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    forgot_password_form()
    st.markdown("</div>", unsafe_allow_html=True)
elif st.session_state.authenticated and not st.session_state.two_fa_passed: # Authenticated, but 2FA pending
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    two_fa_form()
    st.markdown("</div>", unsafe_allow_html=True)
else: # Not authenticated, show landing page or auth forms
    if not st.session_state.show_auth_forms:
        landing_page()
    else:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        if st.session_state.show_signup:
            signup_form()
        else:
            login_form()

        if st.session_state.login_error:
            st.error(st.session_state.login_error)
        if st.session_state.signup_success:
            st.success("Account created successfully! Please log in.")
            st.session_state.signup_success = False
        st.markdown("</div>", unsafe_allow_html=True)

# Add navigation to sidebar for authenticated users
if st.session_state.authenticated and st.session_state.two_fa_passed:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Account Settings")
    st.sidebar.write(f"Logged in as: **{st.session_state.user_email}**")
    if st.sidebar.button("Change Password"):
        st.session_state.show_change_password = True
        st.rerun()
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.two_fa_passed = False
        st.session_state.two_fa_code = None
        st.session_state.user_email = None
        st.session_state.login_error = ""
        st.session_state.show_auth_forms = False
        st.session_state.show_change_password = False
        st.session_state.bot_running = False # Stop bot on logout
        st.rerun()
