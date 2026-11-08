from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine setup with connection pooling for PostgreSQL and SQLite test compatibility
connect_args = {}
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions to API routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
