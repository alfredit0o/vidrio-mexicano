from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import text
from datetime import datetime
from app.db import get_db

medidas_bp = Blueprint(
    "medidas", __name__,
    url_prefix="/medidas",
    template_folder="../templates",
    static_folder="../static"
)

def require_login():
    if "user_email" not in session:
        flash("Debes iniciar sesión.", "warning")
        return False
    return True

@medidas_bp.route("/")
def index():
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        rows = db.execute(text("SELECT * FROM medidas ORDER BY id DESC")).mappings().all()
    return render_template("medidas_list.html", medidas=rows)

@medidas_bp.route("/new", methods=["GET", "POST"])
def new():
    if not require_login(): return redirect(url_for("login"))
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        unidad = request.form.get("unidad","").strip()
        descripcion = request.form.get("descripcion","").strip()
        if not (nombre and unidad):
            flash("Nombre y unidad son obligatorios.", "warning")
            return redirect(url_for("medidas.new"))
        with get_db() as db:
            db.execute(text("""
                INSERT INTO medidas (nombre, unidad, descripcion, creado_por, created_at)
                VALUES (:n, :u, :d, :by, :ts)
            """), dict(n=nombre, u=unidad, d=descripcion, by=session["user_email"], ts=datetime.utcnow()))
        flash("Medida creada.", "success")
        return redirect(url_for("medidas.index"))
    return render_template("medidas_form.html", mode="new")

@medidas_bp.route("/<int:mid>/edit", methods=["GET", "POST"])
def edit(mid):
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        m = db.execute(text("SELECT * FROM medidas WHERE id=:id"), {"id": mid}).mappings().first()
        if not m:
            flash("No existe la medida.", "danger")
            return redirect(url_for("medidas.index"))
        if request.method == "POST":
            nombre = request.form.get("nombre","").strip()
            unidad = request.form.get("unidad","").strip()
            descripcion = request.form.get("descripcion","").strip()
            if not (nombre and unidad):
                flash("Nombre y unidad son obligatorios.", "warning")
                return redirect(url_for("medidas.edit", mid=mid))
            db.execute(text("""
                UPDATE medidas SET nombre=:n, unidad=:u, descripcion=:d WHERE id=:id
            """), dict(n=nombre, u=unidad, d=descripcion, id=mid))
            flash("Medida actualizada.", "success")
            return redirect(url_for("medidas.index"))
    return render_template("medidas_form.html", mode="edit", medida=m)

@medidas_bp.route("/<int:mid>/delete", methods=["POST"])
def delete(mid):
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        db.execute(text("DELETE FROM medidas WHERE id=:id"), {"id": mid})
    flash("Medida eliminada.", "info")
    return redirect(url_for("medidas.index"))
