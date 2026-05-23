import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./longevity.db")

if DATABASE_URL.startswith("sqlite"):
    # NullPool: never keep connections open between requests.
    # This prevents SQLite OS-level file locks from blocking Alembic DDL
    # (batch_alter_table needs an exclusive lock; a pooled idle connection
    # blocks it indefinitely on Windows).
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    # PostgreSQL (or any other DB): use a proper connection pool.
    # pool_pre_ping=True tests connections on checkout so stale connections
    # (e.g. after a DB restart) are silently replaced instead of erroring.
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
