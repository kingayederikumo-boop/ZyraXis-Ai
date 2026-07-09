"""
SQLAlchemy engine + session factory.

This module was imported by app/gateway/auth.py and app/orchestrator/router.py
but did not exist anywhere in the repo, causing ModuleNotFoundError on import
of the entire Orchestrator chain (i.e. every incoming message crashed the worker).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Config
from app.database.models import Base

# check_same_thread only matters for sqlite; harmless to pass for other engines
# only when the URL is actually sqlite.
connect_args = {"check_same_thread": False} if Config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(Config.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they don't exist yet. Call once at startup."""
    Base.metadata.create_all(bind=engine)
