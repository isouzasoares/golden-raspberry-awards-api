"""Movie use cases."""

from app.repositories.movie_repository import MovieRepository
from app.schemas.movie import MoviePage, MovieRead
from app.services.exceptions import NotFoundError


class MovieService:
    """List and look up Worst Picture nominees."""

    def __init__(self, repository: MovieRepository) -> None:
        """Initialize the service.

        Args:
            repository: Source of the movies.
        """
        self._repository = repository

    def list_movies(
        self,
        *,
        year: int | None,
        winner: bool | None,
        limit: int,
        offset: int,
    ) -> MoviePage:
        """Return a page of nominees.

        Args:
            year: Keep only movies nominated in this year.
            winner: Keep only winners (``True``) or only non-winners (``False``).
            limit: Maximum number of movies returned.
            offset: Number of movies skipped.

        Returns:
            The requested page.
        """
        movies, total = self._repository.list(
            year=year, winner=winner, limit=limit, offset=offset
        )
        return MoviePage(
            items=[MovieRead.model_validate(movie) for movie in movies],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_movie(self, movie_id: int) -> MovieRead:
        """Return a single nominee.

        Args:
            movie_id: Movie identifier.

        Returns:
            The movie.

        Raises:
            NotFoundError: If no movie has the given identifier.
        """
        movie = self._repository.get(movie_id)
        if movie is None:
            raise NotFoundError(f"Movie {movie_id} not found")
        return MovieRead.model_validate(movie)
