"""In-memory SQLite engine and session factory."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

IN_MEMORY_SQLITE_URL = "sqlite://"


def create_database_engine() -> Engine:
    """Create an engine bound to a private in-memory SQLite database.

    ``StaticPool`` keeps a single connection alive for the whole lifetime of
    the engine; without it every new connection would open a brand-new,
    empty in-memory database.

    Returns:
        The SQLAlchemy engine.
    """
    return create_engine(
        IN_MEMORY_SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the session factory used by the request handlers.

    Args:
        engine: Engine the sessions are bound to.

    Returns:
        A configured ``sessionmaker``.
    """
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
