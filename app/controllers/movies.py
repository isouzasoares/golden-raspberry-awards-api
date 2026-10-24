"""Movie endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.controllers.dependencies import MovieServiceDep
from app.schemas.movie import MoviePage, MovieRead
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviePage, summary="List nominated movies")
def list_movies(
    service: MovieServiceDep,
    year: Annotated[int | None, Query(description="Nomination year.")] = None,
    winner: Annotated[bool | None, Query(description="Filter by winners.")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MoviePage:
    """Return a page of nominees, optionally filtered by year and winner flag."""
    return service.list_movies(year=year, winner=winner, limit=limit, offset=offset)


@router.get(
    "/{movie_id}",
    response_model=MovieRead,
    summary="Get a movie",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movie not found."}},
)
def get_movie(
    service: MovieServiceDep, movie_id: Annotated[int, Path(ge=1)]
) -> MovieRead:
    """Return a single nominee by its identifier."""
    try:
        return service.get_movie(movie_id)
    except NotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
