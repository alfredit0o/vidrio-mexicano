# app/db.py
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text

# Usa DATABASE_URL si existe; si no, cae a SQLite local para desarrollo.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATABASE_URL = f"sqlite:///{os.path.join(base, 'vidrio.db')}"

# Render/psycopg: pool preconfigurado
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

@contextmanager
def get_db():
    """Yield a connection with BEGIN/COMMIT/ROLLBACK automáticamente."""
    with engine.begin() as conn:
        yield conn

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  address TEXT,
  phone TEXT UNIQUE,
  company TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS medidas (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  unidad TEXT NOT NULL,
  descripcion TEXT,
  creado_por TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS fotos (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  creado_por TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  original_png BYTEA,     -- imagen original (PNG)
  anotada_png BYTEA,      -- imagen con anotaciones (PNG)
  anotaciones_json TEXT   -- lista de anotaciones (JSON)
);

"""

def init_app_db(app):
    # Crear tablas si no existen
    with engine.begin() as conn:
        for stmt in filter(None, SCHEMA_SQL.split(";")):
            s = stmt.strip()
            if s:
                conn.execute(text(s))
                


