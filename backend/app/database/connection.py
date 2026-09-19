"""Database connection and session management.

Uses PostgreSQL when available, falls back to SQLite for development.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# If PostgreSQL URL is set and reachable, use it; otherwise fall back to SQLite
USE_SQLITE = True
if DATABASE_URL and "postgresql" in DATABASE_URL:
    try:
        test_engine = create_engine(DATABASE_URL)
        test_conn = test_engine.connect()
        test_conn.close()
        USE_SQLITE = False
    except Exception:
        USE_SQLITE = True

if USE_SQLITE:
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resourceloop.db")
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
