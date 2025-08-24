import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Secret for sessions
app.secret_key = os.environ.get("FLASK_SECRET", "dev_key_change_me")

# Database (Render: sqlite file at /data so it survives restarts)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:////data/mbu.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Optional encryption key (for later secure storage). If invalid or missing,
# we just don't use Fernet to avoid crashing the app.
ENC_KEY = os.environ.get("ENCRYPTION_KEY", "")
fernet = None
try:
    if ENC_KEY:
        fernet = Fernet(ENC_KEY.encode())
except Exception:
    fernet = None  # stay running even if key is malformed

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)

# Create tables at startup (Flask 3.x safe)
with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# Template helpers
# -----------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    # Allows {{ datetime.utcnow().year }} in templates
    return {"datetime": datetime}

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not email or not password:
            return "Email and password required", 400
        try:
            user = User(email=email, pw_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "Account already exists. Please log in.", 400
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.pw_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        return "Invalid email or password", 401
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/healthz")
def healthz():
    return "ok", 200

# Local dev (Render runs via gunicorn, so this branch is ignored there)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
