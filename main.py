# main.py
import os, re, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from app.db import init_app_db, get_db
from app.blueprints import register_blueprints  # <-- define y registra core + (opcional) módulos

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

# DB y blueprints
init_app_db(app)
register_blueprints(app)

# -------------------- HELPERS --------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def create_user(email, password, first_name, last_name, address, phone, company):
    db = get_db()
    pw_hash = generate_password_hash(password)
    db.execute(
        """INSERT INTO users
           (email, password_hash, first_name, last_name, address, phone, company, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (email, pw_hash, first_name, last_name, address, phone, company, datetime.utcnow().isoformat()),
    )
    db.commit()

def authenticate(email, password):
    db  = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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

        db = get_db()
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            flash("Ese correo ya está registrado.", "danger"); return redirect(url_for("register"))
        if phone and db.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone():
            flash("Ese teléfono ya está registrado.", "danger"); return redirect(url_for("register"))

        try:
            create_user(email, password, first_name, last_name, address, phone, company)
        except sqlite3.IntegrityError:
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
            return redirect(url_for("core.dashboard"))  # dashboard del blueprint core
        flash("Correo o contraseña incorrectos.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

# Listado de rutas para debug
@app.route("/__routes")
def __routes():
    lines = []
    for r in app.url_map.iter_rules():
        lines.append(f"{r.endpoint:25s}  {','.join(sorted(r.methods)):20s}  {r.rule}")
    return "<pre>" + "\n".join(sorted(lines)) + "</pre>"

# ===== Placeholders (mientras mueves a blueprints de módulo) =====
# ===== Placeholders (mientras mueves a blueprints de módulo) =====
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5020)), debug=True)
