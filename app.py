from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import os
from datetime import datetime

app = Flask(__name__)

# Environment configs
app.secret_key = os.getenv("FLASK_SECRET", "devkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///mbu.db")
db = SQLAlchemy(app)

# Encryption key
ENC_KEY = os.getenv("ENCRYPTION_KEY")
FERNET = Fernet(ENC_KEY.encode()) if ENC_KEY else Fernet(Fernet.generate_key())

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)
    subscription_active = db.Column(db.Boolean, default=False)
    trading_enabled = db.Column(db.Boolean, default=False)
    broker = db.Column(db.String(50))
    symbol = db.Column(db.String(40))
    qty = db.Column(db.Float)
    side = db.Column(db.String(5))
    daily_time = db.Column(db.String(5))
    timezone = db.Column(db.String(64))
    trades_per_day = db.Column(db.Integer, default=1)
    trades_today = db.Column(db.Integer, default=0)
    last_trade_date = db.Column(db.String(10))
    realized_pnl = db.Column(db.Float, default=0.0)
    position_qty = db.Column(db.Float, default=0.0)
    position_avg = db.Column(db.Float, default=0.0)
    enc_keys = db.Column(db.Text)

# Bootstrap DB
@app.before_first_request
def bootstrap():
    db.create_all()

# Home
@app.route("/")
def index():
    return render_template("index.html")

# Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]
        if User.query.filter_by(email=email).first():
            return "Email already registered."
        user = User(email=email, pw_hash=generate_password_hash(pw))
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.pw_hash, pw):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        return "Invalid login."
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# Inject datetime into all templates (important fix!)
@app.context_processor
def inject_globals():
    return dict(datetime=datetime)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
