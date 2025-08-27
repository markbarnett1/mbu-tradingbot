import streamlit as st
import datetime
import pandas as pd
import numpy as np

# A dictionary to simulate user data for authentication
# In a real application, this would be a secure database
USER_DATA = {
    "mark@mbu.com": {
        "password": "mbu",
        "2fa_enabled": True,
        "2fa_code": "123456" # This would be dynamically generated in a real app
    }
}

# --- Page Configuration ---
st.set_page_config(
    page_title="MBU Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- State Management and UI Functions ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "two_fa_passed" not in st.session_state:
    st.session_state.two_fa_passed = False
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

def login_form():
    """Displays the login form."""
    with st.form(key="login_form"):
        st.subheader("Login to MBU Trading Bot")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col1, col2 = st.columns([1, 10])
        with col1:
            submit_button = st.form_submit_button(label="Login")

    if submit_button:
        if email in USER_DATA and USER_DATA[email]["password"] == password:
            st.session_state.login_error = ""
            st.session_state.authenticated = True
            # Store user data for 2FA check
            st.session_state.user_email = email
            st.rerun()
        else:
            st.session_state.login_error = "Invalid email or password."

def two_fa_form():
    """Displays the 2FA form."""
    with st.form(key="2fa_form"):
        st.subheader("Two-Factor Authentication")
        st.write(f"Please enter the 6-digit code sent to {st.session_state.user_email}")
        two_fa_input = st.text_input("6-digit code", max_chars=6)

        col1, col2 = st.columns([1, 10])
        with col1:
            submit_button = st.form_submit_button(label="Verify")

    if submit_button:
        user_email = st.session_state.user_email
        correct_code = USER_DATA[user_email]["2fa_code"]
        if two_fa_input == correct_code:
            st.session_state.two_fa_passed = True
            st.session_state.login_error = ""
            st.rerun()
        else:
            st.session_state.login_error = "Incorrect 2FA code."

def main_dashboard():
    """Displays the main trading dashboard after successful login."""
    st.title("MBU Trading Bot Dashboard")
    st.write("Welcome, Mark! Here you can monitor your trading activity.")

    st.sidebar.header("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.two_fa_passed = False
        st.session_state.two_fa_code = None  # Corrected variable name
        st.session_state.user_email = None
        st.rerun()

    st.subheader("Account Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Balance", "$10,500", "500")
    col2.metric("Total Trades", "2,100", "15")
    col3.metric("Win Rate", "75%", "2%")

    st.subheader("Performance Chart")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=["BTC", "ETH", "AAPL"]
    ).cumsum()
    st.line_chart(chart_data)

    st.subheader("Recent Trades")
    trade_data = pd.DataFrame({
        "Date": [datetime.date(2025, 8, 26), datetime.date(2025, 8, 25), datetime.date(2025, 8, 24)],
        "Symbol": ["BTC", "ETH", "AAPL"],
        "Type": ["BUY", "SELL", "BUY"],
        "Quantity": [0.5, 2.0, 10],
        "Price": [26000, 1800, 150],
        "Status": ["Completed", "Completed", "Completed"]
    })
    st.dataframe(trade_data, use_container_width=True)

# --- Main App Logic ---
st.logo("https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.freepik.com%2Fpremium-vector%2Fmodern-design-simple-initial-mbu-logo-with-swoosh-for-business_22096417.htm&psig=AOvVaw0Yg4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4g4&ust=1725514652236000&source=images&cd=vfe&opi=89978449&ved=0CA8QjRxqFwoTCJDq4_Gk9o-GAxUAAAAHAAAAABAJ", link="https://www.mbutradingbot.com")

if st.session_state.authenticated:
    if USER_DATA[st.session_state.user_email]["2fa_enabled"]:
        if st.session_state.two_fa_passed:
            main_dashboard()
        else:
            two_fa_form()
    else:
        main_dashboard()
else:
    login_form()

if st.session_state.login_error:
    st.error(st.session_state.login_error)
