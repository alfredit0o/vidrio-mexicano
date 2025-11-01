# app/blueprints/core.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from app.db import get_db

core_bp = Blueprint("core", __name__)

def current_user_email():
    return session.get("user_email")

@core_bp.route("/")
def root():
    return redirect(url_for("core.dashboard" if current_user_email() else "login"))

@core_bp.route("/dashboard")
def dashboard():
    user_email = current_user_email()
    if not user_email:
        flash("Acceso no autorizado. Inicia sesión.", "warning")
        return redirect(url_for("login"))

    db = get_db()
    u = db.execute("SELECT first_name, last_name FROM users WHERE email = ?", (user_email,)).fetchone()
    full_name = f"{u['first_name']} {u['last_name']}".upper() if u else user_email

    modules = [
        {"name": "Clientes",     "href": url_for("clientes"),     "img": "img/clientes.png"},
        {"name": "Productos",    "href": url_for("productos"),    "img": "img/productos.png"},
        {"name": "Pedidos",      "href": url_for("pedidos"),      "img": "img/pedidos.png"},
        {"name": "Cotizaciones", "href": url_for("cotizaciones"), "img": "img/cotizaciones.png"},
        {"name": "Inventario",   "href": url_for("inventario"),   "img": "img/inventario.png"},
        {"name": "Reportes",     "href": url_for("reportes"),     "img": "img/reportes.png"},
    ]
    return render_template("dashboard.html", user=full_name, modules=modules)
