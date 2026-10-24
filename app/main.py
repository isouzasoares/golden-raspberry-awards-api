"""FastAPI application factory.

Serve it with ``uvicorn app.main:create_app --factory``.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings
from app.db.session import create_database_engine, create_session_factory
from app.models import Base
from app.routers import movies, producers
from app.services.movie_importer import MovieImporter

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    On startup a fresh in-memory database is created and populated with the
    movies of ``settings.csv_path``; it is discarded on shutdown.

    Args:
        settings: Application settings. Defaults to :meth:`Settings.from_env`.

    Returns:
        The configured application.
    """
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine()
        Base.metadata.create_all(engine)
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            imported = MovieImporter(session).import_csv(settings.csv_path)
        logger.info("Imported %d movies from %s", imported, settings.csv_path)

        app.state.session_factory = session_factory
        try:
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="Golden Raspberry Awards API",
        description="Nominees and winners of the Worst Picture category.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(movies.router, prefix=settings.api_prefix)
    application.include_router(producers.router, prefix=settings.api_prefix)
    return application
