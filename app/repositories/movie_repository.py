"""Data access for movies."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Movie


class MovieRepository:
    """Query movies from the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used to run the queries.
        """
        self._session = session

    def get(self, movie_id: int) -> Movie | None:
        """Fetch a movie by its identifier.

        Args:
            movie_id: Movie identifier.

        Returns:
            The movie, or ``None`` when it does not exist.
        """
        return self._session.get(Movie, movie_id)

    def list(
        self,
        *,
        year: int | None = None,
        winner: bool | None = None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Movie], int]:
        """List movies ordered by year and title.

        Args:
            year: Keep only movies nominated in this year.
            winner: Keep only winners (``True``) or only non-winners (``False``).
            limit: Maximum number of movies returned.
            offset: Number of movies skipped.

        Returns:
            The requested page and the total number of matching movies.
        """
        filters = {"year": year, "winner": winner}
        criteria = {
            field: value for field, value in filters.items() if value is not None
        }

        total = self._session.scalar(
            select(func.count()).select_from(Movie).filter_by(**criteria)
        )
        movies = self._session.scalars(
            select(Movie)
            .filter_by(**criteria)
            .order_by(Movie.year, Movie.title, Movie.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return movies, total or 0
