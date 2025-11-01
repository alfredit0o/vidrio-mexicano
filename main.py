# main.py
import os, re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db import init_app_db, get_db          # <- usa SQLAlchemy (engine/conn) definido en app/db.py
from app.blueprints import register_blueprints   # <- registra core + módulos (p.ej. medidas)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")
app.config["ASSET_VERSION"] = os.environ.get("ASSET_VERSION", "1")  # <- añade esto


# Inicializar DB y blueprints
init_app_db(app)
register_blueprints(app)

# -------------------- HELPERS --------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def create_user(email, password, first_name, last_name, address, phone, company):
    pw_hash = generate_password_hash(password)
    with get_db() as db:
        db.execute(text("""
            INSERT INTO users
              (email, password_hash, first_name, last_name, address, phone, company, created_at)
            VALUES
              (:email, :pw, :fn, :ln, :addr, :phone, :company, :ts)
        """), dict(
            email=email, pw=pw_hash, fn=first_name, ln=last_name,
            addr=address, phone=phone, company=company, ts=datetime.utcnow().isoformat()
        ))

def authenticate(email, password):
    with get_db() as db:
        row = db.execute(text(
            "SELECT password_hash FROM users WHERE email = :email"
        ), {"email": email}).mappings().first()
    return bool(row and check_password_hash(row["password_hash"], password))

def get_current_user():
    return session.get("user_email")

# -------------------- AUTH --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email      = request.form.get("email","").strip().lower()
        password   = request.form.get("password","")
        confirm    = request.form.get("confirm","")
        first_name = request.form.get("first_name","").strip()
        last_name  = request.form.get("last_name","").strip()
        address    = request.form.get("address","").strip()
        phone      = request.form.get("phone","").strip()
        company    = request.form.get("company","").strip()
        accept     = request.form.get("accept")

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

        with get_db() as db:
            if db.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email}).first():
                flash("Ese correo ya está registrado.", "danger"); return redirect(url_for("register"))
            if phone and db.execute(text("SELECT 1 FROM users WHERE phone = :p"), {"p": phone}).first():
                flash("Ese teléfono ya está registrado.", "danger"); return redirect(url_for("register"))

        try:
            create_user(email, password, first_name, last_name, address, phone, company)
        except IntegrityError:
            flash("Correo o teléfono ya registrados.", "danger"); return redirect(url_for("register"))

        flash("Cuenta creada. Inicia sesión.", "success")
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
            return redirect(url_for("core.dashboard"))  # endpoint del blueprint core
        flash("Correo o contraseña incorrectos.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

# -------------------- UTIL --------------------
@app.route("/__routes")
def __routes():
    lines = []
    for r in app.url_map.iter_rules():
        lines.append(f"{r.endpoint:25s}  {','.join(sorted(r.methods)):20s}  {r.rule}")
    return "<pre>" + "\n".join(sorted(lines)) + "</pre>"

# ===== Placeholders mientras migras a blueprints =====
@app.route("/clientes")
def clientes():
    return render_template("module_blank.html", title="Clientes")

@app.route("/productos")
def productos():
    return render_template("module_blank.html", title="Productos")

@app.route("/pedidos")
def pedidos():
    return render_template("module_blank.html", title="Pedidos")

@app.route("/cotizaciones")
def cotizaciones():
    return render_template("module_blank.html", title="Cotizaciones")

@app.route("/inventario")
def inventario():
    return render_template("module_blank.html", title="Inventario")

@app.route("/reportes")
def reportes():
    return render_template("module_blank.html", title="Reportes")

# -------------------- DEV LOCAL --------------------
if __name__ == "__main__":
    # En Render te levanta gunicorn por Procfile; esto es solo para local
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5020)), debug=True)
