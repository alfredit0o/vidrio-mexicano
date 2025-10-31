# app/blueprints/core.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from app.db import get_db

core_bp = Blueprint("core", __name__)

def current_user_email():
    return session.get("user_email")

@core_bp.route("/")
def root():
    return redirect(url_for("core.dashboard" if current_user_email() else "auth.login"))

@core_bp.route("/dashboard")
def dashboard():
    user_email = current_user_email()
    if not user_email:
        flash("Acceso no autorizado. Inicia sesión.", "warning")
        return redirect(url_for("auth.login"))

    db = get_db()
    u = db.execute("SELECT first_name, last_name FROM users WHERE email = ?", (user_email,)).fetchone()
    full_name = f"{u['first_name']} {u['last_name']}" if u else user_email

    modules = [
        {"name":"Clientes",     "href": url_for("clientes.index"),     "img": "img/clientes.png"},
        {"name":"Productos",    "href": url_for("productos.index"),    "img": "img/productos.png"},
        {"name":"Pedidos",      "href": url_for("pedidos.index"),      "img": "img/pedidos.png"},
        {"name":"Cotizaciones", "href": url_for("cotizaciones.index"), "img": "img/cotizaciones.png"},
        {"name":"Inventario",   "href": url_for("inventario.index"),   "img": "img/inventario.png"},
        {"name":"Reportes",     "href": url_for("reportes.index"),     "img": "img/reportes.png"},
    ]
    return render_template("dashboard.html", user=full_name, modules=modules)
