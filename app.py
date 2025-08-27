# app.py - Version 2.0 with Backtesting, Risk Management, and Advanced Metrics
import streamlit as st
import pandas as pd
import datetime
import time
import random
import numpy as np

# A strong, visible disclaimer is critical for a financial application.
DISCLAIMER_TEXT = """
**⚠️ Important Risk Disclaimer**

This trading bot is for educational and demonstrative purposes only. Automated trading involves **significant financial risk**, and you may lose more than your initial investment. There is **no guarantee of profit**, and past performance is not an indicator of future results.

By using this bot, you acknowledge that you are responsible for your own trading decisions and financial outcomes. Please use a paper trading account before using real capital. The creators and providers of this bot are not responsible for any financial losses.
"""

# Define some symbols for the bot to "research" and trade.
# In a real-world application, this would be an advanced function
# that uses an API to screen for liquid, trending, or undervalued assets.
STOCKS_TO_TRADE = ["GOOGL", "AMZN", "MSFT", "TSLA"]
CRYPTO_TO_TRADE = ["BTC", "ETH", "SOL", "ADA"]

# --- Website Design and User Interface ---

# Set a simplified, single-page layout with a gold and green theme.
st.set_page_config(
    page_title="MBU Trading Bot",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .main-header {
        color: #FFD700; /* Gold */
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-size: 3em;
        padding-top: 20px;
        padding-bottom: 10px;
    }
    .subheader {
        color: #32CD32; /* Lime Green */
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-size: 1.5em;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #FFD700; /* Gold */
        color: black;
        border: none;
        padding: 10px 20px;
        border-radius: 12px;
        font-size: 1.2em;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #DAA520; /* Darker Gold */
        color: white;
        transform: scale(1.05);
    }
    .stButton>button:active {
        background-color: #B8860B; /* Even darker Gold */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .stRadio > div {
        background-color: #1a1a1a;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #32CD32;
        margin-bottom: 10px;
    }
    .stRadio > label {
        font-weight: bold;
        color: #32CD32; /* Lime Green */
    }
    .stRadio > div > label > div > div:first-child {
        color: #FFD700; /* Gold for text */
    }
    .stRadio > div > label > div > div:first-child:hover {
        color: #32CD32; /* Green on hover */
    }
    .stRadio > div > label > div > div > div > span:last-child {
        color: #FFD700;
        font-weight: bold;
    }
    .stRadio [data-baseweb="radio"] > div {
        color: #32CD32; /* Lime Green */
    }
    .stMarkdown p {
        color: #e0e0e0;
        text-align: justify;
    }
    .disclaimer-box {
        background-color: #280808;
        padding: 20px;
        border-left: 5px solid #ff4d4d;
        margin-bottom: 20px;
        border-radius: 8px;
        font-size: 0.9em;
    }
    .disclaimer-box h1 {
        color: #ff4d4d;
        margin-top: 0;
    }
    .disclaimer-box p {
        color: #ffcccc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 class='main-header'>MBU Trading Bot</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='subheader'>Set Your Trading Parameters and Let the Bot Work for You!</h2>", unsafe_allow_html=True)
st.markdown(f"<div class='disclaimer-box'>{DISCLAIMER_TEXT}</div>", unsafe_allow_html=True)

# Initialize session state variables for the bot's state
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'pdt_count' not in st.session_state:
    st.session_state.pdt_count = 0
if 'last_trade_date' not in st.session_state:
    st.session_state.last_trade_date = datetime.date.today()
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0
if 'trades_executed' not in st.session_state:
    st.session_state.trades_executed = []
if 'open_positions' not in st.session_state:
    st.session_state.open_positions = {}
if 'historical_data' not in st.session_state:
    # Simulate historical data for backtesting
    dates = pd.date_range(end=datetime.date.today(), periods=100, freq='B')
    data = {
        'Date': dates,
        'GOOGL': np.random.normal(200, 5, 100).cumsum() + 1000,
        'AMZN': np.random.normal(100, 3, 100).cumsum() + 500,
        'MSFT': np.random.normal(150, 4, 100).cumsum() + 800,
        'TSLA': np.random.normal(800, 10, 100).cumsum() + 2000,
        'BTC': np.random.normal(50000, 1000, 100).cumsum() + 50000,
        'ETH': np.random.normal(3000, 200, 100).cumsum() + 3000,
    }
    st.session_state.historical_data = pd.DataFrame(data).set_index('Date')

# --- Trading Strategy Functions ---

def get_trading_signal(strategy_name, current_price, history_prices):
    """
    Simulates a trading signal based on the chosen strategy.
    In a real app, this would use live market data and APIs.
    """
    signal = "HOLD"
    random_value = random.random()
    
    if strategy_name == "Momentum":
        # Simple simulated momentum check
        if len(history_prices) > 5:
            price_change = current_price - history_prices.iloc[-5]
            if price_change > 0 and random_value > 0.6:
                signal = "BUY"
            elif price_change < 0 and random_value < 0.4:
                signal = "SELL"
    
    elif strategy_name == "Breakout":
        # Simple simulated breakout check
        if len(history_prices) > 20:
            if current_price > history_prices.max() and random_value > 0.7:
                signal = "BUY"
            elif current_price < history_prices.min() and random_value < 0.3:
                signal = "SELL"
    
    elif strategy_name == "Mean Reversion":
        # Simple simulated mean reversion check
        if len(history_prices) > 10:
            mean = history_prices.mean()
            if current_price < mean * 0.95 and random_value < 0.4:
                signal = "BUY"
            elif current_price > mean * 1.05 and random_value > 0.6:
                signal = "SELL"
    
    return signal

def calculate_metrics(trades):
    """Calculates advanced performance metrics."""
    if not trades:
        return {
            "Total P/L": 0,
            "Sharpe Ratio": 0,
            "Max Drawdown": 0,
            "Winning Trades": 0,
            "Losing Trades": 0,
            "Win Ratio": 0
        }

    df = pd.DataFrame(trades)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Cumulative P/L'] = df['P/L'].cumsum()
    
    # Sharpe Ratio (Simulated)
    returns = df['P/L']
    if len(returns) > 1 and returns.std() != 0:
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) # Assume 252 trading days
    else:
        sharpe_ratio = 0
    
    # Max Drawdown
    cumulative_returns = df['Cumulative P/L']
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() if not drawdown.empty else 0
    
    # Win/Loss Ratio
    winning_trades = df[df['P/L'] > 0]
    losing_trades = df[df['P/L'] < 0]
    win_ratio = len(winning_trades) / len(df) if len(df) > 0 else 0
    
    return {
        "Total P/L": df['Cumulative P/L'].iloc[-1],
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown": max_drawdown,
        "Winning Trades": len(winning_trades),
        "Losing Trades": len(losing_trades),
        "Win Ratio": win_ratio
    }

def execute_trade(symbol, side, quantity, price, stop_loss_pct, take_profit_pct):
    """
    Simulates the execution of a trade.
    Returns the profit/loss for the trade.
    """
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
    st.info(f"OPENED trade: {side} {quantity} shares of {symbol} at ${price:.2f}")

def close_trade(symbol, current_price):
    """
    Closes an open position and calculates profit/loss.
    """
    position = st.session_state.open_positions[symbol]
    entry_price = position['Entry_Price']
    side = position['Side']
    quantity = position['Quantity']
    
    if side == "BUY":
        profit = (current_price - entry_price) * quantity
    else: # SELL (short)
        profit = (entry_price - current_price) * quantity
        
    st.session_state.total_profit += profit
    
    # Log the trade
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
    st.success(f"CLOSED trade: {side} {quantity} shares of {symbol} at ${current_price:.2f} | P/L: ${profit:.2f}")
    
    del st.session_state.open_positions[symbol]
    
def perform_rebalance():
    """
    Simulates a portfolio rebalancing event.
    In a real app, this would check asset weights and adjust accordingly.
    """
    st.session_state.trades_executed.append({
        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Symbol": "N/A",
        "Side": "Rebalance",
        "Quantity": "N/A",
        "P/L": "N/A",
        "Cumulative P/L": st.session_state.total_profit,
        "Reason": "Rebalance"
    })
    st.info("Portfolio rebalancing in progress...")

def run_backtest(strategy, stop_loss_pct, take_profit_pct):
    """
    Runs a simulation of the trading strategy on historical data.
    """
    st.info("Running backtest... please wait.")
    test_trades = []
    test_positions = {}
    
    for symbol in st.session_state.historical_data.columns:
        prices = st.session_state.historical_data[symbol]
        
        for i in range(1, len(prices)):
            current_price = prices.iloc[i]
            historical_prices = prices.iloc[:i]
            
            # Check for open position to apply risk management
            if symbol in test_positions:
                position = test_positions[symbol]
                entry_price = position['Entry_Price']
                
                # Check Stop-Loss
                if (current_price - entry_price) / entry_price <= -stop_loss_pct / 100:
                    profit = (current_price - entry_price) * position['Quantity']
                    test_trades.append({
                        "Date": prices.index[i].strftime("%Y-%m-%d %H:%M:%S"),
                        "Symbol": symbol, "Side": position['Side'], "Quantity": position['Quantity'],
                        "P/L": profit, "Reason": "Stop Loss"
                    })
                    del test_positions[symbol]
                    continue
                
                # Check Take-Profit
                if (current_price - entry_price) / entry_price >= take_profit_pct / 100:
                    profit = (current_price - entry_price) * position['Quantity']
                    test_trades.append({
                        "Date": prices.index[i].strftime("%Y-%m-%d %H:%M:%S"),
                        "Symbol": symbol, "Side": position['Side'], "Quantity": position['Quantity'],
                        "P/L": profit, "Reason": "Take Profit"
                    })
                    del test_positions[symbol]
                    continue

            # Get trading signal
            signal = get_trading_signal(strategy, current_price, historical_prices)
            
            if signal == "BUY" and symbol not in test_positions:
                quantity = random.randint(1, 10)
                test_positions[symbol] = {
                    "Date": prices.index[i],
                    "Symbol": symbol,
                    "Side": "BUY",
                    "Quantity": quantity,
                    "Entry_Price": current_price
                }
    
    # Close any remaining open positions
    for symbol, position in test_positions.items():
        profit = (prices.iloc[-1] - position['Entry_Price']) * position['Quantity']
        test_trades.append({
            "Date": prices.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
            "Symbol": symbol, "Side": position['Side'], "Quantity": position['Quantity'],
            "P/L": profit, "Reason": "End of Backtest"
        })

    # Calculate and display metrics for the backtest
    metrics = calculate_metrics(test_trades)
    st.success("Backtest complete!")
    st.subheader("Backtesting Results")
    colA, colB, colC = st.columns(3)
    colA.metric("Final P/L", f"${metrics['Total P/L']:.2f}")
    colB.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
    colC.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
    st.metric("Win/Loss Ratio", f"{metrics['Win Ratio']:.2%}")
    st.dataframe(pd.DataFrame(test_trades))

# --- Main App Logic and UI ---

col1, col2 = st.columns(2)

with col1:
    st.markdown("<h3 style='color: #FFD700;'>Choose a Trading Strategy</h3>", unsafe_allow_html=True)
    strategy = st.radio(
        "Which strategy should the bot use?",
        options=["Momentum", "Breakout", "Mean Reversion"],
        index=0,
    )

    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Set Trading Timeframe</h3>", unsafe_allow_html=True)
    timeframe = st.radio(
        "How long should the bot run for?",
        options=["1 day", "1 week", "1 month", "Trade until canceled"],
        index=0,
    )
    
    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Risk Management</h3>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        stop_loss_pct = st.number_input("Stop-Loss %", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
    with col4:
        take_profit_pct = st.number_input("Take-Profit %", min_value=0.0, max_value=100.0, value=10.0, step=0.1)

    st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Backtesting</h3>", unsafe_allow_html=True)
    if st.button("📈 Run Backtest"):
        run_backtest(strategy, stop_loss_pct, take_profit_pct)

with col2:
    st.markdown("<h3 style='color: #FFD700;'>Bot Controls</h3>", unsafe_allow_html=True)
    if st.session_state.bot_running:
        if st.button("🔴 Stop Bot"):
            st.session_state.bot_running = False
            st.success("Bot has been stopped.")
            st.stop()
        st.warning("The bot is currently running. You can stop it at any time.")
    else:
        if st.button("🟢 Start Bot"):
            st.session_state.bot_running = True
            st.session_state.start_time = datetime.datetime.now()
            st.session_state.open_positions = {}
            st.session_state.trades_executed = []
            st.success(f"Bot started using the {strategy} strategy.")

    if st.session_state.bot_running:
        st.markdown("<h3 style='color: #FFD700; margin-top: 30px;'>Live Dashboard</h3>", unsafe_allow_html=True)
        placeholder = st.empty()
        
        # Determine the end time based on the selected timeframe
        end_time = None
        if timeframe == "1 day":
            end_time = st.session_state.start_time + datetime.timedelta(days=1)
        elif timeframe == "1 week":
            end_time = st.session_state.start_time + datetime.timedelta(weeks=1)
        elif timeframe == "1 month":
            end_time = st.session_state.start_time + datetime.timedelta(days=30)
        
        while st.session_state.bot_running:
            # Check for bot stop condition
            if end_time and datetime.datetime.now() > end_time:
                st.session_state.bot_running = False
                st.warning("Trading period has ended. Bot stopped automatically.")
                break
            
            # Check for PDT reset
            current_date = datetime.date.today()
            if current_date > st.session_state.last_trade_date:
                st.session_state.pdt_count = 0
                st.session_state.last_trade_date = current_date
                st.info("PDT counter has been reset for the new day.")
            
            # Check open positions for stop-loss/take-profit
            for symbol, position in list(st.session_state.open_positions.items()):
                # In a real app, this would get the live price from a market API
                current_price = position['Entry_Price'] * (1 + random.uniform(-0.05, 0.05))
                
                # Stop-Loss logic
                if (current_price - position['Entry_Price']) / position['Entry_Price'] <= -stop_loss_pct / 100:
                    close_trade(symbol, current_price)
                    
                # Take-Profit logic
                elif (current_price - position['Entry_Price']) / position['Entry_Price'] >= take_profit_pct / 100:
                    close_trade(symbol, current_price)

            # Choose a random asset to simulate the "research" function
            symbol = random.choice(STOCKS_TO_TRADE + CRYPTO_TO_TRADE)
            is_stock = symbol in STOCKS_TO_TRADE
            
            # Check PDT rule for stocks
            if is_stock and st.session_state.pdt_count >= 1:
                st.info(f"Skipping trade for stock '{symbol}' due to PDT rule (max 1 trade/day).")
                time.sleep(10)
                continue
            
            # Get trading signal
            if symbol not in st.session_state.open_positions:
                # Simulate a live price and historical prices for the signal
                current_price = st.session_state.historical_data[symbol].iloc[-1]
                history_prices = st.session_state.historical_data[symbol].iloc[-20:]
                
                signal = get_trading_signal(strategy, current_price, history_prices)
                
                if signal == "BUY":
                    quantity = random.randint(1, 10)
                    execute_trade(symbol, signal, quantity, current_price, stop_loss_pct, take_profit_pct)
                    
                    if is_stock:
                        st.session_state.pdt_count += 1
            
            # Rebalance occasionally
            if len(st.session_state.trades_executed) > 0 and len(st.session_state.trades_executed) % 5 == 0:
                perform_rebalance()
                
            # Update dashboard in real-time
            with placeholder.container():
                metrics = calculate_metrics(st.session_state.trades_executed)
                colA, colB, colC = st.columns(3)
                colA.metric("Total P/L", f"${st.session_state.total_profit:.2f}")
                colB.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
                colC.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
                st.dataframe(pd.DataFrame(st.session_state.trades_executed).iloc[::-1])
            
            time.sleep(random.randint(5, 20))
