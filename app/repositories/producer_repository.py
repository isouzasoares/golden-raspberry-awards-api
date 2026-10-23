"""Data access for producers."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Movie, Producer
from app.models.movie import movie_producers
from app.schemas.producer import ProducerAwardInterval


class ProducerRepository:
    """Query producers from the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: Session used to run the queries.
        """
        self._session = session

    def list_award_intervals(self) -> list[ProducerAwardInterval]:
        """List the interval between every pair of consecutive awards.

        Each award counts on its own: a producer who wins twice in the same
        year has an interval of zero between those awards.

        Returns:
            One entry per pair of consecutive awards of the same producer,
            ordered by the year of the earlier award and by producer name.
        """
        previous_win = (
            func.lag(Movie.year)
            .over(partition_by=Producer.id, order_by=Movie.year)
            .label("previous_win")
        )
        awards = (
            select(
                Producer.name.label("producer"),
                previous_win,
                Movie.year.label("following_win"),
            )
            .join(movie_producers, movie_producers.c.producer_id == Producer.id)
            .join(Movie, Movie.id == movie_producers.c.movie_id)
            .where(Movie.winner.is_(True))
            .subquery()
        )
        query = (
            select(
                awards.c.producer,
                (awards.c.following_win - awards.c.previous_win).label("interval"),
                awards.c.previous_win,
                awards.c.following_win,
            )
            .where(awards.c.previous_win.is_not(None))
            .order_by(awards.c.previous_win, awards.c.producer)
        )
        return [
            ProducerAwardInterval.model_validate(row)
            for row in self._session.execute(query)
        ]
