from flask import Blueprint, render_template
from .medidas import medidas_bp   # <--- IMPORTA

core = Blueprint("core", __name__, template_folder="../templates", static_folder="../static")

@core.route("/")
def index():
    return render_template("login.html")

@core.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

def register_blueprints(app):
    app.register_blueprint(core)
    app.register_blueprint(medidas_bp)  # <--- REGISTRA
