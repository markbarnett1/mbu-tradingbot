import os
from datetime import datetime, timezone
import pytz

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from passlib.hash import bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from filelock import FileLock
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'change-me')
# NOTE: On Render Free (no disk), /data may not exist. SQLite will still create a file in /app if needed.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///mbu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# --- Encryption helper ---
def _valid_fernet_key(s: str) -> bool:
    try:
        return isinstance(s, str) and len(s.encode()) >= 44
    except Exception:
        return False

_ENC = os.getenv('ENCRYPTION_KEY', '')
FERNET = Fernet(_ENC.encode()) if _valid_fernet_key(_ENC) else Fernet(Fernet.generate_key())

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)

    subscription_active = db.Column(db.Boolean, default=False)
    trading_enabled = db.Column(db.Boolean, default=True)

    broker = db.Column(db.String(50), default='tradier')

    symbol = db.Column(db.String(40), default=os.getenv('DEFAULT_SYMBOL', 'AAPL'))
    qty = db.Column(db.Float, default=float(os.getenv('DEFAULT_QTY', '1')))
    side = db.Column(db.String(5), default=os.getenv('DEFAULT_SIDE', 'buy'))

    daily_time = db.Column(db.String(5), default=os.getenv('DEFAULT_DAILY_TIME', '09:30'))  # local hh:mm
    timezone = db.Column(db.String(64), default='UTC')
    trades_per_day = db.Column(db.Integer, default=1)
    trades_today = db.Column(db.Integer, default=0)
    last_trade_date = db.Column(db.String(10), default='')  # YYYY-MM-DD in user's local tz

    realized_pnl = db.Column(db.Float, default=0.0)
    position_qty = db.Column(db.Float, default=0.0)
    position_avg = db.Column(db.Float, default=0.0)

    enc_keys = db.Column(db.Text, default='')  # encrypted blob

    def set_keys(self, d: dict):
        keys = [
            'ALPACA_KEY','ALPACA_SECRET','ALPACA_BASE_URL',
            'BINANCE_KEY','BINANCE_SECRET',
            'COINBASE_KEY','COINBASE_SECRET','COINBASE_PASSPHRASE',
            'TRADIER_TOKEN','TRADIER_ACCOUNT_ID'
        ]
        blob = ';'.join([f"{k}={d.get(k,'')}" for k in keys])
        self.enc_keys = FERNET.encrypt(blob.encode()).decode()

    def get(self, key):
        try:
            data = FERNET.decrypt(self.enc_keys.encode()).decode()
            parts = dict(p.split('=', 1) for p in data.split(';') if '=' in p)
            return parts.get(key, '')
        except Exception:
            return ''

class TradeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    ts = db.Column(db.String(19))  # UTC timestamp
    symbol = db.Column(db.String(40))
    side = db.Column(db.String(5))
    qty = db.Column(db.Float)
    price = db.Column(db.Float)
    broker = db.Column(db.String(30))
    realized_pnl = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Scheduler & bootstrap (Flask 3.x: no before_first_request) ---
scheduler = None
_bootstrapped = False

def run_minutely():
    now_utc = datetime.now(tz=timezone.utc)
    # FIX: wrap DB access in app context
    with app.app_context():
        users = User.query.filter_by(subscription_active=True).all()
        for u in users:
            if should_trade_now(u, now_utc):
                execute_trade_safe(u)



def start_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler(timezone='UTC', daemon=True)
        scheduler.add_job(run_minutely, 'cron', minute='*')
        scheduler.start()

def bootstrap_once():
    """Ensure DB tables exist and scheduler is running (runs exactly once)."""
    global _bootstrapped
    if _bootstrapped:
        return
    with app.app_context():
        db.create_all()
    start_scheduler()
    _bootstrapped = True

@app.before_request
def _ensure_bootstrap():
    bootstrap_once()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html', year=datetime.utcnow().year)

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pw = request.form['password']
        if not email or not pw:
            return 'Email and password required', 400
        if User.query.filter_by(email=email).first():
            return 'Account already exists', 400
        u = User(email=email, pw_hash=bcrypt.hash(pw))
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pw = request.form['password']
        u = User.query.filter_by(email=email).first()
        if not u or not bcrypt.verify(pw, u.pw_hash):
            error = 'Invalid email or password'
        else:
            login_user(u)
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

def all_timezones():
    try:
        return pytz.all_timezones
    except Exception:
        return ['UTC']

@app.route('/dashboard')
@login_required
def dashboard():
    logs = TradeLog.query.filter_by(user_id=current_user.id).order_by(TradeLog.id.desc()).limit(50).all()
    last_order = logs[0] if logs else None
    return render_template(
        'dashboard.html',
        user=current_user,
        paypal_email=os.getenv('PAYPAL_EMAIL',''),
        logs=logs,
        last_order=last_order,
        timezones=all_timezones()
    )

@app.route('/save-broker', methods=['POST'])
@login_required
def save_broker():
    u = current_user
    u.broker = request.form.get('broker','tradier')
    u.symbol = request.form.get('symbol','AAPL').strip()
    u.qty = float(request.form.get('qty','1') or 1)
    u.side = request.form.get('side','buy')
    keys = {k:request.form.get(k,'') for k in [
        'ALPACA_KEY','ALPACA_SECRET','ALPACA_BASE_URL',
        'BINANCE_KEY','BINANCE_SECRET',
        'COINBASE_KEY','COINBASE_SECRET','COINBASE_PASSPHRASE',
        'TRADIER_TOKEN','TRADIER_ACCOUNT_ID'
    ]}
    u.set_keys(keys)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/save-schedule', methods=['POST'])
