# app/db.py
import os, sqlite3
from flask import g

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "vidrio.db")  # archivo en la raíz

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            address TEXT,
            phone TEXT UNIQUE,
            company TEXT,
            created_at TEXT NOT NULL
        );
    """)
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_unique ON users(phone);")
    db.commit()

def close_db(e=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_app_db(app):
    @app.teardown_appcontext
    def teardown(exception):
        close_db()
    with app.app_context():
        init_db()
