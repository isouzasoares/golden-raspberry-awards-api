"""Producer award interval rules."""

from app.repositories.producer_repository import ProducerRepository
from app.schemas.producer import ProducerAwardIntervals


class AwardIntervalService:
    """Find producers with the shortest and longest gap between awards."""

    def __init__(self, repository: ProducerRepository) -> None:
        """Initialize the service.

        Args:
            repository: Source of the producer award intervals.
        """
        self._repository = repository

    def get_extreme_intervals(self) -> ProducerAwardIntervals:
        """Return every interval tied for the minimum and for the maximum.

        Only consecutive awards of the same producer are compared. When no
        producer has won more than once, both lists are empty.

        Returns:
            The shortest (``min``) and longest (``max``) award intervals.
        """
        intervals = self._repository.list_award_intervals()
        if not intervals:
            return ProducerAwardIntervals(min=[], max=[])

        shortest = min(item.interval for item in intervals)
        longest = max(item.interval for item in intervals)
        return ProducerAwardIntervals(
            min=[item for item in intervals if item.interval == shortest],
            max=[item for item in intervals if item.interval == longest],
        )
