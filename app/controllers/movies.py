"""Movie endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.controllers.dependencies import SessionDep
from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MoviePage, MovieRead

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviePage, summary="List nominated movies")
def list_movies(
    session: SessionDep,
    year: Annotated[int | None, Query(description="Nomination year.")] = None,
    winner: Annotated[bool | None, Query(description="Filter by winners.")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MoviePage:
    """Return a page of nominees, optionally filtered by year and winner flag."""
    movies, total = MovieRepository(session).list(
        year=year, winner=winner, limit=limit, offset=offset
    )
    return MoviePage(
        items=[MovieRead.model_validate(movie) for movie in movies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{movie_id}",
    response_model=MovieRead,
    summary="Get a movie",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movie not found."}},
)
def get_movie(session: SessionDep, movie_id: Annotated[int, Path(ge=1)]) -> MovieRead:
    """Return a single nominee by its identifier."""
    movie = MovieRepository(session).get(movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie {movie_id} not found",
        )
    return MovieRead.model_validate(movie)
