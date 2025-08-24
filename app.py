import os
from datetime import datetime, timezone
import pytz

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# ----- App & Config -----
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////data/mbu.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Make `datetime` available in Jinja templates (fixes “datetime is undefined”)
app.jinja_env.globals["datetime"] = datetime

# ----- Encryption helper -----
def _valid_fernet_key(s: str) -> bool:
    # Fernet expects a 32-byte urlsafe base64 key (44 chars)
    try:
        return isinstance(s, str) and len(s.encode()) >= 44
    except Exception:
        return False

_ENC = os.getenv("ENCRYPTION_KEY", "")
FERNET = Fernet(_ENC.encode()) if _valid_fernet_key(_ENC) else Fernet(Fernet.generate_key())

# ----- Models -----
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)

    subscription_active = db.Column(db.Boolean, default=False)
    trading_enabled = db.Column(db.Boolean, default=True)

    broker = db.Column(db.String(50), default="tradier")

    symbol = db.Column(db.String(40), default=os.getenv("DEFAULT_SYMBOL", "AAPL"))
    qty = db.Column(db.Float, default=float(os.getenv("DEFAULT_QTY", "1")))
    side = db.Column(db.String(5), default=os.getenv("DEFAULT_SIDE", "buy"))

    daily_time = db.Column(db.String(5), default=os.getenv("DEFAULT_DAILY_TIME", "09:30"))  # local hh:mm
    timezone = db.Column(db.String(64), default="UTC")
    trades_per_day = db.Column(db.Integer, default=1)
    trades_today = db.Column(db.Integer, default=0)
    last_trade_date = db.Column(db.String(10), default="")  # YYYY-MM-DD in user's local tz

    realized_pnl = db.Column(db.Float, default=0.0)
    position_qty = db.Column(db.Float, default=0.0)
    position_avg = db.Column(db.Float, default=0.0)

    enc_keys = db.Column(db.Text, default="")  # encrypted blob

    def set_keys(self, d: dict):
        keys = [
            "ALPACA_KEY","ALPACA_SECRET","ALPACA_BASE_URL",
            "BINANCE_KEY","BINANCE_SECRET",
            "COINBASE_KEY","COINBASE_SECRET","COINBASE_PASSPHRASE",
            "TRADIER_TOKEN","TRADIER_ACCOUNT_ID",
        ]
        blob = ";".join([f"{k}={d.get(k,'')}" for k in keys])
        self.enc_keys = FERNET.encrypt(blob.encode()).decode()

    def get(self, key):
        try:
            data = FERNET.decrypt(self.enc_keys.encode()).decode()
            parts = dict(p.split("=", 1) for p in data.split(";") if "=" in p)
            return parts.get(key, "")
        except Exception:
            return ""

class TradeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
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

# ----- One-time bootstrap (create tables) -----
_bootstrapped = False

def bootstrap_once():
    global _bootstrapped
    if _bootstrapped:
        return
    # idempotent; safe if multiple workers call it
    with app.app_context():
        db.create_all()
    _bootstrapped = True

@app.before_request
def _ensure_bootstrap():
    bootstrap_once()

# ----- Helpers -----
def all_timezones():
    try:
        return pytz.all_timezones
    except Exception:
        return ["UTC"]

# ----- Routes -----
@app.route("/healthz")
def healthz():
    return "ok", 200

@app.route("/wake")
def wake():
    return jsonify(ok=True, ts=datetime.utcnow().isoformat())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        if not email or not pw:
            return "Email and password required", 400
        if User.query.filter_by(email=email).first():
            return "Account already exists", 400
        u = User(email=email, pw_hash=generate_password_hash(pw))
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        u = User.query.filter_by(email=email).first()
        if not u or not check_password_hash(u.pw_hash, pw):
            error = "Invalid email or password"
        else:
            login_user(u)
            return redirect(url_for("dashboard"))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    logs = (TradeLog.query
            .filter_by(user_id=current_user.id)
            .order_by(TradeLog.id.desc())
            .limit(50).all())
    last_order = logs[0] if logs else None
    return render_template(
        "dashboard.html",
        user=current_user,
        paypal_email=os.getenv("PAYPAL_EMAIL",""),
        logs=logs,
        last_order=last_order,
        timezones=all_timezones()
    )

@app.route("/save-broker", methods=["POST"])
@login_required
def save_broker():
    u = current_user
    u.broker = request.form.get("broker","tradier")
    u.symbol = (request.form.get("symbol","AAPL") or "AAPL").strip().upper()
    try:
        u.qty = float(request.form.get("qty","1") or 1)
    except Exception:
        u.qty = 1.0
    u.side = request.form.get("side","buy")
    keys = {k:request.form.get(k,"") for k in [
        "ALPACA_KEY","ALPACA_SECRET","ALPACA_BASE_URL",
        "BINANCE_KEY","BINANCE_SECRET",
        "COINBASE_KEY","COINBASE_SECRET","COINBASE_PASSPHRASE",
        "TRADIER_TOKEN","TRADIER_ACCOUNT_ID",
    ]}
    u.set_keys(keys)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/save-schedule", methods=["POST"])
@login_required
def save_schedule():
    u = current_user
    u.timezone = request.form.get("timezone","UTC")
    u.daily_time = request.form.get("daily_time","09:30")
    try:
        u.trades_per_day = max(1, min(24, int(request.form.get("trades_per_day","1") or 1)))
    except Exception:
        u.trades_per_day = 1
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/toggle-trading", methods=["POST"])
@login_required
def toggle_trading():
    u = current_user
    action = request.form.get("action","")
    u.trading_enabled = (action == "start")
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/place-now", methods=["POST"])
@login_required
def place_now():
    # TEMP: safe stub so missing broker modules cannot crash the app.
    log = TradeLog(
        user_id=current_user.id,
        ts=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        symbol=current_user.symbol,
        side=current_user.side,
        qty=float(current_user.qty),
        price=0.0,
        broker=current_user.broker,
        realized_pnl=0.0,
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    bootstrap_once()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8080")))
