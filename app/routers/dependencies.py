"""Dependencies shared by the routers."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.repositories.movie_repository import MovieRepository
from app.repositories.producer_repository import ProducerRepository
from app.services.award_intervals import AwardIntervalService
from app.services.movie_service import MovieService


def get_session(request: Request) -> Iterator[Session]:
    """Provide a database session scoped to the current request.

    Args:
        request: Incoming request, used to reach the application state.

    Yields:
        An open session, closed once the response is sent.
    """
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_movie_service(session: SessionDep) -> MovieService:
    """Build the movie service for the current request."""
    return MovieService(MovieRepository(session))


def get_award_interval_service(session: SessionDep) -> AwardIntervalService:
    """Build the award interval service for the current request."""
    return AwardIntervalService(ProducerRepository(session))


MovieServiceDep = Annotated[MovieService, Depends(get_movie_service)]
AwardIntervalServiceDep = Annotated[
    AwardIntervalService, Depends(get_award_interval_service)
]
