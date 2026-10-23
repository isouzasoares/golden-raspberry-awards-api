"""Data access for movies."""

from collections.abc import Sequence

from sqlalchemy import Select, func, select
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
        query = self._filtered(select(Movie), year=year, winner=winner)
        total = self._session.scalar(
            self._filtered(select(func.count(Movie.id)), year=year, winner=winner)
        )
        movies = self._session.scalars(
            query.order_by(Movie.year, Movie.title, Movie.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return movies, total or 0

    @staticmethod
    def _filtered(query: Select, *, year: int | None, winner: bool | None) -> Select:
        if year is not None:
            query = query.where(Movie.year == year)
        if winner is not None:
            query = query.where(Movie.winner.is_(winner))
        return query