@login_required
def save_schedule():
    u = current_user
    u.timezone = request.form.get('timezone','UTC')
    u.daily_time = request.form.get('daily_time','09:30')
    try:
        u.trades_per_day = max(1, min(24, int(request.form.get('trades_per_day','1'))))
    except Exception:
        u.trades_per_day = 1
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/toggle-trading', methods=['POST'])
@login_required
def toggle_trading():
    u = current_user
    action = request.form.get('action','')
    u.trading_enabled = (action == 'start')
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/place-now', methods=['POST'])
@login_required
def place_now():
    if not current_user.subscription_active:
        return 'Subscription required', 402
    execute_trade_for_user(current_user)
    return redirect(url_for('dashboard'))

@app.route('/thank-you')
def thank_you():
    return render_template('thank.html')

@app.route('/paypal/ipn', methods=['POST'])
def paypal_ipn():
    data = request.form.to_dict()
    if data.get('receiver_email','').lower() != os.getenv('PAYPAL_EMAIL','').lower():
        return 'bad receiver', 400
    if data.get('payment_status') == 'Completed':
        payer = data.get('custom') or data.get('payer_email')
        u = User.query.filter_by(email=(payer or '').lower()).first()
        if u:
            u.subscription_active = True
            db.session.commit()
    return 'ok'

# --- Trading helpers ---
def choose_broker(user):
    from brokers.tradier import TradierBroker
    from brokers.alpaca import AlpacaBroker
    from brokers.ccxt_brokers import BinanceBroker, CoinbaseBroker

    if user.broker == 'tradier':
        token = user.get('TRADIER_TOKEN'); acct = user.get('TRADIER_ACCOUNT_ID')
        paper = True if os.getenv('TRADIER_PAPER','true').lower()=='true' else False
        return TradierBroker(token, acct, paper)
    if user.broker == 'alpaca':
        return AlpacaBroker(
            user.get('ALPACA_KEY'),
            user.get('ALPACA_SECRET'),
            user.get('ALPACA_BASE_URL') or 'https://paper-api.alpaca.markets'
        )
    if user.broker == 'binance':
        return BinanceBroker(user.get('BINANCE_KEY'), user.get('BINANCE_SECRET'))
    if user.broker == 'coinbase':
        return CoinbaseBroker(user.get('COINBASE_KEY'), user.get('COINBASE_SECRET'), user.get('COINBASE_PASSPHRASE'))
    raise ValueError('Unsupported broker')

def log_and_update_pnl(u, symbol, side, qty, price, broker_name):
    realized = 0.0
    if side == 'buy':
        new_qty = u.position_qty + qty
        if new_qty <= 0:
            u.position_qty = 0.0
            u.position_avg = 0.0
        else:
            u.position_avg = (u.position_avg * u.position_qty + price * qty) / new_qty if (u.position_qty + qty) > 0 else price
            u.position_qty = new_qty
    else:  # sell
        close_qty = min(qty, u.position_qty)
        if close_qty > 0:
            realized = (price - u.position_avg) * close_qty
            u.position_qty -= close_qty
            if u.position_qty == 0:
                u.position_avg = 0.0
    u.realized_pnl += realized
    log = TradeLog(
        user_id=u.id,
        ts=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        symbol=symbol, side=side, qty=qty, price=price,
        broker=broker_name, realized_pnl=realized
    )
    db.session.add(log)
    db.session.commit()

def execute_trade_for_user(user):
    broker = choose_broker(user)
    price = 0.0
    try:
        price = broker.get_price(user.symbol)
    except Exception:
        pass
    res = broker.place_market_order(user.symbol, user.side, user.qty)
    if not price or price == 0.0:
        try:
            price = broker.get_price(user.symbol)
        except Exception:
            price = 0.0
    log_and_update_pnl(user, user.symbol, user.side, float(user.qty), float(price or 0.0), getattr(broker, 'name', 'broker'))
    return res

def should_trade_now(u, now_utc):
    if not u.subscription_active or not u.trading_enabled:
        return False
    try:
        tz = pytz.timezone(u.timezone or 'UTC')
    except Exception:
        tz = pytz.UTC
    local_now = now_utc.astimezone(tz)
    local_date = local_now.strftime('%Y-%m-%d')
    hhmm = local_now.strftime('%H:%M')
    if u.last_trade_date != local_date:
        u.last_trade_date = local_date
        u.trades_today = 0
        db.session.commit()
    return (hhmm == (u.daily_time or '09:30')) and (u.trades_today < (u.trades_per_day or 1))

def user_lock_path(user_id: int):
    os.makedirs('/data/locks', exist_ok=True)
    return f"/data/locks/user_{user_id}.lock"

def execute_trade_safe(u):
    lock = FileLock(user_lock_path(u.id), timeout=0)
    if not lock.acquire(blocking=False):
        return {'skipped': 'locked'}
    try:
        now_utc = datetime.now(tz=timezone.utc)
        if not should_trade_now(u, now_utc):
            return {'skipped': 'schedule'}
        res = execute_trade_for_user(u)
        u.trades_today += 1
        db.session.commit()
        return res
    finally:
        try:
            lock.release()
        except Exception:
            pass

@app.route('/wake')
def wake():
    return jsonify(ok=True, ts=datetime.utcnow().isoformat())

if __name__ == '__main__':
    # Local dev run
    bootstrap_once()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','8080')))
