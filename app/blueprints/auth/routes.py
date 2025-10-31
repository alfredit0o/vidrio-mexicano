# app/blueprints/auth/routes.py
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db

auth_bp = Blueprint("auth", __name__, template_folder="../../templates")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        ok = bool(row and check_password_hash(row["password_hash"], password))
        if ok:
            session["user_email"] = email
            flash("Has iniciado sesión.", "success")
            return redirect(url_for("core.dashboard"))
        flash("Correo o contraseña incorrectos.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        f = request.form
        email      = f.get("email","").strip().lower()
        password   = f.get("password","")
        confirm    = f.get("confirm","")
        first_name = f.get("first_name","").strip()
        last_name  = f.get("last_name","").strip()
        address    = f.get("address","").strip()
        phone      = f.get("phone","").strip()
        company    = f.get("company","").strip()
        accept     = f.get("accept")

        if not (email and password and confirm and first_name and last_name):
            flash("Completa los campos obligatorios (*).", "warning"); return redirect(url_for("auth.register"))
        if not EMAIL_RE.match(email):
            flash("Correo inválido.", "danger"); return redirect(url_for("auth.register"))
        if password != confirm:
            flash("Las contraseñas no coinciden.", "danger"); return redirect(url_for("auth.register"))
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "warning"); return redirect(url_for("auth.register"))
        if not accept:
            flash("Debes aceptar las políticas para continuar.", "warning"); return redirect(url_for("auth.register"))

        db = get_db()
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            flash("Ese correo ya está registrado.", "danger"); return redirect(url_for("auth.register"))
        if phone and db.execute("SELECT 1 FROM users WHERE phone = ?", (phone,)).fetchone():
            flash("Ese teléfono ya está registrado.", "danger"); return redirect(url_for("auth.register"))

        pw_hash = generate_password_hash(password)
        db.execute("""INSERT INTO users (email,password_hash,first_name,last_name,address,phone,company,created_at)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (email, pw_hash, first_name, last_name, address, phone, company, datetime.utcnow().isoformat()))
        db.commit()

        flash("Cuenta creada. Inicia sesión.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")
