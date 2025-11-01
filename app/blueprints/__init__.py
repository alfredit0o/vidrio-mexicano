# app/blueprints/__init__.py
from .core import core_bp

def register_blueprints(app):
    app.register_blueprint(core_bp)
    # aquí luego: app.register_blueprint(clientes_bp), etc.
