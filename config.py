import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

BOOKS_DIR = os.environ.get("BOOKS_DIR", os.path.join(BASE_DIR, "books"))
COVERS_DIR = os.path.join(BASE_DIR, "static", "covers")

# Garantir que a pasta de capas exista
os.makedirs(COVERS_DIR, exist_ok=True)

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "DATABASE_URL nao configurada. Copie .env.example para .env e preencha "
        "com as credenciais do seu banco PostgreSQL local."
    )

def _normalize_db_url(url):
    """Render e Heroku entregam a URL como postgres://, formato removido no
    SQLAlchemy 1.4+. Converte para postgresql:// antes de usar."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ["DATABASE_URL"])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
