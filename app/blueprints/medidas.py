from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from sqlalchemy import text
from datetime import datetime
import base64, json

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

# ============ LISTADO ============
@medidas_bp.route("/")
def index():
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        rows = db.execute(text("""
          SELECT id, nombre, creado_por, created_at, anotada_png IS NOT NULL AS tiene_anotada,
                 CASE WHEN anotada_png IS NOT NULL THEN anotada_png ELSE original_png END AS thumb
          FROM fotos
          ORDER BY id DESC
        """)).fetchall()

    # Convertimos a data URI (solo para listar)
    fotos = []
    for r in rows:
        png_bytes = r[5]
        data_uri = None
        if png_bytes:
            b64 = base64.b64encode(png_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{b64}"
        fotos.append({
            "id": r[0],
            "nombre": r[1],
            "creado_por": r[2],
            "created_at": r[3],
            "tiene_anotada": bool(r[4]),
            "data_uri": data_uri
        })
    return render_template("medidas_list.html", fotos=fotos)

# ============ CAPTURAR (CÁMARA) ============
@medidas_bp.route("/new", methods=["GET"])
def new():
    if not require_login(): return redirect(url_for("login"))
    return render_template("medidas_capture.html")

@medidas_bp.route("/new", methods=["POST"])
def new_post():
    if not require_login(): return redirect(url_for("login"))
    nombre = request.form.get("nombre","").strip()
    dataurl = request.form.get("dataurl","")
    if not nombre or not dataurl.startswith("data:image/png;base64,"):
        flash("Falta nombre o foto.", "warning")
        return redirect(url_for("medidas.new"))

    # decode base64
    b64 = dataurl.split(",",1)[1]
    png_bytes = base64.b64decode(b64)

    with get_db() as db:
        db.execute(text("""
          INSERT INTO fotos (nombre, creado_por, created_at, original_png)
          VALUES (:n, :by, :ts, :img)
        """), {"n": nombre, "by": session["user_email"], "ts": datetime.utcnow(), "img": png_bytes})

    flash("Foto guardada.", "success")
    return redirect(url_for("medidas.index"))

# ============ VER ============
@medidas_bp.route("/<int:fid>")
def view(fid):
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        row = db.execute(text("""
          SELECT id, nombre, creado_por, created_at, original_png, anotada_png, anotaciones_json
          FROM fotos WHERE id=:id
        """), {"id": fid}).first()
    if not row:
        flash("No existe la foto.", "danger")
        return redirect(url_for("medidas.index"))

    def to_datauri(png_bytes):
        if not png_bytes: return None
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    original_uri = to_datauri(row[4])
    anotada_uri  = to_datauri(row[5])
    anotaciones  = json.loads(row[6]) if row[6] else []
    return render_template("medidas_view.html",
                           foto_id=row[0], nombre=row[1], creado_por=row[2], created_at=row[3],
                           original_uri=original_uri, anotada_uri=anotada_uri, anotaciones=anotaciones)

# ============ ANOTAR ============
@medidas_bp.route("/<int:fid>/annotate", methods=["GET"])
def annotate(fid):
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        row = db.execute(text("SELECT id, nombre, original_png, anotaciones_json FROM fotos WHERE id=:id"), {"id": fid}).first()
    if not row:
        flash("No existe la foto.", "danger"); return redirect(url_for("medidas.index"))

    b64 = base64.b64encode(row[2]).decode("utf-8") if row[2] else None
    dataurl = f"data:image/png;base64,{b64}" if b64 else None
    anotaciones = json.loads(row[3]) if row[3] else []
    return render_template("medidas_annotate.html",
                           foto_id=row[0], nombre=row[1], base_image=dataurl, anotaciones=anotaciones)

@medidas_bp.route("/<int:fid>/annotate", methods=["POST"])
def annotate_save(fid):
    if not require_login(): return redirect(url_for("login"))
    # Recibimos dataurl de PNG anotado y JSON de anotaciones
    dataurl = request.form.get("dataurl","")
    anot_json = request.form.get("anotaciones","[]")
    if not dataurl.startswith("data:image/png;base64,"):
        flash("No se recibió imagen anotada.", "warning")
        return redirect(url_for("medidas.annotate", fid=fid))
    png_bytes = base64.b64decode(dataurl.split(",",1)[1])

    with get_db() as db:
        db.execute(text("""
           UPDATE fotos SET anotada_png=:png, anotaciones_json=:jn WHERE id=:id
        """), {"png": png_bytes, "jn": anot_json, "id": fid})

    flash("Anotaciones guardadas.", "success")
    return redirect(url_for("medidas.view", fid=fid))

# ============ ELIMINAR ============
@medidas_bp.route("/<int:fid>/delete", methods=["POST"])
def delete(fid):
    if not require_login(): return redirect(url_for("login"))
    with get_db() as db:
        db.execute(text("DELETE FROM fotos WHERE id=:id"), {"id": fid})
    flash("Foto eliminada.", "info")
    return redirect(url_for("medidas.index"))
