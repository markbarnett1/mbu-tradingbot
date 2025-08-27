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

# --- Custom CSS for Green and Gold Theme ---
def apply_custom_css():
    """Applies custom CSS for the green and gold theme."""
    st.markdown("""
        <style>
            .stApp {
                background-color: #f0f2f6; /* Light gray background */
                color: #2c3e50; /* Dark gray text */
            }
            .stHeader {
                background-color: #27ae60; /* Professional green */
                padding: 1rem;
                border-bottom: 2px solid #f1c40f; /* Gold accent */
            }
            .stSidebar {
                background-color: #2c3e50; /* Darker sidebar for contrast */
                color: #ecf0f1;
            }
            .stSidebar .stButton>button {
                background-color: #f1c40f; /* Gold button */
                color: #2c3e50;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            .stTextInput>div>div>input {
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
            }
            .stSubheader {
                color: #27ae60; /* Green subheaders */
                font-weight: bold;
                border-bottom: 1px solid #ecf0f1;
                padding-bottom: 0.5rem;
            }
            .stMetric > div {
                background-color: #ffffff;
                border-radius: 12px;
                border-left: 5px solid #27ae60; /* Green highlight */
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .stDataFrame {
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            /* Add some spacing for a cleaner look */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .st-emotion-cache-18lgl3p {
                margin-top: 1.5rem;
            }
        </style>
        """, unsafe_allow_html=True)


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
        st.session_state.two_fa_code = None
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
apply_custom_css()
st.logo("https://placehold.co/100x100/27AE60/F1C40F?text=MBU", link="https://www.mbutradingbot.com")

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
