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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///mbu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# --- FIX START: redirect unauthorized users + make datetime available in templates ---
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'

@app.context_processor
def inject_globals():
    from datetime import datetime as _dt
    return dict(datetime=_dt)
# --- FIX END ---

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

    daily_time = db.Column(db.String(5), default=os.getenv('DEFAULT_DAILY_TIME', '09:30'))
    timezone = db.Column(db.String(64), default='UTC')
    trades_per_day = db.Column(db.Integer, default=1)
    trades_today = db.Column(db.Integer, default=0)
    last_trade_date = db.Column(db.String(10), default='')

    realized_pnl = db.Column(db.Float, default=0.0)
    position_qty = db.Column(db.Float, default=0.0)
    position_avg = db.Column(db.Float, default=0.0)

    enc_keys = db.Column(db.Text, default='')

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
    ts = db.Column(db.String(19))
    symbol = db.Column(db.String(40))
    side = db.Column(db.String(5))
    qty = db.Column(db.Float)
    price = db.Column(db.Float)
    broker = db.Column(db.String(30))
    realized_pnl = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Scheduler & bootstrap ---
scheduler = None
_bootstrapped = False

def run_minutely():
    now_utc = datetime.now(tz=timezone.utc)
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

# ... (rest of your routes and trading functions stay the same) ...

@app.route('/wake')
def wake():
    return jsonify(ok=True, ts=datetime.utcnow().isoformat())

if __name__ == '__main__':
    bootstrap_once()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','8080')))
