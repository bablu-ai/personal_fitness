"""
Shared pytest fixtures for the backend test suite.

Provides:
- in-memory SQLite DB that is created fresh for every test
- FastAPI TestClient with the DB dependency overridden

Implementation note: SQLite in-memory databases are connection-scoped. When FastAPI
runs sync endpoints in a thread pool, SQLAlchemy may open a NEW connection which
sees an empty database. We work around this by using StaticPool — all connections
share the same underlying database object so tables created in one connection are
visible to all others.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Must be set before app.main is imported — prevents _run_migrations() from
# touching the real longevity.db during test collection.
os.environ.setdefault("TESTING", "1")

from app.db.database import Base, get_db  # noqa: E402

# Import all models so Base.metadata is fully populated before create_all
import app.db.models  # noqa: F401, E402

from app.main import app  # noqa: E402


@pytest.fixture()
def db_engine():
    """
    Create an in-memory SQLite engine with all tables for one test.

    StaticPool with a unique connection object per fixture call ensures:
    1. All SQLAlchemy connections within this test share the same in-memory database
       (so tables created by create_all are visible in thread-pool workers).
    2. Each test gets its own isolated database (no cross-test data leakage).

    The trick: StaticPool reuses a single provided connection. We create a raw
    sqlite3 connection and give it to the pool so every session uses it.
    """
    import sqlite3
    raw_conn = sqlite3.connect(":memory:", check_same_thread=False)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        creator=lambda: raw_conn,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()
    raw_conn.close()


@pytest.fixture()
def db_session(db_engine):
    """Return a SQLAlchemy session bound to the in-memory engine."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """
    Return a FastAPI TestClient with get_db overridden to use the in-memory DB.
    Each test gets a clean, isolated database.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
