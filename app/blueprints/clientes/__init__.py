# app/blueprints/clientes/__init__.py
from flask import Blueprint, render_template

bp = Blueprint("clientes", __name__, template_folder="../../templates")

@bp.route("/")
def index():
    return render_template("module_blank.html", title="Clientes")
