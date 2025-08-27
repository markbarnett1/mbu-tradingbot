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

# --- Custom CSS for Professional Green and Gold Theme ---
def apply_custom_css():
    """Applies custom CSS for the green and gold theme."""
    st.markdown("""
        <style>
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
            .metric-card > div {
                background-color: #ffffff;
                border-radius: 12px;
                border-left: 5px solid #27ae60; /* Green highlight */
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 1rem;
            }
            .stDataFrame {
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
            }
            .landing-subheader {
                font-size: 1.5rem;
                color: #7f8c8d;
                margin-top: -1rem;
                margin-bottom: 2rem;
            }
            .hero-image {
                margin: 2rem 0;
            }
            .stButton>button.cta-button {
                background-color: #f1c40f;
                color: #2c3e50;
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
                margin: 5rem auto;
                padding: 2rem;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
                border-top: 5px solid #27ae60;
            }
            .switch-button {
                background-color: transparent !important;
                border: none !important;
                color: #27ae60 !important;
                text-decoration: underline;
                margin-top: 1rem;
                cursor: pointer;
            }
            /* Dashboard layout */
            .dashboard-section {
                background-color: #ffffff;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            /* Correct button styles */
            .stButton>button {
                background-color: #f1c40f;
                color: #2c3e50;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #e6b100;
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
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False
if "show_auth_forms" not in st.session_state:
    st.session_state.show_auth_forms = False

def landing_page():
    """Displays the main landing page with marketing content."""
    st.markdown("<div class='landing-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='landing-header'>MBU TRADING BOT</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='landing-subheader'>Intelligent, Automated Trading for Your Success</h2>", unsafe_allow_html=True)
    
    # Using the new image provided by the user and fixing the deprecated parameter
    st.image("fotor_creation_2025-08-27.jpg", use_container_width=True)

    st.markdown("<p style='text-align: center; max-width: 600px; margin: auto; font-size: 1.1rem;'>Our intelligent bot analyzes market trends in real-time, executing trades with precision and speed to maximize your returns. We take the emotion out of trading so you can focus on your goals.</p>", unsafe_allow_html=True)
    
    st.button("Get Started", key="start_button", type="primary", on_click=lambda: st.session_state.update(show_auth_forms=True), help="Click to login or sign up.")

    st.markdown("</div>", unsafe_allow_html=True)

def login_form():
    """Displays the login form."""
    with st.container():
        st.subheader("Login to Your Account")
        email = st.text_input("Email", placeholder="Enter your email", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        col1, col2 = st.columns([1, 10])
        with col1:
            submit_button = st.button("Login", key="login_button")
        with col2:
            st.button("Don't have an account? Sign Up", key="switch_to_signup", on_click=lambda: st.session_state.update(show_signup=True, login_error=""), help="Switch to the sign-up form.")

    if submit_button:
        if email in USER_DATA and USER_DATA[email]["password"] == password:
            st.session_state.login_error = ""
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.rerun()
        else:
            st.session_state.login_error = "Invalid email or password."

def signup_form():
    """Displays the sign-up form."""
    with st.container():
        st.subheader("Create a New Account")
        email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
        password = st.text_input("Password", type="password", placeholder="Create a password", key="signup_password")
        
        col1, col2 = st.columns([1, 10])
        with col1:
            signup_button = st.button("Sign Up", key="signup_button")
        with col2:
            st.button("Already have an account? Login", key="switch_to_login", on_click=lambda: st.session_state.update(show_signup=False, login_error=""), help="Switch to the login form.")

    if signup_button:
        # In a real app, you would add the new user to a database here
        # For this demo, we just show a success message
        st.session_state.signup_success = True
        st.session_state.show_signup = False # Switch back to login after success

def two_fa_form():
    """Displays the 2FA form."""
    with st.container():
        st.subheader("Two-Factor Authentication")
        st.write(f"Please enter the 6-digit code sent to {st.session_state.user_email}")
        two_fa_input = st.text_input("6-digit code", max_chars=6)

        col1, col2 = st.columns([1, 10])
        with col1:
            submit_button = st.button("Verify", key="2fa_button")

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
    st.write("Welcome, Mark! Here is a professional overview of your trading activity.")

    st.sidebar.header("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.two_fa_passed = False
        st.session_state.two_fa_code = None
        st.session_state.user_email = None
        st.session_state.login_error = ""
        st.session_state.show_auth_forms = False
        st.rerun()

    # --- Section: Account Summary (Improved) ---
    st.markdown("---")
    st.subheader("Account Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Current Balance", "$10,500", "500")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Total Trades", "2,100", "15")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Win Rate", "75%", "2%")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Section: Performance Chart ---
    st.markdown("---")
    st.subheader("Bot Performance")
    with st.container():
        st.write("This chart shows the cumulative performance of the bot over time.")
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=["BTC", "ETH", "AAPL"]
        ).cumsum()
        st.line_chart(chart_data)

    # --- Section: Recent Trades ---
    st.markdown("---")
    st.subheader("Recent Trade History")
    with st.container():
        st.write("A detailed log of recent trades executed by the bot.")
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
