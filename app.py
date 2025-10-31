import os, re, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "vidrio.db")

# -------- DB -------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    # Tabla con email único y también phone único
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            company TEXT,
            created_at TEXT NOT NULL
        );
    """)
    # Asegurar índice único en phone (si ya hay datos duplicados, fallará al crear; ver nota abajo)
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_unique ON users(phone);")
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

with app.app_context():
    init_db()

# -------- Helpers -------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def create_user(email, password, first_name, last_name, address, phone, company):
    db = get_db()
    pw_hash = generate_password_hash(password)
    db.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, address, phone, company, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (email, pw_hash, first_name, last_name, address, phone, company, datetime.utcnow().isoformat()))
    db.commit()

def authenticate(email, password):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return bool(row and check_password_hash(row["password_hash"], password))

def get_current_user():
    return session.get("user_email")

# -------- Rutas -------
@app.route("/")
def root():
    return redirect(url_for("dashboard" if get_current_user() else "login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email       = request.form.get("email","").strip().lower()
        password    = request.form.get("password","")
        confirm     = request.form.get("confirm","")
        first_name  = request.form.get("first_name","").strip()
        last_name   = request.form.get("last_name","").strip()
        address     = request.form.get("address","").strip()
        phone       = request.form.get("phone","").strip()
        company     = request.form.get("company","").strip()
        accept      = request.form.get("accept")  # "on" si marcó el checkbox

        # Validaciones
        if not (email and password and confirm and first_name and last_name):
            flash("Completa los campos obligatorios (*).", "warning"); return redirect(url_for("register"))
        if not EMAIL_RE.match(email):
            flash("Correo inválido.", "danger"); return redirect(url_for("register"))
        if password != confirm:
            flash("Las contraseñas no coinciden.", "danger"); return redirect(url_for("register"))
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "warning"); return redirect(url_for("register"))
        if not accept:
            flash("Debes aceptar las políticas para continuar.", "warning"); return redirect(url_for("register"))

        db = get_db()
        # Unicidad de correo y teléfono
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            flash("Ese correo ya está registrado.", "danger"); return redirect(url_for("register"))
        if phone and db.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone():
            flash("Ese teléfono ya está registrado.", "danger"); return redirect(url_for("register"))

        try:
            create_user(email, password, first_name, last_name, address, phone, company)
        except sqlite3.IntegrityError as e:
            # Por si el índice único de phone/email dispara aquí
            msg = "Correo o teléfono ya registrados."
            flash(msg, "danger"); return redirect(url_for("register"))

        flash("Cuenta creada. Inicia sesión.", "success")
        # regresar a inicio (login)
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if authenticate(email, password):
            session["user_email"] = email
            flash("Has iniciado sesión.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    user_email = get_current_user()
    if not user_email:
        flash("Acceso no autorizado. Inicia sesión.", "warning")
        return redirect(url_for("login"))

    db = get_db()
    u = db.execute("SELECT first_name, last_name FROM users WHERE email = ?", (user_email,)).fetchone()
    full_name = f"{u['first_name']} {u['last_name']}" if u else user_email

    # Un menú simple
    menu = [
        {"href": url_for("dashboard"), "label": "Inicio"},
        {"href": "#", "label": "Pedidos (próximamente)"},
        {"href": "#", "label": "Perfil (próximamente)"},
        {"href": url_for("logout"), "label": "Cerrar sesión"},
    ]
    return render_template("dashboard.html", user=full_name, menu=menu)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5020)), debug=True)
