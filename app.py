import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "vidrio.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def create_user(username, password):
    db = get_db()
    pw_hash = generate_password_hash(password)
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate(username, password):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        return False
    return check_password_hash(row["password_hash"], password)

def get_current_user():
    return session.get("user")

@app.route("/")
def root():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Ingresa usuario y contraseña.", "warning")
            return redirect(url_for("register"))
        ok = create_user(username, password)
        if ok:
            flash("Usuario creado. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        else:
            flash("El usuario ya existe. Elige otro.", "danger")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if authenticate(username, password):
            session["user"] = username
            flash("Has iniciado sesión.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        flash("Acceso no autorizado. Inicia sesión.", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
