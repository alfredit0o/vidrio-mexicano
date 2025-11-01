# app/blueprints/__init__.py
from flask import Blueprint, render_template, session, redirect, url_for

# Importa el BP de Medidas
from .medidas import medidas_bp

# ---- Core (homepage + dashboard) ----
core = Blueprint(
    "core",
    __name__,
    template_folder="../templates",
    static_folder="../static",
)

@core.route("/", endpoint="index")
def index():
    # Si ya hay sesión, ve al dashboard; si no, al login
    if session.get("user_email"):
        return redirect(url_for("core.dashboard"))
    return redirect(url_for("login"))

@core.route("/dashboard", endpoint="dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---- Registro de blueprints ----
def register_blueprints(app):
    app.register_blueprint(core)
    app.register_blueprint(medidas_bp)   # 👈 IMPORTANTE: registra Medidas
