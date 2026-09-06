import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.database.base import Base

logger = logging.getLogger(__name__)


def create_db_engine():
    """Create database engine with fallback to SQLite if PostgreSQL is unavailable locally."""
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
            # Test connection
            with engine.connect():
                pass
        return engine
    except (OperationalError, Exception) as exc:
        if settings.USE_SQLITE_FALLBACK:
            logger.warning(
                f"Could not connect to PostgreSQL ({exc}). Falling back to local SQLite database: {settings.SQLITE_DB_PATH}"
            )
            return create_engine(
                settings.SQLITE_DB_PATH, connect_args={"check_same_thread": False}
            )
        raise exc


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures proper closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    # Import all models so that Base.metadata has all table definitions
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
