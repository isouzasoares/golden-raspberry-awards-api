"""Producer payloads."""

from app.schemas.base import ApiSchema


class ProducerAwardInterval(ApiSchema):
    """Time elapsed between two consecutive awards of the same producer."""

    producer: str
    interval: int
    previous_win: int
    following_win: int


class ProducerAwardIntervals(ApiSchema):
    """Producers with the shortest and the longest interval between awards."""

    min: list[ProducerAwardInterval]
    max: list[ProducerAwardInterval]
